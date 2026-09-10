"""Mock 지오코딩. 실제 단계에서 카카오/네이버 API로 교체."""

from __future__ import annotations

import math

PLACE_COORDS: dict[str, tuple[float, float]] = {
    "강남역": (37.4979, 127.0276),
    "홍대입구": (37.5577, 126.9245),
    "홍대": (37.5577, 126.9245),
    "시청": (37.5663, 126.9779),
    "역삼역": (37.5000, 127.0360),
}


def geocode_place(place: str | None) -> tuple[float, float] | None:
    if not place:
        return None
    q = place.strip()
    if q in PLACE_COORDS:
        return PLACE_COORDS[q]
    for name, coord in PLACE_COORDS.items():
        if name in q or q in name:
            return coord
    return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))
