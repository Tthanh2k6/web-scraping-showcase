# web-scraping-showcase

[![CI](https://github.com/Tthanh2k6/web-scraping-showcase/actions/workflows/ci.yml/badge.svg)](https://github.com/Tthanh2k6/web-scraping-showcase/actions/workflows/ci.yml)

Three small Python scrapers that show one habit: before writing a browser scraper, look for the JSON API the page already calls. Every example runs against [toscrape.com](https://toscrape.com), a public sandbox built for practising scraping.

| Command | What it does |
| --- | --- |
| `sniff-api <url>` | Opens the page in headless Chromium, scrolls it, records every JSON response from `fetch`/XHR and lists the endpoints with their top-level keys. |
| `compare-scroll` | Collects the same 100 quotes twice, once by scrolling the page in Playwright and once from the JSON API behind it, and times both. |
| `scrape-books` | Async HTML scraper for books.toscrape.com: bounded concurrency, backoff on 429/5xx with `Retry-After`, output to CSV, JSON and SQLite. |

## What it finds

`sniff-api` on the infinite-scroll page, run on 16 Nov 2026:

```
$ sniff-api https://quotes.toscrape.com/scroll --scrolls 4 --out output/endpoints.json
Discovered 5 JSON endpoint(s) on https://quotes.toscrape.com/scroll:
  [GET 200] https://quotes.toscrape.com/api/quotes?page=1
      keys=['has_next', 'page', 'quotes', 'tag', 'top_ten_tags'] | list_items=10
  [GET 200] https://quotes.toscrape.com/api/quotes?page=2
      keys=['has_next', 'page', 'quotes', 'tag', 'top_ten_tags'] | list_items=10
  ...
```

Once you know `/api/quotes?page=N` exists, the browser is optional. `compare-scroll` measures the difference:

| Run (laptop in Ho Chi Minh City) | Playwright, scroll the page | JSON API with `httpx`, 10 requests | Ratio |
| --- | ---: | ---: | ---: |
| 11 Nov 2026, cold browser start | 31.27 s | 4.15 s | 7.5× |
| 11 Nov 2026, second run | 7.25 s | 4.07 s | 1.8× |
| 16 Nov 2026 | 6.12 s | 3.52 s | 1.7× |

Most of the time on both sides is network latency to the sandbox, so expect different numbers. The larger gain is that the API returns typed fields (`has_next`, `quotes[]`) that do not break when the page layout changes.

## Run it

```bash
git clone https://github.com/Tthanh2k6/web-scraping-showcase.git
cd web-scraping-showcase
python -m venv .venv
.venv\Scripts\activate        # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium

sniff-api https://quotes.toscrape.com/scroll --scrolls 4 --out output/endpoints.json
compare-scroll --out-dir output
scrape-books --pages 2 --concurrency 8 --out-dir output
```

`scrape-books --pages 2` on 16 Nov 2026 printed:

```
Scraped 40 books across 2 page(s) (42 HTTP requests in 4.92s -> 8.1 items/s).
Saved: output\books.csv, output\books.json, output\books.sqlite
```

The SQLite table is keyed by `upc`, so a re-run updates rows instead of adding duplicates. Sample outputs are in [`samples/`](./samples). The full catalogue is `--pages 50` (1,000 books).

Tests: `pytest` (6 offline tests for the HTML parser, the API parser and the exporters).

## Code

- `src/showcase/fetch.py`: shared fetcher with a semaphore, retries, exponential backoff and `Retry-After`.
- `src/showcase/books.py`: list and detail page parser for books.toscrape.com.
- `src/showcase/quotes_compare.py`: the scroll-vs-API comparison.
- `src/showcase/sniffer.py`: the endpoint sniffer.
- `src/showcase/export.py`: CSV, JSON and SQLite upsert.

## Limits

- The sniffer only sees JSON the page requests while it loads and scrolls. Endpoints behind a click, a login or a WebSocket will not show up.
- Rate limiting is per run (`--concurrency` plus backoff). Check a site's terms and robots.txt before pointing these tools at it.

## License

MIT
