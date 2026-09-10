"""LangChain @tool 기반 도우미. 강의 §3 Tool Calling 작성법 준수.

작성법: 함수 작성 → 타입 힌팅 → docstring 설명 → @tool 데코레이터.
파이프라인은 결정적 순서로 `tool.invoke({...})` 직접 호출한다
(에이전트 루프가 아니라 코드가 순서를 정해 검증 용이).
`langchain.tools` 대신 설치된 `langchain_core.tools`의 동일 데코레이터 사용.
"""

from __future__ import annotations

import os

from langchain_core.tools import tool

from .data_loader import load_candidates
from .fee import estimate_fee
from .geo import PLACE_COORDS, haversine_km


@tool
def geocode_place_tool(place: str) -> dict:
    """장소명을 위경도로 변환한다.

    Args:
        place: 기준 장소명 (예: '강남역')
    """
    q = (place or "").strip()
    if q in PLACE_COORDS:
        lat, lon = PLACE_COORDS[q]
        return {"lat": lat, "lon": lon, "matched": q}
    for name, (lat, lon) in PLACE_COORDS.items():
        if name in q or q in name:
            return {"lat": lat, "lon": lon, "matched": name}
    return {"lat": None, "lon": None, "matched": None}


@tool
def search_parking_tool(lat: float, lon: float, radius_km: float = 1.0) -> list:
    """위경도 반경 내 주차장 후보를 거리순으로 조회한다.

    Args:
        lat: 기준 위도
        lon: 기준 경도
        radius_km: 검색 반경(km)
    """
    source = os.getenv("PARKING_SOURCE", "mock").strip().lower()
    if source == "seoul":
        try:
            from .seoul_api import load_seoul_candidates
        except ImportError as e:
            raise RuntimeError(
                "PARKING_SOURCE=seoul이지만 parking_agent.seoul_api 모듈이 없다. "
                "docs/SEOUL_API.md §5 순서대로 seoul_api.py를 먼저 구현하라."
            ) from e
        candidates = load_seoul_candidates()
    else:
        candidates = load_candidates()
    out = []
    for c in candidates:
        try:
            dist = haversine_km(lat, lon, float(c["lat"]), float(c["lon"]))
        except (TypeError, ValueError, KeyError):
            continue
        if dist <= radius_km + 1e-9:
            out.append({**c, "distance_km": dist})
    out.sort(key=lambda c: c["distance_km"])
    return out


@tool
def estimate_fee_tool(
    base_minutes: int, base_fee: int, unit_minutes: int, unit_fee: int, minutes: int
) -> int:
    """주차 요금을 계산한다. 기본시간 내면 기본요금, 초과분은 올림.

    Args:
        base_minutes: 기본 시간(분)
        base_fee: 기본 요금(원)
        unit_minutes: 추가 단위 시간(분)
        unit_fee: 추가 단위 요금(원)
        minutes: 실제 체류 시간(분)
    """
    return estimate_fee(base_minutes, base_fee, unit_minutes, unit_fee, minutes)


PARKING_TOOLS = [geocode_place_tool, search_parking_tool, estimate_fee_tool]
