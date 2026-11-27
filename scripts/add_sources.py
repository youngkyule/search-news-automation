"""게시 중인 글에 '참고할 공식 사이트' 블록을 추가한다 (애드센스 재심사 대비 3단계).

- 주제별로 실제 접속되는 공식/공공 사이트만 연결한다. 매핑되지 않는 글은 건드리지 않는다.
- 마커(rn-sources)로 중복 추가를 막는다. 기본은 dry-run, 실제 적용은 --apply.
- 이 블록은 '출처 안내'일 뿐이다. 글 본문 내용을 해당 출처와 대조·보강하는 것은 사람이 해야 한다."""
import os, re, sys, time

MARK = "rn-sources"
G = ("정부24", "https://www.gov.kr")
SOURCES = [
    (r"전입신고|등본", [G]),
    (r"국비지원|내일배움", [("고용24", "https://www.work24.go.kr"), ("HRD-Net", "https://www.hrd.go.kr")]),
    (r"크롬", [("Chrome 고객센터", "https://support.google.com/chrome")]),
    (r"무보험", [("손해보험협회", "https://www.knia.or.kr"), ("금융소비자 정보포털 파인", "https://fine.fss.or.kr")]),
    (r"중고차", [("자동차365", "https://www.car365.go.kr")]),
    (r"자격증", [("Q-net 한국산업인력공단", "https://www.q-net.or.kr")]),
    (r"관세|직구", [("관세청 유니패스", "https://unipass.customs.go.kr")]),
    (r"카드 분실|카드 한도", [("금융소비자 정보포털 파인", "https://fine.fss.or.kr")]),
    (r"과실비율", [("과실비율정보포털(손해보험협회)", "https://accident.knia.or.kr")]),
    (r"중도상환", [("금융소비자 정보포털 파인", "https://fine.fss.or.kr")]),
    (r"상속포기", [("대한민국 법원", "https://www.scourt.go.kr"), ("찾기쉬운 생활법령정보", "https://easylaw.go.kr")]),
    (r"고소장|임차권등기|과태료 이의", [("찾기쉬운 생활법령정보", "https://easylaw.go.kr")]),
    (r"하이패스", [("한국도로공사 하이패스", "https://www.hipass.co.kr")]),
    (r"실업급여", [("고용보험", "https://www.ei.go.kr"), ("고용24", "https://www.work24.go.kr")]),
    (r"경력단절", [("여성새로일하기센터", "https://saeil.mogef.go.kr"), ("고용24", "https://www.work24.go.kr")]),
    (r"경력증명서|이력서|자기소개서|신입사원", [("고용24", "https://www.work24.go.kr")]),
    (r"저혈압|탈모|소화불량|변비|비염|어지럼", [("국가건강정보포털", "https://health.kdca.go.kr")]),
    (r"아이폰", [("Apple 지원", "https://support.apple.com/ko-kr")]),
    (r"갤럭시", [("삼성전자서비스 지원", "https://www.samsung.com/sec/support/")]),
    (r"카카오톡", [("카카오 고객센터", "https://cs.kakao.com")]),
    (r"블루스크린|와이파이", [("Microsoft 지원", "https://support.microsoft.com/ko-kr")]),
    (r"환불", [("한국소비자원", "https://www.kca.go.kr"), ("소비자24", "https://www.consumer.go.kr")]),
]

def pick(title):
    out = []
    for pat, src in SOURCES:
        if re.search(pat, title):
            out += [s for s in src if s not in out]
    return out

def block(src):
    lis = "".join(f'<li><a href="{u}" target="_blank" rel="noopener noreferrer">{n}</a></li>' for n, u in src)
    return (f'<div class="{MARK}"><h3>참고할 공식 사이트</h3>'
            "<p>제도·요금·절차는 수시로 바뀔 수 있으므로, 실제로 신청하거나 결정하기 전에 아래 공식 사이트에서 최신 내용을 확인하세요.</p>"
            f"<ul>{lis}</ul></div>")

if __name__ == "__main__":
    apply = "--apply" in sys.argv
    if "--offline" in sys.argv:  # 인증 없이 매핑만 확인
        import json
        plan = json.load(open(os.path.join(os.path.dirname(__file__), "..", "data", "cleanup_plan.json"), encoding="utf8"))
        n = 0
        for p in plan["keep"]:
            s = pick(p["title"]); n += bool(s)
            print(("O " if s else "- ") + p["title"][:40], [x[0] for x in s])
        print(f"매핑 {n}/{len(plan['keep'])}"); sys.exit()
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    creds = Credentials(token=None, refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"], client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"], token_uri="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/blogger"])
    svc = build("blogger", "v3", credentials=creds); bid = os.environ["BLOGGER_BLOG_ID"]
    posts, tok = [], None
    while True:
        r = svc.posts().list(blogId=bid, maxResults=100, pageToken=tok, fetchBodies=True, status="LIVE").execute()
        posts += r.get("items", []); tok = r.get("nextPageToken")
        if not tok: break
    done = 0
    for p in posts:
        src = pick(p["title"])
        if not src or MARK in p["content"]:
            print("[건너뜀]", p["title"][:40]); continue
        print(("[추가] " if apply else "[대상] ") + p["title"][:40], [s[0] for s in src]); done += 1
        if apply:
            svc.posts().patch(blogId=bid, postId=p["id"], body={"content": p["content"] + block(src)}).execute(); time.sleep(1)
    print(f"처리 {done}개 / 전체 {len(posts)}개")
