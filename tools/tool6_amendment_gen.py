"""
Tool 6: 보정 청구항 생성기
Claim + DiffAnalysis + 상세설명 -> AmendedClaim
3개 거절이유를 모두 해소하는 보정안 생성
"""

from schemas.claim import Claim                  # 원본 청구항 구조
from schemas.chart import DiffAnalysis, AmendedClaim  # 차이점 분석 결과 + 보정 결과 구조
from llm.client import call_llm_structured       # LLM 호출 공통 함수

# LLM에게 보정 원칙과 품질 평가 기준을 상세히 지시하는 시스템 프롬프트
_SYSTEM = """당신은 한국 특허 청구항 보정 전문가입니다.
거절이유를 모두 해소하는 보정 청구항을 작성하세요.

보정 원칙:
1. §42③1 (실시가능성): 목적수신주파수 설계 방법을 실시가능하게 구체화
   - 타이어 무선 주파수 상수를 이용한 목적수신주파수 결정 방법을 명세서 근거에 따라 기재
2. §42④2 (명확성): '목적수신주파수' 계산/결정 방법을 청구항에 명확히 한정
   - "타이어 무선 주파수 상수에 기초하여 결정되는 목적수신주파수" 등으로 구체화
3. §29② (진보성): '타이어 무선 주파수 상수'를 독립항에 명시적으로 도입
   - 인용발명(사후 오프셋 교정)과의 차별성: 당사 발명(사전 설계)을 부각

주의사항:
- 보정은 출원 당초 명세서 범위를 벗어날 수 없음 (신규사항 추가 금지)
- 원본 청구항의 권리범위를 가능한 한 넓게 유지
- 한국 특허 청구항 문체 준수 ("~를 포함하는", "~인 것을 특징으로 하는" 등)

quality_score 기준 (0.0~1.0):
- 1.0: 3개 거절이유 모두 명확히 해소, 진보성 논거 강력
- 0.7~0.9: 대부분 해소, 일부 보완 필요
- 0.5~0.7: 일부 거절이유 해소 미흡
- 0.5 미만: 주요 거절이유 미해소

addresses_rejections: 실제로 해소된 거절이유 순번 리스트 (예: [1, 2, 3])
"""


def generate_amendment(
    claim: Claim,                    # 보정할 원본 청구항
    diff_analysis: DiffAnalysis,     # Tool 5에서 생성한 차이점 분석 + 대응 전략
    description_text: str = "",      # 당사 상세한 설명 원문 (신규사항 추가 방지용 참고)
) -> AmendedClaim:
    """보정 청구항 생성. quality_score < 0.7이면 Agent가 재시도"""
    # 전략 목록을 텍스트로 변환 — LLM 프롬프트에 포함할 요약문
    strategy_summary = "\n".join([
        f"- 거절이유 {s.rejection_seq} [{s.strategy_type}]: {s.rationale}"
        for s in diff_analysis.strategies
    ])

    # 핵심 차이점 목록을 텍스트로 변환
    diff_summary = "\n".join([f"- {d}" for d in diff_analysis.key_differences])

    # 상세설명은 앞 3000자만 전달 — 너무 길면 LLM 컨텍스트 낭비 + 비용 증가
    desc_context = description_text[:3000] if description_text else "(상세설명 미제공)"

    return call_llm_structured(
        system_prompt=_SYSTEM,
        user_prompt=(
            f"[원본 청구항 {claim.claim_number}]\n{claim.full_text}\n\n"  # 보정 대상 원문
            f"[핵심 차이점]\n{diff_summary}\n\n"                           # 인용발명과의 차이점
            f"[대응 전략]\n{strategy_summary}\n\n"                         # 거절이유별 전략
            f"[상세설명 참고]\n{desc_context}\n\n"                         # 명세서 근거 (신규사항 방지)
            "보정된 청구항과 보정 이유를 작성하고, "
            "addresses_rejections와 quality_score를 평가하세요."
        ),
        response_schema=AmendedClaim,  # 응답을 AmendedClaim Pydantic 모델로 파싱
    )
