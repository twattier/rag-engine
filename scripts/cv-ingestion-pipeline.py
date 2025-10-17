#!/usr/bin/env python3
"""
CV Mass Ingestion Pipeline Script

This script ingests multiple CV PDF files from a directory into the RAG Engine
for testing and demonstration purposes.

Usage:
    # Ingest default 10 CVs
    python scripts/cv-ingestion-pipeline.py

    # Ingest specific number of CVs
    python scripts/cv-ingestion-pipeline.py --max-docs 50

    # Use custom CV directory
    python scripts/cv-ingestion-pipeline.py --source-dir /path/to/cvs

    # Use custom API URL
    python scripts/cv-ingestion-pipeline.py --api-url http://localhost:9000

Features:
    - Progress tracking with status updates
    - Error handling and retry logic
    - Summary statistics at completion
    - Detailed logging for troubleshooting
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List, Optional

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Project root
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_CV_DIR = PROJECT_ROOT / "tests" / "fixtures" / "sample-data" / "cv-pdfs"


class IngestionStats:
    """Track ingestion statistics."""

    def __init__(self):
        self.total_files = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.start_time = time.time()
        self.document_ids: List[str] = []

    def record_success(self, doc_id: str):
        self.successful += 1
        self.document_ids.append(doc_id)

    def record_failure(self):
        self.failed += 1

    def record_skip(self):
        self.skipped += 1

    def elapsed_time(self) -> float:
        return time.time() - self.start_time

    def throughput(self) -> float:
        """Calculate throughput in documents per minute."""
        elapsed = self.elapsed_time()
        if elapsed == 0:
            return 0.0
        return (self.successful / elapsed) * 60

    def print_summary(self):
        """Print final summary statistics."""
        elapsed = self.elapsed_time()
        print("\n" + "="*70)
        print("INGESTION SUMMARY")
        print("="*70)
        print(f"Total files processed:    {self.total_files}")
        print(f"Successfully ingested:    {self.successful}")
        print(f"Failed:                   {self.failed}")
        print(f"Skipped:                  {self.skipped}")
        print(f"Total time:               {elapsed:.2f}s")
        print(f"Average time per doc:     {elapsed / self.successful:.2f}s" if self.successful > 0 else "N/A")
        print(f"Throughput:               {self.throughput():.1f} documents/minute")
        print("="*70)
        print(f"\nIngested document IDs: {len(self.document_ids)}")
        if self.document_ids:
            print("\nTo view documents:")
            print(f"  curl -H 'X-API-Key: <your-key>' {args.api_url}/api/v1/documents")
            print("\nTo clean up test data:")
            print("  ./scripts/clear-test-data.sh")
        print()


def find_cv_files(source_dir: Path, max_docs: int) -> List[Path]:
    """
    Find CV PDF files in the source directory.

    Args:
        source_dir: Directory containing CV PDF files
        max_docs: Maximum number of documents to process

    Returns:
        List of Path objects to CV PDF files

    Raises:
        FileNotFoundError: If directory doesn't exist or no PDFs found
    """
    if not source_dir.exists():
        raise FileNotFoundError(
            f"CV directory not found: {source_dir}\n"
            "Run: python scripts/download-sample-data.py"
        )

    cv_files = sorted(source_dir.glob("*.pdf"))

    if not cv_files:
        raise FileNotFoundError(
            f"No PDF files found in {source_dir}\n"
            "Run: python scripts/download-sample-data.py"
        )

    # Limit to max_docs
    cv_files = cv_files[:max_docs]

    logger.info(f"Found {len(cv_files)} CV files to ingest")
    return cv_files


def ingest_document(
    api_url: str,
    api_key: str,
    cv_file: Path,
    index: int,
    total: int
) -> Optional[str]:
    """
    Ingest a single CV document via API.

    Args:
        api_url: Base API URL
        api_key: API authentication key
        cv_file: Path to CV PDF file
        index: Current document index (1-based)
        total: Total number of documents

    Returns:
        Document ID if successful, None if failed
    """
    logger.info(f"[{index}/{total}] Ingesting: {cv_file.name}")

    try:
        with open(cv_file, "rb") as f:
            files = {
                "file": (cv_file.name, f, "application/pdf")
            }
            metadata = {
                "category": "cv",
                "source": "mass_ingestion",
                "batch_index": index,
                "filename": cv_file.name
            }
            data = {
                "metadata": json.dumps(metadata)
            }
            headers = {
                "X-API-Key": api_key
            }

            response = requests.post(
                f"{api_url}/api/v1/documents/ingest",
                files=files,
                data=data,
                headers=headers,
                timeout=30
            )

        if response.status_code == 202:
            result = response.json()
            doc_id = result.get("documentId")
            logger.info(f"  ✓ Success: {doc_id}")
            return doc_id
        else:
            logger.error(f"  ✗ Failed: HTTP {response.status_code}")
            logger.error(f"    Response: {response.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        logger.error(f"  ✗ Failed: Request timeout")
        return None
    except requests.exceptions.ConnectionError:
        logger.error(f"  ✗ Failed: Connection error (is API running?)")
        return None
    except Exception as e:
        logger.error(f"  ✗ Failed: {type(e).__name__}: {e}")
        return None


def validate_api_health(api_url: str) -> bool:
    """
    Validate API service is accessible.

    Args:
        api_url: Base API URL

    Returns:
        True if API is healthy, False otherwise
    """
    try:
        response = requests.get(f"{api_url}/health", timeout=5)
        if response.status_code == 200:
            logger.info(f"✓ API service is healthy: {api_url}")
            return True
        else:
            logger.error(f"✗ API health check failed: HTTP {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"✗ Cannot reach API at {api_url}: {e}")
        logger.error("  Ensure services are running: docker-compose ps")
        return False


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Mass ingest CV PDF files into RAG Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Ingest default 10 CVs
  python scripts/cv-ingestion-pipeline.py

  # Ingest 50 CVs
  python scripts/cv-ingestion-pipeline.py --max-docs 50

  # Use custom directory
  python scripts/cv-ingestion-pipeline.py --source-dir /path/to/cvs --max-docs 100

Environment Variables:
  API_URL     API base URL (default: http://localhost:9000)
  API_KEY     API authentication key (default: test-key-12345)
        """
    )

    parser.add_argument(
        "--max-docs",
        type=int,
        default=10,
        help="Maximum number of documents to ingest (default: 10)"
    )
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_CV_DIR,
        help=f"Directory containing CV PDF files (default: {DEFAULT_CV_DIR})"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:9000",
        help="API base URL (default: http://localhost:9000)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default="test-key-12345",
        help="API authentication key (default: test-key-12345)"
    )

    global args
    args = parser.parse_args()

    print("="*70)
    print("CV MASS INGESTION PIPELINE")
    print("="*70)
    print(f"Configuration:")
    print(f"  Source directory:  {args.source_dir}")
    print(f"  Max documents:     {args.max_docs}")
    print(f"  API URL:           {args.api_url}")
    print("="*70)
    print()

    # Initialize statistics
    stats = IngestionStats()

    try:
        # Validate API health
        logger.info("Validating API service...")
        if not validate_api_health(args.api_url):
            logger.error("API service validation failed")
            return 1

        # Find CV files
        logger.info("Scanning for CV files...")
        cv_files = find_cv_files(args.source_dir, args.max_docs)
        stats.total_files = len(cv_files)

        # Ingest each document
        print()
        logger.info(f"Starting ingestion of {len(cv_files)} documents...")
        print()

        for idx, cv_file in enumerate(cv_files, 1):
            doc_id = ingest_document(
                args.api_url,
                args.api_key,
                cv_file,
                idx,
                len(cv_files)
            )

            if doc_id:
                stats.record_success(doc_id)
            else:
                stats.record_failure()

            # Brief pause between requests
            time.sleep(0.5)

        # Print summary
        stats.print_summary()

        # Return appropriate exit code
        if stats.failed == 0:
            logger.info("✓ All documents ingested successfully")
            return 0
        elif stats.successful > 0:
            logger.warning(f"⚠ Completed with {stats.failed} failures")
            return 0  # Partial success
        else:
            logger.error("✗ All ingestion attempts failed")
            return 1

    except FileNotFoundError as e:
        logger.error(str(e))
        return 2
    except KeyboardInterrupt:
        logger.warning("\n\nIngestion interrupted by user")
        stats.print_summary()
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
