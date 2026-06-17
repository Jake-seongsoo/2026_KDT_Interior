import * as fs from 'fs'
import * as path from 'path'
import jwt from 'jsonwebtoken'
import type { BrowserContext } from '@playwright/test'

/**
 * E2E 전용 Supabase 로그인 헬퍼.
 *
 * 프론트는 @supabase/ssr(쿠키 기반 세션)을 사용하므로, 백엔드와 동일한
 * SUPABASE_JWT_SECRET으로 access_token을 만들어 `sb-<ref>-auth-token` 쿠키를
 * 주입하면 getSession()이 로그인 상태로 인식한다. (서버 통신 없음)
 */

const TEST_USER_ID = '00000000-0000-0000-0000-000000000001'

// playwright.config는 루트 .env만 로드하므로 URL은 frontend/.env.local에서 직접 읽는다.
function readSupabaseUrl(): string | null {
  if (process.env.NEXT_PUBLIC_SUPABASE_URL) return process.env.NEXT_PUBLIC_SUPABASE_URL
  const envPath = path.resolve(__dirname, '../../frontend/.env.local')
  if (!fs.existsSync(envPath)) return null
  const m = fs.readFileSync(envPath, 'utf-8').match(/^NEXT_PUBLIC_SUPABASE_URL=(.+)$/m)
  return m ? m[1].trim().replace(/['"]/g, '') : null
}

/** 인증 쿠키 주입에 필요한 env가 모두 있는지 — 없으면 테스트를 skip한다. */
export function supabaseAuthAvailable(): boolean {
  return Boolean(process.env.SUPABASE_JWT_SECRET && readSupabaseUrl())
}

/** 브라우저 컨텍스트에 로그인 세션 쿠키를 주입한다. navigate 이전에 호출해야 한다. */
export async function loginAs(context: BrowserContext, userId: string = TEST_USER_ID): Promise<void> {
  const secret = process.env.SUPABASE_JWT_SECRET
  const url = readSupabaseUrl()
  if (!secret || !url) throw new Error('Supabase E2E 인증 env가 없습니다.')

  const ref = new URL(url).hostname.split('.')[0]
  const expSec = Math.floor(Date.now() / 1000) + 60 * 60
  const accessToken = jwt.sign(
    { sub: userId, aud: 'authenticated', role: 'authenticated', email: 'e2e@test.dev' },
    secret,
    { algorithm: 'HS256', expiresIn: '1h' },
  )
  const session = {
    access_token: accessToken,
    token_type: 'bearer',
    expires_in: 3600,
    expires_at: expSec,
    refresh_token: 'e2e-refresh-token',
    user: { id: userId, aud: 'authenticated', role: 'authenticated', email: 'e2e@test.dev' },
  }
  // @supabase/ssr(>=0.5) 쿠키 인코딩: 'base64-' 접두 + base64(JSON)
  const value = `base64-${Buffer.from(JSON.stringify(session)).toString('base64')}`

  await context.addCookies([
    {
      name: `sb-${ref}-auth-token`,
      value,
      domain: 'localhost',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax',
      expires: expSec,
    },
  ])
}
