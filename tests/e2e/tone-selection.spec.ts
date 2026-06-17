import { test, expect } from '@playwright/test'
import type { AnalyzeResponse } from '../../frontend/types/api'

// 톤 선택 페이지 테스트 — sessionStorage에 분석 결과를 직접 주입해 E2E 비용 절감
const MOCK_ANALYZE: AnalyzeResponse = {
  session_id: 'test-session-111',
  rooms: [
    { id: 'room-1', room_type: '거실', confidence: 0.92, priority: 1, area_sqm: 20.5 },
    { id: 'room-2', room_type: '주방', confidence: 0.85, priority: 2, area_sqm: 9.0 },
  ],
  tone_candidates: Array.from({ length: 6 }, (_, i) => ({
    id: `tone-${i + 1}`,
    tone_index: i + 1,
    name: ['호텔라이크', '재팬디', '모던미니멀', '내추럴우드', '보헤미안', '포인트컬러'][i],
    category: ['luxury', 'natural', 'minimal', 'natural', 'trendy', 'color'][i],
    description: '예시 설명',
    reason: '이 도면에 잘 맞습니다.',
    color_palette: [{ name: '화이트', hex: '#FFFFFF' }],
    keywords: ['소파', '조명'],
  })),
  warnings: [],
}

test.describe('톤 선택 페이지 E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate((data) => {
      sessionStorage.setItem(`analyze:${data.session_id}`, JSON.stringify(data))
    }, MOCK_ANALYZE)
  })

  test('톤 카드 6개 표시', async ({ page }) => {
    await page.goto(`/tones/${MOCK_ANALYZE.session_id}`)
    const toneCards = page.getByTestId('tone-card')
    await expect(toneCards).toHaveCount(6)
  })

  test('톤 미선택 시 시안 만들기 버튼 비활성', async ({ page }) => {
    await page.goto(`/tones/${MOCK_ANALYZE.session_id}`)
    const btn = page.locator('button:has-text("톤을 선택해 주세요")')
    await expect(btn).toBeDisabled()
  })

  test('톤 선택 시 버튼 활성화 + 선택 표시', async ({ page }) => {
    await page.goto(`/tones/${MOCK_ANALYZE.session_id}`)
    // 첫 번째 톤 카드 클릭
    await page.getByTestId('tone-card').first().click()
    // 선택됨 표시
    await expect(page.locator('text=선택됨')).toBeVisible()
    // 버튼 활성화
    const btn = page.locator('button:has-text("제안 만들기")')
    await expect(btn).toBeEnabled()
  })

  test('방 정보 카드에 방 개수 표시', async ({ page }) => {
    await page.goto(`/tones/${MOCK_ANALYZE.session_id}`)
    await expect(page.locator('text=2개')).toBeVisible()
  })

  test('방 이름 인라인 편집 UI 진입·취소 (F003)', async ({ page }) => {
    await page.goto(`/tones/${MOCK_ANALYZE.session_id}`)
    await page.getByTestId('rooms-edit').click()
    const input = page.getByLabel('1번 방 이름')
    await expect(input).toBeVisible()
    await expect(input).toHaveValue('거실')
    await input.fill('서재')
    // 취소하면 편집 모드 종료 + 수정 버튼 복귀
    await page.getByRole('button', { name: '수정 취소' }).click()
    await expect(page.getByTestId('rooms-edit')).toBeVisible()
  })
})
