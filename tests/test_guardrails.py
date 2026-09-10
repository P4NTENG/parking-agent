import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.guardrails import check_request
from parking_agent.schemas import RankingParams


def test_no_place_blocked():
    ok, msg, _ = check_request(RankingParams(place=None))
    assert ok is False and "어느 장소" in msg


def test_minutes_clamped():
    ok, msg, fixed = check_request(RankingParams(place="강남역", minutes=9999))
    assert ok is True and fixed.minutes == 1440 and "보정" in msg


def test_radius_clamped():
    ok, _, fixed = check_request(RankingParams(place="강남역", radius_km=50.0))
    assert ok is True and fixed.radius_km == 10.0


def test_negative_price_cleared():
    ok, _, fixed = check_request(RankingParams(place="강남역", max_price=-100))
    assert ok is True and fixed.max_price is None


def test_valid_passthrough():
    ok, msg, fixed = check_request(RankingParams(place="강남역", minutes=60))
    assert ok is True and msg == "" and fixed.minutes == 60
