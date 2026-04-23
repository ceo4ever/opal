---
name: op-dev-execute
description: |
  **코드 실행 단계 스킬**. 오케스트레이터가 지정한 체크리스트를 따라 실제 코드를 작성하고 검증한다. 에이전트 이름 매핑으로 specialist/generalist 가이드를 자동 선택한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe)가 EXECUTE 단계를 디스패치할 때.
  필수 입력: checklist_source (경로 + 섹션, 오케스트레이터 지정). 보장 출력: 코드 변경 + changed_files.
version: 2.0
---

# op-dev-execute — 코드 실행

## 실행 컨텍스트

- **호출자**: 오케스트레이터(opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe)가 EXECUTE 단계를 디스패치
- **실행 주체**: 워커 에이전트 — 에이전트 이름 → 매핑 테이블 → 실행 가이드 자동 선택. 폴백: agent 필드 없음 / 미지정 에이전트 → generalist 가이드.
- **입력**: `checklist_source` (오케스트레이터가 경로+섹션 지정)
  - `PLAN.md` §4 실행 체크리스트 (기능 중심 구조, 기본)
  - 폴백: `PLAN.md` §3 실행 체크리스트 (과거 형식)
  - Wireframe UI: wireframe.md 기반 실행 항목
- **출력**: 코드 변경 + `changed_files` 목록
- **페르소나 처리**: 선택된 가이드(specialist/generalist)에 위임한다

## 프로세스

### Step 1. 실행 가이드 선택 및 로딩

본 에이전트 이름을 확인 → 아래 매핑 테이블 조회 → 두 파일 Read:

| 에이전트 | Read 대상 |
|---------|---------|
| opal-fe-agent, opal-be-agent, opal-db-agent | references/execute-guide.md + references/execute-specialist-guide.md |
| opal-task-agent (범용) | references/execute-guide.md + references/execute-generalist-guide.md |
| 기타 / 미지정 | references/execute-guide.md + references/execute-generalist-guide.md (폴백) |

> **에이전트별 자동 가이드 선택**: 가이드의 금지 행동, 보안 가드레일, 실행 모드별 동작, 페르소나 처리를 숙지한다.

### Step 2. 체크리스트 확인

오케스트레이터가 지정한 `checklist_source`에서 실행 항목을 파악한다.

**입력 우선순위**:
1. `PLAN.md §4` 실행 체크리스트 (기능 중심 구조, F-NNN 소속 기능 포함) — 기본 입력
2. 폴백: `PLAN.md §3` 실행 체크리스트 (과거 형식 PLAN.md)
3. 폴백: `execution-plan.json` (과거 태스크에 json만 있는 경우)

**PLAN.md에 §2·§3 기능별 섹션이 없는 경우 (과거 태스크)**:
- §3 실행 체크리스트가 있으면 그대로 실행
- execution-plan.json이 있으면 기존 json 기반 실행 로직 적용
- 둘 다 없으면 블로커 보고

### Step 3. 코드 작성 및 검증

실행 모드(단순/복잡)에 따라 execute-guide.md의 절차를 따른다.

### Step 3-H. @header 작성 (code-scan 대상 확장자 파일)

파일을 생성하거나 수정할 때, 대상 확장자에 해당하면 @header를 작성/갱신한다.

**대상 확장자**: `.py .js .ts .vue .jsx .tsx .svelte .kt .kts .java .swift`  
+ 프로젝트 `.opal/code-scan.json`의 `extensions`에 추가된 확장자

**절차**:
1. `~/.opal/references/header-standard.md` Read하여 포맷 확인
2. 파일 언어에 맞는 주석 포맷으로 @header 작성/갱신
   - **생성 시**: 필수 필드 모두 작성 (`module`, `layer`, `domain`, `description`, `exports`)
   - **수정 시**: 변경된 내용에 해당하는 필드만 갱신
3. 삽입 위치: 파일 최상단 (shebang 다음 / frontmatter 다음 / 없으면 첫 줄)

### Step 4. 체크리스트 갱신

각 Step 완료 시 체크박스를 실시간 갱신한다:
PLAN.md 실행 체크리스트의 `- [ ] 완료` → `- [x] 완료`

### Step 5. QA 체크리스트 검증

모든 실행 Step 완료 후, op-dev-test-agent 호출 전에 워커가 QA 체크리스트를 자체 검증한다:
`PLAN.md` §5 QA 체크리스트 (기능 중심 구조) 또는 §4 (과거 형식)

## 가드레일

### 절대 금지

| # | 금지 행동 | 이유 |
|---|----------|------|
| 1 | PLAN.md에 없는 파일 생성/수정 | 계획 밖 변경은 추적 불가 |
| 2 | 설계(클래스 구조, 함수 시그니처, DB 스키마)를 임의로 변경 | PLAN에서 QA를 통과한 설계를 무효화 |
| 3 | 다른 영역 침범 (FE 워커가 BE 파일 수정, 또는 그 반대) | 병렬 실행 시 충돌 발생 |
| 4 | PLAN에 명시되지 않은 패키지 설치 | 의존성 변경은 사전 승인 필요 |
| 5 | 환경변수/시크릿을 소스 코드에 하드코딩 | 보안 위반 |

### 보안 가드레일

| # | 패턴 | 감지 방법 | 조치 |
|---|------|----------|------|
| 1 | 하드코딩 시크릿 | `password=`, `secret=`, `api_key=` 리터럴 값 | 환경변수로 교체 제안 |
| 2 | SQL Injection 취약점 | f-string/문자열 연결로 SQL 구성 | 파라미터 바인딩으로 교체 제안 |
| 3 | 민감 파일 커밋 위험 | `.env`, `credentials.*` 파일 생성 시 `.gitignore` 미포함 | `.gitignore` 추가 제안 |
| 4 | 무제한 입력 | 사용자 입력을 검증 없이 DB/파일시스템에 전달 | 입력 검증 추가 제안 |

## 실행 모드

### 단순 모드 (Simple)

워커가 Step 순서대로 직접 실행한다.

```
Step 1 → Step 2 → ... → Step N → QA 체크리스트 → 결과 반환
```

### 복잡 모드 (Complex)

워커 내부에서 Part C 토폴로지에 따라 서브 에이전트를 배치하여 병렬 실행한다.

```
Batch 1: [Agent-1, Agent-2 병렬] → Batch 2: [Agent-3] → ... → QA 체크리스트 → 결과 반환
```

## PLAN.md 기반 실행

PLAN.md §4 실행 체크리스트를 기반으로:

1. `§4.1 Phase 그룹핑`에 따라 Phase별 실행
2. Phase 내 독립 Step은 병렬 또는 순차 실행 (토폴로지 판단)
3. 각 Step의 `depends_on`(또는 **의존** 필드)을 확인하여 선행 작업 완료 여부 검증
4. FE/BE 세부 실행 순서는 선택된 실행 가이드(specialist 또는 generalist)의 절차를 따른다

**execution-plan.json 사용 안 함**: 새 태스크에서는 PLAN.md §4·§3.N.2를 직접 읽는다. 과거 태스크의 json 파일은 폴백으로만 참조.

## 블로커 처리

블로커가 발생하면:

1. **즉시 중단** -- 추측으로 해결하지 않는다
2. **사용자 보고**:
   - Step 번호와 제목
   - 구체적 에러/상황
   - 가능한 원인
   - 해결 방안 제안
3. **사용자 지시 대기** -- 지시에 따라 재개 또는 건너뛰기

## 결과 반환

워커는 op-dev-test-agent를 직접 호출하지 않는다. 실행이 완료되면 결과를 오케스트레이터에 반환한다.

**반환 형식**:
```json
{
  "artifact_path": "tasks/{NNN}-{태스크명}/",
  "summary": "{실행 요약}",
  "status": "complete | blocked",
  "blockers": [],
  "changed_files": ["파일1", "파일2"]
}
```

## EXECUTE 품질 체크리스트

- [ ] 모든 Step 체크박스가 [x] 또는 사용자 승인으로 건너뛰어졌는가
- [ ] 각 Step의 테스트 기준이 통과되었는가
- [ ] 블로커 발생 시 사용자에게 보고되었는가
- [ ] 변경 파일 목록이 PLAN.md의 파일 목록과 일치하는가
- [ ] 코드가 프로젝트 컨벤션을 따르는가
- [ ] QA 체크리스트 체크박스가 갱신되었는가
- [ ] PLAN.md에 없는 파일을 생성/수정하지 않았는가
- [ ] 하드코딩 시크릿이 없는가
- [ ] FE/BE 영역 간 침범이 없는가 (병렬 실행 시)

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | - | 초기 작성 |
| v1.1 | 2026-04-12 | Step 3-H @header 작성 규칙 추가 — code-scan 대상 확장자 파일 생성/수정 시 워커 @header 작성 의무 (109) |
| v1.2 | 2026-04-13 13:48 | PLAN.md 기반 실행 전환 — 입력 우선순위를 "PLAN.md §4 > §3 > json 폴백"으로 변경, execution-plan.json 기반 실행 섹션을 PLAN.md §4·§3.N.2 기능 루프 기반으로 재작성, FE 역할 분담의 ui-designer 호출 방법을 "PLAN.md §3.N.2 FE 화면 설계 참조"로 변경, 가드레일·품질 체크리스트에서 json 참조를 PLAN.md로 통일, 과거 태스크 폴백 규칙 서술 (114) |
| v1.3 | 2026-04-15 | 실행 주체에 전문 에이전트 체계 안내 추가 — PM이 agents.md 매핑 기반 에이전트 선택 (117) |
| v2.0 | 2026-04-23 11:39 | 3구획 구조 전환 — references/ 에 execute-specialist-guide.md / execute-generalist-guide.md 신설, SKILL.md에 에이전트 이름 매핑 테이블 삽입, 페르소나/FE 역할 분담/FE·BE MCP 테이블 섹션을 범용 가이드로 이관, 실행 컨텍스트·Step 1·PLAN.md 기반 실행 섹션 재작성 (129) |
