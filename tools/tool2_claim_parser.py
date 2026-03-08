"""
Tool 2: 청구항 파서
청구항 텍스트 -> list[Claim] 구조체
"""

from pydantic import BaseModel              # Pydantic 기반 클래스 — 응답 래퍼 모델 정의에 사용
from schemas.claim import Claim             # 파싱 결과를 담을 청구항 모델
from llm.client import call_llm_structured  # LLM 호출 공통 함수

# LLM에게 전달할 시스템 프롬프트 — 파싱 규칙과 few-shot 예시를 포함
_SYSTEM = """당신은 한국 특허 청구항 파싱 전문가입니다.
청구항 텍스트를 구조화된 JSON으로 변환하세요.

파싱 규칙:
- claim_type: "independent"(독립항) 또는 "dependent"(종속항)
  - 독립항: 다른 청구항을 인용하지 않음
  - 종속항: "제X항에 있어서" 또는 "제X항 또는 제Y항에 있어서" 형태
- parent_claims: 종속항이면 인용하는 항 번호 리스트, 독립항이면 []
- elements: 청구항을 구성요소 단위로 분리
  - 세미콜론(;), "및", "를 포함하며" 등으로 구분되는 기술적 구성요소
  - element_id: "구성1", "구성2", ... 순서대로
  - text: 구성요소 텍스트 (간결하게, 핵심 기술적 특징만)
  - description_mapping: null (Tool 3에서 채움)
- full_text: 해당 청구항 원문 전체

Few-shot 예시:
입력 청구항 1: "청구항 1. 타이어의 내부에 마련되는 전자모듈; 및 상기 타이어의 외부에 마련되는 리더부를 포함하며, 상기 전자모듈 및 상기 리더부의 송신주파수는, 수신주파수가 목표로 하는 목적수신주파수가 되도록 설계되고, 상기 송신주파수는 상기 목적수신주파수보다 크게 설계된 것을 특징으로 하는 타이어."
출력:
{
  "claim_number": 1, "claim_type": "independent", "parent_claims": [],
  "full_text": "청구항 1. 타이어의 내부에...",
  "elements": [
    {"element_id": "구성1", "text": "타이어의 내부에 마련되는 전자모듈", "description_mapping": null},
    {"element_id": "구성2", "text": "타이어의 외부에 마련되는 리더부", "description_mapping": null},
    {"element_id": "구성3", "text": "송신주파수는 목적수신주파수보다 크게 설계", "description_mapping": null}
  ]
}

입력 청구항 2: "청구항 2. 제1항에 있어서, 상기 송신주파수와 목적수신주파수의 차이는 타이어 무선 주파수 상수에 의해 결정되는 것인 타이어."
출력:
{
  "claim_number": 2, "claim_type": "dependent", "parent_claims": [1],
  "full_text": "청구항 2. 제1항에 있어서...",
  "elements": [
    {"element_id": "구성1", "text": "송신주파수와 목적수신주파수의 차이는 타이어 무선 주파수 상수에 의해 결정", "description_mapping": null}
  ]
}
"""


# LLM은 단일 객체만 반환할 수 있으므로 Claim 리스트를 감싸는 래퍼 모델 정의
class _ClaimListWrapper(BaseModel):
    claims: list[Claim]  # 파싱된 청구항 전체 목록


def parse_claims(text: str) -> list[Claim]:
    """청구항 텍스트를 파싱하여 Claim 리스트 반환"""
    result = call_llm_structured(
        system_prompt=_SYSTEM,
        user_prompt=f"다음 청구항들을 모두 파싱하세요:\n\n{text}",  # 청구항 원문 전달
        response_schema=_ClaimListWrapper,  # LLM 응답을 래퍼 모델로 파싱
    )
    return result.claims  # 래퍼에서 실제 Claim 리스트만 꺼내서 반환
