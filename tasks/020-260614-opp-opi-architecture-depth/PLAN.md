# PLAN: opi 아키텍처 문서 생성 깊이 강화 (WHERE → HOW)

> 작성일: 2026-06-14
> 입력: TASK.md
> 출력: PLAN.md
> 적용 스킬: op-task-plan | 작업 유형: 개선(스킬·참조문서 .md 편집)

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opi SKILL.md | `opal/skills/opal-project-init/SKILL.md` | 수정 대상 — 초기화/최신화 Phase, 디스패치 구조, 변경이력 표 |
| D-2 | 소스 | docs-guide.md | `opal/skills/opal-project-init/references/docs-guide.md` | 수정 대상 — ARCHITECTURE/BACKEND/FRONTEND 템플릿 |
| D-3 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 변경이력·@header·배포 경계·플랫폼 분기·디스패치 의무 규칙 |
| D-4 | 설계 | PROJECT.md | `docs/PROJECT.md` | 프로젝트 원칙(플랫폼 독립·재사용성·표준화), 프로젝트 구성 섹션 |
| D-5 | 설계 | 헌법 PRINCIPLES.md | `~/.opal/PRINCIPLES.md` | §2 단순성·§3 외과적 변경·§4 동작 증거 |
| D-6 | 설계 | opgc SKILL.md | `opal/skills/opal-pilot-gc/SKILL.md` | **디스패치 선례** — PROJECT.md 프로젝트 구성 기반 영역별 워커 병렬 디스패치 + 하위호환 fallback (요구사항 C 재사용 근거) |
| D-7 | 소스(외부) | pointail/backend 자체 docs | `/Volumes/Data/StoreLinkStudio/pointail/workspace/backend/docs/` | **목표 수준 living reference** — layer-rules/transaction-patterns/cross-service/database/error-handling + domain/* + claude/services/* 구조가 "맵과 나침반" 정답지 |
| D-8 | 설계 | citation-rules.md | `~/.opal/references/harness/citation-rules.md` | 산출물 인용 포맷(문서/코드/외부/MUST) |

> 인용 형식: `citation-rules.md` §2 참조. 유형: `기획` / `설계` / `소스` / `외부`.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-project-init/SKILL.md` | opi 스킬 본문 (초기화/최신화 모드) | ✅ 수정 | `D-1:402-412`(초기화 3-1 나열), `D-1:602-639`(최신화 Step C/D 자산), `D-1:97-132`(레이아웃 탐색), `D-1:418-421`(작성 대상), `D-1:871-885`(변경이력) |
| `opal/skills/opal-project-init/references/docs-guide.md` | docs 템플릿 가이드 | ✅ 수정 | `D-2:105-145`(ARCHITECTURE WHERE만), `D-2:187-224`(BACKEND), `D-2:226-262`(FRONTEND) |
| `opal/skills/opal-project-init/references/code-analysis-guide.md` | 심층 코드 분석 공통 방법론 | 🆕 신규 | 없음 — B/E의 탐색·재대조 블록 추출 대상 |
| `docs/CONVENTIONS.md` | 프로젝트 컨벤션 | ❌ 참조만 | `D-3:194-208`(변경이력·배포 경계·플랫폼 분기) |
| `opal/skills/opal-pilot-gc/SKILL.md` | 디스패치 선례 | ❌ 참조만 | `D-6:121,138,150-156`(프로젝트 구성 기반 매트릭스 + fallback) |

### 현재 상태

**근본 원인 3개 (TASK.md `D-... 배경 분석` 확인)**:

1. **템플릿이 WHERE만** — `docs-guide.md`의 ARCHITECTURE.md 구조(`D-2:111-137`)는 시스템 구성·기술 스택 상세·개발 환경·디렉토리 트리뿐. 레이어 규칙·의존 방향·데이터 흐름·트랜잭션·상태 전이·"새 기능 추가 절차"가 없다. BACKEND.md(`D-2:206-217`)에 도메인 패턴·새 기능 가이드가 *부분적으로* 있으나 BACKEND.md는 "BE 있을 때"만 생성(`D-2:273`)되고 ARCHITECTURE보다 후순위라 대형 BE에서 HOW가 유실된다.

2. **초기화/최신화 비대칭** — 초기화 Phase 3-1(`D-1:402-412`)은 분석 항목을 **나열만** 한다. 반면 최신화 모드에는 구체적 탐색 패턴 표 Step C(`D-1:602-617`: 엔트리포인트·베이스클래스·미들웨어·설정로더·라우터·유틸)와 작성 후 코드 1:1 재대조 Step D(`D-1:619-639`)가 이미 있다. **처음 만들 때가 갱신할 때보다 얕다** — 거꾸로 된 비대칭.

3. **PM 단독 표면 훑기 + 단일레포·단일문서 전제** — opi는 PM 직접 분석·작성(`D-1:341-432`). 영역별 전문 워커 디스패치 단계가 없다. SKILL.md는 단일 ARCHITECTURE.md 1벌 전제 — 독립 git N개(우산), 단일레포 다중모듈(pointail/backend `settings.gradle.kts` 50개 모듈 × 5개 서비스) 분기가 없다. 성숙 레포의 자체 docs(pointail/backend는 L3+ 자체 docs 보유)를 흡수하는 단계도 없다.

**목표 수준 정답지 (D-7 living reference 조사 결과)**: pointail/backend는 `docs/architecture/`(layer-rules·transaction-patterns·cross-service-communication·database-architecture·error-handling·module-structure), `docs/domain/`(glossary·state-transitions·business-rules·service-boundaries), `docs/claude/services/{서비스}/`(SERVICE·business-rules·state-transitions·naming·transactions·boundaries·external-integrations·reviewer-checklist) 구조로 HOW를 **다이어그램 + 표 + 명령형 규칙 + 코드 예시 + 체크리스트** 형태로 기술한다. 이것이 opi가 산출해야 할 "맵과 나침반"의 구체적 형태다.

**재사용 가능 자산 (헌법 §2 단순성)**:
- 최신화 Step C/D(`D-1:602-639`)는 이미 검증된 심층 탐색·재대조 방법론 → **공통 블록으로 추출**하여 초기화·최신화가 모두 참조 (요구사항 B + 중복 제거).
- opgc의 "PROJECT.md 프로젝트 구성 기반 디스패치 매트릭스 + 하위호환 fallback"(`D-6:121,150-156`) → **요구사항 C의 디스패치 분기 패턴으로 재사용** (신규 발명 금지).

### 영향 범위

- `opal/skills/opal-project-init/SKILL.md`: 초기화 Phase 3, 최신화 Phase 2 Step C/D, Phase 1-1 Step A 수정 + 변경이력 행 추가. 최신화 Step C/D는 공통 블록 참조로 치환(동작 동일성 유지 필요 — 리스크 §5).
- `opal/skills/opal-project-init/references/docs-guide.md`: ARCHITECTURE/BACKEND/FRONTEND 3개 섹션 심화 + "구현 시 주입 가능 수준" 작성 기준 명문화.
- `opal/skills/opal-project-init/references/code-analysis-guide.md`: 신규 — 심층 탐색 패턴 표 + 재대조 절차 + BE/FE 스택별 체크리스트.
- **배포 경계(MUST)**: 위 3개는 모두 프로젝트 소스(`opal/`). `~/.opal/` 배포본 직접 편집 금지. EXECUTE 완료 후 `./scripts/install-mac.sh` 재배포는 **후속**(이 PLAN 범위 밖, Step에 안내만).
- **동작 영향**: opi 사용자(프로젝트 초기화 수행 시) 산출 문서 깊이 증가. 기존 프로젝트(프로젝트 구성 섹션 없는 경우) 하위호환 fallback 필수.

> **[MUST]** `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함"
> **[MUST]** `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, ...)에서 수행한다."
> **[MUST]** `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다 (행위는 플랫폼 독립적으로 기술하고, 도구명은 어댑터에 위임)."

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `opal/skills/opal-project-init/references/code-analysis-guide.md` | 심층 코드 분석 공통 방법론 — 탐색 패턴 표 + 작성 후 1:1 재대조 절차 + BE/FE 스택별 탐색 체크리스트 + 멀티레포/멀티서비스 판별 + 자체 docs 흡수 절차 | B/D/E 공통 블록 추출 (→ D-1:602-639 자산을 일반화·확장) |

> **설계 결정 — 공통 블록을 references/ 신규 파일로 추출하는 이유**: 헌법 §2 "Remove a duplicated existing pattern before introducing a new one" (`D-5` §2). 최신화 Step C/D를 초기화에 복붙(요구사항 B의 표면적 해법)하면 동일 방법론이 SKILL.md 두 곳에 중복된다. 대신 방법론을 `code-analysis-guide.md`로 추출하고, 초기화 Phase 3 / 최신화 Step C·D 양쪽이 이를 Read·참조하도록 한다. SKILL.md 본문은 "언제/어떤 산출물에" 적용하는지(분기·조건)만 남기고, "어떻게 탐색하는지"(방법론)는 가이드로 위임 — `docs-guide.md`가 docs 작성 방법을 위임받는 것과 동일한 분리 패턴(`D-1:33-34`).

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `references/docs-guide.md` | ARCHITECTURE.md 구조에 HOW 섹션군 추가(레이어 규칙·의존 방향 / 데이터 흐름(요청 생명주기) / 트랜잭션·상태 전이 / 명명 규칙 / "새 기능 추가 절차") + 멀티서비스 시 서비스별 문서 세트 안내 | A (→ D-2:111-137, D-7 layer-rules/transaction-patterns) |
| M-2 | `references/docs-guide.md` | BACKEND.md/FRONTEND.md "도메인 패턴"·"새 기능 추가 가이드" 심화 + 각 문서 "작성 규칙"에 **"구현 시 주입 가능 수준"** 기준 문장 명문화 | A (→ D-2:206-262) |
| M-3 | `SKILL.md` 초기화 Phase 3-1 | 나열형(`:402-412`)을 `code-analysis-guide.md` 참조 기반 심층 분석으로 교체 + 작성 후 코드 1:1 재대조 단계 추가 | B (→ D-1:402-412, N-1) |
| M-4 | `SKILL.md` 최신화 Phase 2 Step C/D | 탐색 패턴 표(`:606-617`)·재대조 표(`:623-639`)를 `code-analysis-guide.md` 참조로 치환 (동작 보존, 중복 제거) | B 단순성 (→ D-1:602-639, N-1) |
| M-5 | `SKILL.md` Phase 1-1 Step A + 초기화 Phase 3 / 최신화 Phase 2 | 멀티레포(독립 git N개)·멀티서비스(단일레포 다중 빌드모듈) 판별 + 영역/서비스별 문서 세트 분기 규칙 추가 | D (→ D-1:97-132, D-7 settings.gradle.kts·services/*) |
| M-6 | `SKILL.md` 초기화 Phase 1-1 / Phase 3 + 최신화 Phase 1 | 코드 디렉토리 내 자체 docs(`docs/`, `ARCHITECTURE`, `ADR/`) 탐색 → 있으면 정제·흡수(출처 추적 보존) / 없으면 직접 생성 분기 추가 | E (→ D-1:93-153,398-432, N-1) |
| M-7 | `SKILL.md` 초기화 Phase 3 / 최신화 Phase 2 | 코드 규모·디렉토리 수 임계 이상 시 영역별 전문 워커(opal-be-agent/opal-fe-agent) 디스패치 분기 + 임계 기준 + PM 종합 절차. 소형이면 PM 직접(폴백) | C (→ D-1:398-432, D-6:121,150-156 재사용) |
| M-8 | `SKILL.md` 변경이력 표 | v4.2 행 추가 (`YYYY-MM-DD HH:mm` KST + 태스크번호 (020)) | MUST (→ D-1:871-885, D-3:194-197) |
| M-9 | `references/docs-guide.md` 하단 | 변경이력 표 추가 또는 갱신 (현재 변경이력 표 부재 — `D-2` 전체에 없음) | MUST (→ D-3:194-197) |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | 없음 | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 공통 분석 방법론 가이드 신규 작성 (다른 변경의 참조 기반) | N-1 code-analysis-guide.md | 상 |
| 2 | ARCHITECTURE/BACKEND/FRONTEND 템플릿 심화 (독립) | M-1, M-2 docs-guide.md | 상 |
| 3 | 초기화 Phase 3 심층화 + 최신화 Step C/D 참조 치환 (N-1 의존) | M-3, M-4 SKILL.md | 중 |
| 4 | 멀티레포/멀티서비스 분기 (N-1 판별 절차 의존) | M-5 SKILL.md | 중 |
| 5 | 자체 docs 흡수 분기 (N-1 의존) | M-6 SKILL.md | 중 |
| 6 | 전문 워커 디스패치 분기 (Phase 3 구조 확정 후) | M-7 SKILL.md | 중 |
| 7 | 변경이력 갱신 | M-8 SKILL.md, M-9 docs-guide.md | 하 |
| 8 | 동작 검증 (재배포 후 opi 재실행 실증) | (검증) | 상 |

> 원칙: 의존 받는 쪽(공통 가이드 N-1)부터. SKILL.md M-3~M-7은 동일 파일을 순차 수정(같은 Phase 불가 — `plan-guide.md` Phase 그룹핑 규칙 3).

### 핵심 설계

#### N-1. `code-analysis-guide.md` 신규 (공통 분석 방법론)

심층 코드 분석을 SKILL.md 본문에서 분리한 단일 진실 원천. 4개 블록으로 구성:

1. **블록 1 — 심층 탐색 패턴 표**: 기존 최신화 Step C 표(`D-1:606-617`: 엔트리포인트·베이스클래스/상속·미들웨어/인터셉터·설정로더·라우터/컨트롤러·공유유틸)를 그대로 이전 + HOW 추출 항목 확장(레이어 경계·의존 방향, 트랜잭션 경계, 상태 전이/enum, 도메인 패턴, 새 기능 추가 경로). 각 행은 "탐색 패턴(행위) → 추출 정보 → ARCHITECTURE/BACKEND 어느 슬롯에 매핑되는가"를 명시.
2. **블록 2 — BE/FE 스택별 탐색 체크리스트**: BE(레이어/포트-어댑터·트랜잭션 매니저·도메인 경계·예외 체계), FE(라우팅·상태관리·컴포넌트 분리·API 클라이언트). pointail/backend D-7 구조를 정답지로 행위 기술 (`[MUST]` 플랫폼 독립 — 도구명 금지).
3. **블록 3 — 작성 후 코드 1:1 재대조 절차**: 기존 Step D 표(`D-1:623-639`) + 4분류(일치/불일치/문서에없음/실제에없음, `D-1:634-638`)를 이전. "HOW 섹션이 코드 근거 없이 추측으로 채워지지 않았는지"를 재대조하는 항목 추가 (헌법 §4 동작 증거 — HOW도 실측 기반).
4. **블록 4 — 레포 구조 판별 + 자체 docs 흡수**: 멀티레포(독립 `.git` N개)·멀티서비스(단일레포 다중 빌드모듈: `settings.gradle.kts`/`nx.json`/워크스페이스 등) 판별 행위 + 코드 디렉토리 내 자체 docs 탐색 행위 + 흡수 시 출처 추적 보존 규칙("어느 원본 docs §에서 흡수했는지 기재").

> **[MUST]** 플랫폼 독립 (`D-3` §플랫폼 분기 격리 / `D-1:615`): 모든 탐색은 도구명이 아닌 행위(파일 탐색·패턴 검색)로 기술한다.

#### M-1/M-2. `docs-guide.md` 템플릿 심화 (요구사항 A)

ARCHITECTURE.md "구조"(`D-2:111-137`)에 기존 WHERE 섹션 **뒤에** HOW 섹션군을 필수로 추가 (D-7 living reference 매핑):

| 신규 HOW 섹션 | 담을 내용 | D-7 정답지 |
|--------------|----------|-----------|
| `## 레이어 규칙 및 의존 방향` | 레이어 정의 + 레이어별 책임 + **의존 방향 규칙(무엇이 무엇을 참조 가능/금지)** + 다이어그램 | layer-rules.md |
| `## 데이터 흐름 (요청 생명주기)` | 요청 진입 → 레이어 통과 → 응답까지의 경로 + 핵심 컴포넌트 | error-handling/layer-rules |
| `## 트랜잭션 · 상태 전이` | 트랜잭션 경계·매니저 선택 규칙 + 상태 enum/전이 패턴 | transaction-patterns.md, state-transitions.md |
| `## 명명 규칙 (구조 차원)` | 레이어/모듈/엔티티 접두사 규칙 (CONVENTIONS와 구분: 여기는 구조적 명명) | naming(service)/glossary |
| `## 새 기능 추가 절차` | "새 도메인/API/화면을 추가하려면" step-by-step 경로 | reviewer-checklist/SERVICE.md |

BACKEND.md "도메인 패턴"(`D-2:206-217`)·FRONTEND.md를 위 깊이로 강화. 각 문서 "작성 규칙"에 작성 기준 문장 명문화:

> **[MUST] 작성 기준 문구 (A의 AC 핵심)**: "각 HOW 섹션은 *구현 시 주입 가능 수준*으로 작성한다 — 이 문서만 읽고 해당 프로젝트 규약대로 새 도메인/API/화면을 구현할 수 있어야 한다. 추상적 서술('적절히 분리한다') 금지, 실제 코드에서 추출한 규칙·경로·패턴(예시 코드/표 포함)으로 기술한다." (근거: TASK.md `:9,:35`, `D-5` §4)

> **멀티서비스 분기 안내**(M-5 연동): ARCHITECTURE.md 구조 끝에 "단일레포 다중 서비스인 경우, 공통 HOW는 ARCHITECTURE.md에 두고 서비스별 특이사항(경계·트랜잭션·명명)은 `docs/services/{서비스}/` 세트로 분기" 안내 추가 (D-7 claude/services/* 구조 반영).

#### M-3/M-4. 초기화 심층화 + 최신화 참조 치환 (요구사항 B)

- **M-3 초기화 Phase 3-1**(`D-1:402-412`): 나열을 "`code-analysis-guide.md`를 Read하여 블록 1~3을 적용한다"로 교체. 작성 후 블록 3(1:1 재대조)을 초기화에도 필수 단계로 추가 → 초기화/최신화 분석 깊이 대칭화 (B의 AC).
- **M-4 최신화 Step C/D**(`D-1:602-639`): 인라인 표를 `code-analysis-guide.md` 블록 1·3 참조로 치환. **동작 보존**(기존 표 내용이 가이드에 100% 이전됐는지 재대조 표 항목 보존 — 리스크 §5).

#### M-5. 멀티레포/멀티서비스 분기 (요구사항 D)

Phase 1-1 Step A(`D-1:97-132`)에 판별 추가, Phase 3/최신화 Phase 2 작성 대상에 분기:

| 구조 | 판별 (code-analysis-guide 블록 4) | 문서 세트 분기 |
|------|----------------------------------|--------------|
| 단일레포·단일서비스 | 코드 디렉토리 1벌, 멀티모듈 빌드파일 없음 | 기존대로 단일 ARCHITECTURE/BACKEND/FRONTEND |
| 멀티레포(우산) | 하위에 독립 `.git` N개 | 레포별 문서 세트 (`docs/{레포}/...`) 또는 레포별 docs/ |
| 멀티서비스(단일레포) | 다중 빌드모듈 + 서비스 경계 식별 (`settings.gradle.kts` 등) | 공통 ARCHITECTURE + 서비스별 `docs/services/{서비스}/` 세트 (D-7 claude/services/* 구조) |

> **[MUST] 하위호환** (`D-6:154` 패턴 차용): 멀티 구조가 아니면 기존 단일 문서 세트로 동작 — 기존 사용자 영향 0.

#### M-6. 자체 docs 흡수 분기 (요구사항 E)

Phase 1-1 분석 + Phase 3 작성 흐름에 분기:

```
코드 디렉토리 내 자체 docs 탐색 (code-analysis-guide 블록 4)
├─ 발견됨 (성숙 레포: ARCHITECTURE/ADR/docs/) → 정제·흡수 경로
│   1. 자체 docs를 Read하여 HOW 정보 추출
│   2. docs-guide.md 템플릿 슬롯에 매핑·정제
│   3. [MUST] 출처 추적 보존: "원본: {레포}/docs/{파일} §{섹션}" 기재
│   4. 코드와 재대조 (블록 3)하여 자체 docs가 stale하지 않은지 검증
└─ 빈약/없음 → 직접 생성 경로 (B/C 심층 분석으로 생성)
```

> **[MUST]** 흡수 시 출처 추적: 흡수한 내용에 원본 docs 경로·섹션을 기재한다 (E의 AC — "출처 추적 보존"). 헌법 §4: 자체 docs도 코드 재대조로 검증 (stale 문서 맹신 금지).

#### M-7. 전문 워커 디스패치 분기 (요구사항 C)

> **설계 결정 — 권고안**: opi는 "PM 직접 수행" 스킬(`D-1:30,341`). 디스패치 도입은 설계 변경이므로 **조건부 분기(임계 이상에서만)**로 제한하고, 디폴트는 직접 수행 유지. opgc의 검증된 "PROJECT.md 프로젝트 구성 기반 매트릭스 + fallback" 패턴(`D-6:121,150-156`)을 재사용한다 — 신규 디스패치 메커니즘 발명 금지(헌법 §2).
>
> **대안 평가**: (가) 직접 수행 유지 + 심층 체크리스트만 강화 = 단순하나 대형 모놀리스에서 표면 훑기 한계 잔존(원인 3 미해소). (나) 항상 디스패치 = 소형 프로젝트 오버헤드·"직접 수행" 정체성 훼손. → **(다) 임계 기반 조건부 디스패치** 채택: 소형은 직접(가의 장점), 대형은 영역별 워커(원인 3 해소).

| 항목 | 설계 |
|------|------|
| 디스패치 임계 기준 | 코드 디렉토리(영역) 수 ≥ 2 **또는** 단일 영역이라도 심층 분석 대상 디렉토리·모듈 수가 임계 초과(대형 모놀리스/멀티서비스). 구체 임계값은 EXECUTE에서 living reference 규모(50모듈) 참고해 명문화 |
| 전문 에이전트 매핑 | Backend→opal-be-agent, Frontend→opal-fe-agent (D-1:298-305 기존 매핑 테이블 재사용) |
| 디스패치 단위 | 영역/서비스 × 분석 (멀티서비스면 서비스별) — opgc 매트릭스(`D-6:166`) 패턴 |
| PM 종합 절차 | 워커는 영역별 심층 분석 결과 반환 → PM이 ARCHITECTURE(공통 HOW) 종합 + 영역간 용어 일관성 검토 + docs-guide 템플릿에 통합 작성 |
| 폴백 | 임계 미만(소형) → PM 직접 수행(기존 동작 유지) / 서브에이전트 미지원 플랫폼 → PM 직접 (`D-1` 실행 컨텍스트 원칙) |

> **[MUST] 디스패치 의무 정합** (`D-3` §디스패치 의무): 본 분기는 opi를 "조건부 디스패치 스킬"로 만든다. 임계 이상에서 디스패치를 PM 직접 수행으로 대체하지 않도록 분기 조건을 SKILL.md에 명시.
> **[MUST] 플랫폼 독립**: 디스패치는 "영역별 전문 워커에게 분석을 위임"이라는 행위로 기술 — 특정 플랫폼 서브에이전트 API에 종속하지 않는다.

#### M-8/M-9. 변경이력 (MUST)

- M-8 SKILL.md frontmatter version `4.0.0`→`4.2.0`, 변경이력 표(`D-1:871-885`)에 v4.2 행 추가.
- M-9 docs-guide.md: 현재 변경이력 표 부재 → "## 변경이력" 표 신설 + 본 변경 행 기재.

> **[MUST]** `docs/CONVENTIONS.md` §변경이력: 일시 `YYYY-MM-DD HH:mm`(KST) + semver + 태스크번호 `(020)`.

---

## 3. 실행 체크리스트

> 총 9개 Step | Phase 5개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1 | 단독 | 공통 가이드 신규 — 후속 모두의 참조 기반 |
> | 2 | 2 | 단독 | docs-guide.md 심화 (Step1과 독립이나 별 파일) |
> | 3 | 3, 4, 5, 6 | **순차** | 모두 SKILL.md 동일 파일 — 순차 필수 (plan-guide Phase 규칙 3) |
> | 4 | 7 | 순차 | 변경이력 (모든 편집 후) |
> | 5 | 8 | 순차 | 동작 검증 (재배포 후) |
>
> 영역: 본 작업은 .md 스킬·참조문서 편집 → 전 Step `opal-task-agent`(범용). 디스패치 분기 *내용 설계*는 BE/FE 지식 무관(문서 기술)하므로 전문 에이전트 불요.

### Step 1: 공통 분석 방법론 가이드 신규 작성
- [ ] 완료
- **파일**: `opal/skills/opal-project-init/references/code-analysis-guide.md` (N-1)
- **영역/에이전트**: 문서 / opal-task-agent
- **작업 내용**: 블록 1(심층 탐색 패턴 표 — 최신화 Step C `D-1:606-617` 이전 + HOW 추출 확장), 블록 2(BE/FE 스택별 탐색 체크리스트 — D-7 정답지 기반, 행위 기술), 블록 3(작성 후 1:1 재대조 절차 — Step D `D-1:623-639` + 4분류 이전 + HOW 추측 검증), 블록 4(멀티레포/멀티서비스 판별 + 자체 docs 흡수·출처 추적) 작성. 변경이력 표 포함.
- **완료 기준**: 4개 블록 모두 존재. 블록 1·3이 기존 최신화 Step C/D 내용을 누락 없이 포함(이전 시 정보 손실 0). 모든 탐색이 도구명 아닌 행위로 기술됨.
- **테스트**: 최신화 Step C 표 6행·Step D 표 8행이 블록 1·3에 1:1 대응되는지 diff 확인. 플랫폼 도구명(Glob/Grep 등) 미등장 grep 검증.
- **의존**: 없음

### Step 2: docs-guide.md 템플릿 심화 (ARCHITECTURE/BACKEND/FRONTEND)
- [ ] 완료
- **파일**: `opal/skills/opal-project-init/references/docs-guide.md` (M-1, M-2, M-9)
- **영역/에이전트**: 문서 / opal-task-agent
- **작업 내용**: ARCHITECTURE.md "구조"에 HOW 섹션 5종(레이어 규칙·의존 방향 / 데이터 흐름 / 트랜잭션·상태 전이 / 명명 규칙 / 새 기능 추가 절차) 추가 + 멀티서비스 분기 안내. BACKEND/FRONTEND "도메인 패턴"·"새 기능 가이드" 심화. 각 "작성 규칙"에 "구현 시 주입 가능 수준" 기준 문장(§2 M-2 [MUST] 문구) 추가. 변경이력 표 신설.
- **완료 기준**: ARCHITECTURE.md "구조"에 레이어·의존방향, 데이터 흐름, "새 기능 추가 절차"가 **필수 섹션**으로 존재. 각 문서 작성 규칙에 "구현 시 주입 가능 수준" 문장 존재. (A의 AC `D-...:51`)
- **테스트**: docs-guide.md에서 "새 기능 추가 절차", "의존 방향", "구현 시 주입 가능 수준" 문자열 grep 존재 확인.
- **의존**: 없음 (Step 1과 별 파일 — 병렬 가능하나 SKILL.md가 둘 다 참조하므로 먼저 확정 권장)

### Step 3: 초기화 모드 심층 분석·재대조 이식 (요구사항 B)
- [ ] 완료
- **파일**: `opal/skills/opal-project-init/SKILL.md` 초기화 Phase 3-1 (M-3)
- **영역/에이전트**: 문서 / opal-task-agent
- **작업 내용**: Phase 3-1 나열(`D-1:402-412`)을 `code-analysis-guide.md` 블록 1~3 참조 적용으로 교체. 작성 후 코드 1:1 재대조(블록 3) 단계를 초기화에 추가.
- **완료 기준**: 초기화 Phase 3에 탐색 패턴 표(또는 가이드 참조)와 작성 후 1:1 재대조 단계가 존재. (B의 AC `D-...:57`)
- **테스트**: 초기화 Phase 3에서 `code-analysis-guide.md` Read 지시 + 재대조 단계 존재 확인.
- **의존**: Step 1

### Step 4: 최신화 Step C/D 참조 치환 + 멀티레포/멀티서비스 분기 (요구사항 D)
- [ ] 완료
- **파일**: `opal/skills/opal-project-init/SKILL.md` 최신화 Step C/D + Phase 1-1 Step A + 작성 대상 (M-4, M-5)
- **영역/에이전트**: 문서 / opal-task-agent
- **작업 내용**: 최신화 Step C/D 인라인 표를 가이드 블록 1·3 참조로 치환(동작 보존). Phase 1-1 Step A에 멀티레포(독립 git N개)·멀티서비스(단일레포 다중 빌드모듈) 판별 추가. Phase 3/최신화 Phase 2 작성 대상에 영역/서비스별 문서 세트 분기 + 하위호환 fallback.
- **완료 기준**: 멀티레포·멀티서비스 양쪽 판별 + 영역/서비스별 문서 세트 분기 규칙 존재. 단일 구조 시 기존 동작 유지(fallback) 명시. 최신화 Step C/D가 가이드 참조로 치환되고 내용 손실 없음. (D의 AC `D-...:69`)
- **테스트**: 멀티레포/멀티서비스 판별 분기 grep 확인. 최신화 모드가 가이드 참조 후 기존 Step C/D와 동일 산출하는지 설계 검토.
- **의존**: Step 1, Step 3 (동일 파일 순차)

### Step 5: 레포 성숙도 분기 + 자체 docs 흡수 (요구사항 E)
- [ ] 완료
- **파일**: `opal/skills/opal-project-init/SKILL.md` 초기화 Phase 1-1/Phase 3 + 최신화 Phase 1 (M-6)
- **영역/에이전트**: 문서 / opal-task-agent
- **작업 내용**: 코드 디렉토리 내 자체 docs 탐색(가이드 블록 4) → 발견 시 정제·흡수(출처 추적 보존) / 없으면 직접 생성, 두 경로 명시 분기. 흡수분 코드 재대조 검증.
- **완료 기준**: "자체 문서 탐색 → 있으면 정제·흡수, 없으면 직접 생성" 분기 존재 + 흡수 시 출처 추적 보존 명시. (E의 AC `D-...:75`)
- **테스트**: 자체 docs 흡수 분기 + "출처" 추적 문구 grep 확인.
- **의존**: Step 1, Step 4 (동일 파일 순차)

### Step 6: 대형 코드베이스 전문 워커 디스패치 분기 (요구사항 C)
- [ ] 완료
- **파일**: `opal/skills/opal-project-init/SKILL.md` 초기화 Phase 3 / 최신화 Phase 2 (M-7)
- **영역/에이전트**: 문서 / opal-task-agent
- **작업 내용**: 코드 규모·디렉토리 수 임계 이상 시 영역별 전문 워커(opal-be-agent/opal-fe-agent) 디스패치 분기 추가. 임계 기준·에이전트 매핑(`D-1:298-305` 재사용)·PM 종합 절차·폴백(소형 직접/미지원 플랫폼 직접) 기술. opgc 매트릭스 패턴(`D-6:150-156`) 차용.
- **완료 기준**: Phase 3에 "임계 이상이면 영역별 전문 워커 디스패치" 분기 + 디스패치 기준·매핑·PM 종합 절차 존재. 디폴트 직접 수행 유지. (C의 AC `D-...:63`)
- **테스트**: 디스패치 임계 기준 + opal-be-agent/opal-fe-agent 매핑 + PM 종합 절차 + 폴백 grep 확인.
- **의존**: Step 1, Step 5 (동일 파일 순차 — Phase 3 구조 확정 후)

### Step 7: 변경이력 갱신
- [ ] 완료
- **파일**: `opal/skills/opal-project-init/SKILL.md` (M-8) + `references/docs-guide.md` (M-9, Step2 미반영 시)
- **영역/에이전트**: 문서 / opal-task-agent
- **작업 내용**: SKILL.md frontmatter version 4.0.0→4.2.0, 변경이력 표에 v4.2 행(`2026-06-14 HH:mm` + 변경 요약 + (020)) 추가. docs-guide.md 변경이력 표 확인.
- **완료 기준**: SKILL.md·docs-guide.md 변경이력 표에 본 태스크(020) 행 존재, 일시·semver·태스크번호 형식 준수. ([MUST] D-3 §변경이력)
- **테스트**: 변경이력 표에 `(020)` 행 + `4.2` 버전 존재 확인.
- **의존**: Step 2, Step 6

### Step 8: 동작 검증 — 재배포 후 opi 재실행 실증 (헌법 §4)
- [ ] 완료
- **파일**: (검증 — 소스 수정 없음)
- **영역/에이전트**: 검증 / PM 직접 (사용자 승인·관찰 필요)
- **작업 내용**: (1) `./scripts/install-mac.sh`로 `~/.opal/` 재배포 (배포 경계 — 후속). (2) 검증 대상 선정: 본 프로젝트(OPAL, BE 없음 → ARCHITECTURE HOW 섹션 채워지는지) **또는** pointail/backend류 대형 BE 샘플(자체 docs 흡수 + 멀티서비스 분기 작동). (3) 업그레이드된 opi 최신화 모드 실행 → ARCHITECTURE.md "레이어 규칙·의존 방향"·"새 기능 추가 절차"가 실제 코드 근거로 채워지는지, BACKEND가 "구현 시 주입 가능 수준"인지 관찰.
- **완료 기준**: opi 재실행 산출 ARCHITECTURE/BACKEND에 HOW 섹션이 추측 아닌 코드 근거로 채워짐을 실제 산출물로 확인. 대형 BE 샘플에서 자체 docs 흡수·서비스 분기 작동 확인. (제약 §동작검증 필수 `D-...:83`, 헌법 §4)
- **테스트**: 재실행 산출 ARCHITECTURE.md에 5종 HOW 섹션 실제 내용 존재 + 출처/근거 기재 확인. 문서 생성만으로 완료 선언 금지.
- **의존**: Step 7 (전체 편집 완료 후)

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] A: docs-guide ARCHITECTURE "구조"에 레이어·의존방향, 데이터 흐름, "새 기능 추가 절차" 필수 섹션 + 각 문서 "구현 시 주입 가능 수준" 기준 문장 존재
- [ ] B: 초기화 Phase 3에 최신화 Step C 동등 탐색 패턴 + 작성 후 1:1 재대조 단계 존재 (초기화/최신화 깊이 대칭)
- [ ] C: Phase 3에 임계 기반 영역별 전문 워커 디스패치 분기 + 기준·매핑·PM 종합 절차 + 폴백 존재
- [ ] D: 멀티레포·멀티서비스 양쪽 판별 + 영역/서비스별 문서 세트 분기 규칙 존재
- [ ] E: 자체 docs 탐색→흡수(출처 추적)/직접 생성 분기 존재
- [ ] 검증: 재배포 후 opi 재실행으로 HOW 섹션이 실제 채워짐 실증 (헌법 §4)

### 일관성 테스트
- [ ] 최신화 Step C/D를 가이드 참조로 치환 후에도 기존 산출물 동작 보존 (정보 손실 0)
- [ ] code-analysis-guide.md ↔ SKILL.md ↔ docs-guide.md 간 용어 일관 (레이어/도메인 패턴/의존 방향 명칭 통일)
- [ ] 디스패치 매핑(opal-be-agent/opal-fe-agent)이 기존 `D-1:298-305` 테이블과 일치
- [ ] 멀티서비스 문서 세트 경로 명명이 D-7 services/* 구조와 정합 (`docs/services/{서비스}/`)
- [ ] 하위호환 fallback이 모든 신규 분기(C/D/E)에 존재 — 기존 단일레포 프로젝트 동작 불변

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙 준수
- [ ] kebab-case 파일 네이밍 (`code-analysis-guide.md`)
- [ ] SKILL.md YAML frontmatter version 4.2.0 갱신
- [ ] 변경이력: SKILL.md·docs-guide.md에 `YYYY-MM-DD HH:mm`(KST)+semver+(020) 행
- [ ] 플랫폼 독립: 모든 탐색·디스패치가 도구명 아닌 행위로 기술 (`D-3` §플랫폼 분기 격리)
- [ ] 배포 경계: 수정은 `opal/` 소스만, `~/.opal/` 직접 편집 없음 (PLAN에 재배포 후속 명시됨)

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 최신화 Step C/D를 가이드로 추출 시 정보 손실 → 기존 동작 회귀 | 중 | Step 1·4 완료 기준에 "기존 표 1:1 대응 diff" 명시. Step 8 검증에서 최신화 모드 실측 |
| 디스패치 분기가 opi "직접 수행" 정체성과 충돌 | 중 | 조건부(임계 이상만) + 디폴트 직접 + 폴백 명시 (M-7 권고안). opgc 검증 패턴 재사용으로 신규 위험 최소화 |
| 템플릿 심화로 소형 프로젝트가 과도한 HOW 섹션 강제 → 빈 섹션 양산 | 중 | "구현 시 주입 가능 수준" 기준 = 코드 근거 없으면 생략 가능 명문화. 소형은 직접 수행 + 간결 |
| 디스패치 임계값 미확정 (PLAN에서 구체값 미정) | 하 | EXECUTE에서 living reference 규모(50모듈) 참고해 명문화 — Step 6 작업 내용에 포함. **decision_required** 후보 |
| 멀티서비스 문서 세트 경로 명명 미합의 (`docs/services/` vs `docs/claude/services/`) | 하 | D-7은 `docs/claude/services/`이나 OPAL 표준은 `docs/` 직속 — **decision_required**: OPAL 산출 표준 경로 확정 필요 |
| 동작 검증 대상(본 프로젝트 vs 외부 대형 BE) 접근성 | 중 | 1차 본 프로젝트(BE 없어 ARCHITECTURE HOW만 검증 가능), 2차 외부 BE 샘플 — 사용자 환경 확인 필요 |
