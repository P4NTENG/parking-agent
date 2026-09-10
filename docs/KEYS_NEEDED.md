# 필요한 API / 키 정리 (사용자 제공용)

현재 최소 파이프라인은 **키 없이 Mock으로 동작**한다. 아래는 실연동 단계에서 필요한 목록이다.

## 지금 당장 필요 없음 (Mock으로 검증 가능)
- 없음. `python scripts/verify_pipeline.py`는 키 없이 통과한다.
- LLM 키가 없어도 규칙 기반 추출 + 템플릿 응답으로 폴백한다.

## LLM 고도화용 (선택, 있으면 품질 검증 가능)
1. `OPENAI_API_KEY` — 수업용 DeepSeek 키 또는 OpenAI 키 중 하나
   - DeepSeek 사용 시: `OPENAI_BASE_URL=https://api.deepseek.com`, `MODEL_NAME=deepseek-v4-flash`
   - OpenAI 사용 시: `OPENAI_BASE_URL` 비움, `MODEL_NAME=gpt-4o-mini` 등
   - 제공 형태: `.env`에 붙여넣을 1줄이면 됨
2. 수업에서 쓰는 모델명이 다르면 `MODEL_NAME` 값만 알려줘

## 실제 주차 데이터 연동용 (다음 단계, 지금 불필요)
3. `DATA_GO_KR_KEY` — 공공데이터포털 일반 인증키 (Encoding)
   - 용도: 한국교통안전공단 주차정보 API `B553881/Parking` (시설/운영/실시간)
   - 신청: data.go.kr → 활용신청 → `http://apis.data.go.kr/B553881/Parking/*`
   - 없으면: `data/seed_sample.csv` + 표준데이터 샘플로 계속 진행
4. `KAKAO_REST_KEY` — 카카오 developers REST API 키
   - 용도: 지명 → 좌표 (키워드 검색), 목적지 길안내 링크
   - 대체: 네이버 지도 API도 가능하면 `NCP_CLIENT_ID / NCP_CLIENT_SECRET`
5. 대상 지역 범위 1개 — 예: "서울 강남구만", "서울 전체", "전국"
   - Mock 중심지(강남역/홍대입구/시청) 외 지역을 추가할 때 필요

## 내가 확인할 질문 3개
- [ ] LLM 키 줄 수 있어? (Yes면 종류: DeepSeek/OpenAI/기타 + 모델명)
- [ ] 주차 API는 교통안전공단으로 갈까, 서울시/특정 지자체로 갈까?
- [ ] 지도 API는 카카오로 갈까? (길안내 링크 필요 여부 포함)
