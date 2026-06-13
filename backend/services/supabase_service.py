import logging
import uuid
from datetime import datetime, timedelta, timezone

from supabase import Client, create_client

from core.config import get_settings

logger = logging.getLogger(__name__)

# 렌더링에서 제외할 공간 (현관·수납·세탁 등 인테리어 제안 가치가 낮은 공간)
_NON_RENDER_TYPES: frozenset[str] = frozenset({
  '현관', '현관창고', '다용도실', '드레스룸', '팬트리', '실외기실', '발코니',
})


def _get_client() -> Client:
  settings = get_settings()
  return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)


class SupabaseService:
  def __init__(self) -> None:
    self._db = _get_client()

  # ── analysis_sessions ─────────────────────────────────────

  async def create_session(self, user_id: str | None, floor_area_pyeong: float) -> dict:
    """도면 분석 세션을 생성한다."""
    session_id = str(uuid.uuid4())
    expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    data = {
      'id': session_id,
      'user_id': user_id,
      'floor_area_pyeong': floor_area_pyeong,
      'status': 'analyzing',
      'expires_at': expires_at,
    }
    resp = self._db.table('analysis_sessions').insert(data).execute()
    return resp.data[0]

  async def update_session_gcs_path(self, session_id: str, gcs_path: str) -> None:
    self._db.table('analysis_sessions').update({'gcs_path': gcs_path}).eq('id', session_id).execute()

  async def update_session_reference(
    self,
    session_id: str,
    reference_gcs_path: str,
    reference_signature: dict | None,
  ) -> None:
    """레퍼런스 이미지 GCS 경로 + Vision 시그니처를 한 번에 저장한다."""
    self._db.table('analysis_sessions').update({
      'reference_gcs_path': reference_gcs_path,
      'reference_signature': reference_signature,
    }).eq('id', session_id).execute()

  async def update_session_status(
    self,
    session_id: str,
    status: str,
    trend_snapshot: dict | None = None,
  ) -> None:
    update_data: dict = {'status': status}
    if trend_snapshot:
      update_data['trend_snapshot'] = trend_snapshot
    self._db.table('analysis_sessions').update(update_data).eq('id', session_id).execute()

  async def get_session(self, session_id: str) -> dict:
    resp = self._db.table('analysis_sessions').select('*').eq('id', session_id).execute()
    if not resp.data:
      raise ValueError(f'세션을 찾을 수 없습니다: {session_id}')
    return resp.data[0]

  async def get_sessions_by_user(self, user_id: str, limit: int = 20) -> list[dict]:
    """사용자의 분석 세션을 최근순으로 조회한다 (기록 조회용).

    idx_sessions_user_created (user_id, created_at desc) 인덱스를 사용한다.
    """
    resp = (
      self._db.table('analysis_sessions')
      .select('*')
      .eq('user_id', user_id)
      .order('created_at', desc=True)
      .limit(limit)
      .execute()
    )
    return resp.data

  # ── rooms ──────────────────────────────────────────────────

  async def insert_rooms(self, session_id: str, rooms_raw: list[dict]) -> list[dict]:
    """Vision 분석 결과 방 목록을 DB에 저장하고 is_render_target을 설정한다."""
    # 우선순위 순 정렬
    sorted_rooms = sorted(rooms_raw, key=lambda r: r.get('priority', 99))
    rows = []
    for idx, room in enumerate(sorted_rooms):
      rows.append({
        'id': str(uuid.uuid4()),
        'session_id': session_id,
        'room_type': room.get('room_type', f'방{idx + 1}'),
        'area_sqm': room.get('area_sqm'),
        'confidence': room.get('confidence', 0.5),
        'priority': room.get('priority', idx + 1),
        'is_render_target': room.get('room_type', '') not in _NON_RENDER_TYPES,
        'position': room.get('position'),
        'has_adjoining_balcony': bool(room.get('has_adjoining_balcony', False)),
        'balcony_expanded': room.get('balcony_expanded'),
      })

    resp = self._db.table('rooms').insert(rows).execute()
    return resp.data

  async def get_render_target_rooms(self, session_id: str) -> list[dict]:
    resp = (
      self._db.table('rooms')
      .select('*')
      .eq('session_id', session_id)
      .eq('is_render_target', True)
      .order('priority')
      .execute()
    )
    return resp.data

  async def get_rooms_by_session(self, session_id: str) -> list[dict]:
    resp = (
      self._db.table('rooms')
      .select('*')
      .eq('session_id', session_id)
      .order('priority')
      .execute()
    )
    return resp.data

  async def get_rooms_by_sessions(self, session_ids: list[str]) -> list[dict]:
    """여러 세션의 방을 일괄 조회한다 (기록 목록의 방 요약용, N+1 방지).

    반환 행에는 session_id가 포함되어 호출부에서 세션별로 묶을 수 있다.
    """
    if not session_ids:
      return []
    resp = (
      self._db.table('rooms')
      .select('session_id, room_type, priority')
      .in_('session_id', session_ids)
      .order('priority')
      .execute()
    )
    return resp.data

  # ── tone_candidates ────────────────────────────────────────

  async def insert_tone_candidates(self, session_id: str, tones: list[dict]) -> list[dict]:
    rows = []
    for tone in tones:
      rows.append({
        'id': str(uuid.uuid4()),
        'session_id': session_id,
        'tone_index': tone.get('tone_index', len(rows) + 1),
        'name': tone.get('name', ''),
        'category': tone.get('category', ''),
        'description': tone.get('description', ''),
        'reason': tone.get('reason', ''),
        'color_palette': tone.get('color_palette', []),
        'keywords': tone.get('keywords', []),
      })

    resp = self._db.table('tone_candidates').insert(rows).execute()
    return resp.data

  async def get_tone(self, tone_id: str) -> dict:
    resp = self._db.table('tone_candidates').select('*').eq('id', tone_id).execute()
    if not resp.data:
      raise ValueError(f'톤을 찾을 수 없습니다: {tone_id}')
    return resp.data[0]

  async def get_tone_candidates_by_session(self, session_id: str) -> list[dict]:
    resp = (
      self._db.table('tone_candidates')
      .select('*')
      .eq('session_id', session_id)
      .order('tone_index')
      .execute()
    )
    return resp.data

  async def get_tones_by_ids(self, tone_ids: list[str]) -> list[dict]:
    """톤 id 목록으로 (id, name)을 일괄 조회한다 (결과 목록의 톤 이름 매핑용)."""
    if not tone_ids:
      return []
    resp = (
      self._db.table('tone_candidates')
      .select('id, name')
      .in_('id', tone_ids)
      .execute()
    )
    return resp.data

  # ── recommendation_results ────────────────────────────────

  async def create_result(
    self,
    session_id: str,
    user_id: str | None,
    selected_tone_id: str,
    budget_10k_won: int | None,
    trend_snapshot: dict | None,
    processing_ms: int = 0,
    refinement_params: dict | None = None,
  ) -> dict:
    data = {
      'id': str(uuid.uuid4()),
      'session_id': session_id,
      'user_id': user_id,
      'selected_tone_id': selected_tone_id,
      'budget_10k_won': budget_10k_won,
      'trend_snapshot': trend_snapshot,
      'processing_ms': processing_ms,
      'refinement_params': refinement_params,
    }
    resp = self._db.table('recommendation_results').insert(data).execute()
    return resp.data[0]

  async def update_result_processing_ms(self, result_id: str, processing_ms: int) -> None:
    self._db.table('recommendation_results').update(
      {'processing_ms': processing_ms}
    ).eq('id', result_id).execute()

  async def get_result(self, result_id: str) -> dict:
    resp = self._db.table('recommendation_results').select('*').eq('id', result_id).execute()
    if not resp.data:
      raise ValueError(f'결과를 찾을 수 없습니다: {result_id}')
    return resp.data[0]

  async def get_results_by_sessions(self, session_ids: list[str]) -> list[dict]:
    """여러 세션의 렌더링 결과를 최근순으로 일괄 조회한다 (기록 목록 중첩용, N+1 방지).

    톤 이름은 selected_tone_id로 get_tones_by_ids를 호출해 호출부에서 매핑한다.
    """
    if not session_ids:
      return []
    resp = (
      self._db.table('recommendation_results')
      .select('id, session_id, selected_tone_id, created_at')
      .in_('session_id', session_ids)
      .order('created_at', desc=True)
      .execute()
    )
    return resp.data

  # ── room_renders ───────────────────────────────────────────

  async def insert_room_render(
    self,
    result_id: str,
    room_id: str,
    room_type: str,
    rationale: str,
    render_gcs_path: str,
    prompt: str,
    furniture_queries: list[dict] | None = None,
  ) -> dict:
    data = {
      'id': str(uuid.uuid4()),
      'result_id': result_id,
      'room_id': room_id,
      'room_type': room_type,
      'rationale': rationale,
      'render_gcs_path': render_gcs_path,
      'prompt': prompt,
    }
    resp = self._db.table('room_renders').insert(data).execute()
    return resp.data[0]

  async def get_room_renders(self, result_id: str) -> list[dict]:
    resp = (
      self._db.table('room_renders')
      .select('*')
      .eq('result_id', result_id)
      .execute()
    )
    return resp.data

  # ── products ───────────────────────────────────────────────

  async def insert_products(self, room_render_id: str, products: list[dict]) -> None:
    if not products:
      return
    rows = []
    for p in products:
      rows.append({
        'id': str(uuid.uuid4()),
        'room_render_id': room_render_id,
        'naver_product_id': p.get('naver_product_id', ''),
        'name': p.get('name', ''),
        'category': p.get('category'),
        'slot': p.get('slot'),
        'price_min': p.get('price_min', 0),
        'price_max': p.get('price_max', 0),
        'image_url': p.get('image_url'),
        'purchase_url': p.get('purchase_url'),
      })
    self._db.table('products').insert(rows).execute()

  async def get_products_by_room_render(self, room_render_id: str) -> list[dict]:
    resp = (
      self._db.table('products')
      .select('*')
      .eq('room_render_id', room_render_id)
      .execute()
    )
    return resp.data
