"""파라미터 기반 결정적 랭킹. LLM은 추출/설명을 맡고, 순서는 여기서 정한다."""

from __future__ import annotations

from .geo import haversine_km
from .tools import estimate_fee_tool


def _open_at_minutes(t: str) -> int:
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def is_open(c: dict, open_at: str | None) -> bool:
    if not open_at:
        return True
    try:
        t = _open_at_minutes(open_at)
    except ValueError:
        return True
    o = _open_at_minutes(c["open_time"])
    cl = _open_at_minutes(c["close_time"])
    if o <= cl:
        return o <= t <= cl
    return t >= o or t <= cl  # 자정 넘김 운영


def rank_candidates(
    candidates: list[dict],
    lat: float,
    lon: float,
    minutes: int = 120,
    radius_km: float = 1.0,
    max_price: int | None = None,
    prefer_free: bool = False,
    sort_by: str = "recommended",
    need_disabled: bool = False,
    open_at: str | None = None,
    top_k: int = 3,
) -> list[dict]:
    scored: list[dict] = []
    for c in candidates:
        dist = haversine_km(lat, lon, c["lat"], c["lon"])
        if dist > radius_km + 1e-9:
            continue
        if need_disabled and c.get("disabled") is False:
            continue
        if not is_open(c, open_at):
            continue
        fee = estimate_fee_tool.invoke(
            {
                "base_minutes": c["base_minutes"],
                "base_fee": c["base_fee"],
                "unit_minutes": c["unit_minutes"],
                "unit_fee": c["unit_fee"],
                "minutes": minutes,
            }
        )
        if max_price is not None and fee > max_price:
            continue
        scored.append({**c, "distance_km": dist, "fee": fee})

    if not scored:
        return []

    max_d = max(s["distance_km"] for s in scored) or 1.0
    max_f = max(s["fee"] for s in scored) or 1

    for s in scored:
        nd = s["distance_km"] / max_d
        nf = s["fee"] / max_f
        # 주어지지 않은 파라미터는 LLM 내재 선호(recommended 가중치)를 따름
        base = 0.5 * nd + 0.5 * nf
        if s["free"]:
            base -= 0.08
        if prefer_free and s["free"]:
            base -= 0.5
        s["_score"] = base

    if sort_by == "distance":
        scored.sort(key=lambda s: (s["distance_km"], s["fee"]))
    elif sort_by == "price":
        scored.sort(key=lambda s: (s["fee"], s["distance_km"]))
    elif sort_by == "free_first":
        scored.sort(key=lambda s: (not s["free"], s["fee"], s["distance_km"]))
    else:  # recommended
        scored.sort(key=lambda s: (s["_score"], s["fee"], s["distance_km"]))

    out = []
    for i, s in enumerate(scored[:top_k], 1):
        out.append(
            {
                "rank": i,
                "id": s["id"],
                "name": s["name"],
                "distance_m": int(s["distance_km"] * 1000),
                "fee": s["fee"],
                "free": s["free"],
                "open": f'{s["open_time"]}~{s["close_time"]}',
                "score": round(s["_score"], 4),
                "base_minutes": s["base_minutes"],
                "base_fee": s["base_fee"],
                "unit_minutes": s["unit_minutes"],
                "unit_fee": s["unit_fee"],
                "disabled": s.get("disabled"),
                "free_now": (s.get("realtime") or {}).get("free_now")
                if isinstance(s.get("realtime"), dict)
                else None,
            }
        )
    return out
