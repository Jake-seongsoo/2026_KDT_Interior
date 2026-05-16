# RISK-03: 모든 비용 발생 엔드포인트에 verify_jwt Depends 적용 필수
import time
from typing import Any

import httpx
from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from pydantic import BaseModel

from core.config import get_settings

_JWKS_CACHE_TTL_SECONDS = 60 * 60
_jwks_cache: dict[str, Any] = {
  'expires_at': 0.0,
  'keys': [],
}


class AuthUser(BaseModel):
  user_id: str
  email: str | None = None


async def _fetch_supabase_jwks(force_refresh: bool = False) -> list[dict[str, Any]]:
  settings = get_settings()
  if not settings.SUPABASE_URL:
    raise JWTError('SUPABASE_URL is required for ES256 JWT verification')

  now = time.monotonic()
  if not force_refresh and _jwks_cache['keys'] and _jwks_cache['expires_at'] > now:
    return _jwks_cache['keys']

  jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
  try:
    async with httpx.AsyncClient(timeout=5.0) as client:
      response = await client.get(jwks_url)
      response.raise_for_status()
      data = response.json()
  except httpx.HTTPError as e:
    raise JWTError(f'Failed to fetch Supabase JWKS: {e}') from e

  keys = data.get('keys')
  if not isinstance(keys, list) or not keys:
    raise JWTError('Supabase JWKS does not contain signing keys')

  _jwks_cache['keys'] = keys
  _jwks_cache['expires_at'] = now + _JWKS_CACHE_TTL_SECONDS
  return keys


async def _get_verification_key(token: str) -> tuple[Any, list[str]]:
  settings = get_settings()
  header = jwt.get_unverified_header(token)
  alg = header.get('alg')

  if alg == 'HS256':
    if not settings.SUPABASE_JWT_SECRET:
      raise JWTError('SUPABASE_JWT_SECRET is required for HS256 JWT verification')
    return settings.SUPABASE_JWT_SECRET, ['HS256']

  if alg != 'ES256':
    raise JWTError(f'The specified alg value is not allowed: {alg}')

  kid = header.get('kid')
  if not kid:
    raise JWTError('ES256 JWT is missing kid header')

  keys = await _fetch_supabase_jwks()
  key = next((candidate for candidate in keys if candidate.get('kid') == kid), None)

  if key is None:
    keys = await _fetch_supabase_jwks(force_refresh=True)
    key = next((candidate for candidate in keys if candidate.get('kid') == kid), None)

  if key is None:
    raise JWTError('No matching Supabase JWKS key found for token kid')

  return key, ['ES256']


async def verify_jwt(authorization: str = Header(None)) -> AuthUser:
  """Supabase JWT를 검증하고 사용자 정보를 반환한다."""
  if not authorization or not authorization.startswith('Bearer '):
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail='Authorization 헤더가 없거나 형식이 잘못되었습니다.',
    )

  token = authorization.removeprefix('Bearer ').strip()

  try:
    key, algorithms = await _get_verification_key(token)
    payload = jwt.decode(
      token,
      key,
      algorithms=algorithms,
      audience='authenticated',
    )
  except JWTError as e:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail=f'유효하지 않은 토큰입니다: {e}',
    ) from e

  user_id = payload.get('sub')
  if not user_id:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail='토큰에 사용자 ID가 없습니다.',
    )

  return AuthUser(user_id=user_id, email=payload.get('email'))
