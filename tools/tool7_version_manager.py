"""
Tool 7: 차수 관리자
결과를 로컬 JSON 파일로 저장/조회 (프로토타입 버전)
저장 경로: data/results/{출원번호}/round_{차수}.json
"""

import json                      # JSON 직렬화/역직렬화
from datetime import datetime    # 저장 시각 기록용
from pathlib import Path         # OS 독립적 파일 경로 처리

# 모든 결과 파일의 루트 디렉토리 — 이 파일 기준으로 두 단계 위 / data / results
_BASE_DIR = Path(__file__).parent.parent / "data" / "results"


def save_version(application_no: str, round_no: int, data: dict) -> str:
    """심사대응 결과를 차수별로 저장. 저장된 파일 경로 반환."""
    dir_path = _BASE_DIR / application_no             # 출원번호별 하위 디렉토리 경로
    dir_path.mkdir(parents=True, exist_ok=True)       # 디렉토리가 없으면 자동 생성 (이미 있어도 오류 없음)

    file_path = dir_path / f"round_{round_no:02d}.json"  # 파일명: round_01.json, round_02.json 등 (2자리 패딩)
    payload = {
        "application_no": application_no,        # 출원번호
        "round_no": round_no,                    # 차수 번호
        "saved_at": datetime.now().isoformat(),  # 저장 시각 (ISO 8601 형식)
        "data": data,                            # 실제 파이프라인 결과 딕셔너리
    }
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),  # 한글 유지 + 들여쓰기 2칸으로 보기 좋게 저장
        encoding="utf-8"
    )
    return str(file_path)  # 저장된 파일의 절대 경로 문자열 반환


def load_version(application_no: str, round_no: int) -> dict:
    """저장된 차수 결과를 로드"""
    file_path = _BASE_DIR / application_no / f"round_{round_no:02d}.json"
    if not file_path.exists():
        raise FileNotFoundError(f"버전 파일 없음: {file_path}")  # 파일 없으면 명확한 오류 발생
    return json.loads(file_path.read_text(encoding="utf-8"))  # JSON 파일을 읽어 딕셔너리로 반환


def list_versions(application_no: str) -> list[int]:
    """출원번호에 대한 저장된 차수 목록 반환"""
    dir_path = _BASE_DIR / application_no
    if not dir_path.exists():
        return []  # 해당 출원번호 디렉토리가 없으면 빈 리스트 반환
    return sorted([
        int(f.stem.replace("round_", ""))        # 파일명에서 "round_" 제거 후 정수 변환 (예: "round_02" → 2)
        for f in dir_path.glob("round_*.json")   # round_로 시작하는 json 파일만 대상
    ])


def get_latest_round(application_no: str) -> int:
    """가장 최근 차수 번호 반환 (없으면 0) — 다음 차수 계산에 사용"""
    versions = list_versions(application_no)
    return versions[-1] if versions else 0  # 저장된 차수가 없으면 0 반환 (다음 실행이 round_01이 됨)
