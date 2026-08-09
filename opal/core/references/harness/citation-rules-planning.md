# 인용 규칙 — 기획 트랙 부록 (Citation Rules · Planning)

> 출처: `opal/core/references/harness/citation-rules.md` §8 (분리 이전 원문)
> 로드 시점: 기획 산출물(정책서·PRD·TRD·IA·와이어프레임 등) 작성 시
> 역할: 비즈니스 용어 우선 원칙(기획 산출물 본문의 코드 식별자 주어 사용 금지 + 자연어 변환 규칙)

---

## 8. 비즈니스 용어 우선 원칙 (기획 산출물)

> **[MUST]** 정책서·PRD·TRD·IA·외부 API 명세서 등 기획 산출물과 brain 페이지의 **본문은 비즈니스 용어/자연어로 서술**한다. 코드 변수·enum·식별자를 본문 서술의 주어로 나열하는 것을 금지한다.

핵심 명제: **"코드는 SSOT 근거이지 본문 서술의 주어가 아니다."**

### 8.1 적용 대상

기획/지식 산출물(비개발 트랙, `citation-rules.md` §1.5) — 정책서, PRD, TRD, IA, 외부 API 명세서, 기능 시나리오/화면 흐름도, brain concept/entity/synthesis 페이지.

> ANALYSIS/PLAN/EXECUTE 등 개발 트랙 산출물은 코드 토큰을 [MUST] 포맷(`citation-rules-dev.md` §2.5)으로 직접 인용하는 것이 정상이므로 이 원칙의 강제 대상이 아니다.

### 8.2 작성 규칙

1. **코드 식별자 본문 나열 금지** — 변수·enum·컬럼·함수명을 본문 문장의 주어/서술 대상으로 쓰지 않는다.
2. **비즈니스 용어 우선** — 의미를 자연어로 서술하고, 코드 식별자는 **괄호 + 근거 인용**(`경로:줄번호`, `citation-rules.md` §2.2)으로만 병기한다.
3. **조건·상태군 풀어쓰기** — enum/플래그 비교식은 의미를 풀어 쓴다.

### 8.3 자연어 변환 예시

| 코드 조건 (Bad — 본문 주어로 사용) | 비즈니스 용어 변환 (Good) | 코드 근거 병기 |
|----------------------------------|--------------------------|---------------|
| `autoSelCancelYn ≠ N` | 자동취소가 켜져 있고 | (`path/to/file:line`) |
| `basicPugCpMsnBscId ≠ null` | 기본 미션이 지정되어 있으며 | (`path/to/file:line`) |
| `AUTO_SELECT_CANCELABLE` 상태 | 자동 선택 취소가 가능한 상태 | (`path/to/file:line`) |

- **Bad**: "`autoSelCancelYn`가 N이 아니고 `basicPugCpMsnBscId`가 null이 아니면 자동 취소된다."
- **Good**: "자동취소가 켜져 있고(`a.java:120`) 기본 미션이 지정되어 있으면(`b.java:88`) 자동으로 취소된다."

### 8.4 표 작성 권장 — "조건(용어)" + "코드 근거" 분리

조건/규칙을 표로 정리할 때는 **의미 컬럼**과 **코드 근거 컬럼**을 분리한다. 코드 식별자를 의미 컬럼에 섞지 않는다.

| 조건 (비즈니스 용어) | 처리 | 코드 근거 |
|---------------------|------|----------|
| 자동취소가 켜져 있고 기본 미션이 지정됨 | 자동 취소 실행 | `path:120`, `path:88` |

### 8.5 검증 연결

- opwt 작성 워커: `opal/skills/opal-pilot-write-tech/references/network-guide.md` §7 공통 작성 원칙이 이 §8을 참조한다.
- opwt QA 워커: `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` §3.1이 이 §8 위반을 검출한다.
- brain ingest 워커: `opal/skills/op-brain-ingest/SKILL.md` STEP 4 entity 작성 규칙이 §8.2(코드 식별자 본문 주어 금지)·§8.8(부록 분리)을 명문화한다.
- brain init 시드: `opal/skills/opal-brain/SKILL.md` 핵심 엔티티 시드 entity 작성 규칙이 §8.2·§8.8을 명문화한다 (소스 커버리지 부록 분리).
- opal-brain 코드→브레인 저술 게이트: `opal/skills/opal-brain/SKILL.md` §공통 규칙 "코드→브레인 저술 자기검토 게이트"가 이 §8을 4항목 체크리스트(구체성·자연스러운 문장·소스 위치 근거)로 집행한다 — entity 시드·concept ingest·synthesis 파일링 add-page 직전 적용.
- 공통 문서 표준: `opal/core/references/opal-doc-standard.md` §3 정책서 행이 이 §8을 가리킨다.

### 8.6 다층 근거 원칙

비즈니스 용어·결정의 근거는 코드 단층만으로 충분하지 않다. 코드(SSOT)·정책서·IA·설계 문서를 **다층 병기**한다.

**언제 적용하는가:**

- brain term 페이지 `sources` 키: 해당 용어가 정의된 근거 문서가 복수 계층(코드+정책+IA)에 걸쳐 있을 때 모두 병기한다.
- PLAN·ANALYSIS 산출물에서 비즈니스 결정을 기술할 때: 코드 참조 외에 정책 조항·화면 근거가 있으면 함께 기재한다.
- 기획 산출물(정책서·TRD·PRD) 작성 시: 동일 개념이 코드·정책·IA 세 계층에서 동시에 정의되면 세 계층 모두 `sources`에 포함한다.

**토큰 형식(SSOT):** `opal/tools/brain-tool/templates/schema-template.md` §4 링크 규칙 — `POL-{번호}` (정책참조), `ia:{system}:{screen}` (IA참조). 형식 변경은 해당 SCHEMA §4를 수정한다.

### 8.7 업무 표면(business-surface) 명명

업무 표면(surface)은 비즈니스 용어가 실제로 등장하는 화면·프로세스·접점을 가리킨다. brain term 페이지의 `surfaces` 키와 정합한다.

**명명 규칙:**

- 형식: `{system}:{screen-id}` — system은 서비스 시스템 식별자(소문자 kebab), screen-id는 IA의 화면 ID 또는 약어.
- 예시: `store-admin:order-list`, `buyer-app:checkout`, `ops-dashboard:settlement`.
- IA 문서가 있으면 해당 화면 ID를 그대로 사용한다. IA 미정 시 업무 맥락에서 의미 있는 식별자를 임시 사용하고, IA 확정 후 갱신한다.
- `ia:{system}:{screen}` 토큰(§4 IA참조)과 동일 식별자 체계를 공유한다.

### 8.8 개발자 부록 분리

기획 산출물(비개발 트랙, `citation-rules.md` §1.5)에서 코드 식별자·enum·API path·레포명은 본문 주어로 사용하지 않는다(§8.2 재확인).

**강등 배치 원칙:**

- 본문에서 코드 식별자가 필요한 경우, 해당 내용을 "소스 커버리지" 또는 "개발자 부록" 섹션으로 분리하여 배치한다.
- 본문 서술 계층(의미)과 코드 참조 계층(식별자)을 문서 구조적으로 분리한다.
- brain term 페이지에서 코드 식별자를 언급해야 한다면 `sources` 키 또는 별도 "개발자 부록" 하위 섹션에만 기재한다.

### 8.9 5W1H 사고 프레임

5W1H(누가·언제·어디서·무엇을·왜·어떻게)는 ingest/query 품질을 점검하는 **사고 틀**로 사용한다.

**[MUST] 5W1H를 페이지 섹션 구조 템플릿으로 강제하는 것을 금지한다.** brain 페이지나 기획 산출물의 섹션 헤딩으로 `## 누가`, `## 왜`, `## 어떻게` 등을 배치하지 않는다.

**올바른 사용:**

- ingest 전 품질 점검: "이 용어 정의에 who(행위자)/what(의미)/why(목적)가 충분히 담겼는가?" 내부 검토 질문으로 사용.
- query 품질 점검: brain search 결과가 질문의 5W1H 요소를 충족하는지 확인하는 틀로 사용.
- 산출물 섹션 구조는 해당 스킬 SKILL.md의 섹션 템플릿을 따른다.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-08-09 20:50 | `citation-rules.md` §8(비즈니스 용어 우선 원칙, 기획 산출물 전용)을 조건부 로드 분리 신설 — 원문 그대로 이동, 내용 축약 없음. §6(사람/AI 탐색 가이드)은 §2.1~§2.4 4종 포맷 전체에 대한 트랙 무관 범용 가이드로 판단되어 이관 대상에서 제외, `citation-rules.md`에 유지 (087) |
