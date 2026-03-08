"""
Tool 4: Claim Chart 생성기
당사 청구항 구성요소 vs 인용발명 텍스트 -> ClaimChart
BAAI/bge-m3로 1차 후보 선별 -> LLM으로 similarity 판정
"""

from typing import Literal                              # 허용 값을 제한하는 타입 힌트
from pydantic import BaseModel                          # Pydantic 기반 클래스 — 응답 래퍼 모델 정의용
from schemas.claim import Claim                         # 당사 청구항 모델
from schemas.chart import ClaimChart, ElementMapping    # Chart 전체 + 구성요소별 매핑 결과 모델
from llm.client import call_llm_structured  # LLM 호출

# LLM에게 전달할 시스템 프롬프트 — 유사도 판정 기준 4가지를 명시
_SYSTEM = """당신은 특허 Claim Chart 작성 전문가입니다.
당사 특허 청구항의 구성요소와 인용발명 후보 문장을 비교하여 유사도를 판정하세요.

판정 기준:
- identical: 동일한 구성요소가 인용발명에 명시적으로 개시됨
- equivalent: 표현은 다르나 기술적으로 동일한 구성 (균등 범위)
- partially_different: 유사하나 기술적 차이점이 존재
- not_found: 인용발명에 대응되는 구성요소가 없음

응답 형식:
- prior_art_text: 가장 대응되는 인용발명 문장 (후보 중 선택, 없으면 "해당 없음")
- similarity: 위 기준 중 하나
- analysis: 판정 근거 설명 (1~2문장, 한국어)
"""


# 구성요소 1개에 대한 LLM 판정 결과
class _ElementJudgment(BaseModel):
    prior_art_text: str  # 인용발명에서 가장 대응되는 문장
    similarity: Literal["identical", "equivalent", "partially_different", "not_found"]  # 유사도 판정
    analysis: str        # 판정 근거 설명


# LLM은 단일 객체만 반환하므로 래퍼로 감쌈
class _JudgmentWrapper(BaseModel):
    judgment: _ElementJudgment


def _split_prior_art(text: str) -> list[str]:
    """인용발명 텍스트를 문장/단락 단위로 분리 — 10자 이하 줄(번호, 제목 등) 제외"""
    lines = [line.strip() for line in text.split("\n") if line.strip()]  # 빈 줄 제거
    return [line for line in lines if len(line) > 10]  # 너무 짧은 줄 제외


def generate_claim_chart(
    our_claim: Claim,       # 당사 청구항 (구성요소 목록 포함)
    prior_art_text: str,    # 인용발명 원문 텍스트
    prior_art_id: str,      # 인용발명 식별자 (예: "인용발명 1")
) -> ClaimChart:
    """
    당사 청구항의 각 구성요소에 대해 인용발명과의 매핑을 생성.
    bge-m3로 상위 3개 후보 선별 -> LLM이 최종 판정.
    """
    sentences = _split_prior_art(prior_art_text)  # 인용발명을 문장 단위로 분리
    mappings: list[ElementMapping] = []            # 구성요소별 판정 결과를 담을 리스트

    prior_art_full = "\n".join(sentences) if sentences else "(인용발명 텍스트 없음)"

    for elem in our_claim.elements:  # 청구항의 각 구성요소에 대해 반복
        # LLM에 인용발명 전문을 직접 넘겨 판정
        result = call_llm_structured(
            system_prompt=_SYSTEM,
            user_prompt=(
                f"당사 구성요소 ({elem.element_id}): {elem.text}\n\n"
                f"인용발명 전문:\n{prior_art_full}\n\n"
                "가장 대응되는 문장을 선택하고 similarity를 판정하세요."
            ),
            response_schema=_JudgmentWrapper,
        )

        j = result.judgment  # 래퍼에서 실제 판정 결과 추출
        mappings.append(
            ElementMapping(
                our_element=elem,
                prior_art_text=j.prior_art_text,
                similarity=j.similarity,
                cosine_score=None,  # bge-m3 제거로 미사용
                analysis=j.analysis,
            )
        )

    # 청구항 전체에 대한 Chart 반환 (구성요소 수만큼의 매핑 포함)
    return ClaimChart(our_claim=our_claim, prior_art_id=prior_art_id, mappings=mappings)
