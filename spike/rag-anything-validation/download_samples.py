#!/usr/bin/env python3
"""
Download real-world sample documents for RAG-Anything validation spike.
Downloads climate change related documents in various formats.
"""

import urllib.request
import os
from pathlib import Path

def download_file(url, filename):
    """Download a file from URL to samples directory"""
    filepath = Path("samples") / filename
    try:
        print(f"Downloading {filename}...")
        urllib.request.urlretrieve(url, filepath)
        print(f"✓ Downloaded: {filepath}")
        return True
    except Exception as e:
        print(f"✗ Failed to download {filename}: {e}")
        return False

def download_climate_samples():
    """
    Download real climate change documents from public sources.
    All documents focus on climate change science domain.
    """

    # Ensure samples directory exists
    Path("samples").mkdir(exist_ok=True)

    print("Downloading climate change sample documents...\n")

    # PDF samples - IPCC and climate research papers
    samples = {
        # Real climate science PDFs
        "climate-ipcc-summary.pdf":
            "https://www.ipcc.ch/site/assets/uploads/2018/02/WG1AR5_SPM_FINAL.pdf",

        # Word documents - Climate reports
        "climate-policy.docx":
            "https://unfccc.int/sites/default/files/resource/Sample_Document.docx",

        # PowerPoint - Climate presentations
        "climate-presentation.pptx":
            "https://unfccc.int/sites/default/files/resource/Sample_Presentation.pptx",
    }

    # Note: Many real-world URLs may not work due to:
    # 1. Authentication requirements
    # 2. JavaScript-rendered downloads
    # 3. Dynamic URLs
    #
    # Alternative approach: Use well-known public document repositories

    print("Note: Downloading from public sources may have limitations.")
    print("Alternative: Using locally generated samples with realistic content.\n")

    # For this spike, we'll generate realistic documents locally
    # and supplement with any successfully downloaded samples

    for filename, url in samples.items():
        download_file(url, filename)

    print("\n✓ Sample download attempt complete!")
    print("Note: Generated samples in create_samples.py provide reliable test coverage.")

if __name__ == "__main__":
    download_climate_samples()
