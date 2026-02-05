# src/crawler/main.py
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from urllib.parse import urlparse

from crawler.fetchers.browser import BrowserFetcher
from crawler.extractors.medium import MediumExtractor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


def pick_extractor(url: str, fetcher: BrowserFetcher):
    host = (urlparse(url).hostname or "").lower()

    # simple routing
    if "medium.com" in host:
        return MediumExtractor(fetcher)
    
    if "genesysoftwares.com" in host:
        return MediumExtractor(fetcher)  # Genesy blog uses similar structure to Medium

    raise ValueError(f"No extractor configured for host: {host}")


async def run(url: str) -> None:
    async with BrowserFetcher() as fetcher:
        extractor = pick_extractor(url, fetcher)
        doc = await extractor.extract(url)

        # Save the raw HTML content to a file for debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain = urlparse(url).hostname or "unknown"
        filePath = f"{domain}_{timestamp}.txt"
        
        try:
            with open(filePath, 'w', encoding='utf-8') as f:
                f.write(doc.text)
            logger.info(f"HTML content saved to {filePath}")
        except Exception as e:
            logger.error(f"Failed to save HTML content: {e}")# Output the result

        # For now, just print some output (later: save to DB / embeddings)
        print("\n=== RESULT ===")
        print("URL:", doc.source_url)
        print("TITLE:", doc.title)
        print("CHARS:", len(doc.text))
        print("\nTEXT PREVIEW:\n", doc.text[:800])


def main() -> None:
    # put a Medium URL here while testing
    # url = "https://medium.com/decodingai/an-end-to-end-framework-for-production-ready-llm-systems-by-building-your-llm-twin-2cc6bb01141f"
    url = "https://genesysoftwares.com/blogs/is-your-software-partner-enterprise-ready#1-what-makes-a-software-partner"
    asyncio.run(run(url))


if __name__ == "__main__":
    main()
