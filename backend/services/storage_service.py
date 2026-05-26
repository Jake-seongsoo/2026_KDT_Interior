# RISK-02: 도면 이미지는 private 저장 + Signed URL(15분) 만 노출.
# Public URL은 renders/ 폴더(AI 생성물)에만 허용한다.
import logging
from datetime import timedelta
from uuid import UUID

from google.cloud import storage

from core.config import get_google_credentials, get_settings

logger = logging.getLogger(__name__)


class StorageService:
  def __init__(self) -> None:
    settings = get_settings()
    self._client = storage.Client(
      project=settings.GCP_PROJECT_ID,
      credentials=get_google_credentials(),
    )
    self._bucket = self._client.bucket(settings.GCS_BUCKET_NAME)
    self._bucket_name = settings.GCS_BUCKET_NAME
    self._render_bucket_name = settings.GCS_RENDER_BUCKET_NAME or settings.GCS_BUCKET_NAME
    self._render_bucket = self._client.bucket(self._render_bucket_name)
    self._ttl = timedelta(minutes=settings.SIGNED_URL_TTL_MINUTES)

  # ── 도면 업로드 (private) ─────────────────────────────────

  def upload_floorplan(
    self,
    user_id: str,
    session_id: UUID,
    data: bytes,
    content_type: str,
  ) -> str:
    """도면을 GCS private 버킷에 업로드하고 GCS 경로를 반환한다."""
    ext = '.png' if content_type == 'image/png' else '.jpg'
    path = f'floor-plans/{user_id}/{session_id}/original{ext}'
    blob = self._bucket.blob(path)
    blob.upload_from_string(data, content_type=content_type)
    # make_public() 호출하지 않음 — Signed URL 만 노출 (RISK-02)
    logger.info('도면 업로드 완료: %s', path)
    return path

  def signed_url_for_floorplan(self, gcs_path: str) -> str:
    """도면 미리보기 요청 시에만 사용하는 15분 TTL Signed URL."""
    blob = self._bucket.blob(gcs_path)
    return blob.generate_signed_url(expiration=self._ttl, version='v4')

  # ── 레퍼런스 이미지 업로드 (private, 도면과 동일 정책) ──

  def upload_reference(
    self,
    user_id: str,
    session_id: UUID,
    data: bytes,
    content_type: str,
  ) -> str:
    """사용자 업로드 인테리어 레퍼런스 이미지를 private 버킷에 저장한다."""
    ext = '.png' if content_type == 'image/png' else '.jpg'
    path = f'references/{user_id}/{session_id}/original{ext}'
    blob = self._bucket.blob(path)
    blob.upload_from_string(data, content_type=content_type)
    logger.info('레퍼런스 이미지 업로드 완료: %s', path)
    return path

  def download_reference(self, gcs_path: str) -> bytes:
    """Imagen 호출용 — 저장된 레퍼런스 이미지 bytes를 가져온다."""
    blob = self._bucket.blob(gcs_path)
    return blob.download_as_bytes()

  def signed_url_for_reference(self, gcs_path: str) -> str:
    """레퍼런스 미리보기용 15분 TTL Signed URL."""
    blob = self._bucket.blob(gcs_path)
    return blob.generate_signed_url(expiration=self._ttl, version='v4')

  # ── 렌더링 이미지 업로드 (public) ────────────────────────

  def upload_render(
    self,
    result_id: UUID,
    room_slug: str,
    data: bytes,
  ) -> str:
    """AI 생성 렌더링 이미지를 GCS public으로 업로드하고 GCS 경로를 반환한다."""
    path = f'renders/{result_id}/{room_slug}.jpg'
    blob = self._render_bucket.blob(path)
    blob.upload_from_string(data, content_type='image/jpeg')
    # Uniform bucket-level access에서는 객체 ACL(make_public)을 사용할 수 없다.
    # 렌더 전용 버킷의 공개 읽기 권한은 IAM 또는 CDN 정책에서 처리한다.
    logger.info('렌더링 이미지 업로드 완료: %s', path)
    return path

  def public_url_for_render(self, gcs_path: str) -> str:
    """GCS 경로로부터 public URL을 생성한다."""
    return f'https://storage.googleapis.com/{self._render_bucket_name}/{gcs_path}'
