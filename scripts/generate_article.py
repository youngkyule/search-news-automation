"""Google Gemini API(무료 티어)로 '라하뉴스' 스타일의 문제해결형 기사를 생성한다."""
import json
import os
import re

import requests

GEMINI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

SYSTEM_PROMPT = """당신은 한국 생활정보 매체 '라하뉴스'의 콘텐츠 에디터입니다.
독자가 구글/네이버에 실제로 검색할 법한 생활 속 문제를 다루고, 신뢰할 수 있고
실질적으로 도움이 되는 해결 방법을 이해하기 쉬운 글로 정리해 전달합니다.

반드시 지켜야 할 원칙:
- 독창적인 문장으로 작성하고, 다른 사이트의 문장을 그대로 베끼지 않는다.
- 근거 없는 수치, 검증되지 않은 효능, 과장된 의학적/재정적 단정은 쓰지 않는다.
- 실제로 취재하거나 인터뷰한 것처럼 꾸미지 않는다. 특정 전문가의 발언, 실존
  인물의 사례, 출처가 불분명한 통계·설문 결과를 지어내서 인용하지 않는다.
  대신 보편적으로 알려진 원리, 공식 절차, 일반적으로 권장되는 방법을 바탕으로
  설명한다.
- 실제로 따라 할 수 있도록, 가능하면 구체적인 수치(소요 시간, 적정 온도·주기,
  준비물, 절차 순서 등)를 포함한 실용적인 단계와 팁을 제공한다. 다른 글에서도
  쓸 법한 뻔하고 추상적인 설명(예: "꾸준히 관리하세요", "전문가와 상담하세요"로
  때우기)만 반복하지 않는다.
- 같은 카테고리의 다른 주제라도 문장 구조와 표현을 기계적으로 복제하지 말고,
  주제별 특성에 맞는 구체적인 체크리스트·판단 기준·예외 상황을 다르게 구성한다.
- 광고성 문구나 특정 상품 홍보는 하지 않는다.
- 최종 결과물은 아래 JSON 스키마 하나만 출력한다. 다른 설명이나 코드블록 표시는 절대 붙이지 않는다.

JSON 스키마:
{
  "title": "검색 키워드를 포함한 기사 제목 (30자 내외)",
  "meta_description": "검색 결과에 노출될 요약 문장 (80~110자)",
  "labels": ["카테고리명", "핵심키워드1", "핵심키워드2"],
  "html": "블로거(Blogger)에 바로 게시할 수 있는 HTML 본문 전체"
}

html 본문 작성 규칙:
- <h2>, <h3> 소제목으로 구조화할 것 (최소 3개 이상의 소제목)
- 도입부: 문제 상황에 공감하는 2~3문장
- 본론: 원인 설명 + 단계별 해결 방법(번호 매긴 <ol> 또는 <ul> 사용)
- 중간에 "주의할 점" 또는 "전문가 상담이 필요한 경우" 섹션 포함
- 하단에 <h3>자주 묻는 질문</h3> 아래 FAQ 3~4개를 반드시 다음 HTML 형식
  그대로 포함할 것(검색결과 FAQ 리치 스니펫 자동 추출에 사용되므로 형식을
  절대 변형하지 말 것):
  <p><strong>Q1. (질문 내용)</strong><br>A1. (답변 내용)</p>
  <p><strong>Q2. (질문 내용)</strong><br>A2. (답변 내용)</p>
  (이런 식으로 Q1, Q2, Q3... 번호를 붙여 각 문답을 하나의 <p> 태그 안에
  <strong>질문</strong><br>답변 구조로 작성. <ul>/<li>나 <h4> 등 다른 태그로
  바꾸지 말 것)
- 전체 분량은 공백 포함 1500자 이상
- 마지막 문단은 요약으로 마무리
- 본문 맨 마지막 줄에 다음 문구를 그대로 포함할 것:
  <p><em>※ 본 기사는 일반적인 정보 제공을 목적으로 하며, 개별 상황에 따라 결과가 다를 수 있습니다. 구체적인 판단이 필요한 경우 관련 전문가 또는 공식 기관에 문의하시기 바랍니다.</em></p>
"""

USER_PROMPT_TEMPLATE = """카테고리: {category}
주제(검색 키워드): {topic}

위 주제로 '라하뉴스'에 게재할 기사를 JSON 스키마에 맞춰 작성해 주세요."""


def _extract_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```$", "", text.strip())
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"응답에서 JSON을 찾을 수 없습니다: {text[:200]}")
    return json.loads(text[start : end + 1])


def generate_article(category, topic, model="gemini-flash-lite-latest", api_key=None):
    api_key = api_key or os.environ["GEMINI_API_KEY"]

    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": USER_PROMPT_TEMPLATE.format(category=category, topic=topic)}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.9,
            "maxOutputTokens": 4096,
        },
    }

    url = GEMINI_ENDPOINT.format(model=model)
    resp = requests.post(url, params={"key": api_key}, json=body, timeout=120)
    resp.raise_for_status()
    result = resp.json()

    candidates = result.get("candidates") or []
    if not candidates:
        raise ValueError(f"Gemini 응답에 candidates가 없습니다: {result}")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(p.get("text", "") for p in parts)
    data = _extract_json(text)

    required = {"title", "meta_description", "labels", "html"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"생성 결과에 필수 필드가 없습니다: {missing}")

    if category not in data["labels"]:
        data["labels"].insert(0, category)

    return data


if __name__ == "__main__":
    import sys

    cat = sys.argv[1] if len(sys.argv) > 1 else "생활정보"
    top = sys.argv[2] if len(sys.argv) > 2 else "변기 막힘 뚫는 법"
    result = generate_article(cat, top)
    print(json.dumps(result, ensure_ascii=False, indent=2))
