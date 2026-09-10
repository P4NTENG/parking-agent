# 필요한 API / 키 현황 (2026-09-11 기준)

## 확보됨 ✅
- `OPENAI_API_KEY` — OpenAI 정식 모드 (`OPENAI_BASE_URL` 비움)
- `MODEL_NAME=gpt-5.6-luna` — 추출·응답 실모델 동작 확인
- `SEOUL_OPENAPI_KEY` — 서울시 `GetParkingInfo` 122건 캐시 확인 (`scripts/cache_seoul.py`)

## 미확보 ⏳
- `KAKAO_REST_KEY` — 카카오 developers REST 키
  - 용도: 서울시 데이터 지오코딩 122건 (`ADDR` 지번 → 위경도). 없으면
    `PARKING_SOURCE=seoul`이 거리 필터에 걸려 0건 폴백한다.
  - 대체: 네이버 지도 `NCP_CLIENT_ID / NCP_CLIENT_SECRET`
- 대상 지역 최종 범위 — 서울 전체 vs 강남권 (지오코딩·캐시 범위에 영향)

## 참고
- `DATA_GO_KR_KEY` (교통안전공단 `B553881`) — 서울시로 방향 확정되어 불필요.
  `.env.example`에만 플레이스홀더 유지.
- `verify_pipeline.py`는 `PARKING_AGENT_NO_LLM=1` 고정이라 키 없이도 전수 통과.
