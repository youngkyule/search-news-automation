# 라하뉴스 자동화 설정 가이드

이 문서를 처음부터 순서대로 따라 하면 '라하뉴스' 블로그가 매일 자동으로
글 2개씩 올라오도록 설정됩니다. 콘텐츠 생성은 비용이 전혀 들지 않는
**Google Gemini API 무료 티어**를 사용하므로, 신용카드 등록이나 유료 결제가
필요 없습니다. 각 기사에는 카테고리별로 고정 배정된 담당 기자 바이라인(이름 +
이메일)이 들어가고, **Pollinations.ai(무료, 가입 불필요)**로 생성한 이미지가
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
   - 저장 후 완료 (게시 상태는 "테스트" 그대로 두어도 자동화에는 문제 없습니다)
6. 좌측 메뉴 → "API 및 서비스" → "사용자 인증 정보"
   - "+ 사용자 인증 정보 만들기" → "OAuth 클라이언트 ID"
   - 애플리케이션 유형: **데스크톱 앱**
   - 이름: `search-news-desktop`
   - 만들기 후 뜨는 창에서 **JSON 다운로드** → 파일명을 `client_secret.json`으로 저장
   - 이 파일은 이 프로젝트 폴더 바로 아래 두되, 절대 GitHub에 올리지 마세요 (`.gitignore`에 이미 등록되어 있습니다)

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
4. 신용카드 등록이나 결제는 전혀 필요 없습니다. 무료 티어 한도(예: 분당 요청 수, 일일 요청 수) 내에서는
   완전히 무료이며, 하루에 글 2개만 생성하므로 무료 한도를 넘을 일이 없습니다.
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
3. 몇 분 후 블로그에 글 2개가 올라오는지 확인
4. 문제가 있다면 Actions 실행 로그에서 에러 메시지를 확인 (Secrets 오타가 가장 흔한 원인)

## STEP 10. 운영

- 이후로는 매일 한국시간 오전 9시에 자동으로 2개 글이 발행됩니다.
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
   테마의 `<head>`에 삽입 작업을 이어서 진행 가능
4. 등록 후 "요청 → 사이트맵 제출"에서 `sitemap.xml` 제출

### 11-4. 블로그 주소를 나중에 또 바꾸는 경우 체크리스트
- Blogger 설정 → 게시 → 블로그 주소 변경 (BLOGGER_BLOG_ID는 변하지 않음 → 자동화 스크립트 수정 불필요)
- ⚠️ 이전 주소 → 새 주소로 **자동 리디렉션되지 않음**
- Google Search Console에 새 주소로 속성을 다시 등록하고 사이트맵도 재제출해야 함
- 네이버 서치어드바이저도 새 주소로 재등록 필요
