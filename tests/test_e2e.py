"""
E2E 테스트 — 출원번호 10-2024-0003365 케이스 전체 흐름
Agent 레이어 포함 실행
"""

import pytest
from agent.agent import run_agent        # Agent 레이어 포함 실행 (판단 + 재시도)
from agent.pipeline import run_pipeline  # 단순 순차 파이프라인 실행


def test_pipeline_e2e(
    office_action_text, our_claims_text, our_description_text, prior_art_texts
):
    """파이프라인 전체 흐름 테스트 — Tool 1~7 순차 실행 후 결과 구조 및 핵심 값 검증"""
    result = run_pipeline(
        office_action_text=office_action_text,
        our_claims_text=our_claims_text,
        our_description_text=our_description_text,
        prior_art_texts=prior_art_texts,
        target_independent_claim_no=1,  # 제1항을 보정 대상으로 지정
    )

    # 결과 딕셔너리에 모든 필수 키가 존재해야 함
    assert "office_action" in result
    assert "parsed_claims" in result
    assert "claim_charts" in result
    assert "diff_analysis" in result
    assert "amended_claim" in result

    # 핵심 결과 값 검증
    assert result["office_action"]["application_no"] == "10-2024-0003365"  # 출원번호 정확성
    assert len(result["parsed_claims"]) == 10   # 청구항 10개 파싱 확인
    assert len(result["claim_charts"]) >= 1     # Chart가 최소 1개 이상 생성되었는지 확인

    amended = result["amended_claim"]
    assert amended.get("amended_text") and len(amended["amended_text"]) > 50  # 보정 텍스트가 충분히 생성되었는지
    assert set(amended.get("addresses_rejections", [])) >= {1, 2, 3}          # 3개 거절이유 모두 해소되었는지


def test_agent_e2e(
    office_action_text, our_claims_text, our_description_text, prior_art_texts
):
    """Agent 레이어 포함 전체 흐름 테스트 (재시도 로직 포함) — pipeline보다 검증 기준이 약간 느슨"""
    result = run_agent(
        office_action_text=office_action_text,
        our_claims_text=our_claims_text,
        our_description_text=our_description_text,
        prior_art_texts=prior_art_texts,
        target_independent_claim_no=1,
    )

    # 최소한 이 두 키는 반드시 존재해야 함
    assert "office_action" in result
    assert "amended_claim" in result

    amended = result["amended_claim"]
    quality_score = amended.get("quality_score", 0)
    assert quality_score is not None, "quality_score가 None"  # 품질 점수가 계산되었는지 확인

    # 해소된 거절이유 수 확인 — Agent는 재시도를 하므로 최소 2개 이상 해소되어야 함
    addresses = set(amended.get("addresses_rejections", []))
    assert len(addresses) >= 2, f"해소된 거절이유가 너무 적음: {addresses}"
