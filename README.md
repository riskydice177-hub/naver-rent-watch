# 서울 아파트 전월세 워치

서울 아파트 전월세 실거래를 매일 자동으로 모아서, 관심 지역에 **새로 등록된 거래**를 웹앱으로 보여줍니다.
PC를 켜둘 필요 없이 GitHub이 매일 수집하고, 노트북·휴대폰 어디서든 웹 주소로 봅니다.

**웹앱:** https://riskydice177-hub.github.io/naver-rent-watch/

## 구조

```
GitHub Actions (매일 07:00 KST)
  └ collect.py ── 국토부 실거래가 API ──▶ site/data/*.json (저장소에 커밋)
                                            └ GitHub Pages 배포 ──▶ site/index.html (웹앱)
```

- `collect.py` — 서울 25개 구, 최근 3개월 전월세 거래 수집. 처음 수집된 날짜(`first_seen`)를 기록해서 새 거래를 구분
- `site/index.html` — 웹앱. 구·동·전세/월세·보증금·월세·면적·준공연도·신규계약·신규등록 기간 필터
- `config.toml` — 수집할 구와 기간
- `.github/workflows/update.yml` — 매일 수집 → 커밋 → 배포

## 데이터 소스

| 소스 | 상태 |
|---|---|
| 국토교통부 아파트 전월세 실거래가 API | ✅ 동작 — 계약 후 신고된 거래 |
| 네이버 부동산 매물 | ⏸ 보류 — 네이버가 자동화 접근을 차단(429), 우회하지 않음 |

## 다른 PC에서 작업하기

```powershell
gh repo clone riskydice177-hub/naver-rent-watch
cd naver-rent-watch
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

- 화면 수정만 할 거면 `site/index.html` 을 고치고 push 하면 자동 배포됩니다.
- 로컬에서 미리보기: `python -m http.server -d site 8000` → http://localhost:8000
- 로컬에서 수집을 돌려보려면 `local.toml` 에 `molit_api_key = "..."` 를 넣고 `python collect.py` (보통은 필요 없음 — Actions가 함)

## API 키

공공데이터포털(data.go.kr) "국토교통부_아파트 전월세 실거래가 자료" 일반 인증키를 저장소 **Settings → Secrets and variables → Actions** 의 `MOLIT_API_KEY` 에 저장해 두었습니다. 키를 바꾸면 여기만 갱신하면 됩니다.

## 수동으로 지금 업데이트

GitHub 저장소 → **Actions** 탭 → "매일 데이터 수집 & 웹앱 배포" → **Run workflow**
