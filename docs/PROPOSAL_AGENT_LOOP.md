# 제안: 에이전트 루프 도입 (AgentExecutor / create_agent)

> 상태: 제안 (미결정). 작성일: 2026-09-11.
> 관련: 강의 §4 Basic Agent (`create_agent`), README 파이프라인 절, `docs/LECTURE.md`.

## 배경
현재 파이프라인은 결정적 오케스트레이션이다. 순서는 코드가 정하고 LLM은
추출(`with_structured_output`)과 설명만 맡는다. `@tool` 3종은 `tool.invoke()`로
직접 호출되며 에이전트 루프는 없다. 덕분에 `verify 12/12`가 결정적이다.

## 제안 내용
LLM이 도구 호출 순서까지 정하는 에이전트 루프를 도입한다. 후보 구현:
- **B1. 강의 정석**: `from langchain.agents import create_agent` +
  `tools=[geocode_place_tool, search_parking_tool, estimate_fee_tool]` (+ 필요시 middleware)
- **B2. 고전 방식**: `create_tool_calling_agent()` + `AgentExecutor`

## 기대 효과
- 강의 진도와 일치 (`@tool` teach → loop teach 흐름)
- 후속 발화("주차비 5천원 이하로, 500m 안") 같은 복합 조건을 프롬프트만으로 처리 가능
- 랭킹 기준 변경이 코드 수정 없이 프롬프트 수준에서 실험 가능

## 비용·리스크
- **verify 재설계 필수**: LLM이 호출 순서를 정하면 결과가 비결정적.
  현재 문자열 assert 방식은 깨진다. `NO_LLM` 모드 유지 + 루프용 별도 시나리오 필요
- **Tool 설계 변경**: `search`가 반경 필터까지 하면 에이전트가 페이징/재조회를
  판단해야 해서 인자 스키마(페이지, 정렬키) 확장 필요
- **비용**: 턴당 LLM 호출 수 증가 (추론+도구+종합 최소 3회)
- **가드레일 위치 변경**: 현재 코드 선행 차단 → 루프 안 `before_agent` 형태로 이전 필요

## 전제 조건
1. Mock이 아닌 실데이터 지오코딩 완료 (`KAKAO_REST_KEY` 발급)
   — 루프가 거리 기준으로 삼을 좌표가 있어야 의미가 있음
2. `PARKING_AGENT_NO_LLM=1` 결정성 모드 유지 방안 확정

## 권장 순서
1. 카카오 지오코딩 완료 후
2. B1(`create_agent`) 스파이크를 별도 스크립트(`scripts/agent_loop_spike.py`)로만 작성,
   기존 `pipeline.run_turn`은 건드리지 않음
3. 루프용 검증 시나리오 3건 추가 후 비교 평가, 그때 전환 여부 결정

## 결정 대기
- [ ] B1 vs B2 선택
- [ ] 전환 시점 (지오코딩 후로 연기 권장)
