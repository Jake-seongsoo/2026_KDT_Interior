-- Phase 2: 가구 슬롯 추천 지원을 위한 스키마 확장
-- products 테이블에 slot 컬럼, room_renders에 furniture_queries 컬럼 추가

alter table public.products
  add column if not exists slot text;

create index if not exists idx_products_render_slot
  on public.products(room_render_id, slot);

alter table public.room_renders
  add column if not exists furniture_queries jsonb default '[]'::jsonb;
