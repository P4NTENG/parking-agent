"""추출 → 조회(Mock) → 랭킹 → 응답 파이프라인. 리랭킹은 prev 병합으로 처리."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from parking_agent.data_loader import load_candidates  # noqa: E402
from parking_agent.extractor import extract_params  # noqa: E402
from parking_agent.geo import geocode_place  # noqa: E402
from parking_agent.rank import rank_candidates  # noqa: E402
from parking_agent.responder import format_answer  # noqa: E402
from parking_agent.schemas import RankingParams  # noqa: E402


def run_turn(
    user_text: str, prev: RankingParams | None = None
) -> dict:
    params, source = extract_params(user_text, prev)
    trace: dict = {"source": source, "params": params.model_dump()}

    if not params.place:
        return {
            "params": params,
            "ranked": [],
            "answer": "어느 장소 근처인지 알려주세요. 예: “강남역 근처 2시간 주차 알려줘”",
            "trace": {**trace, "error": "no_place"},
            "needs_clarification": True,
        }

    coord = geocode_place(params.place)
    if coord is None:
        return {
            "params": params,
            "ranked": [],
            "answer": (
                f"‘{params.place}’ 좌표를 찾지 못했어요. "
                "강남역/홍대입구/시청 중에서 골라 주세요. (Mock 범위)"
            ),
            "trace": {**trace, "error": "geocode_fail"},
            "needs_clarification": True,
        }
    lat, lon = coord
    candidates = load_candidates()
    ranked = rank_candidates(
        candidates,
        lat,
        lon,
        minutes=params.minutes,
        radius_km=params.radius_km,
        max_price=params.max_price,
        prefer_free=params.prefer_free,
        sort_by=params.sort_by,
        need_disabled=params.need_disabled,
        open_at=params.open_at,
        top_k=params.top_k,
    )
    trace.update(
        {"coord": coord, "candidates": len(candidates), "ranked_ids": [r["id"] for r in ranked]}
    )
    answer = format_answer(user_text, params, ranked, trace)
    return {
        "params": params,
        "ranked": ranked,
        "answer": answer,
        "trace": trace,
        "needs_clarification": False,
    }
