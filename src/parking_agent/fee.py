"""요금 계산 순수함수. LLM 없이 단위테스트 가능."""

from __future__ import annotations

import math


def estimate_fee(
    base_minutes: int,
    base_fee: int,
    unit_minutes: int,
    unit_fee: int,
    minutes: int,
) -> int:
    """기본시간 내면 기본요금, 초과분은 올림 계산. 무료면 0."""
    if minutes <= 0:
        return 0
    if base_fee == 0 and unit_fee == 0:
        return 0
    if minutes <= base_minutes:
        return base_fee
    if unit_minutes <= 0:
        return base_fee
    extra = minutes - base_minutes
    units = math.ceil(extra / unit_minutes)
    return base_fee + units * unit_fee


def fee_formula(
    base_minutes: int, base_fee: int, unit_minutes: int, unit_fee: int, minutes: int
) -> str:
    total = estimate_fee(base_minutes, base_fee, unit_minutes, unit_fee, minutes)
    if total == 0:
        return f"무료 ({minutes}분)"
    if minutes <= base_minutes:
        return f"{base_fee}원 (기본 {base_minutes}분 내)"
    extra = minutes - base_minutes
    units = math.ceil(extra / unit_minutes) if unit_minutes else 0
    return (
        f"{total}원 = 기본 {base_fee}원 + 추가 {unit_fee}원 x {units}회 "
        f"(초과 {extra}분/{unit_minutes}분 단위)"
    )
