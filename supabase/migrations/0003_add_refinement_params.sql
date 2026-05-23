-- F007 정밀화 맞춤 렌더링: recommendation_results 테이블에 정밀화 파라미터 컬럼 추가
alter table public.recommendation_results
  add column if not exists refinement_params jsonb;

comment on column public.recommendation_results.refinement_params is
  '정밀화 파라미터 JSON: { budget_10k_won, family_type, style_keywords, keep_appliances }';
