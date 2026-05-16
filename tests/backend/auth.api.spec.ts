import { test, expect } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'

const SAMPLE_PATH = path.resolve(__dirname, '../fixtures/sample_floorplan.jpg')

test.describe('JWT 인증 — RISK-03', () => {
  test('Authorization 헤더 없이 POST /analyze → 401', async ({ request }) => {
    const sampleExists = fs.existsSync(SAMPLE_PATH)
    const buffer = sampleExists
      ? fs.readFileSync(SAMPLE_PATH)
      : Buffer.from('fake-image-data')

    const res = await request.post('/analyze', {
      multipart: {
        file: {
          name: 'test.jpg',
          mimeType: 'image/jpeg',
          buffer,
        },
        floor_area_pyeong: '30',
      },
    })
    expect(res.status()).toBe(401)
  })

  test('잘못된 토큰으로 POST /analyze → 401', async ({ request }) => {
    const sampleExists = fs.existsSync(SAMPLE_PATH)
    const buffer = sampleExists
      ? fs.readFileSync(SAMPLE_PATH)
      : Buffer.from('fake-image-data')

    const res = await request.post('/analyze', {
      headers: { Authorization: 'Bearer this-is-not-a-valid-jwt' },
      multipart: {
        file: {
          name: 'test.jpg',
          mimeType: 'image/jpeg',
          buffer,
        },
        floor_area_pyeong: '30',
      },
    })
    expect(res.status()).toBe(401)
  })

  test('Authorization 헤더 없이 POST /render → 401', async ({ request }) => {
    const res = await request.post('/render', {
      data: {
        session_id: '00000000-0000-0000-0000-000000000000',
        selected_tone_id: '00000000-0000-0000-0000-000000000000',
      },
    })
    expect(res.status()).toBe(401)
  })
})
