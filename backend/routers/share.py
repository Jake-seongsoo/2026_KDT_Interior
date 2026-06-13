"""공유 링크 라우터 (F008).

- POST /share        본인 결과의 공유 링크 생성 (로그인 필요)
- GET  /share/{id}   공유 링크로 결과 조회 (비로그인 허용, 상품 제외, 조회수 증가)

공유 토큰은 share_links.id(uuid)이며 result_id를 직접 노출하지 않는다.
공유 응답은 렌더 이미지 + 톤만 포함하고 추천 상품은 제외한다(include_products=False).
RenderResponse에는 도면·개인정보가 없어 비로그인 노출이 안전하다.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import AuthUser, ensure_owner, verify_jwt
from models.schemas import RenderResponse, ShareCreateRequest, ShareCreateResponse
from routers.render import _assemble_render_response
from services.storage_service import StorageService
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(tags=['share'])


@router.post('/share', response_model=ShareCreateResponse)
async def create_share(
  body: ShareCreateRequest,
  user: AuthUser = Depends(verify_jwt),
) -> ShareCreateResponse:
  """본인 결과의 공유 링크를 생성한다 (이미 있으면 기존 id 반환)."""
  db = SupabaseService()

  try:
    result = await db.get_result(str(body.result_id))
    session = await db.get_session(result['session_id'])
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

  ensure_owner(user, result, session, detail='이 결과를 공유할 권한이 없습니다.')

  share = await db.create_share_link(str(body.result_id))
  logger.info('공유 링크 생성: result=%s, share=%s', body.result_id, share['id'])
  return ShareCreateResponse(share_id=share['id'])


@router.get('/share/{share_id}', response_model=RenderResponse)
async def get_shared_result(share_id: str) -> RenderResponse:
  """공유 링크로 결과를 조회한다 (비로그인 허용, 상품 제외, 조회수 +1)."""
  db = SupabaseService()
  storage = StorageService()

  try:
    share = await db.get_share_link(share_id)
    result = await db.get_result(share['result_id'])
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

  await db.increment_share_view(share_id, share.get('view_count', 0))

  return await _assemble_render_response(db, storage, result, include_products=False)
