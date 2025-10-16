"""Unit tests for content processors."""
from __future__ import annotations

import pytest

from app.processors.table_processor import TableProcessor
from app.processors.equation_processor import EquationProcessor


class TestTableProcessor:
    """Tests for TableProcessor."""

    def test_normalize_table(self):
        """Test table normalization."""
        rows = [
            ["Header1", "Header2", "Header3"],
            [1, 2, 3],
            ["A", None, "C"],
        ]

        normalized = TableProcessor.normalize_table(rows)

        assert len(normalized) == 3
        assert normalized[0] == ["Header1", "Header2", "Header3"]
        assert normalized[1] == ["1", "2", "3"]
        assert normalized[2] == ["A", "", "C"]

    def test_table_to_markdown(self):
        """Test table to Markdown conversion."""
        rows = [
            ["Name", "Age", "City"],
            ["Alice", "30", "NYC"],
            ["Bob", "25", "LA"],
        ]

        md = TableProcessor.table_to_markdown(rows, has_header=True)

        assert "| Name | Age | City |" in md
        assert "| --- | --- | --- |" in md
        assert "| Alice | 30 | NYC |" in md

    def test_get_table_dimensions(self):
        """Test getting table dimensions."""
        rows = [
            ["A", "B", "C"],
            ["D", "E", "F"],
        ]

        dimensions = TableProcessor.get_table_dimensions(rows)

        assert dimensions == (2, 3)


class TestEquationProcessor:
    """Tests for EquationProcessor."""

    def test_normalize_latex(self):
        """Test LaTeX normalization."""
        latex = "  $ E = mc^2 $  "
        normalized = EquationProcessor.normalize_latex(latex)

        assert normalized == "E = mc^2"

    def test_is_valid_latex(self):
        """Test LaTeX validation."""
        assert EquationProcessor.is_valid_latex("E = mc^2")
        assert EquationProcessor.is_valid_latex("\\frac{a}{b}")
        assert EquationProcessor.is_valid_latex("x^2 + y^2 = r^2")
        assert not EquationProcessor.is_valid_latex("")
        assert not EquationProcessor.is_valid_latex("   ")
        assert not EquationProcessor.is_valid_latex("{unclosed brace")
