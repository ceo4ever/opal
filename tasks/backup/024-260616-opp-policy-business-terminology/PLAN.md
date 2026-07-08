# PLAN: 기획 산출물 비즈니스 용어 우선 원칙 내재화

> 작성일: 2026-06-16
> 입력: TASK.md
> 출력: PLAN.md
> 핵심 명제: **"코드는 SSOT 근거이지 본문 서술의 주어가 아니다."** (TASK.md §1, §6)

---

## 0. 요구사항 커버 매트릭스 (R-1 ~ R-7)

| 요구사항 | 대상 파일 | 실행 Step | 비고 |
|---------|----------|----------|------|
| R-1 — citation-rules에 SSOT 신설 | `opal/core/references/harness/citation-rules.md` | Step 1 | 새 §8 신설 + 변경이력 v2.1 추가. 원칙 본문 **유일 SSOT** |
| R-2 — opwt Phase 3 공통 작성 원칙 주입 | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | Step 2 | §7 상단 "공통 작성 원칙" 블록 1개 (4곳 개별 삽입 대신) → §8 참조 |
| R-3 — opwt QA 비즈니스 용어 체크 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | Step 3 | §3 용어 일관성에 신규 절 추가 + §6 QA 절차 1줄 |
| R-4 — brain 페이지 작성 규칙 | `opal/skills/op-brain-ingest/SKILL.md` | Step 4 | STEP 4 작성 규칙 불릿 1줄 추가 + 변경이력 v1.2 |
| R-5 — 공통 문서 표준 포인터 | `opal/core/references/opal-doc-standard.md` | Step 5 | §3 정책서 행 비고에 포인터 1줄 + 변경이력 v2.2 |
| R-6 — 확정 기준 영구 기록 | `.opal/AGENT.md` | Step 6 | 확정 기준 표에 행 추가 (TASK.md §6 원문) |
| R-7 — 배포 + 변경이력 | `scripts/install-mac.sh` 재실행 | Step 7 | 스크립트 코드 변경 불요 — 재배포 명령 실행. 변경이력은 각 Step에서 처리 |

> SSOT 단일화 원칙(TASK.md §5): 원칙 **본문**은 citation-rules §8 1곳에만 둔다. R-2/R-3/R-4/R-5는 모두 "§8을 참조하라"는 포인터만 주입한다 (재서술 금지).

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 근거/용어 SSOT — §8 신설 위치 (R-1) |
| D-2 | 설계 | network-guide.md | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | opwt Phase 3 워커 프롬프트 §7 (R-2) |
| D-3 | 설계 | consistency-rules.md | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | opwt QA 검증 §3/§6 (R-3) |
| D-4 | 설계 | op-brain-ingest SKILL.md | `opal/skills/op-brain-ingest/SKILL.md` | brain 페이지 작성 규칙 STEP 4 (R-4) |
| D-5 | 설계 | opal-doc-standard.md | `opal/core/references/opal-doc-standard.md` | 공통 문서 표준 §3 (R-5) |
| D-6 | 설계 | 프로젝트 AGENT.md | `.opal/AGENT.md` | 확정 기준 표 (R-6) |
| D-7 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 배포 메커니즘 확인 (R-7) |

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/harness/citation-rules.md` | 근거/용어 SSOT 하네스. 현재 §0~§7 + 변경이력(최신 v2.0) | O — §8 신설 + 변경이력 | `citation-rules.md:276-329` (§7 끝 + 변경이력 v2.0) |
| `opal/skills/opal-pilot-write-tech/references/network-guide.md` | opwt 산출물 네트워크 + Phase 3 워커 프롬프트(7-1~7-4) | O — §7 상단 공통 블록 | `network-guide.md:294-298` (§7 헤더~7-1 사이) |
| `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | opwt 정합성 검증 규칙. §3 용어 일관성 / §6 QA 워커 프롬프트 | O — §3 신규 절 + §6 1줄 | `consistency-rules.md:125-143` (§3), `:184-208` (§6 절차) |
| `opal/skills/op-brain-ingest/SKILL.md` | brain ingest 워커. STEP 4 페이지 작성 규칙 불릿 | O — 불릿 1줄 + 변경이력 | `SKILL.md:80-88` (작성 규칙), `:236-241` (변경이력) |
| `opal/core/references/opal-doc-standard.md` | 공통 문서 표준. §3 문서 유형별 필수 섹션 | O — 정책서 행 비고 + 변경이력 | `opal-doc-standard.md:59-67` (§3 기획 산출물), `:148-154` (변경이력) |
| `.opal/AGENT.md` | 프로젝트 PM 설정. 확정 기준 표 | O — 행 추가 | `.opal/AGENT.md:67-73` (확정 기준 표) |
| `scripts/install-mac.sh` | 배포 스크립트. references/skills를 `~/.opal/`로 복사 | X — 코드 변경 불요, 재실행만 | `install-mac.sh:1148-1158` (references 복사), `:893-901` (skills 복사) |

### 현재 상태

1. **citation-rules.md (D-1)**: §0 근거 제시 원칙 → §1 적용범위 → §1.5 트랙별 매트릭스 → §2 인용 포맷(2.1~2.5) → §3 적용 방식 → §4 단계별 의무 → §5 예외 → §6 사람/AI 탐색 → §7 영역 간 용어 일관성. 변경이력은 v1.0/v2.0 (`citation-rules.md:324-329`). **§8이 비어 있음 — 신설 위치로 확정.** "비즈니스 용어 우선"이라는 개념은 어디에도 없음(중복 위험 없음). §7은 "영역 간 토큰 불일치 검출"로 별개 주제이며 §8(본문 서술 시 용어 우선)과 구분됨.
2. **network-guide.md (D-2)**: §7 "Phase 3 워커 프롬프트 템플릿"이 `:294`에서 시작, 인트로(`:296`) 직후 7-1 보강(`:298`)/7-2 재작성(`:337`)/7-3 신규(`:376`)/7-4 외부 API(`:478`) 4개 하위 프롬프트로 구성. 각 프롬프트에 개별 삽입하면 4곳 중복 → §7 인트로 직후 "공통 작성 원칙" 블록 1개로 단일화하는 것이 SSOT 원칙에 부합.
3. **consistency-rules.md (D-3)**: §3 "용어 일관성"(`:125-143`)은 "동일 개념 = 동일 용어" 검증. 본 태스크가 요구하는 "본문이 코드 식별자를 주어로 썼는가"는 다른 차원이므로 §3에 신규 하위 절(§3.1 비즈니스 용어 우선 검증)로 추가. §6 QA 워커 프롬프트 절차(`:195-208`)에 검증 1줄 추가하여 워커가 실제 수행하도록 연결.
4. **op-brain-ingest/SKILL.md (D-4)**: STEP 4 "페이지 작성 규칙" 불릿(`:83-88`). 현재 `코드 참조: 코드 본문 복제 금지 — file_path:line 형식 참조만 허용` 줄(`:86`) 존재. 그 직후 비즈니스 용어 불릿 1줄 추가. 변경이력 최신 v1.1(`:241`).
5. **opal-doc-standard.md (D-5)**: §3 "기획 산출물 (opwt)" 표(`:61-65`)에 정책서 행 없음 — 정책서는 §3 "범용" 표(`:52`)에 존재. §3 범용 정책서 행 비고에 포인터 추가 또는 §1 언어 규칙(`:7-13`)에 포인터. **권장: 범용 §3 정책서 행 비고에 포인터** (정책서가 §3 범용에 위치). 변경이력 최신 v2.1(`:154`), 작성자 컬럼은 v2.1에서 제거됨(`:154`) → 변경이력 행은 `버전/일시/변경내용` 3컬럼.
6. **.opal/AGENT.md (D-6)**: 확정 기준 표(`:71-73`)에 현재 **#1 행만** 존재. TASK.md §6은 "#7 행 추가"로 명시. **discrepancy 발견** — §4 리스크 R-2 참조. 캡틴 의도(영구 기록)를 따르되 행 번호는 EXECUTE에서 확인.
7. **install-mac.sh (D-7)**: `install_opal_references`(`:1148-1158`)가 `opal/core/references/` 전체를 `cp -Rf`로 `~/.opal/references/`에 복사. 스킬은 `:893-901`에서 디렉토리별 복사. **citation-rules.md(references 하위)·opal-doc-standard.md(references 하위)·network-guide.md/consistency-rules.md/op-brain-ingest(skills 하위) 모두 재실행만으로 자동 배포됨.** install.sh/install.ps1(타 플랫폼)도 동일 구조로 복사하므로 별도 코드 수정 불요 — "4번째 동기 지점" 우려는 **스크립트가 디렉토리 전체를 복사하는 방식이라 개별 파일 등록 지점이 없으므로 해당 없음.**

### 영향 범위

- 변경은 모두 **문서/프롬프트 텍스트**다. 코드 로직·실행 경로 변경 없음 → TEST-SCENARIO 불요(TASK.md §5).
- §8 신설 후 opwt 워커(network-guide §7 참조)·QA 워커(consistency-rules §6 참조)·brain 워커(SKILL.md STEP 4)가 §8을 가리키므로, **§8 섹션 번호가 정확해야 한다** (참조 깨짐 방지 — §4 리스크 R-1).
- `.opal/AGENT.md`는 배포 파일이 아닌 프로젝트 PM 설정이므로 직접 수정 대상(TASK.md 제약, install 배포 불요).

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| — | (없음) | 기존 문서에 섹션·행 추가만 수행 | — |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `opal/core/references/harness/citation-rules.md` | §8 "비즈니스 용어 우선 원칙(기획 산출물)" 신설 + 변경이력 v2.1 | `citation-rules.md:322` (§7 끝, §8 삽입), `:329` (변경이력 v2.0 다음 행) |
| 2 | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | §7 인트로 직후 "공통 작성 원칙" 블록 추가 (§8 참조) | `network-guide.md:296-297` (§7 인트로~7-1 사이) |
| 3 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | §3에 §3.1 신규 절 + §6 절차 5단계 직후 1줄 | `consistency-rules.md:143` (§3 끝), `:202` (§6 절차 5) |
| 4 | `opal/skills/op-brain-ingest/SKILL.md` | STEP 4 작성 규칙 불릿 1줄 + 변경이력 v1.2 | `SKILL.md:86` (코드 참조 불릿 다음), `:241` (변경이력 v1.1 다음) |
| 5 | `opal/core/references/opal-doc-standard.md` | §3 범용 정책서 행 비고에 포인터 + 변경이력 v2.2 | `opal-doc-standard.md:52` (정책서 행), `:154` (변경이력 v2.1 다음) |
| 6 | `.opal/AGENT.md` | 확정 기준 표에 행 추가 (TASK.md §6 원문) | `.opal/AGENT.md:73` (표 마지막 행 다음) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| — | (없음) | — |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | §8 SSOT 본문 신설 (하위 레이어 — 나머지가 의존) | citation-rules.md | 중 |
| 2 | opwt Phase 3 공통 블록 (§8 참조) | network-guide.md | 하 |
| 3 | opwt QA 체크 (§8 참조) | consistency-rules.md | 하 |
| 4 | brain 페이지 규칙 (§8 참조) | op-brain-ingest/SKILL.md | 하 |
| 5 | 문서 표준 포인터 (§8 참조) | opal-doc-standard.md | 하 |
| 6 | 확정 기준 영구 기록 | .opal/AGENT.md | 하 |
| 7 | 재배포 + 변경이력 검증 | install-mac.sh 재실행 | 하 |

> **의존성**: Step 1(§8)이 SSOT 본문 → Step 2~5는 §8을 참조하므로 Step 1 완료 후 §8 섹션 번호 확정값을 사용해야 한다. Step 2~6은 서로 다른 파일이라 상호 독립(병렬 가능). Step 7은 모든 편집 완료 후.

### 핵심 설계

#### Step 1 — citation-rules.md §8 신설 (SSOT 본문)

§7(`citation-rules.md:322` 끝) 다음, 변경이력(`:324`) 앞에 신규 §8을 삽입한다 (→ D-1 §7). 아래는 **EXECUTE가 그대로 반영할 §8 초안 문구**다.

```markdown
## 8. 비즈니스 용어 우선 원칙 (기획 산출물)

> **[MUST]** 정책서·PRD·TRD·IA·외부 API 명세서 등 기획 산출물과 brain 페이지의 **본문은 비즈니스 용어/자연어로 서술**한다. 코드 변수·enum·식별자를 본문 서술의 주어로 나열하는 것을 금지한다.

핵심 명제: **"코드는 SSOT 근거이지 본문 서술의 주어가 아니다."**

### 8.1 적용 대상

기획/지식 산출물(비개발 트랙, §1.5) — 정책서, PRD, TRD, IA, 외부 API 명세서, 기능 시나리오/화면 흐름도, brain concept/entity 페이지.

> ANALYSIS/PLAN/EXECUTE 등 개발 트랙 산출물은 코드 토큰을 [MUST] 포맷(§2.5)으로 직접 인용하는 것이 정상이므로 이 원칙의 강제 대상이 아니다.

### 8.2 작성 규칙

1. **코드 식별자 본문 나열 금지** — 변수·enum·컬럼·함수명을 본문 문장의 주어/서술 대상으로 쓰지 않는다.
2. **비즈니스 용어 우선** — 의미를 자연어로 서술하고, 코드 식별자는 **괄호 + 근거 인용**(`경로:줄번호`, §2.2)으로만 병기한다.
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
- brain ingest 워커: `opal/skills/op-brain-ingest/SKILL.md` STEP 4 작성 규칙이 이 §8을 따른다.
- 공통 문서 표준: `opal/core/references/opal-doc-standard.md` §3 정책서 행이 이 §8을 가리킨다.
```

변경이력 행 추가 (`:329` 다음, → D-1 변경이력) — 작성자 컬럼 없는 `버전/날짜/변경내용` 3컬럼 형식 준수:

```markdown
| v2.1 | 2026-06-16 | §8 비즈니스 용어 우선 원칙(기획 산출물) 신설 — 코드 식별자 본문 주어 금지 / 자연어 변환 예시 / 조건·코드 근거 표 분리 (024) |
```

> [MUST] `citation-rules.md` §2.2: 코드 근거는 `` `경로:줄번호` `` 포맷 — §8 병기 예시는 이 포맷을 따른다.
> [MUST] `citation-rules.md` §2.4: 재해석 여지 있는 금지사항은 `[MUST]` 접두사 — §8 본문 첫 [MUST] 블록이 이를 따른다.

#### Step 2 — network-guide.md §7 공통 작성 원칙 블록

§7 인트로(`network-guide.md:296`) "문서 작성/수정 워커에게 전달하는 표준 프롬프트." 직후, 7-1(`:298`) 앞에 공통 블록 1개를 삽입한다 (→ D-2 §7). 4개 하위 프롬프트(7-1~7-4)에 개별 중복 삽입하지 않는다 (SSOT 원칙).

```markdown
### 7-0. 공통 작성 원칙 (모든 Phase 3 프롬프트에 적용)

아래 원칙을 7-1~7-4 모든 워커 프롬프트에 공통 적용한다 (워커 프롬프트의 "수행 작업"에 포함하여 전달).

> **[MUST]** 본문은 비즈니스 용어/자연어로 서술한다. 코드 변수·enum·식별자(`autoSelCancelYn` 등)를 본문 서술의 주어로 나열하지 않으며, 코드 식별자는 괄호+근거 인용(`경로:줄번호`)으로만 병기한다. 조건·상태군은 의미를 풀어 쓴다. **상세 규칙·예시는 `opal/core/references/harness/citation-rules.md` §8 "비즈니스 용어 우선 원칙"을 따른다.**
```

> [MUST] `citation-rules.md` §8: "코드는 SSOT 근거이지 본문 서술의 주어가 아니다." — network-guide §7-0은 본문 재서술 없이 §8을 참조만 한다.

#### Step 3 — consistency-rules.md §3.1 + §6 절차

(a) §3 "용어 일관성"(`consistency-rules.md:125`) 끝(`:143`)에 신규 하위 절 §3.1을 추가한다 (→ D-3 §3):

```markdown
### 3.1 비즈니스 용어 우선 검증 (기획 산출물)

기획 산출물 본문이 코드 식별자를 주어로 서술했는지 검출한다. 상세 기준은 `opal/core/references/harness/citation-rules.md` §8을 따른다.

| 체크 항목 | 기준 |
|-----------|------|
| 본문이 코드 변수·enum·식별자를 서술 주어로 나열했는가 | 위반 0건 (자연어 서술 + 괄호 근거 병기로 전환) |
| 조건·상태군이 비즈니스 용어로 풀어 쓰였는가 | enum 비교식의 의미 풀어쓰기 확인 |
| 코드 식별자가 괄호+근거 인용(`경로:줄번호`)으로만 병기되었는가 | 본문 주어 사용 시 fail |
```

(b) §6 QA 워커 프롬프트 수행 절차(`:202` 5단계 "용어 매핑 테이블…" 직후)에 1줄 추가 (→ D-3 §6):

```markdown
5-1. §3.1 비즈니스 용어 우선 검증 체크 항목을 순회하여 본문이 코드 식별자를 주어로 썼는지 검출하고, 위반을 action_required에 기록한다.
```

#### Step 4 — op-brain-ingest/SKILL.md STEP 4 불릿 + 변경이력

(a) STEP 4 "페이지 작성 규칙" 불릿에서 `코드 참조` 줄(`SKILL.md:86`) 직후에 1줄 추가 (→ D-4 STEP 4):

```markdown
- **비즈니스 용어 우선**: 본문은 비즈니스 용어/자연어로 서술한다. 코드 식별자를 본문 주어로 나열 금지 — 괄호+`file_path:line` 근거로만 병기한다 (상세: `opal/core/references/harness/citation-rules.md` §8)
```

(b) 변경이력 v1.1(`:241`) 다음 행 추가:

```markdown
| v1.2 | 2026-06-16 | STEP 4 작성 규칙에 비즈니스 용어 우선 불릿 추가 — citation-rules §8 참조 (024) |
```

#### Step 5 — opal-doc-standard.md 정책서 행 포인터 + 변경이력

(a) §3 범용 표 정책서 행(`opal-doc-standard.md:52`) 비고 컬럼에 포인터 추가 (→ D-5 §3). 현재 비고는 "비즈니스 규칙":

```markdown
| **정책서** | 개요, 용어정의, 각 정책 영역, 변경이력 | 비즈니스 규칙 — 본문은 비즈니스 용어 우선 (코드 식별자 본문 주어 금지: `citation-rules.md` §8) |
```

(b) 변경이력 v2.1(`:154`) 다음 행 추가 (작성자 컬럼 없는 3컬럼):

```markdown
| v2.2 | 2026-06-16 | §3 정책서 행에 비즈니스 용어 우선 포인터 추가 — citation-rules §8 참조 (024) |
```

> §3 헤더는 구조 변경이 아닌 비고 1줄 보강 → Minor(v2.2)로 처리 (→ D-5 §5 버전 넘버링: 내용 수정 = Minor).

#### Step 6 — .opal/AGENT.md 확정 기준 행 추가

확정 기준 표(`.opal/AGENT.md:73`) 마지막 행 다음에 행을 추가한다 (→ D-6). TASK.md §6 원문을 "원칙" 컬럼에 그대로 사용:

```markdown
| 7 | 정책서·brain 등 기획 산출물은 코드 변수·enum·식별자 나열 금지 — 반드시 비즈니스 용어/자연어로 설명하고, 코드 식별자(`autoSelCancelYn`·`AUTO_SELECT_CANCELABLE` 등)는 괄호+근거 인용(`경로:줄번호`)으로만 병기한다. 조건·상태군은 의미를 풀어 쓴다(예: `autoSelCancelYn≠N` → "자동취소가 켜져 있고", `basicPugCpMsnBscId≠null` → "기본 미션이 지정되어 있으며"). 코드는 SSOT 근거이지 본문 서술의 주어가 아니다. 표는 "조건(용어)"+"코드 근거" 분리 권장. | TASK 024 — citation-rules §8 SSOT 등록 | 2026-06-16 |
```

> **행 번호 주의**: 현재 표에는 #1 행만 존재(`:73`). TASK.md §6은 "#7 행 추가"로 명시. EXECUTE는 **표의 실제 마지막 행 번호 + 1**을 사용하되, 캡틴이 "#7"을 지정했으므로 #7로 기재한다 (§4 리스크 R-2). 표 본문이 #1 다음 바로 #7이 되어 번호가 비연속이 되는 점은 PM Gate에서 캡틴 확인 대상.

#### Step 7 — 재배포 + 변경이력 검증

코드 변경 없음. Step 1~5의 `opal/` 하위 변경 파일을 `~/.opal/`로 재배포한다 (→ D-7 §install_opal_references `install-mac.sh:1148-1158`, §skills 복사 `:893-901`). `.opal/AGENT.md`(Step 6)는 배포 대상 아님(프로젝트 설정).

재배포 명령 (mac):

```bash
bash scripts/install-mac.sh   # 메뉴 [1] OPAL 설치 선택 → references + skills 전체 재복사
```

> install.sh / install.ps1(타 플랫폼)은 동일하게 디렉토리 전체를 복사하는 구조라 개별 파일 등록 지점이 없음 → 코드 수정 불요. 각 플랫폼 사용자가 자기 install 스크립트를 재실행하면 자동 반영.

---

## 3. 실행 체크리스트

> 총 7개 Step | Phase 4개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 순차 | §8 SSOT 본문 — 나머지가 §8 번호에 의존 |
> | 2 | 2, 3, 4, 5, 6 | 병렬 | 서로 다른 파일, §8 확정 후 독립 |
> | 3 | 7 | 순차 | 모든 편집 완료 후 재배포 |

### Step 1: citation-rules.md §8 신설 + 변경이력

- [x] 완료
- **파일**: `opal/core/references/harness/citation-rules.md`
- **작업 내용**: §7 끝(`:322`) 다음 / 변경이력(`:324`) 앞에 §2 핵심설계 Step 1의 §8 초안(8.1~8.5)을 삽입. 변경이력 테이블(`:329`) 끝에 v2.1 행 추가. 8.3/8.4 예시의 `path/to/file:line`은 일반 플레이스홀더 유지(특정 코드 고정 금지).
- **완료 기준**: §8 섹션이 §7과 변경이력 사이에 위치 / 8.1~8.5 하위절 모두 존재 / 핵심 명제·자연어 변환 표·조건·코드 근거 분리 표·[MUST] 블록 포함 / 변경이력 v2.1 행 존재
- **테스트**: `grep -n "## 8. 비즈니스 용어 우선" citation-rules.md` 1건 / `grep "v2.1.*024" citation-rules.md` 1건
- **의존**: 없음

### Step 2: network-guide.md §7-0 공통 작성 원칙 블록

- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/references/network-guide.md`
- **작업 내용**: §7 인트로(`:296`) 직후 / 7-1(`:298`) 앞에 §2 핵심설계 Step 2의 §7-0 블록 삽입. citation-rules §8을 참조만 하고 본문 재서술 금지.
- **완료 기준**: §7-0 블록이 §7 인트로와 7-1 사이에 위치 / [MUST] 1줄 + §8 참조 링크 포함 / 7-1~7-4 본문은 변경 없음
- **테스트**: `grep -n "7-0. 공통 작성 원칙" network-guide.md` 1건 / §8 참조 문자열 존재
- **의존**: Step 1 (§8 섹션 번호 확정값 사용)

### Step 3: consistency-rules.md §3.1 + §6 절차 1줄

- [x] 완료
- **파일**: `opal/skills/opal-pilot-write-tech/references/consistency-rules.md`
- **작업 내용**: §3 끝(`:143`)에 §3.1 비즈니스 용어 우선 검증 절(3개 체크 항목 표) 추가 + §6 QA 절차 5단계(`:202`) 직후 5-1 단계 1줄 추가.
- **완료 기준**: §3.1 절 + 체크 표 3행 존재 / §6 절차에 §3.1 순회 단계 1줄 존재 / 본문은 citation-rules §8 참조만 (재서술 없음)
- **테스트**: `grep -n "3.1 비즈니스 용어 우선 검증" consistency-rules.md` 1건
- **의존**: Step 1

### Step 4: op-brain-ingest/SKILL.md STEP 4 불릿 + 변경이력

- [x] 완료
- **파일**: `opal/skills/op-brain-ingest/SKILL.md`
- **작업 내용**: STEP 4 "코드 참조" 불릿(`:86`) 직후 "비즈니스 용어 우선" 불릿 1줄 추가 + 변경이력 v1.1(`:241`) 다음 v1.2 행 추가.
- **완료 기준**: STEP 4 작성 규칙에 비즈니스 용어 불릿 존재(§8 참조 포함) / 변경이력 v1.2 행 존재
- **테스트**: `grep -n "비즈니스 용어 우선" SKILL.md` 1건 / `grep "v1.2.*024" SKILL.md` 1건
- **의존**: Step 1

### Step 5: opal-doc-standard.md 정책서 행 포인터 + 변경이력

- [x] 완료
- **파일**: `opal/core/references/opal-doc-standard.md`
- **작업 내용**: §3 범용 표 정책서 행(`:52`) 비고를 "비즈니스 규칙 — 본문은 비즈니스 용어 우선 (… `citation-rules.md` §8)"로 보강 + 변경이력 v2.1(`:154`) 다음 v2.2 행(3컬럼) 추가.
- **완료 기준**: 정책서 행 비고에 §8 포인터 존재 / 변경이력 v2.2 행 존재 / 작성자 컬럼 없는 3컬럼 형식 준수
- **테스트**: `grep -n "정책서.*citation-rules.*§8" opal-doc-standard.md` 1건 / `grep "v2.2.*024" opal-doc-standard.md` 1건
- **의존**: Step 1

### Step 6: .opal/AGENT.md 확정 기준 행 추가

- [x] 완료
- **파일**: `.opal/AGENT.md`
- **작업 내용**: 확정 기준 표 마지막 행(`:73`) 다음에 TASK.md §6 원문을 원칙 컬럼으로 한 행 추가. 행 번호는 #7(캡틴 지정), 확정일 2026-06-16, 맥락 "TASK 024 — citation-rules §8 SSOT 등록".
- **완료 기준**: 확정 기준 표에 비즈니스 용어 우선 원칙 행 존재 / TASK.md §6 원문과 일치 / 배포 대상 아님(install 불요)
- **테스트**: `grep -n "코드는 SSOT 근거이지 본문 서술의 주어가 아니다" .opal/AGENT.md` 1건
- **의존**: Step 1 (§8 등록 사실을 맥락에 인용)

### Step 7: 재배포 + 변경이력 검증

- [ ] 완료
- **파일**: `scripts/install-mac.sh` (재실행, 코드 변경 없음)
- **작업 내용**: Step 1~5 편집 완료 후 `bash scripts/install-mac.sh` 메뉴 [1] 실행하여 references + skills 재배포. 배포 후 `~/.opal/references/harness/citation-rules.md`에 §8이 반영되었는지 확인.
- **완료 기준**: `~/.opal/references/harness/citation-rules.md`에 §8 존재 / `~/.opal/skills/opal-pilot-write-tech/references/network-guide.md`에 §7-0 존재 / 5개 수정 문서 모두 변경이력 행 추가됨
- **테스트**: `grep -c "## 8. 비즈니스 용어 우선" ~/.opal/references/harness/citation-rules.md` = 1
- **의존**: Step 1~6 전체

---

## 4. QA 체크리스트 + 설계 피드백

### 기능 테스트

- [x] R-1: citation-rules.md §8이 신설되고 (코드 식별자 본문 주어 금지 / 자연어 변환 예시 / 조건·코드 근거 표 분리 / 핵심 명제 / 변경이력) 5요소를 모두 포함하는가
- [x] R-2: network-guide.md §7-0 공통 작성 원칙이 §8을 참조하고 7-1~7-4 4개 프롬프트에 공통 적용되는가
- [x] R-3: consistency-rules.md §3.1 검증 절 + §6 절차 연결이 존재하는가
- [x] R-4: op-brain-ingest STEP 4에 비즈니스 용어 불릿 + 변경이력이 추가되었는가
- [x] R-5: opal-doc-standard.md 정책서 행 포인터 + 변경이력이 추가되었는가
- [x] R-6: .opal/AGENT.md 확정 기준에 TASK.md §6 원문 행이 추가되었는가
- [ ] R-7: install-mac.sh 재실행으로 5개 문서가 `~/.opal/`에 반영되었는가

### 일관성 테스트

- [x] 원칙 **본문**은 citation-rules §8 1곳에만 존재하고, R-2~R-5는 모두 "§8 참조"만 하는가 (재서술 0건 — SSOT 단일화, TASK.md §5)
- [x] §8을 참조하는 모든 포인터의 섹션 번호가 "§8"로 일치하는가 (참조 깨짐 0건)
- [x] 변경이력 행이 수정 문서 5개(citation-rules / network-guide·consistency-rules는 변경이력 표 없음 확인 / op-brain-ingest / opal-doc-standard)에 빠짐없이 추가되었는가 — **주의: network-guide.md·consistency-rules.md는 변경이력 테이블이 없음** (§4 리스크 R-3)

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [x] 변경이력 행 형식이 각 문서의 기존 컬럼 스키마와 일치하는가 (opal-doc-standard·citation-rules는 작성자 컬럼 없음)
- [x] §8 예시의 코드 경로가 특정 코드에 고정되지 않은 플레이스홀더인가

### 설계 피드백 (점검 결과)

| 항목 | 점검 | 결론 |
|------|------|------|
| **SSOT 중복 위험** | §8 본문 외에 R-2~R-5가 원칙을 재서술하는지 | 회피 — 모두 "§8 참조" 포인터만. network-guide는 §7-0 1블록으로 4곳 중복도 제거 |
| **§7과 §8 주제 중복** | citation-rules §7(영역 간 토큰 불일치)과 §8(본문 용어 우선)이 겹치는지 | 무겹침 — §7=토큰 일치 검출(FE↔BE 등), §8=본문 서술 시 용어 우선. 차원 다름 |
| **변경이력 누락 위험** | 5개 수정 문서 중 변경이력 표가 없는 파일 | network-guide.md·consistency-rules.md는 **변경이력 테이블이 없음** → 이 두 파일은 변경이력 행 추가 불가. TASK.md §5 "수정 문서 각각 변경이력 행"과 충돌 → 리스크 R-3 |
| **배포 누락 위험** | 5개 문서가 install로 실제 복사되는지 | references·skills 전체 디렉토리 복사라 자동 반영. install.sh/ps1 코드 수정 불요 |
| **확정 기준 행 번호** | TASK.md "#7" vs 실제 표 #1만 존재 | 비연속 번호(#1 → #7) 발생 → 리스크 R-2, PM Gate 확인 대상 |

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R-1 | §8 섹션 번호가 citation-rules 향후 개정으로 바뀌면 R-2~R-5 포인터가 깨짐 | 참조 무효화 | 포인터를 "§8 비즈니스 용어 우선 원칙"처럼 **번호 + 제목** 병기로 작성하여 제목으로 재탐색 가능하게 함 (본 PLAN 초안 반영됨) |
| R-2 | TASK.md §6은 "#7 행"인데 `.opal/AGENT.md` 확정 기준 표에 실제로 #1 행만 존재 → 번호 비연속(#1 → #7) | 표 가독성/일관성 저하 | EXECUTE는 캡틴 지정대로 #7로 기재하되, PM Gate에서 캡틴에게 "#2로 정정할지" 확인. **에이전트 자율 변경 금지** — 캡틴 결정 사안 |
| R-3 | network-guide.md·consistency-rules.md에 변경이력 테이블이 없어 "수정 문서 각각 변경이력 행 추가"(TASK.md §5) 충족 불가 | 변경이력 추적 누락 | 두 파일은 변경이력 표가 원래 없으므로 신규 표 추가는 과잉 — **태스크 DONE.md에 두 파일 변경 사실을 기록**하는 것으로 추적성 확보. PM Gate에서 캡틴 확인 |
| R-4 | install 재실행 시 사용자 데이터(community-skills 등) 영향 | 데이터 손실 우려 | install-mac.sh v2.0(`:17`)에서 community-skills는 clean_dirs에서 제외(사용자 데이터 보존) — references/skills만 재복사되므로 안전 |
| R-5 | §8 자연어 변환 예시에 실제 코드 식별자(`autoSelCancelYn` 등) 사용 시, 특정 프로젝트 코드에 결합 | 범용성 저하 | 예시는 "변환 패턴 설명용"으로만 사용하고 코드 근거 컬럼은 `path/to/file:line` 플레이스홀더 유지 (본 PLAN 초안 반영됨) |
