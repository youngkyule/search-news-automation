"""공용 유틸리티: 설정 파일 로딩, 사용한 주제 상태 관리."""
import json
import os

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
