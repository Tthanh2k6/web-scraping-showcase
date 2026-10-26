"""Shared async HTTP client: concurrency limit, retries with backoff, Retry-After support."""
from __future__ import annotations

import asyncio
import logging
import random

import httpx

log = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}
RETRY_STATUSES = {429, 500, 502, 503, 504}


class Fetcher:
    """Thin wrapper around httpx.AsyncClient that never hammers a site.

    - at most `concurrency` requests in flight
    - transient failures (network errors, 429, 5xx) are retried with exponential backoff
    - a server-sent Retry-After header wins over our own backoff
    """

    def __init__(self, concurrency: int = 8, retries: int = 4, timeout: float = 20.0) -> None:
        self._sem = asyncio.Semaphore(concurrency)
        self._retries = retries
        self._client = httpx.AsyncClient(
            headers=DEFAULT_HEADERS, timeout=timeout, follow_redirects=True
        )
        self.requests = 0
        self.retried = 0

    async def __aenter__(self) -> Fetcher:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._client.aclose()

    async def get(self, url: str, **kwargs) -> httpx.Response:
        for attempt in range(self._retries + 1):
            retry_after: float | None = None
            async with self._sem:
                try:
                    resp = await self._client.get(url, **kwargs)
                    self.requests += 1
                except httpx.TransportError as exc:
                    error: Exception = exc
                else:
                    if resp.status_code not in RETRY_STATUSES:
                        resp.raise_for_status()
                        return resp
                    error = httpx.HTTPStatusError(
                        f"HTTP {resp.status_code}", request=resp.request, response=resp
                    )
                    header = resp.headers.get("Retry-After", "")
                    retry_after = float(header) if header.isdigit() else None

            if attempt == self._retries:
                raise error
            self.retried += 1
            wait = retry_after if retry_after is not None else min(30, 2**attempt) + random.random()
            log.warning("retrying %s in %.1fs (%s)", url, wait, error)
            await asyncio.sleep(wait)
        raise AssertionError("unreachable")
