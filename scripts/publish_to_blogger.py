"""매일 실행되는 메인 스크립트: 주제를 골라 기사를 생성하고 Blogger에 발행한다."""
import os
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import (
    add_byline,
    add_faq_jsonld,
    add_related_links,
    insert_images_into_html,
    load_site_config,
    pick_next_topics,
    save_category_cursor,
    save_used_topics,
)
from generate_article import generate_article
from generate_images import generate_images_for_article

from add_sources import block as sources_block, pick as pick_sources  # noqa: E402

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"
DUP_THRESHOLD = 0.6  # 새 주제의 글자 2-gram 중 기존 제목에 들어 있는 비율이 이 값 이상이면 같은 주제로 보고 건너뛴다


def _bigrams(s):
    s = "".join(ch for ch in s if ch.isalnum())
    return {s[i : i + 2] for i in range(len(s) - 1)}


def is_duplicate_topic(topic, live_titles):
    """이미 게시된 글 제목과 주제가 너무 비슷하면 True (같은 주제 반복 발행 방지)."""
    a = _bigrams(topic)
    if not a:
        return False
    for t in live_titles:
        b = _bigrams(t)
        if b and len(a & b) / len(a) >= DUP_THRESHOLD:
            return True
    return False


def fetch_live_titles(service, blog_id):
    titles, token = [], None
    while True:
        r = service.posts().list(blogId=blog_id, maxResults=100, pageToken=token, fetchBodies=False, status="LIVE").execute()
        titles += [p["title"] for p in r.get("items", [])]
        token = r.get("nextPageToken")
        if not token:
            return titles


def get_blogger_service():
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    return build("blogger", "v3", credentials=creds)


def publish_post(service, blog_id, article):
    body = {
        "title": article["title"],
        "content": article["html"],
        "labels": article["labels"],
    }
    meta_description = article.get("meta_description")
    if meta_description:
        body["searchDescription"] = meta_description[:150]
    return (
        service.posts()
        .insert(blogId=blog_id, body=body, isDraft=False)
        .execute()
    )


def add_related_links_after_publish(service, blog_id, res, article, category):
    """발행 직후, 같은 카테고리의 다른 글로 이어지는 "함께 보면 좋은 글" 링크를
    본문 끝에 추가한다(사이트 탐색성/구조적 유지관리 신호 보강, 2026-10-29).
    발행된 글 자신이 글 목록에 섞여 들어오지 않도록 exclude_post_id로 제외한다."""
    html_with_links = add_related_links(article["html"], service, blog_id, category, res["id"])
    if html_with_links == article["html"]:
        return
    body = {
        "title": article["title"],
        "content": html_with_links,
        "labels": article["labels"],
    }
    meta_description = article.get("meta_description")
    if meta_description:
        body["searchDescription"] = meta_description[:150]
    service.posts().update(blogId=blog_id, postId=res["id"], body=body).execute()


def main():
    site = load_site_config()
    count = int(os.environ.get("POSTS_PER_DAY", site.get("posts_per_day", 1)))

    picked, _, _ = pick_next_topics(count)
    if not picked:
        print("발행할 주제가 없습니다. config/topics.json을 확인하세요.")
        sys.exit(1)

    service = None if DRY_RUN else get_blogger_service()
    blog_id = os.environ.get("BLOGGER_BLOG_ID")

    live_titles = [] if DRY_RUN else fetch_live_titles(service, blog_id)

    results = []
    failed = None
    for i, item in enumerate(picked):
        category, topic = item["category"], item["topic"]
        if is_duplicate_topic(topic, live_titles):
            print(f"[건너뜀] 이미 비슷한 글이 있음: ({category}) {topic}")
            if not DRY_RUN:
                _, used_so_far, cursor_so_far = pick_next_topics(i + 1)
                save_used_topics(sorted(used_so_far))
                save_category_cursor(cursor_so_far)
            continue
        print(f"[생성 중] ({category}) {topic}")
        try:
            article = generate_article(category, topic, model=site.get("model", "gemini-flash-lite-latest"))
            # 제목 기준으로도 한 번 더 중복 확인
            if is_duplicate_topic(article["title"], live_titles):
                raise ValueError(f"생성된 제목이 기존 글과 너무 비슷함: {article['title']}")
            article["html"] = add_faq_jsonld(article["html"])
            srcs = pick_sources(article["title"])
            if srcs:
                article["html"] = article["html"].rstrip() + "\n" + sources_block(srcs)

            images_per_post = int(site.get("images_per_post", 4))
            if images_per_post > 0:
                print(f"  [이미지 생성 중] {images_per_post}장")
                images = generate_images_for_article(category, topic, count=images_per_post)
                print(f"  -> {len(images)}장 생성 완료")
                article["html"] = insert_images_into_html(article["html"], images)

            article["html"] = add_byline(article["html"], None, site)
            # 라벨은 카테고리 1개로 통일한다(글마다 제각각인 키워드 라벨이 수십 개 생기는 것을 방지).
            article["labels"] = [category]

            if DRY_RUN:
                print(f"  -> (DRY RUN) 제목: {article['title']}")
            else:
                res = publish_post(service, blog_id, article)
                print(f"  -> 발행 완료: {res.get('url')}")
                add_related_links_after_publish(service, blog_id, res, article, category)
                time.sleep(5)  # Blogger API 호출 간 약간의 간격
        except Exception as exc:
            print(f"  [실패] ({category}) {topic}: {exc}")
            failed = (category, topic, exc)
            break

        results.append({"category": category, "topic": topic, "title": article["title"]})
        live_titles.append(article["title"])

        if not DRY_RUN:
            # 이미 발행에 성공한 글까지만 반영한 상태를 즉시 저장한다.
            # 중간에 실패해도 다음 실행이 같은 주제를 중복 발행하지 않도록 함.
            _, used_so_far, cursor_so_far = pick_next_topics(i + 1)
            save_used_topics(sorted(used_so_far))
            save_category_cursor(cursor_so_far)

    print(f"\n총 {len(results)}개 기사 처리 완료.")
    for r in results:
        print(f" - [{r['category']}] {r['title']}")

    if failed:
        category, topic, exc = failed
        print(f"\n[중단] ({category}) {topic} 처리 중 오류로 이후 주제는 건너뜀: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
