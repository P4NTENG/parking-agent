"""랭킹에 필요한 파라미터 스키마. LLM이 대화에서 추출해 구조화한다."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SortBy = Literal["recommended", "distance", "price", "free_first"]


class RankingParams(BaseModel):
    """사용자 발화에서 추출되는 구조화 파라미터."""

    place: str | None = Field(default=None, description="기준 장소명, 예: 강남역")
    minutes: int = Field(default=120, description="예상 체류시간(분)")
    radius_km: float = Field(default=1.0, description="검색 반경(km)")
    max_price: int | None = Field(default=None, description="허용 상한 요금(원)")
    prefer_free: bool = Field(default=False, description="무료 우선 여부")
    sort_by: SortBy = Field(
        default="recommended",
        description="정렬 기준. 명시 없으면 recommended(LLM 내재 선호: 거리+요금 균형)",
    )
    need_disabled: bool = Field(default=False, description="장애인 구역 필요 여부")
    open_at: str | None = Field(default=None, description="이용 시각 HH:MM, 예: 23:00")
    top_k: int = Field(default=3, description="추천 개수")

    def merge(self, other: "RankingParams") -> "RankingParams":
        """리랭킹용 병합: 새로 추출된 값이 기본값이 아니면 덮어쓴다."""
        data = self.model_dump()
        update = other.model_dump(exclude_unset=True)
        # LLM이 명시하지 않은 필드는 기본값으로 오므로, 의미 있는 변경만 반영
        for k, v in update.items():
            if k == "minutes" and v == 120 and self.minutes != 120:
                continue
            if k == "sort_by" and v == "recommended" and self.sort_by != "recommended":
                continue
            if k in ("radius_km",) and v == 1.0:
                continue
            if k in ("top_k",) and v == 3:
                continue
            if v is None and k in ("place", "max_price", "open_at"):
                continue
            if isinstance(v, bool) and v is False and getattr(self, k) is True:
                # False는 '명시적 해제'와 '미지정' 구분이 불가 -> True 유지
                # 단, sort_by가 바뀌면 prefer_free도 함께 재해석하므로 허용
                continue
            data[k] = v
        # place가 새로 들어오면 좌표 재계산 필요 -> 호출자가 처리
        return RankingParams(**data)
