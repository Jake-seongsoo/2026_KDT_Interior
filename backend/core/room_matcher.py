"""방 이름 매칭 공통 유틸.

도면에서 추출된 방 이름(부부욕실, 침실2 등)을 사전 키(욕실, 침실)에 매칭한다.
가구 슬롯 조회, GCS 슬러그 변환, Imagen 프롬프트 힌트 조회가 공유하는 단일 구현.
"""
from collections.abc import Mapping


def lookup_room_key(room_type: str, key_map: Mapping) -> str | None:
  """방 이름으로 딕셔너리 키를 찾는다.

  매칭 우선순위: 정확 매칭 → endswith(부부욕실→욕실) → startswith(침실2→침실)
  매칭 실패 시 None 반환.
  """
  if room_type in key_map:
    return room_type
  for key in key_map:
    if room_type.endswith(key):
      return key
  for key in key_map:
    if room_type.startswith(key):
      return key
  return None
