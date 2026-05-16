from cachetools import TTLCache

from core.config import get_settings

_settings = get_settings()

# 인테리어 트렌드 데이터 24시간 캐시
# key: 'tone-trend:{year}' (예: 'tone-trend:2026')
# value: 트렌드 키워드/컬러 팔레트 dict
trend_cache: TTLCache = TTLCache(
  maxsize=100,
  ttl=_settings.CACHE_TTL_HOURS * 3600,
)

# 가구별 검색어 24시간 캐시
# key: 'fq:{tone_id}:{room_type}' (예: 'fq:uuid-123:거실')
# value: list[{slot, query, expected_colors}]
furniture_query_cache: TTLCache = TTLCache(
  maxsize=500,
  ttl=_settings.CACHE_TTL_HOURS * 3600,
)
