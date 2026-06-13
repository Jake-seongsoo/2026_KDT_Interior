"""추천 상품 품질 평가 스크립트 (수동 실행용).

사용법:
  cd G:/workspace/2026_KDT_Interior/backend
  python ../tests/eval/recommendation_accuracy.py

환경변수 필요:
  ANTHROPIC_API_KEY

출력:
  tests/eval/results/{YYYYMMDD}.csv
  콘솔에 color_match_rate, slot_coverage_rate 요약

목표:
  color_match_rate >= 0.60
  slot_coverage_rate >= 0.85
"""

import asyncio
import csv
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# backend 경로를 sys.path에 추가
BACKEND_DIR = Path(__file__).resolve().parents[2] / 'backend'
sys.path.insert(0, str(BACKEND_DIR))

from services.claude_service import ClaudeService
from services.ikea_service import IkeaService
from services.product_filter import filter_products_by_expected_colors
from core.room_furniture_map import get_furniture_slots


# ── 픽스처: 평가용 톤 10개 ────────────────────────────────────
EVAL_TONES = [
  {
    'id': 'eval-tone-01',
    'name': '딥그린 모던',
    'description': '다크그린 계열의 모던한 공간',
    'keywords': ['모던', '딥그린', '벨벳', '우드'],
    'color_palette': [
      {'name': '딥그린', 'hex': '#2E4D3A', 'role': '주조색'},
      {'name': '웜화이트', 'hex': '#F7F3EA', 'role': '벽'},
    ],
  },
  {
    'id': 'eval-tone-02',
    'name': '호텔라이크',
    'description': '뉴트럴 팔레트의 고급스러운 공간',
    'keywords': ['호텔라이크', '뉴트럴', '간접조명', '럭셔리'],
    'color_palette': [
      {'name': '웜화이트', 'hex': '#F7F3EA', 'role': '벽'},
      {'name': '딥그레이', 'hex': '#4A4A4A', 'role': '가구'},
      {'name': '골드', 'hex': '#C9A84C', 'role': '포인트'},
    ],
  },
  {
    'id': 'eval-tone-03',
    'name': '내추럴 우드',
    'description': '원목과 리넨 소재의 자연스러운 공간',
    'keywords': ['내추럴', '원목', '리넨', '베이지'],
    'color_palette': [
      {'name': '월넛', 'hex': '#5C4033', 'role': '가구'},
      {'name': '아이보리', 'hex': '#F5F0E8', 'role': '벽'},
      {'name': '베이지', 'hex': '#D9C4A7', 'role': '패브릭'},
    ],
  },
  {
    'id': 'eval-tone-04',
    'name': '미드센추리 모던',
    'description': '레트로 감성의 따뜻한 공간',
    'keywords': ['미드센추리', '머스타드', '테라코타', '레트로'],
    'color_palette': [
      {'name': '머스타드', 'hex': '#C8952A', 'role': '포인트'},
      {'name': '테라코타', 'hex': '#C4714A', 'role': '소품'},
      {'name': '크림', 'hex': '#F2ECD8', 'role': '벽'},
    ],
  },
  {
    'id': 'eval-tone-05',
    'name': '모노크롬 미니멀',
    'description': '블랙·화이트 중심의 미니멀한 공간',
    'keywords': ['미니멀', '블랙', '화이트', '무광'],
    'color_palette': [
      {'name': '블랙', 'hex': '#1A1A1A', 'role': '포인트'},
      {'name': '화이트', 'hex': '#FFFFFF', 'role': '벽'},
      {'name': '라이트그레이', 'hex': '#E5E5E5', 'role': '가구'},
    ],
  },
  {
    'id': 'eval-tone-06',
    'name': '코랄 팝',
    'description': '밝고 활기찬 코랄 포인트 공간',
    'keywords': ['코랄', '팝', '화이트', '경쾌함'],
    'color_palette': [
      {'name': '코랄', 'hex': '#E8725A', 'role': '포인트'},
      {'name': '화이트', 'hex': '#FFFFFF', 'role': '벽'},
      {'name': '라이트우드', 'hex': '#C9A87C', 'role': '가구'},
    ],
  },
  {
    'id': 'eval-tone-07',
    'name': '인디고 블루',
    'description': '짙은 블루 계열의 세련된 공간',
    'keywords': ['인디고', '네이비', '블루', '골드'],
    'color_palette': [
      {'name': '인디고', 'hex': '#3D4E81', 'role': '포인트'},
      {'name': '크림', 'hex': '#F5EDD6', 'role': '벽'},
      {'name': '골드', 'hex': '#C8A951', 'role': '소품'},
    ],
  },
  {
    'id': 'eval-tone-08',
    'name': '젠 스타일',
    'description': '일본 선(禅) 감성의 고요한 공간',
    'keywords': ['젠', '일본식', '다크브라운', '대나무'],
    'color_palette': [
      {'name': '다크브라운', 'hex': '#3B2A1A', 'role': '가구'},
      {'name': '샌드베이지', 'hex': '#E8DCC8', 'role': '벽'},
      {'name': '그린', 'hex': '#6B8C6E', 'role': '식물'},
    ],
  },
  {
    'id': 'eval-tone-09',
    'name': '스칸디 화이트',
    'description': '밝고 깨끗한 스칸디나비아 스타일',
    'keywords': ['스칸디', '화이트', '파인우드', '심플'],
    'color_palette': [
      {'name': '오프화이트', 'hex': '#F8F6F2', 'role': '벽'},
      {'name': '파인우드', 'hex': '#D4B896', 'role': '가구'},
      {'name': '라이트그레이', 'hex': '#DCDCDC', 'role': '패브릭'},
    ],
  },
  {
    'id': 'eval-tone-10',
    'name': '보타닉 그린',
    'description': '식물과 자연 소재가 어우러진 공간',
    'keywords': ['보타닉', '그린', '라탄', '자연'],
    'color_palette': [
      {'name': '올리브그린', 'hex': '#6B7B3A', 'role': '포인트'},
      {'name': '오프화이트', 'hex': '#F5F2ED', 'role': '벽'},
      {'name': '라탄', 'hex': '#C8A96E', 'role': '소품'},
    ],
  },
]

EVAL_ROOM_TYPES = ['거실', '안방', '침실', '주방']


async def evaluate_one(
  claude: ClaudeService,
  ikea: IkeaService,
  tone: dict,
  room_type: str,
) -> dict:
  """단일 톤+방 조합의 추천 품질을 평가한다."""
  slots = get_furniture_slots(room_type)
  rooms = [{'id': f'{tone["id"]}-{room_type}', 'room_type': room_type}]
  slots_map = {room_type: slots}

  # 가구 쿼리 생성
  try:
    queries_by_room = await claude.generate_furniture_queries(
      tone=tone, rooms=rooms, slots_map=slots_map
    )
    queries = queries_by_room.get(rooms[0]['id'], [])
  except Exception as e:
    return {
      'tone_id': tone['id'],
      'tone_name': tone['name'],
      'room_type': room_type,
      'slot_count': len(slots),
      'searched_slots': 0,
      'matched_products': 0,
      'total_products': 0,
      'slot_coverage_rate': 0.0,
      'color_match_rate': 0.0,
      'error': str(e),
    }

  # 슬롯별 검색 및 색상 매칭 평가
  searched_slots = 0
  matched_products = 0
  total_products = 0

  for fq in queries:
    try:
      products = await ikea.search_products(fq['query'], display=5)
      if products:
        searched_slots += 1
        filtered = filter_products_by_expected_colors(
          products, fq.get('expected_colors', []), limit=5
        )
        for p in filtered:
          total_products += 1
          name_lower = p.get('name', '').lower()
          if any(c.lower() in name_lower for c in fq.get('expected_colors', [])):
            matched_products += 1
    except Exception:
      pass

  slot_coverage = searched_slots / len(slots) if slots else 0.0
  color_match = matched_products / total_products if total_products > 0 else 0.0

  return {
    'tone_id': tone['id'],
    'tone_name': tone['name'],
    'room_type': room_type,
    'slot_count': len(slots),
    'searched_slots': searched_slots,
    'matched_products': matched_products,
    'total_products': total_products,
    'slot_coverage_rate': round(slot_coverage, 3),
    'color_match_rate': round(color_match, 3),
    'error': '',
  }


async def main() -> None:
  claude = ClaudeService()
  ikea = IkeaService()

  results = []
  total = len(EVAL_TONES) * len(EVAL_ROOM_TYPES)
  done = 0

  for tone in EVAL_TONES:
    for room_type in EVAL_ROOM_TYPES:
      done += 1
      print(f'[{done}/{total}] {tone["name"]} + {room_type} 평가 중...')
      row = await evaluate_one(claude, ikea, tone, room_type)
      results.append(row)

      # 요율 제한 방지
      await asyncio.sleep(0.5)

  # CSV 저장
  today = datetime.now(timezone.utc).strftime('%Y%m%d')
  output_dir = Path(__file__).parent / 'results'
  output_dir.mkdir(parents=True, exist_ok=True)
  output_path = output_dir / f'{today}.csv'

  fieldnames = [
    'tone_id', 'tone_name', 'room_type', 'slot_count', 'searched_slots',
    'matched_products', 'total_products', 'slot_coverage_rate', 'color_match_rate', 'error',
  ]
  with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

  # 요약 출력
  valid = [r for r in results if not r['error']]
  avg_color_match = sum(r['color_match_rate'] for r in valid) / len(valid) if valid else 0.0
  avg_slot_coverage = sum(r['slot_coverage_rate'] for r in valid) / len(valid) if valid else 0.0

  print('\n===== 평가 결과 요약 =====')
  print(f'평가 조합: {len(results)}개 ({len(EVAL_TONES)} 톤 × {len(EVAL_ROOM_TYPES)} 방)')
  print(f'오류:      {len(results) - len(valid)}건')
  print(f'색상 매칭률: {avg_color_match:.1%}  (목표: ≥ 60%)')
  print(f'슬롯 탐색률: {avg_slot_coverage:.1%}  (목표: ≥ 85%)')
  print(f'\n결과 저장: {output_path}')

  if avg_color_match < 0.60 or avg_slot_coverage < 0.85:
    print('\n⚠ 목표 미달 — ENABLE_MULTI_FURNITURE_RECO 활성화 전 프롬프트/필터 튜닝 필요')
    sys.exit(1)
  else:
    print('\n✓ 목표 달성 — ENABLE_MULTI_FURNITURE_RECO=true 활성화 가능')


if __name__ == '__main__':
  asyncio.run(main())
