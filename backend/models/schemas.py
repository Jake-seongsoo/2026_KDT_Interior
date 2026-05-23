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
  # 도면 URL은 절대 포함하지 않는다 (RISK-02)


# ── /render 요청·응답 모델 ─────────────────────────────────

class RenderRequest(BaseModel):
  session_id: UUID
  selected_tone_id: UUID
  budget_10k_won: int | None = None


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


# ── /health 응답 ───────────────────────────────────────────

class HealthResponse(BaseModel):
  status: str = 'ok'
  environment: str
