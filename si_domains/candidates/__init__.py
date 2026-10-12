"""Offline generation of .si domain candidate labels."""

from .build import CATEGORIES, generate_all, generate_category

__all__ = ["CATEGORIES", "generate_all", "generate_category"]
