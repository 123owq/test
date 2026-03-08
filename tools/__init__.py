# tools 패키지 공개 인터페이스 — 외부에서 `from tools import analyze_office_action` 형태로 사용 가능

from .tool1_oa_analyzer import analyze_office_action    # Tool 1: 의견제출통지서 → OfficeAction
from .tool2_claim_parser import parse_claims            # Tool 2: 청구항 텍스트 → list[Claim]
from .tool3_desc_mapper import map_description          # Tool 3: 구성요소 ↔ 상세설명 매핑
from .tool4_chart_generator import generate_claim_chart # Tool 4: 청구항 vs 인용발명 → ClaimChart
from .tool5_diff_analyzer import analyze_diff           # Tool 5: ClaimChart + OfficeAction → DiffAnalysis
from .tool6_amendment_gen import generate_amendment     # Tool 6: 보정 청구항 → AmendedClaim
from .tool7_version_manager import (                    # Tool 7: 결과 저장/조회 유틸리티
    save_version,       # 결과를 JSON 파일로 저장
    load_version,       # 저장된 차수 결과 로드
    list_versions,      # 출원번호에 대한 저장된 차수 목록 조회
    get_latest_round,   # 가장 최근 차수 번호 반환
)

__all__ = [
    "analyze_office_action",
    "parse_claims",
    "map_description",
    "generate_claim_chart",
    "analyze_diff",
    "generate_amendment",
    "save_version", "load_version", "list_versions", "get_latest_round",
]
