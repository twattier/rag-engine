#!/usr/bin/env python3
"""
Download CV PDF sample data from HuggingFace for testing.

This script downloads CV/resume PDF files from the gigswar/cv_files HuggingFace dataset
for use in end-to-end integration testing of the RAG Engine document ingestion pipeline.

Usage:
    # Download default 10 CVs
    python scripts/download-sample-data.py

    # Download custom number of CVs
    python scripts/download-sample-data.py --max-cvs 50

    # Download to custom directory
    python scripts/download-sample-data.py --max-cvs 20 --output-dir /path/to/custom/dir
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)


def download_cv_samples(
    max_cvs: int = 10,
    output_dir: str = "tests/fixtures/sample-data/cv-pdfs",
    dataset_name: str = "gigswar/cv_files"
) -> int:
    """
    Download CV PDF samples from HuggingFace dataset.

    Args:
        max_cvs: Maximum number of CV PDFs to download
        output_dir: Output directory for downloaded CVs
        dataset_name: HuggingFace dataset name (default: "gigswar/cv_files")

    Returns:
        Number of successfully downloaded CVs

    Raises:
        ImportError: If datasets library is not installed
        Exception: For download or file write errors
    """
    try:
        from datasets import load_dataset
    except ImportError:
        logger.error(
            "The 'datasets' library is required. Install with: "
            "pip install datasets"
        )
        raise

    logger.info(f"Loading HuggingFace dataset: {dataset_name}")

    try:
        # Load the dataset from HuggingFace
        # Try to load from available splits
        dataset = None

        if dataset_name == "d4rk3r/resumes-raw-pdf":
            # This dataset uses 'train' split
            try:
                dataset = load_dataset(dataset_name, split="train")
            except Exception as e:
                logger.error(f"Failed to load dataset split 'train': {e}")
                raise
        else:
            # Default: gigswar/cv_files uses test/validation splits
            try:
                dataset = load_dataset(dataset_name, split="test")
            except ValueError:
                # Fallback to validation if test doesn't exist
                try:
                    dataset = load_dataset(dataset_name, split="validation")
                except ValueError:
                    # Last resort: try train split
                    dataset = load_dataset(dataset_name, split="train")

        logger.info(f"Dataset loaded successfully. Total CVs available: {len(dataset)}")
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_path.absolute()}")

    # Limit to available CVs
    num_to_download = min(max_cvs, len(dataset))
    logger.info(f"Downloading {num_to_download} CV PDFs...")

    downloaded_count = 0

    for idx in range(num_to_download):
        try:
            item = dataset[idx]

            # Extract PDF content - different datasets have different formats
            pdf_content: Optional[bytes] = None

            # Try different field names based on dataset
            if 'pdf' in item:
                pdf_obj = item['pdf']

                # Check if it's a pdfplumber PDF object with stream
                if hasattr(pdf_obj, 'stream'):
                    # Read from the stream and reset position
                    stream = pdf_obj.stream
                    stream.seek(0)  # Reset to beginning
                    pdf_content = stream.read()
                    stream.seek(0)  # Reset again for any future use
                # Handle dict with 'bytes' key or direct bytes
                elif isinstance(pdf_obj, dict) and 'bytes' in pdf_obj:
                    pdf_content = pdf_obj['bytes']
                elif isinstance(pdf_obj, bytes):
                    pdf_content = pdf_obj
            elif 'content' in item:
                # d4rk3r/resumes-raw-pdf uses 'content' field
                content = item['content']
                if isinstance(content, bytes):
                    pdf_content = content
                elif hasattr(content, 'read'):
                    pdf_content = content.read()
            elif 'file' in item:
                file_obj = item['file']
                if isinstance(file_obj, bytes):
                    pdf_content = file_obj
                elif hasattr(file_obj, 'read'):
                    pdf_content = file_obj.read()

            if pdf_content is None:
                logger.warning(
                    f"CV {idx}: Could not find PDF content in dataset item. "
                    f"Available keys: {list(item.keys())}"
                )
                continue

            # Generate filename
            pdf_path = output_path / f"cv_{idx:03d}.pdf"

            # Write PDF to file
            with open(pdf_path, "wb") as f:
                f.write(pdf_content)

            file_size_kb = len(pdf_content) / 1024
            downloaded_count += 1

            logger.info(
                f"✓ Downloaded CV {downloaded_count}/{num_to_download}: "
                f"{pdf_path.name} ({file_size_kb:.1f} KB)"
            )

        except Exception as e:
            logger.error(f"Failed to download CV {idx}: {e}")
            continue

    logger.info(f"\n{'='*60}")
    logger.info(f"Download complete!")
    logger.info(f"Successfully downloaded: {downloaded_count}/{num_to_download} CVs")
    logger.info(f"Location: {output_path.absolute()}")
    logger.info(f"{'='*60}\n")

    return downloaded_count


def main() -> int:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Download CV PDF samples from HuggingFace for testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download default 10 CVs
  %(prog)s

  # Download 50 CVs
  %(prog)s --max-cvs 50

  # Download to custom directory
  %(prog)s --max-cvs 20 --output-dir ./my-cv-data
        """
    )

    parser.add_argument(
        "--max-cvs",
        type=int,
        default=10,
        help="Maximum number of CV PDFs to download (default: 10)"
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default="tests/fixtures/sample-data/cv-pdfs",
        help="Output directory for downloaded CVs (default: tests/fixtures/sample-data/cv-pdfs)"
    )

    parser.add_argument(
        "--dataset",
        type=str,
        default="gigswar/cv_files",
        choices=["gigswar/cv_files", "d4rk3r/resumes-raw-pdf"],
        help="HuggingFace dataset to download from (default: gigswar/cv_files)"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.max_cvs <= 0:
        logger.error("--max-cvs must be a positive integer")
        return 1

    try:
        downloaded = download_cv_samples(
            max_cvs=args.max_cvs,
            output_dir=args.output_dir,
            dataset_name=args.dataset
        )

        if downloaded == 0:
            logger.error("No CVs were downloaded")
            return 1

        return 0

    except ImportError:
        logger.error(
            "\nRequired dependencies missing. Install with:\n"
            "  pip install datasets\n"
        )
        return 1

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
