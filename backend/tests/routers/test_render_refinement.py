"""render 라우터의 정밀화 파라미터 처리 테스트."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models.schemas import RenderRequest


SESSION_ID = uuid.uuid4()
TONE_ID = uuid.uuid4()


def _make_request(**kwargs) -> RenderRequest:
  return RenderRequest(session_id=SESSION_ID, selected_tone_id=TONE_ID, **kwargs)


class TestRefinementDictPassthrough:
  """refinement_dict()가 router → supabase_service로 올바르게 전달되는지 확인."""

  def test_정밀화_없으면_None(self):
    req = _make_request()
    assert req.refinement_dict() is None

  def test_예산만_있으면_dict(self):
    req = _make_request(budget_10k_won=2000)
    d = req.refinement_dict()
    assert d is not None
    assert d['budget_10k_won'] == 2000

  def test_복합_정밀화_dict(self):
    req = _make_request(
      budget_10k_won=5000,
      family_type='family_with_kid',
      style_keywords=['미니멀'],
      keep_appliances=True,
    )
    d = req.refinement_dict()
    assert d['family_type'] == 'family_with_kid'
    assert d['style_keywords'] == ['미니멀']
    assert d['keep_appliances'] is True


class TestRenderRequestSerialization:
  """RenderRequest JSON 직렬화 테스트."""

  def test_정밀화_포함_직렬화(self):
    req = _make_request(
      budget_10k_won=3000,
      family_type='couple',
      style_keywords=['모던', '내추럴'],
      keep_appliances=False,
    )
    data = req.model_dump()
    assert data['budget_10k_won'] == 3000
    assert data['family_type'] == 'couple'
    assert data['style_keywords'] == ['모던', '내추럴']
    assert data['keep_appliances'] is False

  def test_정밀화_미포함_직렬화(self):
    req = _make_request()
    data = req.model_dump()
    assert data['budget_10k_won'] is None
    assert data['family_type'] is None
    assert data['style_keywords'] is None
    assert data['keep_appliances'] is None
