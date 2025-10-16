"""Image processor for format conversion and encoding."""
from __future__ import annotations

import base64
from pathlib import Path
from PIL import Image
from io import BytesIO


class ImageProcessor:
    """Processes images for document parsing."""

    @staticmethod
    def image_to_base64(image_path: Path, max_width: int = 800) -> str:
        """
        Convert image to base64 string with optional resizing.

        Args:
            image_path: Path to image file
            max_width: Maximum width for resizing (maintains aspect ratio)

        Returns:
            Base64-encoded image string
        """
        with Image.open(image_path) as img:
            # Resize if needed
            if img.width > max_width:
                aspect_ratio = img.height / img.width
                new_height = int(max_width * aspect_ratio)
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)

            # Convert to bytes
            buffer = BytesIO()
            img_format = img.format or "PNG"
            img.save(buffer, format=img_format)
            img_bytes = buffer.getvalue()

            # Encode to base64
            return base64.b64encode(img_bytes).decode("utf-8")

    @staticmethod
    def get_image_dimensions(image_path: Path) -> tuple[int, int]:
        """
        Get image dimensions.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (width, height)
        """
        with Image.open(image_path) as img:
            return img.size
