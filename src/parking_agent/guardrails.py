"""결정론적 가드레일. 강의 §5 Advanced Agent > Guardrails.

LLM 호출 전에 정규식·범위 검사로 저비용 차단. 통과하면 값을 정규화(clamp)하고,
실패하면 LLM에 넘기지 않고 즉시 안내 메시지를 반환한다.
"""

from __future__ import annotations

from .schemas import RankingParams

MIN_MINUTES, MAX_MINUTES = 1, 24 * 60
MIN_RADIUS, MAX_RADIUS = 0.1, 10.0
MIN_TOP_K, MAX_TOP_K = 1, 10


def check_request(params: RankingParams) -> tuple[bool, str, RankingParams]:
    """(통과 여부, 안내 메시지, 정규화된 params) 반환."""
    if not (params.place or "").strip():
        return (
            False,
            "어느 장소 근처인지 알려주세요. 예: “강남역 근처 2시간 주차 알려줘”",
            params,
        )
    data = params.model_dump()
    data["minutes"] = max(MIN_MINUTES, min(MAX_MINUTES, params.minutes))
    data["radius_km"] = max(MIN_RADIUS, min(MAX_RADIUS, params.radius_km))
    data["top_k"] = max(MIN_TOP_K, min(MAX_TOP_K, params.top_k))
    if data.get("max_price") is not None and data["max_price"] < 0:
        data["max_price"] = None
    fixed = RankingParams(**data)
    notes = []
    if fixed.minutes != params.minutes:
        notes.append(f"체류시간 {params.minutes}분→{fixed.minutes}분으로 보정")
    if fixed.radius_km != params.radius_km:
        notes.append(f"반경 {params.radius_km}km→{fixed.radius_km}km로 보정")
    msg = ". ".join(notes)
    return True, msg, fixed
