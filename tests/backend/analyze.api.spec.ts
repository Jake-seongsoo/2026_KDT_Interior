import { test, expect } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'
import { issueTestJwt } from '../fixtures/auth'

const SAMPLE_PATH = path.resolve(__dirname, '../../82type_sample.jpg')

// 분석 결과를 이후 render 테스트에서 재사용하기 위해 모듈 스코프 변수에 저장
export let savedSessionId: string | null = null
export let savedToneId: string | null = null

test.describe.serial('POST /analyze', () => {
  test('5MB 초과 파일 → 413', async ({ request }) => {
    const jwt = issueTestJwt()
    // 6MB 더미 버퍼 생성
    const largeBuffer = Buffer.alloc(6 * 1024 * 1024, 0)

    const res = await request.post('/analyze', {
      headers: { Authorization: `Bearer ${jwt}` },
      multipart: {
        file: {
          name: 'large.jpg',
          mimeType: 'image/jpeg',
          buffer: largeBuffer,
        },
        floor_area_pyeong: '30',
      },
    })
    expect(res.status()).toBe(413)
  })

  test('정상 도면 업로드 → 200 + 방·톤 반환', async ({ request }) => {
    test.setTimeout(60_000) // Claude API 호출 시간 허용

    if (!fs.existsSync(SAMPLE_PATH)) {
      test.skip(true, '82type_sample.jpg 파일이 없습니다. 루트 디렉터리에 도면 파일을 추가해주세요.')
    }

    const jwt = issueTestJwt()
    const buffer = fs.readFileSync(SAMPLE_PATH)

    const res = await request.post('/analyze', {
      headers: { Authorization: `Bearer ${jwt}` },
      multipart: {
        file: {
          name: '82type_sample.jpg',
          mimeType: 'image/jpeg',
          buffer,
        },
        floor_area_pyeong: '30',
      },
    })

    expect(res.status()).toBe(200)

    const body = await res.json()
    expect(body.session_id).toBeTruthy()
    expect(Array.isArray(body.rooms)).toBe(true)
    expect(body.rooms.length).toBeGreaterThanOrEqual(1)
    expect(Array.isArray(body.tone_candidates)).toBe(true)
    expect(body.tone_candidates.length).toBe(6)

    // 응답에 도면 URL이 포함되지 않아야 함 (RISK-02)
    const bodyText = JSON.stringify(body)
    expect(bodyText).not.toContain('storage.googleapis.com/floor-plans')
    expect(bodyText).not.toContain('signed')

    // 이후 render 테스트에서 재사용
    savedSessionId = body.session_id
    savedToneId = body.tone_candidates[0].id
  })
})
