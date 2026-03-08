"""
Tool 3: 상세설명 매퍼
청구항 구성요소 <-> 상세한 설명 단락 매핑
BAAI/bge-m3로 관련 후보 단락을 먼저 선별하고 LLM으로 매핑 텍스트 추출
"""

from pydantic import BaseModel                          # Pydantic 기반 클래스 — 응답 래퍼 모델 정의용
from schemas.claim import Claim, ClaimElement           # 청구항 및 구성요소 모델
from llm.client import call_llm_structured  # LLM 호출

# LLM에게 전달할 시스템 프롬프트 — 명세서 매핑 규칙 지시
_SYSTEM = """당신은 특허 명세서 분석 전문가입니다.
청구항 구성요소가 상세한 설명의 어느 부분에서 구체화되는지 찾아 매핑하세요.

규칙:
- 구성요소와 가장 관련성 높은 상세설명 내용을 찾아 description_mapping에 기재
- 관련 단락을 직접 인용하거나 핵심 내용을 요약하여 기재 (1~3문장)
- 관련 내용이 없으면 "상세설명에서 직접적인 기재 없음"으로 기재
"""


# LLM이 구성요소 1개에 대해 반환하는 매핑 결과
class _MappingResult(BaseModel):
    element_id: str           # 구성요소 식별자 (예: "구성1")
    description_mapping: str  # 상세설명에서 해당 구성요소에 대응하는 내용


# LLM은 단일 객체만 반환하므로 래퍼로 감쌈
class _MappingWrapper(BaseModel):
    result: _MappingResult


def _split_into_sentences(text: str) -> list[str]:
    """상세설명을 문장/단락 단위로 분리 — 빈 줄 제거 + 너무 짧은 줄(제목 등) 제외"""
    lines = [line.strip() for line in text.split("\n") if line.strip()]  # 빈 줄 제거
    sentences = [line for line in lines if len(line) > 20]               # 20자 미만 줄(제목 등) 제외
    return sentences if sentences else lines  # 모두 짧으면 원본 줄 그대로 반환


def map_description(claims: list[Claim], description_text: str) -> list[Claim]:
    """
    각 청구항의 구성요소에 상세설명 매핑을 채워서 반환.
    bge-m3로 관련 후보 문장을 선별한 뒤 LLM으로 최종 매핑 추출.
    """
    sentences = _split_into_sentences(description_text)  # 상세설명을 문장 단위로 분리
    updated_claims = []  # 매핑이 채워진 청구항을 담을 리스트

    for claim in claims:  # 입력된 모든 청구항에 대해 반복
        updated_elements: list[ClaimElement] = []  # 매핑이 채워진 구성요소를 담을 리스트
        desc_full = "\n".join(sentences) if sentences else "(상세설명 없음)"

        for elem in claim.elements:  # 청구항의 각 구성요소에 대해 반복
            if not sentences:
                updated_elements.append(elem)  # 상세설명이 없으면 매핑 없이 그대로 유지
                continue

            # LLM에 상세설명 전문을 직접 넘겨 매핑 추출
            result = call_llm_structured(
                system_prompt=_SYSTEM,
                user_prompt=(
                    f"구성요소 ID: {elem.element_id}\n"
                    f"구성요소 텍스트: {elem.text}\n\n"
                    f"상세설명 전문:\n{desc_full}\n\n"
                    "이 구성요소와 가장 관련된 상세설명 내용을 반환하세요."
                ),
                response_schema=_MappingWrapper,
            )
            # 원본 구성요소를 복사하면서 description_mapping 필드만 업데이트
            updated_elements.append(
                elem.model_copy(
                    update={"description_mapping": result.result.description_mapping}
                )
            )

        # 원본 청구항을 복사하면서 elements 필드만 매핑이 채워진 버전으로 교체
        updated_claims.append(claim.model_copy(update={"elements": updated_elements}))

    return updated_claims  # 매핑이 채워진 청구항 리스트 반환
