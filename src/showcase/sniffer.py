"""Demo 3: Reusable Hidden-API Sniffer — captures XHR/Fetch JSON endpoints on any page."""
from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from playwright.async_api import Response, async_playwright


@dataclass
class CapturedEndpoint:
    method: str
    url: str
    status: int
    content_type: str
    sample_keys: list[str]
    item_count_hint: int | None


def _summarize_json(body: Any) -> tuple[list[str], int | None]:
    if isinstance(body, dict):
        keys = list(body.keys())[:10]
        for v in body.values():
            if isinstance(v, list):
                return keys, len(v)
        return keys, None
    if isinstance(body, list):
        sample = list(body[0].keys())[:10] if body and isinstance(body[0], dict) else []
        return sample, len(body)
    return [], None


async def sniff_json_endpoints(
    url: str,
    scrolls: int = 2,
    wait_ms: int = 600,
) -> list[CapturedEndpoint]:
    captured: list[CapturedEndpoint] = []
    seen_urls: set[str] = set()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        async def _on_response(resp: Response) -> None:
            ct = resp.headers.get("content-type", "")
            req_type = resp.request.resource_type
            if "json" not in ct.lower() and req_type not in ("xhr", "fetch"):
                return
            if resp.url in seen_urls:
                return
            try:
                data = await resp.json()
            except Exception:
                return
            seen_urls.add(resp.url)
            keys, count_hint = _summarize_json(data)
            captured.append(
                CapturedEndpoint(
                    method=resp.request.method,
                    url=resp.url,
                    status=resp.status,
                    content_type=ct,
                    sample_keys=keys,
                    item_count_hint=count_hint,
                )
            )

        page.on("response", _on_response)
        await page.goto(url, wait_until="networkidle")
        for _ in range(scrolls):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(wait_ms)
        await browser.close()

    return captured


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover hidden JSON/XHR APIs behind any JavaScript-rendered page."
    )
    parser.add_argument(
        "url",
        nargs="?",
        default="https://quotes.toscrape.com/scroll",
        help="Target page URL to inspect",
    )
    parser.add_argument("--scrolls", type=int, default=2, help="Number of scroll triggers")
    parser.add_argument("--out", type=Path, default=None, help="Optional JSON output file")
    args = parser.parse_args()

    endpoints = asyncio.run(sniff_json_endpoints(args.url, scrolls=args.scrolls))
    print(f"Discovered {len(endpoints)} JSON endpoint(s) on {args.url}:")
    for ep in endpoints:
        print(
            f"  [{ep.method} {ep.status}] {ep.url}\n"
            f"      keys={ep.sample_keys} | list_items={ep.item_count_hint}"
        )
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(
            json.dumps([asdict(e) for e in endpoints], indent=2),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
