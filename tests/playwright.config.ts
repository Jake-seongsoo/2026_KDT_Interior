import { defineConfig, devices } from '@playwright/test'
import * as dotenv from 'dotenv'
import * as path from 'path'

// 루트 .env 로드 (SUPABASE_JWT_SECRET 등)
dotenv.config({ path: path.resolve(__dirname, '../.env') })

export default defineConfig({
  testDir: '.',
  fullyParallel: false,  // 외부 API 비용 절감을 위해 직렬 실행
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { open: 'never', outputFolder: 'playwright-report' }],
  ],
  use: {
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'backend-api',
      testMatch: /backend\/.*\.api\.spec\.ts/,
      use: {
        baseURL: process.env.BACKEND_URL ?? 'http://localhost:8000',
      },
    },
    {
      name: 'e2e-chromium',
      testMatch: /e2e\/.*\.spec\.ts/,
      use: {
        ...devices['Desktop Chrome'],
        baseURL: process.env.FRONTEND_URL ?? 'http://localhost:3000',
      },
    },
  ],
})
