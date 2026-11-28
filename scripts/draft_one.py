"""제목에 특정 문구가 들어간 게시 중인 글을 초안으로 되돌린다. 사용: draft_one.py "문구" [--apply]"""
import os
import sys

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

key = sys.argv[1]
apply = "--apply" in sys.argv
creds = Credentials(
    token=None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"], client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token",
    scopes=["https://www.googleapis.com/auth/blogger"],
)
svc = build("blogger", "v3", credentials=creds)
bid = os.environ["BLOGGER_BLOG_ID"]
tok, hits = None, []
while True:
    r = svc.posts().list(blogId=bid, maxResults=100, pageToken=tok, fetchBodies=False, status="LIVE").execute()
    hits += [p for p in r.get("items", []) if key in p["title"]]
    tok = r.get("nextPageToken")
    if not tok:
        break
for p in hits:
    print(("[초안] " if apply else "[대상] ") + p["title"], p["url"])
    if apply:
        svc.posts().revert(blogId=bid, postId=p["id"]).execute()
print(f"{len(hits)}개")
