"""Tool 4: Claim Chart 생성기 단위 테스트"""

from schemas.chart import ClaimChart


def test_chart_returns_correct_type(claim_chart):
    assert isinstance(claim_chart, ClaimChart)


def test_chart_prior_art_id(claim_chart):
    assert claim_chart.prior_art_id == "인용발명 1"


def test_chart_mapping_count(claim1, claim_chart):
    # 청구항 1의 구성요소 수만큼 매핑 생성
    assert len(claim_chart.mappings) == len(claim1.elements)


def test_chart_similarity_values(claim_chart):
    valid_values = {"identical", "equivalent", "partially_different", "not_found"}
    for m in claim_chart.mappings:
        assert m.similarity in valid_values


def test_chart_matches_examiner_analysis(claim_chart):
    """
    심사관 분석 결과와 일치 여부 검증:
    - 구성1 (전자모듈): identical 또는 equivalent
    - 구성2 (리더부): identical 또는 equivalent
    - 구성3 (주파수 설계): partially_different
    """
    freq_related = [
        m for m in claim_chart.mappings
        if "주파수" in m.our_element.text or "송신" in m.our_element.text
    ]
    if freq_related:
        assert any(
            m.similarity in ("partially_different", "not_found")
            for m in freq_related
        ), "주파수 설계 구성요소가 identical로 잘못 판정됨"


def test_chart_has_analysis(claim_chart):
    for m in claim_chart.mappings:
        assert m.analysis and len(m.analysis) > 5
