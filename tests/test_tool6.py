"""Tool 6: 보정 청구항 생성기 단위 테스트"""

from schemas.chart import AmendedClaim


def test_amendment_returns_correct_type(amended_claim1):
    assert isinstance(amended_claim1, AmendedClaim)


def test_amendment_has_text(amended_claim1):
    assert amended_claim1.amended_text and len(amended_claim1.amended_text) > 50


def test_amendment_addresses_all_rejections(amended_claim1):
    """3개 거절이유를 모두 해소해야 함"""
    assert set(amended_claim1.addresses_rejections) >= {1, 2, 3}, \
        f"미해소 거절이유: {set(range(1, 4)) - set(amended_claim1.addresses_rejections)}"


def test_amendment_quality_score(amended_claim1):
    assert amended_claim1.quality_score is not None
    assert 0.0 <= amended_claim1.quality_score <= 1.0


def test_amendment_contains_key_terms(amended_claim1):
    """보정 청구항에 핵심 기술 용어가 포함되어야 함"""
    assert "목적수신주파수" in amended_claim1.amended_text or "수신주파수" in amended_claim1.amended_text
