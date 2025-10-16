#!/bin/bash
# Download real-world climate change documents from public sources

SAMPLES_DIR="samples"
mkdir -p "$SAMPLES_DIR"

echo "Downloading climate change sample documents..."

# IPCC Climate Change Report (PDF - Text-based with tables and figures)
echo "Downloading IPCC Summary for Policymakers PDF..."
wget -q --show-progress -O "$SAMPLES_DIR/climate-ipcc-spm.pdf" \
    "https://www.ipcc.ch/site/assets/uploads/2018/02/WG1AR5_SPM_FINAL.pdf" || \
    echo "Note: IPCC PDF download may require alternative source"

# Alternative: Climate.gov resources
echo "Downloading Climate.gov report..."
wget -q --show-progress -O "$SAMPLES_DIR/climate-indicators.pdf" \
    "https://www.climate.gov/sites/default/files/2023_StateOfClimate_LowRes.pdf" || \
    echo "Note: Climate.gov PDF unavailable"

# World Bank Climate Documents (often available in DOCX/PDF)
echo "Attempting World Bank climate documents..."
wget -q --show-progress -O "$SAMPLES_DIR/climate-world-bank.pdf" \
    "https://documents.worldbank.org/curated/en/099125306012322331/pdf/P17382008a37060290a96c05b3b7a0fb10.pdf" || \
    echo "Note: World Bank document unavailable"

# For DOCX and PPTX, we'll rely on generated samples
# as most public sources serve PDFs or require authentication

echo ""
echo "Download attempt complete!"
echo "Note: Public document downloads can be unreliable."
echo "Falling back to generated samples ensures consistent testing."

# Check what we got
echo ""
echo "Successfully downloaded files:"
ls -lh "$SAMPLES_DIR"/*.pdf 2>/dev/null || echo "No PDF files downloaded"
