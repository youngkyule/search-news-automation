"""매일 실행되는 메인 스크립트: 주제를 골라 기사를 생성하고 Blogger에 발행한다."""
import os
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import (
    add_byline,
    insert_images_into_html,
    load_site_config,
    pick_next_topics,
    pick_reporter,
    save_category_cursor,
    save_used_topics,
)
from generate_article import generate_article
from generate_images import generate_images_for_article

DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"


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


def main():
    site = load_site_config()
    count = int(os.environ.get("POSTS_PER_DAY", site.get("posts_per_day", 5)))

    picked, _, _ = pick_next_topics(count)
    if not picked:
        print("발행할 주제가 없습니다. config/topics.json을 확인하세요.")
        sys.exit(1)

    service = None if DRY_RUN else get_blogger_service()
    blog_id = os.environ.get("BLOGGER_BLOG_ID")

    results = []
    failed = None
    for i, item in enumerate(picked):
        category, topic = item["category"], item["topic"]
        print(f"[생성 중] ({category}) {topic}")
        try:
            article = generate_article(category, topic, model=site.get("model", "gemini-flash-lite-latest"))

            images_per_post = int(site.get("images_per_post", 4))
            if images_per_post > 0:
                print(f"  [이미지 생성 중] {images_per_post}장")
                images = generate_images_for_article(category, topic, count=images_per_post)
                print(f"  -> {len(images)}장 생성 완료")
                article["html"] = insert_images_into_html(article["html"], images)

            reporter = pick_reporter(site)
            article["html"] = add_byline(article["html"], reporter, site)
            print(f"  [담당 기자] {reporter['name']} 기자 ({reporter['email']})")

            if DRY_RUN:
                print(f"  -> (DRY RUN) 제목: {article['title']}")
            else:
                res = publish_post(service, blog_id, article)
                print(f"  -> 발행 완료: {res.get('url')}")
                time.sleep(5)  # Blogger API 호출 간 약간의 간격
        except Exception as exc:
            print(f"  [실패] ({category}) {topic}: {exc}")
            failed = (category, topic, exc)
            break

        results.append({"category": category, "topic": topic, "title": article["title"]})

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
