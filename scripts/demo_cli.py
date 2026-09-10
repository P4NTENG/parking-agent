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
    no_stream = "--no-stream" in sys.argv
    stream = not no_stream
    prev = None
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    first = args[0] if args else None
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

        emitted = [0]

        def _on_token(token: str) -> None:
            emitted[0] += 1
            print(token, end="", flush=True)

        if stream:
            # 진짜 LLM 토큰 스트리밍: 답변 토큰이 오는 대로 출력.
            # 파라미터/랭킹은 추출 후 알 수 있어 답변 뒤에 표시한다.
            print("\n에이전트: ", end="", flush=True)
            out = run_turn(text, prev, stream=True, on_token=_on_token)
            prev = out["params"]
            print()  # 스트림 종료 줄바꿈
            if emitted[0] == 0:
                # 명확화/폴백 경로는 스트리밍 토큰이 없으므로 완성본 출력
                print(f"에이전트: {out['answer']}")
            print(f"[파라미터] {out['params'].model_dump()} (추출:{out['trace'].get('source')})")
            if out["ranked"]:
                print(f"[랭킹] {' > '.join(r['id'] for r in out['ranked'])}")
            print()
        else:
            out = run_turn(text, prev, stream=False)
            prev = out["params"]
            print(f"\n[파라미터] {out['params'].model_dump()} (추출:{out['trace'].get('source')})")
            if out["ranked"]:
                print(f"[랭킹] {' > '.join(r['id'] for r in out['ranked'])}")
            print(f"\n에이전트: {out['answer']}\n")
        if once and not pending:
            break


if __name__ == "__main__":
    main()
