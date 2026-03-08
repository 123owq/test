"""Tool 7: 차수 관리자 단위 테스트 (LLM 호출 없음 — 파일 I/O만 테스트)"""

import pytest
import json
from pathlib import Path
from tools.tool7_version_manager import (
    save_version, load_version, list_versions, get_latest_round
)

TEST_APP_NO = "TEST-2024-9999"                          # 실제 출원번호와 겹치지 않는 테스트용 번호
TEST_DATA = {"test_key": "test_value", "number": 42}    # 저장/로드 검증용 더미 데이터


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """각 테스트 실행 후 생성된 파일/디렉토리를 자동으로 정리 (autouse=True: 모든 테스트에 자동 적용)"""
    yield  # 테스트 실행
    # 테스트 종료 후 정리 실행
    base = Path(__file__).parent.parent / "data" / "results" / TEST_APP_NO
    if base.exists():
        import shutil
        shutil.rmtree(base)  # 테스트용 디렉토리 전체 삭제


def test_save_creates_file():
    """save_version 호출 시 파일이 실제로 생성되는지 확인"""
    path = save_version(TEST_APP_NO, 1, TEST_DATA)
    assert Path(path).exists()


def test_save_returns_correct_path():
    """반환된 경로에 출원번호와 차수가 올바르게 포함되는지 확인"""
    path = save_version(TEST_APP_NO, 1, TEST_DATA)
    assert TEST_APP_NO in path   # 출원번호가 경로에 포함되어야 함
    assert "round_01" in path    # 차수가 2자리 패딩으로 포함되어야 함


def test_load_returns_correct_data():
    """저장 후 로드 시 원본 데이터가 동일하게 복원되는지 확인"""
    save_version(TEST_APP_NO, 1, TEST_DATA)
    loaded = load_version(TEST_APP_NO, 1)
    assert loaded["data"] == TEST_DATA              # 저장한 데이터가 그대로 복원되어야 함
    assert loaded["application_no"] == TEST_APP_NO  # 출원번호 메타데이터 확인
    assert loaded["round_no"] == 1                  # 차수 메타데이터 확인


def test_list_versions_empty():
    """존재하지 않는 출원번호에 대해 빈 리스트를 반환하는지 확인"""
    result = list_versions("NONEXISTENT-APP")
    assert result == []


def test_list_versions_multiple():
    """여러 차수 저장 후 차수 번호 목록이 오름차순으로 반환되는지 확인"""
    save_version(TEST_APP_NO, 1, TEST_DATA)
    save_version(TEST_APP_NO, 2, TEST_DATA)
    save_version(TEST_APP_NO, 3, TEST_DATA)
    versions = list_versions(TEST_APP_NO)
    assert versions == [1, 2, 3]  # 정렬된 순서로 반환되어야 함


def test_get_latest_round_empty():
    """저장된 차수가 없을 때 0을 반환하는지 확인 (다음 실행이 round_01이 되도록)"""
    assert get_latest_round("NONEXISTENT-APP") == 0


def test_get_latest_round_after_save():
    """두 차수 저장 후 최신 차수(2)를 올바르게 반환하는지 확인"""
    save_version(TEST_APP_NO, 1, TEST_DATA)
    save_version(TEST_APP_NO, 2, TEST_DATA)
    assert get_latest_round(TEST_APP_NO) == 2


def test_load_nonexistent_raises():
    """존재하지 않는 파일 로드 시 FileNotFoundError가 발생하는지 확인"""
    with pytest.raises(FileNotFoundError):
        load_version("NONEXISTENT-APP", 99)
