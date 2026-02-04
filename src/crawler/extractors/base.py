# src/crawler/extractors/base.py
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ExtractedDocument:
    """
    This is the output shape that all extractors should return.
    (Similar to a TS interface.)
    """
    source_url: str
    title: str
    text: str
    metadata: Dict[str, Any]


class BaseExtractor(ABC):
    """
    Contract for all extractors:
    input: link (url)
    output: ExtractedDocument
    """

    @abstractmethod
    async def extract(self, link: str, **kwargs) -> ExtractedDocument:
        raise NotImplementedError
