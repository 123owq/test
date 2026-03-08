from __future__ import annotations      # 타입 힌트에서 문자열 형태의 전방 참조를 허용 (Python 3.10 이하 호환)
from typing import Literal              # 특정 값만 허용하는 타입 힌트 (예: "independent" 또는 "dependent"만 허용)
from pydantic import BaseModel          # 데이터 유효성 검사 + 직렬화 라이브러리


class ClaimElement(BaseModel):
    """청구항 하나의 구성요소 한 개 — "전자모듈", "리더부" 같은 기술적 구성 단위"""
    element_id: str                          # 구성요소 식별자 (예: "구성1", "구성2", "구성3")
    text: str                                # 구성요소 텍스트 (핵심 기술적 특징만 간결하게)
    description_mapping: str | None = None   # Tool 3에서 채우는 필드 — 상세한 설명의 어느 부분에 해당하는지


class Claim(BaseModel):
    """청구항 한 개 전체 — Tool 2의 파싱 출력 단위"""
    claim_number: int                                   # 청구항 번호 (1, 2, 3 ...)
    claim_type: Literal["independent", "dependent"]     # 독립항(다른 항 인용 없음) 또는 종속항(다른 항 인용)
    parent_claims: list[int] = []                       # 독립항이면 빈 리스트 [], 종속항이면 인용하는 항 번호 목록
    full_text: str                                      # 해당 청구항의 원문 전체
    elements: list[ClaimElement]                        # 이 청구항을 구성하는 구성요소 목록
