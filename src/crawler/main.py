# src/crawler/main.py
from __future__ import annotations

import asyncio
import logging
from urllib.parse import urlparse

from crawler.fetchers.http import HttpFetcher
from crawler.extractors.medium import MediumExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def pick_extractor(url: str, fetcher: HttpFetcher):
    host = (urlparse(url).hostname or "").lower()

    # simple routing
    if "medium.com" in host:
        return MediumExtractor(fetcher)

    raise ValueError(f"No extractor configured for host: {host}")


async def run(url: str) -> None:
    async with HttpFetcher() as fetcher:
        extractor = pick_extractor(url, fetcher)
        doc = await extractor.extract(url)

        # For now, just print some output (later: save to DB / embeddings)
        print("\n=== RESULT ===")
        print("URL:", doc.source_url)
        print("TITLE:", doc.title)
        print("CHARS:", len(doc.text))
        print("\nTEXT PREVIEW:\n", doc.text[:800])


def main() -> None:
    # put a Medium URL here while testing
    url = "https://sodium.com/@example/some-article"
    asyncio.run(run(url))


if __name__ == "__main__":
    main()
