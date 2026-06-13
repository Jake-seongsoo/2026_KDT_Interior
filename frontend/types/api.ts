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
  has_reference?: boolean
}

export interface Appliance {
  name: string  // 한국어 가전명 (냉장고, 세탁기 등)
  room: string  // 배치할 방 유형 (주방, 다용도실 등)
}

export interface RenderRequest {
  session_id: string
  selected_tone_id: string
  budget_10k_won?: number | null
  family_type?: string | null       // 'single' | 'couple' | 'family_with_kid' | 'family_with_pet'
  style_keywords?: string[] | null  // 무드 칩 선택 결과
  keep_appliances?: boolean | null
  appliances?: Appliance[] | null   // 사용자 지정 가전 배치 목록
  user_text?: string | null         // 사용자 자유 입력 텍스트
}

export interface RefinementParams {
  budget_10k_won?: number | null
  family_type?: string | null
  style_keywords?: string[] | null
  keep_appliances?: boolean | null
  appliances?: Appliance[] | null
  user_text?: string | null
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

// ── 분석 기록 조회 (F011) ──────────────────────────────────

export interface HistoryResultItem {
  result_id: string
  tone_name: string
  created_at: string  // ISO8601
}

export interface HistorySessionItem {
  session_id: string
  created_at: string
  floor_area_pyeong: number
  status: string                     // 'analyzing' | 'completed' | 'failed'
  room_summary: string               // 예: '거실·주방·안방'
  thumbnail_url?: string | null      // 도면 Signed URL (15분 TTL)
  results: HistoryResultItem[]       // 최근순 렌더 결과
}

export interface HistoryResponse {
  sessions: HistorySessionItem[]
}
