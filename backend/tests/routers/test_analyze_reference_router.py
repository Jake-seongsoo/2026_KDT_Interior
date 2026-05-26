"""analyze 라우터 레퍼런스 기능 단위 테스트."""
import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from routers.analyze import _to_analyze_response, _validate_file

SESS = str(uuid.uuid4())


def _rooms():
  return [{'id': str(uuid.uuid4()), 'room_type': '거실', 'confidence': 0.9, 'priority': 1}]


def _tones():
  return [{'id': str(uuid.uuid4()), 'name': '자연 속 고요', 'tone_index': 1}]


class TestToAnalyzeResponseHasReference:
  def test_has_reference_기본값_False(self):
    """has_reference 미전달 시 False여야 한다."""
    res = _to_analyze_response(SESS, _rooms(), _tones())
    assert res.has_reference is False

  def test_has_reference_True_전달(self):
    """has_reference=True 전달 시 True여야 한다."""
    res = _to_analyze_response(SESS, _rooms(), _tones(), has_reference=True)
    assert res.has_reference is True

  def test_has_reference_False_명시적_전달(self):
    """has_reference=False 명시적 전달 시 False여야 한다."""
    res = _to_analyze_response(SESS, _rooms(), _tones(), has_reference=False)
    assert res.has_reference is False

  def test_기존_필드_정상_동작(self):
    """has_reference 추가 후에도 session_id, rooms, tone_candidates 필드가 정상이어야 한다."""
    res = _to_analyze_response(SESS, _rooms(), _tones(), has_reference=True)
    assert str(res.session_id) == SESS
    assert len(res.rooms) == 1
    assert len(res.tone_candidates) == 1


class TestValidateFileReference:
  def test_unsupported_mime_415(self):
    """미지원 MIME 형식은 415를 발생시켜야 한다."""
    file = MagicMock()
    file.content_type = 'image/gif'
    with pytest.raises(HTTPException) as exc:
      _validate_file(file, b'data')
    assert exc.value.status_code == 415

  def test_over_5mb_413(self):
    """5MB 초과 파일은 413을 발생시켜야 한다."""
    file = MagicMock()
    file.content_type = 'image/jpeg'
    with pytest.raises(HTTPException) as exc:
      _validate_file(file, b'x' * (5 * 1024 * 1024 + 1))
    assert exc.value.status_code == 413

  def test_exactly_5mb_통과(self):
    """정확히 5MB는 통과해야 한다."""
    file = MagicMock()
    file.content_type = 'image/jpeg'
    _validate_file(file, b'x' * (5 * 1024 * 1024))  # 예외 없음

  def test_valid_jpeg_통과(self):
    """유효한 JPEG 파일은 예외 없이 통과해야 한다."""
    file = MagicMock()
    file.content_type = 'image/jpeg'
    _validate_file(file, b'valid-data')

  def test_valid_png_통과(self):
    """유효한 PNG 파일은 예외 없이 통과해야 한다."""
    file = MagicMock()
    file.content_type = 'image/png'
    _validate_file(file, b'valid-data')
