# Python Web Scraping & Hidden JSON API Extraction Showcase

<div align="center">
  <img src="https://raw.githubusercontent.com/Tthanh2k6/Portfolio/main/public/IMG/project-scraping.png" alt="Python Web Scraping & Hidden API Extraction Toolkit" width="100%" />

  <br />

  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.11+" />
    <img src="https://img.shields.io/badge/Async_HTTP-httpx_%2B_asyncio-00F0FF?style=flat-square" alt="httpx + asyncio" />
    <img src="https://img.shields.io/badge/Headless_Browser-Playwright-2EAD33?style=flat-square&logo=playwright&logoColor=white" alt="Playwright" />
    <img src="https://img.shields.io/badge/Storage-CSV_%7C_JSON_%7C_SQLite-10B981?style=flat-square&logo=sqlite&logoColor=white" alt="SQLite" />
    <img src="https://img.shields.io/badge/Tests-4_Passed_(Pytest)-FF6B00?style=flat-square&logo=pytest&logoColor=white" alt="Pytest" />
  </p>
</div>

---

A production-style Python scraping toolkit built for real-world data extraction jobs. All demos target **[toscrape.com](https://toscrape.com)** — a public sandbox created specifically for testing scrapers — so everything in this repository is 100% legal, reproducible, and safe to run.

## ✨ What This Repository Demonstrates

| Command | Scenario | Key Engineering Highlights |
| :--- | :--- | :--- |
| `scrape-books` | **Polite Async HTML Scraping** (`books.toscrape.com`) | Concurrent detail-page fetching (`asyncio.Semaphore`), exponential backoff + `Retry-After` handling, star/price normalization, and simultaneous **CSV + JSON + idempotent SQLite** export. |
| `compare-scroll` | **Infinite Scroll vs. Hidden JSON API** (`quotes.toscrape.com/scroll`) | Side-by-side benchmark extracting the exact same dataset via **Playwright headless Chromium** (infinite scrolling) vs. the **underlying JSON API** (`/api/quotes?page=N`). |
| `sniff-api` | **Reusable Hidden-API Sniffer** (Any URL) | Launches headless Chromium, auto-scrolls the page, intercepts `XHR` / `fetch` JSON responses, and prints a ranked table of discovered API endpoints with schema previews. |

---

## 📊 Real Benchmark: Playwright Infinite Scroll vs. Hidden JSON API

Measured on `https://quotes.toscrape.com/scroll` (100 quotes across 10 pages):

| Metric | Playwright Headless Browser (`/scroll`) | Direct Hidden JSON API (`/api/quotes`) | Improvement |
| :--- | :--- | :--- | :--- |
| **Total Time (100 items)** | `~4.80 s` | `~1.45 s` | **3.3× faster** |
| **Throughput** | `~20.8 items/s` | `~68.9 items/s` | **+231% throughput** |
| **Browser RAM Overhead** | `~180 MB` (Chromium process) | `< 15 MB` (pure `httpx`) | **>90% less memory** |
| **Fragility** | Breaks on CSS/DOM layout changes | Clean structured JSON (`has_next`, `quotes[]`) | **Production-grade stability** |

> **Why this matters for clients:** Before writing a slow, resource-heavy browser scraper, I always inspect the site's network traffic for a private/hidden JSON API. When one exists, your scraper runs faster, costs less to host, and rarely breaks.

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
scrape-books --pages 3 --concurrency 8 --output-dir output

# Or scrape the entire 1,000-book catalog (50 pages)
scrape-books --pages 50 --concurrency 10 --output-dir output
```

Outputs generated in `output/` (sample outputs included in [`samples/`](./samples)):
- `books.csv` — UTF-8 CSV ready for Excel / Google Sheets
- `books.json` — Clean, typed JSON array
- `books.sqlite` — Idempotent SQLite table (`books` keyed by `upc`, safe to re-run on a schedule without duplicates)

### 2. Benchmark Infinite Scroll vs. Hidden JSON API

```bash
compare-scroll --max-pages 10 --output-dir output
```

### 3. Sniff Hidden JSON APIs on Any JavaScript Page

```bash
sniff-api https://quotes.toscrape.com/scroll --scrolls 4
```

Example output:
```text
Discovered 1 JSON API endpoint(s)
┌────────┬──────────────────────────────────────────────┬────────┬────────────┬───────┬──────────────────────────────┐
│ Method │ Endpoint URL                                 │ Status │ Size (B)   │ Items │ Top-Level Keys / Preview     │
├────────┼──────────────────────────────────────────────┼────────┼────────────┼───────┼──────────────────────────────┤
│ GET    │ https://quotes.toscrape.com/api/quotes?page=1│ 200    │ 2,942      │ 10    │ has_next, page, quotes, ...  │
└────────┴──────────────────────────────────────────────┴────────┴────────────┴───────┴──────────────────────────────┘
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
│   ├── fetch.py           # PoliteHttpClient: concurrency semaphore, retries, exponential backoff
│   ├── books.py           # Async HTML + detail parser for books.toscrape.com
│   ├── quotes_compare.py  # Hidden JSON API vs. Playwright infinite-scroll benchmark
│   ├── sniffer.py         # Generic XHR/Fetch JSON API discovery tool
│   ├── export.py          # CSV, JSON, and idempotent SQLite upsert exporters
│   └── cli.py             # CLI entry points (scrape-books, compare-scroll, sniff-api)
├── samples/               # Sample CSV & JSON outputs (books.csv, books.json, quotes.csv, quotes.json)
├── tests/                 # Offline unit tests for HTML parsers, API parsers, and exporters
└── pyproject.toml
```

## 🔒 Data Ethics & Compliance

- Respects rate limits with bounded concurrency (`asyncio.Semaphore`), configurable request delays, and `Retry-After` headers.
- Collects only publicly available data; never harvests personal/private user data.

---

**Author:** **Trung Thanh Tran** (*Trần Trung Thành*) · [GitHub `@Tthanh2k6`](https://github.com/Tthanh2k6) · [Upwork Profile](https://www.upwork.com/freelancers/~01ee7c2348cb4b62fe)
