"""LLM 파라미터 추출 + 키 없을 때 동작하는 규칙 기반 폴백."""

from __future__ import annotations

import os
import re

from dotenv import load_dotenv

from .geo import PLACE_COORDS
from .schemas import RankingParams

load_dotenv()

_EXTRACT_SYS = """너는 주차장 추천용 파라미터 추출기다.
사용자 발화(한국어)에서 아래 JSON 스키마로만 답하라.
- place: 기준 장소명 (없으면 null)
- minutes: 체류시간 분. "2시간"=120, "30분"=30. 없으면 120.
- radius_km: 반경. "500m"=0.5. 없으면 1.0.
- max_price: 상한요금 원. 없으면 null.
- prefer_free: 무료 언급시 true.
- sort_by: "가까운/역세권"→distance, "저렴/싼/가성비"→price, "무료"→free_first, 없으면 recommended.
- need_disabled: 장애인 언급시 true.
- open_at: "23시/밤11시/심야"→"23:00" 등으로 HH:MM 정규화. 없으면 null.
- top_k: 기본 3.
추측 금지. 모르면 기본값."""


def _rule_extract(text: str) -> RankingParams:
    place = None
    for name in PLACE_COORDS:
        if name in text:
            place = name
            break
    minutes = 120
    m = re.search(r"(\d+)\s*시간", text)
    if m:
        minutes = int(m.group(1)) * 60
        m2 = re.search(r"(\d+)\s*시간\s*(\d+)\s*분", text)
        if m2:
            minutes = int(m2.group(1)) * 60 + int(m2.group(2))
    else:
        m = re.search(r"(\d+)\s*분", text)
        if m and "기본" not in text:
            minutes = int(m.group(1))
    radius_km = 1.0
    m = re.search(r"(\d+(?:\.\d+)?)\s*km", text, re.I)
    if m:
        radius_km = float(m.group(1))
    else:
        m = re.search(r"(\d+)\s*m\b", text)
        if m and "만원" not in text:
            radius_km = int(m.group(1)) / 1000
    max_price = None
    m = re.search(r"(\d+)\s*만원\s*이하", text)
    if m:
        max_price = int(m.group(1)) * 10000
    else:
        m = re.search(r"(\d+)\s*원\s*이하", text)
        if m:
            max_price = int(m.group(1))
    prefer_free = "무료" in text
    if "가까운" in text or "거리순" in text:
        sort_by = "distance"
    elif "저렴" in text or "싼" in text or "가성비" in text or "비싸" in text:
        sort_by = "price"
    elif "무료" in text:
        sort_by = "free_first"
    else:
        sort_by = "recommended"
    need_disabled = "장애인" in text
    open_at = None
    # "2시간"의 "2시"를 시각으로 오인하지 않도록 '시+간/분' 제외
    m = re.search(r"(\d{1,2})\s*시(?![간분])", text)
    if m or "심야" in text or "밤" in text:
        if "심야" in text:
            open_at = "23:00"
        elif m:
            open_at = f"{int(m.group(1)):02d}:00"
    m = re.search(r"(\d{1,2}):(\d{2})", text)
    if m:
        open_at = f"{int(m.group(1)):02d}:{m.group(2)}"
    return RankingParams(
        place=place,
        minutes=minutes,
        radius_km=radius_km,
        max_price=max_price,
        prefer_free=prefer_free,
        sort_by=sort_by,  # type: ignore[arg-type]
        need_disabled=need_disabled,
        open_at=open_at,
    )


def _llm_disabled() -> bool:
    """테스트 결정성용. 1이면 키가 있어도 규칙 기반 사용."""
    return os.getenv("PARKING_AGENT_NO_LLM", "").strip().lower() in ("1", "true", "yes")


def _build_extractor():
    """ChatPromptTemplate | structured-LLM Runnable. LangChain 스타일 조립."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [("system", _EXTRACT_SYS), ("human", "발화: {utterance}")]
    )
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "deepseek-v4-flash"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        temperature=0,
    )
    return prompt | llm.with_structured_output(RankingParams)


def extract_params(text: str, prev: RankingParams | None = None) -> tuple[RankingParams, str]:
    """(params, source) 반환. source는 'llm' 또는 'rule'."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and not _llm_disabled():
        try:
            params = _build_extractor().invoke({"utterance": text})
            if isinstance(params, dict):
                params = RankingParams(**params)
            if prev is not None:
                params = prev.merge(params)
            return params, "llm"
        except Exception as e:
            print(f"[경고] LLM 추출 실패, 규칙 기반으로 폴백: {e}")
    params = _rule_extract(text)
    if prev is not None:
        params = prev.merge(params)
    return params, "rule"
