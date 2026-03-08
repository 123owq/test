from __future__ import annotations      # 타입 힌트 전방 참조 허용
import json                             # JSON 문자열 파싱용
from typing import Literal, Any         # 허용 값을 제한하는 타입 힌트
from pydantic import BaseModel, field_validator  # 데이터 유효성 검사 + 직렬화

from .claim import Claim, ClaimElement  # 같은 schemas 패키지의 청구항 관련 모델 import


class ElementMapping(BaseModel):
    """당사 청구항 구성요소 1개와 인용발명 사이의 유사도 판정 결과 — Tool 4의 구성요소별 출력"""
    our_element: ClaimElement           # 당사 청구항의 구성요소 (예: 구성3 "송신주파수 설계")
    prior_art_text: str                 # 가장 대응되는 인용발명 문장 (없으면 "해당 없음")
    similarity: Literal[                # 유사도 판정 결과
        "identical",           # 동일: 인용발명에 명시적으로 동일한 구성이 개시됨
        "equivalent",          # 균등: 표현은 다르나 기술적으로 동일한 구성
        "partially_different", # 부분 차이: 유사하나 기술적 차이점이 존재
        "not_found",           # 미개시: 인용발명에 대응 구성이 없음
    ]
    cosine_score: float | None = None   # bge-m3 임베딩 코사인 유사도 (LLM 판정 전 참고값, 필수 아님)
    analysis: str                       # 판정 근거 설명 (1~2문장 한국어)


class ClaimChart(BaseModel):
    """청구항 1개에 대한 인용발명 비교표 전체 — Tool 4의 최종 출력"""
    our_claim: Claim                    # 비교 대상인 당사 청구항
    prior_art_id: str                   # 인용발명 식별자 (예: "인용발명 1")
    mappings: list[ElementMapping]      # 구성요소별 유사도 판정 결과 목록 (구성요소 수만큼)


class ResponseStrategy(BaseModel):
    """거절이유 1건에 대한 대응 전략 — Tool 5의 전략 단위"""
    rejection_seq: int                  # 대응할 거절이유 순번 (OfficeAction.rejection_reasons의 seq와 매칭)
    strategy_type: Literal[             # 대응 방식
        "amendment",   # 보정: 청구항 문구를 수정하여 거절이유 해소
        "argument",    # 의견: 청구항은 그대로 두고 심사관 논거에 반박
        "both",        # 보정 + 의견 병행
    ]
    rationale: str                      # 이 전략을 선택한 근거 설명


class DiffAnalysis(BaseModel):
    """차이점 분석 + 거절이유별 대응 전략 — Tool 5의 최종 출력"""
    key_differences: list[str]          # 당사 발명과 인용발명의 핵심 차이점 목록 (구체적 기술적 근거 포함)
    strategies: list[ResponseStrategy]  # 각 거절이유(seq)에 대한 대응 전략 목록 (모든 거절이유 포함 필수)

    @field_validator("key_differences", "strategies", mode="before")
    @classmethod
    def parse_json_string(cls, v: Any) -> Any:
        """LLM이 리스트를 JSON 문자열로 반환하는 경우를 처리"""
        if isinstance(v, str):
            return json.loads(v)
        return v


class AmendedClaim(BaseModel):
    """보정된 청구항과 보정 이유 — Tool 6의 최종 출력"""
    original_claim_number: int          # 보정 대상 원본 청구항 번호
    original_text: str                  # 보정 전 원본 청구항 텍스트
    amended_text: str                   # 보정 후 청구항 텍스트 (한국 특허 문체 준수)
    amendment_rationale: str            # 보정 이유서 — 거절이유별로 어떻게 해소했는지 설명
    addresses_rejections: list[int]     # 이 보정으로 실제 해소된 거절이유 순번 목록 (예: [1, 2, 3])
    quality_score: float | None = None  # 보정 품질 점수 (0.0~1.0) — Agent 재시도 여부 판단 기준 (0.7 미만이면 재시도)
