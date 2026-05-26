-- =============================================================================
-- 0005: analysis_sessions에 레퍼런스 이미지 경로 + 톤 시그니처 컬럼 추가
-- 사용자가 도면과 함께 업로드하는 인테리어 레퍼런스 사진(카페·SNS 캡쳐 1장)을
-- 보관하고, Claude Vision으로 추출한 톤 시그니처를 톤 생성·렌더링 입력으로 사용한다.
-- =============================================================================

alter table public.analysis_sessions
  add column if not exists reference_gcs_path  text,
  add column if not exists reference_signature jsonb;

comment on column public.analysis_sessions.reference_gcs_path is
  '사용자 업로드 레퍼런스 이미지 GCS 경로 (private 버킷). 없으면 NULL.';

comment on column public.analysis_sessions.reference_signature is
  'Claude Vision으로 레퍼런스 이미지에서 추출한 톤 시그니처 JSON: '
  '{ primary_hex, secondary_hex, accent_hex, materials[], style_tokens[], lighting, mood }';

-- 레퍼런스 보유 세션 빠른 필터링 (분석·통계 용)
create index if not exists idx_sessions_reference
  on public.analysis_sessions(user_id)
  where reference_gcs_path is not null;
