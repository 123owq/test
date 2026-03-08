"""Tool 2: 청구항 파서 단위 테스트"""

from schemas.claim import Claim


def test_parse_returns_list(parsed_claims):
    assert isinstance(parsed_claims, list)
    assert len(parsed_claims) > 0


def test_total_claim_count(parsed_claims):
    assert len(parsed_claims) == 10


def test_independent_claims(parsed_claims):
    independent = [c for c in parsed_claims if c.claim_type == "independent"]
    # 청구항 1, 8이 독립항
    assert len(independent) == 2
    claim_numbers = {c.claim_number for c in independent}
    assert 1 in claim_numbers
    assert 8 in claim_numbers


def test_claim1_is_independent(claim1):
    assert claim1.claim_type == "independent"
    assert claim1.parent_claims == []


def test_claim1_has_elements(claim1):
    # 청구항 1은 전자모듈, 리더부, 주파수 설계 — 최소 3개 구성요소
    assert len(claim1.elements) >= 3


def test_claim2_is_dependent_on_1(parsed_claims):
    claim2 = next(c for c in parsed_claims if c.claim_number == 2)
    assert claim2.claim_type == "dependent"
    assert 1 in claim2.parent_claims


def test_claim2_mentions_twfc(parsed_claims):
    claim2 = next(c for c in parsed_claims if c.claim_number == 2)
    full_text_lower = claim2.full_text.lower() if claim2.full_text else ""
    elements_text = " ".join(e.text for e in claim2.elements).lower()
    assert "주파수 상수" in full_text_lower or "주파수 상수" in elements_text


def test_all_claims_have_full_text(parsed_claims):
    for c in parsed_claims:
        assert c.full_text and len(c.full_text) > 10
