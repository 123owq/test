"""
얇은 Agent 레이어 — 판단 지점 2개

판단 지점 1: 선행특허 루프
  인용발명이 여러 건일 때 Tool 4~5를 건별로 실행하고,
  차이점이 가장 명확한(공략하기 유리한) 인용발명을 전략 기준으로 선택.

판단 지점 2: 보정 실패 재시도
  Tool 6 결과의 quality_score < 0.7 또는 일부 거절이유 미해소 시
  전략을 강화하여 최대 MAX_RETRY회 재시도.
"""

# 타입 힌트용 스키마 import — 각 도구의 입출력 데이터 구조 정의
from schemas.office_action import OfficeAction       # 의견제출통지서 분석 결과 구조
from schemas.claim import Claim                       # 청구항 한 개의 구조
from schemas.chart import ClaimChart, DiffAnalysis, AmendedClaim  # Chart/분석/보정 결과 구조

# 각 도구(Tool) import
from tools.tool4_chart_generator import generate_claim_chart  # Tool 4: 청구항 vs 인용발명 비교표 생성
from tools.tool5_diff_analyzer import analyze_diff            # Tool 5: 차이점 분석 + 대응 전략 수립
from tools.tool6_amendment_gen import generate_amendment      # Tool 6: 보정 청구항 생성
from tools.tool7_version_manager import save_version, get_latest_round  # Tool 7: 결과 저장/차수 조회
from tools.tool8_excel_exporter import export_excel                     # Tool 8: Excel Claim Chart 생성

from llm.client import call_llm_structured  # LLM 호출 공통 함수

QUALITY_THRESHOLD = 0.7  # 보정 결과가 이 점수 이상이어야 성공으로 판정 (0~1 사이)
MAX_RETRY = 2             # 보정 실패 시 최대 재시도 횟수 (초과하면 최선의 결과로 종료)


def run_agent(
    office_action_text: str,           # 의견제출통지서 원문 텍스트
    our_claims_text: str,              # 당사 특허 청구항 원문 텍스트
    our_description_text: str,         # 당사 특허 상세한 설명 원문 텍스트
    prior_art_texts: dict[str, str],   # {"인용발명 1": "인용발명 원문", ...} 형태의 딕셔너리
    target_independent_claim_no: int = 1,  # 보정할 독립항 번호 (기본값: 제1항)
) -> dict:
    """
    Agent 레이어를 포함한 실행.
    판단 지점 2개를 통해 선행특허 루프와 보정 재시도를 제어.
    """
    # Tool 1~3은 함수 내부에서 import — 순환 import 방지 및 지연 로드
    from tools.tool1_oa_analyzer import analyze_office_action  # Tool 1: 통지서 분석
    from tools.tool2_claim_parser import parse_claims          # Tool 2: 청구항 파싱
    from tools.tool3_desc_mapper import map_description        # Tool 3: 상세설명 매핑

    print("\n" + "=" * 60)
    print(" 특허 심사대응 Agent 시작")
    print("=" * 60)

    # ── Tool 1: 의견제출통지서 분석 ────────────────────────────
    print("\n[Agent > Tool 1] 통지서 분석...")
    office_action: OfficeAction = analyze_office_action(office_action_text)  # LLM이 통지서를 읽고 거절이유, 인용발명 등을 구조화
    print(f"  거절이유 {len(office_action.rejection_reasons)}개, "
          f"인용발명 {len(office_action.cited_prior_arts)}건")

    # ── Tool 2: 청구항 파싱 ────────────────────────────────────
    print("\n[Agent > Tool 2] 청구항 파싱...")
    claims: list[Claim] = parse_claims(our_claims_text)  # LLM이 청구항 텍스트를 독립항/종속항/구성요소 단위로 분해
    print(f"  {len(claims)}개 파싱 완료")

    # ── Tool 3: 상세설명 매핑 ──────────────────────────────────
    print("\n[Agent > Tool 3] 상세설명 매핑...")
    claims = map_description(claims, our_description_text)  # 각 청구항 구성요소가 상세한 설명의 어느 부분에 해당하는지 연결

    # 보정 대상 독립항 선택 — 지정 번호가 없으면 첫 번째 독립항, 그것도 없으면 첫 번째 청구항
    target_claim = next(
        (c for c in claims if c.claim_number == target_independent_claim_no),  # 지정 번호의 청구항 검색
        next((c for c in claims if c.claim_type == "independent"), claims[0]),  # 없으면 첫 번째 독립항
    )

    # ── 판단 지점 1: 선행특허 루프 ────────────────────────────
    # 인용발명이 여러 건일 때 각각에 대해 Chart를 만들고, 우리에게 가장 유리한 것을 선택
    print(f"\n[Agent > 판단 지점 1] 선행특허 {len(office_action.cited_prior_arts)}건 처리")
    charts: list[ClaimChart] = []  # 인용발명별 Chart를 담을 리스트

    for pa in office_action.cited_prior_arts:  # 심사관이 인용한 선행발명 각각에 대해 반복
        prior_art_text = prior_art_texts.get(pa.id, "")  # 인용발명 ID로 원문 텍스트 조회
        if not prior_art_text:
            prior_art_text = next(iter(prior_art_texts.values()), "")  # 매칭 실패 시 첫 번째 인용발명 원문으로 대체
        print(f"  Tool 4: Claim Chart 생성 ({pa.id})...")
        chart = generate_claim_chart(target_claim, prior_art_text, pa.id)  # 당사 청구항 구성요소 vs 인용발명 유사도 판정
        charts.append(chart)  # 결과를 리스트에 추가

    # 인용발명이 여러 건이면 차이점이 가장 많은(우리에게 유리한) chart를 전략 기준으로 선택
    primary_chart = _select_primary_chart(charts)
    print(f"  기준 차트: {primary_chart.prior_art_id} "
          f"(diff_count={_diff_count(primary_chart)})")

    # ── Tool 5: 차이점 분석 + 전략 수립 ───────────────────────
    print("\n[Agent > Tool 5] 차이점 분석 + 전략 생성...")
    diff: DiffAnalysis = analyze_diff(primary_chart, office_action)  # Chart와 거절이유를 종합해 거절이유별 대응 전략 생성

    # ── 판단 지점 2: 보정 실패 재시도 ────────────────────────
    total_rejections = set(r.seq for r in office_action.rejection_reasons)  # 해소해야 할 거절이유 번호 집합 (예: {1, 2, 3})
    amended: AmendedClaim | None = None  # 보정 결과 초기화

    for attempt in range(1, MAX_RETRY + 2):  # 최초 1회 + 재시도 MAX_RETRY회 = 총 MAX_RETRY+1회 시도
        print(f"\n[Agent > 판단 지점 2] Tool 6: 보정 생성 (시도 {attempt}/{MAX_RETRY + 1})...")
        amended = generate_amendment(target_claim, diff, our_description_text)  # LLM이 보정 청구항 생성

        score = amended.quality_score or 0.0  # 보정 품질 점수 (None이면 0으로 처리)
        missing = total_rejections - set(amended.addresses_rejections)  # 아직 해소되지 않은 거절이유 번호 집합

        if score >= QUALITY_THRESHOLD and not missing:
            # 품질 점수가 기준 이상이고 모든 거절이유가 해소된 경우 → 성공으로 종료
            print(f"  보정 성공 (quality_score={score:.2f}, 미해소={missing})")
            break

        if attempt <= MAX_RETRY:
            # 아직 재시도 횟수가 남아있으면 전략을 강화한 뒤 다시 시도
            print(f"  보정 미흡 (score={score:.2f}, 미해소 거절이유={missing}) — 전략 강화 후 재시도")
            diff = _strengthen_strategy(diff, missing, office_action)  # 미해소 거절이유에 집중한 강화 전략 재생성
        # attempt > MAX_RETRY이면 루프 자연 종료 — 최선의 결과(amended)를 그대로 사용

    # ── Tool 7: 결과 저장 ──────────────────────────────────────
    round_no = get_latest_round(office_action.application_no) + 1  # 기존 최대 차수 + 1 = 이번 차수 번호
    result = {
        "office_action": office_action.model_dump(),          # OfficeAction 객체를 딕셔너리로 변환
        "parsed_claims": [c.model_dump() for c in claims],   # Claim 리스트 전체를 직렬화
        "claim_charts": [c.model_dump() for c in charts],    # 인용발명별 Chart 전체를 직렬화
        "diff_analysis": diff.model_dump(),                   # 차이점 분석/전략을 직렬화
        "amended_claim": amended.model_dump() if amended else {},  # 보정 결과 직렬화 (None이면 빈 딕셔너리)
    }
    saved_path = save_version(office_action.application_no, round_no, result)  # JSON 파일로 디스크에 저장
    print(f"\n[Agent > Tool 7] 결과 저장 완료: {saved_path}")

    # ── Tool 8: Excel Claim Chart 생성 ─────────────────────────────────────
    print("\n[Agent > Tool 8] Excel Claim Chart 생성 중...")
    if amended:
        excel_path = export_excel(office_action, charts, diff, amended, round_no)
        print(f"[Agent > Tool 8] Excel 저장 완료: {excel_path}")
    else:
        print("[Agent > Tool 8] 보정 결과 없음 — Excel 생성 건너뜀")

    print("=" * 60)

    return result  # 호출자에게 전체 결과 딕셔너리 반환


# ── 내부 헬퍼 ──────────────────────────────────────────────────────────────


def _diff_count(chart: ClaimChart) -> int:
    """Chart에서 인용발명과 차이가 있는 구성요소 수를 반환 (partially_different 또는 not_found)"""
    return sum(
        1 for m in chart.mappings                                        # 모든 구성요소 매핑을 순회
        if m.similarity in ("partially_different", "not_found")          # 차이가 있는 것만 카운트
    )


def _select_primary_chart(charts: list[ClaimChart]) -> ClaimChart:
    """여러 인용발명 중 우리에게 가장 유리한(차이점이 많은) chart 선택"""
    if len(charts) == 1:
        return charts[0]  # 인용발명이 1건이면 선택할 것 없이 그대로 반환
    return max(charts, key=_diff_count)  # 차이점 개수가 가장 많은 chart 반환 (우리에게 유리한 논거)


def _strengthen_strategy(
    diff: DiffAnalysis,              # 기존 차이점 분석 결과
    missing_rejections: set[int],    # 아직 해소되지 않은 거절이유 번호 집합
    office_action: OfficeAction,     # 원본 통지서 분석 결과 (거절이유 상세 내용 참조용)
) -> DiffAnalysis:
    """미해소 거절이유에 집중한 강화 전략 재생성"""
    # 재시도 전용 시스템 프롬프트 — 이전 시도가 실패했음을 LLM에게 알림
    _RETRY_SYSTEM = """이전 보정 시도가 일부 거절이유를 해소하지 못했습니다.
미해소된 거절이유에 집중하여 더 강력하고 구체적인 대응 전략을 수립하세요.
이전 전략보다 더 명확한 기술적 근거와 구체적인 보정 방향을 제시해야 합니다."""

    # 미해소 거절이유의 상세 내용만 추출 (앞 200자로 축약해서 토큰 절약)
    missing_details = "\n".join([
        f"- 거절이유 {r.seq} [{r.legal_basis}]: {r.detail[:200]}..."
        for r in office_action.rejection_reasons
        if r.seq in missing_rejections  # 미해소된 것만 필터링
    ])

    # 기존 차이점 분석 결과를 텍스트로 변환 (LLM이 이전 맥락을 이어받을 수 있게)
    existing_diffs = "\n".join([f"- {d}" for d in diff.key_differences])

    # LLM에게 강화 전략 재생성 요청 — 결과는 DiffAnalysis 구조로 반환
    return call_llm_structured(
        system_prompt=_RETRY_SYSTEM,
        user_prompt=(
            f"[미해소 거절이유]\n{missing_details}\n\n"
            f"[기존 차이점 분석]\n{existing_diffs}\n\n"
            "미해소 거절이유를 해소할 수 있는 강화된 전략을 수립하세요."
        ),
        response_schema=DiffAnalysis,  # 응답을 DiffAnalysis Pydantic 모델로 파싱
    )
