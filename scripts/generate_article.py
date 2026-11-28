"""Google Gemini API(무료 티어)로 '라하뉴스' 스타일의 문제해결형 기사를 생성한다."""
import datetime
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
- 수치 원칙(매우 중요): 기한·금액·요건·법 조항처럼 공식 기관이 정한 수치는
  확실히 아는 경우에만 쓰고, 그때도 '어느 기관의 안내 기준'인지 밝힌다. 확실하지
  않으면 숫자를 쓰지 말고 "금액·기간은 기관 공지에 따라 달라질 수 있으니 신청 전
  해당 사이트에서 확인하세요"처럼 확인 방법을 안내한다. 생활·건강 팁에서 근거를
  댈 수 없는 시간·온도·비율·횟수·용량(예: "60도에서 30분", "하루 3번", "1:1 희석")
  을 만들어 내지 않는다. 숫자가 없어도 판단 기준, 확인 순서, 흔한 실패 원인,
  예외 상황으로 충분히 구체적인 글을 쓸 수 있다.
- 제도·요금·절차는 바뀐다. 오늘 날짜는 사용자 메시지에 주어지며, 그보다 앞선 연도의
  제도를 '현재'인 것처럼 쓰지 않는다. 최신 내용을 확신할 수 없는 항목은 그 사실을
  분명히 적고 공식 사이트 확인을 안내한다.
- 해당 주제의 공식 기관·제조사 지원 페이지 이름(예: 정부24, 고용24, 한국소비자원,
  제조사 고객지원)을 본문에서 언급해 독자가 원문을 확인할 수 있게 한다. 실제
  존재가 확실하지 않은 기관명, URL, 전화번호는 쓰지 않는다.
- 다른 글에서도 쓸 법한 뻔하고 추상적인 설명(예: "꾸준히 관리하세요", "전문가와
  상담하세요"로 때우기)만 반복하지 않는다. 독자가 실제로 막히는 지점(신청이
  반려될 때, 예외에 해당할 때, 일반 방법이 안 통할 때)을 구체적으로 다룬다.
- 건강·법률·금융 주제는 진단·처방·법률 자문처럼 쓰지 않는다. 일반 정보임을 밝히고,
  병원·전문가·공식 기관에 가야 하는 신호나 상황을 분명히 적는다.
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
- <h2>, <h3> 소제목으로 구조화할 것 (최소 4개 이상의 소제목)
- 글의 구성 방식은 사용자 메시지의 '구성 방식'을 따른다. 모든 글을 같은 틀로
  쓰지 말고, 소제목 문구와 문단 전개를 주제에 맞게 다르게 짠다.
- 도입부: 문제 상황에 공감하는 2~3문장 (뻔한 인사말·반복 문구 금지)
- 본론: 원인 설명 + 단계별 해결 방법 + 흔한 실수와 예외 상황
- 필요하면 <table>로 비교·정리하고, 번호/글머리 목록은 의미가 있을 때만 쓴다
- 중간에 "주의할 점" 또는 "전문가·공식 기관에 문의해야 하는 경우" 섹션 포함
- 본문 어딘가에 "기준일" 문장을 넣는다: 예) "이 글은 {기준일} 기준 공개된 안내를 바탕으로 정리했으며, 이후 바뀔 수 있습니다."
- 하단에 <h3>자주 묻는 질문</h3> 아래 FAQ 3~4개를 반드시 다음 HTML 형식
  그대로 포함할 것(검색결과 FAQ 리치 스니펫 자동 추출에 사용되므로 형식을
  절대 변형하지 말 것):
  <p><strong>Q1. (질문 내용)</strong><br>A1. (답변 내용)</p>
  <p><strong>Q2. (질문 내용)</strong><br>A2. (답변 내용)</p>
  (이런 식으로 Q1, Q2, Q3... 번호를 붙여 각 문답을 하나의 <p> 태그 안에
  <strong>질문</strong><br>답변 구조로 작성. <ul>/<li>나 <h4> 등 다른 태그로
  바꾸지 말 것)
- 전체 분량은 공백 제외 2,500자 이상 (분량을 채우려고 같은 말을 반복하지 말 것)
- 마지막 문단은 요약으로 마무리
- 본문 맨 마지막 줄에 다음 문구를 그대로 포함할 것:
  <p><em>※ 본 기사는 일반적인 정보 제공을 목적으로 하며, 개별 상황에 따라 결과가 다를 수 있습니다. 구체적인 판단이 필요한 경우 관련 전문가 또는 공식 기관에 문의하시기 바랍니다.</em></p>
"""

USER_PROMPT_TEMPLATE = """오늘 날짜: {today}
카테고리: {category}
주제(검색 키워드): {topic}
구성 방식: {layout}

위 주제로 '라하뉴스'에 게재할 기사를 JSON 스키마에 맞춰 작성해 주세요.
'기준일'에는 위 오늘 날짜(연·월)를 사용하세요."""

# 모든 글이 같은 틀(원인-해결-주의-FAQ)로 찍혀 나오지 않도록 글마다 다른 구성 방식을 준다.
LAYOUTS = [
    "독자가 실제로 겪는 상황별 분기형: '이런 경우엔 이렇게'로 나누어 설명한다.",
    "흔한 실수와 실패 사례 중심형: 사람들이 자주 틀리는 지점과 되돌리는 방법을 앞에 둔다.",
    "확인 순서 중심형: 먼저 확인할 것 → 다음에 할 것 → 안 될 때의 대안 순으로 전개한다.",
    "비교·정리형: 선택지나 방법의 차이를 표(<table>)로 비교하고 어떤 경우에 무엇이 맞는지 설명한다.",
    "궁금증 해소형: 독자가 실제로 묻는 질문 4~5개를 소제목으로 삼아 차례로 답한다.",
    "예외·주의 중심형: 기본 절차는 짧게, 예외 상황과 막혔을 때의 대처를 깊이 다룬다.",
]

MIN_TEXT_CHARS = 2500
BANNED_PHRASES = ["직접 해봤", "제가 써", "저는 ", "인터뷰", "취재 결과", "설문조사 결과"]


def validate_article(data):
    """저품질·허위 표현이 섞인 결과를 발행 전에 걸러낸다. 문제 목록(빈 리스트면 통과)을 돌려준다."""
    html = data.get("html", "")
    text = re.sub(r"<[^>]+>", "", html)
    problems = []
    n_chars = len(re.sub(r"\s", "", text))
    if n_chars < MIN_TEXT_CHARS:
        problems.append(f"본문이 너무 짧음({n_chars}자)")
    if len(re.findall(r"<h[23][^>]*>", html)) < 4:
        problems.append("소제목 4개 미만")
    if "자주 묻는 질문" not in html or not re.search(r"<strong>Q1\.", html):
        problems.append("FAQ 형식 누락")
    for ph in BANNED_PHRASES:
        if ph in text:
            problems.append(f"금지 표현 포함: {ph.strip()}")
    return problems


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


def pick_layout(topic):
    """주제 문자열로 구성 방식을 고정 선택한다(같은 주제는 항상 같은 방식, 주제마다는 다르게)."""
    return LAYOUTS[sum(ord(c) for c in topic) % len(LAYOUTS)]


def generate_article(category, topic, model="gemini-flash-lite-latest", api_key=None, max_attempts=3):
    """기사를 생성하고 validate_article을 통과할 때까지 최대 max_attempts번 다시 시도한다."""
    last = None
    for attempt in range(1, max_attempts + 1):
        data = _generate_once(category, topic, model, api_key)
        problems = validate_article(data)
        if not problems:
            return data
        last = problems
        print(f"  [재시도 {attempt}/{max_attempts}] 품질 검사 미통과: {', '.join(problems)}")
    raise ValueError(f"품질 검사를 통과하지 못해 발행하지 않음: {', '.join(last)}")


def _generate_once(category, topic, model, api_key):
    api_key = api_key or os.environ["GEMINI_API_KEY"]
    today = datetime.date.today()
    today_str = f"{today.year}년 {today.month}월 {today.day}일"

    body = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": USER_PROMPT_TEMPLATE.format(
                            today=today_str, category=category, topic=topic, layout=pick_layout(topic)
                        )
                    }
                ],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.7,
            "maxOutputTokens": 8192,
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
