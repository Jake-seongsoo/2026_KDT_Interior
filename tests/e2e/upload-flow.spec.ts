import { test, expect } from '@playwright/test'
import * as path from 'path'
import * as fs from 'fs'

const SAMPLE_PATH = path.resolve(__dirname, '../../82type_sample.jpg')

test.describe('업로드 플로우 E2E', () => {
  test('홈 페이지 로드', async ({ page }) => {
    await page.goto('/')
    await expect(page.locator('h1')).toContainText('AI 인테리어')
  })

  test('파일 선택 시 미리보기 표시', async ({ page }) => {
    if (!fs.existsSync(SAMPLE_PATH)) {
      test.skip(true, '샘플 도면 파일이 없습니다.')
    }

    await page.goto('/')
    const input = page.locator('input[type="file"]')
    await input.setInputFiles(SAMPLE_PATH)

    // 미리보기 이미지가 표시되어야 함
    await expect(page.locator('img[alt="도면 미리보기"]')).toBeVisible()
  })

  test('파일 선택 전에는 분석 시작 버튼 비활성', async ({ page }) => {
    await page.goto('/')
    const btn = page.locator('button[type="submit"]')
    await expect(btn).toBeDisabled()
  })

  test('파일 선택 후 분석 시작 버튼 활성화', async ({ page }) => {
    if (!fs.existsSync(SAMPLE_PATH)) {
      test.skip(true, '샘플 도면 파일이 없습니다.')
    }

    await page.goto('/')
    const input = page.locator('input[type="file"]')
    await input.setInputFiles(SAMPLE_PATH)

    const btn = page.locator('button[type="submit"]')
    await expect(btn).not.toBeDisabled()
  })
})
