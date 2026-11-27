"""data/cleanup_plan.json 의 'draft' 목록 글을 Blogger에서 초안(비공개)으로 되돌린다.

삭제가 아니라 revert(초안 전환)이므로 Blogger 관리 화면에서 언제든 다시 게시할 수 있다.
기본은 dry-run. 실제 실행: python cleanup_posts.py --apply
필요한 환경변수: GOOGLE_REFRESH_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, BLOGGER_BLOG_ID"""
import json, os, sys, time
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

apply = "--apply" in sys.argv
plan = json.loads((Path(__file__).parent.parent / "data" / "cleanup_plan.json").read_text(encoding="utf8"))
targets = {d["url"].split("?")[0] for d in plan["draft"]}

creds = Credentials(token=None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
    client_id=os.environ["GOOGLE_CLIENT_ID"], client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    token_uri="https://oauth2.googleapis.com/token", scopes=["https://www.googleapis.com/auth/blogger"])
svc = build("blogger", "v3", credentials=creds)
blog_id = os.environ["BLOGGER_BLOG_ID"]

posts, token = [], None
while True:
    r = svc.posts().list(blogId=blog_id, maxResults=100, pageToken=token, fetchBodies=False, status="LIVE").execute()
    posts += r.get("items", [])
    token = r.get("nextPageToken")
    if not token: break
print(f"게시 중 {len(posts)}개 / 초안 전환 대상 {len(targets)}개 (apply={apply})")
n = 0
for p in posts:
    if p["url"].split("?")[0] in targets:
        n += 1
        print(("[초안전환] " if apply else "[대상] ") + p["title"][:50])
        if apply:
            svc.posts().revert(blogId=blog_id, postId=p["id"]).execute()
            time.sleep(1)
print(f"처리 {n}개. 남는 게시글 {len(posts)-n}개")
