import * as jwt from 'jsonwebtoken'

const SECRET = process.env.SUPABASE_JWT_SECRET ?? ''
const TEST_USER_ID = '00000000-0000-0000-0000-000000000001'

/**
 * Supabase JWT Secret으로 서명한 테스트용 JWT를 발급한다.
 * 실제 Supabase와 동일한 HS256 + audience='authenticated' 형식.
 */
export function issueTestJwt(userId: string = TEST_USER_ID): string {
  if (!SECRET) {
    throw new Error(
      'SUPABASE_JWT_SECRET 환경변수가 설정되지 않았습니다. .env를 확인해주세요.',
    )
  }
  return jwt.sign(
    {
      sub: userId,
      aud: 'authenticated',
      role: 'authenticated',
      email: 'test@example.com',
      exp: Math.floor(Date.now() / 1000) + 3600,
    },
    SECRET,
    { algorithm: 'HS256' },
  )
}

export { TEST_USER_ID }
