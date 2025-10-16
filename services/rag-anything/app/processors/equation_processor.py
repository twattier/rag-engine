"""Equation processor for LaTeX formatting."""
from __future__ import annotations

import re


class EquationProcessor:
    """Processes mathematical equations."""

    @staticmethod
    def normalize_latex(latex: str) -> str:
        """
        Normalize LaTeX equation string.

        Args:
            latex: Raw LaTeX equation

        Returns:
            Normalized LaTeX string
        """
        # Remove surrounding whitespace
        normalized = latex.strip()

        # Remove dollar signs if present
        normalized = normalized.strip("$")

        # Remove equation environment tags if present
        normalized = re.sub(r"\\begin\{equation\}|\{\\end\{equation\}", "", normalized)

        return normalized.strip()

    @staticmethod
    def is_valid_latex(latex: str) -> bool:
        """
        Basic validation of LaTeX equation.

        Args:
            latex: LaTeX equation string

        Returns:
            True if LaTeX appears valid
        """
        if not latex or not latex.strip():
            return False

        # Check for balanced braces
        brace_count = latex.count("{") - latex.count("}")
        if brace_count != 0:
            return False

        # Check for common LaTeX commands
        has_latex_command = bool(re.search(r"\\[a-zA-Z]+", latex))

        return has_latex_command or any(char in latex for char in "^_{}=")
