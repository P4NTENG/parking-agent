"""키 없이 실행 가능한 자동 검증. 추출→랭킹→리랭킹 시나리오."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# 키가 있어도 규칙 기반 경로로 고정 → 결정적 검증 (LLM 품질은 demo/수동으로 별도 확인)
os.environ.setdefault("PARKING_AGENT_NO_LLM", "1")
os.environ.setdefault("PARKING_SOURCE", "mock")
os.environ.setdefault("LLM_STREAM", "false")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.geo import geocode_place
from parking_agent.pipeline import run_turn
from parking_agent.schemas import RankingParams

PASS, FAIL = "PASS", "FAIL"
results: list[tuple[str, str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    results.append((name, PASS if cond else FAIL, detail))
    print(f"[{results[-1][1]}] {name} {detail}")


def main() -> int:
    # S1: 기본 질의 → 장소/시간 추출 + 랭킹 + 요금 근거
    s1 = run_turn("강남역 근처 2시간 주차 알려줘")
    check("S1.추출 place/minutes", s1["params"].place == "강남역" and s1["params"].minutes == 120,
          str(s1["params"].model_dump()))
    check("S1.랭킹 2~3건", 2 <= len(s1["ranked"]) <= 3, str([r["id"] for r in s1["ranked"]]))
    check("S1.요금 포함", "원" in s1["answer"] or "무료" in s1["answer"], "")

    # S2: 무료 선호 → free_first + 무료 후보 최상단
    s2 = run_turn("홍대입구 근처 무료 위주로 1시간")
    check("S2.무료 추출", s2["params"].prefer_free and s2["params"].sort_by == "free_first",
          str(s2["params"].model_dump()))
    check("S2.무료 최상단", bool(s2["ranked"]) and s2["ranked"][0]["free"], str([r["id"] for r in s2["ranked"]]))

    # S3: 불만 → 리랭킹 (비싸 → price 정렬로 전환)
    s3a = run_turn("강남역 근처 2시간 주차 알려줘")
    s3b = run_turn("너무 비싸, 저렴한 걸로 보여줘", s3a["params"])
    check("S3.리랭킹 price 전환", s3b["params"].sort_by == "price", str(s3b["params"].model_dump()))
    fees = [r["fee"] for r in s3b["ranked"]]
    check("S3.요금 오름차순", fees == sorted(fees), str(fees))

    # S4: 구체 정보 추가 → 시간/장소 유지 + minutes 갱신
    s4 = run_turn("30분만 주차할 거야", s3a["params"])
    check("S4.시간 갱신+장소 유지", s4["params"].minutes == 30 and s4["params"].place == "강남역",
          str(s4["params"].model_dump()))

    # S5: 미지정 장소 → 명확화 질문 (에러 스택 노출 금지)
    s5 = run_turn("주차장 알려줘")
    check("S5.장소 명확화", s5["needs_clarification"] and "어느 장소" in s5["answer"], s5["answer"][:40])

    # S6: 모르는 장소 → 폴백 안내 (장소 명확화 또는 지오코딩 실패 모두 허용)
    s6 = run_turn("없는지명ㅁㅁ 근처 1시간")
    check("S6.지오코딩 폴백", s6["needs_clarification"], s6["answer"][:40])
    # S6b: geocode_fail 분기 직접 검증 (추출기가 장소를 잡았으나 좌표 없는 경우)
    check("S6b.geocode None", geocode_place("없는지명ㅁㅁ") is None, "")
    s6b = run_turn("1시간 주차 알려줘", RankingParams(place="없는지명ㅁㅁ"))
    # prev 병합 특성상 place가 유지되면 geocode_fail, 아니면 S6와 동일하게 명확화
    check("S6b.지오코딩 실패 처리", s6b["needs_clarification"], s6b["answer"][:40])

    failed = [r for r in results if r[1] == FAIL]
    print(f"\n{len(results)-len(failed)}/{len(results)} 통과 (rule 기반, 키 불필요)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
