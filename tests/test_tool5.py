"""Tool 5: 차이점 분석 + 전략 생성기 단위 테스트"""

from schemas.chart import DiffAnalysis


def test_diff_returns_correct_type(diff_analysis):
    assert isinstance(diff_analysis, DiffAnalysis)


def test_diff_has_key_differences(diff_analysis):
    assert len(diff_analysis.key_differences) > 0


def test_diff_strategies_cover_all_rejections(office_action, diff_analysis):
    """3개 거절이유 모두에 대한 전략이 수립되어야 함"""
    strategy_seqs = {s.rejection_seq for s in diff_analysis.strategies}
    expected_seqs = {r.seq for r in office_action.rejection_reasons}
    assert strategy_seqs == expected_seqs, \
        f"전략 미수립 거절이유: {expected_seqs - strategy_seqs}"


def test_diff_strategy_types_valid(diff_analysis):
    valid_types = {"amendment", "argument", "both"}
    for s in diff_analysis.strategies:
        assert s.strategy_type in valid_types
