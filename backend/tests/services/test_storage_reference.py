"""StorageService 레퍼런스 이미지 메서드 단위 테스트."""
from unittest.mock import MagicMock, patch

from services.storage_service import StorageService

USER_ID = 'user-123'
SESSION_ID = 'session-456'


def _make_svc() -> StorageService:
  with patch('services.storage_service.storage.Client'), \
       patch('services.storage_service.get_settings') as mock_settings, \
       patch('services.storage_service.get_google_credentials'):
    mock_settings.return_value = MagicMock(
      GCP_PROJECT_ID='test-project',
      GCS_BUCKET_NAME='test-bucket',
      GCS_RENDER_BUCKET_NAME='test-render-bucket',
      SIGNED_URL_TTL_MINUTES=15,
    )
    svc = StorageService()
    svc._bucket = MagicMock()
    svc._render_bucket = MagicMock()
    return svc


class TestUploadReference:
  def test_jpeg_경로_형식(self):
    """JPEG 업로드 시 경로가 references/{user}/{session}/original.jpg 여야 한다."""
    svc = _make_svc()
    mock_blob = MagicMock()
    svc._bucket.blob.return_value = mock_blob

    path = svc.upload_reference(USER_ID, SESSION_ID, b'image-data', 'image/jpeg')

    expected = f'references/{USER_ID}/{SESSION_ID}/original.jpg'
    assert path == expected
    svc._bucket.blob.assert_called_once_with(expected)
    mock_blob.upload_from_string.assert_called_once_with(b'image-data', content_type='image/jpeg')

  def test_png_경로에_png_확장자(self):
    """PNG 업로드 시 경로에 .png 확장자가 붙어야 한다."""
    svc = _make_svc()
    svc._bucket.blob.return_value = MagicMock()

    path = svc.upload_reference(USER_ID, SESSION_ID, b'image-data', 'image/png')

    assert path.endswith('.png')

  def test_make_public_호출_안_함(self):
    """private 정책이므로 make_public이 호출되면 안 된다."""
    svc = _make_svc()
    mock_blob = MagicMock()
    svc._bucket.blob.return_value = mock_blob

    svc.upload_reference(USER_ID, SESSION_ID, b'data', 'image/jpeg')

    mock_blob.make_public.assert_not_called()


class TestDownloadReference:
  def test_download_as_bytes_반환(self):
    """download_reference는 blob.download_as_bytes() 결과를 반환해야 한다."""
    svc = _make_svc()
    mock_blob = MagicMock()
    mock_blob.download_as_bytes.return_value = b'ref-image-bytes'
    svc._bucket.blob.return_value = mock_blob

    result = svc.download_reference('references/user/session/original.jpg')

    assert result == b'ref-image-bytes'
    mock_blob.download_as_bytes.assert_called_once()

  def test_private_버킷_사용(self):
    """download_reference는 렌더 버킷이 아닌 private 버킷을 사용해야 한다."""
    svc = _make_svc()
    mock_blob = MagicMock()
    mock_blob.download_as_bytes.return_value = b'data'
    svc._bucket.blob.return_value = mock_blob

    svc.download_reference('references/user/session/original.jpg')

    svc._bucket.blob.assert_called_once()
    svc._render_bucket.blob.assert_not_called()


class TestSignedUrlForReference:
  def test_signed_url_생성_호출(self):
    """signed_url_for_reference는 generate_signed_url을 호출하고 URL을 반환해야 한다."""
    svc = _make_svc()
    mock_blob = MagicMock()
    mock_blob.generate_signed_url.return_value = 'https://example.com/signed'
    svc._bucket.blob.return_value = mock_blob

    url = svc.signed_url_for_reference('references/user/session/original.jpg')

    assert url == 'https://example.com/signed'
    mock_blob.generate_signed_url.assert_called_once()
