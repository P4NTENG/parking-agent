# 서울시 공영주차장 API (GetParkingInfo) — 실측 정리

> 확인일: 2026-09-11 / 호출: `GET http://openapi.seoul.go.kr:8088/{KEY}/json/GetParkingInfo/{start}/{end}`
> 예: `.../json/GetParkingInfo/1/5` → 정상 (`RESULT.CODE=INFO-000`)
> 키: `.env`의 `SEOUL_OPENAPI_KEY` 사용. `.env.example`에는 플레이스홀더만 둔다.

## 1. 최상위 구조

```json
{
  "GetParkingInfo": {
    "list_total_count": 122,
    "RESULT": {"CODE": "INFO-000", "MESSAGE": "정상 처리되었습니다"},
    "row": [ {...}, ... ]
  }
}
```

- `list_total_count`: 122 (시영 공영주차장 수, 2026-09-11 기준)
- 페이징: `/{start}/{end}` 1-indexed. 122건이라 1회 전량 가능하나 권장 100건씩 2회.

## 2. row 필드 (총 40개)

| 필드 | 예시 | 비고 |
|---|---|---|
| `PKLT_CD` | `"171721"` | 주차장 코드 (PK) |
| `PKLT_NM` | `"세종로 공영주차장(시)"` | 이름, `(시)`=시영 |
| `ADDR` | `"종로구 세종로 80-1"` | 지번 주소, **위경도 없음** → 카카오 지오코딩 필요 |
| `PKLT_TYPE` | `"NW"` | NW=노외, NS=노상 |
| `PRK_TYPE_NM` | `"노외 주차장"` | 표시명 |
| `OPER_SE` / `OPER_SE_NM` | `"1"` / `"시간제 주차장"` | 1=시간제, 4=버스전용(예외처리 필요) |
| `TELNO` | `"02-2290-6566"` | 빈 문자열 가능 |
| `PRK_STTS_YN` / `PRK_STTS_NM` | `"1"` / `"현재~20분이내 연계데이터 존재…"` | 1=실시간 연계, 0=미연계중 |
| `TPKCT` | `1260.0` | 총 주차면 수 (float로 옴) |
| `NOW_PRK_VHCL_CNT` | `143.0` | 현재 주차대수. `PRK_STTS_YN=0`이면 0 + `UPDT_TM=""` |
| `NOW_PRK_VHCL_UPDT_TM` | `"2026-09-11 00:15:33"` | 미연계시 빈 문자열 |
| `PAY_YN` / `PAY_YN_NM` | `"Y"` / `"유료"` | `N`=무료 (버스전용 예: 훈련원공원 앞) |
| `NGHT_PAY_YN` | `"N"` | 야간 개방 여부 (전수 N으로 보임, 신뢰 낮음) |
| `WD_OPER_BGNG_TM` / `WD_OPER_END_TM` | `"0000"` / `"2400"` | 평일 HHMM. `0900-1900`형도 있음(여의도공원) |
| `WE_OPER_*` / `LHLDY_OPER_*` | 동상 | 주말/공휴일. `0000-0000` = 미운영 |
| `SAT_CHGD_FREE_SE` / `SAT_CHGD_FREE_NM` | `"N"` / `"무료"` | ⚠️ 코드-표시명 뒤집힘 주의. `N`→무료, `Y`→유료로 응답됨. **NM 기준 해석** |
| `LHLDY_CHGD_FREE_SE` / `..._NAME` | `"N"` / `"무료"` | 동상 (키 이름에 `_NAME` 오타 있음) |
| `PRD_AMT` | `"176000"` | 월정기요금. string, 빈 문자열/`"0"` 가능 |
| `STRT_PKLT_MNG_NO` | `""` | 노상 관리번호. 노외는 빈 문자열 |
| `BSC_PRK_CRG` | `430.0` | 기본요금(원, float) |
| `BSC_PRK_HR` | `5.0` | ⚠️ 이름은 HR이나 **단위는 분**. 5.0 = 5분 |
| `ADD_PRK_CRG` / `ADD_PRK_HR` | `430.0` / `5.0` | 추가요금/추가단위(분). 0이면 정보없음 |
| `BUS_BSC_PRK_CRG` 등 4개 | `0.0` | 버스 요금. 일반 주차장은 0 |
| `DAY_MAX_CRG` | `0.0` / `28800.0` | 일 최대요금. 0=없음, 양재역 28800원 예시 |
| `SHRN_PKLT_*` 4개 | `"*"` / `"N"` | 공유주차장 정보. 전수 `*`/`N` → 무시 |

## 3. 내부 모델 매핑 (`seed_sample.csv` 컬럼)

| 내부 | 서울시 원천 | 변환 |
|---|---|---|
| `id` | `PKLT_CD` | 그대로 |
| `name` | `PKLT_NM` | 그대로 |
| `lat/lon` | 없음 (`ADDR`만) | 카카오 주소검색으로 지오코딩 필요 |
| `base_minutes` | `BSC_PRK_HR` | `int(float)` — 분 단위 |
| `base_fee` | `BSC_PRK_CRG` | `int(float)` |
| `unit_minutes` | `ADD_PRK_HR` | `int(float)` |
| `unit_fee` | `ADD_PRK_CRG` | `int(float)` |
| `open_time/close_time` | `WD_OPER_BGNG_TM/END_TM` | `"0900"`→`"09:00"` 변환 |
| `free` | `PAY_YN` | `Y`=false, `N`=true. `BSC_PRK_CRG=0`도 free로 취급 |
| `disabled` | 없음 | 서울시 API에 없음 → 별도 관리 |
| `realtime` (신규) | `PRK_STTS_YN`, `TPKCT`, `NOW_PRK_VHCL_CNT` | 잔여면 = `TPKCT - NOW` (연계시에만) |

## 4. 주의점 (실측)

1. **요금 단위**: `BSC_PRK_HR=5.0`은 5시간이 아니라 5분. 세종로 5분 430원.
2. **무료 판정**: `SAT_CHGD_FREE_SE` 코드값이 반대로 보임. `SE=N & NM=무료`가 정상 케이스. 코드는 믿지 말고 `PAY_YN + NM` 조합으로 판정.
3. **숫자 타입 혼재**: `TPKCT`는 number, `PRD_AMT`는 string. 파서는 둘 다 받게.
4. **미연계 행**: `PRK_STTS_YN=0`이면 `NOW_*` 무시 (면목유수지, 버스전용 등).
5. **버스전용 제외**: `OPER_SE=4` (훈련원공원 앞 관광버스 전용)는 일반 추천에서 제외.
6. **위경도 없음**: `ADDR` 지번만 옴. 카카오 `주소검색` 122건 지오코딩 1회 캐시하면 해결.
7. **일최대/월정기**: 있으면 랭킹 보너스로만 사용, 이번 단계 요금식은 기본+추가만.

## 5. 다음 작업 제안

- [ ] `src/parking_agent/seoul_api.py`: `fetch_all()` (100+22건 페이징) + `parse_row()` (위 매핑표대로) — Mock 파이프라인은 건드리지 않음
- [ ] `scripts/cache_seoul.py`: 원본 JSON → `data/seoul_cache.json` 저장 (`.gitignore` 대상)
- [ ] 카카오 지오코딩 122건 → `lat/lon` 채우기 (`KAKAO_REST_KEY` 필요)
