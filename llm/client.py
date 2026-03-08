"""
LLM 호출 및 임베딩 클라이언트

- LLM: Factchat Gateway (Anthropic SDK, claude-sonnet-4-6)
- 임베딩: sentence-transformers BAAI/bge-m3 (로컬, 지연 로드)
"""

from __future__ import annotations  # 타입 힌트 전방 참조 허용

import os                           # 환경변수 읽기용 (API 키 로드)
from typing import TypeVar, Type    # 제네릭 타입 힌트용 — T가 어떤 Pydantic 모델이든 받을 수 있게 함

import anthropic                    # Anthropic SDK
from pydantic import BaseModel      # 응답을 파싱할 Pydantic 모델의 기반 클래스
from dotenv import load_dotenv      # .env 파일에서 환경변수 로드

load_dotenv()  # 프로젝트 루트의 .env 파일을 읽어 os.environ에 등록 (FACTCHAT_API 등)

T = TypeVar("T", bound=BaseModel)  # T는 BaseModel을 상속한 임의의 Pydantic 모델 — 반환 타입을 동적으로 지정
#제네릭은 '타입 자체'를 매개변수처럼 취급하는 기법 주면 그거 그대로 반환 T 네가 넣은 게 뭔지 끝까지 기억했다가 돌려줄게"라는 약속.
#bound: "그래도 Pydantic 모델 형제들만 들어와야 해"라는 최소한의 자격 요건.

DEFAULT_MODEL = "claude-haiku-4-5-20251001"  # 사용할 기본 모델

# Anthropic SDK 클라이언트 — base_url을 Factchat Gateway로 지정
_client = anthropic.Anthropic(
    base_url="https://factchat-cloud.mindlogic.ai/v1/gateway/claude",  # Anthropic 네이티브 엔드포인트
    api_key=os.environ.get("FACTCHAT_API", ""),                        # .env의 API 키 (없으면 빈 문자열 → 401 오류)
)


def call_llm_structured( # 각각 툴이 이걸 호출해서 형식 무조건 지키도록 하는것 !
    system_prompt: str,          # LLM에게 역할/규칙을 지시하는 시스템 프롬프트
    user_prompt: str,            # 실제 분석/처리할 내용을 담은 사용자 프롬프트
    response_schema: Type[T],    # 응답을 파싱할 Pydantic 모델 클래스 (예: OfficeAction, Claim 등)
    model: str = DEFAULT_MODEL,  # 사용할 모델 (기본값: DEFAULT_MODEL)
) -> T:
    """
    Factchat Gateway(Anthropic SDK)를 통해 LLM을 호출하고 결과를 Pydantic 모델로 반환.
    Anthropic tool_use 방식으로 구조화 출력 강제.
    """
    response = _client.messages.create(
        model=model,
        max_tokens=4096,
        system=system_prompt,                                   # 역할/규칙 지시
        messages=[
            {"role": "user", "content": user_prompt},          # 처리할 실제 내용
        ],
        tools=[{
            "name": "respond",                                  # 도구 이름 (임의)
            "description": "응답 반환",
            "input_schema": response_schema.model_json_schema(),  # Pydantic 모델의 JSON 스키마를 입력 스키마로 전달
        }],
        tool_choice={"type": "tool", "name": "respond"},        # 반드시 이 도구를 사용하도록 강제
    )

    # LLM이 반환한 tool_use 블록의 input(dict)을 Pydantic 모델로 파싱
    tool_use_block = next(b for b in response.content if b.type == "tool_use")
    return response_schema.model_validate(tool_use_block.input)  # dict → Pydantic 모델 인스턴스 변환



if __name__ == "__main__":
    # 연결 테스트 — `uv run python llm/client.py` 로 직접 실행 시 동작 확인
    from pydantic import BaseModel as BM

    class PingResponse(BM):
        message: str

    result = call_llm_structured(
        system_prompt="테스트입니다.",
        user_prompt="안녕하세요. message 필드에 '연결 성공'이라고 응답하세요.",
        response_schema=PingResponse,
    )
    print(f"LLM 연결 테스트: {result.message}")
