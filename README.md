# 검색뉴스 (SearchNews) — 자동 생활정보 블로그

한국인이 구글/네이버에서 많이 검색하는 '생활 속 문제'를 주제로,
**Google Gemini API 무료 티어**가 기사를 생성하고 Blogger API로 자동 발행하는
파이프라인입니다. 비용이 전혀 들지 않으며, GitHub Actions가 매일 1개씩 글을 올립니다.

## 구성
- `config/site.json` — 사이트 기본 정보, 카테고리, 소개/개인정보처리방침/문의 페이지 내용
- `config/topics.json` — 카테고리별 주제(검색 키워드) 뱅크
- `data/used_topics.json` — 이미 사용한 주제 기록 (자동 갱신됨)
- `scripts/generate_article.py` — Gemini API(무료)로 기사 1건 생성
- `scripts/publish_to_blogger.py` — 매일 실행되는 메인 스크립트 (주제 선택 → 생성 → 발행)
- `scripts/get_refresh_token.py` — 최초 1회, 로컬에서 Google OAuth 인증
- `scripts/create_static_pages.py` — 최초 1회, 필수 페이지(소개/개인정보처리방침/문의) 생성
- `.github/workflows/daily-publish.yml` — 매일 자동 실행 워크플로
- `theme/신문사_테마_가이드.md` — Blogger 테마를 신문사 스타일로 꾸미는 방법
- `SETUP.md` — 처음부터 끝까지 따라 하는 설정 가이드 (여기부터 시작하세요)
- `ADSENSE_CHECKLIST.md` — 애드센스 신청 전 체크리스트

## 시작하기

`SETUP.md`를 순서대로 따라 하세요. Blogger 블로그 생성, Google Cloud API 설정,
GitHub Secrets 등록까지 단계별로 안내되어 있습니다.

## 로컬 테스트 (발행 없이 생성만 확인)

```bash
pip install -r requirements.txt
set GEMINI_API_KEY=AIzaSyxxxx
set DRY_RUN=true
python scripts/publish_to_blogger.py
```
