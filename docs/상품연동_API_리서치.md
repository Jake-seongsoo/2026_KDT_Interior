# 상품 연동 API 리서치 — 네이버쇼핑 · 한샘 · 일룸 · IKEA

> 작성일: 2026-04-30 | AI 인테리어 추천 서비스 개발 참고 자료

---

## 요약 — MVP에서 바로 쓸 수 있는 방법

| 방법 | 난이도 | 비용 | 추천 단계 |
|------|--------|------|----------|
| **네이버 검색 API (쇼핑)** | 낮음 | ₩0 (일 25,000회 무료) | MVP 즉시 |
| **Claude Web Search (트렌드용)** | 낮음 | ~$0.01/회 | MVP (트렌드 검색만) |
| **한샘·일룸 B2B 파트너십** | 중간 | 협상 | Phase 2 |
| **IKEA B2B 제휴** | 높음 | 협상 | Phase 3 |

---

## 1. 네이버 쇼핑 검색 API

### 엔드포인트 및 기본 정보

```
GET https://openapi.naver.com/v1/search/shop
```

**요청 헤더:**
```
X-Naver-Client-Id: {발급받은 ID}
X-Naver-Client-Secret: {발급받은 SECRET}
```

**요청 파라미터:**
```
query   : "북유럽 스타일 소파"   (검색어)
display : 10                    (결과 수, 최대 100)
start   : 1                     (시작 위치)
sort    : sim | date | asc | dsc (정렬 기준)
```

**응답 예시:**
```json
{
  "lastBuildDate": "Fri, 30 Apr 2026 10:00:00 +0900",
  "total": 1234,
  "items": [
    {
      "title": "모던 북유럽 소파 2인용",
      "link": "https://...",
      "image": "https://...",
      "lprice": "298000",
      "hprice": "450000",
      "mallName": "한샘몰",
      "productId": "12345"
    }
  ]
}
```

**주요 반환 데이터:**
- ✅ 상품명, 가격(최저~최고), 이미지, 구매링크, 판매처
- ⚠️ 실시간 재고: 반환되지 않음 (링크 클릭 후 확인 필요)

### 무료 쿼터

| 항목 | 내용 |
|------|------|
| 일일 무료 한도 | **25,000회/일** |
| MVP 단계 예상 사용량 | 100~500회/일 → **무료 운영 가능** |
| 초과 시 | 별도 비용 없음 (쿼터 초과 시 차단) |

### 신청 방법 (즉시 가능)

```
1. https://developers.naver.com 접속
2. "Applications" → "새 애플리케이션 추가"
3. 애플리케이션명: "Interior AI Recommender"
4. 사용 API: 검색 → 쇼핑 선택
5. Client ID, Secret 발급
6. .env에 저장:
   NAVER_CLIENT_ID=...
   NAVER_CLIENT_SECRET=...
```

**테스트 명령어:**
```bash
curl -H "X-Naver-Client-Id: {ID}" \
     -H "X-Naver-Client-Secret: {SECRET}" \
     "https://openapi.naver.com/v1/search/shop?query=북유럽소파&display=10"
```

### FastAPI 구현 예시

```python
import httpx
import os
from fastapi import APIRouter

router = APIRouter()

@router.post("/api/search-products")
async def search_products(style: str, category: str, count: int = 5):
    headers = {
        "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
        "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET"),
    }
    params = {
        "query": f"{style} {category}",
        "display": count,
        "sort": "sim"
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://openapi.naver.com/v1/search/shop",
            headers=headers,
            params=params,
            timeout=5.0
        )

    data = response.json()
    products = []
    for item in data.get("items", []):
        products.append({
            "name": item["title"].replace("<b>", "").replace("</b>", ""),
            "price_min": int(item["lprice"]),
            "price_max": int(item["hprice"]),
            "image": item["image"],
            "link": item["link"],
            "seller": item["mallName"]
        })
    return {"query": params["query"], "products": products}
```

### 네이버 쇼핑 커넥트 (어필리에이트)

```
출시: 2025년 7월
가입 조건: 블로그·클립·크리에이터 채널 보유
수수료율: 판매자별 설정 (1~30%)

→ MVP 단계에서는 직링크 제공
→ Phase 2~3 수익화 단계에서 파트너스 링크로 전환
```

---

## 2. 한샘 / 일룸 연동

### 공개 API 현황

| 업체 | 공개 API | 권장 방법 |
|------|---------|----------|
| 한샘 | ❌ 없음 | 네이버쇼핑으로 검색 (한샘몰 상품 포함됨) → Phase 2에 B2B 문의 |
| 일룸 | ❌ 없음 | 동일 |

### Phase 2 B2B 파트너십 신청

```
한샘 파트너팀 이메일: partner@hanssem.com
일룸 비즈니스 문의: business@iloom.com

제목: AI 인테리어 추천 서비스 파트너십 제안
내용:
  - 서비스: 도면 기반 AI 인테리어 추천 플랫폼
  - 제안: 상품 데이터 실시간 연동
  - 수익 구조: CPC 또는 CPA 협상
  - 예상 상품 노출 규모: [월 추천 수]
```

---

## 3. IKEA Korea

### 공개 API 현황

```
공개 API: ❌ 없음
백엔드 API: 존재하나 이용약관상 자동화 수집 금지
```

### MVP 단계 권장 방법

```
→ 네이버쇼핑 API로 통합 검색
  (IKEA 공식몰도 네이버쇼핑에 노출됨)
→ 별도 크롤링 불필요

Phase 3 이후: IKEA 공식 제휴 신청
  이메일: ikea.kr-partner@ikea.com
  수수료율: 판매가의 3~8% (협상)
```

---

## 4. Claude Web Search 활용 범위

| 용도 | 권장 여부 | 이유 |
|------|----------|------|
| 트렌드 검색 (도면 기반 톤 6개 생성) | ✅ 권장 | 최신 인테리어 트렌드 실시간 탐색에 최적 |
| 상품 검색 (가격·링크 필요) | ❌ 비권장 | 구조화 데이터 미반환, 비용 25배 비쌈 |

**하이브리드 아키텍처:**
```
트렌드 검색 → Claude Web Search
              "2026 북유럽 미니멀리즘 인테리어 트렌드"

상품 검색  → 네이버 검색 API
              "북유럽 소파 추천"
```

---

## 5. 단계별 구현 로드맵

### Phase 1 — MVP (현재)
```
네이버 검색 API만 사용
- 구현 시간: 2~3일
- 비용: ₩0
- 커버리지: 네이버쇼핑 전체 (한샘·일룸·IKEA 포함)
```

### Phase 2 — 파트너십 추가 (5~6월)
```
- 한샘·일룸 B2B 파트너십 체결
- 파트너 상품 우선 정렬
- 네이버 쇼핑 커넥트 파트너 신청
```

### Phase 3 — 수익화 (6월~)
```
- 네이버 쇼핑 커넥트: 5~30% 수수료
- 한샘·일룸: 5~15% 마진
- IKEA 제휴: 3~8% 마진
- 오늘의집 광고 연동 (CPC/CPA)
```

---

## 비용 요약

| 항목 | 초기비용 | 월간비용 |
|------|---------|---------|
| 네이버 검색 API | ₩0 | ₩0 (25K회/일 무료) |
| Claude Web Search | ₩0 | ~₩1,000 (트렌드 검색 100회/일 기준) |
| 한샘·일룸 파트너십 | ₩0 | 수익 공유 (판매 발생 시) |

---

## 참고 링크

- [네이버 개발자센터](https://developers.naver.com/)
- [네이버 검색 API 쇼핑 가이드](https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md)
- [네이버 쇼핑 커넥트](https://shopping.naver.com/connect)
- [오늘의집 파트너센터](https://www.partnerbucketplace.com/)
- [Claude Web Search Tool 문서](https://platform.claude.com/docs/ko/agents-and-tools/tool-use/web-search-tool)

---

*작성: KDT AI/LLM 과정 개인 포트폴리오 | 문의: shark1011.sk@gmail.com*
