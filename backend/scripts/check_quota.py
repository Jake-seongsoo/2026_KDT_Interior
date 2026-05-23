"""GCP Gemini Image 쿼터 상태 진단 스크립트.

단일 호출 성공 여부로 free_tier=0 버그인지 burst 쿼터 문제인지 구분한다.
실행: python scripts/check_quota.py
"""
import asyncio
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import get_google_credentials, get_settings
from google import genai
from google.genai import types


async def main() -> None:
  settings = get_settings()
  print(f'프로젝트 : {settings.GCP_PROJECT_ID}')
  print(f'모델     : {settings.GEMINI_IMAGE_MODEL}')
  print(f'Location : {settings.GEMINI_IMAGE_LOCATION}')
  print('-' * 50)

  client = genai.Client(
    vertexai=True,
    project=settings.GCP_PROJECT_ID,
    location=settings.GEMINI_IMAGE_LOCATION,
    credentials=get_google_credentials(),
  )

  config = types.GenerateContentConfig(
    response_modalities=['IMAGE'],
    image_config=types.ImageConfig(aspect_ratio='4:3'),
  )

  # 테스트 1: 단일 호출
  print('[테스트 1] 단일 API 호출...')
  t0 = time.time()
  try:
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
      None,
      lambda: client.models.generate_content(
        model=settings.GEMINI_IMAGE_MODEL,
        contents='A simple white room with a window. Minimal interior design.',
        config=config,
      ),
    )
    elapsed = time.time() - t0
    has_image = any(
      part.inline_data and part.inline_data.data
      for c in (response.candidates or [])
      for part in (c.content.parts or [])
    )
    if has_image:
      print(f'  결과: 성공 ({elapsed:.1f}s) — 이미지 생성 정상')
    else:
      print(f'  결과: 응답은 왔으나 이미지 없음 ({elapsed:.1f}s)')
      print(f'  응답: {response}')
  except Exception as e:
    elapsed = time.time() - t0
    print(f'  결과: 실패 ({elapsed:.1f}s)')
    print(f'  오류: {e}')
    if '429' in str(e) or 'RESOURCE_EXHAUSTED' in str(e):
      print()
      print('  진단: free_tier=0 버그 의심 — 단일 호출도 429 발생')
      print('  조치: GCP Console > APIs & Services > Quotas에서')
      print('        "Generate Content" 항목 한도가 0인지 확인')
      print('        0이면 Google Cloud Support에 버그 신고 필요')
    return

  # 테스트 2: 연속 3회 호출 (burst 테스트)
  print()
  print('[테스트 2] 연속 3회 호출 (burst 쿼터 테스트)...')
  results = []
  for i in range(3):
    t1 = time.time()
    try:
      response = await loop.run_in_executor(
        None,
        lambda: client.models.generate_content(
          model=settings.GEMINI_IMAGE_MODEL,
          contents=f'A cozy bedroom interior design, attempt {i + 1}.',
          config=config,
        ),
      )
      results.append(('성공', time.time() - t1))
      print(f'  {i + 1}회: 성공 ({time.time() - t1:.1f}s)')
    except Exception as e:
      results.append(('실패', time.time() - t1))
      print(f'  {i + 1}회: 실패 ({time.time() - t1:.1f}s) — {e}')

  print()
  failures = [r for r in results if r[0] == '실패']
  if not failures:
    print('진단: 연속 3회 모두 성공 — burst 한도 내 정상 동작')
    print('     9개 병렬 실행 시 burst 한도 초과 가능성. semaphore 조정 권장.')
  else:
    print('진단: 연속 호출에서 429 발생 — QPM 한도가 매우 낮음')
    print('     GCP Console에서 쿼터 한도 확인 및 증가 요청 필요')


if __name__ == '__main__':
  asyncio.run(main())
