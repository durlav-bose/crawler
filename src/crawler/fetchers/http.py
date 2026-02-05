# src/crawler/fetchers/http.py
from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


@dataclass
class HttpResponse:
    url: str
    status: int
    text: str
    content_type: str | None = None


class HttpFetcher:
    """
    Small wrapper around aiohttp.
    - Handles timeouts
    - Retries on transient network errors
    - Reuses one session for many requests (important for performance)
    """

    def __init__(
        self,
        *,
        timeout_seconds: int = 25,
        user_agent: str = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        max_concurrency: int = 10,
    ) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._headers = {
            "User-Agent": user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }
        self._session: Optional[aiohttp.ClientSession] = None
        self._sem = asyncio.Semaphore(max_concurrency)

    async def __aenter__(self) -> "HttpFetcher":
        self._session = aiohttp.ClientSession(timeout=self._timeout, headers=self._headers)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def _require_session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("HttpFetcher session not started. Use: `async with HttpFetcher() as f:`")
        return self._session

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.6, min=0.6, max=6),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
    )
    async def fetch_text(self, url: str, extra_headers: dict | None = None) -> HttpResponse:
        """
        Fetch URL and return raw text (usually HTML).
        Retries on transient network errors.
        """
        session = self._require_session()
        headers = {**self._headers}
        if extra_headers:
            headers.update(extra_headers)

        async with self._sem:
            logger.debug("HTTP GET %s", url)
            async with session.get(url, headers=headers, allow_redirects=True) as resp:
                content_type = resp.headers.get("Content-Type")
                text = await resp.text(errors="ignore")
                return HttpResponse(
                    url=str(resp.url),
                    status=resp.status,
                    text=text,
                    content_type=content_type,
                )
