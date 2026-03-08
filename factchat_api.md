---
title: '개요'
description: 'Gateway API 개요 및 빠른 시작'
order: 1
isFeatured: true
lastEditedDate: '2026-02-24'
tags: ['gateway', 'overview', 'api']
---

# Gateway API

<OverviewCard>

<TenantName /> Gateway API에 오신 것을 환영합니다! 🙌

Gateway API는 OpenAI, Anthropic, Google Gemini, xAI, Perplexity 등 주요 AI 제공업체의 모델을 **하나의 API 키와 하나의 Base URL**로 통합 제공하는 LLM 게이트웨이입니다.

기존에 사용하시던 OpenAI SDK나 Anthropic SDK를 그대로 사용하면서, Base URL만 변경하면 바로 시작할 수 있습니다.

</OverviewCard>

<Accordion>
  <AccordionButton>Gateway API란 무엇인가요?</AccordionButton>
  <AccordionPanel>
    Gateway API는 여러 AI 제공업체의 API를 하나의 통합 엔드포인트로 제공하는 프록시 서비스입니다.
    기존에는 OpenAI, Anthropic, Google 등 각 제공업체별로 별도의 API 키와 엔드포인트를 관리해야 했지만,
    Gateway를 사용하면 하나의 키로 모든 모델에 접근할 수 있습니다.
  </AccordionPanel>
</Accordion>

<Indent mt={12} />

## Base URL

| API 형식 | Base URL |
| --- | --- |
| OpenAI 호환 (Chat Completions) | `https://factchat-cloud.mindlogic.ai/v1/gateway` |
| Anthropic 네이티브 (Messages API) | `https://factchat-cloud.mindlogic.ai/v1/gateway/claude` |
| OpenAI Responses API | `https://factchat-cloud.mindlogic.ai/v1/gateway` |

## 전체 엔드포인트

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/v1/gateway/models/` | 사용 가능한 모델 목록 조회 |
| POST | `/v1/gateway/chat/completions/` | OpenAI 호환 채팅 완성 |
| POST | `/v1/gateway/claude/v1/messages/` | Anthropic 네이티브 Messages API |
| POST | `/v1/gateway/responses/` | OpenAI Responses API (o-시리즈) |
| POST | `/v1/gateway/audio/speech/` | 텍스트 음성 변환 (Google Gemini TTS) |
| POST | `/v1/gateway/images/generate/` | 이미지 생성 |
| POST | `/v1/gateway/video/generation/` | 비동기 비디오 생성 |

## 인증

모든 엔드포인트는 <TenantName /> API 키가 필요합니다. 두 가지 헤더 방식을 지원합니다:

```bash
# 방법 1: Authorization 헤더 (OpenAI 스타일)
Authorization: Bearer YOUR_API_KEY

# 방법 2: x-api-key 헤더 (Anthropic SDK 스타일)
x-api-key: YOUR_API_KEY
```

자세한 내용은 [인증](/docs/gateway/getting-started/authentication)을 참조하세요.

## 빠른 시작

<Banner variant="info">
  시작하기 전에 <TenantName /> API 키가 필요합니다. 아직 발급받지 않으셨다면 [인증 가이드](/docs/gateway/getting-started/authentication)를 참고해주세요.
</Banner>

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://factchat-cloud.mindlogic.ai/v1/gateway",
)

response = client.chat.completions.create(
    model="claude-sonnet-4-6",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

## 공식 제공업체 문서

| API | 공식 문서 |
| --- | --- |
| OpenAI Chat Completions | [platform.openai.com/docs/api-reference/chat](https://platform.openai.com/docs/api-reference/chat) |
| OpenAI Responses API | [platform.openai.com/docs/api-reference/responses](https://platform.openai.com/docs/api-reference/responses) |
| Anthropic Messages API | [docs.anthropic.com/en/api/messages](https://docs.anthropic.com/en/api/messages) |
| Google Gemini | [ai.google.dev/api/generate-content](https://ai.google.dev/api/generate-content) |

