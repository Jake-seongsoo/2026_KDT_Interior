"""
서비스 계층 pytest 픽스처 모음.

tests/services/ 하위 테스트 파일에서만 사용되는 픽스처.
공유 픽스처(clear_caches, minimal_jpeg 등)는 tests/conftest.py 참조.

마이그레이션 가이드 (로컬 픽스처 → conftest 교체 순서):
  1. 각 파일의 `svc` 픽스처 → `claude_service_sync`
  2. `service` 픽스처(settings+AsyncAnthropic 패치) → `claude_service_async`
  3. `_make_mock_response`, `_make_response` 함수 → `make_claude_response` 팩토리
  4. `TONE`, `SAMPLE_TONE`, `_TONE` 상수 → `minimal_tone`
  5. `SAMPLE_SIG`, `SAMPLE_SIGNATURE` 상수 → `reference_signature`
  6. `_make_svc()` (ImagenService) → `imagen_service`
  7. `_make_svc()` (StorageService) → `storage_service`
"""

import json
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ── ClaudeService 픽스처 ──────────────────────────────────────────────────────

@pytest.fixture
def claude_service_sync():
    """build_imagen_prompt 등 순수 동기 메서드 테스트용.

    AsyncAnthropic 초기화는 발생하지만 실제 API 호출은 없음.
    async 메서드(_client 사용)를 호출하면 MagicMock 반환 — 필요 시
    `svc._client.messages.create = AsyncMock(...)` 으로 교체한다.
    """
    with patch('services.claude_service.get_settings') as mock_settings, \
         patch('services.claude_service.AsyncAnthropic'):
        mock_settings.return_value = MagicMock(
            ANTHROPIC_API_KEY='test-key',
            CLAUDE_MODEL='claude-sonnet-4-6',
        )
        from services.claude_service import ClaudeService
        return ClaudeService()


@pytest.fixture
def claude_service_async():
    """generate_tone_candidates 등 async 메서드 테스트용.

    `svc._client`가 MagicMock이므로 각 테스트에서 아래처럼 주입한다:
        svc._client.messages.create = AsyncMock(return_value=make_claude_response(tones))
    """
    with patch('services.claude_service.get_settings') as mock_settings, \
         patch('services.claude_service.AsyncAnthropic'):
        mock_settings.return_value = MagicMock(
            ANTHROPIC_API_KEY='test-key',
            CLAUDE_MODEL='claude-sonnet-4-6',
        )
        from services.claude_service import ClaudeService
        yield ClaudeService()


@pytest.fixture
def make_claude_service():
    """mock_client를 직접 주입할 때 쓰는 ClaudeService 팩토리.

    test_claude_service_vision.py처럼 AsyncAnthropic의 return_value를
    서비스 생성 전에 설정해야 하는 경우에 사용한다.

    사용법:
        def test_xxx(make_claude_service):
            client = MagicMock()
            client.messages.create = AsyncMock(return_value=...)
            svc = make_claude_service(mock_client=client)
            result = await svc.some_async_method(...)

    주의: __init__에서 self._client = AsyncAnthropic(mock_client) 가 실행된 뒤
    with 블록이 종료되므로, patch 해제 후에도 self._client는 mock을 유지한다.
    생성자 밖에서 AsyncAnthropic을 다시 참조하는 코드가 생기면 이 팩토리는 깨진다.
    """
    def _factory(mock_client: MagicMock | None = None) -> object:
        with patch('services.claude_service.get_settings') as mock_settings, \
             patch('services.claude_service.AsyncAnthropic') as mock_anthropic:
            mock_settings.return_value = MagicMock(
                ANTHROPIC_API_KEY='test-key',
                CLAUDE_MODEL='claude-sonnet-4-6',
            )
            if mock_client is not None:
                mock_anthropic.return_value = mock_client
            from services.claude_service import ClaudeService
            return ClaudeService()

    return _factory


# ── Claude API 응답 팩토리 ────────────────────────────────────────────────────

@pytest.fixture
def make_claude_response():
    """Anthropic Messages API 응답 mock 객체 팩토리.

    사용법:
        # 톤 목록 → 표준 톤 추천 응답
        resp = make_claude_response(tones_list)

        # 임의 dict (reference signature, visual attrs 등)
        resp = make_claude_response({'primary_hex': '#A07...'})

        # 트렌드 요약 오버라이드
        resp = make_claude_response(tones, trend_summary=['2026: 자연소재'])
    """
    def _build(
        payload: list | dict,
        trend_summary: list[str] | None = None,
    ) -> MagicMock:
        if isinstance(payload, list):
            data: dict = {
                'tones': payload,
                'trend_summary': trend_summary or ['2026 트렌드: 자연소재'],
            }
        else:
            data = payload

        block = SimpleNamespace(
            text=f'```json\n{json.dumps(data, ensure_ascii=False)}\n```'
        )
        resp = MagicMock()
        resp.content = [block]
        return resp

    return _build


# ── 방(Room) 픽스처 ───────────────────────────────────────────────────────────

@pytest.fixture
def room_living():
    """거실 — 발코니 비인접, 면적 20.5㎡."""
    return {
        'id': str(uuid.uuid4()),
        'room_type': '거실',
        'confidence': 0.92,
        'priority': 1,
        'area_sqm': 20.5,
        'has_adjoining_balcony': False,
        'balcony_expanded': None,
    }


@pytest.fixture
def room_master():
    """안방 — 발코니 비인접, 면적 14.0㎡."""
    return {
        'id': str(uuid.uuid4()),
        'room_type': '안방',
        'confidence': 0.88,
        'priority': 2,
        'area_sqm': 14.0,
        'has_adjoining_balcony': False,
        'balcony_expanded': None,
    }


@pytest.fixture
def room_kitchen():
    """주방 — 면적 10.0㎡."""
    return {
        'id': str(uuid.uuid4()),
        'room_type': '주방',
        'confidence': 0.85,
        'priority': 3,
        'area_sqm': 10.0,
    }


@pytest.fixture
def room_bathroom():
    """욕실 — 면적 5.5㎡."""
    return {
        'id': str(uuid.uuid4()),
        'room_type': '욕실',
        'confidence': 0.85,
        'priority': 4,
        'area_sqm': 5.5,
    }


@pytest.fixture
def room_bedroom2():
    """침실2 — 면적 9.5㎡ (번호 포함 방 이름 테스트용)."""
    return {
        'id': str(uuid.uuid4()),
        'room_type': '침실2',
        'confidence': 0.80,
        'priority': 3,
        'area_sqm': 9.5,
        'has_adjoining_balcony': False,
        'balcony_expanded': None,
    }


@pytest.fixture
def standard_rooms(room_living, room_master, room_kitchen, room_bathroom):
    """거실·안방·주방·욕실 — 일반적인 4개 방 조합."""
    return [room_living, room_master, room_kitchen, room_bathroom]


# ── 톤(Tone) 픽스처 ───────────────────────────────────────────────────────────

@pytest.fixture
def minimal_tone():
    """build_imagen_prompt 테스트에 충분한 최소 톤 구조."""
    return {
        'id': str(uuid.uuid4()),
        'tone_index': 1,
        'name': '내추럴 모던',
        'category': 'natural',
        'description': '따뜻한 우드와 린넨 조합',
        'reason': '채광 좋은 거실에 적합',
        'color_palette': [
            {'name': '아이보리', 'hex': '#F5EFE5', 'role': '벽·천장'},
            {'name': '웜 브라운', 'hex': '#A0785A', 'role': '가구'},
        ],
        'keywords': ['우드', '린넨', '내추럴', '소파', '러그'],
    }


@pytest.fixture
def six_tones():
    """카테고리 다양성 규칙(6개 고유 카테고리)을 충족하는 톤 목록."""
    specs = [
        ('japandi',     '자연 속 고요',       '#E8DCC8', ['자파니즈', '원목', '미니멀']),
        ('coastal',     '해안의 바람',         '#7EC8E3', ['코스탈', '블루', '화이트', '라탄']),
        ('industrial',  '어반 인더스트리얼',    '#9E9E9E', ['인더스트리얼', '메탈', '그레이']),
        ('biophilic',   '보태니컬 그린',        '#3A5F3A', ['바이오필릭', '그린', '식물']),
        ('dark-moody',  '모던 다크',            '#2C2C2C', ['다크무디', '블랙', '매트']),
        ('vintage',     '레트로 빈티지',        '#C1694F', ['빈티지', '테라코타', '어스톤']),
    ]
    return [
        {
            'id': str(uuid.uuid4()),
            'tone_index': i + 1,
            'name': name,
            'category': cat,
            'description': f'{name} 스타일',
            'reason': f'{name}이 이 공간에 적합한 이유',
            'color_palette': [{'name': 'Primary', 'hex': hex_, 'role': '벽'}],
            'keywords': keywords,
        }
        for i, (cat, name, hex_, keywords) in enumerate(specs)
    ]


@pytest.fixture
def three_custom_tones():
    """직접 입력 모드 결과 — tone_index 1(안전)·2(중립)·3(대담)."""
    variants = [
        (1, '안전 베이지',    'natural', '사용자 입력에 충실한 따뜻한 베이지'),
        (2, '균형 웜톤',      'minimal', '베이지와 2026 트렌드 뉴트럴을 균형 있게 혼합'),
        (3, '대담 콘트라스트', 'japandi', '베이지 기반에 딥 컬러 포인트로 개성 강조'),
    ]
    return [
        {
            'id': str(uuid.uuid4()),
            'tone_index': idx,
            'name': name,
            'category': cat,
            'description': desc,
            'reason': f'{name}을 선택한 이유',
            'color_palette': [{'name': '웜 베이지', 'hex': '#E8D5B7', 'role': '벽·천장'}],
            'keywords': ['베이지', '내추럴', '따뜻함'],
        }
        for idx, name, cat, desc in variants
    ]


# ── 레퍼런스 이미지 시그니처 픽스처 ──────────────────────────────────────────

@pytest.fixture
def reference_signature():
    """레퍼런스 이미지 분석 결과 시그니처."""
    return {
        'primary_hex': '#A0785A',
        'secondary_hex': '#D4C4B0',
        'accent_hex': '#3D6B5A',
        'materials': ['원목', '린넨'],
        'style_tokens': ['보태니컬', '스칸디나비안'],
        'lighting': '자연광',
        'mood': '따뜻하고 차분한',
    }


# ── ImagenService 픽스처 ──────────────────────────────────────────────────────

@pytest.fixture
def imagen_service():
    """실제 GCP 호출 없는 ImagenService 인스턴스.

    render_room, render_rooms_parallel 테스트에서 필요한 메서드를 교체해 사용한다.
    """
    with patch('services.imagen_service.get_settings') as mock_settings, \
         patch('services.imagen_service.get_google_credentials'), \
         patch('services.imagen_service.genai.Client'):
        mock_settings.return_value = MagicMock(
            IMAGEN_MODEL='imagen-4.0-generate-001',
            IMAGEN_CAPABILITY_MODEL='imagen-3.0-capability-001',
            GCP_PROJECT_ID='test-project',
            GCP_REGION='asia-northeast3',
        )
        from services.imagen_service import ImagenService
        yield ImagenService()


# ── StorageService 픽스처 ─────────────────────────────────────────────────────

@pytest.fixture
def storage_service():
    """실제 GCS 접근 없는 StorageService 인스턴스.

    _bucket, _render_bucket이 MagicMock이므로 blob().upload_from_string() 등을
    assert_called_once_with()로 검증할 수 있다.
    """
    with patch('services.storage_service.storage.Client'), \
         patch('services.storage_service.get_settings') as mock_settings, \
         patch('services.storage_service.get_google_credentials'):
        mock_settings.return_value = MagicMock(
            GCP_PROJECT_ID='test-project',
            GCS_BUCKET_NAME='test-bucket',
            GCS_RENDER_BUCKET_NAME='test-render-bucket',
            SIGNED_URL_TTL_MINUTES=15,
        )
        from services.storage_service import StorageService
        svc = StorageService()
        svc._bucket = MagicMock()
        svc._render_bucket = MagicMock()
        yield svc
