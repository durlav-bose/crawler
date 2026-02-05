# src/crawler/fetchers/browser.py
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


@dataclass
class BrowserResponse:
    url: str
    status: int
    text: str
    content_type: str | None = None


class BrowserFetcher:
    """
    Fetcher that uses Playwright to render pages with a real browser.
    - Bypasses JavaScript-based bot detection
    - Slower than HttpFetcher but more reliable for protected sites
    - Good for sites like Medium that block automated requests
    """

    def __init__(
        self,
        *,
        timeout_seconds: int = 30,
        headless: bool = True,
        max_concurrency: int = 5,
    ) -> None:
        self._timeout = timeout_seconds * 1000  # Playwright uses milliseconds
        self._headless = headless
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._sem = asyncio.Semaphore(max_concurrency)

    async def __aenter__(self) -> "BrowserFetcher":
        self._playwright = await async_playwright().start()
        
        # Launch Chromium browser
        self._browser = await self._playwright.chromium.launch(headless=self._headless)
        
        # Create a browser context with realistic viewport and user agent
        self._context = await self._browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        logger.info("Browser fetcher initialized")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser fetcher closed")

    def _require_context(self) -> BrowserContext:
        if not self._context:
            raise RuntimeError("BrowserFetcher not started. Use: `async with BrowserFetcher() as f:`")
        return self._context

    @retry(
        reraise=True,
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(Exception),
    )
    async def fetch_text(self, url: str) -> BrowserResponse:
        """
        Fetch URL using a real browser and return rendered HTML.
        Slower but bypasses JavaScript-based bot detection.
        """
        context = self._require_context()

        async with self._sem:
            logger.info("Browser GET %s", url)
            page: Page = await context.new_page()
            
            try:
                # Navigate to the page
                response = await page.goto(url, timeout=self._timeout, wait_until="domcontentloaded")
                
                if not response:
                    raise RuntimeError(f"Failed to load page: {url}")
                
                # Wait a bit for dynamic content to load
                await page.wait_for_timeout(2000)  # 2 seconds
                
                # Get the rendered HTML
                content = await page.content()
                status = response.status
                final_url = page.url
                content_type = response.headers.get("content-type")
                
                logger.info("Browser fetch completed: status=%d url=%s", status, final_url)
                
                return BrowserResponse(
                    url=final_url,
                    status=status,
                    text=content,
                    content_type=content_type,
                )
            finally:
                await page.close()
