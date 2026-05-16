from fastapi import APIRouter

from core.config import get_settings
from models.schemas import HealthResponse

router = APIRouter(tags=['health'])


@router.get('/health', response_model=HealthResponse)
async def health() -> HealthResponse:
  """서비스 상태를 확인한다. 인증 불필요 (Cold Start 워밍업 용도)."""
  settings = get_settings()
  return HealthResponse(status='ok', environment=settings.environment)
