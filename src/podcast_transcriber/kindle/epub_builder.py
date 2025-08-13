from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Chapter:
    title: str
    text: str


@dataclass
class Document:
    title: str
    author: Optional[str] = None
    chapters: List[Chapter] = field(default_factory=list)
    summary: Optional[str] = None


# This module is intentionally minimal and delegates to exporters.export_book
# A richer “Document AST” can evolve without breaking callers.

