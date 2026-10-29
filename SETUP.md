# 라하뉴스 자동화 설정 가이드

이 문서를 처음부터 순서대로 따라 하면 '라하뉴스' 블로그가 매일 자동으로
글 5개씩 올라오도록 설정됩니다. 콘텐츠 생성은 비용이 전혀 들지 않는
**Google Gemini API 무료 티어**를 사용하므로, 신용카드 등록이나 유료 결제가
필요 없습니다. 각 기사에는 "[라하뉴스 편집팀 작성]" 바이라인이 들어가고(2026-10-29부터,
아래 STEP 14 참고), **Pollinations.ai(무료, 가입 불필요)**로 생성한 이미지가
글마다 3~5장씩 본문 중간중간에 들어갑니다. Google 계정 로그인이 필요한 단계는
**반드시 본인이 직접 브라우저에서 진행**해 주세요.

---

## STEP 1. Blogger 블로그 만들기

1. 브라우저에서 https://blogger.com 접속 → 본인 구글 계정으로 로그인
2. "새 블로그 만들기" 클릭
3. 제목: `라하뉴스`
4. 블로그 주소: 원하는 주소 입력 (예: `rahanews-kr.blogspot.com`, 이미 쓰이고 있으면 다른 주소 시도)
5. 테마는 아무거나 선택(나중에 `theme/신문사_테마_가이드.md`로 바꿉니다)
6. 생성 완료 후, 주소창의 블로그 URL을 기억해 두세요. (예: `https://rahanews-kr.blogspot.com`, 현재 실제 주소)

## STEP 2. Google Cloud에서 Blogger API 사용 설정

1. https://console.cloud.google.com 접속 (블로그와 같은 구글 계정으로 로그인)
2. 상단 "프로젝트 선택" → "새 프로젝트" → 이름: `search-news-automation` → 만들기
3. 좌측 메뉴 → "API 및 서비스" → "라이브러리"
4. 검색창에 `Blogger API` 입력 → 선택 → **사용 설정** 클릭
5. 좌측 메뉴 → "API 및 서비스" → "OAuth 동의 화면"
   - User Type: **외부(External)** 선택 → 만들기
   - 앱 이름: `라하뉴스 자동화`, 사용자 지원 이메일: 본인 이메일
   - 범위(Scopes) 단계는 기본값으로 넘어가도 됩니다
   - "테스트 사용자" 단계에서 본인 구글 이메일 주소를 추가
   - 저장 후 완료
   - ⚠️ **게시 상태를 반드시 "프로덕션(게시)"으로 전환할 것.** "테스트 중" 상태로
     두면 발급되는 refresh token이 **7일 후 자동 만료**되어 7일 뒤 자동 발행이
     `invalid_grant: Token has been expired or revoked` 오류로 실패함
     (2026-10-20 실제 발생 — 최초 설정 후 7일 뒤 스케줄 실행이 깨짐). 아래
     STEP 2-1을 이어서 진행해 "대상" 페이지에서 "앱 게시"까지 완료할 것.
6. 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
   - "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
   - 애플리케이션 유형: **데스크톱 앱**
   - 이름: `search-news-desktop`
   - 만들기 후 뜨는 창에서 **JSON 다운로드** → 파일명을 `client_secret.json`으로 저장
   - 이 파일은 이 프로젝트 폴더 바로 아래 두되, 절대 GitHub에 올리지 마세요 (`.gitignore`에 이미 등록되어 있습니다)

## STEP 2-1. OAuth 동의 화면을 "프로덕션"으로 게시 (필수)

refresh token이 7일마다 만료되는 것을 막으려면 앱을 테스트 모드에서 꺼내야 합니다.

1. Google Cloud Console → "Google 인증 플랫폼" → **"브랜딩"** 페이지로 이동
   - "애플리케이션 홈페이지"에 블로그 주소 입력 (예: `https://rahanews-kr.blogspot.com/`)
   - "애플리케이션 개인정보처리방침 링크"에 개인정보처리방침 페이지 주소 입력
     (STEP 7에서 자동 생성된 페이지, 예: `https://rahanews-kr.blogspot.com/p/blog-page_12.html`)
   - "승인된 도메인"에 블로그 도메인 추가 (예: `rahanews-kr.blogspot.com`)
   - 저장
2. "대상" 페이지로 이동 → **"앱 게시"** 클릭 → "프로덕션으로 푸시하시겠어요?" 확인창에서
   **확인** 클릭
   - Blogger API 범위는 민감/제한 범위가 아니고 승인된 도메인도 1개뿐이라 Google의
     별도 인증 심사 없이 즉시 "프로덕션 단계"로 전환됨
   - 게시 상태가 "프로덕션 단계"로 바뀌면 이후 발급되는 refresh token은 만료되지 않음
3. 이미 "테스트 중" 상태에서 발급받은 refresh token을 쓰고 있었다면, 프로덕션 전환 후
   **STEP 3을 다시 실행해 refresh token을 새로 발급받고 GitHub Secret을 갱신**해야
   함(기존 테스트 모드 토큰은 전환 시점에 이미 살아있어도 되고 만료되어 있어도 됨 —
   새로 받는 게 가장 확실함).

## STEP 3. 내 PC에서 1회 로그인하여 refresh token 받기

1. 파이썬 설치 확인: PowerShell에서 `python --version` (3.9 이상 권장)
2. 이 프로젝트 폴더에서 아래 명령 실행:

```bash
pip install -r requirements.txt
python scripts/get_refresh_token.py client_secret.json
```

3. 자동으로 브라우저가 열리면, STEP 1~2에서 사용한 구글 계정으로 로그인하고 동의
   - "앱이 확인되지 않았습니다" 경고가 뜨면 "고급" → "search-news-automation(안전하지 않음)으로 이동" 클릭 (본인이 만든 앱이라 안전합니다)
4. 터미널에 아래 세 값이 출력됩니다. **메모장에 복사해 두세요.**
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REFRESH_TOKEN`

⚠️ **이 PC(anaconda 환경)에서 `ImportError: DLL load failed while importing _ssl`
또는 `OpenSSL.crypto` 관련 `AttributeError`가 날 경우** (2026-10-20 실제 발생):
anaconda의 `_ssl`이 PATH상의 다른 OpenSSL DLL과 충돌하는 문제. 아래처럼 anaconda
자체 DLL 경로를 PATH 맨 앞에 넣고 같은 터미널에서 실행하면 해결됨:

```powershell
$env:PATH = "C:\Users\yyk82\anaconda3\Library\bin;C:\Users\yyk82\anaconda3\DLLs;" + $env:PATH
python scripts/get_refresh_token.py client_secret.json
```

## STEP 4. Blog ID 확인하기

가장 쉬운 방법: 블로그 관리 화면 접속 후 주소창 URL을 확인합니다.

```
https://www.blogger.com/blog/posts/1234567890123456789
```

위 숫자 부분(`1234567890123456789`)이 `BLOGGER_BLOG_ID`입니다.

## STEP 5. Google Gemini API 키 발급 (무료)

1. https://aistudio.google.com/apikey 접속 (블로그와 같은 구글 계정으로 로그인)
2. **"Create API key"** 클릭 → 기존 Google Cloud 프로젝트(`search-news-automation`) 선택 또는 새 프로젝트 선택
3. 생성된 키를 복사해 두세요 (`GEMINI_API_KEY`)
4. 신용카드 등록이나 결제는 전혀 필요 없습니다. `gemini-flash-lite-latest` 모델 기준
   무료 티어 한도는 대략 분당 15회, 일일 약 1,000회 수준이며(계정/프로젝트별로 다를 수
   있음), 하루 5개 기사 생성(= 하루 5회 호출)은 이 한도에 크게 못 미쳐 완전히 무료로
   운영됩니다. 하루 발행 개수를 늘리고 싶다면 `config/site.json`의 `posts_per_day`
   값과 `.github/workflows/daily-publish.yml`의 `POSTS_PER_DAY` 값을 함께 올리면
   되지만, Gemini 한도보다 **Blogger의 자동생성 콘텐츠 스팸 정책**과 `config/topics.json`
   주제 소진 속도가 먼저 걸림돌이 되므로 과도하게 늘리지 않는 것을 권장합니다
   (2026-10-21 기준 하루 5개로 설정, 주제 뱅크 205개로 확장함).
5. 무료 한도가 궁금하면 https://ai.google.dev/gemini-api/docs/rate-limits 에서 확인할 수 있습니다.

## STEP 6. GitHub 저장소 만들고 Secrets 등록

1. https://github.com 에서 새 저장소(Repository) 생성 (Private 추천)
2. 이 프로젝트 폴더를 그 저장소에 push:

```bash
git init
git add .
git commit -m "init: 라하뉴스 자동화 프로젝트"
git branch -M main
git remote add origin https://github.com/<내-계정>/<저장소명>.git
git push -u origin main
```

3. GitHub 저장소 → **Settings → Secrets and variables → Actions → New repository secret**
   아래 5개를 각각 등록:

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | STEP 5에서 받은 키 |
| `GOOGLE_CLIENT_ID` | STEP 3에서 받은 값 |
| `GOOGLE_CLIENT_SECRET` | STEP 3에서 받은 값 |
| `GOOGLE_REFRESH_TOKEN` | STEP 3에서 받은 값 |
| `BLOGGER_BLOG_ID` | STEP 4에서 확인한 숫자 |

## STEP 7. 필수 페이지 자동 생성 (소개/개인정보처리방침/문의)

애드센스 승인에는 이 페이지들이 꼭 필요합니다. 로컬에서 1회만 실행하세요.

```bash
set GEMINI_API_KEY=...           # PowerShell이면 $env:GEMINI_API_KEY="..."
set GOOGLE_CLIENT_ID=...
set GOOGLE_CLIENT_SECRET=...
set GOOGLE_REFRESH_TOKEN=...
set BLOGGER_BLOG_ID=...
python scripts/create_static_pages.py
```

실행 후 `config/site.json`의 `contact_page.html`에 있는 이메일 주소를
실제 이메일로 바꾸는 것을 추천합니다 (문의 페이지 재발행은 Blogger 관리 화면에서
직접 수정해도 됩니다).

## STEP 8. 블로그 테마를 신문사 스타일로 꾸미기

`theme/신문사_테마_가이드.md` 문서를 참고해 Blogger 테마 커스터마이징을 진행하세요.

## STEP 9. 자동화 테스트 실행

1. GitHub 저장소 → **Actions** 탭 → "Daily Publish to Blogger" 워크플로 선택
2. **Run workflow** 버튼으로 수동 실행
3. 몇 분 후 블로그에 글 5개가 올라오는지 확인
4. 문제가 있다면 Actions 실행 로그에서 에러 메시지를 확인 (Secrets 오타가 가장 흔한 원인)

## STEP 10. 운영

- 이후로는 매일 한국시간 오전 9시에 자동으로 5개 글이 발행됩니다.
- 발행 시간을 바꾸고 싶다면 `.github/workflows/daily-publish.yml`의 `cron` 값을 수정하세요
  (cron은 UTC 기준이며, KST는 UTC+9시입니다).
- 주제가 바닥나면 `config/topics.json`에 새 항목을 추가해 주세요.

## STEP 11. 구글·네이버 검색 노출 설정 (2026-10-18 진행)

### 11-1. Blogger 자체 설정
- 설정 → 개인정보 보호 → **"검색엔진에 표시됨"** ON (검색엔진이 블로그를 찾을 수 있게 허용)
- 설정 → 메타 태그 → **"검색 설명 사용 설정"** ON + 홈페이지용 검색 설명(요약 문구) 입력
  - ⚠️ 이 입력란은 **쉼표(,)가 들어가면 저장 오류**가 남. 쉼표 없는 문장으로 작성할 것.
- 설정 → 크롤러 및 색인 생성 → **"맞춤 robots.txt"/"맞춤 로봇 헤더 태그"는 OFF 유지**
  (Blogger 기본값이 이미 크롤링을 허용하므로 건드릴 필요 없음)
- 각 글의 검색 설명(`searchDescription`)도 `scripts/publish_to_blogger.py`가
  `generate_article()`이 만든 `meta_description`을 Blogger API로 자동 전송하도록
  반영되어 있음(2026-10-18부터 신규 발행 글에 자동 적용). 기존 글은
  `scripts/backfill_search_description.py`로 일괄 채워 넣음.

### 11-2. Google Search Console
1. Blogger 설정 → 크롤러 및 색인 생성 → **"Google Search Console"** 링크 클릭
   (블로그와 같은 구글 계정이면 소유권이 자동으로 확인됨)
2. "URL 접두어" 방식으로 `https://<내-블로그-주소>.blogspot.com/` 등록
3. 좌측 메뉴 **Sitemaps** → `sitemap.xml` 입력 후 제출
   (Blogger가 `/sitemap.xml`을 자동 생성해 줌 — 별도로 만들 필요 없음)
4. **URL 검사**에서 홈페이지 주소를 검사 → "색인 생성 요청" 클릭(선택 사항이지만 초기 노출에 도움)

### 11-3. 네이버 서치어드바이저 (Claude가 자동 진행 불가 — 직접 진행 필요)
Claude의 브라우저 자동화 환경에서는 `naver.com` 계열 도메인이 안전 정책상
차단되어 있어 직접 접속이 불가능함. 아래 과정은 사용자가 직접 진행:
1. https://searchadvisor.naver.com 접속 → 네이버 계정 로그인
2. "웹마스터 도구" → "사이트 등록" → 블로그 주소 입력
3. 소유 확인 방법으로 **"HTML 태그"** 선택 → 발급된
   `<meta name="naver-site-verification" content="...">` 코드를 Claude에게 전달하면
   테마의 `<head>`에 삽입 작업을 이어서 진행 가능(viewport 메타 태그 바로 뒤에 삽입)
4. 소유 확인 완료 후 "요청 → 사이트맵 제출"에서 `sitemap.xml` 제출
5. "요청 → RSS 제출"에서 RSS 주소 제출 시 **반드시 `?alt=rss`를 붙일 것**:
   - ❌ `https://<주소>.blogspot.com/feeds/posts/default` (Atom 형식 — 네이버가 거부함)
   - ✅ `https://<주소>.blogspot.com/feeds/posts/default?alt=rss` (RSS 2.0 형식 — 정상 등록됨)
   - Blogger의 기본 피드는 Atom(`<feed>` 루트)이라 `alt=rss` 파라미터로 RSS 2.0(`<rss>` 루트)
     버전을 받아야 네이버의 RSS 제출 검증을 통과함. (2026-10-18 실제로 Atom 주소가
     거부되는 것을 확인하고 이 방법으로 해결함)

**2026-10-18 기준 완료 상태**: Google Search Console(속성 등록·사이트맵·색인 요청)과
네이버 서치어드바이저(사이트 소유 확인·사이트맵 제출·RSS 제출) 모두 완료됨.

### 11-4. 다음(Daum) 웹마스터도구
1. https://webmaster.daum.net 접속 → 다음 계정 로그인 → 사이트 등록
2. 소유 확인 방법으로 **PIN 코드(robots.txt)** 방식 선택 시 발급되는
   `#DaumWebMasterTool:...` 형태의 PIN 코드를 Blogger 설정 → 크롤러 및 색인 생성 →
   **"맞춤 robots.txt" 사용 설정을 ON** 으로 바꾼 뒤, 기존 기본 robots.txt 내용
   (Mediapartners-Google 허용, `/search`·`/share-widget` 차단, Sitemap 경로)을
   그대로 유지한 채 맨 아래에 PIN 코드 줄을 추가해서 저장
   - ⚠️ "맞춤 robots.txt"를 켜면 Blogger가 자동 생성하던 기본 robots.txt가
     완전히 대체되므로, 다른 크롤러를 막지 않으려면 기본 지시어를 반드시 함께 넣을 것
   - 저장 직후 `/robots.txt`를 바로 확인했을 때 캐시 때문에 이전 내용이 보일 수 있음 →
     `/robots.txt?cb=1`처럼 쿼리 파라미터를 붙여 캐시를 우회해서 재확인
3. 다음 웹마스터도구 대시보드에서 "응답코드 200 / 서버연결 가능 / 수집상태 가능"이
   뜨면 소유 확인 완료
4. "수집요청" 메뉴(`/tool/collect`)에서 아래 두 가지를 제출:
   - **수집 Seed URL 등록 (사이트맵)**: `https://rahanews-kr.blogspot.com/sitemap.xml`
   - **수집 Seed URL 등록 (RSS 피드, Atom 피드, 리스트 페이지)**:
     `https://rahanews-kr.blogspot.com/feeds/posts/default?alt=rss`
     (네이버와 마찬가지로 `?alt=rss`를 붙인 RSS 2.0 주소를 사용)
   - 각 섹션 제출 후 "수집요청이 완료되었습니다." 메시지가 뜨면 정상 처리된 것

**2026-10-18 기준 완료 상태**: 다음 웹마스터도구 사이트 소유 확인(robots.txt PIN
방식) 및 사이트맵·RSS 수집요청 제출 완료.

### 11-5. 네이트(Nate) 검색
2026-10-18 기준, 네이트는 일반 웹 콘텐츠를 위한 자체 사이트/웹마스터 등록 도구를
제공하지 않음(지도/업체 등록용 `map.nate.com`만 존재). 별도로 할 수 있는 등록
작업이 없으며, 네이트는 보통 다음(Daum) 검색 결과를 함께 활용하는 것으로 알려져
있어 위 다음 등록이 간접적으로 도움이 될 수 있음.

### 11-6. 블로그 주소를 나중에 또 바꾸는 경우 체크리스트
- Blogger 설정 → 게시 → 블로그 주소 변경 (BLOGGER_BLOG_ID는 변하지 않음 → 자동화 스크립트 수정 불필요)
- ⚠️ 이전 주소 → 새 주소로 **자동 리디렉션되지 않음**
- Google Search Console에 새 주소로 속성을 다시 등록하고 사이트맵도 재제출해야 함
- 네이버 서치어드바이저도 새 주소로 재등록 필요
- 다음 웹마스터도구도 새 주소로 사이트 재등록(PIN 재발급) 및 사이트맵·RSS 재제출 필요
- ⚠️ 레이아웃 → "페이지 목록(상단)" 가젯의 홈/카테고리/소개/문의/개인정보처리방침
  메뉴 링크 12개가 전부 절대 URL로 저장되어 있어 **자동으로 갱신되지 않음** —
  직접 하나씩 수정해야 메뉴 클릭 시 404/연결 오류가 나지 않음 (자세한 내용은
  `theme/신문사_테마_가이드.md`의 "4-2. 블로그 주소 변경" 참고, 2026-10-18 실제 발생)

## STEP 12. 장애 이력 — refresh token 만료로 자동 발행 실패 (2026-10-20)

**증상**: 매일 아침 9시(KST) 자동 발행이 1주일 정도 잘 되다가 갑자기 실패.
GitHub Actions 로그에 아래 에러:

```
google.auth.exceptions.RefreshError: ('invalid_grant: Token has been expired or revoked.', ...)
```

**원인**: STEP 2에서 OAuth 동의 화면 게시 상태를 "테스트 중"으로 둔 채 운영 중이었음.
Google 정책상 "테스트 중" 상태에서 발급된 refresh token은 **발급 후 7일이 지나면
자동으로 만료**됨(실제 사용 여부와 무관). 최초 설정 후 정확히 7일째 되는 날
자동 발행이 깨짐.

**해결 (영구 조치)**:
1. Google Cloud Console → Google 인증 플랫폼 → 브랜딩에서 애플리케이션 홈페이지 /
   개인정보처리방침 링크 / 승인된 도메인을 채워 넣음 (게시에 필요한 필수 입력값)
2. "대상" 페이지 → "앱 게시" → "프로덕션으로 푸시" 확인 → 게시 상태가
   "프로덕션 단계"로 전환됨 (Blogger scope는 민감/제한 범위가 아니라 Google
   인증 심사 없이 즉시 적용됨). 이제부터는 refresh token이 7일 후 만료되지 않음.
3. 이미 만료된 refresh token은 되살릴 수 없으므로, STEP 3을 다시 실행해 새
   refresh token을 발급받고 GitHub Secret `GOOGLE_REFRESH_TOKEN`을 새 값으로 교체
4. GitHub Actions → Daily Publish to Blogger → "Run workflow"로 그날 발행분을
   수동 실행해 밀린 기사를 바로 발행함

**재발 방지**: STEP 2/2-1에 "반드시 프로덕션으로 게시" 안내를 추가해 두었으므로,
이 프로젝트를 처음부터 다시 설정하는 경우에도 같은 문제가 생기지 않음.

## STEP 13. 일일 발행 개수 조정 (2026-10-21, 2개 → 5개)

**변경 내용**: 하루 발행 개수를 2개에서 5개로 늘림.
- `config/site.json`의 `posts_per_day`: 2 → 5
- `.github/workflows/daily-publish.yml`의 `POSTS_PER_DAY`: "2" → "5"
- `config/topics.json`에 카테고리당 약 10개씩, 총 80개 주제를 추가(130개 → 205개)
  하루 5개 기준으로도 약 40일간 중복 없이 순환 가능

**판단 근거**: Gemini API(`gemini-flash-lite-latest`) 무료 티어 자체 한도는 분당
15회, 일일 약 1,000회 수준으로 매우 넉넉해서 하루 수백 개도 이론상 가능하지만,
아래 이유로 "API 한도만큼" 늘리지 않고 하루 5개로 제한함:
- **Blogger 스팸 정책 위험**: 자동 생성 콘텐츠를 과도하게 빠른 속도로 대량 발행하면
  Google의 "대규모 콘텐츠 품질 저하(scaled content abuse)" 정책에 걸려 블로그나
  구글 계정이 정지될 위험이 있음 (`ADSENSE_CHECKLIST.md` 참고)
- **주제 뱅크 고갈**: 주제 뱅크가 너무 빨리 소진되면 콘텐츠 다양성이 떨어짐
- **GitHub Actions 실행 시간**: 기사 1개당 이미지 생성 포함 약 5~8분 소요. 5개면
  약 25~40분으로 안전한 범위

**추가 개선(안정성)**: `scripts/publish_to_blogger.py`를 수정해 발행 개수가 늘어난
만큼 중간 실패의 영향도 커지는 문제에 대비함. 기존에는 하루치 전체(N개)를 다
처리한 뒤 한 번에 `used_topics.json`/`category_cursor.json`을 저장했기 때문에,
N개 중 일부(예: 3번째)에서 에러가 나면 이미 발행에 성공한 1~2번째 글의 주제도
"사용함"으로 기록되지 않아 다음 실행 때 같은 주제로 중복 발행될 위험이 있었음.
이제는 글 1개를 발행할 때마다 즉시 저장하도록 바꿔서, 중간에 실패해도 이미
발행된 글까지는 정상적으로 기록되고 다음 실행에서 중복되지 않음.

**발행 개수를 추가로 조정하려면**: `config/site.json`의 `posts_per_day`와
`.github/workflows/daily-publish.yml`의 `POSTS_PER_DAY`를 같은 값으로 맞춰서
수정하면 됨. 단, 위 "판단 근거"에 언급된 제약(특히 Blogger 스팸 정책)을 고려해
과도하게 늘리지 않는 것을 권장함.

## STEP 14. 애드센스 1차 승인 거절 대응 (2026-10-29)

`rahanews-kr.blogspot.com`이 구글 애드센스 승인 심사에서 거절됨. 정확한 사유와
조치 내용은 `ADSENSE_CHECKLIST.md`의 "1차 반려 이력 및 조치" 섹션에 상세히
기록해 두었고, 핵심만 요약하면 다음과 같음.

**거절 사유** (애드센스 콘솔 → 사이트 → 사이트 상세 화면에서 확인, 이메일보다
더 정확함): "가치가 별로 없는 콘텐츠" + "게시자 콘텐츠가 없는 화면에 광고"

**코드 변경**:
- `scripts/common.py`: 가짜 개인 기자명/이메일 바이라인을 "[라하뉴스 편집팀
  작성]"으로 교체(`build_byline_html`). 같은 카테고리 다른 글로 이어지는
  "함께 보면 좋은 글" 링크 기능 추가(`add_related_links` 등)
- `scripts/generate_article.py`: SYSTEM_PROMPT에서 "기자" 역할극 제거, 가짜
  취재/인터뷰/출처 생성 금지 명시, 구체적 수치·체크리스트 포함 지시 강화
- `scripts/publish_to_blogger.py`: 신규 발행 글에 관련 글 링크 자동 추가
- `scripts/backfill_related_links.py` (신규): 기존 글에 관련 글 링크 소급 적용
- `config/site.json`: 소개 페이지에 "편집팀 기획 + AI 작성 도구 + 편집팀 검토"
  제작 방식을 투명하게 명시

**기존 글 백필**: `scripts/backfill_byline.py`(바이라인 교체)와
`scripts/backfill_related_links.py`(관련 글 링크 추가)를 로컬에서 1회 실행해
기존 발행 글에도 소급 반영함.

**재신청**: 애드센스 콘솔 → 사이트 → rahanews-kr.blogspot.com → "문제를
수정했음을 확인합니다" 체크 → "검토 요청" 버튼 클릭(자동화 대상 아님, 콘텐츠를
최종 확인한 사용자가 직접 진행).
