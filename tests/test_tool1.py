"""Tool 1: 통지서 분석기 단위 테스트"""

from schemas.office_action import OfficeAction


def test_office_action_returns_correct_type(office_action):
    assert isinstance(office_action, OfficeAction)


def test_application_number(office_action):
    assert office_action.application_no == "10-2024-0003365"


def test_rejection_reason_count(office_action):
    assert len(office_action.rejection_reasons) == 3


def test_rejection_reason_legal_bases(office_action):
    bases = [r.legal_basis for r in office_action.rejection_reasons]
    assert any("42" in b and "3" in b and "1" in b for b in bases), \
        "§42③1 (실시가능성) 거절이유 누락"
    assert any("42" in b and "4" in b and "2" in b for b in bases), \
        "§42④2 (명확성) 거절이유 누락"
    assert any("29" in b and "2" in b for b in bases), \
        "§29② (진보성) 거절이유 누락"


def test_prior_art_count(office_action):
    assert len(office_action.cited_prior_arts) == 1


def test_prior_art_reference(office_action):
    ref = office_action.cited_prior_arts[0].reference
    assert "2007-141071" in ref or "141071" in ref


def test_submission_deadline(office_action):
    assert "2026" in office_action.submission_deadline
    assert "02" in office_action.submission_deadline or "2" in office_action.submission_deadline


def test_target_claims(office_action):
    assert len(office_action.all_target_claims) == 10
    assert 1 in office_action.all_target_claims
    assert 10 in office_action.all_target_claims
