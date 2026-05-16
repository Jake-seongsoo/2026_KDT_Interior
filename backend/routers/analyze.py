import asyncio
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from core.auth import AuthUser, verify_jwt
from models.schemas import AnalyzeResponse, RoomOut, ToneCandidateOut
from services.claude_service import ClaudeService
from services.storage_service import StorageService
from services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter(tags=['analyze'])

_MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
_ALLOWED_TYPES = {'image/jpeg', 'image/jpg', 'image/png'}


def _to_analyze_response(
  session_id: str,
  rooms_data: list[dict],
  tones_data: list[dict],
  warnings: list[str] | None = None,
) -> AnalyzeResponse:
  rooms_out = [
    RoomOut(
      id=r['id'],
      room_type=r['room_type'],
      confidence=r.get('confidence', 0.5),
      priority=r.get('priority', 0),
      area_sqm=r.get('area_sqm'),
    )
    for r in rooms_data
  ]
  tones_out = [
    ToneCandidateOut(
      id=t['id'],
      tone_index=t.get('tone_index', i + 1),
      name=t['name'],
      category=t.get('category', ''),
      description=t.get('description', ''),
      reason=t.get('reason', ''),
      color_palette=t.get('color_palette', []),
      keywords=t.get('keywords', []),
    )
    for i, t in enumerate(tones_data)
  ]

  return AnalyzeResponse(
    session_id=session_id,
    rooms=rooms_out,
    tone_candidates=tones_out,
    warnings=warnings or [],
  )


@router.get('/analyze/{session_id}', response_model=AnalyzeResponse)
async def get_analyze_result(
  session_id: str,
  user: AuthUser = Depends(verify_jwt),
) -> AnalyzeResponse:
  """저장된 분석 결과를 다시 조회한다."""
  db = SupabaseService()
  try:
    session = await db.get_session(session_id)
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

  if session.get('user_id') != user.user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail='이 세션에 접근할 권한이 없습니다.',
    )

  rooms_data = await db.get_rooms_by_session(session_id)
  tones_data = await db.get_tone_candidates_by_session(session_id)
  return _to_analyze_response(session_id, rooms_data, tones_data)


@router.post('/analyze', response_model=AnalyzeResponse)
async def analyze(
  file: UploadFile = File(...),
  floor_area_pyeong: float = Form(..., ge=1.0, le=200.0),
  user: AuthUser = Depends(verify_jwt),  # RISK-03
) -> AnalyzeResponse:
  """도면 이미지를 분석해 방 정보와 톤 후보 6개를 반환한다."""
  # 파일 형식 검사
  if file.content_type not in _ALLOWED_TYPES:
    raise HTTPException(
      status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
      detail='JPG 또는 PNG 파일만 지원합니다.',
    )

  # 5MB 제한
  data = await file.read()
  if len(data) > _MAX_FILE_SIZE:
    raise HTTPException(
      status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
      detail='파일 크기는 5MB 이하여야 합니다.',
    )

  db = SupabaseService()
  storage = StorageService()
  claude = ClaudeService()

  # 세션 생성 (status='analyzing')
  session = await db.create_session(
    user_id=user.user_id,
    floor_area_pyeong=floor_area_pyeong,
  )
  session_id = session['id']
  logger.info('분석 세션 생성: %s (user=%s)', session_id, user.user_id)

  # GCS 업로드 + Vision 분석 병렬 실행
  # GCS 완료를 기다리지 않고 메모리 내 binary로 Claude 호출 즉시 시작
  upload_task = asyncio.to_thread(
    storage.upload_floorplan,
    user.user_id,
    session_id,
    data,
    file.content_type,
  )
  vision_task = claude.analyze_floorplan(data, file.content_type, floor_area_pyeong)

  try:
    gcs_path, vision_result = await asyncio.gather(upload_task, vision_task)
  except Exception as e:
    await db.update_session_status(session_id, 'failed')
    logger.error('분석 실패 (session=%s): %s', session_id, e)
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail='도면 분석 중 오류가 발생했습니다. 다시 시도해주세요.',
    ) from e

  # GCS 경로 업데이트
  await db.update_session_gcs_path(session_id, gcs_path)

  # 방 정보 저장
  raw_rooms = vision_result.get('rooms', [])
  if not raw_rooms:
    await db.update_session_status(session_id, 'failed')
    raise HTTPException(
      status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
      detail='도면에서 방을 인식하지 못했습니다. 한글 방 이름이 보이는 선명한 도면을 사용해주세요.',
    )

  rooms_data = await db.insert_rooms(session_id, raw_rooms)

  # 톤 후보 6개 생성
  try:
    tones_raw, trend_snapshot = await claude.generate_tone_candidates(
      rooms_data, floor_area_pyeong
    )
  except Exception as e:
    await db.update_session_status(session_id, 'failed')
    logger.error('톤 생성 실패 (session=%s): %s', session_id, e)
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail='톤 후보 생성 중 오류가 발생했습니다.',
    ) from e

  tones_data = await db.insert_tone_candidates(session_id, tones_raw)
  await db.update_session_status(session_id, 'completed', trend_snapshot)

  warnings = vision_result.get('warnings', [])
  logger.info('분석 완료 (session=%s): 방 %d개, 톤 %d개', session_id, len(rooms_data), len(tones_data))

  return _to_analyze_response(session_id, rooms_data, tones_data, warnings)
