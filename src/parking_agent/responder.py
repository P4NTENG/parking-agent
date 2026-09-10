"""LLM 응답 생성 + 키 없을 때 템플릿 폴백."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from .fee import fee_formula
from .schemas import RankingParams

load_dotenv()


def _template_answer(params: RankingParams, ranked: list[dict]) -> str:
    if not ranked:
        return (
            "조건에 맞는 주차장을 찾지 못했어요. "
            "반경을 넓히거나(예: 2km) 요금 상한을 올려서 다시 물어봐 주세요."
        )
    lines = [f"'{params.place}' 근처 {params.minutes}분 기준 추천 {len(ranked)}곳:"]
    for r in ranked:
        formula = fee_formula(
            r["base_minutes"], r["base_fee"], r["unit_minutes"], r["unit_fee"], params.minutes
        )
        lines.append(
            f"{r['rank']}. {r['name']} - {r['distance_m']}m, {formula}, 운영 {r['open']}"
        )
    lines.append("마음에 안 들면 “더 저렴한 걸로”, “더 가까운 걸로”라고 말해 주세요.")
    return "\n".join(lines)


def format_answer(
    user_text: str, params: RankingParams, ranked: list[dict], trace: dict
) -> str:
    api_key = os.getenv("OPENAI_API_KEY", "")
    if api_key and ranked:
        try:
            from langchain_openai import ChatOpenAI

            llm = ChatOpenAI(
                model=os.getenv("MODEL_NAME", "deepseek-v4-flash"),
                base_url=os.getenv("OPENAI_BASE_URL") or None,
                temperature=0.2,
            )
            cand = "\n".join(
                f"- {r['name']} {r['distance_m']}m {r['fee']}원 운영{r['open']}"
                for r in ranked
            )
            prompt = (
                "너는 주차장 추천 비서다. 후보와 요금 계산식을 근거로 1~3순위를 설명하라. "
                "할루시네이션 금지, 후보 외 장소 언급 금지.\n"
                f"사용자: {user_text}\n파라미터: {params.model_dump_json()}\n후보:\n{cand}"
            )
            resp = llm.invoke(prompt)
            content = resp.content if isinstance(resp.content, str) else str(resp.content)
            return content + f"\n\n[추출:{trace.get('source')} sort={params.sort_by}]"
        except Exception as e:
            print(f"[경고] LLM 응답 실패, 템플릿 폴백: {e}")
    return _template_answer(params, ranked)
