import logging

import svgwrite

logger = logging.getLogger(__name__)

# 방 우선순위 기반 기본 그리드 배치 (position 데이터 없을 때 fallback)
_FALLBACK_POSITIONS = [
  {'x': 0.05, 'y': 0.05, 'w': 0.55, 'h': 0.55},  # 거실 (우선순위 1)
  {'x': 0.62, 'y': 0.05, 'w': 0.33, 'h': 0.40},  # 주방 (우선순위 2)
  {'x': 0.05, 'y': 0.63, 'w': 0.40, 'h': 0.32},  # 안방 (우선순위 3)
  {'x': 0.48, 'y': 0.63, 'w': 0.47, 'h': 0.32},  # 작은방 (우선순위 4)
]

_ROOM_COLORS = ['#EEF4FB', '#FBF4EE', '#F4FBEE', '#FBF0EE']
_TEXT_COLOR = '#2A1A0A'
_BORDER_COLOR = '#B0906A'


def build_layout_svg(rooms: list[dict], canvas_w: int = 600, canvas_h: int = 400) -> str:
  """방 정보를 기반으로 2D 탑뷰 SVG 배치도를 생성한다."""
  dwg = svgwrite.Drawing(size=(canvas_w, canvas_h))

  # 배경
  dwg.add(dwg.rect(
    insert=(0, 0),
    size=(canvas_w, canvas_h),
    fill='#FAF7F2',
    stroke='#C4B090',
    stroke_width=2,
  ))

  for idx, room in enumerate(rooms[:4]):  # 최대 4개 방만 표시
    pos = room.get('position') or _FALLBACK_POSITIONS[idx % len(_FALLBACK_POSITIONS)]
    x = pos['x'] * canvas_w
    y = pos['y'] * canvas_h
    w = pos['w'] * canvas_w
    h = pos['h'] * canvas_h

    fill_color = _ROOM_COLORS[idx % len(_ROOM_COLORS)]

    # 방 사각형
    dwg.add(dwg.rect(
      insert=(x, y),
      size=(w, h),
      fill=fill_color,
      stroke=_BORDER_COLOR,
      stroke_width=1.5,
      rx=4,
    ))

    # 방 이름 (중앙)
    dwg.add(dwg.text(
      room.get('room_type', f'방{idx + 1}'),
      insert=(x + w / 2, y + h / 2 + 5),
      text_anchor='middle',
      font_size=14,
      font_family='Malgun Gothic, Apple SD Gothic Neo, sans-serif',
      fill=_TEXT_COLOR,
      font_weight='600',
    ))

    # 면적 표시 (있을 때만)
    area = room.get('area_sqm')
    if area:
      dwg.add(dwg.text(
        f'{area:.1f}㎡',
        insert=(x + w / 2, y + h / 2 + 22),
        text_anchor='middle',
        font_size=11,
        font_family='Malgun Gothic, Apple SD Gothic Neo, sans-serif',
        fill='#8B6950',
      ))

  logger.info('SVG 배치도 생성 완료: 방 %d개', len(rooms[:4]))
  return dwg.tostring()
