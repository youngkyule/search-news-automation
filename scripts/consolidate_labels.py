"""게시 중인 글의 라벨을 카테고리 1개로 통일한다(라벨이 100개 넘게 흩어져 있던 것을 8개로).
각 글이 이미 가진 카테고리 라벨(config/site.json의 categories)만 남기고 나머지는 지운다.
기본 dry-run, --apply 로 실행."""
import os
import sys
import time

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from common import load_site_config

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    cats = set(load_site_config()["categories"])
    creds = Credentials(
        token=None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"], client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    svc = build("blogger", "v3", credentials=creds)
    bid = os.environ["BLOGGER_BLOG_ID"]
    posts, tok = [], None
    while True:
        r = svc.posts().list(blogId=bid, maxResults=100, pageToken=tok, fetchBodies=False, status="LIVE").execute()
        posts += r.get("items", [])
        tok = r.get("nextPageToken")
        if not tok:
            break
    n = 0
    for p in posts:
        labels = p.get("labels", [])
        keep = [l for l in labels if l in cats][:1]
        if not keep:
            print(f"[건너뜀] 카테고리 라벨 없음: {p['title'][:30]} {labels}")
            continue
        if keep == labels:
            continue
        n += 1
        print(("[변경] " if apply else "[대상] ") + f"{p['title'][:30]} {len(labels)}개 -> {keep}")
        if apply:
            svc.posts().patch(blogId=bid, postId=p["id"], body={"labels": keep}).execute()
            time.sleep(1)
    print(f"처리 {n}개 / 전체 {len(posts)}개")
