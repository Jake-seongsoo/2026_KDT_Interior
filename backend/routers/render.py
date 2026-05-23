import asyncio
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status

from core.auth import AuthUser, verify_jwt
from core.config import get_settings
from core.room_furniture_map import get_furniture_slots
from models.schemas import ProductOut, RenderRequest, RenderResponse, RoomResultOut, ToneCandidateOut
from services.claude_service import ClaudeService
from services.imagen_service import ImagenService
from services.ikea_service import IkeaService
from services.product_filter import enrich_query_with_vision, filter_products_by_expected_colors, rerank_products_by_visuals
from services.storage_service import StorageService
from services.supabase_service import SupabaseService
from services.svg_service import build_layout_svg

logger = logging.getLogger(__name__)

router = APIRouter(tags=['render'])

# 렌더링 실패 시 대체 이미지 URL
_PLACEHOLDER_URL = None  # None으로 반환, 프론트에서 fallback UI 표시


def _to_tone_out(tone: dict) -> ToneCandidateOut:
  return ToneCandidateOut(
    id=tone['id'],
    tone_index=tone.get('tone_index', 1),
    name=tone['name'],
    category=tone.get('category', ''),
    description=tone.get('description', ''),
    reason=tone.get('reason', ''),
    color_palette=tone.get('color_palette', []),
    keywords=tone.get('keywords', []),
  )


def _room_slug(room_type: str) -> str:
  """방 이름을 GCS 경로에 사용 가능한 슬러그로 변환한다.

  매칭 우선순위: 정확 → endswith(부부욕실→욕실) → startswith(침실2→침실)
  """
  slug_map = {
    '거실': 'livingroom',
    '주방': 'kitchen',
    '주방/식당': 'kitchen',
    '안방': 'master_bedroom',
    '침실': 'bedroom',
    '욕실': 'bathroom',
    '발코니': 'balcony',
    '발코나': 'balcony',
    '현관': 'entrance',
    '다용도실': 'utility',
    '알파룸': 'alpha_room',
    '드레스룸': 'dressroom',
  }
  if room_type in slug_map:
    return slug_map[room_type]
  for key, slug in slug_map.items():
    if room_type.endswith(key):
      return slug
  for key, slug in slug_map.items():
    if room_type.startswith(key):
      suffix = room_type[len(key):]
      return f'{slug}{suffix}'
  return 'room'


def _build_product_query(room: dict, tone: dict) -> str:
  """방 유형과 선택 톤 키워드로 이케아 검색 쿼리를 생성한다. (단일 쿼리 폴백 경로 전용)

  욕실·주방 등 기능적 공간은 방 이름을 앞에 붙여 전용 상품이 검색되도록 한다.
  """
  keywords = tone.get('keywords', [])
  room_type = room.get('room_type', '거실')

  # 방 유형별 대표 품목 (이케아 판매 기준)
  # 욕실·주방 등 기능 공간은 방 이름이 prefix로 붙음
  furniture_map = {
    '거실': '소파',
    '주방': '주방 식탁',
    '안방': '침대',
    '침실': '침대',
    '욕실': '욕실 수납장',
    '발코니': '발코니 선반',
    '발코나': '발코니 선반',
    '알파룸': '책상',
    '드레스룸': '행거',
  }
  furniture = furniture_map.get(room_type)
  if furniture is None:
    furniture = next((v for k, v in furniture_map.items() if room_type.endswith(k)), None)
  if furniture is None:
    furniture = next((v for k, v in furniture_map.items() if room_type.startswith(k)), '가구')

  style = keywords[0] if keywords else tone.get('name', '')

  return f'{style} {furniture}'


async def _process_room_vision_and_products(
  room_queries: list[dict],
  img_bytes: bytes,
  claude: ClaudeService,
  ikea: IkeaService,
  use_vision: bool,
) -> tuple[list[dict], dict | None]:
  """Vision으로 렌더링 이미지를 먼저 분석한 뒤 쿼리를 보강해 이케아를 검색한다.

  Vision 분석 결과(색상·재질·스타일)를 검색 쿼리에 반영하므로
  이미지에 보이는 가구 스타일과 유사한 상품이 검색된다.
  Vision 실패 시 원본 텍스트 쿼리로 폴백한다.
  """
  slots = [fq['slot'] for fq in room_queries]

  # 1단계: Vision 분석 (이미지 있을 때만)
  visual_attrs: dict | None = None
  if use_vision and isinstance(img_bytes, bytes):
    visual_attrs = await claude.analyze_render_visuals(img_bytes, 'image/jpeg', slots)

  # 2단계: Vision 결과로 슬롯별 쿼리 보강
  enriched_queries = [
    {**fq, 'query': enrich_query_with_vision(fq['query'], (visual_attrs or {}).get(fq['slot']))}
    for fq in room_queries
  ]

  # 3단계: 보강된 쿼리로 이케아 검색
  ikea_results = await asyncio.gather(
    *[ikea.search_products(fq['query'], display=10) for fq in enriched_queries],
    return_exceptions=True,
  )

  flat: list[dict] = []
  for fq, ikea_prods in zip(enriched_queries, ikea_results):
    if isinstance(ikea_prods, Exception) or not ikea_prods:
      continue
    reranked = rerank_products_by_visuals(
      ikea_prods,
      fq.get('expected_colors', []),
      visual_attrs,
      limit=5,
    )
    for p in reranked:
      p['slot'] = fq['slot']
    flat.extend(reranked)

  return flat, visual_attrs


async def _build_furniture_queries(
  claude: ClaudeService,
  rooms: list[dict],
  tone: dict,
) -> list[list[dict]]:
  """Claude로 방별 가구 슬롯 검색어를 생성한다. 실패 시 기존 단일 쿼리로 폴백."""
  slots_map = {r['room_type']: get_furniture_slots(r['room_type']) for r in rooms}
  try:
    queries_by_room = await claude.generate_furniture_queries(
      tone=tone,
      rooms=rooms,
      slots_map=slots_map,
    )
    return [queries_by_room.get(r['id'], []) for r in rooms]
  except Exception as e:
    logger.warning('가구 쿼리 생성 실패, 단일 쿼리 폴백: %s', e)
    return [
      [{'slot': '가구', 'query': _build_product_query(r, tone), 'expected_colors': []}]
      for r in rooms
    ]


async def _verify_session_and_tone(
  db: SupabaseService,
  body: RenderRequest,
  user: AuthUser,
) -> tuple[dict, list[dict], dict]:
  """세션 소유자 확인 + 렌더링 대상 방 + 선택 톤을 조회한다."""
  try:
    session = await db.get_session(str(body.session_id))
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

  if session.get('user_id') != user.user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail='이 세션에 접근할 권한이 없습니다.',
    )

  rooms = await db.get_render_target_rooms(str(body.session_id))
  if not rooms:
    raise HTTPException(
      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail='렌더링할 방이 없습니다.',
    )

  try:
    tone = await db.get_tone(str(body.selected_tone_id))
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

  if tone.get('session_id') != str(body.session_id):
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail='선택한 톤이 이 세션에 속하지 않습니다.',
    )

  return session, rooms, tone


async def _upload_render_image(
  img_result: bytes | Exception,
  room: dict,
  room_index: int,
  rationale: str,
  result_id: str,
  storage: StorageService,
) -> tuple[str | None, str, str]:
  """렌더링 이미지를 GCS에 업로드하고 (render_url, gcs_path, rationale)을 반환한다."""
  if isinstance(img_result, Exception):
    logger.warning('방 렌더링 실패 (%s): %s', room['room_type'], img_result)
    return None, '', f'{room["room_type"]} 이미지 생성에 실패했습니다.'

  slug = _room_slug(room['room_type'])
  if room_index > 0:
    slug = f'{slug}_{room_index}'

  gcs_path = await asyncio.to_thread(storage.upload_render, result_id, slug, img_result)
  render_url = storage.public_url_for_render(gcs_path)
  return render_url, gcs_path, rationale


@router.post('/render', response_model=RenderResponse)
async def render(
  body: RenderRequest,
  user: AuthUser = Depends(verify_jwt),  # RISK-03
) -> RenderResponse:
  """선택한 톤으로 방별 인테리어 시안을 생성한다."""
  started_ms = int(time.time() * 1000)

  db = SupabaseService()
  storage = StorageService()
  imagen = ImagenService()
  ikea = IkeaService()
  claude = ClaudeService()

  session, rooms, tone = await _verify_session_and_tone(db, body, user)

  refinement = body.refinement_dict()

  # 방별 Imagen 프롬프트 생성
  imagen_specs = [
    {
      'room_type': room['room_type'],
      'prompt': claude.build_imagen_prompt(room, tone, refinement=refinement),
      'rationale': claude.build_rationale(room, tone),
    }
    for room in rooms
  ]

  settings = get_settings()
  use_multi_furniture = settings.ENABLE_MULTI_FURNITURE_RECO

  logger.info(
    '렌더링 시작: 방 %d개 (session=%s, multi_furniture=%s)',
    len(rooms), body.session_id, use_multi_furniture,
  )

  # recommendation_results 헤더 먼저 생성
  result = await db.create_result(
    session_id=str(body.session_id),
    user_id=user.user_id,
    selected_tone_id=str(body.selected_tone_id),
    budget_10k_won=body.budget_10k_won,
    trend_snapshot=session.get('trend_snapshot'),
    refinement_params=refinement,
  )
  result_id = result['id']

  furniture_queries_per_room: list[list[dict]] = [[] for _ in rooms]

  visual_attrs_per_room: list[dict | None] = [None] * len(rooms)

  if use_multi_furniture:
    # Phase 2: Claude로 가구별 검색어 생성 → Imagen 병렬 실행 → 방별 Vision+Naver 병렬
    furniture_queries_per_room, image_results = await asyncio.gather(
      _build_furniture_queries(claude, rooms, tone),
      imagen.render_rooms_parallel(imagen_specs),
    )

    use_vision = settings.ENABLE_VISION_RERANK

    # 방별로 Vision 분석 + Naver 검색을 동시에 수행
    room_tasks = [
      _process_room_vision_and_products(
        room_queries=furniture_queries_per_room[i],
        img_bytes=image_results[i] if i < len(image_results) else Exception('인덱스 초과'),
        claude=claude,
        ikea=ikea,
        use_vision=use_vision,
      )
      for i in range(len(rooms))
    ]
    room_task_results = await asyncio.gather(*room_tasks, return_exceptions=True)

    product_results: list[list[dict]] = []
    for i, task_result in enumerate(room_task_results):
      if isinstance(task_result, Exception):
        product_results.append([])
      else:
        flat, visual_attrs = task_result
        product_results.append(flat)
        visual_attrs_per_room[i] = visual_attrs

  else:
    # 단일 쿼리 경로 — 이케아만 사용
    product_queries = [_build_product_query(room, tone) for room in rooms]
    image_results, ikea_only = await asyncio.gather(
      imagen.render_rooms_parallel(imagen_specs),
      asyncio.gather(*[ikea.search_products(q, display=5) for q in product_queries], return_exceptions=True),
    )
    product_results = [
      prods if not isinstance(prods, Exception) else []
      for prods in ikea_only
    ]

  # 방별 결과 조립 + GCS 업로드 + DB 저장
  room_results_out: list[RoomResultOut] = []
  for i, (room, spec) in enumerate(zip(rooms, imagen_specs)):
    img_result = image_results[i] if i < len(image_results) else Exception('인덱스 초과')
    prod_result = product_results[i] if i < len(product_results) else []

    render_url, render_gcs_path, rationale = await _upload_render_image(
      img_result, room, i, spec['rationale'], result_id, storage
    )

    # room_renders 저장
    render_row = await db.insert_room_render(
      result_id=result_id,
      room_id=room['id'],
      room_type=room['room_type'],
      rationale=rationale,
      render_gcs_path=render_gcs_path,
      prompt=spec['prompt'],
      furniture_queries=furniture_queries_per_room[i] if use_multi_furniture else None,
    )

    # 상품 저장
    products_clean: list[dict] = []
    if isinstance(prod_result, Exception):
      logger.warning('상품 검색 실패 (%s): %s', room['room_type'], prod_result)
    else:
      products_clean = prod_result if isinstance(prod_result, list) else []

    await db.insert_products(render_row['id'], products_clean)

    room_results_out.append(
      RoomResultOut(
        room_id=room['id'],
        room_type=room['room_type'],
        rationale=rationale,
        render_url=render_url,
        visual_attributes=visual_attrs_per_room[i],
        products=[
          ProductOut(
            naver_product_id=p.get('naver_product_id'),
            name=p['name'],
            category=p.get('category'),
            slot=p.get('slot'),
            price_min=p.get('price_min', 0),
            price_max=p.get('price_max', 0),
            image_url=p.get('image_url'),
            purchase_url=p.get('purchase_url'),
            match_score=p.get('match_score'),
            match_reasons=p.get('match_reasons'),
            source=p.get('source'),
          )
          for p in products_clean
        ],
      )
    )

  # SVG 배치도 생성 (동기, 빠름)
  svg_layout = build_layout_svg(rooms)

  # 처리 시간 업데이트
  processing_ms = int(time.time() * 1000) - started_ms
  await db.update_result_processing_ms(result_id, processing_ms)

  # 톤 Pydantic 모델 변환
  logger.info('렌더링 완료 (result=%s, %dms)', result_id, processing_ms)

  return RenderResponse(
    result_id=result_id,
    selected_tone=_to_tone_out(tone),
    svg_layout=svg_layout,
    room_results=room_results_out,
    processing_ms=processing_ms,
  )


@router.get('/results/{result_id}', response_model=RenderResponse)
async def get_render_result(
  result_id: str,
  user: AuthUser = Depends(verify_jwt),
) -> RenderResponse:
  """저장된 렌더링 결과를 다시 조회한다."""
  db = SupabaseService()
  storage = StorageService()

  try:
    result = await db.get_result(result_id)
    session = await db.get_session(result['session_id'])
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

  if result.get('user_id') != user.user_id or session.get('user_id') != user.user_id:
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail='이 결과에 접근할 권한이 없습니다.',
    )

  try:
    tone = await db.get_tone(result['selected_tone_id'])
  except ValueError as e:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e

  rooms = await db.get_render_target_rooms(result['session_id'])
  svg_layout = build_layout_svg(rooms)
  room_renders = await db.get_room_renders(result_id)

  products_by_render_id = {
    render_row['id']: await db.get_products_by_room_render(render_row['id'])
    for render_row in room_renders
  }

  room_results_out = [
    RoomResultOut(
      room_id=render_row['room_id'],
      room_type=render_row['room_type'],
      rationale=render_row.get('rationale') or '',
      render_url=(
        storage.public_url_for_render(render_row['render_gcs_path'])
        if render_row.get('render_gcs_path')
        else _PLACEHOLDER_URL
      ),
      products=[
        ProductOut(
          naver_product_id=p.get('naver_product_id'),
          name=p['name'],
          category=p.get('category'),
          price_min=p.get('price_min', 0),
          price_max=p.get('price_max', 0),
          image_url=p.get('image_url'),
          purchase_url=p.get('purchase_url'),
        )
        for p in products_by_render_id.get(render_row['id'], [])
      ],
    )
    for render_row in room_renders
  ]

  return RenderResponse(
    result_id=result_id,
    selected_tone=_to_tone_out(tone),
    svg_layout=svg_layout,
    room_results=room_results_out,
    processing_ms=result.get('processing_ms', 0),
  )
