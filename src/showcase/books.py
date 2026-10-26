"""Demo 1: Scrape up to 1,000 books from books.toscrape.com with bounded async concurrency."""
from __future__ import annotations

import argparse
import asyncio
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from showcase.export import write_csv, write_json, write_sqlite
from showcase.fetch import Fetcher

BASE_URL = "https://books.toscrape.com/"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
PRICE_RE = re.compile(r"[\d.]+")
STOCK_RE = re.compile(r"\((\d+)\s+available\)")


@dataclass
class Book:
    upc: str
    title: str
    category: str
    price_gbp: float
    rating: int
    in_stock: int
    url: str


def parse_catalog_page(html: str, page_url: str) -> tuple[list[str], str | None]:
    """Extract book detail URLs and the next catalog page URL."""
    soup = BeautifulSoup(html, "lxml")
    book_urls = [
        urljoin(page_url, a["href"])
        for a in soup.select("article.product_pod h3 a[href]")
    ]
    next_link = soup.select_one("li.next a[href]")
    next_url = urljoin(page_url, next_link["href"]) if next_link else None
    return book_urls, next_url


def parse_book_detail(html: str, url: str) -> Book:
    """Parse a single book detail page into a structured Book record."""
    soup = BeautifulSoup(html, "lxml")
    title = soup.select_one("div.product_main h1").get_text(strip=True)

    crumbs = [a.get_text(strip=True) for a in soup.select("ul.breadcrumb li a")]
    category = crumbs[2] if len(crumbs) >= 3 else "Unknown"

    price_text = soup.select_one("p.price_color").get_text(strip=True)
    price_match = PRICE_RE.search(price_text)
    price_gbp = float(price_match.group(0)) if price_match else 0.0

    rating_el = soup.select_one("p.star-rating")
    rating_classes = rating_el.get("class", []) if rating_el else []
    rating = next((RATING_MAP[c] for c in rating_classes if c in RATING_MAP), 0)

    table = {
        row.select_one("th").get_text(strip=True): row.select_one("td").get_text(strip=True)
        for row in soup.select("table.table-striped tr")
        if row.select_one("th") and row.select_one("td")
    }
    upc = table.get("UPC", url)
    avail_text = table.get("Availability", "")
    stock_match = STOCK_RE.search(avail_text)
    in_stock = int(stock_match.group(1)) if stock_match else 0

    return Book(
        upc=upc,
        title=title,
        category=category,
        price_gbp=price_gbp,
        rating=rating,
        in_stock=in_stock,
        url=url,
    )


async def scrape_books(max_pages: int = 50, concurrency: int = 12) -> tuple[list[Book], float, int]:
    t0 = time.perf_counter()
    async with Fetcher(concurrency=concurrency) as fetcher:
        # books.toscrape.com has 50 pages: page-1.html .. page-50.html
        first_resp = await fetcher.get(BASE_URL)
        book_urls, next_url = parse_catalog_page(first_resp.text, BASE_URL)

        if next_url and max_pages > 1:
            page_urls = [
                urljoin(BASE_URL, f"catalogue/page-{p}.html")
                for p in range(2, max_pages + 1)
            ]
            page_resps = await asyncio.gather(
                *(fetcher.get(u) for u in page_urls),
                return_exceptions=True,
            )
            for u, resp in zip(page_urls, page_resps):
                if isinstance(resp, Exception):
                    continue
                urls, _ = parse_catalog_page(resp.text, u)
                book_urls.extend(urls)

        async def _fetch_book(u: str) -> Book:
            r = await fetcher.get(u)
            return parse_book_detail(r.text, u)

        books = await asyncio.gather(*(_fetch_book(u) for u in book_urls))
        elapsed = time.perf_counter() - t0
        return list(books), elapsed, fetcher.requests


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape books.toscrape.com to CSV, JSON, SQLite.")
    parser.add_argument("--pages", type=int, default=50, help="Number of catalog pages (1..50)")
    parser.add_argument("--concurrency", type=int, default=12, help="Max concurrent requests")
    parser.add_argument("--out-dir", type=Path, default=Path("output"), help="Output directory")
    args = parser.parse_args()

    books, elapsed, reqs = asyncio.run(
        scrape_books(max_pages=args.pages, concurrency=args.concurrency)
    )
    out_dir: Path = args.out_dir
    write_csv(books, out_dir / "books.csv")
    write_json(books, out_dir / "books.json")
    write_sqlite(books, out_dir / "books.sqlite", table="books", primary_key="upc")

    print(
        f"Scraped {len(books)} books across {args.pages} page(s) "
        f"({reqs} HTTP requests in {elapsed:.2f}s -> {len(books)/elapsed:.1f} items/s)."
    )
    print(f"Saved: {out_dir / 'books.csv'}, {out_dir / 'books.json'}, {out_dir / 'books.sqlite'}")


if __name__ == "__main__":
    main()
