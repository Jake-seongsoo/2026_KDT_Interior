"""분석 기록 조회 라우터 (F011).

로그인 사용자의 분석 세션을 최근순으로 조회하고, 각 세션에 그 세션의
렌더링 결과(톤별)를 중첩해 반환한다. 본인 user_id로만 쿼리하므로
타인 데이터 노출이 원천 차단된다 (별도 ensure_owner 불필요).
"""
import asyncio
import logging

from fastapi import APIRouter, Depends

from core.auth import AuthUser, verify_jwt
from models.schemas import HistoryResponse, HistoryResultItem, HistorySessionItem
from services.storage_service import StorageService
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(tags=['history'])

_HISTORY_LIMIT = 20


def _room_summary(rooms: list[dict]) -> str:
  """방 목록(priority 순)을 중복 없는 요약 문자열로 만든다. (예: '거실·주방·안방')"""
  seen: list[str] = []
  for room in rooms:
    room_type = room.get('room_type')
    if room_type and room_type not in seen:
      seen.append(room_type)
  return '·'.join(seen) if seen else '방 정보 없음'


@router.get('/history', response_model=HistoryResponse)
async def get_history(user: AuthUser = Depends(verify_jwt)) -> HistoryResponse:
  """로그인 사용자의 분석 기록을 최근 20개 조회한다 (세션 + 결과 중첩)."""
  db = SupabaseService()
  storage = StorageService()

  sessions = await db.get_sessions_by_user(user.user_id, limit=_HISTORY_LIMIT)
  if not sessions:
    return HistoryResponse(sessions=[])

  session_ids = [s['id'] for s in sessions]
  rooms = await db.get_rooms_by_sessions(session_ids)
  results = await db.get_results_by_sessions(session_ids)

  # 톤 이름 매핑 (결과의 selected_tone_id → name)
  tone_ids = list({r['selected_tone_id'] for r in results if r.get('selected_tone_id')})
  tones = await db.get_tones_by_ids(tone_ids)
  tone_name_by_id = {str(t['id']): t.get('name', '') for t in tones}

  # 세션별 방·결과 묶기 (전체가 정렬되어 오므로 세션 내 순서 유지)
  rooms_by_session: dict[str, list[dict]] = {}
  for room in rooms:
    rooms_by_session.setdefault(room['session_id'], []).append(room)

  results_by_session: dict[str, list[dict]] = {}
  for res in results:
    results_by_session.setdefault(res['session_id'], []).append(res)

  items: list[HistorySessionItem] = []
  for s in sessions:
    sid = s['id']

    # 도면 썸네일 Signed URL — gcs_path 있을 때만, 실패해도 None으로 graceful degrade
    thumbnail_url = None
    gcs_path = s.get('gcs_path')
    if gcs_path:
      try:
        thumbnail_url = await asyncio.to_thread(storage.signed_url_for_floorplan, gcs_path)
      except Exception as e:
        logger.warning('도면 썸네일 URL 발급 실패 (session=%s): %s', sid, e)

    result_items = [
      HistoryResultItem(
        result_id=r['id'],
        tone_name=tone_name_by_id.get(str(r.get('selected_tone_id')), ''),
        created_at=r['created_at'],
      )
      for r in results_by_session.get(sid, [])
    ]

    items.append(HistorySessionItem(
      session_id=sid,
      created_at=s['created_at'],
      floor_area_pyeong=s['floor_area_pyeong'],
      status=s.get('status', 'completed'),
      room_summary=_room_summary(rooms_by_session.get(sid, [])),
      thumbnail_url=thumbnail_url,
      results=result_items,
    ))

  logger.info('기록 조회: user=%s, 세션 %d개', user.user_id, len(items))
  return HistoryResponse(sessions=items)
