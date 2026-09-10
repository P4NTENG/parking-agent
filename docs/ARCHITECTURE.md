# ARCHITECTURE — 구현 방식 설명

> 최종 갱신: 2026-09-11. 코드가 진실이며, 이 문서는 따라간다.
> 어긋나면 코드를 고치거나 이 문서를 고친다.

## 1. 설계 원칙
1. **순서는 코드가 정한다.** LLM은 파라미터 추출과 최종 설명만 맡는다.
   에이전트 루프 없음 (제안은 `docs/PROPOSAL_AGENT_LOOP.md`).
2. **결정적 검증.** `verify_pipeline.py`는 `PARKING_AGENT_NO_LLM=1` 고정이라
   키 유무와 무관하게 같은 결과가 나온다.
3. **Mock 기본.** 키 없이 전체 동작. 실데이터는 `PARKING_SOURCE=seoul`로 전환.
4. **LangGraph 금지.** LangChain은 `@tool` + `ChatPromptTemplate | LLM`까지만 사용.

## 2. 턴 생명주기 (`pipeline.run_turn`)

```
사용자 발화 (+prev: 이전 턴 params)
 → extract_params → RankingParams (LLM 구조화 / 규칙 폴백)
 → check_request 가드레일 (차단 시 즉시 안내 후 종료)
 → geocode_place_tool.invoke (장소 → 위경도, Mock 사전)
 → search_parking_tool.invoke (반경 필터 + 거리순, mock/seoul 분기)
 → rank_candidates (요금·운영·상한 필터 + 정렬, fee는 estimate_fee_tool 경유)
 → format_answer (LLM 스트리밍 설명 / 템플릿 폴백)
 → (params, ranked, answer, trace) 반환. prev=params로 다음 턴 리랭킹
```

## 3. 모듈 지도 (`src/parking_agent/`)
| 모듈 | 역할 | LLM 사용 |
|---|---|---|
| `schemas.py` | `RankingParams` (place/minutes/radius_km/max_price/prefer_free/sort_by/need_disabled/open_at/top_k) + `merge()` | 없음 |
| `extractor.py` | 추출. LLM 경로(`ChatPromptTemplate | with_structured_output`) + 규칙 폴백 + 부정어 해제 | 추출 시 |
| `guardrails.py` | `check_request`: 장소 필수, minutes 1~1440·반경 0.1~10·top_k 1~10 보정, 음수 상한 제거 | 없음 |
| `tools.py` | `@tool` 3종 (geocode/search/fee) + `PARKING_TOOLS`. 호출은 코드가 `invoke()`로 직접 | 없음 (호출 대상) |
| `geo.py` | Mock 좌표 사전 + haversine | 없음 |
| `data_loader.py` | `seed_sample.csv` 로더 | 없음 |
| `seoul_api.py` | `fetch_all` 페이징 + `parse_row`(SEOUL_API.md §3) + 지오코딩 캐시 병합. stdlib만 사용 | 없음 |
| `rank.py` | 필터 + 점수(`거리 0.5 + 요금 0.5`, 무료 보너스) + 정렬 4종. `disabled=None`(미상)은 통과, `False`만 제외 | 없음 |
| `responder.py` | `ChatPromptTemplate | LLM` Runnable. 스트리밍 기본, 키 없거나 후보 없으면 템플릿. 잔여면·장애인정보없음 표기 | 설명 시 |
| `pipeline.py` | 위 순서 조립 + trace 기록. `PARKING_SOURCE` 분기는 tool 내부 | 없음 |

## 4. 후보 스키마 (두 소스 공통 + α)
`id, name, lat, lon, base_minutes, base_fee, unit_minutes, unit_fee,`
`open_time, close_time, free, disabled(True/False/None=미상)` +
seoul 전용 `addr, needs_geocode, realtime{total, now, free_now, linked, updated_at}`.
`rank` 출력은 여기에 `rank, distance_m, fee, score, open`을 더한다.

## 5. 환경 플래그 (`.env.example` 참조)
| 변수 | 기본 | 의미 |
|---|---|---|
| `OPENAI_API_KEY` | 없음 | 있으면 LLM 경로, 없으면 규칙+템플릿 |
| `MODEL_NAME` | `deepseek-v4-flash` | 현재 `gpt-5.6-luna` 사용 중 |
| `OPENAI_BASE_URL` | 비움 | 비우면 OpenAI 정식 |
| `LLM_STREAM` | `true` | 응답 스트리밍 |
| `PARKING_AGENT_NO_LLM` | 미설정 | `1`이면 키 있어도 규칙 기반 (verify 고정) |
| `PARKING_SOURCE` | `mock` | `seoul`이면 서울시 캐시/실시간 |
| `SEOUL_OPENAPI_KEY` | 없음 | `cache_seoul.py` + seoul 소스용 |
| `KAKAO_REST_KEY` | 없음 | 미발급. 지오코딩 대기 중 |

## 6. 스크립트 (`scripts/`)
- `demo_cli.py`: 대화형 + `--once` 1회 + `--no-stream`. 토큰 0개면 완성본 출력
- `verify_pipeline.py`: 12 시나리오 (추출·랭킹·리랭킹·폴백). NO_LLM/mock 고정
- `cache_seoul.py`: 서울시 122건 → `data/seoul_cache.json` (git 미추적)
- `geocode_seoul.py`: Nominatim 백필 → `data/geocode_cache.json`.
  **행별 호출이라 폐기 예정**. 구 단위 일괄 방식으로 대체한다 (`docs/HANDOVER.md` §2)

## 7. 테스트 (`tests/`, pytest 23건)
- `test_fee.py`: 요금 경계값 5건 (순수함수)
- `test_rank.py`: 정렬·무료우선·리랭킹 3건
- `test_tools.py`: tool 5건 (지오코딩·요금·검색·레지스트리)
- `test_guardrails.py`: 차단·보정 5건
- `test_seoul.py`: disabled 미상 통과·realtime 전달·부정어 리셋·캐시 병합 5건

## 8. 의도적 미구현
- 에이전트 루프 / LangGraph (PROPOSAL에서 결정 대기)
- `OPER_SE=4` 버스전용 제외 (HANDOVER §2에 이관)
- 카카오 지오코딩 (키 대기)
