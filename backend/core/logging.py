import logging
import sys


def setup_logging() -> None:
  """uvicorn과 호환되는 표준 로깅 설정."""
  logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    stream=sys.stdout,
  )
  # 외부 라이브러리 로그 수준 억제
  logging.getLogger('google').setLevel(logging.WARNING)
  logging.getLogger('anthropic').setLevel(logging.WARNING)
  logging.getLogger('httpx').setLevel(logging.WARNING)
