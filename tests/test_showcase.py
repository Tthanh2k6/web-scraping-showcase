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
