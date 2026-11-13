# naver-rent-watch

서울 아파트 전월세를 매일 확인해서, 관심 지역에 **새로 등록된 거래**를 웹페이지 리포트로 정리합니다.

## 데이터 소스

| 소스 | 상태 | 내용 |
|---|---|---|
| 국토교통부 아파트 전월세 실거래가 API | ✅ 동작 | 계약이 완료되어 신고된 전월세 거래 (시세 파악용) |
| 네이버 부동산 매물 | ⏸ 보류 | 네이버가 자동화 접근을 429로 차단 중 — 차단 우회는 하지 않음 |

## 처음 설정

1. [공공데이터포털](https://www.data.go.kr)에 로그인 → **"국토교통부_아파트 전월세 실거래가 자료"** 검색 → 활용신청 (보통 즉시~1시간 내 승인)
2. 마이페이지에서 **일반 인증키(Decoding)** 를 복사
3. 프로젝트 폴더에 `local.toml` 파일을 만들고 아래처럼 저장 (git에 올라가지 않음)
   ```toml
   molit_api_key = "여기에_인증키"
   ```
4. 가상환경 준비 (이미 되어 있으면 생략)
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

## 실행

```powershell
.\.venv\Scripts\python.exe main.py --open
```

- 리포트: `reports/latest.html` (날짜별 사본도 함께 저장)
- 첫 실행은 기준점을 만드는 단계라 NEW 표시가 없고, 다음 실행부터 새로 신고된 거래에 **NEW** 가 붙습니다.

## 관심 지역·조건 바꾸기

`config.toml` 을 수정하세요. 구/동, 전세·월세, 보증금·월세 상한, 면적, 준공연도, 신규계약만 보기 등을 설정할 수 있습니다.
리포트 화면에서도 구·동·구분·단지명으로 추가 필터링할 수 있습니다.

## 매일 자동 실행

```powershell
powershell -ExecutionPolicy Bypass -File schedule.ps1 -Time 08:30
```
