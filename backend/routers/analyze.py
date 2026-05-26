import asyncio
import json
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
  has_reference: bool = False,
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
    has_reference=has_reference,
  )


async def _analyze_floorplan_and_save_rooms(
  file_data: bytes,
  content_type: str,
  floor_area_pyeong: float,
  user_id: str,
  db: SupabaseService,
  storage: StorageService,
  claude: ClaudeService,
) -> tuple[str, list[dict], list[str]]:
  """Vision 분석 + GCS 업로드 + 방 저장 공통 로직.

  반환: (session_id, rooms_data, warnings)
  """
  session = await db.create_session(user_id=user_id, floor_area_pyeong=floor_area_pyeong)
  session_id = session['id']
  logger.info('분석 세션 생성: %s (user=%s)', session_id, user_id)

  upload_task = asyncio.to_thread(
    storage.upload_floorplan, user_id, session_id, file_data, content_type
  )
  vision_task = claude.analyze_floorplan(file_data, content_type, floor_area_pyeong)

  try:
    gcs_path, vision_result = await asyncio.gather(upload_task, vision_task)
  except Exception as e:
    await db.update_session_status(session_id, 'failed')
    logger.error('분석 실패 (session=%s): %s', session_id, e)
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail='도면 분석 중 오류가 발생했습니다. 다시 시도해주세요.',
    ) from e

  await db.update_session_gcs_path(session_id, gcs_path)

  raw_rooms = vision_result.get('rooms', [])
  if not raw_rooms:
    await db.update_session_status(session_id, 'failed')
    raise HTTPException(
      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail='도면에서 방을 인식하지 못했습니다. 한글 방 이름이 보이는 선명한 도면을 사용해주세요.',
    )

  rooms_data = await db.insert_rooms(session_id, raw_rooms)
  warnings = vision_result.get('warnings', [])
  return session_id, rooms_data, warnings


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
  has_reference = bool(session.get('reference_gcs_path'))
  return _to_analyze_response(session_id, rooms_data, tones_data, has_reference=has_reference)


def _validate_file(file: UploadFile, data: bytes) -> None:
  """파일 형식과 크기를 검사한다."""
  if file.content_type not in _ALLOWED_TYPES:
    raise HTTPException(
      status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
      detail='JPG 또는 PNG 파일만 지원합니다.',
    )
  if len(data) > _MAX_FILE_SIZE:
    raise HTTPException(
      status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
      detail='파일 크기는 5MB 이하여야 합니다.',
    )


async def _handle_reference_upload(
  reference: UploadFile | None,
  user_id: str,
  session_id: str,
  db: SupabaseService,
  storage: StorageService,
  claude: ClaudeService,
) -> dict | None:
  """레퍼런스 이미지 업로드·Vision 분석·DB 저장을 처리한다.

  reference가 없으면 None 반환(정상 경로). Vision 분석이 실패해도 업로드는 유지하고
  signature만 None으로 저장 — 톤 생성은 시그니처 없이 진행되어 graceful degrade.
  """
  if reference is None:
    return None

  ref_data = await reference.read()
  _validate_file(reference, ref_data)

  upload_task = asyncio.to_thread(
    storage.upload_reference, user_id, session_id, ref_data, reference.content_type
  )
  vision_task = claude.analyze_reference_image(ref_data, reference.content_type)

  ref_gcs_path, signature = await asyncio.gather(upload_task, vision_task)
  await db.update_session_reference(session_id, ref_gcs_path, signature)
  logger.info(
    '레퍼런스 처리 완료 (session=%s): gcs=%s signature=%s',
    session_id, ref_gcs_path, 'OK' if signature else 'FAIL',
  )
  return signature


@router.post('/analyze', response_model=AnalyzeResponse)
async def analyze(
  file: UploadFile = File(...),
  floor_area_pyeong: float = Form(..., ge=1.0, le=200.0),
  reference: UploadFile | None = File(None),
  user: AuthUser = Depends(verify_jwt),
) -> AnalyzeResponse:
  """도면 이미지를 분석해 방 정보와 톤 후보 6개를 반환한다.

  reference 이미지가 있으면 톤 6개를 모두 그 분위기로 변주한다.
  """
  data = await file.read()
  _validate_file(file, data)

  db = SupabaseService()
  storage = StorageService()
  claude = ClaudeService()

  session_id, rooms_data, warnings = await _analyze_floorplan_and_save_rooms(
    data, file.content_type, floor_area_pyeong, user.user_id, db, storage, claude
  )

  reference_signature = await _handle_reference_upload(
    reference, user.user_id, session_id, db, storage, claude
  )

  try:
    tones_raw, trend_snapshot = await claude.generate_tone_candidates(
      rooms_data, floor_area_pyeong, reference_signature=reference_signature,
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

  logger.info('분석 완료 (session=%s): 방 %d개, 톤 %d개', session_id, len(rooms_data), len(tones_data))
  return _to_analyze_response(
    session_id, rooms_data, tones_data, warnings, has_reference=reference is not None,
  )


@router.post('/analyze/custom', response_model=AnalyzeResponse)
async def analyze_custom(
  file: UploadFile = File(...),
  floor_area_pyeong: float = Form(..., ge=1.0, le=200.0),
  user_text: str = Form('', max_length=500),
  mood_chips: str = Form('[]'),
  reference: UploadFile | None = File(None),
  user: AuthUser = Depends(verify_jwt),
) -> AnalyzeResponse:
  """사용자 입력(자유 텍스트 + 무드 칩)을 기반으로 톤 변형 3개를 반환한다.

  레퍼런스 이미지만 있어도 동작하며, user_text와 reference 둘 다 없으면 400 반환.
  """
  data = await file.read()
  _validate_file(file, data)

  if not user_text.strip() and reference is None:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='원하는 분위기를 입력하거나 레퍼런스 이미지를 추가해주세요.',
    )

  try:
    chips: list[str] = json.loads(mood_chips)
    if not isinstance(chips, list):
      chips = []
  except (json.JSONDecodeError, ValueError):
    chips = []

  db = SupabaseService()
  storage = StorageService()
  claude = ClaudeService()

  session_id, rooms_data, warnings = await _analyze_floorplan_and_save_rooms(
    data, file.content_type, floor_area_pyeong, user.user_id, db, storage, claude
  )

  reference_signature = await _handle_reference_upload(
    reference, user.user_id, session_id, db, storage, claude
  )

  try:
    tones_raw, trend_snapshot = await claude.generate_custom_tone_variants(
      rooms_data, floor_area_pyeong, user_text, chips,
      reference_signature=reference_signature,
    )
  except Exception as e:
    await db.update_session_status(session_id, 'failed')
    logger.error('커스텀 톤 생성 실패 (session=%s): %s', session_id, e)
    raise HTTPException(
      status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
      detail='톤 변형 생성 중 오류가 발생했습니다.',
    ) from e

  tones_data = await db.insert_tone_candidates(session_id, tones_raw)
  await db.update_session_status(session_id, 'completed', trend_snapshot)

  logger.info('커스텀 분석 완료 (session=%s): 방 %d개, 톤 %d개', session_id, len(rooms_data), len(tones_data))
  return _to_analyze_response(
    session_id, rooms_data, tones_data, warnings, has_reference=reference is not None,
  )
