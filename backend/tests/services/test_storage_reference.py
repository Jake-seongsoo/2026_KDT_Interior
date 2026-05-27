"""StorageService 레퍼런스 이미지 메서드 단위 테스트."""
import pytest

USER_ID = 'user-123'
SESSION_ID = 'session-456'


class TestUploadReference:
  def test_jpeg_경로_형식(self, storage_service):
    """JPEG 업로드 시 경로가 references/{user}/{session}/original.jpg 여야 한다."""
    mock_blob = storage_service._bucket.blob.return_value

    path = storage_service.upload_reference(USER_ID, SESSION_ID, b'image-data', 'image/jpeg')

    expected = f'references/{USER_ID}/{SESSION_ID}/original.jpg'
    assert path == expected
    storage_service._bucket.blob.assert_called_once_with(expected)
    mock_blob.upload_from_string.assert_called_once_with(b'image-data', content_type='image/jpeg')

  def test_png_경로에_png_확장자(self, storage_service):
    """PNG 업로드 시 경로에 .png 확장자가 붙어야 한다."""
    path = storage_service.upload_reference(USER_ID, SESSION_ID, b'image-data', 'image/png')
    assert path.endswith('.png')

  def test_make_public_호출_안_함(self, storage_service):
    """private 정책이므로 make_public이 호출되면 안 된다."""
    mock_blob = storage_service._bucket.blob.return_value

    storage_service.upload_reference(USER_ID, SESSION_ID, b'data', 'image/jpeg')

    mock_blob.make_public.assert_not_called()


class TestDownloadReference:
  def test_download_as_bytes_반환(self, storage_service):
    """download_reference는 blob.download_as_bytes() 결과를 반환해야 한다."""
    mock_blob = storage_service._bucket.blob.return_value
    mock_blob.download_as_bytes.return_value = b'ref-image-bytes'

    result = storage_service.download_reference('references/user/session/original.jpg')

    assert result == b'ref-image-bytes'
    mock_blob.download_as_bytes.assert_called_once()

  def test_private_버킷_사용(self, storage_service):
    """download_reference는 렌더 버킷이 아닌 private 버킷을 사용해야 한다."""
    mock_blob = storage_service._bucket.blob.return_value
    mock_blob.download_as_bytes.return_value = b'data'

    storage_service.download_reference('references/user/session/original.jpg')

    storage_service._bucket.blob.assert_called_once()
    storage_service._render_bucket.blob.assert_not_called()


class TestSignedUrlForReference:
  def test_signed_url_생성_호출(self, storage_service):
    """signed_url_for_reference는 generate_signed_url을 호출하고 URL을 반환해야 한다."""
    mock_blob = storage_service._bucket.blob.return_value
    mock_blob.generate_signed_url.return_value = 'https://example.com/signed'

    url = storage_service.signed_url_for_reference('references/user/session/original.jpg')

    assert url == 'https://example.com/signed'
    mock_blob.generate_signed_url.assert_called_once()
