# ANALYSIS: 워크스페이스 Git 일괄 동기화 — git-sync-tool + opal-workspace-sync

> 작성일: 2026-07-02
> 입력: TASK.md
> 출력: ANALYSIS.md

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | 도구/스킬 배포 모델·컴포넌트 구조 정합 |
| D-2 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 네이밍·@header·배포 경계·도구 규약 |
| D-3 | 소스 | 기존 도구 (state-tool/tool-scan) | `opal/tools/state-tool/run.sh`, `opal/tools/tool-scan/run.sh` | 도구 구조·run.sh·JSON 계약 참조 패턴 |
| D-4 | 설계 | 도구 규약 | `opal/core/references/opal-harness.md §9` | OPAL Tools 호출 방식·JSON 출력 규약 |
| D-5 | 소스 | install 스크립트 | `scripts/install-mac.sh` | 신규 도구/스킬 배포 등록 |
| D-6 | 소스 | 스킬 참조 | `opal/skills/opal-brain/SKILL.md` | 유사한 operator 타입 스킬 (단계 파이프라인 없음) |

---

## 1. 기존 도구 구조 관례

### (a) `run.sh` 래퍼 구조/역할

**state-tool/tool-scan 패턴** (`state-tool:1-12`, `tool-scan:1-12`):
- `#!/bin/bash` 진입점
- 환경변수: VENV_PYTHON 설정 (선택사항 오버라이드 지원 — tool-scan은 `${OPAL_VENV_PYTHON:-...}`)
- venv 검사: `$HOME/.opal/.venv/bin/python` 존재 여부 → 없으면 JSON `{"ok":false,"error":"..."}` 반환, exit 1
- 투명 위임: `exec "$VENV_PYTHON" "$SCRIPT_DIR/{script_name}.py" "$@"` (인자 그대로 전달)

### (b) 구현 언어 및 진입점 파일

**표준**: Python (state-tool, tool-scan 모두 Python 구현)
- run.sh: Bash 래퍼만
- 실구현: `{tool-name}.py` (표준 라이브러리만 사용 — json/argparse/pathlib/sys/subprocess/re)

### (c) JSON 출력 계약

**state_tool.py:66-100**, **tool_scan.py:45-86**:
- 형식: `{"ok": boolean, "command": "subcommand", "error": "ERROR_CODE"(ok=false), "detail": "...", ...}`
- ERROR_CODES 카탈로그: 모든 에러는 dict에서만 참조 (`state_tool.py:68-100`, `tool_scan.py:45-54`)
- exit code: 0 (성공) / 1 (실패)

### (d) 디렉토리 레이아웃/테스트

구조 (`opal/tools/{tool-name}/`): run.sh + {tool}.py + (선택)lib/ + (선택)tests/
- tool-scan은 `lib/federation` 보유
- 기존 도구는 명시적 단위테스트 미존재 (TEST-SCENARIO.md 기반 검증)

**신규 git-sync-tool 따라야 할 패턴**: run.sh 래퍼 + Python 구현 + JSON 출력 규약

---

## 2. 스킬 위치·구조 관례

### (a) `skills/` vs `opal/skills/` 목록

**skills/ (독립 6개)**: api-analyzer / erd-modeler / interview / ui-designer / wireframe-builder / web-to-markdown

**opal/skills/ (OPAL 24개)**:
- 오케스트레이터: opal-pilot-dev(opd), opal-pilot-dev-short(opds), opal-pilot-project(opp) 등
- 단계 스킬: op-dev-analysis, op-dev-plan, op-dev-qa, op-task 등
- operator (멀티모드, 파이프라인 X): **opal-brain** (init/ingest/query/lint 4모드)
- OPAL 관리: opal-project-init(opi), opal-skill-creator 등

### (b) `opal-brain` 구조 (가장 유사한 템플릿)

**SKILL.md frontmatter** (`opal-brain:1-15`): name, description(트리거 포함), alias(opbr), triggers, version, domain, pipeline(`MODE: init | ingest | query | lint`)

**특징** (`opal-brain:17-43`): 단계 파이프라인 없음 / 다중 모드 선택형 / 도구 직접 호출(`~/.opal/tools/brain-tool/run.sh`) / JSON 응답 검증

### (c) opal-workspace-sync 정확한 배치 경로 및 근거

**경로**: `opal/skills/opal-workspace-sync/`

**근거**: ① 네이밍 opal 접두사=OPAL 전용(`CONVENTIONS.md:30-36`) ② opal/ 내 스킬 ③ operator 타입(파이프라인 X, opal-brain 동형) ④ install 자동 순회(`install-mac.sh:1059-1068`)

---

## 3. install 등록점

### (a) 스킬 배포 로직
- 독립 스킬: `install-mac.sh:1052-1055` — find로 `skills/` 1단계 순회
- OPAL 스킬: `install-mac.sh:1057-1068` — for 루프로 `opal/skills/*/` 순회 + strip_deploy_md_recursive

### (b) 도구 배포 로직 (`install-mac.sh:1108-1120`)
- `install_dir "$opal_dir/tools" "$opal_home/tools"` 일괄 복사
- 개별 도구 chmod +x (state-tool:1120-1124, tool-scan:1151-1155, playwright-tool:1113-1118)

### (c) 신규 등록 방식
- **도구**: `opal/tools/git-sync-tool/` 생성 → 자동 순회 배포 + install-mac.sh ~1120줄에 chmod +x 블록 추가 (별도 나열 불요, chmod만 추가)
- **스킬**: `opal/skills/opal-workspace-sync/` 생성 → 자동 순회 (명시 나열 불필요)

---

## 4. git 판정 명령 (5종 skip 사유)

| Skip 사유 | 판정 명령 | 판정 로직 |
|---------|---------|---------|
| **dirty** | `git status --porcelain` | 출력 길이 > 0 → skip |
| **no-upstream** | `git rev-parse --abbrev-ref --symbolic-full-name @{u}` | stdout="@{u}" 또는 exit != 0 → skip |
| **detached HEAD** | `git symbolic-ref -q HEAD` | exit != 0 → skip |
| **diverged** | `git rev-list --left-right --count @{u}...HEAD` | "M N"에서 M>0 AND N>0 → skip |
| **fetch-failed** | `git fetch --all --prune` | exit != 0 → skip |

**diverged 출력 해석**: "0 N"(N>0)=ahead만 / "M 0"(M>0)=behind만(ff 가능) / "M N"(둘 다>0)=diverged→skip

> 참고: `rev-list --left-right --count @{u}...HEAD`의 출력은 좌(@{u} 고유=behind)/우(HEAD 고유=ahead) 카운트다. 좌=behind, 우=ahead로 해석하며, PLAN에서 정확한 컬럼 매핑을 최종 확정한다.

**ff 판정**: clean + upstream + not detached + not diverged + behind 존재 → `git pull --ff-only` (exit 0=성공, !=0=non-ff/충돌)

**주의**: git 2.22+ 필요(`rev-list --left-right --count`), no-upstream 먼저 검사 후 diverged 판정

---

## 5. @header·컨벤션 핵심

- **@header** (`CONVENTIONS.md:170-174`): 코드 파일 상단 @header 블록. `.py`=`"""...{}"""`, `.sh`는 적용 대상 아님(`# @header: shell script — 적용 대상 아님` 주석). 필드: module/layer/domain/description/exports/depends. 실제 예 `state_tool.py:1-12`, `tool_scan.py:1-14`
- **변경이력** (`CONVENTIONS.md:91-104`): 버전(semver)/일시(YYYY-MM-DD HH:mm KST)/내용(태스크번호). install이 배포본에서 자동 strip
- **네이밍** (`CONVENTIONS.md:14-36`): kebab-case 폴더(Python은 snake_case), 스킬 `{그룹}-{역할}`
- **배포 경계** (`CONVENTIONS.md:200-203`): `~/.opal/` 직접 편집 금지 → 소스 수정 → install 재배포
- **플랫폼 분기 격리** (`CONVENTIONS.md:205-208`): 스킬·도구 본문에 플랫폼 조건문 금지

---

## 6. 중복 방지

**유사 git 순회/동기화 기능 없음** — brain-tool/code-scan/state-tool 모두 git 조작 X. grep(`git status|rev-parse|rev-list|fetch|pull`) over `opal/tools/` = 0건. → git-sync-tool + opal-workspace-sync는 완전 신규.

---

## 영향 범위

- **신규 생성**: `opal/tools/git-sync-tool/`(run.sh + git_sync_tool.py), `opal/skills/opal-workspace-sync/`(SKILL.md + references/)
- **수정**: `scripts/install-mac.sh` (git-sync-tool chmod +x 블록 ~1120줄, state-tool 패턴)
- **간접**: `~/.opal/`에 배포 (install 후), 기존 도구/스킬 영향 없음
- 요약: [ ] DB [ ] API [ ] 설정 [ ] 빌드/배포 파이프라인 (install-mac.sh 추가만)

---

## 핵심 발견 사항

1. 도구 래퍼 패턴 확정 — run.sh venv 검사 후 Python 호출 (`state-tool:1-12`, `tool-scan:1-12`)
2. JSON 계약 표준 — `{"ok", "error", ...}` (`state_tool.py:66-100`, `opal-harness.md:228-237`)
3. 스킬 위치 결정 — `opal/skills/` (operator 타입, opal-brain 동형)
4. install 등록 패턴 — 자동 순회 + 개별 도구 chmod +x (`install-mac.sh:1052-1120`)
5. operator 타입 스킬 구조 — 다중 모드 선택형 (`opal-brain:1-43`)

---

## PLAN 착수를 위한 확정 사실 요약

**git-sync-tool**: 경로 `opal/tools/git-sync-tool/` / run.sh + git_sync_tool.py / 표준 라이브러리 + git CLI(2.22+) / JSON 출력(`{"ok", "repositories":[...], "summary":{...}, "error"}`) / install 자동 순회 + chmod

**opal-workspace-sync**: 경로 `opal/skills/opal-workspace-sync/` / SKILL.md(frontmatter + 모드 라우팅) + references/ / operator 타입(opal-brain 템플릿) / 대상결정 3분기 + git-sync-tool 호출 + 5섹션 보고서 + 문제저장소 AskUserQuestion 승인 게이트 / install 자동 순회

**배포 일관성**: run.sh=state-tool ✅ / Python=tool-scan ✅ / SKILL.md=opal-brain ✅ / install=자동순회+chmod ✅

**안전성 검증 포인트**: ① git 명령 정확성 5종 skip 테스트 ② dirty/diverged 무손실 원상보존 ③ JSON 계약 ok/error/repositories

---

## 설계 피드백/리스크

**설계 빈틈**: 없음 (스킬명·구조·순회깊이·pull정책·skip 5종·보고서 5섹션 모두 TASK.md에서 잠김)

**운영 리스크**:

| 항목 | 설명 | 완화 |
|------|------|------|
| git 버전 호환 | git 2.22 미만서 `rev-list --left-right --count` 미지원 | 도구 문서에 최소 버전 명시 |
| 직속 자식만 순회 | 2단계+ 깊이 누락 | TASK.md 확정("1단계만") + 문서 명시 |
| 스킬 신설 방식 | skill-creator 권장(메모리 피드백) | `feedback_skill_creation.md` — PLAN 활용 명시 |

---

## 변경이력

| 버전 | 작성일 | 변경내용 |
|------|--------|---------|
| v1.0 | 2026-07-02 | 초기 작성 — 도구/스킬 구조 분석, 배포 모델 확인, 5종 skip 판정 명령 검증 (052) |
