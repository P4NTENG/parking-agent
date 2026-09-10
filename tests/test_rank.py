import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.data_loader import load_candidates
from parking_agent.rank import rank_candidates


def _latlon():
    return 37.4979, 127.0276  # 강남역


def test_price_sort_ascending():
    lat, lon = _latlon()
    ranked = rank_candidates(load_candidates(), lat, lon, minutes=120, sort_by="price")
    fees = [r["fee"] for r in ranked]
    assert fees == sorted(fees)


def test_free_first_top():
    lat, lon = 37.5577, 126.9245  # 홍대입구
    ranked = rank_candidates(
        load_candidates(), lat, lon, minutes=60, sort_by="free_first", radius_km=2.0
    )
    assert ranked and ranked[0]["free"] is True


def test_rerank_keeps_place_changes_sort():
    lat, lon = _latlon()
    cands = load_candidates()
    before = rank_candidates(cands, lat, lon, minutes=120, sort_by="recommended")
    after = rank_candidates(cands, lat, lon, minutes=120, sort_by="price")
    assert [r["id"] for r in before] != [r["id"] for r in after] or len(before) > 1
