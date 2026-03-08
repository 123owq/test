"""
파이프라인 실행기 — Tool 1~7 순차 실행
Agent 판단 로직 없이 단순 체이닝.
Agent 레이어가 필요 없는 단순 실행 시 이쪽을 사용.
"""

# 타입 힌트용 스키마 import
from schemas.office_action import OfficeAction          # 통지서 분석 결과 구조
from schemas.claim import Claim                         # 청구항 구조
from schemas.chart import ClaimChart, DiffAnalysis, AmendedClaim  # Chart/분석/보정 결과 구조

# 각 도구(Tool) import
from tools.tool1_oa_analyzer import analyze_office_action    # Tool 1: 통지서 분석
from tools.tool2_claim_parser import parse_claims            # Tool 2: 청구항 파싱
from tools.tool3_desc_mapper import map_description          # Tool 3: 상세설명 매핑
from tools.tool4_chart_generator import generate_claim_chart # Tool 4: Claim Chart 생성
from tools.tool5_diff_analyzer import analyze_diff           # Tool 5: 차이점 분석 + 전략
from tools.tool6_amendment_gen import generate_amendment     # Tool 6: 보정 청구항 생성
from tools.tool7_version_manager import save_version, get_latest_round  # Tool 7: 결과 저장
from tools.tool8_excel_exporter import export_excel                     # Tool 8: Excel Claim Chart 생성


def run_pipeline(
    office_action_text: str,              # 의견제출통지서 원문 텍스트
    our_claims_text: str,                 # 당사 특허 청구항 원문 텍스트
    our_description_text: str,            # 당사 특허 상세한 설명 원문 텍스트
    prior_art_texts: dict[str, str],      # {"인용발명 1": "원문", ...} 형태의 딕셔너리
    target_independent_claim_no: int = 1, # 보정할 독립항 번호 (기본값: 제1항)
) -> dict:
    """
    Tool 1 ~ 7을 순차 실행하는 기본 파이프라인.

    Args:
        office_action_text: 의견제출통지서 텍스트
        our_claims_text: 당사 청구항 전문
        our_description_text: 당사 상세한 설명 전문
        prior_art_texts: {인용발명ID: 인용발명텍스트} 딕셔너리
        target_independent_claim_no: 보정 대상 독립항 번호 (기본값: 1)

    Returns:
        실행 결과 딕셔너리 (모든 Tool 출력 포함)
    """
    print("\n" + "=" * 60)
    print(" 특허 심사대응 파이프라인 시작")
    print("=" * 60)

    # ── Tool 1: 통지서 분석 ────────────────────────────────────
    print("\n[Tool 1] 의견제출통지서 분석 중...")
    office_action: OfficeAction = analyze_office_action(office_action_text)  # LLM이 통지서 구조화
    print(f"  거절이유 {len(office_action.rejection_reasons)}개 추출")
    print(f"  인용발명 {len(office_action.cited_prior_arts)}건: "
          f"{[pa.reference for pa in office_action.cited_prior_arts]}")
    print(f"  제출기한: {office_action.submission_deadline}")

    # ── Tool 2: 청구항 파싱 ────────────────────────────────────
    print("\n[Tool 2] 청구항 파싱 중...")
    claims: list[Claim] = parse_claims(our_claims_text)  # LLM이 청구항을 독립항/종속항/구성요소 단위로 분해
    independent = [c for c in claims if c.claim_type == "independent"]  # 독립항만 필터링
    dependent = [c for c in claims if c.claim_type == "dependent"]      # 종속항만 필터링
    print(f"  총 {len(claims)}개 파싱 완료 "
          f"(독립항 {len(independent)}개, 종속항 {len(dependent)}개)")

    # ── Tool 3: 상세설명 매핑 ──────────────────────────────────
    print("\n[Tool 3] 상세설명 매핑 중...")
    claims = map_description(claims, our_description_text)  # 각 구성요소에 상세설명 근거 연결
    print("  구성요소-상세설명 매핑 완료")

    # 보정 대상 독립항 선택 — 지정 번호 없으면 첫 번째 독립항, 그것도 없으면 첫 번째 청구항
    target_claim = next(
        (c for c in claims if c.claim_number == target_independent_claim_no),
        independent[0] if independent else claims[0],
    )
    print(f"  보정 대상 청구항: 제{target_claim.claim_number}항 ({target_claim.claim_type})")

    # ── Tool 4: Claim Chart 생성 ───────────────────────────────
    charts: list[ClaimChart] = []  # 인용발명별 Chart를 담을 리스트
    for pa in office_action.cited_prior_arts:  # 인용발명 각각에 대해 Chart 생성
        prior_art_text = prior_art_texts.get(pa.id, "")  # 인용발명 ID로 원문 조회
        if not prior_art_text:
            prior_art_text = next(iter(prior_art_texts.values()), "")  # 매칭 실패 시 첫 번째 값으로 대체
        print(f"\n[Tool 4] Claim Chart 생성 중 ({pa.id})...")
        chart = generate_claim_chart(target_claim, prior_art_text, pa.id)  # 구성요소별 유사도 판정
        charts.append(chart)
        for m in chart.mappings:  # 구성요소별 판정 결과 출력
            print(f"  {m.our_element.element_id}: {m.similarity} "
                  f"(cosine={m.cosine_score:.3f if m.cosine_score else 'N/A'})")

    # ── Tool 5: 차이점 분석 + 전략 ────────────────────────────
    print("\n[Tool 5] 차이점 분석 및 전략 생성 중...")
    diff: DiffAnalysis = analyze_diff(charts[0], office_action)  # 첫 번째 Chart와 거절이유로 전략 수립
    print(f"  핵심 차이점 {len(diff.key_differences)}개")
    for s in diff.strategies:
        print(f"  거절이유 {s.rejection_seq}: [{s.strategy_type}]")

    # ── Tool 6: 보정 청구항 생성 ───────────────────────────────
    print("\n[Tool 6] 보정 청구항 생성 중...")
    amended: AmendedClaim = generate_amendment(target_claim, diff, our_description_text)  # LLM이 보정안 작성
    print(f"  보정 완료 (quality_score={amended.quality_score})")
    print(f"  해소된 거절이유: {amended.addresses_rejections}")

    # ── Tool 7: 결과 저장 ──────────────────────────────────────
    round_no = get_latest_round(office_action.application_no) + 1  # 기존 최대 차수 + 1
    result = {
        "office_action": office_action.model_dump(),          # Pydantic 모델 → 딕셔너리 변환
        "parsed_claims": [c.model_dump() for c in claims],   # 청구항 리스트 직렬화
        "claim_charts": [c.model_dump() for c in charts],    # Chart 리스트 직렬화
        "diff_analysis": diff.model_dump(),                   # 차이점 분석 직렬화
        "amended_claim": amended.model_dump(),                # 보정 결과 직렬화
    }
    saved_path = save_version(office_action.application_no, round_no, result)  # JSON 파일로 저장
    print(f"\n[Tool 7] 결과 저장 완료: {saved_path}")

    # ── Tool 8: Excel Claim Chart 생성 ─────────────────────────────────────
    print("\n[Tool 8] Excel Claim Chart 생성 중...")
    excel_path = export_excel(office_action, charts, diff, amended, round_no)
    print(f"[Tool 8] Excel 저장 완료: {excel_path}")

    print("\n" + "=" * 60)
    print(f" 파이프라인 완료 — 차수 {round_no}")
    print("=" * 60)

    return result  # 호출자에게 전체 결과 반환
