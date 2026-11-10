# Python Web Scraping & Hidden JSON API Extraction Showcase

<div align="center">
  <img src="https://raw.githubusercontent.com/Tthanh2k6/Portfolio/main/public/IMG/project-scraping.png" alt="Python Web Scraping & Hidden API Extraction Toolkit" width="100%" />

  <br />

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.10+" />
    <img src="https://img.shields.io/badge/Async_HTTP-httpx_%2B_asyncio-00F0FF?style=flat-square" alt="httpx + asyncio" />
    <img src="https://img.shields.io/badge/Headless_Browser-Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white" alt="Playwright" />
    <img src="https://img.shields.io/badge/Storage-CSV_%7C_JSON_%7C_SQLite-10B981?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite" />
    <img src="https://img.shields.io/badge/Tests-6_Passed_(Pytest)-FF6B00?style=flat-square&logo=pytest&logoColor=white" alt="Pytest" />
  </p>
</div>

*Note on the preview image: its "1.6x – 15x" range does not match this repo's benchmark. The benchmark below measured about 3.3× on one run; your result depends on network and machine.*

---

A Python scraping toolkit with small, runnable examples of common scraping tasks. All demos target **[toscrape.com](https://toscrape.com)**, a public sandbox made for practising scraping, so the examples can be run without hitting a real business's site.

## ✨ What This Repository Demonstrates

| Command | Scenario | Key Engineering Highlights |
| :--- | :--- | :--- |
| `scrape-books` | **Polite Async HTML Scraping** (`books.toscrape.com`) | Concurrent detail-page fetching (`asyncio.Semaphore`), exponential backoff + `Retry-After` handling, star/price normalization, and simultaneous **CSV + JSON + idempotent SQLite** export. |
| `compare-scroll` | **Infinite Scroll vs. Hidden JSON API** (`quotes.toscrape.com/scroll`) | Side-by-side benchmark extracting the exact same dataset via **Playwright headless Chromium** (infinite scrolling) vs. the **underlying JSON API** (`/api/quotes?page=N`). |
| `sniff-api` | **Reusable Hidden-API Sniffer** (Any URL) | Launches headless Chromium, auto-scrolls the page, intercepts `XHR` / `fetch` JSON responses, and prints a ranked table of discovered API endpoints with schema previews. |

---

## 📊 Real Benchmark: Playwright Infinite Scroll vs. Hidden JSON API

Two runs of `compare-scroll` on 11 Nov 2026 from a laptop in Ho Chi Minh City, `https://quotes.toscrape.com/scroll` (100 quotes, 10 pages):

| Run | Playwright headless Chromium (`/scroll`) | Hidden JSON API with `httpx` (`/api/quotes`, 10 requests) | Speedup |
| :--- | :---: | :---: | :---: |
| 1 (cold browser start) | 31.27 s | 4.15 s | 7.5× |
| 2 | 7.25 s | 4.07 s | 1.8× |

Timings depend on network latency to the sandbox and on browser start-up, so run it yourself rather than trusting these numbers. Memory was not measured. The bigger practical gain is maintenance: the JSON API returns structured fields (`has_next`, `quotes[]`), while the browser path depends on page layout.

> **Why this matters for clients:** Before writing a slow, resource-heavy browser scraper, I always inspect the site's network traffic for a private/hidden JSON API. When one exists, the scraper is usually faster, cheaper to host and less likely to break when the page layout changes.

---

## 🚀 Quickstart

```bash
# 1. Clone and install in a virtual environment
git clone https://github.com/Tthanh2k6/web-scraping-showcase.git
cd web-scraping-showcase
python -m venv .venv

# Windows (PowerShell)
.\.venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

pip install -e ".[dev]"
playwright install chromium
```

### 1. Scrape Catalog & Product Details (CSV + JSON + SQLite)

```bash
# Scrape first 3 pages (60 books) with concurrency=8
scrape-books --pages 3 --concurrency 8 --out-dir output

# Or scrape the entire 1,000-book catalog (50 pages)
scrape-books --pages 50 --concurrency 10 --out-dir output
```

Outputs generated in `output/` (sample outputs included in [`samples/`](./samples)):
- `books.csv` — UTF-8 CSV ready for Excel / Google Sheets
- `books.json` — Clean, typed JSON array
- `books.sqlite` — Idempotent SQLite table (`books` keyed by `upc`, safe to re-run on a schedule without duplicates)

### 2. Benchmark Infinite Scroll vs. Hidden JSON API

```bash
# Scrapes all 10 pages both ways and writes quotes.csv / quotes.json
compare-scroll --out-dir output
```

### 3. Sniff Hidden JSON APIs on Any JavaScript Page

```bash
sniff-api https://quotes.toscrape.com/scroll --scrolls 4 --out output/endpoints.json
```

Output format (illustrative; one entry per captured JSON response, the count depends on `--scrolls`):
```text
Discovered N JSON endpoint(s) on https://quotes.toscrape.com/scroll:
  [GET 200] https://quotes.toscrape.com/api/quotes?page=1
      keys=['has_next', 'page', 'quotes', ...] | list_items=10
```

---

## 🧪 Running Tests

```bash
pytest -v
```

---

## 📁 Project Structure

```text
web-scraping-showcase/
├── src/showcase/
│   ├── fetch.py           # Fetcher: concurrency semaphore, retries, exponential backoff, Retry-After
│   ├── books.py           # Async HTML + detail parser for books.toscrape.com
│   ├── quotes_compare.py  # Hidden JSON API vs. Playwright infinite-scroll benchmark
│   ├── sniffer.py         # Generic XHR/Fetch JSON API discovery tool
│   └── export.py          # CSV, JSON, and idempotent SQLite upsert exporters
├── samples/               # Sample CSV & JSON outputs (books.csv, books.json, quotes.csv, quotes.json)
├── tests/                 # Offline unit tests for HTML parsers, API parsers, and exporters
└── pyproject.toml         # console scripts: scrape-books, compare-scroll, sniff-api (each module's main())
```

## 🔒 Data Ethics & Compliance

- Limits load with bounded concurrency (`asyncio.Semaphore`, `--concurrency`), backs off on 429/5xx and honours `Retry-After` headers.
- Collects only publicly available data; never harvests personal/private user data.

---

**Author:** **Trung Thanh Tran** (*Trần Trung Thành*) · [GitHub `@Tthanh2k6`](https://github.com/Tthanh2k6) · [Upwork Profile](https://www.upwork.com/freelancers/~01ee7c2348cb4b62fe)
