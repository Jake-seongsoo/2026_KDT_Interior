# Moodie — AI 인테리어 추천 서비스

도면 이미지 업로드 → Claude Vision 분석 → 2026 트렌드 기반 톤 6개 선택 → Imagen 방별 렌더링 + 네이버쇼핑 상품 추천

## 로컬 개발 환경 설정

### 사전 준비

1. `.env` 설정 (루트 디렉터리)

```powershell
Copy-Item .env.example .env
# .env를 열어 모든 키 채우기:
# ANTHROPIC_API_KEY, GCP_PROJECT_ID, GCS_BUCKET_NAME
# SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_JWT_SECRET
```

2. 프론트엔드 `.env.local` 설정

```powershell
Copy-Item frontend\.env.local.example frontend\.env.local
# NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY 채우기
```

### Supabase 초기화

1. Supabase 대시보드 → SQL Editor → `supabase/migrations/0001_init.sql` 전체 붙여넣기 후 실행
2. Supabase Auth → Providers → Google 활성화
3. Redirect URL 등록:
   - `http://localhost:3000/auth/callback`
   - `https://your-app.vercel.app/auth/callback`

### GCS 버킷 초기화

```bash
gsutil mb -l asia-northeast3 gs://${GCS_BUCKET_NAME}

# 30일 자동 삭제 정책
cat > lifecycle.json << 'EOF'
{
  "rule": [{
    "action": {"type": "Delete"},
    "condition": {"age": 30}
  }]
}
EOF
gsutil lifecycle set lifecycle.json gs://${GCS_BUCKET_NAME}
```

---

## 백엔드 실행

```powershell
cd backend

# Python 가상환경 생성 (최초 1회)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# 개발 서버 실행 (포트 8000)
uvicorn main:app --reload --port 8000
```

헬스 체크:
```bash
curl http://localhost:8000/health
# → {"status": "ok", "environment": "development"}
```

---

## 프론트엔드 실행

```powershell
cd frontend

# 의존성 설치 (최초 1회)
npm install

# shadcn 컴포넌트 추가 (최초 1회)
npx shadcn@latest init
npx shadcn@latest add button card input label progress tabs

# 개발 서버 실행 (포트 3000)
npm run dev
```

브라우저에서 `http://localhost:3000` 접속

---

## Playwright 테스트 실행

백엔드와 프론트엔드를 먼저 실행한 상태에서:

```powershell
cd tests

# 의존성 설치 (최초 1회)
npm install
npx playwright install chromium

# 백엔드 API 테스트만 실행 (실제 API 호출, ~2분)
npm run test:backend

# 프론트엔드 E2E 테스트만 실행 (sessionStorage mock 사용)
npm run test:e2e

# 전체 테스트
npm test

# 테스트 리포트 확인
npm run test:report
```

> **주의**: `analyze.api.spec.ts`와 `render.api.spec.ts`는 실제 Claude/Imagen/Naver API를 호출합니다.
> 1회 실행당 약 $1 내외의 비용이 발생할 수 있습니다. CI에서는 backend-api 프로젝트만 PR마다 실행하고 E2E는 nightly로 제한하세요.

---

## Cold Start 대응 (발표 당일)

```bash
# 발표 30분 전 워밍업 호출 (컨테이너 유지)
curl https://<cloud-run-url>/health

# 발표 당일 최소 인스턴스 1로 설정
gcloud run services update interior-api --min-instances=1

# 발표 후 원복
gcloud run services update interior-api --min-instances=0
```

---

## 배포

> 상세한 단계별 절차·재배포·롤백·운영 가이드는 **[docs/배포_운영.md](docs/배포_운영.md)** 참조.

### 백엔드 (GCP Cloud Run) — GitHub Actions 자동 배포

`master` 브랜치에 `backend/**` 변경이 푸시되면 `.github/workflows/deploy-backend.yml`이
Cloud Build로 이미지를 빌드해 Cloud Run에 자동 배포한다. (수동 실행: Actions 탭 → Run workflow)

최초 1회 수동 배포·권한 설정은 [docs/배포_운영.md](docs/배포_운영.md) 0~2장 참조.

### 프론트엔드 (Vercel)

Vercel 대시보드에서 GitHub 연동 후 자동 배포 (Root Directory = `frontend`). 환경변수:
- `NEXT_PUBLIC_API_URL` (Cloud Run URL)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_ENVIRONMENT` (`production`)

---

## Phase 2 예정 기능

- 방 정보 인라인 수정 + 재분석 (F003)
- 톤 재선택 (F006)
- 개인정보 수집 동의 모달 (RISK-07)
- AI 생성 이미지 워터마크 (RISK-08)
- 분석 기록 조회 (F011)
- 공유 링크 `/share/[uuid]` SSR (F008)
