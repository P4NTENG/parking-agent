# PLAN — 최소 파이프라인 검증 계획

> 작성일: 2026-09-10 / 작업 폴더: `D:\git\parking-agent` (git init 완료, 빈 repo에서 시작)
> 원칙 1: 기능 고도화보다 **파이프라인 동작 검증**이 우선
> 원칙 2: **LangChain까지만 사용. LangGraph 금지** (수업이 LangChain 프레임워크부터 시작했으므로)

## 1. 배경

- 이전에 논의된 풀스펙(실시간 API, 랭킹 고도화, FE)은 이번 단계에서 제외한다.
- 수업 진도에 맞춰 `langchain-core` + `langchain-openai`의 Agent 개념
  (`ChatPromptTemplate` → `Tool` → `AgentExecutor`)이 실제로 도는지 확인하는 것이 목표다.
- 외부 변수(공공데이터 키 발급, 지도 API 쿼터)를 배제하기 위해 모든 외부 I/O는 Mock으로 시작한다.

## 2. 검증 대상 파이프라인 (최소 구성)

### 2.1 흐름

1. 입력 정규화: 사용자 질의 + (선택) 체류시간 `minutes` 추출. 기본값 120분.
2. `geocode_place_mock`: "강남역" 같은 지명 → 고정 위경도 매핑 (딕셔너리 5~10개).
3. `search_parking_mock`: 위경도 + 반경(기본 1km) → `data/seed_sample.csv`에서 3~5건 반환. 거리(haversine) 정렬.
4. `estimate_fee`: 각 후보에 대해 `기본요금 + ceil((minutes-기본시간)/추가단위)*추가요금` 계산. 순수함수이므로 단위테스트 가능.
5. LLM 종합: 후보 + 요금을 근거로 1~3순위 추천. 요금 계산식 명시.

### 2.2 LangChain 구성 (LangGraph 없음)

- `ChatOpenAI(model=수업용 Flash급, temperature=0)` — `langchain-openai`
- `ChatPromptTemplate` — 시스템 프롬프트에 "반드시 Tool을 써서 근거를 만들 것" 지시
- `Tool` 3개 — `@tool` 데코레이터 (`langchain-core`)
- `AgentExecutor` — `create_tool_calling_agent()` + `AgentExecutor(..., verbose=True)` 조합
- 실행 확인은 `scripts/demo_cli.py`의 단일 질의 + `scripts/verify_pipeline.py`의 5개 시나리오

왜 `AgentExecutor`인가: 수업에서 배우는 고전 LangChain Agent 실행기이며,
`StateGraph/ToolNode` 같은 LangGraph 개념 없이도 Tool 호출 루프를 검증할 수 있다.

## 3. 파일 구성 (최소)

```
pyproject.toml 또는 requirements.txt
  langchain-core, langchain-openai, python-dotenv, (선택) pydantic
.env.example
  OPENAI_API_KEY= / OPENAI_BASE_URL= / MODEL_NAME=
src/parking_agent/
  __init__.py
  tools_mock.py      # geocode/search/fee 3개 Mock Tool
  fee.py             # estimate_fee 순수함수 (tools_mock에서 import)
  prompt.py          # ChatPromptTemplate 정의
  agent.py           # create_tool_calling_agent + AgentExecutor 조립
  data_loader.py     # seed_sample.csv 로더 + haversine
data/
  seed_sample.csv    # 수기 10건 (주차장명, 위도, 경도, 기본시간/요금, 추가단위/요금, 운영시간)
scripts/
  demo_cli.py        # 단일 질의 실행, verbose 로그 출력
  verify_pipeline.py # 5개 시나리오 자동 검증 (Tool 호출 여부 + 요금 포함 여부)
tests/
  test_fee.py        # estimate_fee 경계값 테스트 5건
```

초기 `seed_sample.csv` 컬럼:
`id, name, lat, lon, base_minutes, base_fee, unit_minutes, unit_fee, open_time, close_time`

## 4. 단계별 작업 (검증 중심, 총 3~4일 분량을 1일 MVP로 압축 가능)

### Step 0 — 프로젝트 뼈대 (0.5h)
- [ ] `pyproject.toml` 또는 `requirements.txt` 생성
- [ ] `.env.example`, `.gitignore` (완료), `README.md` (완료)
- [ ] `python -c "import langchain_core; print('ok')"`로 설치 확인

### Step 1 — 순수함수 + Mock 데이터 (1h)
- [ ] `data/seed_sample.csv` 10건 수기 작성 (강남역 주변 가상 좌표)
- [ ] `fee.py: estimate_fee(base_m, base_f, unit_m, unit_f, minutes)` 구현
- [ ] `tests/test_fee.py`: 0분/경계/초과/장시간 5건. `pytest` 통과가 1차 게이트.

### Step 2 — Mock Tool 3종 (1h)
- [ ] `geocode_place_mock("강남역") → (37.4979, 127.0276)` 딕셔너리 방식
- [ ] `search_parking_mock(lat, lon, radius_km=1.0)` → 거리순 3건 + `fee` 미계산 상태로 반환
- [ ] `@tool` 데코레이터 부착, docstring에 인자 설명 명시 (LLM이 인자를 맞추는 데 중요)

### Step 3 — Agent 조립 (1h)
- [ ] `prompt.py`: 시스템 메시지에 "추측 금지, Tool 결과만 근거로 사용, 요금 계산식 표시" 명시
- [ ] `agent.py`: `create_tool_calling_agent(llm, tools, prompt)` + `AgentExecutor`
- [ ] `demo_cli.py`: 질의 1건 실행, `verbose=True`로 Tool 호출 로그 육안 확인

### Step 4 — 검증 스크립트 (1h)
- [ ] `verify_pipeline.py` 시나리오 5건:
  1. "강남역 근처 2시간" → 3개 Tool 모두 호출, 요금 포함
  2. "홍대입구 30분 무료 위주" → geocode + search 호출, 무료 후보 우선 언급
  3. "없는지명ㅁㅁ 1시간" → geocode 실패 → 폴백 답변 (에러 스택 노출 금지)
  4. "30분 vs 3시간 요금 비교해줘" → estimate 2회 이상 호출
  5. "심야(23시) 주차 가능?" → 운영시간 필터 언급 (Mock이므로 시간 비교 로직만 확인)
- [ ] 판정 기준: Tool 호출 순서 로그 + 최종 답변에 `원`, `m/km`, 후보명 포함 여부 (문자열 assert)
- [ ] 3회 연속 통과 시 검증 완료로 간주

## 5. 명시적 비범위 (이번 단계에서 하지 않는 것)

- LangGraph (`StateGraph`, `ToolNode`, `MemorySaver`, `stream`) 도입 금지
- 실제 외부 API 연동 (`B553881`, 카카오 지도, 서울시 API) 금지 — Mock 통과 후 별도 이슈로 분리
- DB/벡터검색/랭킹 모델/프론트엔드 금지
- 요금 정확도 고도화(할증/1일권/월정기) 금지 — 기본+추가 요금만

## 6. 다음 단계로 넘어가는 조건 (Definition of Done)

- [ ] `pytest tests/test_fee.py` 통과
- [ ] `python scripts/verify_pipeline.py` 5/5 통과 × 3회 연속
- [ ] `verbose` 로그에서 Tool 인자 오류 0건
- [ ] README의 빠른 시작 절차대로 제3자가 재현 가능
- [ ] 위 4개 충족 시 커밋 `feat: minimal langchain pipeline verified` 후 실제 API 연동 이슈 생성

## 7. 오픈 질문 (구현 중 결정)

1. 수업용 모델 endpoint가 DeepSeek 호환(`base_url` 커스텀)인가, OpenAI 정식인가? → `.env.example`에 둘 다 주석으로 남김.
2. 패키지 관리: 수업이 `pip + requirements.txt`면 그것을, 아니면 `uv + pyproject`로 통일. (둘 다 적어두고 하나 선택)
3. 대상 지역 Mock 중심지: 강남역 고정 vs 학교 주변? → `seed_sample.csv` 중심 좌표 1개만 먼저 결정하면 됨.

## 8. 예상 리스크 + 대응

| 리스크 | 대응 |
|---|---|
| LLM이 Tool을 건너뛰고 할루시네이션 | 시스템 프롬프트에 "Tool 미사용 답변 금지" + `verify`에서 요금 숫자 assert |
| Tool 인자(lat/lon) 추출 실패 | `geocode`를 첫 강제 호출 대상으로 프롬프트에 명시, 실패 시 폴백 |
| 수업용 저비용 모델의 tool-calling 불안정 | `temperature=0`, Tool 설명을 짧고 명확하게, 재시도 1회 |
| 범위 creep (실시간/랭킹 욕심) | 본 문서 섹션 5를 기준으로 리뷰 시 반려 |
