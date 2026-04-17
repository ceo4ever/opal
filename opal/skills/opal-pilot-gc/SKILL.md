---
name: opal-pilot-gc
description: |
  **경량 Pilot — 코드 컨벤션·보안 체크 오케스트레이터**. 커밋 전 보안·컨벤션 검사를 5단계 파이프라인으로 수행한다.
  반드시 이 스킬을 사용해야 하는 상황: "opal-pilot-gc", "opgc", "gc", "//opgc", "//gc", "garbage collection", "보안 체크", "컨벤션 체크".
  약어: opgc | 별칭: gc
---

# opal-pilot-gc (경량 Pilot — GC 오케스트레이터)

## Harness

모드: GC (SCAN → CHECK → REPORT → APPLY → CLOSE)

> 부트스트랩에서 로드되지 않은 경우: `~/.opal/references/opal-harness.md`를 Read한다.

**[MUST]** 스킬 시작 즉시 모드에 따라 서브 하네스를 Read한다:
- `--agentic` 플래그 있음 → `~/.opal/references/opal-harness-agentic.md`를 Read한다
- `--agentic` 없음 (기본) → `~/.opal/references/opal-harness-interactive.md`를 Read한다

---

## Arguments 파싱

```
//opgc                          # 전체 체크 (기본: staged 범위, APPLY 승인 대기)
//opgc --only security          # 보안만 (opal-convention-checker 디스패치 생략)
//opgc --only convention        # 컨벤션만 (opal-security-checker 디스패치 생략)
//opgc --scope staged           # 스테이징된 변경분 (기본)
//opgc --scope all              # 프로젝트 전체
//opgc --apply                  # REPORT 후 바로 APPLY (사용자 승인 생략)
//opgc --agentic                # Agentic Mode (자율 실행 — CLOSE 진입 게이트만 유지)
```

| Arguments | 기본값 | 설명 |
|---------|------|------|
| `--only security` | - | 보안 체크만 실행 |
| `--only convention` | - | 컨벤션 체크만 실행 |
| `--scope staged` | ✅ 기본 | git staged 파일 대상 |
| `--scope all` | - | 프로젝트 전체 파일 대상 |
| `--apply` | - | REPORT 완료 후 자동 APPLY |
| `--agentic` | - | Agentic Mode 활성화 |

---

## 태스크 폴더 자동 생성 규칙

```
tasks/{NNN}-{YYMMDD}-opgc-{short-summary}/
  ├── STATE.md                        # 파이프라인 상태 + 실행 요약 테이블 (허브)
  ├── GC-SECURITY-{타임스탬프}.md     # 보안 보고서 (체크리스트 내장, 자기완결)
  ├── GC-CONVENTION-{타임스탬프}.md   # 컨벤션 보고서 (체크리스트 내장, 자기완결)
  └── DONE.md                         # CLOSE 단계 완료 문서
```

`short-summary` 자동 생성 규칙:
- 기본: `staged` 또는 `all`
- `--only security`: `{scope}-sec-only`
- `--only convention`: `{scope}-conv-only`
- `--apply`: `{scope}-apply`
- 예: `tasks/NNN-260417-opgc-staged-apply/`

`NNN`: `.opal/MEMORY.md`의 `last_task_number` + 1로 채번. SCAN 단계에서 즉시 갱신.

---

## STEP 1: SCAN

**목적**: 대상 파일 선별, 기술 스택 감지, 기준 문서 로드, STATE.md 생성

### 1.1 범위 파싱 및 파일 선별

```bash
# --scope staged (기본)
git diff --name-only --staged

# --scope all
git ls-files
```

### 1.2 기술 스택 감지

다음 파일 존재 여부 확인:
- `package.json` → Node.js/React/Vue/Next/Express
- `requirements.txt` / `pyproject.toml` → Python/Django/Flask/FastAPI
- `go.mod` → Go
- `pom.xml` / `build.gradle` → Java/Spring Boot
- `Cargo.toml` → Rust

### 1.3 기준 문서 로드 확인

- `docs/SECURITY.md` 존재 여부 확인 (존재 → opal-security-checker에 경로 전달, 부재 → 플래그 설정)
- `docs/CONVENTIONS.md` 존재 여부 확인 (존재 → opal-convention-checker에 경로 전달, 부재 → 플래그 설정)

### 1.4 STATE.md 생성

태스크 폴더 생성 + STATE.md 초기화 (§STATE.md 도메인 치환값 참조).

**산출물**: STATE.md 갱신

**게이트**: 없음 (자동 진행)

---

## STEP 2: CHECK

**목적**: opal-security-checker + opal-convention-checker 병렬 디스패치

### 2.1 에이전트 병렬 디스패치

`--only` 플래그 없으면 두 에이전트를 동시에 디스패치한다.

**병렬 디스패치 프롬프트 템플릿** (각 에이전트에 전달):

```
[WORKER]

당신은 opal-{security|convention}-checker 에이전트입니다.
~/.opal/agents/opal-{security|convention}-checker/AGENT.md를 Read하고 프로세스를 따르세요.

## 핵심 제약 (Guards)
- [MUST] ~/ .opal/ 경로 파일 직접 수정 금지
- [MUST] 커밋 금지 (git commit 호출 금지)
- [MUST] 커뮤니티 스킬 원본 수정 금지 — Read 래핑만
- [MUST] docs/SECURITY.md (또는 docs/CONVENTIONS.md) 자동 갱신 금지

## 입력 파라미터
- task_folder: {task_folder}
- target_files: {파일 목록}
- timestamp: {ts}
- checklist_path: ~/.opal/skills/opal-pilot-gc/references/base-{security|convention}-checklist.md
- template_path: ~/.opal/skills/opal-pilot-gc/references/report-{security|convention}-template.md
- project_root: {project_root}
- apply_mode: {manual|auto}
- docs/SECURITY.md 존재: {true|false}      # 보안 에이전트만
- docs/CONVENTIONS.md 존재: {true|false}   # 컨벤션 에이전트만

## 참조 문서 경로
- docs/CONVENTIONS.md (컨벤션 에이전트 유일 기준)
- docs/SECURITY.md (보안 에이전트 계층 2)
- docs/ARCHITECTURE.md (시스템 구조 참조)
```

### 2.2 완료 확인 게이트

두 에이전트(또는 선택된 에이전트)의 `status: completed` 확인.

**산출물**: 각 에이전트 보고서 임시 결과 (STATE 로그)

**게이트**: 워커 완료 확인

---

## STEP 3: REPORT

**목적**: 에이전트 결과 수합, 빈도/심각도 트리거 감지, STATE.md 요약 테이블 갱신

### 3.1 결과 수합

각 에이전트가 생성한 보고서 파일 확인:
- `{task_folder}/GC-SECURITY-{ts}.md`
- `{task_folder}/GC-CONVENTION-{ts}.md`

### 3.2 빈도 분석 상수

```
FREQ_THRESHOLD = 3  # 파일 수 기준 (향후 --freq-threshold로 오버라이드 가능성은 있으나 이번 구현 범위 아님)
```

### 3.3 트리거 감지 (독립 판정)

```
// 빈도 트리거 (N=3, 파일 수 기준)
동일 fingerprint가 FREQ_THRESHOLD개 이상 파일 → "[빈도 트리거]" 제안 생성

// 심각도 트리거 (Critical 또는 High — 빈도 트리거와 완전 독립 판정)
Critical 또는 High 이슈 1건 이상 → "[심각도 트리거]" 제안 생성
// 두 트리거는 별개 §4 항목으로 분리 표기한다

// 새 카테고리 트리거
기존 CONVENTIONS.md/SECURITY.md에 없는 카테고리 → "[새 카테고리 트리거]" 제안 생성
```

### 3.4 STATE.md 실행 요약 테이블 갱신

```markdown
## 이번 실행 요약

| 에이전트 | 총 이슈 | Critical | High | 적용 완료 | 실패 | 확인 필요 | 보류 | 문서 제안 | 보고서 |
|----------|--------|----------|------|----------|------|----------|------|----------|--------|
| security | 12 | 1 | 3 | 7 | 1 | 2 | 2 | 2건 | [→](./GC-SECURITY-{ts}.md) |
| convention | 27 | 0 | 0 | 25 | 0 | 1 | 1 | 1건 | [→](./GC-CONVENTION-{ts}.md) |
| **합계** | 39 | 1 | 3 | 32 | 1 | 3 | 3 | 3건 | - |
```

**산출물**: `GC-SECURITY-{ts}.md`, `GC-CONVENTION-{ts}.md`, STATE.md 갱신

**게이트**: 사용자 확인 (기본) 또는 `--apply` 자동 진행

보고 형식:
```
📋 [REPORT] 완료 — opal-pilot-gc

📎 보안 보고서: GC-SECURITY-{ts}.md (Critical {N} / High {N} / 총 {N}건)
📎 컨벤션 보고서: GC-CONVENTION-{ts}.md (총 {N}건)
📎 문서 업데이트 제안: {N}건

APPLY 단계로 넘어갈까요? (--apply 플래그 없으면 대기)
```

---

## STEP 4: APPLY

**목적**: 보고서 체크리스트 순회, 자동 판정, 문서 업데이트 제안 승인 UX

### 4.1 실행 모드

| 모드 | 동작 |
|------|------|
| **기본** (--apply 없음) | REPORT 후 사용자 승인 대기 → 승인 시 APPLY |
| **--apply** | REPORT 완료 즉시 APPLY 자동 실행 |

### 4.2 자동 판정 알고리즘

각 이슈 순회:
1. 사용자가 직전 세션에서 보류 지시 → `[~] pending` + 보류 사유 주석
2. auto_fixable == false + 명확한 fix_hint → `[?] review` + 해결 방안 주석
3. auto_fixable == false + 판단 모호 → `[?] review` + 판단 근거 주석
4. auto_fixable == true + 수정 성공 → `[x] done` + 적용 시각 주석
5. auto_fixable == true + 수정 실패 → `[!] failed` + 실패 사유/권장 주석

**롤백 방안 (3-tier stash)**:

```bash
# Tier 1: 파일 단위 즉시 롤백
git stash push --keep-index -- {file}  # 수정 전
# 검증 실패 시:
git stash pop

# Tier 2: 세션 진입 전 전역 스냅샷
git stash push --keep-index --include-untracked -m "gc-session-{ts}"
# 세션 abort 시 이 stash로 복원

# Tier 3: 커밋 분리 금지
# GC는 커밋 생성하지 않는다 (하네스 §1 커밋 규칙)
# git commit / git reset 절대 호출 금지
```

### 4.3 문서 업데이트 제안 승인 UX

```
[GC — 문서 업데이트 제안 승인]

다음 {N}건의 제안이 있습니다:

  [1] [빈도 트리거] CONVENTIONS.md §5 "Import 순서 규칙" 신설 제안
      근거: 4개 파일에서 import 순서 위반 (빈도 트리거 N=3)

  [2] [심각도 트리거] SECURITY.md §3 "하드코딩 시크릿 금지" 추가 제안
      근거: Critical 이슈 2건 발견 (심각도 트리거 — 빈도 트리거와 독립)

승인할 번호를 입력하세요:
  - 번호 나열: 1,2  (쉼표 구분)
  - 전체 승인: a
  - 전체 거부: n
  - 상세 보기: d <번호>
```

문서 갱신 실행 방식: `opal-project-init` 스킬 재사용 (opi 최신화 모드 Phase 3 섹션 추가 흐름).

**[MUST]** 문서 자동 갱신 금지 — 캡틴 명시 승인 후에만 실행.

**산출물**: 보고서 체크박스/주석 갱신 (별도 LOG 파일 없음)

---

## STEP 5: CLOSE

**목적**: 실행 요약 집계, DONE.md 생성

> **[MUST] CLOSE 진입 게이트**: APPLY 단계 사용자 확인 없이는 CLOSE 진입 금지.
> (하네스 §1 Guards, TASK.md §제약조건 원문 준수)

### 5.1 DONE.md 생성

`{task_folder}/DONE.md` 생성 — `done-template.md` 참조:
```
~/.opal/skills/opal-pilot-gc/references/done-template.md
```

### 5.2 State Gate

하네스 §3 State Gate 참조 — STATE.md CLOSE 단계 행 `✅` 전환.

**산출물**: `DONE.md`

보고 형식:
```
✅ [CLOSE] opal-pilot-gc 실행 완료
📎 산출물: tasks/{NNN}-{ts}-opgc-{summary}/DONE.md
태스크가 완료되었습니다.
```

---

## STATE.md 도메인 치환값

| 필드 | 값 |
|------|------|
| 모드 | GC |
| 단계 목록 | SCAN / CHECK / REPORT / APPLY / CLOSE |

**파이프라인 현황판 행 구조** (STATE.md 초기 생성 시):

```markdown
| # | 단계 | 항목 | 상태 | 시점 |
|---|------|------|------|------|
| 1 | SCAN | 대상 파일 선별 + 스택 감지 | ⬜ | - |
| 2 | CHECK | 에이전트 병렬 디스패치 | ⬜ | - |
| 3 | CHECK | 에이전트 완료 확인 | ⬜ | - |
| 4 | REPORT | GC-SECURITY-{ts}.md 생성 | ⬜ | - |
| 5 | REPORT | GC-CONVENTION-{ts}.md 생성 | ⬜ | - |
| 6 | REPORT | 실행 요약 테이블 갱신 | ⬜ | - |
| 7 | REPORT | 사용자 확인 | ⬜ | - |
| 8 | APPLY | 체크박스 순회 + 자동 판정 | ⬜ | - |
| 9 | APPLY | 문서 업데이트 제안 승인 | ⬜ | - |
| 10 | APPLY | 사용자 확인 | ⬜ | - |
| 11 | CLOSE | DONE.md 생성 | ⬜ | - |
| 12 | CLOSE | State Gate | ⬜ | - |
```

**실행 요약 테이블 템플릿** (REPORT 단계에서 STATE.md에 추가):

```markdown
## 이번 실행 요약

| 에이전트 | 총 이슈 | Critical | High | 적용 완료 | 실패 | 확인 필요 | 보류 | 문서 제안 | 보고서 |
|----------|--------|----------|------|----------|------|----------|------|----------|--------|
| security | {N} | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 | [→](./GC-SECURITY-{ts}.md) |
| convention | {N} | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 | [→](./GC-CONVENTION-{ts}.md) |
| **합계** | {N} | {N} | {N} | {N} | {N} | {N} | {N} | {N}건 | - |
```

---

## Agentic Mode (--agentic 플래그)

`~/.opal/references/opal-harness-agentic.md`를 Read한다.

Agentic 모드 특수 규칙:
- **CLOSE 진입 게이트만 유지** — REPORT, APPLY의 중간 사용자 확인 게이트는 자율 통과
- `AGENTIC-LOG.md`를 태스크 폴더에 생성하여 자율 결정 내역을 기록
- 문서 업데이트 제안 승인: `--agentic` 시 **자동 승인하지 않고** 보고서 §4에 기록만 한 뒤 CLOSE 후 사용자에게 일괄 안내
- 보고서 내 `[?] review` 항목은 **건너뛰지 않고** 주석에 "agentic: 사용자 확인 필요" 표기
- CLOSE 진입 전 캡틴 확인 메시지 표시:
  ```
  [Agentic CLOSE 게이트] 자율 실행 완료. CLOSE 진입 승인? (y/n)
  ```

---

## Fingerprint 알고리즘 (설계 참조)

에이전트 내부 집계용 — 보고서 미노출:

```
fingerprint_input = "{category_id}|{normalized_tokens}"
fingerprint = sha1(fingerprint_input).hex()[:16]

정규화 순서:
1. 코드 스니펫 ±3줄 추출
2. 주석 제거
3. 문자열 리터럴 → STR
4. 숫자 리터럴 → NUM
5. 식별자 → ID (언어별 정규식 — base-security-checklist.md 참조)
6. 연속 공백 → 단일 스페이스
7. 파일 경로·라인 번호 제외
```

---

## 관련 references

| 파일 | 역할 |
|------|------|
| `references/report-security-template.md` | 보안 보고서 템플릿 |
| `references/report-convention-template.md` | 컨벤션 보고서 템플릿 |
| `references/base-security-checklist.md` | OWASP+CWE+SANS+도메인 체크리스트 |
| `references/base-convention-checklist.md` | 컨벤션 카테고리 체크리스트 |
| `references/done-template.md` | DONE.md 템플릿 |
| `references/sample-report-security.md` | 보안 샘플 보고서 (참조용) |
| `references/sample-report-convention.md` | 컨벤션 샘플 보고서 (참조용) |

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-17 | 초기 작성 — 5단계 파이프라인, arguments 파싱, STATE.md 치환값, 에이전트 병렬 디스패치, Agentic Mode, CLOSE 진입 게이트, 트리거 독립 판정, stash 롤백, fingerprint (122) |
