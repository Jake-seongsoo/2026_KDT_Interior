import { test, expect } from '@playwright/test'
import type { RenderResponse } from '../../frontend/types/api'

// 결과 페이지 테스트 — sessionStorage에 렌더 결과를 직접 주입
const MOCK_RENDER: RenderResponse = {
  result_id: 'result-abc-123',
  selected_tone: {
    id: 'tone-1',
    tone_index: 1,
    name: '호텔라이크',
    category: 'luxury',
    description: '차분한 뉴트럴 팔레트와 간접조명 중심',
    reason: '거실이 넓어 고급스러운 무드가 잘 맞습니다.',
    color_palette: [
      { name: '웜 화이트', hex: '#F7F3EA', role: '벽' },
      { name: '딥 그레이', hex: '#4A4A4A', role: '가구' },
    ],
    keywords: ['호텔라이크', '뉴트럴', '간접조명'],
  },
  svg_layout: '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400"><rect width="600" height="400" fill="#FAF7F2"/><text x="300" y="200" text-anchor="middle">거실</text></svg>',
  room_results: [
    {
      room_id: 'room-1',
      room_type: '거실',
      rationale: '거실에 호텔라이크 톤을 적용했습니다. 넓은 공간에 뉴트럴 컬러가 잘 어울립니다.',
      render_url: 'https://storage.googleapis.com/test-bucket/renders/result-abc-123/livingroom.jpg',
      products: [
        {
          name: '호텔라이크 3인 소파',
          price_min: 480000,
          price_max: 520000,
          image_url: 'https://shopping-phinf.pstatic.net/test.jpg',
          purchase_url: 'https://example.com',
        },
      ],
    },
    {
      room_id: 'room-2',
      room_type: '주방',
      rationale: '주방에 호텔라이크 톤을 적용했습니다.',
      render_url: null,  // 렌더링 실패 케이스
      products: [],
    },
  ],
  processing_ms: 35000,
  disclaimer: 'AI가 생성한 이미지이며 실제 시공 결과와 다를 수 있습니다.',
}

test.describe('결과 페이지 E2E', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    await page.evaluate((data) => {
      sessionStorage.setItem(`render:${data.result_id}`, JSON.stringify(data))
    }, MOCK_RENDER)
  })

  test('선택 톤 이름 표시', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    await expect(page.locator('h1:has-text("호텔라이크")')).toBeVisible()
  })

  test('2D 배치도 표시', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    await expect(page.getByText('2D 공간 배치도')).toBeVisible()
  })

  test('방 탭 개수 확인', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    // 거실, 주방 탭이 있어야 함 (room-tab으로 배치도 셀과 구분)
    const tabs = page.getByTestId('room-tab')
    await expect(tabs).toHaveCount(2)
    await expect(tabs.filter({ hasText: '거실' })).toBeVisible()
    await expect(tabs.filter({ hasText: '주방' })).toBeVisible()
  })

  test('AI 생성 이미지 고지 표시 (RISK-08)', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    await expect(page.locator('text=AI 생성 이미지').first()).toBeVisible()
  })

  test('render_url이 null인 방도 에러 없이 표시', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    // 주방 탭 클릭
    await page.getByTestId('room-tab').filter({ hasText: '주방' }).click()
    await expect(page.locator('text=이미지 생성 실패').first()).toBeVisible()
  })

  test('면책 문구 표시', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    await expect(page.locator('text=AI가 생성한 이미지')).toBeVisible()
  })

  test('추천 상품 합계(예산 신호) 표시 + 공사비 제외 고지', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    const budget = page.getByTestId('budget-summary')
    await expect(budget).toBeVisible()
    await expect(budget).toContainText('추천 상품 합계')
    await expect(budget).toContainText('480,000원')
    await expect(budget).toContainText('시공·공사비는 포함하지 않습니다')
  })

  test('공유하기 버튼이 1순위(primary)로 노출', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    const share = page.getByTestId('share-button')
    await expect(share).toBeVisible()
    await expect(share).toHaveText(/공유하기/)
  })

  test('홈으로 버튼이 / 로 이동', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    await page.getByRole('link', { name: '홈으로', exact: true }).click()
    await expect(page).toHaveURL('/')
  })

  test('render_session 키가 있을 때 다른 톤 버튼이 /tones/{sessionId}로 이동', async ({ page }) => {
    await page.goto('/')
    await page.evaluate((data) => {
      sessionStorage.setItem(`render:${data.result_id}`, JSON.stringify(data))
      sessionStorage.setItem(`render_session:${data.result_id}`, 'session-xyz')
    }, MOCK_RENDER)
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    await page.getByRole('link', { name: /다른 톤/ }).click()
    await expect(page).toHaveURL('/tones/session-xyz')
  })

  test('render_session 키가 없으면 다른 톤 버튼은 표시되지 않음', async ({ page }) => {
    await page.goto(`/result/${MOCK_RENDER.result_id}`)
    await expect(page.getByRole('link', { name: /다른 톤/ })).toHaveCount(0)
  })
})
