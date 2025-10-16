#!/usr/bin/env python3
"""
Test RAG-Anything parsing capabilities across all required document formats.
Part of Story 0.1: RAG-Anything Technical Validation Spike
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any
import sys

# Track results
results = {
    "formats_tested": [],
    "successful_formats": [],
    "failed_formats": [],
    "parsing_times": {},
    "errors": {},
    "output_structures": {}
}


def test_format(file_path: Path, format_name: str) -> dict[str, Any]:
    """
    Test parsing a single document format.

    Returns:
        Dictionary with success status, timing, output structure, and any errors
    """
    result = {
        "format": format_name,
        "file": str(file_path),
        "success": False,
        "parse_time_seconds": 0.0,
        "error": None,
        "output_structure": None
    }

    if not file_path.exists():
        result["error"] = f"File not found: {file_path}"
        return result

    try:
        # Import raganything with proper API
        try:
            from raganything import RAGAnything, RAGAnythingConfig
            print(f"✓ raganything module imported successfully")
        except ImportError as e:
            result["error"] = f"Failed to import raganything: {e}"
            return result

        # Test parsing with timing
        start_time = time.perf_counter()

        # Create RAG-Anything instance with configuration
        # Note: This requires LLM function callbacks which we'll mock for parsing-only tests
        async def mock_llm_func(prompt, **kwargs):
            """Mock LLM function for parsing-only tests"""
            return "mock_response"

        async def mock_embedding_func(texts):
            """Mock embedding function for parsing-only tests"""
            return [[0.0] * 384 for _ in texts]  # Mock embeddings

        config = RAGAnythingConfig(
            working_dir=str(Path("outputs/rag_storage")),
            parser="mineru",
            parse_method="auto",
            enable_image_processing=True,
            enable_table_processing=True,
            enable_equation_processing=True,
        )

        # Initialize RAG-Anything
        # Note: This may require async context
        import asyncio

        async def parse_document():
            rag = RAGAnything(
                config=config,
                llm_model_func=mock_llm_func,
                embedding_func=mock_embedding_func
            )

            # Process document
            await rag.process_document_complete(
                file_path=str(file_path),
                output_dir=str(Path("outputs") / file_path.stem),
                parse_method="auto"
            )

            return True

        # Run async parsing
        asyncio.run(parse_document())

        end_time = time.perf_counter()
        result["parse_time_seconds"] = end_time - start_time
        result["success"] = True

        # Analyze output structure
        output_path = Path("outputs") / file_path.stem
        if output_path.exists():
            result["output_structure"] = {
                "output_directory": str(output_path),
                "files_created": list([f.name for f in output_path.iterdir()])
            }

    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
        import traceback
        result["traceback"] = traceback.format_exc()

    return result


def analyze_output(parsed_output: Any) -> dict[str, Any]:
    """Analyze and describe the structure of parsed output"""
    structure = {
        "type": type(parsed_output).__name__,
        "keys": None,
        "text_content_present": False,
        "metadata_present": False,
        "tables_extracted": False,
        "images_extracted": False
    }

    if isinstance(parsed_output, dict):
        structure["keys"] = list(parsed_output.keys())
        structure["text_content_present"] = any(
            key in parsed_output for key in ["text", "content", "body"]
        )
        structure["metadata_present"] = "metadata" in parsed_output
        structure["tables_extracted"] = "tables" in parsed_output
        structure["images_extracted"] = "images" in parsed_output

    return structure


def discover_raganything_api():
    """
    Discover RAG-Anything API structure by examining the module.
    This is critical for understanding how to use the library.
    """
    print("\n" + "="*70)
    print("RAG-ANYTHING API DISCOVERY")
    print("="*70 + "\n")

    try:
        import raganything

        print("Module imported successfully!")
        print(f"Module location: {raganything.__file__}")
        print(f"Module version: {getattr(raganything, '__version__', 'unknown')}")
        print("\nAvailable attributes and methods:")

        public_attrs = [attr for attr in dir(raganything) if not attr.startswith('_')]
        for attr in public_attrs:
            obj = getattr(raganything, attr)
            print(f"  - {attr}: {type(obj).__name__}")

        print("\nModule docstring:")
        print(raganything.__doc__ or "No docstring available")

        # Try to find parser classes or functions
        print("\nLooking for parser-related components...")
        parser_attrs = [attr for attr in public_attrs if 'parse' in attr.lower()]
        for attr in parser_attrs:
            print(f"  Found: {attr}")

        return True

    except ImportError as e:
        print(f"✗ Failed to import raganything: {e}")
        print("\nThis indicates RAG-Anything is not properly installed.")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during API discovery: {e}")
        return False


def main():
    """Main test execution"""
    print("="*70)
    print("RAG-ANYTHING FORMAT VALIDATION SPIKE")
    print("Story 0.1: Testing 6 document formats")
    print("="*70 + "\n")

    # First, discover the API
    if not discover_raganything_api():
        print("\n✗ Cannot proceed without RAG-Anything installed")
        sys.exit(1)

    # Define test files
    samples_dir = Path("samples")
    test_files = {
        "PDF (text-based)": samples_dir / "climate-research-paper.pdf",
        "PDF (scanned)": samples_dir / "climate-scanned.pdf",  # May not exist
        "Plain Text": samples_dir / "climate-abstract.txt",
        "Markdown": samples_dir / "climate-report.md",
        "Word DOCX": samples_dir / "climate-mitigation-strategies.docx",
        "PowerPoint PPTX": samples_dir / "climate-science-presentation.pptx",
        "CSV": samples_dir / "climate-data.csv"
    }

    print("\n" + "="*70)
    print("TESTING DOCUMENT FORMATS")
    print("="*70 + "\n")

    # Test each format
    for format_name, file_path in test_files.items():
        print(f"\nTesting: {format_name}")
        print(f"File: {file_path}")
        print("-" * 70)

        if not file_path.exists():
            print(f"⚠ File not found - skipping")
            results["formats_tested"].append(format_name)
            results["failed_formats"].append(format_name)
            results["errors"][format_name] = "File not found"
            continue

        result = test_format(file_path, format_name)
        results["formats_tested"].append(format_name)

        if result["success"]:
            results["successful_formats"].append(format_name)
            results["parsing_times"][format_name] = result["parse_time_seconds"]
            results["output_structures"][format_name] = result["output_structure"]
            print(f"✓ Success! Parsed in {result['parse_time_seconds']:.2f}s")
        else:
            results["failed_formats"].append(format_name)
            results["errors"][format_name] = result["error"]
            print(f"✗ Failed: {result['error']}")

    # Save results
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    results_file = output_dir / "format_validation_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total formats tested: {len(results['formats_tested'])}")
    print(f"Successful: {len(results['successful_formats'])}")
    print(f"Failed: {len(results['failed_formats'])}")
    print(f"\nResults saved to: {results_file}")

    # Print success/failure details
    if results["successful_formats"]:
        print("\n✓ Successful formats:")
        for fmt in results["successful_formats"]:
            print(f"  - {fmt}")

    if results["failed_formats"]:
        print("\n✗ Failed formats:")
        for fmt in results["failed_formats"]:
            print(f"  - {fmt}: {results['errors'].get(fmt, 'Unknown error')}")


if __name__ == "__main__":
    main()
