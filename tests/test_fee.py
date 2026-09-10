import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.fee import estimate_fee


def test_base_included():
    assert estimate_fee(30, 2000, 15, 800, 30) == 2000


def test_extra_roundup():
    # 40분 = 기본30 + 초과10 -> 1회 추가
    assert estimate_fee(30, 2000, 15, 800, 40) == 2800


def test_exact_unit():
    assert estimate_fee(30, 2000, 15, 800, 45) == 2800


def test_free():
    assert estimate_fee(60, 0, 15, 0, 120) == 0


def test_zero_minutes():
    assert estimate_fee(30, 2000, 15, 800, 0) == 0
