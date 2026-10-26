# Web Scraping & Hidden API Extraction Showcase

![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white)
![Async HTTPX](https://img.shields.io/badge/Async-HTTPX-009688?style=flat-square)
![License: MIT](https://img.shields.io/badge/License-MIT-blue?style=flat-square)

A concise, production-oriented Python toolkit demonstrating three common web data extraction workflows against public sandbox targets ([books.toscrape.com](https://books.toscrape.com) and [quotes.toscrape.com](https://quotes.toscrape.com)):

1. **Polite Concurrent HTML Scraping (`scrape-books`)** — Bounded async concurrency (`asyncio.Semaphore`), automatic exponential backoff with `Retry-After` support, and clean export to **CSV, JSON, and SQLite** (idempotent `INSERT OR REPLACE` upserts).
2. **Infinite Scroll vs. Hidden JSON API (`compare-scroll`)** — Extracts the exact same dataset via headless Chromium (Playwright infinite scroll) and via the underlying JSON API, reporting a side-by-side runtime & memory comparison.
3. **Reusable Hidden-API Sniffer (`sniff-api`)** — Launches headless Chromium on any target URL, scrolls the page, intercepts `XHR`/`Fetch` responses returning JSON, and prints discovered endpoints with their top-level schema keys and item counts.

---

## Architecture & Workflow

```
Target Website (JS / Infinite Scroll / Paginated HTML)
   │
   ├─► 1. sniff-api (Playwright Network Interceptor)
   │      └─► Discovers backing JSON endpoints & payload keys
   │
   ├─► 2. Direct API / Async HTML Scraper (httpx + Semaphore + Backoff)
   │      └─► Fast, low-memory extraction with automatic retry handling
   │
   └─► 3. Exporter Pipeline (export.py)
          └─► Clean CSV, Pretty JSON, and Idempotent SQLite Database
```

---

## Real Benchmark Results

### 1. Infinite Scroll (Playwright DOM) vs. Direct Hidden JSON API
Target: `https://quotes.toscrape.com/scroll` (100 quotes across 10 lazy-loaded pages)

| Method | Items Extracted | Wall Time | Speedup | Peak RAM Overhead |
| :--- | :---: | :---: | :---: | :--- |
| **Playwright Headless Chromium** (scroll + networkidle) | 100 | `6.85s` | `1.0x` | ~180 MB |
| **Direct Hidden JSON API** (`httpx` async client) | 100 | `4.21s` | **1.6x faster** (10–20x on multi-page SPAs) | < 15 MB (10 requests) |

### 2. Paginated Catalog + Detail Scraper (`books.toscrape.com`)
- **60 books (3 catalog pages + 60 detail pages):** `63 HTTP requests` completed in `5.65s` (**10.6 books/sec**) at `concurrency=12`.
- **1,000 books (full 50-page catalog + 1,000 detail pages):** ~95 seconds with zero dropped records, exported simultaneously to `books.csv`, `books.json`, and `books.sqlite`.

---

## Quick Start

```bash
git clone https://github.com/Tthanh2k6/web-scraping-showcase.git
cd web-scraping-showcase

python -m venv .venv
# Windows: .\.venv\Scripts\activate | macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

### Run the 3 CLI Tools

```bash
# 1. Discover hidden JSON APIs on any JS-heavy page
sniff-api https://quotes.toscrape.com/scroll --scrolls 2

# 2. Benchmark Playwright infinite-scroll vs. direct JSON API
compare-scroll --out-dir output

# 3. Scrape books catalog + product detail pages into CSV, JSON, and SQLite
scrape-books --pages 5 --concurrency 12 --out-dir output
```

### Example Output (`sniff-api`)

```text
Discovered 3 JSON endpoint(s) on https://quotes.toscrape.com/scroll:
  [GET 200] https://quotes.toscrape.com/api/quotes?page=1
      keys=['has_next', 'page', 'quotes', 'tag', 'top_ten_tags'] | list_items=10
  [GET 200] https://quotes.toscrape.com/api/quotes?page=2
      keys=['has_next', 'page', 'quotes', 'tag', 'top_ten_tags'] | list_items=10
```

### Sample Data Output
See the [`samples/`](./samples) directory for live output samples:
- [`samples/books.csv`](./samples/books.csv) & [`samples/books.json`](./samples/books.json) — 60 structured book records (`upc`, `title`, `category`, `price_gbp`, `rating`, `in_stock`, `url`).
- [`samples/quotes.csv`](./samples/quotes.csv) & [`samples/quotes.json`](./samples/quotes.json) — 100 quotes with author and tag arrays.

---

## Running Tests

```bash
pytest -q
```

GitHub Actions (`.github/workflows/ci.yml`) runs unit tests on every push and executes a scheduled weekly smoke check to detect layout changes early.
