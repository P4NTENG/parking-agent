# 강의 정리 — AI캠퍼스 생성형AI 5. 생성형 AI 서비스 개발 (이미애)

> 교재: `docs/(교재)AI캠퍼스_생성형AI_5.생성형 AI 서비스 개발_이미애.pdf` (172p, SK AX)
> 정리일: 2026-09-11. 주차 에이전트 프로젝트의 수업 정합성 판단용.

## 1. Introduction
- AI 제품 6단계 진화, RAG / Pre-Processing 개념
- Agent 정의와 ReAct (Reasoning → Acting), Agent vs LLM
- OWASP LLM 보안, AI Application 개발 체크리스트 8영역
  (환각방지·프롬프트인젝션·RBAC·편향감사·설명가능성·PII·감사로그·유해콘텐츠)

## 2. LLM과 친해지기
- Hugging Face / Google GenAI / OpenAI SDK 사용법, Gemini–OpenAI SDK 비교

## 3. LangChain 기본 컴포넌트
- **Chat Model**: `init_chat_model()`, 파라미터, 호출
- **Message**: Human/AI/ToolMessage 활용
- **Prompt**: `PromptTemplate`, `MessagePlaceholder`
- **Structured Output**: Pydantic, JSON Schema
- **LCEL**: `Prompt | Model | OutputParser` 체인, Runnable 인터페이스,
  `RunnableBranch` 분기
- **Tool Calling**: Built-in tools/toolkit, `@tool` 커스텀 도구
  (날씨·사칙연산·알라딘 예제). 작성법 = 함수 + 타입힌팅 + docstring + 데코레이터

## 4. Basic Agent
- `from langchain.agents import create_agent` / `agent = create_agent(model, tools=[...])`
- 실행 플로우 7단계: Request → Model → Action → Tools → Observation → 종합 → Result
- **Short-term Memory**: Checkpointer + `thread_id` (같은 스레드=맥락 유지)
- **구조화된 답변**: `response_format` + `response["structured_response"]` 후처리

## 5. Advanced Agent (컨텍스트 엔지니어링)
- **Runtime & State**: `messages`(실행 로그), `context`(사용자 신분증),
  `store`(장기보관), stream writer
- **Middleware**
  - Built-in: `LLMToolEmulator`, `TodoListMiddleware`, Human-in-the-loop,
    PII detection, Summarization → `middleware=[...]` 순서대로 장착
  - Custom Node-style: `@before_agent / @before_model / @after_model / @after_agent`
    (입력: `state, runtime`)
  - Custom Wrap-style: `@wrap_tool_call / @wrap_model_call` (입력: `request, handler`)
- **Guardrails**: 결정론적(정규식·키워드, `jump_to="end"`) vs 모델 기반.
  Before / After / Combine. 대표: PII·HITL·Prompt Injection·유해콘텐츠·품질체크
- **Long-term Memory**: `InMemoryStore` + `namespace = user_id::app_name`,
  `managed_keys_map`으로 키 관리, `@tool` 조회/저장 + `@wrap_model_call` 주입

## 부록. RAG / LangGraph 트랙 (학습목표에 포함)
- ETL + 벡터DB 적재, Advanced Retrieval & Re-ranking, 할루시네이션 제어
- State 기반 Cyclic Graph, Persistence + Dynamic Interrupt, Multi-Agent 오케스트레이션

## 프로젝트 시사점
- 강의 정석은 `@tool` + `create_agent`. 우리 파이프라인(구조화 추출 + 결정적 랭킹)은
  검증 용이성을 위한 변형이므로, 진도 맞춤이 필요해지면 `create_agent` 방식으로
  이전하는 것이 자연스럽다. 관련 논의는 README 파이프라인 절 참조.
- 참고 링크: https://docs.langchain.com (가이드·API·Academy는 교재 p171 목록 참조)
