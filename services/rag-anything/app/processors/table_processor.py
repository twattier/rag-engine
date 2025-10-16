"""Table processor for structure normalization."""
from __future__ import annotations

from typing import Any


class TableProcessor:
    """Processes tables for consistent structure."""

    @staticmethod
    def normalize_table(rows: list[list[Any]]) -> list[list[str]]:
        """
        Normalize table data to consistent string format.

        Args:
            rows: List of rows, each row is a list of cell values

        Returns:
            Normalized table with all cells as strings
        """
        normalized = []
        for row in rows:
            normalized_row = [str(cell).strip() if cell is not None else "" for cell in row]
            normalized.append(normalized_row)
        return normalized

    @staticmethod
    def table_to_markdown(rows: list[list[Any]], has_header: bool = True) -> str:
        """
        Convert table to Markdown format.

        Args:
            rows: List of rows, each row is a list of cell values
            has_header: Whether first row is header

        Returns:
            Markdown-formatted table string
        """
        if not rows:
            return ""

        normalized = TableProcessor.normalize_table(rows)
        md_lines = []

        # Add header row
        if has_header and len(normalized) > 0:
            header = normalized[0]
            md_lines.append("| " + " | ".join(header) + " |")
            md_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

            # Add data rows
            for row in normalized[1:]:
                md_lines.append("| " + " | ".join(row) + " |")
        else:
            # No header, all rows are data
            for row in normalized:
                md_lines.append("| " + " | ".join(row) + " |")

        return "\n".join(md_lines)

    @staticmethod
    def get_table_dimensions(rows: list[list[Any]]) -> tuple[int, int]:
        """
        Get table dimensions.

        Args:
            rows: List of rows

        Returns:
            Tuple of (num_rows, num_columns)
        """
        if not rows:
            return (0, 0)

        num_rows = len(rows)
        num_cols = max(len(row) for row in rows) if rows else 0
        return (num_rows, num_cols)
