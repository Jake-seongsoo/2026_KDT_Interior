from core.room_matcher import lookup_room_key

# 방 유형별 추천 가구 슬롯 정의
# 이케아 한국 판매 카테고리 기준으로 정의 (수전·타일 등 이케아 미판매 품목 제외)
ROOM_FURNITURE_SLOTS: dict[str, list[str]] = {
  '거실': ['소파', '사이드테이블', '조명', '러그'],
  '안방': ['침대', '협탁', '조명', '커튼'],
  '침실': ['침대', '협탁', '조명', '커튼'],
  '작은방': ['침대', '책상', '조명', '수납장'],
  '주방': ['식탁', '식탁의자', '조명', '주방수납장'],
  '욕실': ['욕실수납장', '욕실매트', '욕실거울', '수건걸이'],
  '발코니': ['선반', '화분', '조명', '러그'],
  '발코나': ['선반', '화분', '조명', '러그'],
  '현관': ['신발장', '벤치', '조명', '거울'],
  '다용도실': ['수납선반', '세탁바구니', '조명'],
  '알파룸': ['책상', '의자', '조명', '수납장'],
  '드레스룸': ['행거', '서랍장', '조명', '거울'],
}

DEFAULT_FURNITURE_SLOTS: list[str] = ['가구', '조명', '러그']


def get_furniture_slots(room_type: str) -> list[str]:
  """방 유형에 맞는 가구 슬롯 목록을 반환한다. 미지 방 유형이면 기본값 반환."""
  key = lookup_room_key(room_type, ROOM_FURNITURE_SLOTS)
  return ROOM_FURNITURE_SLOTS[key] if key else DEFAULT_FURNITURE_SLOTS
