"""Unit tests for HTML parsers, JSON endpoint summarizer, and CSV/JSON/SQLite exporters."""
from __future__ import annotations

import sqlite3
from pathlib import Path

from showcase.books import Book, parse_book_detail, parse_catalog_page
from showcase.export import write_csv, write_json, write_sqlite
from showcase.sniffer import _summarize_json

SAMPLE_CATALOG_HTML = """
<html><body>
  <section>
    <ol class="row">
      <li>
        <article class="product_pod">
          <h3><a href="catalogue/a-light-in-the-attic_1000/index.html">A Light in the Attic</a></h3>
        </article>
      </li>
    </ol>
    <ul class="pager"><li class="next"><a href="catalogue/page-2.html">next</a></li></ul>
  </section>
</body></html>
"""

SAMPLE_BOOK_HTML = """
<html><body>
  <ul class="breadcrumb">
    <li><a href="/">Home</a></li>
    <li><a href="/books">Books</a></li>
    <li><a href="/poetry">Poetry</a></li>
    <li class="active">A Light in the Attic</li>
  </ul>
  <div class="product_main">
    <h1>A Light in the Attic</h1>
    <p class="price_color">£51.77</p>
    <p class="star-rating Three"></p>
  </div>
  <table class="table table-striped">
    <tr><th>UPC</th><td>a897fe39b1053632</td></tr>
    <tr><th>Availability</th><td>In stock (22 available)</td></tr>
  </table>
</body></html>
"""


def test_parse_catalog_page() -> None:
    urls, next_url = parse_catalog_page(SAMPLE_CATALOG_HTML, "https://books.toscrape.com/")
    assert urls == ["https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"]
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_parse_book_detail() -> None:
    book = parse_book_detail(
        SAMPLE_BOOK_HTML,
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
    )
    assert book.upc == "a897fe39b1053632"
    assert book.title == "A Light in the Attic"
    assert book.category == "Poetry"
    assert book.price_gbp == 51.77
    assert book.rating == 3
    assert book.in_stock == 22


def test_exporters_roundtrip(tmp_path: Path) -> None:
    books = [
        Book(
            upc="u1",
            title="Book One",
            category="Tech",
            price_gbp=19.99,
            rating=5,
            in_stock=10,
            url="https://example.com/1",
        ),
        Book(
            upc="u2",
            title="Book Two",
            category="Science",
            price_gbp=29.50,
            rating=4,
            in_stock=3,
            url="https://example.com/2",
        ),
    ]
    csv_path = tmp_path / "books.csv"
    json_path = tmp_path / "books.json"
    db_path = tmp_path / "books.sqlite"

    assert write_csv(books, csv_path) == 2
    assert write_json(books, json_path) == 2
    assert write_sqlite(books, db_path, table="books", primary_key="upc") == 2
    # Idempotent upsert check
    assert write_sqlite(books, db_path, table="books", primary_key="upc") == 2

    with sqlite3.connect(db_path) as conn:
        count = conn.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    assert count == 2


def test_summarize_json() -> None:
    keys, count = _summarize_json({"has_next": True, "page": 1, "quotes": [{}, {}, {}]})
    assert "quotes" in keys
    assert count == 3


def test_parse_retry_after_seconds_date_and_garbage():
    from datetime import datetime, timedelta, timezone
    from email.utils import format_datetime

    from showcase.fetch import MAX_RETRY_AFTER, parse_retry_after

    assert parse_retry_after("120") == 120.0
    assert parse_retry_after("999999") == MAX_RETRY_AFTER
    future = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=90), usegmt=True)
    assert 80 <= parse_retry_after(future) <= 91
    assert parse_retry_after("soon") is None
    assert parse_retry_after("") is None


def test_sqlite_upsert_keeps_columns_it_does_not_write(tmp_path):
    import sqlite3

    db_path = tmp_path / "items.sqlite"
    write_sqlite([{"upc": "a1", "price": 10.0}], db_path, table="items", primary_key="upc")
    with sqlite3.connect(db_path) as conn:
        conn.execute('ALTER TABLE items ADD COLUMN first_seen TEXT')
        conn.execute("UPDATE items SET first_seen = '2026-11-01'")
    write_sqlite([{"upc": "a1", "price": 12.5}], db_path, table="items", primary_key="upc")
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT price, first_seen FROM items WHERE upc = 'a1'").fetchone()
    assert row == (12.5, "2026-11-01")
