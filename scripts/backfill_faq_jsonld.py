"""기존에 발행된 글에 FAQPage 구조화 데이터(schema.org JSON-LD)가 없으면 추가하는
1회성 스크립트.

2026-10-29: 애드센스 재신청 전 "실제적인 사용자 관심" 신호를 보강하기 위해 추가.
검색결과에 FAQ 아코디언이 함께 노출되면 클릭률(CTR)이 올라가는 효과가 있고,
봇/가짜 트래픽이 아닌 합법적인 방법이다. 글의 FAQ 섹션 형식이 예상과 다르면
(extract_faq_pairs가 빈 리스트를 반환하면) 건너뛴다 — 잘못된 구조화 데이터를
넣는 것보다 생략하는 편이 안전하다."""
import os
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import add_faq_jsonld, has_faq_jsonld


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
    blog_id = os.environ["BLOGGER_BLOG_ID"]
    service = get_blogger_service()

    posts = service.posts().list(blogId=blog_id, maxResults=50, fetchBodies=True).execute()
    items = posts.get("items", [])
    print(f"총 {len(items)}개 글 확인\n", flush=True)

    for post in items:
        content = post["content"]
        if has_faq_jsonld(content):
            print(f"[건너뜀] 이미 FAQ 구조화 데이터 있음: {post['title'][:30]}", flush=True)
            continue

        new_content = add_faq_jsonld(content)
        if new_content == content:
            print(f"[건너뜀] FAQ 형식을 인식하지 못함: {post['title'][:30]}", flush=True)
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
        print(f"[완료] {post['title'][:30]}", flush=True)
        time.sleep(2)

    print("\n모든 글 처리 완료.", flush=True)


if __name__ == "__main__":
    main()
