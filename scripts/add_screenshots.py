"""공식 사이트 화면 캡처(assets/blog/shots/*.jpg)를 글에 넣고 출처·확인일을 표기한다. 기본 dry-run, --apply 로 실행.
캡처는 직접 사용해 본 경험이 아니라 '공식 안내 화면'임을 캡션에 분명히 적는다. 마커 rn-shot 으로 중복을 막는다."""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
RAW = "https://raw.githubusercontent.com/youngkyule/search-news-automation/main/assets/blog/shots/"

# 글 번호 → (이 소제목 다음 첫 문단 뒤에 삽입, 파일명, alt, 캡션 문구, 출처 이름, 출처 주소)
SHOTS = {
    1: ("인터넷 전입신고 시 꼭 알아야 할 주의할 점", "01-gov24-faq.jpg",
        "정부24 자주묻는질문 '온라인 전입신고시 제약사항은 무엇이 있나요?' 화면",
        "정부24 자주묻는질문(FAQ) 화면 캡처, 2026년 11월 28일 확인", "정부24(gov.kr)", "https://www.gov.kr/portal/faq/986"),
}


def figure(shot):
    _, fn, alt, cap, src_name, src_url = shot
    return (
        '<figure class="rn-shot" style="margin:18px 0;text-align:center;">'
        f'<img src="{RAW}{fn}" alt="{alt}" loading="lazy" style="max-width:100%;height:auto;border:1px solid #ddd;border-radius:6px;"/>'
        f'<figcaption style="font-size:12px;color:#888;margin-top:4px;">{cap} · 출처: '
        f'<a href="{src_url}" target="_blank" rel="noopener noreferrer">{src_name}</a></figcaption></figure>\n'
    )


def insert(idx, content):
    shot = SHOTS[idx]
    if "rn-shot" in content:
        return content
    m = re.search(r"<h2[^>]*>\s*" + re.escape(shot[0]) + r"\s*</h2>", content)
    if not m:
        return content
    end = content.find("</p>", m.end())
    if end == -1:
        return content
    end += 4
    return content[:end] + "\n" + figure(shot) + content[end:]


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    man = {m["idx"]: m for m in json.load(open(ROOT / "data" / "flow_manifest.json", encoding="utf8"))}
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
    for idx in SHOTS:
        p = posts.get(man[idx]["url"].split("?")[0])
        if not p:
            continue
        new = insert(idx, p["content"])
        if new == p["content"]:
            print(f"[변경없음] {idx:02d}")
            continue
        print(("[적용] " if apply else "[대상] ") + f"{idx:02d} {man[idx]['title'][:30]}")
        if apply:
            svc.posts().patch(blogId=bid, postId=p["id"], body={"content": new}).execute()
            time.sleep(1)
