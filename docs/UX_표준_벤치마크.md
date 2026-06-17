# Moodie · UX 표준 벤치마크 (AI 인테리어 장르)

> 작성일: 2026-06-17 | KDT AI/LLM 과정 포트폴리오
> **이 문서의 역할:** 이 분야 대표 제품들의 공통 흐름·용어·배치(장르 표준)를 정리하고, Moodie가 (A) 그대로 따라야 할 표준과 (B) Moodie에만 있어 새로 안내해야 할 것으로 나눈다.
> 페르소나·JTBD는 `페르소나_정의.md`, `JTBD.md` 참조. 미스핏 백로그(A 비교·검증)와 직접 연결된다.

---

## 1. 조사한 대표 제품 5개

| 제품 | 한 줄 특징 | 입력 |
|------|-----------|------|
| **RoomGPT / RoomsGPT** | 가장 좁고 빠른 흐름(20초 내), 400만 사용자 — 장르의 사실상 표준 | 방 **사진** |
| **Interior AI** | 사진 + 스타일 → 포토리얼 재구성 | 방 **사진** |
| **Spacely AI** | 프로용, CAD 임포트·테마/스타일 설정·빠른 렌더(60초) | 방 사진 / CAD |
| **Spacejoy** | "Shop the Look" — 디자인 안의 모든 가구가 구매 가능 | 방 사진 |
| **Collov AI** | 빈 방 가구 배치(버추얼 스테이징)·스타일 다중 | 방 사진 |

---

## 2. 공통 표준 (이 장르가 합의한 것)

### 흐름 (Flow)

> **사진 업로드 → 방 유형 선택 → 스타일 선택 → 생성 → Before/After 확인 → Variations(다른 안) → Shop the Look → 저장/공유**

- 직선형이고 단계가 적다. "업로드 → 선택 → 생성" 3스텝이 핵심.
- 생성 후 **여러 안(variations)을 나란히** 보고 고르는 게 기본.
- 무료 크레딧(일일) → 유료 전환 모델이 흔함.

### 용어 (Terminology) — 영문 UI 관행

| 표준 용어 | 의미 |
|----------|------|
| **Upload a photo of your room** | 입력 |
| **Room type** | 거실/침실/주방/욕실… 선택 |
| **Design style / Theme** | Modern·Minimalist·Scandinavian·Japandi·Bohemian… (+ "describe your own" 커스텀 프롬프트) |
| **Generate / Redesign** | 실행 |
| **Before / After** | 원본↔결과 슬라이더 비교 |
| **Variations / Regenerate** | 다른 안 생성 |
| **Shop the look** | 결과 속 상품 구매 |
| **Credits · Download · Share** | 사용량·내보내기 |

### 배치 (Layout)

- **모바일 우선 단일 컬럼.** 입력 컨트롤(업로드·방 유형·스타일) → 결과 이미지(크게) → 하단에 다른 안 썸네일·상품 목록.
- **스타일 선택 = 썸네일 카드 그리드** + 라벨.
- 결과는 **큰 이미지 1장 중심**, 그 옆/아래에 variations·"shop the look".

---

## 3. A. Moodie가 그대로 따라야 할 표준 (재발명·재교육 불필요)

사용자가 RoomGPT 류에서 이미 학습한 패턴 — 다르게 만들면 오히려 혼란. Moodie가 이미 대부분 따르고 있다.

| 표준 | Moodie 현황 |
|------|------------|
| 직선형 업로드→선택→생성→결과 | ✅ 따름 (page → analyze → tones → render → result) |
| 스타일 선택 = **썸네일 카드 그리드 + 라벨** | ✅ `ToneCandidateGrid` (팔레트 바 + 이름 + 카테고리 뱃지) |
| 결과의 **방 유형 선택(Room type)** | ✅ `RoomTabs` (거실·주방·안방…) |
| **Shop the look** = 결과에 상품 목록 부착 | ✅ `ProductGrid` (이케아) |
| "**describe your own style**" 커스텀 프롬프트 | ✅ 직접 입력 모드(`CustomToneInput` + 무드 칩) |
| 생성 중 **진행/로딩** 표시 | ✅ `LoadingScreen` / progress |
| **저장·공유·다운로드** 액션 | ✅ 공유 링크·PDF |
| AI 생성 고지 라벨 | ✅ (법적 의무와도 일치) |

### 보강 권고 (표준인데 Moodie가 약한 것)

- **Variations 비교** — 장르 표준은 "여러 안을 나란히 비교 후 선택". Moodie는 톤 1개씩만 봐서 재선택→재렌더가 필요 → 미스핏 **A**와 동일. 표준을 못 따르는 부분이므로 우선 보강 대상.
- **용어**: 장르 표준은 "**스타일/테마**"인데 Moodie는 "**톤**". 둘 다 통용은 되지만, 첫 화면에서 "톤 = 색·분위기 방향"임을 한 줄로 잡아주면 학습 비용이 준다.

---

## 4. B. Moodie에만 있어 **새로 안내해야** 할 것 (경쟁사에 없음 = 사용자 기대 밖)

여기가 핵심이다. 사용자는 RoomGPT 멘탈 모델("내 방 사진 올리면 바꿔줌")로 들어오는데, Moodie는 전제가 다르다. **명시적 온보딩·안내가 없으면 사용자가 틀린 입력을 하거나 가치를 못 알아챈다.**

| # | Moodie 고유 | 왜 안내가 필요한가 | 안내 방식 제안 |
|---|------------|-------------------|---------------|
| **B1** | **입력 = 도면(평면도), 방 사진 아님** | 장르 100%가 "방 사진 업로드". 사용자는 거실 사진을 올리려 함 → 실패 | 업로드 화면에 **예시 도면 이미지 1장**(분양도면·네이버 캡처)과 "방 사진이 아니라 **평면도**를 올려주세요" 명시. 현재 텍스트 안내만 있음 → 시각 예시로 강화 |
| **B2** | **Before가 없음** (살기 전 빈 집 전제) | Before/After는 장르 표준 기대인데 Moodie는 비교 대상이 없음 | "아직 살기 전인 새 집의 **방향을 잡는** 도구"라고 첫 화면에서 프레이밍. Before/After 슬라이더를 기대하지 않게 |
| **B3** | **집 전체를 방별로 한 번에**(멀티룸) | 경쟁사는 "이 방 하나 재구성". Moodie는 도면→거실·주방·안방 동시 | 결과 진입 시 "**집 전체를 방별로** 제안했어요" 한 줄 + 배치도로 전체 조망 먼저 |
| **B4** | **톤 = 근거·팔레트가 붙은 큐레이션 6개** (스타일 키워드 아님) | 경쟁사는 고정 스타일 목록에서 고름. Moodie는 도면+2026 트렌드로 **개인화 6개 + AI 추천 이유** | 톤 화면에 "**당신 도면에 맞춰 추천한 6가지**"임을 강조(개인화가 차별점인데 지금은 잘려서 안 보임 → 미스핏 A) |
| **B5** | **2D SVG 배치도(탑뷰)** | 사진 기반 경쟁사엔 없음. 처음 보면 용도 불명 | 배치도 위에 "방을 누르면 해당 방 제안으로 이동" 같은 **상호작용 힌트** |
| **B6** | **정밀화(예산·가족형태·가전 배치)** | 경쟁사의 "regenerate/variations"와 다른 **구조화 입력**. "정밀화"는 비표준 용어 | 버튼 라벨을 "**내 조건으로 다시(예산·가족)**"처럼 풀어쓰고, 모달 첫 줄에 무엇을 얻는지 설명 |

---

## 5. 한 줄 결론

- **따라라:** 업로드→선택→생성→결과 직선 흐름, 카드 그리드 스타일 선택, 방 탭, Shop the look, 저장/공유 — 이미 표준을 잘 따름. **단, "여러 안 비교(variations)"는 표준인데 약하니 보강.**
- **새로 안내하라:** ①도면 입력(사진 아님) ②Before 없음(빈 집 전제) ③멀티룸 ④개인화 톤 6개 ⑤2D 배치도 ⑥정밀화 — 경쟁사에 없는 6가지는 **기대 밖**이라 명시적 온보딩/문구가 없으면 오입력·가치 미인지로 이어진다.

---

## 참고 출처

- BFD Research Group — Best AI Interior Design (2026): https://www.bfdresearchgroup.org/best-ai-interior-design/
- homedesigns.ai — 10 Best AI Interior Design Tools 2026: https://homedesigns.ai/go/10-best-ai-interior-design-tools-in-2026-honest-comparison/
- RoomsGPT: https://www.roomsgpt.io/design
- Spacely AI: https://www.spacely.ai/
- dressmycrib — 13 AI Interior Design Tools (2026): https://dressmycrib.com/blog/ai-interior-design
- Apartment Therapy — Free AI Interior Design Tools: https://www.apartmenttherapy.com/ai-interior-design-37304209

---

*작성: KDT AI/LLM 과정 개인 포트폴리오 | 근거: 웹 벤치마크 + frontend 화면 코드 직접 검토*
