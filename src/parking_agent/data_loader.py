"""seed CSV 로더. 실제 단계에서 공공데이터 API 클라이언트로 교체."""

from __future__ import annotations

import csv
from pathlib import Path

SEED_PATH = Path(__file__).resolve().parents[2] / "data" / "seed_sample.csv"


def _to_bool(s: str) -> bool:
    return s.strip().lower() in ("true", "1", "y", "yes")


def load_candidates() -> list[dict]:
    rows: list[dict] = []
    with open(SEED_PATH, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            rows.append(
                {
                    "id": r["id"],
                    "name": r["name"],
                    "lat": float(r["lat"]),
                    "lon": float(r["lon"]),
                    "base_minutes": int(r["base_minutes"]),
                    "base_fee": int(r["base_fee"]),
                    "unit_minutes": int(r["unit_minutes"]),
                    "unit_fee": int(r["unit_fee"]),
                    "open_time": r["open_time"],
                    "close_time": r["close_time"],
                    "free": _to_bool(r.get("free", "false")),
                    "disabled": _to_bool(r.get("disabled", "false")),
                }
            )
    return rows
