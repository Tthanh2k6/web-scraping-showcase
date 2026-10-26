"""Clean data export helpers for CSV, JSON, and SQLite with idempotent upserts."""
from __future__ import annotations

import csv
import json
import sqlite3
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable


def _to_dicts(rows: Iterable[Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for r in rows:
        if is_dataclass(r) and not isinstance(r, type):
            result.append(asdict(r))
        elif isinstance(r, dict):
            result.append(dict(r))
        else:
            raise TypeError(f"Unsupported row type: {type(r)!r}")
    return result


def write_csv(rows: Iterable[Any], path: str | Path) -> int:
    data = _to_dicts(rows)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if not data:
        out.write_text("", encoding="utf-8")
        return 0
    fieldnames = list(data[0].keys())
    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            flat = {
                k: (json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v)
                for k, v in row.items()
            }
            writer.writerow(flat)
    return len(data)


def write_json(rows: Iterable[Any], path: str | Path) -> int:
    data = _to_dicts(rows)
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(data)


def write_sqlite(
    rows: Iterable[Any],
    path: str | Path,
    table: str = "items",
    primary_key: str = "upc",
) -> int:
    data = _to_dicts(rows)
    if not data:
        return 0
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = list(data[0].keys())

    def _sql_type(val: Any) -> str:
        if isinstance(val, bool):
            return "INTEGER"
        if isinstance(val, int):
            return "INTEGER"
        if isinstance(val, float):
            return "REAL"
        return "TEXT"

    col_defs = []
    for c in cols:
        sql_t = _sql_type(data[0][c])
        pk = " PRIMARY KEY" if c == primary_key else ""
        col_defs.append(f'"{c}" {sql_t}{pk}')

    placeholders = ", ".join(["?"] * len(cols))
    col_names = ", ".join(f'"{c}"' for c in cols)
    sql_create = f'CREATE TABLE IF NOT EXISTS "{table}" ({", ".join(col_defs)})'
    sql_upsert = f'INSERT OR REPLACE INTO "{table}" ({col_names}) VALUES ({placeholders})'

    with sqlite3.connect(out) as conn:
        conn.execute(sql_create)
        values = [
            tuple(
                json.dumps(r[c], ensure_ascii=False) if isinstance(r[c], (list, dict)) else r[c]
                for c in cols
            )
            for r in data
        ]
        conn.executemany(sql_upsert, values)
        conn.commit()
    return len(data)
