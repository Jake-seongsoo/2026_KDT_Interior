"""가전 배치 옵션(appliances)의 Imagen 프롬프트 반영 테스트"""
import pytest
from unittest.mock import patch
from services.claude_service import ClaudeService


TONE = {
  'name': '내추럴 모던',
  'keywords': ['우드', '린넨'],
  'color_palette': [{'name': 'ivory', 'hex': '#F5EFE5'}],
}


@pytest.fixture
def svc():
  with patch('services.claude_service.get_settings'):
    return ClaudeService()


class TestBuildApplianceHint:
  """_build_appliance_hint 단위 테스트"""

  def test_refinement_없으면_빈_문자열(self, svc):
    result = svc._build_appliance_hint('주방', None)
    assert result == ''

  def test_appliances_없으면_빈_문자열(self, svc):
    result = svc._build_appliance_hint('주방', {'appliances': None})
    assert result == ''

  def test_appliances_빈_리스트면_빈_문자열(self, svc):
    result = svc._build_appliance_hint('주방', {'appliances': []})
    assert result == ''

  def test_해당_방_가전_영문으로_변환(self, svc):
    result = svc._build_appliance_hint('주방', {
      'appliances': [
        {'name': '냉장고', 'room': '주방'},
        {'name': '인덕션', 'room': '주방'},
      ]
    })
    assert 'refrigerator' in result
    assert 'induction cooktop' in result
    assert 'integrated naturally' in result

  def test_다른_방_가전은_제외(self, svc):
    result = svc._build_appliance_hint('주방', {
      'appliances': [
        {'name': '냉장고', 'room': '주방'},
        {'name': '세탁기', 'room': '다용도실'},  # 다른 방 → 주방 프롬프트에서 제외
      ]
    })
    assert 'refrigerator' in result
    assert 'washing machine' not in result

  def test_다용도실_가전_해당_방에만_포함(self, svc):
    appliances = [
      {'name': '세탁기', 'room': '다용도실'},
      {'name': '건조기', 'room': '다용도실'},
      {'name': '스타일러', 'room': '다용도실'},
    ]
    utility_result = svc._build_appliance_hint('다용도실', {'appliances': appliances})
    kitchen_result = svc._build_appliance_hint('주방', {'appliances': appliances})

    assert 'washing machine' in utility_result
    assert 'dryer' in utility_result
    assert 'clothing care machine' in utility_result
    assert utility_result == '' or 'washing machine' in utility_result  # 욕실 프롬프트
    assert kitchen_result == ''  # 주방에는 포함 안 됨

  def test_매핑_없는_가전명은_제외(self, svc):
    # 알 수 없는 가전명은 _APPLIANCE_EN_MAP에 없으므로 제외
    result = svc._build_appliance_hint('거실', {
      'appliances': [{'name': '알수없는가전', 'room': '거실'}]
    })
    assert result == ''


class TestBuildImagenPromptWithAppliances:
  """build_imagen_prompt에서 appliances 통합 동작 테스트"""

  def test_주방_냉장고_전자레인지_프롬프트_포함(self, svc):
    room = {'room_type': '주방'}
    prompt = svc.build_imagen_prompt(room, TONE, refinement={
      'appliances': [
        {'name': '냉장고', 'room': '주방'},
        {'name': '전자레인지', 'room': '주방'},
        {'name': '식기세척기', 'room': '주방'},
      ]
    })
    assert 'refrigerator' in prompt
    assert 'microwave oven' in prompt
    assert 'dishwasher' in prompt

  def test_다용도실_세탁기_건조기_스타일러(self, svc):
    room = {'room_type': '다용도실'}
    prompt = svc.build_imagen_prompt(room, TONE, refinement={
      'appliances': [
        {'name': '세탁기', 'room': '다용도실'},
        {'name': '건조기', 'room': '다용도실'},
        {'name': '스타일러', 'room': '다용도실'},
      ]
    })
    assert 'washing machine' in prompt
    assert 'dryer' in prompt
    assert 'clothing care machine' in prompt

  def test_거실_공기청정기_로봇청소기(self, svc):
    room = {'room_type': '거실'}
    prompt = svc.build_imagen_prompt(room, TONE, refinement={
      'appliances': [
        {'name': '공기청정기', 'room': '거실'},
        {'name': '로봇청소기', 'room': '거실'},
      ]
    })
    assert 'air purifier' in prompt
    assert 'robot vacuum' in prompt

  def test_appliances_없을때_기존_동작과_동일(self, svc):
    room = {'room_type': '거실'}
    prompt_no_refinement = svc.build_imagen_prompt(room, TONE)
    prompt_empty_appliances = svc.build_imagen_prompt(room, TONE, refinement={'appliances': []})
    # 가전 없으면 'with ... integrated naturally' 문구 없어야 함
    assert 'integrated naturally' not in prompt_no_refinement
    assert 'integrated naturally' not in prompt_empty_appliances

  def test_appliances_있으면_keep_appliances_추상_문구_생략(self, svc):
    room = {'room_type': '주방'}
    prompt = svc.build_imagen_prompt(room, TONE, refinement={
      'keep_appliances': True,
      'appliances': [{'name': '냉장고', 'room': '주방'}],
    })
    # 구체적 가전이 명시된 경우 추상 "retain existing appliances" 문구는 생략
    assert 'retain existing appliances' not in prompt
    assert 'refrigerator' in prompt

  def test_keep_appliances_True_appliances_없으면_추상_문구_유지(self, svc):
    room = {'room_type': '거실'}
    prompt = svc.build_imagen_prompt(room, TONE, refinement={
      'keep_appliances': True,
      'appliances': None,
    })
    assert 'retain existing appliances' in prompt

  def test_방이_다르면_프롬프트_교차_오염_없음(self, svc):
    appliances = [
      {'name': '냉장고', 'room': '주방'},
      {'name': '세탁기', 'room': '다용도실'},
    ]
    kitchen_prompt = svc.build_imagen_prompt({'room_type': '주방'}, TONE, refinement={'appliances': appliances})
    utility_prompt = svc.build_imagen_prompt({'room_type': '다용도실'}, TONE, refinement={'appliances': appliances})

    assert 'refrigerator' in kitchen_prompt
    assert 'washing machine' not in kitchen_prompt

    assert 'washing machine' in utility_prompt
    assert 'refrigerator' not in utility_prompt
