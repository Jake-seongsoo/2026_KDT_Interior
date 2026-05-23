-- =============================================================================
-- 0004: rooms 테이블에 발코니 인접·확장 여부 컬럼 추가
-- =============================================================================

alter table public.rooms
  add column if not exists has_adjoining_balcony boolean not null default false,
  add column if not exists balcony_expanded       boolean;

comment on column public.rooms.has_adjoining_balcony is
  '이 방이 발코니/베란다와 인접해 있는지 여부 (Claude Vision 추출)';

comment on column public.rooms.balcony_expanded is
  '발코니 확장형 여부. true=확장됨(벽선 없음), false=비확장(실선 벽), null=판별불가';
