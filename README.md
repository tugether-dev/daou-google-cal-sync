# 🗕️ DaouOffice CalDAV → Google Calendar 자동 동기화

DaouOffice의 CalDAV 캔더 데이터를 가져와,  구글 캔더에 **2가지 전 ~ 2가지 후 일정**만 자동으로 **등록, 수정, 삭제 동기화**하는 Python 스크립트입니다.

---

## 🚀 기능 요약

- **다우오피스 CalDAV 캔더** → **Google Calendar**로 자동 동기화
- **CRUD 완전 지원**
  - 새 일정 생성
  - 일정 변경 시 자동 업데이트
  - 삭제된 일정도 Google Calendar에서 자동 삭제
- **시간 필터 적용** (오늘 기준 ± \xb12가지)
- **환경변수(.env) 기능**  
- **GitHub Actions**를 통해 **10분마다 자동 실행** (07:00~22:00)

---

## 📆파일 구조

```
v1_gcal_sync/
├─ .github/workflows/sync.yml   # GitHub Actions 워크플로우 파일
├─ requirements.txt             # Python 패키지 목록
├─ sync.py                      # 메인 스크립트
├─ .env                          # 환경변수 파일 (로컬 테스트용)
└─ README.md                     # 설명 문서
```

---

## 📦 설치 및 준비

1. **레포 클론**

```bash
git clone https://github.com/tugether-dev/daou-google-cal-sync.git
cd daou-google-cal-sync
```

2. **Python 가상환경 설정 (선택)**

```bash
python3 -m venv venv
source venv/bin/activate  # (Windows: venv\Scripts\activate)
```

3. **필수 패키지 설치**

```bash
pip install -r requirements.txt
```

4. **.env 파일 생성**

```plaintext
GOOGLE_CREDS={구글 OAuth 클라이언트 서비스 정보}
GOOGLE_TOKEN={구글 인증 토큰}
GOOGLE_CALENDAR_ID={가져올 Google Calendar ID}
CALDAV_URL={다우오피스 CalDAV URL}
CALDAV_USER={다우오피스 로그인 ID}
CALDAV_PASS={다우오피스 번호}
```

> **특정**: `.env`는 방어된 건지 검토하지 않게 조절해야 합니다.

---

## 🚀 실행 방법

### 로컬에서 수동 실행

```bash
python sync.py
```

### GitHub Actions 자동 실행

- `.github/workflows/sync.yml` 파일에 시간 설정 완료
- **07:00 ~ 22:00 사이, 10분마다 자동 실행**

---

## 📝 주의사항

- 동기화 범위는 "오늘 기준 ± \xb12가지" 입니다.
- 다우오피스 CalDAV 일정에 참석자(ATTENDEE) 정보는 동기화하지 않습니다.
- 등록, 수정, 삭제 모두 `event id (UID)` 기준으로 그룹합니다.
- Google Calendar API 사용량은 현재 무료 한도 내역 (2025년 4월 기준)

