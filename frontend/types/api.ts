// 백엔드 Pydantic 모델과 1:1 대응하는 TypeScript 타입

export interface ColorChip {
  name: string
  hex: string
  role?: string | null
}

export interface RoomOut {
  id: string
  room_type: string
  confidence: number
  priority: number
  area_sqm?: number | null
}

export interface ToneCandidateOut {
  id: string
  tone_index: number
  name: string
  category: string
  description: string
  reason: string
  color_palette: ColorChip[]
  keywords: string[]
}

export interface AnalyzeResponse {
  session_id: string
  rooms: RoomOut[]
  tone_candidates: ToneCandidateOut[]
  warnings: string[]
}

export interface RenderRequest {
  session_id: string
  selected_tone_id: string
  budget_10k_won?: number | null
}

export interface ProductOut {
  naver_product_id?: string | null
  name: string
  category?: string | null
  slot?: string | null              // 가구 슬롯 (소파/조명/러그 등). Phase 2 이전은 null
  price_min: number
  price_max: number
  image_url?: string | null
  purchase_url?: string | null
  match_score?: number | null       // Vision 재랭킹 점수 (0~1). 미사용 시 null
  match_reasons?: string[] | null   // 일치 이유 ("색상 일치", "구조/재질 일치" 등)
}

export interface RoomResultOut {
  room_id: string
  room_type: string
  rationale: string
  render_url?: string | null
  products: ProductOut[]
  visual_attributes?: Record<string, unknown> | null  // Vision 추출 시각 속성 (슬롯별 색상·구조)
}

export interface RenderResponse {
  result_id: string
  selected_tone: ToneCandidateOut
  svg_layout: string
  room_results: RoomResultOut[]
  processing_ms: number
  disclaimer: string
}

export interface HealthResponse {
  status: string
  environment: string
}
