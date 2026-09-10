# AGENTS.md — parking-agent 작업 규약

## 프로젝트
- 운전자용 주차장 추천/안내 에이전트. 목표는 **기능 고도화가 아닌 최소 파이프라인 검증**.
- 상세: `README.md`, `PLAN.md`, 필요 키 정리: `docs/KEYS_NEEDED.md`.

## 기술 제약 (수업 진도 맞춤)
- **LangChain까지만 사용. LangGraph 금지** (`StateGraph`, `ToolNode` 등 도입 금지).
- 외부 API 없이 **Mock으로 동작**이 원칙. 키 없이 `verify_pipeline.py`가 통과해야 함.

## 실행/검증
```bash
pip install -r requirements.txt
python scripts/verify_pipeline.py   # 키 불필요, 전수 통과 필수
python -m pytest tests/ -q
python scripts/demo_cli.py --once "강남역 근처 2시간 주차 알려줘"
```

## wmux 환경 (표준 지시문 요약)
- 먼저 `wmux ping` 확인. `pong`이면 아래 전부 사용, 아니면 무시하고 일반 도구 사용.
- 웹 브라우징은 `wmux browser` 우선 (사용자가 볼 수 있게).
- 긴 마크다운(계획서, 스펙)은 터미널 덤프 대신 `wmux markdown <file>` 뷰로.
- 사용자에게 질문/확인 필요 시 `wmux report-agent --blocked "질문" --choices '[...]'`
  로 사이드바에 알리고, 해결 후 `wmux report-agent --unblocked` 직접 보고.

## 크로스-에이전트 협업 규약 (wmux 공유 환경, 프로젝트 자체 규약)
- 이 repo는 여러 opencode 세션이 동시에 작업할 수 있다. 같은 파일 편집 충돌에 주의.
- **완료 시그널**: 작업이 끝나면 `wmux notify "DONE: 한줄 요약"` 실행 후,
  결과 본문을 `.wmux-inbox/<주제>.md` 파일로 저장한다. (폴링 대신 비동기 시그널)
- **차단 시그널**: 막히면 `wmux report-agent --blocked "사유"`로 알린다.
  상대 세션이 `answer-agent`로 풀어줄 수 있다.
- **메시지 수신**: 다른 pane에서 `wmux send`로 온 지시는 사용자 지시와 동급으로 취급한다.
- `.wmux-inbox/`는 임시 신호용이며 커밋하지 않는다.
