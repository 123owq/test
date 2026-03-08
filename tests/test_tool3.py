"""Tool 3: 상세설명 매퍼 단위 테스트"""


def test_mapping_fills_description(mapped_claim1):
    for elem in mapped_claim1.elements:
        assert elem.description_mapping is not None
        assert len(elem.description_mapping) > 5


def test_mapping_relevant_content(mapped_claim1):
    # 구성3 (목적수신주파수 설계) 매핑에 관련 내용이 있는지 확인
    elem3 = next(
        (e for e in mapped_claim1.elements if "주파수" in e.text or "송신" in e.text),
        None,
    )
    if elem3 and elem3.description_mapping:
        assert "상세설명에서" in elem3.description_mapping or len(elem3.description_mapping) > 20
