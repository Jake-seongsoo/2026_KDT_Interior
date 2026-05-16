import { test, expect } from '@playwright/test'
import { issueTestJwt, TEST_USER_ID } from '../fixtures/auth'
import { savedSessionId, savedToneId } from './analyze.api.spec'

test.describe.serial('POST /render', () => {
  test('소유자가 아닌 사용자 → 403', async ({ request }) => {
    // analyze에서 저장한 세션이 없으면 스킵
    if (!savedSessionId || !savedToneId) {
      test.skip(true, 'analyze 테스트 결과가 없습니다. analyze.api.spec.ts를 먼저 실행해주세요.')
    }

    // 다른 user_id로 JWT 발급
    const otherJwt = issueTestJwt('99999999-9999-9999-9999-999999999999')

    const res = await request.post('/render', {
      headers: {
        Authorization: `Bearer ${otherJwt}`,
        'Content-Type': 'application/json',
      },
      data: {
        session_id: savedSessionId,
        selected_tone_id: savedToneId,
      },
    })

    expect(res.status()).toBe(403)
  })

  test('정상 렌더링 → 200 + 방별 결과', async ({ request }) => {
    test.setTimeout(120_000) // Imagen + Naver 병렬 호출 허용 시간

    if (!savedSessionId || !savedToneId) {
      test.skip(true, 'analyze 테스트 결과가 없습니다. analyze.api.spec.ts를 먼저 실행해주세요.')
    }

    const jwt = issueTestJwt(TEST_USER_ID)

    const res = await request.post('/render', {
      headers: {
        Authorization: `Bearer ${jwt}`,
        'Content-Type': 'application/json',
      },
      data: {
        session_id: savedSessionId,
        selected_tone_id: savedToneId,
      },
    })

    expect(res.status()).toBe(200)

    const body = await res.json()
    expect(body.result_id).toBeTruthy()
    expect(body.svg_layout).toContain('<svg')
    expect(Array.isArray(body.room_results)).toBe(true)
    expect(body.room_results.length).toBeGreaterThanOrEqual(1)
    expect(body.processing_ms).toBeGreaterThan(0)

    // 성공한 방의 render_url은 GCS public URL 형식이어야 함
    const successRoom = body.room_results.find((r: { render_url?: string }) => r.render_url)
    if (successRoom) {
      expect(successRoom.render_url).toMatch(/^https:\/\/storage\.googleapis\.com\//)
    }

    // disclaimer 포함 확인
    expect(body.disclaimer).toBeTruthy()
  })
})
