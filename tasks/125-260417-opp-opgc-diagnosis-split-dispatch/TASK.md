# TASK: opgc 진단 전담화 + 프로젝트 구성 표준 정립

> 작성일: 2026-04-17 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청 (대화 기반 — opgc CLI 정리, APPLY 제거, 동적 병렬 디스패치, PROJECT.md 표준)
> 출력: TASK.md

## 작업 목표

opal-pilot-gc(opgc)를 "진단 전담 Pilot"으로 재정의하고(APPLY 단계 완전 제거, 수정은 opds로 수동 체인), PROJECT.md "프로젝트 구성" 섹션을 표준으로 정립하여 CHECK 단계가 프로젝트 구성에 따라 체커를 동적으로 병렬 디스패치하도록 한다.

## 배경

opal-pilot-gc는 122번 태스크에서 신설된 경량 Pilot(SCAN → CHECK → REPORT → APPLY → CLOSE 5단계)로, 진단과 자동 수정을 한 스킬에 묶어 처리한다. 운영 과정에서 다음 3가지 구조 한계가 드러났다:

1. **역할 비대**: opgc가 진단(체크/보고서)과 수정(APPLY)을 함께 책임지면서 SKILL.md가 복잡해졌다. 반면 opds는 이미 TASK → PLAN → EXECUTE → TEST → CLOSE 파이프라인으로 "코드 수정+회귀 검증"을 처리한다. 기능이 중복된다.
2. **CLI 인지 부담**: `--only security`, `--only convention`은 토글보다 길고, `--apply`(승인 스킵)와 `--agentic`(전 게이트 자율)이 역할이 겹쳐 혼란스럽다.
3. **단일 스택 가정**: CHECK가 `opal-convention-checker` 1개 + `opal-security-checker` 1개를 고정 디스패치한다. FE/BE/Batch 등 다중 구성 프로젝트에서는 영역별 전문성과 병렬성을 살리지 못한다.

또한 에이전트 컨텍스트 주입의 기반이 될 "프로젝트 구성" 정보가 PROJECT.md 표준 섹션으로 존재하지 않아, 다른 오케스트레이터(opp, oppd 등)도 FE/BE 영역별 라우팅을 수행할 수 없는 상태다.

## 배경 분석 (대화에서 도출)

### 현재 구조 스냅샷

| 컴포넌트 | 상태 |
|---------|------|
| `opal/skills/opal-pilot-gc/SKILL.md` | v1.0, 5단계 파이프라인(SCAN/CHECK/REPORT/APPLY/CLOSE), `--only X` · `--scope staged\|all` · `--apply` · `--agentic` 4플래그, 12행 파이프라인 현황판, APPLY 섹션에 자동 판정 알고리즘 + 3-tier stash 롤백 |
| `opal/agents/opal-convention-checker/AGENT.md` | Phase 1~7 구성, Phase 6에 APPLY 알고리즘(수정 실행), tools에 Edit/Write 포함, `apply_mode` 입력 파라미터 사용 |
| `opal/agents/opal-security-checker/AGENT.md` | 동일 구조, Phase 6에 APPLY, `apply_mode` 입력 |
| `docs/PROJECT.md` | "프로젝트 개요", "프로젝트 구조", "주요 컴포넌트"는 있으나 "**프로젝트 구성**"(요소/경로/기술 스택/전문 에이전트) 표준 섹션 부재. "프로젝트 문서" 테이블에 `적용 범위` 컬럼 없음 |
| `docs/CONVENTIONS.md`, `docs/SECURITY.md` | 허브+링크 모델 미정립. 현재 OPAL 자체는 단일 문서만 존재 |
| `opal/skills/opal-project-init/SKILL.md` | 새 프로젝트 초기화 스킬. "프로젝트 구성" 표준 섹션 생성 템플릿 부재 |
| `opal/core/references/opal-pm.md` §6 / `opal/core/references/pm/context-injection.md` | 에이전트 컨텍스트 주입 문서 존재. PROJECT.md "프로젝트 구성" 기반 라우팅 규약 미반영 |
| `opal/core/references/agents.md` | `opgc` 예시 명령어 일부 포함. `--apply` / `--only X` 문법 사용 중 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` (참조) | TASK → PLAN → EXECUTE → TEST → CLOSE 5단계, 조기 에스컬레이션 규칙(요구사항 ≥ 8 등) 존재. GC 수정 체인 진입점으로 재활용 가능 |

### 설계 중복 지점

- opgc APPLY = opds EXECUTE + TEST (파일 수정 + stash + 회귀 검증)
- opgc `--agentic` = opgc `--apply` + REPORT 게이트 자율(→ `--apply`가 사실상 하위 집합)
- 컨벤션 체커의 `apply_mode` / `Edit` 권한 = opds의 `op-dev-execute` 워커와 기능 중복

## 확정된 설계 방향 (대화에서 합의)

### D-1. CLI 정리 (opgc SKILL.md)

- **제거**: `--apply` 플래그 (역할이 `--agentic`에 흡수됨)
- **교체**: `--only security` → `--security`, `--only convention` → `--convention` (A안: 토글 조합 방식. 둘 다 생략 = 기본(둘 다), 둘 다 지정 = 둘 다)
- **유지**: `--scope staged|all`, `--agentic`
- **조합 허용**: `--scope all --convention`, `--agentic --convention`, `--scope all --convention --agentic` 등 축이 다르면 자유 조합

### D-2. APPLY 단계 완전 제거

- opgc 파이프라인을 **SCAN → CHECK → REPORT → CLOSE** 4단계로 축소
- APPLY(자동 수정, stash 롤백, 문서 업데이트 제안 승인 UX) 섹션 삭제
- CLOSE 단계에서 "수정이 필요하면 `//opds "{태스크폴더} GC 결과 반영"`으로 호출" 안내 문구 추가
- opgc는 **진단+보고서 생성**까지만 담당 (코드 파일 수정 없음)

### D-3. opgc → opds 수동 체인 (A안)

- 자동 체인, 플래그 기반 체인 모두 도입하지 않음(MVP 단순화)
- opgc 보고서가 opds의 참조 문서로 자연 연결되도록 **TASK.md 골격 예시**를 opgc SKILL.md에 수록
- 예시 골격: 배경("opgc 실행 결과 N건 이슈 감지"), 참조 문서(GC-*.md), 요구사항(auto_fixable 이슈 목록), 제약(`[?] review` 제외, 회귀 금지)

### D-4. SCAN 동적 분할 병렬 디스패치

- SCAN에서 `docs/PROJECT.md`의 "**프로젝트 구성**" 섹션을 파싱
- 요소별 `경로`로 `target_files`를 분할하고, `전문 에이전트` 정보를 각 체커 호출에 참조로 주입
- CHECK에서 체커를 N회 병렬 디스패치 (요소 × 체커 유형)
- **Fallback**: 섹션 부재 시 현행 1+1 디스패치 유지 (하위호환)
- **요소 유형별 규칙** (기획 제외, 배치=BE 상속)

### D-5. 체커 에이전트 APPLY 제거

- `opal-convention-checker/AGENT.md`, `opal-security-checker/AGENT.md`의 Phase 6(APPLY) 섹션 삭제
- `apply_mode` 입력 파라미터 제거
- `tools`에서 `Edit`, `Write` 제거(Read, Grep, Glob, Bash만 유지)
- Phase 7 `changed_files`는 보고서 파일만 포함

### D-6. 체커 참조 문서 체이닝 (허브+링크 모델)

- `docs/CONVENTIONS.md`, `docs/SECURITY.md`를 **허브 문서**로 규정
- 허브 안에 영역별 상세 문서 링크 규약을 둠 (예: `FE-CONVENTIONS.md`, `BE-CONVENTIONS.md`, `BATCH.md`)
- 체커 Phase 흐름: 허브 Read → 링크 파싱 → 호출 범위(`scope`)에 매칭되는 상세 문서 Read → 체크
- "CONVENTIONS.md 유일 기준" 원칙은 **단일 진입점** 형태로 유지 (허브가 유일 진입점)

### D-7. PROJECT.md 표준 섹션 신설

- 신설 섹션 제목: `## 프로젝트 구성`
- 스키마:
  - `| 요소 | 경로 | 기술 스택 | 전문 에이전트 |`
- "프로젝트 문서" 테이블에 **`적용 범위`** 컬럼 추가 (전체 / Frontend / Backend / Batch / Mobile 등)
- 배치는 "(Backend 상속)" 표기 — 기술 스택 컬럼에서 상속 관계 선언
- OPAL 자체 프로젝트는 FE/BE 구성이 없으므로 **섹션 존재 + 단일 행(프레임워크 자체)** 또는 **표준 주석 + 예시 블록**으로 작성 (하위호환 검증용)

### D-8. opi 반영

- `opal-project-init/SKILL.md`가 신규 프로젝트 초기화 시 "프로젝트 구성" 섹션과 "프로젝트 문서" `적용 범위` 컬럼을 생성하도록 템플릿/인터뷰 갱신
- 기존 프로젝트의 opi 최신화 흐름에서도 "프로젝트 구성" 섹션 누락 감지 → 추가 제안

### D-9. opal-pm.md §6 / context-injection.md 연동

- 에이전트 컨텍스트 주입 규약에 "PROJECT.md 프로젝트 구성 기반 라우팅" 항목 추가
- 워커 디스패치 시 대상 파일의 경로와 "프로젝트 구성" 요소 경로를 매칭하여 적합한 `전문 에이전트` 참조 주입

### D-10. 주변 문서 정합화

- `opal/core/references/agents.md`의 opgc 예시 명령어에서 `--apply` / `--only X` 제거 → 신 CLI 반영
- `README.md` 내 opgc 언급이 있다면 동일 교체
- opgc SKILL.md `변경이력`에 v1.1 추가

### D-11. 허브+링크 가이드 문서

- 새 참조 문서 `opal/core/references/conventions-hub-model.md` 신설 (또는 opi references로 편입) — 허브+링크 구조, 링크 규약, FE/BE/Batch 예시
- 기존 프로젝트에는 적용 강제하지 않음 — 선택 모델

## 요구사항

### F-1. opgc CLI 축약·조합 체계 전환

- [x] **무엇을**: `--only security/convention`을 `--security` / `--convention`(토글)로 교체하고, `--apply`를 제거한다. **어디에**: `opal/skills/opal-pilot-gc/SKILL.md` "Arguments 파싱" 섹션과 Arguments 테이블. **왜**: D-1. **AC**: Arguments 파싱 블록에 `--apply`가 전혀 등장하지 않고, Arguments 테이블에 `--security` / `--convention` 2행이 존재하며 `--only`로 시작하는 행이 0개다. 조합 예시 5종 이상(`--scope all --convention`, `--agentic --convention`, `--scope all --convention --agentic` 포함)이 수록된다.

### F-2. opgc APPLY 단계 제거

- [x] **무엇을**: `## STEP 4: APPLY` 섹션 전체와 관련 기술(3-tier stash, 자동 판정 알고리즘, 문서 업데이트 제안 승인 UX)을 삭제하고, 파이프라인을 SCAN/CHECK/REPORT/CLOSE 4단계로 재번호한다. **어디에**: opgc SKILL.md. **왜**: D-2. **AC**: SKILL.md에 "APPLY" 단어가 Guards 설명 맥락(수정 금지) 외에는 등장하지 않으며, `STEP 4`가 `CLOSE`이고, 파이프라인 현황판 테이블이 8행 이하로 축소되어 SCAN/CHECK/REPORT/CLOSE만 포함한다.

### F-3. opgc → opds 수동 체인 가이드

- [x] **무엇을**: opgc CLOSE 단계에 "수정이 필요하면 `//opds "{태스크폴더} GC 결과 반영"`으로 호출" 안내와 opds용 TASK.md 골격 예시를 포함한다. **어디에**: opgc SKILL.md `STEP 4(CLOSE)`. **왜**: D-3. **AC**: CLOSE 섹션에 `//opds` 호출 예시 1개 이상과 "요구사항(auto_fixable 이슈 목록)", "참조 문서(GC-*.md)", "제약(`[?] review` 제외, 회귀 금지)"를 포함한 TASK.md 골격 블록이 존재한다.

### F-4. PROJECT.md 기반 SCAN 동적 분할 병렬 디스패치

- [x] **무엇을**: SCAN 단계에서 `docs/PROJECT.md`의 "프로젝트 구성" 섹션을 파싱하고, 요소별 `target_files`를 분할한다. CHECK 단계에서 요소 × 체커 유형 조합으로 병렬 디스패치한다. 섹션 부재 시 현행 1+1 fallback을 유지한다. **어디에**: opgc SKILL.md `STEP 1(SCAN)` 하위 신설 절 + `STEP 2(CHECK)` 디스패치 절. **왜**: D-4. **AC**: SCAN 절차에 "프로젝트 구성 섹션 파싱" 의사코드와 요소별 `target_files` 분할 표가 존재하며, CHECK 절차에 "요소 × 체커" 병렬 매트릭스 예시(단일/모노레포/FE+BE+Batch 3케이스 이상)가 있고, "섹션 부재 시 fallback" 분기가 명시된다.

### F-5. 체커 AGENT.md 두 개의 APPLY 제거

- [x] **무엇을**: `opal-convention-checker`, `opal-security-checker` AGENT.md에서 Phase 6(APPLY) 삭제, `apply_mode` 입력 파라미터 제거, `tools`에서 `Edit, Write` 제거, Phase 7 `changed_files`에 소스 파일 제거(보고서만 반환), 행동 규칙 내 "자동 갱신 금지" 문구는 유지한다. **어디에**: `opal/agents/opal-convention-checker/AGENT.md`, `opal/agents/opal-security-checker/AGENT.md`. **왜**: D-5. **AC**: 두 AGENT.md 모두 ① `Phase 6` / `APPLY` 소제목이 사라지고, ② `tools: [Read, Grep, Glob, Bash]`로 축소되며, ③ 입력 명세에 `apply_mode` 행이 없고, ④ Phase 7 반환 예시의 `changed_files`가 보고서 `*.md`만 포함한다.

### F-6. 체커 허브+링크 참조 체이닝 반영

- [x] **무엇을**: 두 체커 AGENT.md의 Phase에 "허브(CONVENTIONS.md 또는 SECURITY.md) Read → 링크 파싱 → 호출 범위(`scope`)에 매칭되는 상세 문서 Read" 절차를 반영한다. 입력 명세에 `scope` 파라미터(frontend|backend|batch|mobile|all 등)를 추가한다. **어디에**: 두 AGENT.md. **왜**: D-6. **AC**: 두 AGENT.md의 입력 명세에 `scope` 행이 있고, 실행 프로세스 Phase에 "허브 Read → 링크 파싱 → 상세 문서 Read" 흐름이 명시되며, Phase 흐름은 `check_enabled` 판정과 공존한다.

### F-7. PROJECT.md "프로젝트 구성" 섹션 + "프로젝트 문서" `적용 범위` 컬럼

- [x] **무엇을**: OPAL 자체 `docs/PROJECT.md`에 `## 프로젝트 구성` 섹션(요소/경로/기술 스택/전문 에이전트 스키마)을 신설하고, "프로젝트 문서" 테이블에 `적용 범위` 컬럼을 추가한다. OPAL 자체는 FE/BE가 없으므로 "Framework" 단일 행 또는 "해당 없음" 표기로 기입한다. **어디에**: `docs/PROJECT.md`. **왜**: D-7. **AC**: PROJECT.md에 `## 프로젝트 구성` H2 섹션이 존재하고 스키마 4컬럼이 모두 채워져 있으며, "프로젝트 문서" 테이블의 컬럼이 `문서 / 설명 / 적용 범위 / 참조 시점`으로 4개이고 모든 행의 `적용 범위` 셀이 비어있지 않다.

### F-8. opi 반영 — 신규 프로젝트 초기화 시 표준 섹션 생성

- [x] **무엇을**: `opal-project-init/SKILL.md`가 신규 프로젝트 초기화 시 "프로젝트 구성" 섹션(템플릿 + 요소 인터뷰)과 "프로젝트 문서" `적용 범위` 컬럼을 PROJECT.md에 자동 포함하도록 갱신한다. 기존 프로젝트 opi 최신화 흐름에서는 섹션 누락을 감지하여 추가 제안한다. **어디에**: `opal/skills/opal-project-init/SKILL.md`. **왜**: D-8. **AC**: opi SKILL.md에 "프로젝트 구성 섹션 생성" 단계 또는 템플릿이 명시적으로 존재하며, 최신화 흐름에 "기존 PROJECT.md에 프로젝트 구성 섹션 부재 시 추가 제안" 분기가 있다.

### F-9. opal-pm.md §6 / context-injection.md — 프로젝트 구성 기반 라우팅

- [x] **무엇을**: 워커 디스패치 시 대상 파일 경로와 "프로젝트 구성" 섹션의 요소 경로를 매칭하여 전문 에이전트를 자동 선정하는 규약을 추가한다. **어디에**: `opal/core/references/opal-pm.md` §6 요약 또는 `opal/core/references/pm/context-injection.md` 상세. **왜**: D-9. **AC**: 문서에 "PROJECT.md 프로젝트 구성 기반 라우팅" 절이 존재하고, 파일 경로 → 요소 매칭 의사코드 또는 예시 1개 이상이 포함된다.

### F-10. 주변 문서 정합화

- [x] **무엇을**: `opal/core/references/agents.md`의 opgc 예시 명령어 갱신(`--apply` 제거, `--only X` → `--X`), opgc SKILL.md 변경이력 v1.1 추가, `README.md`의 opgc 언급 검토·갱신. **어디에**: agents.md, opgc SKILL.md 변경이력, README.md(변경 필요 시). **왜**: D-10. **AC**: agents.md에 `--apply` / `--only` 문자열이 opgc 섹션에서 사라지고, opgc SKILL.md 변경이력 테이블에 v1.1 행(2026-04-17, 125)이 추가되며, README.md에서 opgc 언급이 있으면 신 CLI로 일치한다(없으면 해당 없음 기록).

### F-11. 허브+링크 가이드 문서

- [x] **무엇을**: 허브+링크 구조 가이드를 신설한다 — 허브(CONVENTIONS.md/SECURITY.md)와 영역별 상세 문서(FE/BE/Batch) 연결 규약, 링크 포맷, 예시 블록. **어디에**: `opal/core/references/conventions-hub-model.md` 신설(또는 opi references). **왜**: D-11. **AC**: 신설 문서에 ① 허브 문서의 역할, ② 링크 규약(예: `> 영역별 상세: [FE-CONVENTIONS.md](./FE-CONVENTIONS.md) — Frontend`), ③ 체커의 참조 체이닝 흐름, ④ 최소 1개 이상의 예시 블록이 포함된다.

## 제약 조건

- 하네스 Guards §1 준수: 캡틴 명시 승인 없이는 본 산출물 외 코드 파일 수정 금지, 커밋 금지(완료 후 캡틴 지시 시만)
- **하위호환**: "프로젝트 구성" 섹션이 없는 기존 프로젝트에서 opgc는 현행 1+1 단일 디스패치로 동일하게 동작해야 한다
- **`~/.opal/` 경로 직접 수정 금지**: 소스 경로(`opal/core/...`, `opal/skills/...`, `opal/agents/...`)에서만 수정. 배포는 캡틴이 `install-mac.sh`로 수행
- **커뮤니티 스킬 원본 수정 금지**: getsentry, openai 하위는 Read 래핑만
- **기준 문서 자동 갱신 금지 유지**: 체커가 `docs/CONVENTIONS.md`, `docs/SECURITY.md`를 자동 갱신하지 않는다는 원칙은 그대로 유지
- **단일 태스크 완료**: 본건은 125 하나에서 완료한다(126/127 태스크 분리 없음)
- **산출물 인용 규칙**: `opal/core/references/harness/citation-rules.md`를 준수한다(PLAN/EXECUTE 산출물 작성 시)

## 기술 스택

- Markdown (SKILL.md, AGENT.md, PROJECT.md, 가이드 문서)
- YAML frontmatter (스킬/에이전트 메타)
- Bash (opgc SCAN 단계 git 명령, OPAL tools 호출)
- Node.js (`~/.opal/tools/date/date.js` 등 OPAL tools)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-pilot-gc SKILL | `opal/skills/opal-pilot-gc/SKILL.md` | 본 개편 주 대상 — CLI/APPLY/SCAN/CHECK/CLOSE 전반 수정 |
| D-2 | 소스 | opal-convention-checker AGENT | `opal/agents/opal-convention-checker/AGENT.md` | APPLY 제거, scope 입력 추가, 허브+링크 체이닝 반영 |
| D-3 | 소스 | opal-security-checker AGENT | `opal/agents/opal-security-checker/AGENT.md` | 동일 |
| D-4 | 설계 | docs/PROJECT.md | `docs/PROJECT.md` | "프로젝트 구성" 섹션 신설 + "프로젝트 문서" 테이블 `적용 범위` 컬럼 추가 |
| D-5 | 설계 | docs/CONVENTIONS.md | `docs/CONVENTIONS.md` | 허브+링크 모델 검토 — OPAL 자체는 단일 문서라 예시/주석 수준만 |
| D-6 | 소스 | opal-project-init SKILL | `opal/skills/opal-project-init/SKILL.md` | 표준 섹션 생성 템플릿 반영 |
| D-7 | 소스 | opal-pm.md | `opal/core/references/opal-pm.md` | §6 또는 context-injection.md 연동 |
| D-8 | 소스 | context-injection.md | `opal/core/references/pm/context-injection.md` | 프로젝트 구성 기반 라우팅 규약 |
| D-9 | 소스 | agents.md | `opal/core/references/agents.md` | opgc 예시 명령어 정합화 |
| D-10 | 참조 | opal-pilot-dev-short SKILL | `opal/skills/opal-pilot-dev-short/SKILL.md` | 수동 체인 대상 파이프라인 구조 확인 |
| D-11 | 하네스 | citation-rules | `opal/core/references/harness/citation-rules.md` | 산출물 인용 규칙 준수 |
| D-12 | 하네스 | opal-harness.md | `opal/core/references/opal-harness.md` | Guards, Gates, STATE.md 규약 |
| D-13 | 하네스 | header-rules | `opal/core/references/harness/header-rules.md` | .md @header 규칙 (해당 파일에 적용 여부 판단) |
