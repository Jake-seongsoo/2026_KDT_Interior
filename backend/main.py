from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.logging import setup_logging
from routers import analyze, health, render

setup_logging()
settings = get_settings()

app = FastAPI(
  title='AI 인테리어 추천 API',
  description='도면 업로드 → Claude Vision 분석 → 톤 선택 → Imagen 방별 렌더링',
  version='0.1.0',
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.cors_origins_list,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*'],
)

app.include_router(health.router)
app.include_router(analyze.router)
app.include_router(render.router)
