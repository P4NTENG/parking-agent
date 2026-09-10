"""서울시 공영주차장 실데이터 어댑터 (GetParkingInfo).

docs/SEOUL_API.md §3 매핑표대로 원본 row를 내부 스키마로 변환한다.
내부 스키마는 data_loader.load_candidates()와 동일 + realtime 추가.
위경도는 API에 없으므로 lat/lon=0.0, needs_geocode=True (카카오 지오코딩 대기).

Mock 파이프라인과 독립 모듈. 표준라이브러리만 사용 (의존성 추가 없음).
"""

from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_URL = "http://openapi.seoul.go.kr:8088"
SERVICE = "GetParkingInfo"
CACHE_PATH = Path(__file__).resolve().parents[2] / "data" / "seoul_cache.json"


def _api_key() -> str:
    key = os.getenv("SEOUL_OPENAPI_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "SEOUL_OPENAPI_KEY가 비어 있다. .env에 서울시 인증키를 넣어라."
        )
    return key


def _get_json(url: str, timeout: float = 15.0) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_page(start: int, end: int, timeout: float = 15.0) -> tuple[list[dict], int]:
    """1 페이지 조회. (row 리스트, list_total_count) 반환."""
    url = f"{BASE_URL}/{_api_key()}/json/{SERVICE}/{start}/{end}"
    body = _get_json(url, timeout).get(SERVICE, {})
    result = body.get("RESULT", {})
    if result.get("CODE") != "INFO-000":
        raise RuntimeError(f"서울시 API 오류: {result.get('CODE')} {result.get('MESSAGE')}")
    return body.get("row", []), int(body.get("list_total_count", 0))


def fetch_all(page_size: int = 100, timeout: float = 15.0) -> list[dict]:
    """전량 페이징 조회. 122건이면 100+22, 2회 호출."""
    rows, total = fetch_page(1, page_size, timeout)
    if len(rows) >= total:
        return rows
    all_rows = list(rows)
    start = page_size + 1
    while len(all_rows) < total:
        end = min(start + page_size - 1, total)
        page, _ = fetch_page(start, end, timeout)
        if not page:
            break
        all_rows.extend(page)
        start = end + 1
    return all_rows


def _to_float(v: object, default: float = 0.0) -> float:
    try:
        return float(str(v).strip() or default)
    except (ValueError, TypeError):
        return default


def _hhmm_to_hh_mm(s: object, default: str) -> str:
    """'0900' → '09:00'. 빈값/형식오류면 default."""
    t = str(s or "").strip()
    if len(t) == 4 and t.isdigit():
        return f"{t[:2]}:{t[2:]}"
    return default


def parse_row(row: dict) -> dict:
    """원본 1행을 내부 스키마로 변환. docs/SEOUL_API.md §3."""
    base_minutes = int(_to_float(row.get("BSC_PRK_HR")))
    base_fee = int(_to_float(row.get("BSC_PRK_CRG")))
    unit_minutes = int(_to_float(row.get("ADD_PRK_HR")))
    unit_fee = int(_to_float(row.get("ADD_PRK_CRG")))
    pay_yn = str(row.get("PAY_YN", "")).strip().upper()
    free = pay_yn == "N" or (base_fee == 0 and unit_fee == 0)

    linked = str(row.get("PRK_STTS_YN", "")).strip() == "1"
    total = int(_to_float(row.get("TPKCT")))
    now = int(_to_float(row.get("NOW_PRK_VHCL_CNT")))

    return {
        "id": str(row.get("PKLT_CD", "")),
        "name": str(row.get("PKLT_NM", "")),
        "addr": str(row.get("ADDR", "")),
        "lat": 0.0,
        "lon": 0.0,
        "needs_geocode": True,
        "base_minutes": base_minutes,
        "base_fee": base_fee,
        "unit_minutes": unit_minutes,
        "unit_fee": unit_fee,
        "open_time": _hhmm_to_hh_mm(row.get("WD_OPER_BGNG_TM"), "00:00"),
        "close_time": _hhmm_to_hh_mm(row.get("WD_OPER_END_TM"), "23:59"),
        "free": free,
        "disabled": False,  # 서울시 API에 없음
        "realtime": {
            "total": total,
            "now": now,
            "free_now": (total - now) if linked else None,
            "linked": linked,
            "updated_at": str(row.get("NOW_PRK_VHCL_UPDT_TM", "") or ""),
        },
    }


def _rows_from_cache(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        body = json.load(f)
    if isinstance(body, dict):
        if SERVICE in body and isinstance(body[SERVICE], dict):
            return body[SERVICE].get("row", [])
        if isinstance(body.get("row"), list):
            return body["row"]
        if isinstance(body.get("rows"), list):
            return body["rows"]
    if isinstance(body, list):
        return body
    raise RuntimeError(f"캐시 형식 오류: {path}")


def load_seoul_candidates(
    rows: list[dict] | None = None,
    cache_path: Path | str | None = CACHE_PATH,
) -> list[dict]:
    """pipeline PARKING_SOURCE=seoul 분기용. rows > 캐시 > 실시간 순으로 소스 선택."""
    if rows is None and cache_path is not None:
        rows = _rows_from_cache(Path(cache_path))
    if rows is None:
        rows = fetch_all()
    return [parse_row(r) for r in rows]
