# parking-agent

운전자용 주차장 추천/안내 에이전트. 현재 단계 목표는 **기능 고도화가 아닌 최소 파이프라인 검증**이다.

> 범위: 백엔드 에이전트 우선 (LangChain만 사용, LangGraph 사용 금지 — 수업 진도 맞춤)

## 목표 (이번 세션)

실제 계획한 에이전트 파이프라인이 예상대로 동작하는지 검증한다:

1. 사용자 질의 → LLM이 올바른 Tool을 올바른 인자로 호출하는가?
2. Tool 결과 → LLM이 요금/거리/운영 기준으로 추천을 조합하는가?
3. Mock 데이터로 end-to-end가 끊김 없이 도는가?

## 최소 파이프라인 (LangChain)

```
사용자 질의 ("강남역 근처 2시간 주차")
 → ChatOpenAI + ChatPromptTemplate
 → AgentExecutor (tool-calling, ReAct 스타일)
   ├─ geocode_place_mock (지명 → 위경도)
   ├─ search_parking_mock (반경 내 후보 3~5건)
   └─ estimate_fee (기본요금 + 추가요금 계산, 순수함수)
 → 최종 답변 (추천 1~3순위 + 근거: 요금/거리/운영시간)
```

- LangGraph (`StateGraph`, `ToolNode`, `MessagesState`)는 이번 단계에서 도입하지 않는다.
- 외부 API (`data.go.kr`, 카카오/네이버 지도)는 연동하지 않고, `Mock`으로 대체한다.
- 검증 통과 후 다음 단계에서 실제 API 클라이언트로 교체한다.

## 빠른 시작 (예정)

```bash
# 1. 의존성 설치 (uv 권장, pip도 가능)
uv sync
# 또는
pip install -r requirements.txt

# 2. 환경변수
cp .env.example .env
# OPENAI_API_KEY / OPENAI_BASE_URL (수업용 DeepSeek 호환 endpoint 가능)

# 3. 최소 파이프라인 실행
python scripts/demo_cli.py "강남역 근처 2시간 주차 알려줘"

# 4. 검증 시나리오 실행
python scripts/verify_pipeline.py
```

## 검증 기준

- [ ] `geocode → search → estimate` 순서로 Tool 호출됨
- [ ] Tool 인자(lat/lon/minutes)가 질의에서 올바르게 추출됨
- [ ] Tool 실패 시 에러 메시지가 아닌 폴백 답변 반환
- [ ] 최종 답변에 요금 근거(계산식) 포함
- [ ] 수업용 모델(Flash급 저비용)으로도 3회 연속 성공

자세한 단계별 계획은 [PLAN.md](./PLAN.md) 참조.
