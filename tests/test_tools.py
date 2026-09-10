import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.tools import (
    PARKING_TOOLS,
    estimate_fee_tool,
    geocode_place_tool,
    search_parking_tool,
)


def test_geocode_known():
    out = geocode_place_tool.invoke({"place": "강남역"})
    assert out["lat"] == 37.4979 and out["matched"] == "강남역"


def test_geocode_unknown():
    out = geocode_place_tool.invoke({"place": "없는지명ㅁㅁ"})
    assert out["lat"] is None and out["matched"] is None


def test_fee_tool():
    assert estimate_fee_tool.invoke(
        {
            "base_minutes": 30,
            "base_fee": 2000,
            "unit_minutes": 15,
            "unit_fee": 800,
            "minutes": 40,
        }
    ) == 2800


def test_search_tool_sorted():
    rows = search_parking_tool.invoke({"lat": 37.4979, "lon": 127.0276, "radius_km": 1.0})
    assert len(rows) >= 2
    dists = [r["distance_km"] for r in rows]
    assert dists == sorted(dists)


def test_tool_registry():
    assert {t.name for t in PARKING_TOOLS} == {
        "geocode_place_tool",
        "search_parking_tool",
        "estimate_fee_tool",
    }
