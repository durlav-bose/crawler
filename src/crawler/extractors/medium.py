# src/crawler/extractors/medium.py
from __future__ import annotations

import logging
from bs4 import BeautifulSoup

from crawler.extractors.base import BaseExtractor, ExtractedDocument
from crawler.fetchers.browser import BrowserFetcher

logger = logging.getLogger(__name__)


class MediumExtractor(BaseExtractor):
    """
    Extracts:
    - title
    - article text (best-effort)
    Uses browser-based fetching to bypass Medium's bot protection.
    """

    def __init__(self, fetcher: BrowserFetcher) -> None:
        self._fetcher = fetcher

    async def extract(self, link: str, **kwargs) -> ExtractedDocument:
        # Use browser fetcher to bypass bot detection
        resp = await self._fetcher.fetch_text(link)

        if resp.status >= 400:
            logger.error(f"Medium returned {resp.status} for {link}.")
            raise RuntimeError(f"Medium fetch failed: status={resp.status} url={resp.url}")

        soup = BeautifulSoup(resp.text, "lxml")

        # Title: try <h1>, then <title>
        title_tag = soup.find("h1")
        if title_tag and title_tag.get_text(strip=True):
            title = title_tag.get_text(strip=True)
        else:
            title = (soup.title.get_text(strip=True) if soup.title else "").strip()

        # Medium article text is usually inside <article>…</article>
        article = soup.find("article")
        if article:
            paragraphs = [p.get_text(" ", strip=True) for p in article.find_all("p")]
        else:
            # fallback: all <p> on page (noisy but works sometimes)
            paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]

        # Clean: remove empty lines and join
        paragraphs = [p for p in paragraphs if p]
        text = "\n".join(paragraphs)

        logger.info("Extracted Medium article: title=%r chars=%d", title, len(text))

        return ExtractedDocument(
            source_url=resp.url,
            title=title or "(untitled)",
            text=text,
            metadata={
                "source": "medium",
                "http_status": resp.status,
                "content_type": resp.content_type,
            },
        )
