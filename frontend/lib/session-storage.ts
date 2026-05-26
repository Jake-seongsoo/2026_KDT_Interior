import type { AnalyzeResponse, RefinementParams, RenderResponse, ToneCandidateOut } from '@/types/api'

export type ToneMode = 'auto' | 'custom'

export interface CustomInput {
  userText: string
  moodChips: string[]
}

const KEYS = {
  uploadBase64: 'upload:file:base64',
  uploadName: 'upload:file:name',
  uploadType: 'upload:file:type',
  uploadFloorArea: 'upload:floorArea',
  referenceBase64: 'upload:reference:base64',
  referenceName: 'upload:reference:name',
  referenceType: 'upload:reference:type',
  mode: 'tone:mode',
  customInput: 'tone:custom_input',
  analyze: (sessionId: string) => `analyze:${sessionId}`,
  tone: (sessionId: string) => `tone:${sessionId}`,
  refinement: (sessionId: string) => `refinement:${sessionId}`,
  renderResult: (resultId: string) => `render:${resultId}`,
  renderSession: (resultId: string) => `render_session:${resultId}`,
} as const

export const uploadStorage = {
  save(base64: string, name: string, type: string, floorArea: number) {
    sessionStorage.setItem(KEYS.uploadBase64, base64)
    sessionStorage.setItem(KEYS.uploadName, name)
    sessionStorage.setItem(KEYS.uploadType, type)
    sessionStorage.setItem(KEYS.uploadFloorArea, String(floorArea))
  },
  load() {
    return {
      base64: sessionStorage.getItem(KEYS.uploadBase64),
      name: sessionStorage.getItem(KEYS.uploadName) ?? 'floorplan.jpg',
      type: sessionStorage.getItem(KEYS.uploadType) ?? 'image/jpeg',
      floorArea: Number(sessionStorage.getItem(KEYS.uploadFloorArea) ?? '30'),
    }
  },
  clear() {
    sessionStorage.removeItem(KEYS.uploadBase64)
    sessionStorage.removeItem(KEYS.uploadName)
    sessionStorage.removeItem(KEYS.uploadType)
    sessionStorage.removeItem(KEYS.uploadFloorArea)
  },
}

export const referenceStorage = {
  save(base64: string, name: string, type: string) {
    sessionStorage.setItem(KEYS.referenceBase64, base64)
    sessionStorage.setItem(KEYS.referenceName, name)
    sessionStorage.setItem(KEYS.referenceType, type)
  },
  load(): { base64: string; name: string; type: string } | null {
    const base64 = sessionStorage.getItem(KEYS.referenceBase64)
    if (!base64) return null
    return {
      base64,
      name: sessionStorage.getItem(KEYS.referenceName) ?? 'reference.jpg',
      type: sessionStorage.getItem(KEYS.referenceType) ?? 'image/jpeg',
    }
  },
  clear() {
    sessionStorage.removeItem(KEYS.referenceBase64)
    sessionStorage.removeItem(KEYS.referenceName)
    sessionStorage.removeItem(KEYS.referenceType)
  },
}

export const modeStorage = {
  set(mode: ToneMode) {
    sessionStorage.setItem(KEYS.mode, mode)
  },
  get(): ToneMode {
    return (sessionStorage.getItem(KEYS.mode) as ToneMode) ?? 'auto'
  },
  clear() {
    sessionStorage.removeItem(KEYS.mode)
  },
}

export const customInputStorage = {
  set(input: CustomInput) {
    sessionStorage.setItem(KEYS.customInput, JSON.stringify(input))
  },
  get(): CustomInput | null {
    const raw = sessionStorage.getItem(KEYS.customInput)
    return raw ? (JSON.parse(raw) as CustomInput) : null
  },
  clear() {
    sessionStorage.removeItem(KEYS.customInput)
  },
}

export const analyzeStorage = {
  save(sessionId: string, result: AnalyzeResponse) {
    sessionStorage.setItem(KEYS.analyze(sessionId), JSON.stringify(result))
  },
  load(sessionId: string): AnalyzeResponse | null {
    const raw = sessionStorage.getItem(KEYS.analyze(sessionId))
    return raw ? (JSON.parse(raw) as AnalyzeResponse) : null
  },
}

export const toneStorage = {
  save(sessionId: string, tone: ToneCandidateOut) {
    sessionStorage.setItem(KEYS.tone(sessionId), JSON.stringify(tone))
  },
  load(sessionId: string): ToneCandidateOut | null {
    const raw = sessionStorage.getItem(KEYS.tone(sessionId))
    return raw ? (JSON.parse(raw) as ToneCandidateOut) : null
  },
  clear(sessionId: string) {
    sessionStorage.removeItem(KEYS.tone(sessionId))
  },
}

export const refinementStorage = {
  save(sessionId: string, params: RefinementParams) {
    sessionStorage.setItem(KEYS.refinement(sessionId), JSON.stringify(params))
  },
  load(sessionId: string): RefinementParams | null {
    const raw = sessionStorage.getItem(KEYS.refinement(sessionId))
    return raw ? (JSON.parse(raw) as RefinementParams) : null
  },
  clear(sessionId: string) {
    sessionStorage.removeItem(KEYS.refinement(sessionId))
  },
}

export const renderStorage = {
  save(resultId: string, sessionId: string, result: RenderResponse) {
    sessionStorage.setItem(KEYS.renderResult(resultId), JSON.stringify(result))
    sessionStorage.setItem(KEYS.renderSession(resultId), sessionId)
  },
  loadResult(resultId: string): RenderResponse | null {
    const raw = sessionStorage.getItem(KEYS.renderResult(resultId))
    return raw ? (JSON.parse(raw) as RenderResponse) : null
  },
  loadSessionId(resultId: string): string | null {
    return sessionStorage.getItem(KEYS.renderSession(resultId))
  },
}
