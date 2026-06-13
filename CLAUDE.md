# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요

AI 인테리어 추천 서비스 — 도면 이미지 업로드 → Claude Vision 분석 → 2026 트렌드 기반 톤 6개 선택 → Imagen 방별 렌더링 + 이케아 상품 추천. KDT 포트폴리오 겸 개인 실사용 목적.

## 기술 스택

| 계층 | 기술 |
|------|------|
| 프론트엔드 | Next.js 15, React 19, TypeScript, Tailwind CSS v4, shadcn/ui |
| 백엔드 | FastAPI, Python 3.12, Uvicorn |
| 인증 | Supabase Auth (Google OAuth) + JWT |
| DB | Supabase (PostgreSQL) |
| AI | Claude Sonnet 4.6 (Vision + Web Search), Vertex AI Imagen 4 (렌더링 전용) |
| 외부 API | 이케아 비공식 검색 API (sik.search.blue.cdtapps.com), GCP Cloud Storage |
| 배포 | Vercel (프론트엔드), GCP Cloud Run (백엔드) |
| 테스트 | Playwright (API + E2E), Pytest (유닛) |

## 실행 명령

### 백엔드 (포트 8000)
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### 프론트엔드 (포트 3000)
```bash
cd frontend
npm install
npx shadcn@latest init        # 최초 1회
npm run dev
```

### 백엔드 유닛 테스트
```bash
cd backend
pytest                         # 전체
pytest tests/services/test_claude_service.py   # 단일 파일
pytest -k "test_ikea"         # 이름 패턴 매칭
```

### Playwright 테스트 (실제 API 호출 — 비용 ~$1)
```bash
cd tests
npm install
npx playwright install chromium

npm run test:backend   # /analyze /render API만 (~2분)
npm run test:e2e       # 브라우저 E2E (sessionStorage mock)
npm test               # 전체
npm run test:report    # HTML 리포트
```

> `analyze.api.spec.ts`, `render.api.spec.ts`는 실제 Claude/Imagen/이케아 API를 호출해 비용이 발생하므로 필요할 때만 실행.

## 환경변수 설정

루트 `.env.example` → `.env` 로 복사 후 값 채우기.  
프론트엔드 `frontend/.env.local.example` → `frontend/.env.local` 로 복사.

필수 키: `ANTHROPIC_API_KEY`, `GCP_PROJECT_ID`, `GCS_BUCKET_NAME`, `GCS_RENDER_BUCKET_NAME`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`.

> 이케아 비공식 API는 별도 키 불필요. 네이버 쇼핑 API 연동은 제거됨 (2026-06, naver_service.py 삭제).

GCP 로컬 인증: `backend/service-account.json` 에 서비스 계정 키 배치 후 `.env`에 경로 지정.

## 아키텍처 핵심

### 요청 흐름
1. **업로드**: 도면 이미지 → GCS 저장 → `analysis_sessions` 생성
2. **분석** (`POST /analyze`): Claude Vision으로 방 구조 파악 + Web Search로 2026 트렌드 조회 → 톤 6개 생성 → Supabase 저장
3. **렌더링** (`POST /render`): 선택된 톤 기반 SVG 2D 배치도 생성 + Imagen으로 방별 이미지 병렬 생성 + 이케아 상품 검색 → 결과 저장

### 백엔드 레이어 구조
```
routers/      ← HTTP 엔드포인트 (얇게 유지, 인증·검증만)
services/     ← 비즈니스 로직 (claude, imagen, ikea, svg, storage, supabase)
core/         ← 공통 (config, auth JWT검증, cache TTL, room_furniture_map)
models/       ← Pydantic 스키마 (schemas.py 단일 파일)
```

### 프론트엔드 라우트 구조 (App Router)
```
/                      ← 도면 업로드 (FloorPlanUploader)
/auth/login            ← Google OAuth 로그인
/analyze               ← 분석 대기 (polling)
/tones/[sessionId]     ← 톤 선택 (6개 카드)
/render/[sessionId]    ← 렌더링 대기
/result/[id]           ← 방별 결과 (RoomTabs + ProductGrid + SvgLayoutViewer)
```

### 인증 흐름
- `middleware.ts`가 보호 라우트 접근 시 `/auth/login` 리다이렉트
- 백엔드는 `Authorization: Bearer <supabase-jwt>` 헤더로 검증 (`core/auth.py`)
- Playwright 테스트용 JWT 생성은 `tests/fixtures/auth.ts` 참조

### 캐싱 전략
- `core/cache.py`: `trend_cache` (24h TTL, Web Search 결과), `furniture_query_cache` (24h, 이케아 쿼리)
- GCS 렌더링 이미지: 30일 자동 삭제 정책 (버킷 라이프사이클)
- Signed URL TTL: 15분 (`SIGNED_URL_TTL_MINUTES`)

## AI 모델 제약 & 프롬프트 전략

### Claude Vision 인식률 한계 (AECV-bench 실측치)

| 항목 | 인식률 |
|------|--------|
| 침실·욕실 | 70~78% |
| 문(Door) | ~26% |
| 창문(Window) | ~14% |

**MVP 범위 제한**: Vision 목표를 **방 이름·방 개수 인식**으로 제한. 입력 도면은 아파트 분양도면/네이버 부동산 캡처로 한정. 문·창문 정밀 배치는 Phase 2 수정 UI 이후.

**프롬프트 전략** (`services/claude_service.py` 수정 시 준수):
1. 프롬프트 분해 4단계 순서: 공간 인식 → 구조 인식 → 수치 추출 → 문/창문 확인
2. 낮은 신뢰도 항목 → 프론트엔드에서 사용자 확인 요청 UI 표시

### 렌더링 엔진 결정 사항

- **항상**: Imagen 4 (`imagen-4.0-generate-001`) — 텍스트 전용, 고품질
- **레퍼런스 있을 때**: Claude Vision이 이미지에서 추출한 시그니처(색상·재질·조명·무드)를 영문 텍스트 힌트로 변환해 Imagen 프롬프트에 추가. 이미지 복사(StyleReferenceImage)가 아닌 분위기 재해석.
- 분기 로직 없음 — `render_rooms_parallel`은 항상 `render_room`(generate 모델)만 호출. 레퍼런스 특성은 `build_imagen_prompt(reference_signature=...)` 텍스트로 반영
- Gemini Image는 PoC 후 미사용으로 확정 — 관련 코드(gemini_image_service.py, poc_gemini_conditioning.py) 삭제 완료.

### 이케아 비공식 API 제약

- **비공식 엔드포인트** — `sik.search.blue.cdtapps.com`은 이케아 내부 검색 인프라. 응답 구조 변경 시 `ikea_service.py`의 `_parse` 수정 필요
- **재고 상태 미반환** — 이케아 API도 재고를 제공하지 않으므로 "품절 자동 필터링" 기능 구현 불가
- 상품 링크 클릭 후 이케아 공식 사이트에서 직접 확인하도록 UI 안내 필수
- API 키 불필요, 요청 제한 없음 (단, 과도한 호출은 IP 차단 위험)
- `next.config.ts`에 `www.ikea.com` 이미지 호스트 등록 완료

## 법적 의무 — UI/출력 작성 시 필수 체크

### 출력별 필수 면책 문구

렌더링 이미지 하단 (UI 라벨로 충족 — 이미지 파일 워터마크 불필요):
> "AI 생성 이미지" (RoomRenderCard 우측 하단 라벨)

예산 추정 출력:
> "AI 기반 참고 단가이며 실제 공사비는 ±30% 오차 발생 가능. 최종 견적은 시공업체 직접 확인 필수."

상품 링크 근처:
> "가격·재고는 검색 시점 기준이며 실시간 반영이 아닐 수 있습니다."

벽 분류 출력 (Phase 2+):
> "벽 분류는 도면 두께 기반 AI 추정(신뢰도 70~85%). 실제 시공 전 관리사무소·구조 기술사 확인 필수."

### 절대 사용 금지 표현

```
❌ "우리 AI는 100% 정확합니다"
❌ "내력벽을 신뢰있게 판별합니다" (신뢰도 수치 없이)
❌ "이 렌더링으로 시공할 수 있습니다"
❌ "품절 상품 자동 필터링" (이케아 API가 재고 미제공)
❌ "플랫폼은 일체의 책임을 지지 않습니다" (공정위 적발 대상)
❌ "사진과 똑같이 만들어드립니다" (레퍼런스 이미지 conditioning은 스타일 참고이며 복제·재현 아님)
```

## 구현 로드맵

### Phase 1 — MVP (완료)
- 톤 6개 추천 → 선택 → 방별 Imagen 렌더링 → 이케아 상품 링크 end-to-end
- AI 생성 이미지 고지 문구 (UI 라벨 + API 응답 disclaimer)
- 워터마크는 UI 라벨로 고지 의무 충족 — 이미지 파일 임베드 불필요로 결정

### Phase 2 — 고도화 (완료, 2026.05)
- 톤 재선택 (F006): 결과 페이지 "다른 톤" 버튼 → `/tones/[sessionId]` 복귀
- 방 면적(area_sqm) UI 표시: RoomInfoCard + LayoutCanvas SVG 배치도

### Phase 3 — 완성 (진행 중, 2026.06)
- F007 정밀화 맞춤 렌더링 ✅ (2026-05-23): 결과 페이지 "정밀화" 버튼 → RefinementModal(shadcn Dialog) → `/render` 재호출. 정밀화 파라미터: budget_10k_won, family_type, style_keywords(최대3), keep_appliances. DB: recommendation_results.refinement_params jsonb 컬럼 추가 (0003_add_refinement_params.sql). shadcn UI 정식 도입(components.json, dialog, label).
- F008 공유 링크 — 미구현 (DB 테이블만 존재)
- F011 분석 기록 조회 — 미구현
- fc10: Vision 정확도 80%+ 달성 후 벽 분류 기능 (SNS 이미지 → 내 방 적용 가능 여부)

## DB 스키마 주요 테이블

`supabase/migrations/0001_init.sql` 참조.  
핵심: `analysis_sessions` → `rooms` + `tone_candidates` (1:N) → `render_results` → `rooms` (1:1)

## 배포

```bash
# 백엔드 (Cloud Run)
cd backend
docker build -t gcr.io/${GCP_PROJECT_ID}/interior-api .
docker push gcr.io/${GCP_PROJECT_ID}/interior-api
gcloud run deploy interior-api --image ... --region asia-northeast3

# 프론트엔드: Vercel 대시보드에서 자동 배포 (main 브랜치 push)
```

Cold Start 대응: 발표 30분 전 `GET /health` 워밍업 호출, Cloud Run 최소 인스턴스 1 설정.
