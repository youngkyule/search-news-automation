"""기존에 이미 발행된 글들에 기자 바이라인([검색뉴스] 기자명 기자 | 이메일)을
소급 추가하는 1회성 스크립트. 이미 바이라인이 있는 글은 건너뛴다."""
import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import add_byline, has_byline, load_site_config


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
    print(f"총 {len(items)}개 글 확인", flush=True)

    for post in items:
        post_id = post["id"]
        title = post["title"]
        content = post["content"]
        labels = post.get("labels", [])
        category = labels[0] if labels else "생활정보"

        if has_byline(content):
            print(f"[건너뜀] 이미 바이라인이 있음: {title}", flush=True)
            continue

        new_content = add_byline(content, category, site)
        service.posts().update(
            blogId=blog_id, postId=post_id, body={"content": new_content}
        ).execute()
        print(f"[완료] {title} -> {category} 담당 기자 배정", flush=True)
        time.sleep(2)

    print("\n모든 글 처리 완료.", flush=True)


if __name__ == "__main__":
    main()
