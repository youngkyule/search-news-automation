"""공용 유틸리티: 설정 파일 로딩, 사용한 주제 상태 관리."""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE_CONFIG_PATH = os.path.join(ROOT, "config", "site.json")
TOPICS_PATH = os.path.join(ROOT, "config", "topics.json")
USED_TOPICS_PATH = os.path.join(ROOT, "data", "used_topics.json")


def load_site_config():
    with open(SITE_CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_topics():
    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_used_topics():
    if not os.path.exists(USED_TOPICS_PATH):
        return []
    with open(USED_TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_used_topics(used):
    os.makedirs(os.path.dirname(USED_TOPICS_PATH), exist_ok=True)
    with open(USED_TOPICS_PATH, "w", encoding="utf-8") as f:
        json.dump(used, f, ensure_ascii=False, indent=2)


def pick_next_topics(count):
    """카테고리를 순환하며 아직 쓰지 않은 주제를 count개 고른다.
    모든 주제를 다 썼다면 사용 기록을 초기화하고 처음부터 다시 돈다.
    """
    topics_by_category = load_topics()
    used = set(load_used_topics())
    categories = list(topics_by_category.keys())

    picked = []
    cat_index = 0
    attempts = 0
    max_attempts = sum(len(v) for v in topics_by_category.values()) * 2 + len(categories) + 10

    while len(picked) < count and attempts < max_attempts:
        category = categories[cat_index % len(categories)]
        cat_index += 1
        attempts += 1

        candidates = [t for t in topics_by_category[category] if f"{category}::{t}" not in used]
        if not candidates:
            continue

        topic = candidates[0]
        picked.append({"category": category, "topic": topic})
        used.add(f"{category}::{topic}")

    if len(picked) < count:
        # 모든 주제를 소진한 경우: 사용 기록을 리셋하고 부족한 만큼 다시 채운다
        used = set()
        for category in categories:
            if len(picked) >= count:
                break
            for topic in topics_by_category[category]:
                if len(picked) >= count:
                    break
                key = f"{category}::{topic}"
                if key not in used:
                    picked.append({"category": category, "topic": topic})
                    used.add(key)

    return picked, used


def _image_tag(data_uri, alt):
    safe_alt = alt.replace('"', "'")
    return (
        f'<img src="{data_uri}" alt="{safe_alt}" '
        'style="max-width:100%;height:auto;border-radius:8px;margin:16px 0;" loading="lazy"/>'
    )


def insert_images_into_html(html, images):
    """images: [(data_uri, alt_text), ...]. <h2> 소제목 앞마다 이미지를 하나씩 배치하고,
    남는 이미지는 첫 문단 뒤에 추가한다. 이미지가 없으면 원본 html을 그대로 반환한다."""
    if not images:
        return html

    remaining = list(images)

    def repl(_match):
        if remaining:
            data_uri, alt = remaining.pop(0)
            return _image_tag(data_uri, alt) + "\n<h2>"
        return "<h2>"

    html = re.sub(r"<h2>", repl, html)

    if remaining:
        leftover_html = "".join(_image_tag(uri, alt) for uri, alt in remaining)
        new_html, count = re.subn(r"</p>", "</p>\n" + leftover_html, html, count=1)
        html = new_html if count else html + leftover_html

    return html


BYLINE_MARKER = 'class="kn-byline"'


def assign_reporter(category, site):
    reporters = site.get("reporters", {})
    return reporters.get(category, "편집팀")


def build_byline_html(category, site):
    """신문 기사처럼 [매체명] 기자명 기자 | 이메일 형태의 바이라인을 만든다."""
    reporter = assign_reporter(category, site)
    email = site.get("press_email", "")
    site_name = site.get("site_name", "검색뉴스")
    email_part = f' | <a href="mailto:{email}">{email}</a>' if email else ""
    return (
        f'<p {BYLINE_MARKER} style="color:#666;font-size:14px;margin:0 0 20px 0;">'
        f"[{site_name}] {reporter} 기자{email_part}</p>"
    )


def has_byline(html):
    return BYLINE_MARKER in html


def add_byline(html, category, site):
    """이미 바이라인이 있으면 그대로 두고, 없으면 맨 앞에 추가한다."""
    if has_byline(html):
        return html
    return build_byline_html(category, site) + "\n" + html
