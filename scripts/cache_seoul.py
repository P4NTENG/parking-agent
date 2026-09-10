"""서울시 원본 JSON 캐시: data/seoul_cache.json 저장 (.gitignore 대상)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.seoul_api import CACHE_PATH, SERVICE, fetch_all


def main() -> int:
    ap = argparse.ArgumentParser(description="서울시 GetParkingInfo 원본 캐시 저장")
    ap.add_argument("--out", default=str(CACHE_PATH), help="저장 경로")
    ap.add_argument("--page-size", type=int, default=100, help="페이지 크기")
    args = ap.parse_args()

    rows = fetch_all(page_size=args.page_size)
    body = {SERVICE: {"list_total_count": len(rows), "row": rows}}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(body, f, ensure_ascii=False)
    print(f"{len(rows)}건 저장: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
