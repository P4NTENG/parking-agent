"""LLM 응답 생성 + 키 없을 때 템플릿 폴백. 기본 스트리밍."""

from __future__ import annotations

import os
from collections.abc import Callable, Iterator

from dotenv import load_dotenv

from .fee import fee_formula
from .schemas import RankingParams

load_dotenv()


def _stream_enabled(explicit: bool | None = None) -> bool:
    """기본 스트리밍 여부. 인자 > LLM_STREAM env > 기본 True."""
    if explicit is not None:
        return explicit
    return os.getenv("LLM_STREAM", "true").strip().lower() in ("1", "true", "yes", "y")


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


_RESPOND_SYS = (
    "너는 주차장 추천 비서다. 후보와 요금 계산식을 근거로 1~3순위를 설명하라. "
    "할루시네이션 금지, 후보 외 장소 언급 금지."
)


def _build_responder(streaming: bool):
    """ChatPromptTemplate | LLM Runnable. LangChain 스타일 조립."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", _RESPOND_SYS),
            (
                "human",
                "사용자: {user_text}\n파라미터: {params_json}\n후보:\n{candidates}",
            ),
        ]
    )
    llm = ChatOpenAI(
        model=os.getenv("MODEL_NAME", "deepseek-v4-flash"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
        temperature=0.2,
        streaming=streaming,
    )
    return prompt | llm


def _candidates_text(ranked: list[dict]) -> str:
    return "\n".join(
        f"- {r['name']} {r['distance_m']}m {r['fee']}원 운영{r['open']}" for r in ranked
    )


def _chain_input(user_text: str, params: RankingParams, ranked: list[dict]) -> dict:
    return {
        "user_text": user_text,
        "params_json": params.model_dump_json(),
        "candidates": _candidates_text(ranked),
    }


def format_answer_stream(
    user_text: str, params: RankingParams, ranked: list[dict], trace: dict
) -> Iterator[str]:
    """LLM 토큰 스트림 생성기. 키 없으면 템플릿 전체를 1청크로 yield."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    suffix = f"\n\n[추출:{trace.get('source')} sort={params.sort_by}]"
    if api_key and ranked:
        try:
            for chunk in _build_responder(streaming=True).stream(
                _chain_input(user_text, params, ranked)
            ):
                content = chunk.content
                text = content if isinstance(content, str) else str(content)
                if text:
                    yield text
            yield suffix
            return
        except Exception as e:
            print(f"[경고] LLM 응답 실패, 템플릿 폴백: {e}")
    yield _template_answer(params, ranked)


def format_answer(
    user_text: str,
    params: RankingParams,
    ranked: list[dict],
    trace: dict,
    stream: bool | None = None,
    on_token: Callable[[str], None] | None = None,
) -> str:
    """기본 스트리밍으로 LLM 호출 후 전체 문자열 반환.

    verify/tests 호환용: 반환값은 기존과 동일. 토큰 단위 출력이
    필요하면 on_token 콜백 또는 format_answer_stream() 사용.
    """
    if not _stream_enabled(stream):
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key and ranked:
            try:
                resp = _build_responder(streaming=False).invoke(
                    _chain_input(user_text, params, ranked)
                )
                content = resp.content if isinstance(resp.content, str) else str(resp.content)
                return content + f"\n\n[추출:{trace.get('source')} sort={params.sort_by}]"
            except Exception as e:
                print(f"[경고] LLM 응답 실패, 템플릿 폴백: {e}")
        return _template_answer(params, ranked)
    parts: list[str] = []
    for token in format_answer_stream(user_text, params, ranked, trace):
        parts.append(token)
        if on_token is not None:
            on_token(token)
    return "".join(parts)
