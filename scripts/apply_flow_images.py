"""assets/blog/NN-k.(jpg|png)로 저장한 Flow 이미지를 글에 적용한다 (기본 dry-run, --apply로 실행).

- 이미지는 GitHub 저장소(raw.githubusercontent.com)에서 서빙하므로, 먼저 assets/blog를 커밋·push 해야 한다.
- 글의 기존 이미지(Pollinations 등 <img> 전부)를 제거하고, 새 이미지를 <h2> 앞에 배치한다.
- 사진 아래에 작은 글씨로 출처("이미지: AI 생성(Google Flow)")를 표기한다. 재실행해도 중복되지 않는다.
- 이미지 파일이 없는 글은 건드리지 않는다."""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW = "https://raw.githubusercontent.com/youngkyule/search-news-automation/main/assets/blog/"
CAPTION = "이미지: AI 생성(Google Flow)"
FIG_RE = re.compile(r'<figure class="rn-img".*?</figure>\s*', re.S)
IMG_RE = re.compile(r"<img\b[^>]*>\s*", re.S)


def fig(url, alt):
    return (
        '<figure class="rn-img" style="margin:18px 0;text-align:center;">'
        f'<img src="{url}" alt="{alt}" loading="lazy" style="max-width:100%;height:auto;border-radius:8px;"/>'
        f'<figcaption style="font-size:12px;color:#888;margin-top:4px;">{CAPTION}</figcaption></figure>\n'
    )


def files_for(idx):
    d = ROOT / "assets" / "blog"
    return sorted(p for p in d.glob(f"{idx:02d}-*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))


def rebuild(content, imgs, title):
    content = FIG_RE.sub("", content)
    content = IMG_RE.sub("", content)  # 기존(Pollinations 등) 이미지 제거
    figs = [fig(RAW + p.name, f"{title} 관련 이미지 {n}") for n, p in enumerate(imgs, 1)]
    out, k = [], 0
    for s in re.split(r"(<h2>)", content):  # <h2> 앞에 하나씩
        if s == "<h2>" and k < len(figs):
            out.append(figs[k])
            k += 1
        out.append(s)
    res = "".join(out)
    if k < len(figs):  # 남은 이미지는 첫 문단 뒤
        res = re.sub(r"</p>", "</p>\n" + "".join(figs[k:]), res, count=1)
    return res


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    man = json.load(open(ROOT / "data" / "flow_manifest.json", encoding="utf8"))
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
        imgs = files_for(m["idx"])
        p = posts.get(m["url"].split("?")[0])
        if not imgs or not p:
            print(f"[건너뜀] {m['idx']:02d} 이미지 {len(imgs)}장 / 글 {'있음' if p else '없음'}")
            continue
        n += 1
        print(("[교체] " if apply else "[대상] ") + f"{m['idx']:02d} {m['title'][:35]} ({len(imgs)}장)")
        if apply:
            svc.posts().patch(blogId=bid, postId=p["id"], body={"content": rebuild(p["content"], imgs, m["title"])}).execute()
            time.sleep(1)
    print(f"처리 {n}개")
