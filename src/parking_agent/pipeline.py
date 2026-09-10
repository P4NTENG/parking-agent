"""추출 → 조회(Mock/서울실데이터) → 랭킹 → 응답 파이프라인. 리랭킹은 prev 병합."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from parking_agent.data_loader import load_candidates  # noqa: E402
from parking_agent.extractor import extract_params  # noqa: E402
from parking_agent.geo import geocode_place  # noqa: E402
from parking_agent.rank import rank_candidates  # noqa: E402
from parking_agent.responder import format_answer  # noqa: E402
from parking_agent.schemas import RankingParams  # noqa: E402


def _load_candidates_by_source() -> tuple[list[dict], str]:
    """PARKING_SOURCE=mock(기본)|seoul. seoul은 seoul_api 모듈 필요."""
    source = os.getenv("PARKING_SOURCE", "mock").strip().lower()
    if source == "seoul":
        try:
            from parking_agent.seoul_api import load_seoul_candidates
        except ImportError as e:
            raise RuntimeError(
                "PARKING_SOURCE=seoul이지만 parking_agent.seoul_api 모듈이 없다. "
                "docs/SEOUL_API.md §5 순서대로 seoul_api.py를 먼저 구현하라."
            ) from e
        return load_seoul_candidates(), "seoul"
    return load_candidates(), "mock"


def run_turn(
    user_text: str,
    prev: RankingParams | None = None,
    stream: bool | None = None,
    on_token: Callable[[str], None] | None = None,
) -> dict:
    """stream=None이면 LLM_STREAM env(기본 true)를 따른다."""
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
    try:
        candidates, data_source = _load_candidates_by_source()
    except RuntimeError as e:
        return {
            "params": params,
            "ranked": [],
            "answer": str(e),
            "trace": {**trace, "error": "no_data_source"},
            "needs_clarification": True,
        }
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
        {
            "coord": coord,
            "data_source": data_source,
            "candidates": len(candidates),
            "ranked_ids": [r["id"] for r in ranked],
        }
    )
    answer = format_answer(user_text, params, ranked, trace, stream=stream, on_token=on_token)
    return {
        "params": params,
        "ranked": ranked,
        "answer": answer,
        "trace": trace,
        "needs_clarification": False,
    }
