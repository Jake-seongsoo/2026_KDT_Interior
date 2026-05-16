from functools import lru_cache
from pathlib import Path

from google.oauth2 import service_account
from google.oauth2.service_account import Credentials
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
  model_config = SettingsConfigDict(
    env_file=ROOT_DIR / '.env',
    env_file_encoding='utf-8',
    case_sensitive=True,
    extra='ignore',
    populate_by_name=True,
  )

  environment: str = Field(default='development', validation_alias='ENVIRONMENT')

  # Anthropic Claude
  ANTHROPIC_API_KEY: str = ''
  CLAUDE_MODEL: str = 'claude-sonnet-4-6'

  # GCP
  GCP_PROJECT_ID: str = ''
  GCP_REGION: str = 'asia-northeast3'
  GCS_BUCKET_NAME: str = ''
  GCS_RENDER_BUCKET_NAME: str = ''
  GOOGLE_APPLICATION_CREDENTIALS: str = str(ROOT_DIR / 'backend' / 'service-account.json')
  IMAGEN_MODEL: str = 'imagen-4.0-generate-001'

  # Supabase
  SUPABASE_URL: str = ''
  SUPABASE_ANON_KEY: str = ''
  SUPABASE_SERVICE_ROLE_KEY: str = ''
  SUPABASE_JWT_SECRET: str = ''

  # 네이버 쇼핑
  NAVER_CLIENT_ID: str = ''
  NAVER_CLIENT_SECRET: str = ''

  # CORS (쉼표 구분)
  CORS_ORIGINS: str = 'http://localhost:3000,http://127.0.0.1:3000'

  # 운영 설정
  SIGNED_URL_TTL_MINUTES: int = 15
  CACHE_TTL_HOURS: int = 24

  # 가구별 다중 검색어 기능 플래그 (Phase 2)
  ENABLE_MULTI_FURNITURE_RECO: bool = False

  # Vision 재분석 기반 네이버 추천 재랭킹 플래그
  ENABLE_VISION_RERANK: bool = False

  @property
  def cors_origins_list(self) -> list[str]:
    return [o.strip() for o in self.CORS_ORIGINS.split(',') if o.strip()]

  @property
  def google_credentials_path(self) -> str | None:
    raw = self.GOOGLE_APPLICATION_CREDENTIALS.strip()
    if not raw:
      return None

    path = Path(raw).expanduser()
    candidates = [
      path,
      ROOT_DIR / path,
      ROOT_DIR / 'backend' / path,
    ]

    for candidate in candidates:
      if candidate.exists():
        return str(candidate.resolve())

    return str((ROOT_DIR / path).resolve())


@lru_cache
def get_settings() -> Settings:
  return Settings()


_VERTEX_AI_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']


@lru_cache
def get_google_credentials() -> Credentials | None:
  settings = get_settings()
  credentials_path = settings.google_credentials_path
  if not credentials_path or not Path(credentials_path).exists():
    return None
  return service_account.Credentials.from_service_account_file(
    credentials_path,
    scopes=_VERTEX_AI_SCOPES,
  )
