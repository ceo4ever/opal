# ADD_DONE-1: SKILL.md §2 컨텍스트 흡수 보강

> 추가작업 번호: ADD-1
> 시작: 2026-05-08 13:13 (KST)
> 완료: 2026-05-08 13:31 (KST)
> 적용 스킬: opp (interactive)

---

## 1. 사유

본 태스크 EXECUTE/QA 통과 후 캡틴 후속 검토에서 **두 시나리오의 자동화 수준 한계**가 확인되었다:

1. **프로젝트에서 그냥 호출 (시나리오 1)**: 현재 §2는 `docs/` 문서만 흡수하므로, `docs/`가 비어있는 프로젝트에서는 사실상 인터뷰 의존
2. **소스 코드 자체 미스캔**: `package.json` 등 의존성 매니페스트, 디렉토리 구조, OPAL `code-scan.json` 등 코드베이스 메타가 §2 흡수 대상에서 누락됨

캡틴 지시: **본 태스크 안에서 보강 완성**. CLOSE 단계 재진입(추가작업 프로세스, harness/additional-work.md)으로 처리.

## 2. 변경 내용

### 2.1 SKILL.md §2 구조 재편

기존 평면 표 1개 → 3개 하위 절(§2-1 / §2-2 / §2-3)로 분리:

- **§2-1 환경별 흡수 (1차)**: 기존 표 그대로 (OPAL 프로젝트 + 태스크 폴더 / OPAL 프로젝트 / 비-OPAL 3행)
- **§2-2 코드베이스 흡수 (모든 환경, 신규)**:
  - `.opal/code-scan.json` 연동 — `code-scan scan/domain/layer/exports` 출력 활용
  - 의존성 매니페스트 — `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`, `pom.xml`, `build.gradle` 중 존재하는 것
  - 디렉토리 트리 — `find . -maxdepth 3 -type d` (`node_modules`, `.git` 제외)
- **§2-3 추론 통지 규칙**: 기존 1줄 통지 문구 분리

### 2.2 우선순위 정책 추가

§2-2 끝에 명시: "2-1 환경별 흡수가 우선. 2-2는 보강용. 충돌 시 2-1을 신뢰하고 2-2는 chips·세부 노드 보강에만 사용."

## 3. 변경 파일

| 종류 | 경로 | 변경 |
|------|------|------|
| 수정 | `skills/system-architecture-html/SKILL.md` | §2 (line ~72-83 → ~72-100) 구조 재편 + 표 1개 신규 (3행) + 우선순위 정책 1줄 |
| 신규 | `tasks/135-260507-opp-system-arch-html-skill-port/ADD_DONE-1.md` | 본 문서 |

## 4. 영향 범위

### 영향 받지 않는 항목

- frontmatter `description` / `triggers`: 무수정 (호출 매칭 패턴 동일)
- §0 호출 환경: 무수정
- §1 환경 감지: 무수정 (환경 판정 로직 동일)
- §3 Interview / §4 Draft / §5 Save and present: 무수정 (입력 품질만 향상)
- references/ 4파일 (template.html / design-system.md / copywriting.md / examples.md): 무수정
- `opal-skills-registry.json` 등록 항목: 무수정 (alias `html-sa`, 트리거, paths 동일)

### 영향 받는 항목 (긍정적)

- 시나리오 1 자동화 수준 ↑: `docs/`가 비어있어도 의존성 매니페스트와 디렉토리 트리에서 보강 추론 가능
- OPAL 프로젝트에서 `code-scan.json`이 있는 경우 도메인·레이어·exports 메타 자동 활용
- 인터뷰 분량 추가 절감 (기술 스택 chips 자동 채움)

## 5. 검증 결과

**QA Gate 통과 (2026-05-08 14:00, op-task-qa)**

- AC 충족 결과:
  - [x] SKILL.md §2가 §2-1/§2-2/§2-3 구조로 분리됨 (라인 76, 84, 94)
  - [x] §2-2에 `code-scan.json` 행 존재 (라인 86-88, `code-scan domain/layer/exports` 언급)
  - [x] §2-2에 의존성 매니페스트 행 존재 (라인 89-91, package.json/pyproject.toml/requirements.txt/go.mod/Cargo.toml/pom.xml/build.gradle 언급)
  - [x] §2-2에 디렉토리 트리 행 존재 (라인 92-93, `find . -maxdepth 3 -type d` + node_modules/.git 제외 명시)
  - [x] §2-2 끝에 우선순위 정책 1줄 명시 (라인 92-93 후, "2-1이 우선, 2-2는 보강용" blockquote)
  - [x] 다른 섹션(§0/§1/§3/§4/§5) 무수정 (grep 확인: "## 0. 호출 환경" ~ "## Reference files")
  - [x] frontmatter 무수정 (name, description, license 확인)
  - [x] references/ 4파일 무수정 (template.html / design-system.md / copywriting.md / examples.md, 타임스탐프 2026-05-07 10:50)
  - [x] YAML frontmatter 파싱 통과 (라인 1-13 구조 정상)
  - [x] `~/.opal/` 무수정 (R-7 메모리 규칙, ADD-1 기간 2026-05-08 13:13~13:31 내 ~/.opal/ 변경 0건)

**판정: Pass** — `tasks/135-260507-opp-system-arch-html-skill-port/QA-ADD_DONE-1.md` 참조

## 6. 인용

- 추가작업 절차 SSOT: `~/.opal/references/harness/additional-work.md`
- 본 태스크 산출물: `tasks/135-260507-opp-system-arch-html-skill-port/{TASK,PLAN,DONE}.md`
- 대상 스킬: `skills/system-architecture-html/SKILL.md` (Override Step 1 결과 — standalone 위치)
- 메모리 규칙: `.opal/memory/feedback_deploy_boundary.md`
