import { test, expect } from '@playwright/test'

test.describe('GET /health', () => {
  test('인증 없이 200 반환', async ({ request }) => {
    const res = await request.get('/health')
    expect(res.status()).toBe(200)
  })

  test('응답에 status:ok 포함', async ({ request }) => {
    const res = await request.get('/health')
    const body = await res.json()
    expect(body.status).toBe('ok')
    expect(body.environment).toBeTruthy()
  })
})
