import { createClient } from '@/lib/supabase/client'
import type {
  AnalyzeResponse,
  HistoryResponse,
  RenderRequest,
  RenderResponse,
  RoomCorrection,
  ShareCreateResponse,
} from '@/types/api'

const BASE = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export class AuthRequiredError extends Error {
  constructor() {
    super('로그인이 필요합니다.')
    this.name = 'AuthRequiredError'
  }
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const sb = createClient()
  const { data } = await sb.auth.getSession()
  if (!data.session) {
    throw new AuthRequiredError()
  }
  return { Authorization: `Bearer ${data.session.access_token}` }
}

export async function postAnalyze(
  file: File,
  floorAreaPyeong: number,
  referenceFile?: File,
): Promise<AnalyzeResponse> {
  const headers = await getAuthHeaders()
  const fd = new FormData()
  fd.append('file', file)
  fd.append('floor_area_pyeong', String(floorAreaPyeong))
  if (referenceFile) fd.append('reference', referenceFile)

  const res = await fetch(`${BASE}/analyze`, {
    method: 'POST',
    headers,
    body: fd,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '분석 요청에 실패했습니다.')
  }

  return res.json()
}

export async function postAnalyzeCustom(
  file: File,
  floorAreaPyeong: number,
  userText: string,
  moodChips: string[],
  referenceFile?: File,
): Promise<AnalyzeResponse> {
  const headers = await getAuthHeaders()
  const fd = new FormData()
  fd.append('file', file)
  fd.append('floor_area_pyeong', String(floorAreaPyeong))
  fd.append('user_text', userText)
  fd.append('mood_chips', JSON.stringify(moodChips))
  if (referenceFile) fd.append('reference', referenceFile)

  const res = await fetch(`${BASE}/analyze/custom`, {
    method: 'POST',
    headers,
    body: fd,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '분석 요청에 실패했습니다.')
  }

  return res.json()
}

export async function postRender(body: RenderRequest): Promise<RenderResponse> {
  const headers = await getAuthHeaders()

  const res = await fetch(`${BASE}/render`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify(body),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '렌더링 요청에 실패했습니다.')
  }

  return res.json()
}

/** 방 이름을 수정한다 (F003 — 본인 세션만). 수정 반영된 AnalyzeResponse를 반환한다. */
export async function patchRooms(
  sessionId: string,
  rooms: RoomCorrection[],
): Promise<AnalyzeResponse> {
  const headers = await getAuthHeaders()

  const res = await fetch(`${BASE}/analyze/${sessionId}/rooms`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify({ rooms }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '방 정보 수정에 실패했습니다.')
  }

  return res.json()
}

export async function getAnalyzeResult(sessionId: string): Promise<AnalyzeResponse> {
  const headers = await getAuthHeaders()

  const res = await fetch(`${BASE}/analyze/${sessionId}`, { headers })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '분석 결과를 불러오지 못했습니다.')
  }

  return res.json()
}

export async function getRenderResult(resultId: string): Promise<RenderResponse> {
  const headers = await getAuthHeaders()

  const res = await fetch(`${BASE}/results/${resultId}`, { headers })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '렌더링 결과를 불러오지 못했습니다.')
  }

  return res.json()
}

export async function getSessionHistory(): Promise<HistoryResponse> {
  const headers = await getAuthHeaders()

  const res = await fetch(`${BASE}/history`, { headers })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '분석 기록을 불러오지 못했습니다.')
  }

  return res.json()
}

/** 결과의 공유 링크를 생성한다 (본인 결과만 — 로그인 필요). */
export async function createShareLink(resultId: string): Promise<ShareCreateResponse> {
  const headers = await getAuthHeaders()

  const res = await fetch(`${BASE}/share`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...headers },
    body: JSON.stringify({ result_id: resultId }),
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '공유 링크 생성에 실패했습니다.')
  }

  return res.json()
}

/** 공유 링크로 결과를 조회한다 (비로그인 — SSR 서버 컴포넌트에서 호출).
 *  no-store로 매 요청 최신 조회(조회수 증가 반영), 인증 헤더 없음. */
export async function getSharedResult(shareId: string): Promise<RenderResponse> {
  const res = await fetch(`${BASE}/share/${shareId}`, { cache: 'no-store' })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail ?? '공유된 결과를 불러오지 못했습니다.')
  }

  return res.json()
}
