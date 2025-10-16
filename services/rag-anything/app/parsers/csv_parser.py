"""CSV parser using pandas."""
from __future__ import annotations

from pathlib import Path
import pandas as pd

from app.parsers.base_parser import BaseParser
from app.models import ContentItem


class CSVParser(BaseParser):
    """Parser for CSV files using pandas."""

    async def parse(self, file_path: Path) -> list[ContentItem]:
        """Parse CSV file and return table content."""
        df = pd.read_csv(file_path)

        # Convert DataFrame to list of lists (rows)
        rows = [df.columns.tolist()] + df.values.tolist()

        return [
            ContentItem(
                type="table",
                rows=rows,
                page_idx=0,
                structure="csv_table",
            )
        ]
