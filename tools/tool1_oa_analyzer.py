"""
Tool 1: 통지서 분석기
의견제출통지서 텍스트 -> OfficeAction 구조체
"""

from schemas.office_action import OfficeAction  # 분석 결과를 담을 Pydantic 모델
from llm.client import call_llm_structured      # LLM 호출 공통 함수

# LLM에게 전달할 시스템 프롬프트 — 추출 규칙을 상세히 명시
_SYSTEM = """당신은 한국 특허 심사 전문가입니다.
의견제출통지서를 분석하여 JSON으로 구조화하세요.

추출 규칙:
- application_no: 출원번호 (예: "10-2024-0003365")
- title: 발명의 명칭 그대로
- rejection_reasons: 각 거절이유를 법조항 기준으로 분리
  - seq: 순번 (1, 2, 3...)
  - legal_basis: "특허법 제XX조제X항제X호" 형식 그대로
  - target_claims: 해당 거절이유가 적용되는 청구항 번호 리스트
  - summary: 거절이유 핵심을 한 문장으로 요약
  - detail: 심사관 지적 내용 전문 (원문 보존)
- cited_prior_arts: 인용된 선행발명 목록
  - id: "인용발명 1", "인용발명 2" 등
  - reference: 공보번호 전체 (예: "일본 공개특허공보 특개2007-141071호")
  - publication_date: 공개일 (예: "2007.06.07.")
  - key_paragraphs: 심사관이 참조한 단락/도면 번호 리스트
- all_target_claims: 심사 대상 청구항 전체 번호 리스트
- submission_deadline: 제출기일 "YYYY.MM.DD." 형식
"""


def analyze_office_action(text: str) -> OfficeAction:
    """의견제출통지서 텍스트를 OfficeAction 모델로 변환"""
    return call_llm_structured(
        system_prompt=_SYSTEM,
        user_prompt=f"다음 의견제출통지서를 분석하세요:\n\n{text}",  # 원문을 그대로 LLM에 전달
        response_schema=OfficeAction,  # LLM 응답을 OfficeAction Pydantic 모델로 파싱
    )
