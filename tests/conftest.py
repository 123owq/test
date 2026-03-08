"""공통 픽스처 — 샘플 데이터 로드 + LLM 결과 캐싱 (session scope)"""

import pytest
from pathlib import Path

SAMPLES_DIR = Path(__file__).parent.parent / "data" / "samples"  # 샘플 데이터 디렉토리 경로


# ── 원본 텍스트 (파일 로드만 — LLM 호출 없음) ────────────────────────────────

@pytest.fixture(scope="session")  # session: 전체 테스트 세션에서 딱 한 번만 실행
def office_action_text() -> str:
    """의견제출통지서 원문 텍스트 로드"""
    return (SAMPLES_DIR / "office_action_10-2024-0003365.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def our_claims_text() -> str:
    """당사 특허 청구항 원문 텍스트 로드"""
    return (SAMPLES_DIR / "our_patent_claims.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def our_description_text() -> str:
    """당사 특허 상세한 설명 원문 텍스트 로드"""
    return (SAMPLES_DIR / "our_patent_description.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def prior_art_text() -> str:
    """인용발명(일본 특허 JP2007-141071) 원문 텍스트 로드"""
    return (SAMPLES_DIR / "prior_art_jp2007141071.txt").read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def prior_art_texts(prior_art_text) -> dict[str, str]:
    """인용발명 ID → 원문 딕셔너리 (pipeline/agent에서 사용하는 형태)"""
    return {"인용발명 1": prior_art_text}


# ── LLM 결과 캐싱 (세션당 1회 호출) ──────────────────────────────────────────
# 각 fixture는 처음 요청 시 LLM을 호출하고, 이후 같은 세션에서는 캐시된 결과 재사용
# → 73회였던 LLM 호출을 ~5회로 감소

@pytest.fixture(scope="session")
def office_action(office_action_text):
    """Tool 1 실행 결과 캐싱 — 통지서 분석 (OfficeAction)"""
    from tools.tool1_oa_analyzer import analyze_office_action
    return analyze_office_action(office_action_text)


@pytest.fixture(scope="session")
def parsed_claims(our_claims_text):
    """Tool 2 실행 결과 캐싱 — 청구항 파싱 (list[Claim])"""
    from tools.tool2_claim_parser import parse_claims
    return parse_claims(our_claims_text)


@pytest.fixture(scope="session")
def claim1(parsed_claims):
    """parsed_claims에서 제1항만 추출 — tool3/4/5/6 테스트의 공통 입력"""
    return next(c for c in parsed_claims if c.claim_number == 1)


@pytest.fixture(scope="session")
def claim_chart(claim1, prior_art_text):
    """Tool 4 실행 결과 캐싱 — 제1항 vs 인용발명 1 Claim Chart"""
    from tools.tool4_chart_generator import generate_claim_chart
    return generate_claim_chart(claim1, prior_art_text, "인용발명 1")


@pytest.fixture(scope="session")
def diff_analysis(claim_chart, office_action):
    """Tool 5 실행 결과 캐싱 — 차이점 분석 + 대응 전략 (DiffAnalysis)"""
    from tools.tool5_diff_analyzer import analyze_diff
    return analyze_diff(claim_chart, office_action)


@pytest.fixture(scope="session")
def mapped_claim1(claim1, our_description_text):
    """Tool 3 실행 결과 캐싱 — 제1항 구성요소에 상세설명 매핑이 채워진 Claim"""
    from tools.tool3_desc_mapper import map_description
    return map_description([claim1], our_description_text)[0]  # 리스트에서 첫 번째(유일한) 항목 추출


@pytest.fixture(scope="session")
def amended_claim1(claim1, diff_analysis, our_description_text):
    """Tool 6 실행 결과 캐싱 — 제1항 보정 결과 (AmendedClaim)"""
    from tools.tool6_amendment_gen import generate_amendment
    return generate_amendment(claim1, diff_analysis, our_description_text)
