"""data/fixes/NN.json(기존 문구 정확 치환)과 NN_sources.json(공식 출처 블록)을 라이브 글에 적용한다.
기본 dry-run, --apply 로 실행. 원문(old)이 라이브 글에 정확히 1번 있을 때만 치환하고, 아니면 경고만 출력한다.
--offline : API 없이 data/posts 스냅샷에서 치환 가능 여부만 점검한다."""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from add_sources import MARK, block  # noqa: E402

ROOT = Path(__file__).parent.parent
FIX = ROOT / "data" / "fixes"


def load(idx):
    f = FIX / f"{idx:02d}.json"
    fixes = json.load(open(f, encoding="utf8")) if f.exists() else []
    s = FIX / f"{idx:02d}_sources.json"
    srcs = [tuple(x) for x in json.load(open(s, encoding="utf8"))] if s.exists() else []
    return fixes, srcs


def transform(idx, content):
    """(새 content, 적용 수, 경고 목록)"""
    fixes, srcs = load(idx)
    done, warn = 0, []
    for fx in fixes:
        old, new = fx["old"], fx["new"]
        c = content.count(old)
        if c == 1:
            content = content.replace(old, new)
            done += 1
        elif c == 0 and new and new in content:
            pass  # 이미 적용됨
        else:
            warn.append(f"원문 {c}회: {old[:30]!r}")
    if srcs and MARK not in content:
        content = content.rstrip() + "\n" + block(srcs) + "\n"
        done += 1
    return content, done, warn


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    man = json.load(open(ROOT / "data" / "flow_manifest.json", encoding="utf8"))
    if "--offline" in sys.argv:
        tot = 0
        for m in man:
            base = ROOT / "data" / "posts" / f"{m['idx']:02d}.html"
            _, n, w = transform(m["idx"], base.read_text(encoding="utf8"))
            tot += n
            print(f"{m['idx']:02d} 적용가능 {n}", w if w else "")
        print("합계", tot)
        sys.exit()
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"], client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    svc = build("blogger", "v3", credentials=creds)
    bid = os.environ["BLOGGER_BLOG_ID"]
    posts, tok = {}, None
    while True:
        r = svc.posts().list(blogId=bid, maxResults=100, pageToken=tok, fetchBodies=True, status="LIVE").execute()
        for p in r.get("items", []):
            posts[p["url"].split("?")[0]] = p
        tok = r.get("nextPageToken")
        if not tok:
            break
    n = 0
    for m in man:
        p = posts.get(m["url"].split("?")[0])
        if not p:
            continue
        new, k, warn = transform(m["idx"], p["content"])
        if warn:
            print(f"[경고] {m['idx']:02d}", warn)
        if k and new != p["content"]:
            n += 1
            print(("[적용] " if apply else "[대상] ") + f"{m['idx']:02d} {m['title'][:30]} ({k}건)")
            if apply:
                svc.posts().patch(blogId=bid, postId=p["id"], body={"content": new}).execute()
                time.sleep(1)
    print(f"처리 {n}개")
