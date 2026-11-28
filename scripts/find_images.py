"""Wikimedia Commons에서 글 주제에 맞는 사진 후보를 찾아 data/image_plan.json에 저장한다.

- 허용 라이선스: CC0, 퍼블릭도메인, CC BY, CC BY-SA (NC/ND 제외 → 광고 블로그에서 사용 가능)
- 작가·라이선스·원본 페이지 URL을 함께 저장해 사진 아래 출처 표기에 사용한다.
- API 키 불필요. 글 하나당 최대 3장, 전체에서 같은 사진 중복 금지."""
import html, json, re, sys, time
from pathlib import Path
import requests

UA = {"User-Agent": "rahanews-blog-image-picker/1.0 (educational blog; contact via blog)"}
API = "https://commons.wikimedia.org/w/api.php"
ROOT = Path(__file__).parent.parent
BAD = re.compile(r"logo|diagram|map|screenshot|icon|flag|poster|cartoon|drawing|painting|stamp|coat of arms|scan|\bsvg\b|nude|bikini", re.I)

# (제목 정규식, [검색어 3개])
Q = [
 (r"전입신고", ["moving boxes apartment", "official documents stamp office", "apartment building residential"]),
 (r"국비지원", ["adult learners classroom training", "student studying laptop notebook", "vocational training workshop"]),
 (r"크롬", ["laptop browser web", "person using laptop desk", "computer monitor office"]),
 (r"무보험", ["car accident damaged cars road", "insurance claim documents", "traffic police accident"]),
 (r"중고차", ["used car dealership lot", "car mechanic inspection", "car keys hand"]),
 (r"자격증", ["certificate exam studying", "student writing exam desk", "books study notes"]),
 (r"관세|직구", ["cardboard parcel package delivery", "customs cargo airport", "online shopping parcel laptop"]),
 (r"카드 분실", ["credit cards wallet", "credit card payment terminal", "wallet cards hand"]),
 (r"변기", ["clean bathroom toilet", "cleaning brush bathroom", "bathroom tiles clean"]),
 (r"과실비율", ["car collision intersection", "traffic intersection cars", "road traffic cars city"]),
 (r"중도상환", ["bank loan documents calculator", "house keys mortgage", "calculator money desk"]),
 (r"이불 진드기", ["bedroom bed white sheets", "vacuum cleaner mattress", "bedding laundry sunlight"]),
 (r"상속포기", ["legal documents signing pen", "courthouse building", "will testament papers"]),
 (r"신입사원", ["office new employee meeting", "business people office handshake", "office desk laptop coffee"]),
 (r"공무원 시험", ["student studying library exam", "notebook pen study desk", "exam hall students"]),
 (r"카카오톡", ["smartphone messaging app hand", "smartphone chat screen", "data backup hard drive"]),
 (r"등본", ["official documents stack", "printer printing paper office", "laptop documents desk"]),
 (r"실업급여", ["job seeker resume office", "job center employment", "person job search laptop"]),
 (r"경력단절", ["woman returning to work office", "job interview candidate", "woman laptop home working"]),
 (r"저혈압", ["woman dizzy headache", "glass of water health", "blood pressure measuring"]),
 (r"탈모", ["hair brush comb", "hair care shampoo", "stressed woman hands head"]),
 (r"소화불량", ["stomach ache abdomen", "healthy meal vegetables table", "herbal tea cup"]),
 (r"변비", ["glass of water morning", "fruits vegetables fiber", "walking exercise park"]),
 (r"환불", ["online shopping customer service", "package return box", "credit card laptop shopping"]),
 (r"비염", ["allergy sneezing tissue", "humidifier room", "air purifier living room"]),
 (r"경력증명서", ["business document certificate", "office worker computer", "employee id card"]),
 (r"와이파이", ["wifi router", "laptop internet desk", "router cables desk"]),
 (r"아이폰", ["iphone smartphone hand", "smartphone photos hand", "smartphone storage memory"]),
 (r"블루스크린", ["computer repair motherboard", "laptop error", "technician computer repair"]),
 (r"세탁기", ["washing machine laundry", "laundry detergent", "laundry room clean"]),
 (r"갤럭시", ["smartphone hot charging", "android phone hand", "phone charging cable"]),
 (r"고소장", ["police station", "legal documents pen", "law books gavel"]),
 (r"경고등", ["car dashboard warning lights", "car instrument cluster", "car mechanic engine"]),
 (r"커튼", ["curtains window living room", "laundry hanging sunlight", "washing machine clothes"]),
 (r"주차 위반", ["parking violation ticket car", "parked cars street", "no parking sign"]),
 (r"임차권등기", ["apartment rental keys", "house keys landlord", "apartment building"]),
 (r"신발장", ["shoe rack entrance shoes", "sneakers shoes", "shoes cleaning"]),
 (r"이력서", ["resume writing desk", "job interview", "laptop resume desk"]),
 (r"하이패스", ["highway toll gate", "expressway cars road", "car driving highway"]),
]
OK_LIC = re.compile(r"^(CC0|Public domain|PD|CC BY(-SA)?\b)", re.I)
BADLIC = re.compile(r"NC|ND", re.I)

def search(q):
    p = dict(action="query", generator="search", gsrsearch=q + " filetype:bitmap", gsrnamespace=6, gsrlimit=30,
             prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=800, format="json")
    for attempt in range(6):
        r = requests.get(API, params=p, headers=UA, timeout=30)
        if r.status_code != 429: break
        time.sleep(int(r.headers.get("Retry-After", 10)) + 5 * attempt)
    r.raise_for_status()
    pages = sorted(r.json().get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0))
    out = []
    for pg in pages:
        ii = (pg.get("imageinfo") or [{}])[0]
        md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        title = pg["title"]
        if ii.get("mime") != "image/jpeg" or BAD.search(title): continue
        if not OK_LIC.match(lic) or BADLIC.search(lic): continue
        w, h = ii.get("width", 0), ii.get("height", 0)
        if w < 1200 or w < h * 1.2: continue
        artist = re.sub(r"<[^>]+>", "", html.unescape(md.get("Artist", {}).get("value", ""))).strip()
        artist = re.sub(r"\s+", " ", artist)[:60] or "작가 미상"
        out.append(dict(title=title, thumb=ii["thumburl"], page=ii["descriptionurl"], artist=artist, license=lic))
    return out

if __name__ == "__main__":
    plan = json.load(open(ROOT / "data" / "cleanup_plan.json", encoding="utf8"))["keep"]
    used, result = set(), []
    for post in plan:
        qs = next((q for pat, q in Q if re.search(pat, post["title"])), None)
        if not qs:
            print("[매핑없음]", post["title"][:40]); continue
        picks = []
        for q in qs:
            for c in search(q):
                if c["title"] not in used:
                    used.add(c["title"]); picks.append(c); break
            time.sleep(3)
        print(f"[{len(picks)}장]", post["title"][:40])
        result.append(dict(url=post["url"], title=post["title"], images=picks))
    json.dump(result, open(ROOT / "data" / "image_plan.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
