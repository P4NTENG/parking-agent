# 인수인계서 (2026-09-11 심야 작성, 내일 작업 재개용)

## 0. 한 줄 요약
Mock 검증 완료 → 실모델·서울시 실데이터 어댑터까지 연결됨.
내일은 **행정구역(구) 단위 일괄 수집 + 정적 캐시** 방향으로 데이터층을 다시 잡는다.
행별(Nominatim 1건씩) 지오코딩은 폐기한다.

## 1. 확정된 방향 (바꾸지 말 것)
- 데이터: **서울시 `GetParkingInfo`**, 교통안전공단(`B553881`) 아님. 실측: `docs/SEOUL_API.md`
- 모델: OpenAI 정식, `MODEL_NAME=gpt-5.6-luna` (`OPENAI_BASE_URL` 비움)
- 아키텍처: 추출(LLM 구조화) → 결정적 랭킹(코드) → 설명(LLM). 에이전트 루프 미도입
  (제안은 `docs/PROPOSAL_AGENT_LOOP.md`, 결정 대기)
- `PARKING_SOURCE=mock` 기본. `verify_pipeline.py`는 `PARKING_AGENT_NO_LLM=1` 고정이라
  키 유무와 무관하게 결정적 (pytest 23/23, verify 12/12)
- LangGraph 금지. `@tool` + `ChatPromptTemplate | LLM` + 결정적 가드레일까지만 사용

## 2. 내일 할 일 (우선순위순)
1. **구 단위 일괄 수집으로 전환**: `GetParkingInfo` 전량(122건)을 1~2회 호출로 받아
   `data/seoul_cache.json`에 고정. 행별 API 호출·행별 지오코딩 금지 (정적 데이터).
   - `scripts/cache_seoul.py`는 이미 전량 페이징을 하므로 유지. `scripts/geocode_seoul.py`는
     행별 Nominatim 방식이라 **방향 전환 시 삭제 또는 재작성 결정**.
2. **좌표 확보 방안 결정** (택1):
   a. 좌표 포함된 서울시/자치구 API가 있는지 확인 (예: 자치구별 주차장 API, 서울시설공단)
   b. 구 단위로 묶어 지오코딩 1회성 백필 후 정적 캐시 (`data/geocode_cache.json`에 65건 있음,
      gitignore라 로컬에만 존재 — 필요하면 내일 이어받기)
   c. `KAKAO_REST_KEY` 발급 → 카카오 주소검색 일괄 지오코딩 후 정적 캐시
3. `OPER_SE=4`(버스전용) 추천 제외 미구현 → `rank` 또는 `parse` 단계에 추가
4. 카카오 키 있으면 `PARKING_SOURCE=seoul` E2E 스모크
   (`demo_cli.py "시청역 근처 1시간" --once --no-stream`)

## 3. 키 현황 (`.env`, git 미추적)
- 있음: `OPENAI_API_KEY`, `SEOUL_OPENAPI_KEY` / 없음: `KAKAO_REST_KEY`
- `.env.example`는 플레이스홀더만. 값 있는 `.env`를 커밋하지 말 것

## 4. 오늘 한 일 (미커밋 → 이 커밋에 포함)
- 버그 수정: 스트리밍 빈 답변 누락(`demo_cli.py`), `disabled` 오필터
  (서울시 원천 미상을 `None`으로, rank는 명시적 `False`만 제외),
  무료해제 불가 (`"무료 말고"` → `prefer_free=False` 리셋)
- 기능: 실시간 잔여(`free_now`) 랭킹 통과 + 응답 표시, `seoul_api` 지오코딩 캐시 병합
- 테스트: `tests/test_seoul.py` 5건 (disabled·realtime·부정어·캐시병합)
- 중단됨: 행별 Nominatim 백필 (65/122에서 429로 중단, 방향 오류로 폐기)

## 5. 협업 메모
- 옆 pane(opencode 세션)이 같은 repo에서 실API 쪽 담당. 같은 파일 동시 편집 주의,
  작업 전 `git pull`, 메시지 전송은 `wmux send --surface <id>` + `send-key enter`.
- 에이전트 규약: `AGENTS.md`, wmux 설정법: `docs/WMUX_SETUP.md`
- 역할 분담은 문서화하지 않기로 함. 이 파일에도 쓰지 말 것.

## 6. 재개 명령어
```bash
git pull
pip install -r requirements.txt
python -m pytest -q                    # 23 통과 확인
python scripts/verify_pipeline.py      # 12/12 확인
copy .env.example .env 2>NUL & rem 키 기입 (최초 1회)
python scripts/cache_seoul.py          # 서울시 122건 캐시 갱신
```
