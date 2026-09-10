"""대화형 데모: 질의 → 추출/랭킹 → 불만/추가정보 입력시 리랭킹."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from parking_agent.pipeline import run_turn

BANNER = """=== parking-agent 최소 파이프라인 데모 ===
예: 강남역 근처 2시간 주차 알려줘
리랭킹 예: 너무 비싸, 저렴한 걸로 / 더 가까운 걸로 / 무료로 / 30분만
종료: quit
"""


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    print(BANNER)
    once = "--once" in sys.argv
    prev = None
    first = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else None
    pending = [first] if first else []
    while True:
        try:
            text = pending.pop(0) if pending else input("나: ").strip()
        except EOFError:
            break
        if not text:
            continue
        if text.lower() in ("quit", "exit", "q"):
            break
        out = run_turn(text, prev)
        prev = out["params"]
        print(f"\n[파라미터] {out['params'].model_dump()} (추출:{out['trace'].get('source')})")
        if out["ranked"]:
            print(f"[랭킹] {' > '.join(r['id'] for r in out['ranked'])}")
        print(f"\n에이전트: {out['answer']}\n")
        if once and not pending:
            break


if __name__ == "__main__":
    main()
