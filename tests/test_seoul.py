import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.extractor import extract_params
from parking_agent.rank import rank_candidates
from parking_agent.schemas import RankingParams
from parking_agent.seoul_api import load_seoul_candidates, parse_row


def _row(**kw):
    base = {
        "PKLT_CD": "1",
        "PKLT_NM": "테스트",
        "ADDR": "종로구 세종로 80-1",
        "PAY_YN": "Y",
        "PRK_STTS_YN": "1",
        "TPKCT": 100,
        "NOW_PRK_VHCL_CNT": 30,
        "NOW_PRK_VHCL_UPDT_TM": "2026-09-11 00:00:00",
        "BSC_PRK_CRG": 1000,
        "BSC_PRK_HR": 30,
        "ADD_PRK_CRG": 500,
        "ADD_PRK_HR": 15,
        "WD_OPER_BGNG_TM": "0000",
        "WD_OPER_END_TM": "2400",
    }
    base.update(kw)
    return base


def test_disabled_unknown_passes_filter():
    cands = [
        {
            "id": "1",
            "name": "t",
            "lat": 37.5,
            "lon": 127.0,
            "base_minutes": 30,
            "base_fee": 1000,
            "unit_minutes": 15,
            "unit_fee": 500,
            "open_time": "00:00",
            "close_time": "23:59",
            "free": False,
            "disabled": None,  # 서울시 원천: 미상 → 통과해야 함
        }
    ]
    ranked = rank_candidates(
        cands, 37.5, 127.0, minutes=60, need_disabled=True
    )
    assert len(ranked) == 1 and ranked[0]["disabled"] is None


def test_disabled_false_still_filtered():
    cands = [
        {
            "id": "1",
            "name": "t",
            "lat": 37.5,
            "lon": 127.0,
            "base_minutes": 30,
            "base_fee": 1000,
            "unit_minutes": 15,
            "unit_fee": 500,
            "open_time": "00:00",
            "close_time": "23:59",
            "free": False,
            "disabled": False,
        }
    ]
    assert rank_candidates(cands, 37.5, 127.0, need_disabled=True) == []


def test_realtime_passthrough():
    parsed = parse_row(_row())
    assert parsed["realtime"]["free_now"] == 70
    assert parsed["disabled"] is None
    ranked = rank_candidates(
        [
            {
                "id": "1",
                "name": "t",
                "lat": 37.5,
                "lon": 127.0,
                "base_minutes": 30,
                "base_fee": 1000,
                "unit_minutes": 15,
                "unit_fee": 500,
                "open_time": "00:00",
                "close_time": "23:59",
                "free": False,
                "disabled": None,
                "realtime": parsed["realtime"],
            }
        ],
        37.5,
        127.0,
    )
    assert ranked[0]["free_now"] == 70


def test_negation_resets_free():
    import os

    os.environ["PARKING_AGENT_NO_LLM"] = "1"
    p, src = extract_params("홍대입구 무료로 1시간")
    assert src == "rule" and p.prefer_free is True
    p2, _ = extract_params("무료 말고 일반으로 보여줘", p)
    assert p2.prefer_free is False and p2.sort_by == "recommended"
    assert p2.place == "홍대입구"


def test_geocode_cache_merge(tmp_path):
    import json

    rows = [_row()]
    cache = tmp_path / "geo.json"
    cache.write_text(
        json.dumps({"1": {"lat": 37.1, "lon": 127.1}}), encoding="utf-8"
    )
    import parking_agent.seoul_api as api

    orig = api.GEOCODE_PATH
    api.GEOCODE_PATH = cache
    try:
        out = api.load_seoul_candidates(rows=rows, cache_path=None)
    finally:
        api.GEOCODE_PATH = orig
    assert out[0]["lat"] == 37.1 and out[0]["needs_geocode"] is False
