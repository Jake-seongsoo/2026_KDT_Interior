-- =============================================================================
-- AI 인테리어 추천 서비스 — 초기 스키마
-- Supabase 대시보드 > SQL Editor > 이 파일 전체 붙여넣기 후 실행
-- =============================================================================

-- uuid 생성 확장 활성화
create extension if not exists "pgcrypto";

-- =============================================================================
-- 1. users — 개인정보 동의 상태만 별도 보관 (auth.users 참조)
-- =============================================================================
create table if not exists public.users (
  id                uuid        primary key references auth.users(id) on delete cascade,
  consent_given_at  timestamptz                 -- null이면 동의 전
);

alter table public.users enable row level security;
-- 서비스 키(service_role)는 RLS 우회. 프론트 직접 접근 없음
create policy "서비스 키만 접근" on public.users
  using (false);  -- 모든 행 수준 직접 접근 차단 (서비스 키는 우회)

-- =============================================================================
-- 2. analysis_sessions — 도면 업로드 세션
-- =============================================================================
create table if not exists public.analysis_sessions (
  id                  uuid        primary key default gen_random_uuid(),
  user_id             uuid        references auth.users(id) on delete set null,
  gcs_path            text,                     -- floor-plans/{uid}/{sid}/original.jpg
  floor_area_pyeong   numeric(5,1) not null,
  status              text        not null default 'analyzing'
                        check (status in ('analyzing', 'completed', 'failed')),
  trend_snapshot      jsonb,                    -- Web Search 트렌드 스냅샷
  created_at          timestamptz not null default now(),
  expires_at          timestamptz not null default (now() + interval '30 days')
);

alter table public.analysis_sessions enable row level security;
create policy "서비스 키만 접근" on public.analysis_sessions using (false);

create index idx_sessions_user_created
  on public.analysis_sessions(user_id, created_at desc);

-- =============================================================================
-- 3. rooms — Vision 분석으로 추출된 방 정보
-- =============================================================================
create table if not exists public.rooms (
  id               uuid        primary key default gen_random_uuid(),
  session_id       uuid        not null references public.analysis_sessions(id) on delete cascade,
  room_type        text        not null,
  area_sqm         numeric(6,2),
  confidence       numeric(4,3) check (confidence between 0 and 1),
  priority         int         not null default 99,
  is_render_target boolean     not null default false,
  position         jsonb        -- {x, y, w, h} 0~1 상대 좌표
);

alter table public.rooms enable row level security;
create policy "서비스 키만 접근" on public.rooms using (false);

create index idx_rooms_session_priority
  on public.rooms(session_id, priority);

-- =============================================================================
-- 4. tone_candidates — 도면 기반 AI 추천 톤 6개
-- =============================================================================
create table if not exists public.tone_candidates (
  id            uuid  primary key default gen_random_uuid(),
  session_id    uuid  not null references public.analysis_sessions(id) on delete cascade,
  tone_index    int   not null check (tone_index between 1 and 6),
  name          text  not null,
  category      text,
  description   text,
  reason        text,
  color_palette jsonb not null default '[]',
  keywords      jsonb not null default '[]'
);

alter table public.tone_candidates enable row level security;
create policy "서비스 키만 접근" on public.tone_candidates using (false);

create index idx_tone_session
  on public.tone_candidates(session_id);

-- =============================================================================
-- 5. recommendation_results — 사용자가 선택한 톤 기준 결과 헤더
-- =============================================================================
create table if not exists public.recommendation_results (
  id                uuid        primary key default gen_random_uuid(),
  session_id        uuid        not null references public.analysis_sessions(id),
  user_id           uuid        references auth.users(id),
  selected_tone_id  uuid        not null references public.tone_candidates(id),
  budget_10k_won    int,
  trend_snapshot    jsonb,
  processing_ms     int         not null default 0,
  created_at        timestamptz not null default now()
);

alter table public.recommendation_results enable row level security;
create policy "서비스 키만 접근" on public.recommendation_results using (false);

create index idx_result_session
  on public.recommendation_results(session_id);

create index idx_result_user
  on public.recommendation_results(user_id, created_at desc);

-- =============================================================================
-- 6. room_renders — 선택 톤으로 생성한 방별 이미지와 추천 근거
-- =============================================================================
create table if not exists public.room_renders (
  id              uuid  primary key default gen_random_uuid(),
  result_id       uuid  not null references public.recommendation_results(id) on delete cascade,
  room_id         uuid  not null references public.rooms(id),
  room_type       text  not null,   -- JOIN 없이 조회하기 위한 중복 필드
  rationale       text,
  render_gcs_path text,             -- renders/{result_id}/{slug}.jpg
  prompt          text              -- 재현·디버깅용 Imagen 프롬프트
);

alter table public.room_renders enable row level security;
create policy "서비스 키만 접근" on public.room_renders using (false);

create index idx_render_result
  on public.room_renders(result_id);

-- =============================================================================
-- 7. products — 네이버쇼핑 상품 (방별 3~5개)
-- =============================================================================
create table if not exists public.products (
  id                uuid        primary key default gen_random_uuid(),
  room_render_id    uuid        not null references public.room_renders(id) on delete cascade,
  naver_product_id  text,
  name              text        not null,
  category          text,
  price_min         int         not null default 0,
  price_max         int         not null default 0,
  image_url         text,
  purchase_url      text,
  fetched_at        timestamptz not null default now()
);

alter table public.products enable row level security;
create policy "서비스 키만 접근" on public.products using (false);

create index idx_products_render
  on public.products(room_render_id);

-- =============================================================================
-- 8. share_links — 공유 링크 UUID (/share/[uuid] SSR)
-- =============================================================================
create table if not exists public.share_links (
  id          uuid        primary key default gen_random_uuid(),
  result_id   uuid        not null unique references public.recommendation_results(id),
  created_at  timestamptz not null default now(),
  view_count  int         not null default 0
);

alter table public.share_links enable row level security;
create policy "서비스 키만 접근" on public.share_links using (false);

-- =============================================================================
-- 9. vision_experiments — 프롬프트 버전별 정확도 R&D 기록
-- =============================================================================
create table if not exists public.vision_experiments (
  id               uuid        primary key default gen_random_uuid(),
  prompt_version   text        not null,   -- v1, v2, v3
  sample_label     text        not null,   -- 예: '25평형_LH_01'
  ground_truth     jsonb       not null,
  prediction       jsonb,
  room_accuracy    numeric(4,3),
  door_accuracy    numeric(4,3),
  window_accuracy  numeric(4,3),
  overall_accuracy numeric(4,3),
  prompt_tokens    int,
  notes            text,
  created_at       timestamptz not null default now()
);

alter table public.vision_experiments enable row level security;
-- vision_experiments는 서비스 키로만 삽입 (RLS 정책 없음 = 직접 행 접근 불가)
create policy "서비스 키만 접근" on public.vision_experiments using (false);

-- =============================================================================
-- 완료 메시지
-- =============================================================================
do $$
begin
  raise notice 'AI 인테리어 추천 서비스 스키마 초기화 완료 (9개 테이블)';
end $$;
