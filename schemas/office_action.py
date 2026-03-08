from pydantic import BaseModel  # Pydantic: 데이터 유효성 검사 + JSON 직렬화를 자동으로 처리해주는 라이브러리


class PriorArt(BaseModel):
    """심사관이 거절 근거로 인용한 선행발명 한 건"""
    id: str                         # 내부 식별자 (예: "인용발명 1") — prior_art_texts 딕셔너리 키와 매칭
    reference: str                  # 공보번호 전체 (예: "일본 공개특허공보 특개2007-141071호")
    publication_date: str           # 선행발명 공개일 (예: "2007.06.07.")
    key_paragraphs: list[str] = []  # 심사관이 실제로 참조한 단락/도면 번호 (예: ["단락 [13-19]", "도면 1-4"])


class RejectionReason(BaseModel):
    """거절이유 한 건 — 하나의 법조항 위반에 해당"""
    seq: int                     # 거절이유 순번 (1, 2, 3 ...) — Agent 재시도 시 기준으로 사용
    legal_basis: str             # 해당 법조항 (예: "특허법 제42조제3항제1호")
    target_claims: list[int]     # 이 거절이유가 적용되는 청구항 번호 목록 (예: [1, 2, 3, ..., 10])
    summary: str                 # 거절이유 핵심을 한 문장으로 요약한 것
    detail: str                  # 심사관 지적 내용 원문 전체


class OfficeAction(BaseModel):
    """의견제출통지서 전체 분석 결과 — Tool 1의 출력"""
    application_no: str                      # 출원번호 (예: "10-2024-0003365")
    title: str                               # 발명의 명칭
    rejection_reasons: list[RejectionReason] # 거절이유 목록 (법조항별로 분리)
    cited_prior_arts: list[PriorArt]         # 인용된 선행발명 목록
    all_target_claims: list[int]             # 심사 대상 청구항 전체 번호 (예: [1, 2, 3, ..., 10])
    submission_deadline: str                 # 의견서 제출기한 (예: "2026.02.21.")
