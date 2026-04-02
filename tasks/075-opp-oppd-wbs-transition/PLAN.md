# PLAN: oppd ROADMAP → WBS 전환

> 작성일: 2026-04-02
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd 스킬 본체 (Phase 2 ROADMAP 참조 전체) | ✅ |
| `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | 현재 로드맵 가이드 | ✅ (삭제 후 wbs-guide.md 신규 생성) |
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | 자동 검증 루핑 전략 (ROADMAP.md 참조 9곳) | ✅ |
| `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 병렬 실행 전략 (ROADMAP.md 참조 6곳) | ✅ |
| `opal/core/references/opal-harness.md` | 하네스 공통 인프라 | ❌ (ROADMAP 키워드 없음) |
| `opal/core/references/opal-skills-registry.json` | 스킬 레지스트리 (oppd description에 "ROADMAP" 포함) | ✅ |
| `opal/skills/opal-project-init/SKILL.md` | opi 스킬 (예시 텍스트에 roadmap.md 언급) | ❌ (예시 텍스트일 뿐, 실제 참조 아님) |

### 현재 상태

1. **oppd SKILL.md**: Phase 2를 "2-ROADMAP"으로, 산출물을 `docs/ROADMAP.md`로 정의. 약 30곳에서 `ROADMAP` 키워드 사용. Phase 흐름은 `PLAN → ROADMAP → EXECUTE`.
2. **roadmap-guide.md**: 206줄. 태스크 분할 원칙, 액션 구조, 스킬 판단 기준, 로드맵 구조(`docs/ROADMAP.md` 템플릿), PM 검수 체크리스트 등 포함. **액션 테이블에 `상태`/`완료일시` 컬럼 없음**. Work Package 계층 없이 플랫 액션 목록만 존재.
3. **verification-loop-guide.md**: `ROADMAP.md`를 9곳에서 참조 (검증 명령 소스, E2E 조건 등).
4. **parallel-execution-guide.md**: `ROADMAP.md`를 6곳에서 참조 (그래프 구축, 병렬 그룹, 충돌 검사 등).
5. **opal-harness.md**: ROADMAP 키워드 없음. 변경 불필요.
6. **opal-skills-registry.json**: oppd 설명에 `opwt→ROADMAP→opd/opds 순차 실행` 포함.

### 영향 범위

- **직접 영향**: oppd 스킬 및 하위 참조 문서 6개 파일
- **간접 영향**: oppd를 사용하는 프로젝트의 기존 `docs/ROADMAP.md` → 기존 프로젝트는 이 태스크 스코프 밖 (신규 프로젝트부터 적용)
- **WBS 신규 개념 도입**: Work Package 계층, 액션 상태/완료일시, `--wbs` 플래그
- **STATE.md 경량화**: 액션 진행 추적이 WBS로 이동하므로, STATE.md의 "로드맵" 테이블에서 액션 상태 추적 중복 제거

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | WBS 수립 가이드 (roadmap-guide.md 대체) |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 2 | `opal/skills/opal-pilot-project-dev/SKILL.md` | ROADMAP → WBS 전환 (Phase 2 명칭, 산출물, 참조, 프로세스, STATE 템플릿, `--wbs` 플래그) |
| 3 | `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | `ROADMAP.md` → `WBS.md` 참조 전환 (9곳) |
| 4 | `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | `ROADMAP.md` → `WBS.md` 참조 전환 (6곳) |
| 5 | `opal/core/references/opal-skills-registry.json` | oppd description의 `ROADMAP` → `WBS` 전환 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| 6 | `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | wbs-guide.md로 대체 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | WBS 가이드 작성 (핵심 문서) | wbs-guide.md (신규) | 높음 |
| 2 | oppd SKILL.md WBS 전환 | SKILL.md | 높음 |
| 3 | verification-loop-guide.md 참조 전환 | verification-loop-guide.md | 낮음 |
| 4 | parallel-execution-guide.md 참조 전환 | parallel-execution-guide.md | 낮음 |
| 5 | 스킬 레지스트리 전환 | opal-skills-registry.json | 낮음 |
| 6 | roadmap-guide.md 삭제 | roadmap-guide.md | 낮음 |

### 핵심 설계

#### 1. wbs-guide.md (신규 — roadmap-guide.md 대체)

roadmap-guide.md를 기반으로 하되, 다음을 변경:

**명칭 전환**:
- "로드맵" → "WBS(Work Breakdown Structure)"
- `docs/ROADMAP.md` → `docs/WBS.md`
- `# ROADMAP: {프로젝트명}` → `# WBS: {프로젝트명}`

**Work Package 계층 도입**:
현재 플랫 액션 목록(`A01`, `A02`, ...)을 **Work Package → Action 2단계 계층**으로 변환.

```markdown
## Work Package 구조

| WP | Work Package | 설명 | 포함 액션 |
|----|-------------|------|----------|
| WP1 | 기본 구조 | 프로젝트 초기 셋업 | A01 |
| WP2 | 데이터 레이어 | DB 스키마 + 모델 + 인증 | A02, A03 |
| WP3 | API 레이어 | 핵심 API + 비즈니스 로직 | A04, A05 |
| WP4 | UI 레이어 | 메인 화면 + UX | A06 |
```

Work Package는 마일스톤과 1:1이 아닌 **작업 분류** 단위. 기존 마일스톤 섹션은 그대로 유지.

**액션 테이블에 `상태`, `완료일시` 컬럼 추가**:

```markdown
## 액션 목록

| # | WP | 액션 | 설명 | 스킬 | 의존성 | 실행 | 우선순위 | 검증 명령 | PRD 매핑 | 상태 | 완료일시 |
|---|-----|------|------|------|--------|------|---------|----------|----------|------|---------|
| A01 | WP1 | 기본 구조 | ... | //opds | - | 순차 | Must | ... | - | 미시작 | - |
```

**상태 값 열거형**: `미시작` / `진행 중` / `완료` / `실패` / `스킵`

**사용자 확정 후 후속 조치 체크** 섹션 갱신:
- `ROADMAP.md` → `WBS.md`
- `3-ROADMAP` → `2-WBS`

#### 2. oppd SKILL.md 전환

**Phase 명칭 변경**:
- `PLAN → ROADMAP → EXECUTE` → `PLAN → WBS → EXECUTE`
- `2-ROADMAP` → `2-WBS`
- `Phase 2: 로드맵 수립` → `Phase 2: WBS 수립`

**산출물 변경**:
- `docs/ROADMAP.md` → `docs/WBS.md` (모든 참조)

**참조 변경**:
- `references/roadmap-guide.md` → `references/wbs-guide.md`

**STATE.md 템플릿 변경**:
- Phase 진행 현황 테이블: `2-ROADMAP | PM 직접 | docs/ROADMAP.md` → `2-WBS | PM 직접 | docs/WBS.md`
- "로드맵" 섹션을 "WBS 액션 현황" 등으로 리네이밍. 다만, 액션 상태 추적은 WBS.md가 담당하므로 STATE.md의 로드맵 테이블에서 `상태` 컬럼을 제거하고 WBS.md를 참조하도록 변경.

**STATE.md 경량화** (액션 진행 추적 중복 정리):
- STATE.md의 "로드맵" 테이블: 액션 목록은 유지하되 `상태` 컬럼 제거. WBS.md가 액션 단위 상태를 관리.
- STATE.md는 Phase 레벨 상태 + 의사결정 로그 + 블로커 + 검증 루프 로그에 집중.

**`--wbs` 플래그 지원**:
- SKILL.md 상단 또는 "사전 조건 체크" 부근에 `--wbs` 플래그 설명 추가.
- `--wbs` 플래그가 있으면 Phase 1(PRD/TRD) + Phase 2(WBS) 완료 후 파이프라인 종료.
- 사용자 확정 보고에서 "Phase 3 실행 없이 종료" 명시.

**DONE.md 템플릿**: `docs/ROADMAP.md` → `docs/WBS.md`.

**문서 등록 프로토콜**: `docs/ROADMAP.md` → `docs/WBS.md`.

**보고 메시지**: `[ROADMAP]` → `[WBS]`.

**변경이력**: 새 버전 추가.

#### 3. verification-loop-guide.md

`ROADMAP.md`를 `WBS.md`로 일괄 치환 (9곳). `roadmap-guide.md` 참조를 `wbs-guide.md`로 치환 (1곳).

#### 4. parallel-execution-guide.md

`ROADMAP.md`를 `WBS.md`로 일괄 치환 (5곳). `ROADMAP 수립` → `WBS 수립` 치환 (1곳).

#### 5. opal-skills-registry.json

oppd description: `opwt→ROADMAP→opd/opds 순차 실행` → `opwt→WBS→opd/opds 순차 실행`.

#### 6. roadmap-guide.md 삭제

wbs-guide.md 생성 확인 후 삭제.

---

## 3. 실행 체크리스트

> 총 6개 Step

### Step 1: wbs-guide.md 작성

- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` (신규)
- **작업 내용**:
  - roadmap-guide.md의 전체 내용을 기반으로 WBS 가이드 작성
  - "로드맵" → "WBS" 명칭 전환 (제목, 본문, 참조 전부)
  - `docs/ROADMAP.md` → `docs/WBS.md` 전환
  - `# ROADMAP:` → `# WBS:` 전환
  - Work Package 계층 구조 섹션 추가 (WP 테이블 + WP → Action 관계 정의)
  - 액션 테이블에 `WP`, `상태`, `완료일시` 컬럼 추가
  - 상태 열거형 정의: `미시작` / `진행 중` / `완료` / `실패` / `스킵`
  - 완료일시 형식: `YYYY-MM-DD HH:mm` (KST)
  - "사용자 확정 후 후속 조치 체크"에서 `ROADMAP.md` → `WBS.md`, `3-ROADMAP` → `2-WBS`
- **완료 기준**: wbs-guide.md가 존재하고, ROADMAP 키워드가 0건이며, Work Package 계층 + 상태/완료일시 컬럼이 액션 테이블에 포함
- **테스트**: `grep -c ROADMAP wbs-guide.md` → 0 / Work Package 섹션 존재 확인 / 액션 테이블에 `상태`, `완료일시` 컬럼 존재 확인
- **의존**: 없음

### Step 2: oppd SKILL.md WBS 전환

- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/SKILL.md`
- **작업 내용**:
  - Phase 명칭: `PLAN → ROADMAP → EXECUTE` → `PLAN → WBS → EXECUTE`
  - Phase 라벨: `2-ROADMAP` → `2-WBS`
  - 섹션 제목: `Phase 2: 로드맵 수립` → `Phase 2: WBS 수립`
  - 산출물: `docs/ROADMAP.md` → `docs/WBS.md` (모든 곳)
  - 참조: `references/roadmap-guide.md` → `references/wbs-guide.md`
  - 보고 메시지: `[ROADMAP]` → `[WBS]`
  - STATE.md 템플릿: `2-ROADMAP` → `2-WBS`, `docs/ROADMAP.md` → `docs/WBS.md`, "로드맵 (Phase 2 확정 후)" → "WBS 액션 (Phase 2 확정 후)", 로드맵 테이블에서 `상태` 컬럼 제거 (WBS.md가 담당)
  - DONE.md 템플릿: `docs/ROADMAP.md` → `docs/WBS.md`
  - 문서 등록 프로토콜: `docs/ROADMAP.md` → `docs/WBS.md`
  - `--wbs` 플래그: 파이프라인 섹션 및 사전 조건 체크 부근에 `--wbs` 설명 추가 — Phase 1~2까지만 실행 후 종료
  - Phase 3 실행 루프: `ROADMAP.actions` → `WBS.actions`, `ROADMAP.md에서 추출` → `WBS.md에서 추출`
  - Agentic Mode: `Phase 2 (ROADMAP)` → `Phase 2 (WBS)`
  - description (YAML frontmatter): `로드맵 수립` → `WBS 수립` (해당 시)
  - 변경이력에 새 버전 추가
- **완료 기준**: SKILL.md 내 `ROADMAP` 키워드 0건 (변경이력 설명 제외). `--wbs` 플래그 설명이 존재. `2-WBS` Phase가 정의됨.
- **테스트**: `grep -c ROADMAP SKILL.md` → 변경이력 행만 잔존 확인 / `--wbs` 검색 1건 이상 / `2-WBS` 검색 존재
- **의존**: Step 1

### Step 3: verification-loop-guide.md 참조 전환

- [x] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md`
- **작업 내용**:
  - `ROADMAP.md` → `WBS.md` 일괄 치환 (9곳)
  - `roadmap-guide.md` → `wbs-guide.md` 치환 (1곳, 495번 줄 부근)
- **완료 기준**: 파일 내 `ROADMAP` 키워드 0건
- **테스트**: `grep -ci ROADMAP verification-loop-guide.md` → 0
- **의존**: 없음

### Step 4: parallel-execution-guide.md 참조 전환

- [ ] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md`
- **작업 내용**:
  - `ROADMAP.md` → `WBS.md` 일괄 치환 (5곳)
  - `ROADMAP 수립(Phase 2)` → `WBS 수립(Phase 2)` 치환 (1곳, 126번 줄)
- **완료 기준**: 파일 내 `ROADMAP` 키워드 0건
- **테스트**: `grep -ci ROADMAP parallel-execution-guide.md` → 0
- **의존**: 없음

### Step 5: opal-skills-registry.json 전환

- [ ] 완료
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**:
  - oppd 항목의 description: `opwt→ROADMAP→opd/opds 순차 실행` → `opwt→WBS→opd/opds 순차 실행`
- **완료 기준**: JSON 파싱 에러 없음. oppd description에 `WBS` 포함.
- **테스트**: `python3 -c "import json; json.load(open('file'))"` 성공 / `grep "WBS" opal-skills-registry.json` 존재
- **의존**: 없음

### Step 6: roadmap-guide.md 삭제

- [ ] 완료
- **파일**: `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` (삭제)
- **작업 내용**:
  - wbs-guide.md 존재 확인 후 roadmap-guide.md 삭제
- **완료 기준**: roadmap-guide.md 미존재. wbs-guide.md 존재.
- **테스트**: `ls references/` 에서 roadmap-guide.md 없음, wbs-guide.md 있음 확인
- **의존**: Step 1

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] `ROADMAP.md` → `WBS.md` 리네이밍이 모든 파일에서 완료되었는가
- [ ] WBS 액션 테이블에 `상태`, `완료일시` 컬럼이 추가되었는가
- [ ] WBS 구조에 Work Package 계층이 도입되었는가 (WP → Action 2단계)
- [ ] oppd SKILL.md 내 모든 ROADMAP 참조가 WBS로 전환되었는가
- [ ] `references/wbs-guide.md`가 생성되고 `roadmap-guide.md`가 삭제되었는가
- [ ] STATE.md 템플릿에서 액션 진행 추적 중복이 정리되었는가 (WBS가 액션 상태 담당)
- [ ] opal-harness.md 내 ROADMAP 참조 확인 완료 (변경 불필요 확인)
- [ ] Phase 3 실행 루프에서 WBS 기반으로 액션을 읽도록 반영되었는가
- [ ] `--wbs` 플래그가 Phase 1~2까지만 실행 후 종료하도록 정의되었는가

### 일관성 테스트

- [ ] `opal/` 디렉토리 전체에서 `grep -r ROADMAP` 시 변경이력 설명 외에 잔존 참조 없음
- [ ] verification-loop-guide.md, parallel-execution-guide.md에서 `WBS.md` 참조가 올바른가
- [ ] opal-skills-registry.json이 유효한 JSON인가
- [ ] STATE.md 템플릿과 SKILL.md의 Phase 명칭이 일치하는가 (`2-WBS`)
- [ ] wbs-guide.md 내 액션 테이블 컬럼이 SKILL.md의 2-4 사용자 확정 보고 테이블과 일치하는가

### 문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가 (`wbs-guide.md`)
- [ ] wbs-guide.md에 WBS 구조, Work Package 계층, 상태 열거형, PM 검수 체크리스트가 포함되어 있는가
- [ ] 변경이력이 갱신되었는가 (SKILL.md)

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 기존 oppd 프로젝트의 `docs/ROADMAP.md` 호환성 | 진행 중인 프로젝트에서 ROADMAP.md → WBS.md 미그레이션 필요 | 이 태스크는 스킬 정의만 변경. 기존 프로젝트 마이그레이션은 별도 태스크로 관리. SKILL.md에 마이그레이션 노트 추가 고려. |
| ROADMAP 키워드 누락 전환 | 일부 참조가 잔존하여 참조 오류 발생 | QA 체크리스트에 전체 grep 검증 포함. Step 완료 시마다 검증. |
| Work Package 계층 과도한 복잡도 | 소규모 프로젝트에서 불필요한 오버헤드 | WP 계층은 선택적 사용으로 정의. 액션이 5개 미만이면 WP 생략 가능하도록 가이드에 명시. |
| `--wbs` 플래그 파서 충돌 | 기존 플래그(`--agentic`)와의 조합 문제 | 플래그 조합 가능하도록 정의 (`--wbs --agentic` 허용). SKILL.md에 조합 규칙 명시. |
