"""RenderRequest 정밀화 파라미터 직렬화·역직렬화 테스트"""
import pytest
from uuid import uuid4
from models.schemas import RenderRequest


SESSION_ID = str(uuid4())
TONE_ID = str(uuid4())


def _make_request(**kwargs) -> RenderRequest:
  return RenderRequest(session_id=SESSION_ID, selected_tone_id=TONE_ID, **kwargs)


class TestRenderRequestRefinementFields:
  def test_기본값은_모두_None(self):
    req = _make_request()
    assert req.budget_10k_won is None
    assert req.family_type is None
    assert req.style_keywords is None
    assert req.keep_appliances is None

  def test_예산_설정(self):
    req = _make_request(budget_10k_won=3000)
    assert req.budget_10k_won == 3000

  def test_가족형태_설정(self):
    req = _make_request(family_type='family_with_kid')
    assert req.family_type == 'family_with_kid'

  def test_취향_키워드_설정(self):
    req = _make_request(style_keywords=['미니멀', '모던'])
    assert req.style_keywords == ['미니멀', '모던']

  def test_기존_가전_유지_설정(self):
    req = _make_request(keep_appliances=True)
    assert req.keep_appliances is True

  def test_사용자_텍스트_설정(self):
    req = _make_request(user_text='거실에 그린톤 포인트 벽을 원해요')
    assert req.user_text == '거실에 그린톤 포인트 벽을 원해요'


class TestRefinementDict:
  def test_모든_필드_없으면_None_반환(self):
    req = _make_request()
    assert req.refinement_dict() is None

  def test_예산만_있으면_dict_반환(self):
    req = _make_request(budget_10k_won=5000)
    result = req.refinement_dict()
    assert result is not None
    assert result['budget_10k_won'] == 5000
    assert result['family_type'] is None

  def test_전체_필드_있으면_dict_반환(self):
    req = _make_request(
      budget_10k_won=3000,
      family_type='couple',
      style_keywords=['내추럴'],
      keep_appliances=True,
      user_text='수납 많이',
    )
    result = req.refinement_dict()
    assert result == {
      'budget_10k_won': 3000,
      'family_type': 'couple',
      'style_keywords': ['내추럴'],
      'keep_appliances': True,
      'appliances': None,
      'user_text': '수납 많이',
    }

  def test_user_text만_있으면_dict_반환(self):
    req = _make_request(user_text='그린톤 포인트 벽')
    result = req.refinement_dict()
    assert result is not None
    assert result['user_text'] == '그린톤 포인트 벽'
    assert result['family_type'] is None

  def test_keep_appliances_False도_refinement_포함(self):
    # False는 falsy지만, 명시적으로 설정된 경우 budget 등 다른 필드가 있어야 dict 반환
    req = _make_request(budget_10k_won=1000, keep_appliances=False)
    result = req.refinement_dict()
    assert result is not None
    assert result['keep_appliances'] is False
