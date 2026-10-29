"""기존에 발행된 글에 "함께 보면 좋은 글"(관련 글) 섹션이 없으면 추가하는 1회성 스크립트.

2026-10-29: 애드센스 승인 거절 사유("가치가 별로 없는 콘텐츠",
"지속적인 콘텐츠 큐레이션 및 구조적 유지관리") 대응. 신규 발행 글에는
publish_to_blogger.py가 자동으로 관련 글 섹션을 붙이지만, 이미 발행된
글에는 없으므로 이 스크립트로 한 번에 보완한다. 이미 섹션이 있는 글은
건너뛴다(재실행해도 중복 추가되지 않음)."""
import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import add_related_links, has_related_links, load_site_config, resolve_category


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


def main():
    site = load_site_config()
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    service = get_blogger_service()

    posts = service.posts().list(blogId=blog_id, maxResults=50, fetchBodies=True).execute()
    items = posts.get("items", [])
    print(f"총 {len(items)}개 글 확인\n", flush=True)

    for post in items:
        content = post["content"]
        if has_related_links(content):
            print(f"[건너뜀] 이미 관련 글 섹션 있음: {post['title'][:30]}", flush=True)
            continue

        category = resolve_category(post.get("labels", []), site)
        new_content = add_related_links(content, service, blog_id, category, post["id"])
        if new_content == content:
            print(f"[건너뜀] 같은 카테고리의 다른 글이 없음: {post['title'][:30]}", flush=True)
            continue

        body = {
            "title": post["title"],
            "labels": post.get("labels", []),
            "content": new_content,
        }
        search_description = post.get("searchDescription")
        if search_description:
            body["searchDescription"] = search_description

        service.posts().update(blogId=blog_id, postId=post["id"], body=body).execute()
        print(f"[완료] {post['title'][:30]} ({category})", flush=True)
        time.sleep(2)

    print("\n모든 글 처리 완료.", flush=True)


if __name__ == "__main__":
    main()
