"""data/enrich/NN.html(보강 섹션)을 라이브 글에 끼워 넣는다. 기본 dry-run, --apply 로 실행.

- 삽입 위치: '자주 묻는 질문' <h2> 앞 → 없으면 공식 출처 블록(rn-sources) 앞 → 없으면 글 맨 끝
- 마커 <!--rn-enrich-->...<!--/rn-enrich--> 로 감싸므로 재실행해도 중복되지 않고 내용만 갱신된다
- --offline : API 없이 data/posts/NN.html(스냅샷)에 적용한 결과만 data/enriched_preview/ 에 저장
"""
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
START, END = "<!--rn-enrich-->", "<!--/rn-enrich-->"
BLOCK_RE = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\s*", re.S)
FAQ_RE = re.compile(r"<h2[^>]*>\s*(자주 묻는 질문|자주 묻는 질문[^<]*|FAQ[^<]*)\s*</h2>")


# 보강 조사에서 공식 자료와 어긋난 것이 확인된 기존 문구의 정확한 치환 (글 번호 → [(원문, 수정문)])
FIXES = {
    1: [("정부24에서 전입신고를 진행하는 과정 중 마지막 단계에서 임대차계약서를 첨부하면 확정일자까지 한 번에 신청할 수 있는 체크박스가 있습니다. 이를 활용하면 동사무소를 방문하지 않고도 동시에 처리할 수 있습니다.",
         "정부24 전입신고 화면에서는 확정일자를 함께 신청할 수 없습니다. 확정일자는 임대차계약서 원본을 가지고 주민센터를 방문해 받는 것이 기본이며, 그 밖의 경로는 이용 조건이 있으니 해당 기관 안내를 확인하세요.")],
    4: [("당혹스러움은로", "당혹스러움으로")],
    5: [("가상해 봐야", "가정해 봐야")],
    10: [("과실비율분쟁조정위원회", "과실비율분쟁심의위원회")],
    24: [("할보항변권", "할부항변권"), ("신용카드 결의", "신용카드 결제")],
    38: [("비용 20채 절감", "비용 20% 절감")],
}


def fix(idx, content):
    for old, new in FIXES.get(idx, []):
        content = content.replace(old, new)
    return content


def merge(content, add):
    content = BLOCK_RE.sub("", content)
    block = f"{START}\n{add.strip()}\n{END}\n"
    m = FAQ_RE.search(content)
    if m:
        return content[: m.start()] + block + content[m.start():]
    i = content.find('<div class="rn-sources"')
    if i != -1:
        return content[:i] + block + content[i:]
    return content + "\n" + block


def addition(idx):
    p = ROOT / "data" / "enrich" / f"{idx:02d}.html"
    return p.read_text(encoding="utf8") if p.exists() else None


if __name__ == "__main__":
    apply = "--apply" in sys.argv
    offline = "--offline" in sys.argv
    man = json.load(open(ROOT / "data" / "flow_manifest.json", encoding="utf8"))
    if offline:
        out = ROOT / "data" / "enriched_preview"
        out.mkdir(exist_ok=True)
        for m in man:
            add = addition(m["idx"])
            base = ROOT / "data" / "posts" / f"{m['idx']:02d}.html"
            if add and base.exists():
                (out / f"{m['idx']:02d}.html").write_text(fix(m["idx"], merge(base.read_text(encoding="utf8"), add)), encoding="utf8")
                print("미리보기", m["idx"])
            else:
                print("건너뜀", m["idx"])
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
        add, p = addition(m["idx"]), posts.get(m["url"].split("?")[0])
        if not add or not p:
            print(f"[건너뜀] {m['idx']:02d} 보강 {'있음' if add else '없음'} / 글 {'있음' if p else '없음'}")
            continue
        n += 1
        print(("[적용] " if apply else "[대상] ") + f"{m['idx']:02d} {m['title'][:35]} (+{len(re.sub('<[^>]+>', '', add))}자)")
        if apply:
            svc.posts().patch(blogId=bid, postId=p["id"], body={"content": fix(m["idx"], merge(p["content"], add))}).execute()
            time.sleep(1)
    print(f"처리 {n}개")
