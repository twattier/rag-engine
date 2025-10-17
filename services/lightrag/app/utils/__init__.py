"""Utility functions for LightRAG service."""

from __future__ import annotations

from .entity_config import build_extraction_prompt, load_entity_types

__all__ = ["load_entity_types", "build_extraction_prompt"]
