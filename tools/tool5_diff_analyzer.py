"""
Tool 5: 차이점 분석 + 전략 생성기
ClaimChart + OfficeAction -> DiffAnalysis
Chain-of-Thought 방식으로 거절이유별 대응 전략 수립
"""

from schemas.chart import ClaimChart, DiffAnalysis  # Chart 입력 + 분석 결과 모델
from schemas.office_action import OfficeAction      # 거절이유 목록이 담긴 통지서 분석 결과
from llm.client import call_llm_structured          # LLM 호출 공통 함수

# LLM에게 전달할 시스템 프롬프트 — 단계적 분석 방법과 도메인 힌트 포함
_SYSTEM = """당신은 특허 심사대응 전략 전문가입니다.
Claim Chart 분석 결과와 거절이유를 바탕으로 대응 전략을 수립하세요.

단계적으로 분석하세요:
1. Claim Chart에서 "partially_different" 또는 "not_found"인 구성요소를 파악
2. 각 거절이유의 핵심 기술적 논거를 이해
3. 인용발명과의 실제 기술적 차이점을 구체적으로 기술
4. 각 거절이유를 극복하기 위한 전략(amendment/argument/both)을 결정

본 도메인 힌트 (타이어 전자장치 관련):
- §42③1 (실시가능성) 반박: "주파수는 매질에 따라 변하지 않는다"는 심사관 주장에 대해,
  타이어 구성품(고무, 강선 등)의 유전율/임피던스가 전자모듈의 공진주파수에 영향을 미치므로
  송신주파수를 목적수신주파수보다 크게 설계하는 것이 가능함을 논거로 활용
- §42④2 (명확성) 해소: 목적수신주파수의 결정 방법을 청구항에 명확히 한정하여 보정
- §29② (진보성): 인용발명은 사후 교정(오프셋 측정 후 보정)이지만 당사 발명은
  사전 설계(타이어 무선 주파수 상수 활용한 사전 계산)라는 점을 강조

key_differences: 핵심 차이점을 명확하고 구체적으로 기술 (기술적 근거 포함)
strategies: 각 거절이유 순번별 전략 (모든 거절이유를 포함해야 함)
"""


def analyze_diff(chart: ClaimChart, office_action: OfficeAction) -> DiffAnalysis:
    """Claim Chart와 거절이유를 분석하여 대응 전략을 생성"""
    # Chart의 각 구성요소 매핑을 텍스트로 변환 — LLM이 읽기 쉬운 형태로 포맷팅
    chart_summary = "\n".join([
        f"- {m.our_element.element_id} [{m.similarity}]: {m.our_element.text}\n"
        f"  → 인용발명: {m.prior_art_text}\n"
        f"  → 분석: {m.analysis}"
        for m in chart.mappings
    ])

    # 거절이유 목록을 텍스트로 변환 — 상세 내용은 앞 300자로 축약 (토큰 절약)
    rejection_summary = "\n".join([
        f"{r.seq}. [{r.legal_basis}]\n  요약: {r.summary}\n  상세: {r.detail[:300]}..."
        for r in office_action.rejection_reasons
    ])

    return call_llm_structured(
        system_prompt=_SYSTEM,
        user_prompt=(
            f"[Claim Chart 분석 결과]\n{chart_summary}\n\n"
            f"[거절이유 ({len(office_action.rejection_reasons)}개)]\n{rejection_summary}\n\n"
            "핵심 차이점과 각 거절이유별 대응 전략을 분석하세요. "
            # 모든 거절이유 번호를 명시하여 누락 방지
            f"전략은 반드시 거절이유 {[r.seq for r in office_action.rejection_reasons]} 모두에 대해 작성하세요."
        ),
        response_schema=DiffAnalysis,  # 응답을 DiffAnalysis Pydantic 모델로 파싱
    )
