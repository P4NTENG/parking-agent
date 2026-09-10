"""서울시 ADDR → 위경도 백필 (Nominatim, 키 불필요).

- 사용 정책 준수: 초당 1건, User-Agent+Referer 명시, 캐시 재사용.
- data/seoul_cache.json의 ADDR을 읽어 data/geocode_cache.json에
  {PKLT_CD: {lat, lon}} 저장. 실패분은 needs_geocode=True로 남긴다.
- 122건 ≈ 3분. 중간 중단해도 저장된 만큼 resume.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.seoul_api import CACHE_PATH, _rows_from_cache

GEOCODE_PATH = Path(__file__).resolve().parents[1] / "data" / "geocode_cache.json"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
UA = "parking-agent-class-project/0.1 (education; contact: local)"


def _variants(addr: str) -> list[str]:
    """전체 → 구 제거 → 단독 순 폴백. '종로구 세종로 80-1'은 구 포함시 실패 확인."""
    out = [f"{addr}, 서울특별시, 대한민국", f"{addr}, 서울특별시"]
    tokens = addr.split()
    if len(tokens) > 2:
        short = " ".join(tokens[1:])
        out.append(f"{short}, 서울특별시")
    out.append(addr)
    seen, uniq = set(), []
    for v in out:
        if v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def _fetch(q: str, timeout: float) -> list:
    params = urllib.parse.urlencode(
        {"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "kr"}
    )
    req = urllib.request.Request(
        f"{NOMINATIM}?{params}",
        headers={"User-Agent": UA, "Referer": "http://localhost/"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 429:
            time.sleep(10)  # rate-limit 백오프 후 1회 재시도
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        raise


def _geocode(addr: str, timeout: float = 15.0) -> tuple[float, float] | None:
    for q in _variants(addr):
        try:
            items = _fetch(q, timeout)
        except Exception:
            return None  # 네트워크/지속 429는 다음 실행 resume에서 재시도
        if items:
            return float(items[0]["lat"]), float(items[0]["lon"])
        time.sleep(0.3)
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="서울시 주차장 지오코딩 백필")
    ap.add_argument("--limit", type=int, default=0, help="0=전체, N=앞 N건만")
    ap.add_argument("--delay", type=float, default=1.5, help="건당 대기 초")
    args = ap.parse_args()

    rows = _rows_from_cache(CACHE_PATH)
    if rows is None:
        print("캐시 없음. 먼저 python scripts/cache_seoul.py 실행")
        return 1
    cache: dict = {}
    if GEOCODE_PATH.exists():
        cache = json.loads(GEOCODE_PATH.read_text(encoding="utf-8"))

    targets = rows[: args.limit] if args.limit else rows
    done = fail = skipped = 0
    for r in targets:
        code = str(r.get("PKLT_CD", ""))
        if code in cache:
            skipped += 1
            continue
        addr = str(r.get("ADDR", "")).strip()
        if not addr:
            fail += 1
            continue
        try:
            hit = _geocode(addr)
        except Exception as e:
            print(f"[{code}] 오류: {e}")
            hit = None
        if hit:
            cache[code] = {"lat": hit[0], "lon": hit[1], "addr": addr}
            done += 1
        else:
            fail += 1
        time.sleep(args.delay)

    GEOCODE_PATH.parent.mkdir(parents=True, exist_ok=True)
    GEOCODE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    print(f"성공 {done} / 실패 {fail} / 스킵 {skipped} → {GEOCODE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
