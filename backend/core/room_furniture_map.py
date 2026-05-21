# 방 유형별 추천 가구 슬롯 정의
# 각 슬롯은 네이버 쇼핑 카테고리와 매칭되는 한국어 단어
ROOM_FURNITURE_SLOTS: dict[str, list[str]] = {
  '거실': ['소파', '사이드테이블', '조명', '러그'],
  '안방': ['침대', '협탁', '조명', '커튼'],
  '침실': ['침대', '협탁', '조명', '커튼'],
  '작은방': ['침대', '책상', '조명', '수납장'],
  '주방': ['식탁', '식탁의자', '조명', '수납장'],
  '욕실': ['수납장', '욕실매트', '거울', '수전'],
  '발코니': ['선반', '화분', '조명', '러그'],
  '발코나': ['선반', '화분', '조명', '러그'],
  '현관': ['신발장', '벤치', '조명', '거울'],
  '다용도실': ['수납선반', '세탁바구니', '조명'],
  '알파룸': ['책상', '의자', '조명', '수납장'],
  '드레스룸': ['행거', '서랍장', '조명', '거울'],
}

DEFAULT_FURNITURE_SLOTS: list[str] = ['가구', '조명', '러그']


def get_furniture_slots(room_type: str) -> list[str]:
  """방 유형에 맞는 가구 슬롯 목록을 반환한다.

  매칭 우선순위: 정확 매칭 → endswith(부부욕실→욕실) → startswith(침실2→침실)
  미지 방 유형이면 기본값 반환.
  """
  if room_type in ROOM_FURNITURE_SLOTS:
    return ROOM_FURNITURE_SLOTS[room_type]
  for key, slots in ROOM_FURNITURE_SLOTS.items():
    if room_type.endswith(key):
      return slots
  for key, slots in ROOM_FURNITURE_SLOTS.items():
    if room_type.startswith(key):
      return slots
  return DEFAULT_FURNITURE_SLOTS
