from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ── 공통 모델 ───────────────────────────────────────────────

class ColorChip(BaseModel):
  name: str
  hex: str
  role: str | None = None


# ── /analyze 응답 모델 ─────────────────────────────────────

class RoomOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  room_type: str
  confidence: float = Field(ge=0.0, le=1.0)
  priority: int
  area_sqm: float | None = None
  has_adjoining_balcony: bool = False
  balcony_expanded: bool | None = None


class ToneCandidateOut(BaseModel):
  model_config = ConfigDict(from_attributes=True)

  id: UUID
  tone_index: int = Field(ge=1, le=6)
  name: str
  category: str
  description: str
  reason: str
  color_palette: list[ColorChip]
  keywords: list[str]


class AnalyzeResponse(BaseModel):
  session_id: UUID
  rooms: list[RoomOut]
  tone_candidates: list[ToneCandidateOut]
  warnings: list[str] = []
  has_reference: bool = False  # 레퍼런스 이미지 기반 톤이면 true (프론트엔드 배지 용)
  # 도면·레퍼런스 URL은 절대 포함하지 않는다 (RISK-02)


# ── /render 요청·응답 모델 ─────────────────────────────────

class Appliance(BaseModel):
  """사용자가 배치할 가전제품 1개 — 이름과 배치 방 유형을 함께 전달한다."""
  name: str   # 한국어 가전명 (냉장고, 세탁기 등)
  room: str   # 배치할 방 유형 (주방, 다용도실 등)


class RenderRequest(BaseModel):
  session_id: UUID
  selected_tone_id: UUID
  budget_10k_won: int | None = None
  family_type: str | None = None        # 'single' | 'couple' | 'family_with_kid' | 'family_with_pet'
  style_keywords: list[str] | None = None  # 무드 칩 선택 결과
  keep_appliances: bool | None = None
  appliances: list[Appliance] | None = None  # 사용자 지정 가전 배치 목록
  user_text: str | None = None           # 사용자 자유 입력 텍스트

  def refinement_dict(self) -> dict | None:
    """정밀화 파라미터가 하나라도 있으면 dict로, 없으면 None 반환."""
    appliances_data = [a.model_dump() for a in self.appliances] if self.appliances else None
    if any([self.budget_10k_won, self.family_type, self.style_keywords, self.keep_appliances, appliances_data, self.user_text]):
      return {
        'budget_10k_won': self.budget_10k_won,
        'family_type': self.family_type,
        'style_keywords': self.style_keywords,
        'keep_appliances': self.keep_appliances,
        'appliances': appliances_data,
        'user_text': self.user_text,
      }
    return None


class ProductOut(BaseModel):
  naver_product_id: str | None = None
  name: str
  category: str | None = None
  slot: str | None = None          # 가구 슬롯 (소파/조명/러그 등). Phase 2 이전은 None
  price_min: int
  price_max: int
  image_url: str | None = None
  purchase_url: str | None = None
  match_score: float | None = None         # Vision 재랭킹 점수 (0~1). 미사용 시 None
  match_reasons: list[str] | None = None  # 일치 이유 ("색상 일치", "구조/재질 일치" 등)
  source: str | None = None               # 상품 출처 ('naver' | 'ikea')


class RoomResultOut(BaseModel):
  room_id: UUID
  room_type: str
  rationale: str
  area_sqm: float | None = None      # Claude Vision 추출 면적 (㎡). 미인식 시 None
  render_url: str | None = None      # GCS public URL. 렌더링 실패 시 None
  products: list[ProductOut] = []
  visual_attributes: dict | None = None  # Vision 추출 시각 속성 (슬롯별 색상·구조)


class RenderResponse(BaseModel):
  result_id: UUID
  selected_tone: ToneCandidateOut
  svg_layout: str                 # SVG 문자열 (응답 전용, DB 미저장)
  room_results: list[RoomResultOut]
  processing_ms: int
  disclaimer: str = (
    'AI가 생성한 이미지이며 실제 시공 결과와 다를 수 있습니다. '
    '가격·재고는 검색 시점 기준이며 실시간 반영이 아닐 수 있습니다.'
  )


# ── /share 요청·응답 모델 (F008 공유 링크) ─────────────────

class ShareCreateRequest(BaseModel):
  result_id: UUID


class ShareCreateResponse(BaseModel):
  share_id: UUID


# ── /history 응답 모델 (F011 분석 기록 조회) ───────────────

class HistoryResultItem(BaseModel):
  """기록 세션에 중첩되는 렌더링 결과 1건."""
  result_id: UUID
  tone_name: str
  created_at: str  # ISO8601 문자열 (Supabase timestamptz)


class HistorySessionItem(BaseModel):
  session_id: UUID
  created_at: str
  floor_area_pyeong: float
  status: str                      # 'analyzing' | 'completed' | 'failed'
  room_summary: str                # 예: '거실·주방·안방'
  thumbnail_url: str | None = None  # 도면 Signed URL (15분 TTL, 본인 세션만 — RISK-02 준수)
  results: list[HistoryResultItem] = []  # 최근순 렌더 결과


class HistoryResponse(BaseModel):
  sessions: list[HistorySessionItem]


# ── /health 응답 ───────────────────────────────────────────

class HealthResponse(BaseModel):
  status: str = 'ok'
  environment: str
