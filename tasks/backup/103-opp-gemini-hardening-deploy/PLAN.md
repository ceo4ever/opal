# PLAN: Gemini Hardening 글로벌 배포

> 작성일: 2026-04-09
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `GEMINI.md` (프로젝트 루트) | HARDENING SSOT — `# === GEMINI HARDENING START/END ===` 마커로 감싼 v1.0 본문 (라인 10~182) | 없음 (SSOT) |
| `opal/bootstrapper/gemini-bootstrap.md` | 기존 OPAL 부트스트래퍼 소스 — ` ```markdown ... ``` ` 블록 추출 패턴 | 참조 (구조 모방) |
| `opal/bootstrapper/gemini-hardening.md` | HARDENING 소스 (신규) | 신규 생성 |
| `scripts/install-mac.sh` | macOS 인스톨러 — `install_opal_section()`, `install_opal()`, `print_summary()` | 수정 |

### 현재 상태

- **HARDENING SSOT**: 프로젝트 루트 `GEMINI.md` 라인 10~182에 `# === GEMINI HARDENING START ===` ~ `# === GEMINI HARDENING END ===` 마커 사이 본문(GUARD-1~5, 실패 보고 형식 포함)이 존재한다.
- **OPAL 마커 처리 헬퍼**: `install_opal_section()`은 `OPAL_START`/`OPAL_END` 상수에 하드코딩되어 있어 다른 마커에는 재사용 불가하다. TASK 제약("수정 금지")에 따라 동일 패턴을 복제한 신규 함수가 필요하다.
- **본문 추출**: `extract_bootstrap_content()`는 ` ```markdown ` ~ ` ``` ` 블록 사이를 추출한다. HARDENING 소스도 동일 구조를 따라야 재사용 가능하다.
- **Gemini 배포 호출 위치**: `install_opal()` 내부, `install_opal_section "$opal_dir/bootstrapper/gemini-bootstrap.md" "$USER_HOME/.gemini/GEMINI.md" "Gemini"` 직후가 신규 함수 호출 지점이다(라인 457~458).
- **설치 요약 함수**: TASK.md는 `print_installed_summary`로 표기했으나 실제 코드의 함수명은 `print_summary`다 (라인 734~780). **문서/코드 불일치 → 코드 기준 진행**.
- **요약 출력 패턴**: `print_summary()`는 마커 존재 여부(`grep -qF "$OPAL_START"`)로 한 줄을 출력한다. HARDENING 항목도 동일 패턴을 추가한다.

### 영향 범위

- 신규 파일 1개(`opal/bootstrapper/gemini-hardening.md`)와 `scripts/install-mac.sh` 단일 파일 변경.
- `~/.gemini/GEMINI.md`의 **OPAL 섹션은 비파괴**(별도 마커이므로 `install_opal_section`이 OPAL 마커만 교체).
- 기존 인스톨러 함수(`install_opal_section`)는 변경 없음 → 하위 호환 유지.
- macOS 외 배포 스크립트(있다면)는 본 태스크 범위 외.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 |
|---|----------|------|
| 1 | `opal/bootstrapper/gemini-hardening.md` | HARDENING 소스 — ` ```markdown ` 블록 안에 GEMINI HARDENING 섹션 본문 포함 |

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `scripts/install-mac.sh` | (a) `HARDENING_START`/`HARDENING_END` 상수 추가 (b) `install_gemini_hardening()` 함수 추가 — `install_opal_section()`과 동일 로직, 마커만 다름, R2 분기 제외 (c) `install_opal()` 내 Gemini OPAL 배포 직후 `install_gemini_hardening` 호출 추가 (d) `print_summary()`에 `~/.gemini/GEMINI.md HARDENING` 항목 추가 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | - | 없음 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | HARDENING 소스 파일 생성 (SSOT 복사) | `opal/bootstrapper/gemini-hardening.md` | 하 |
| 2 | 인스톨러 상수/함수/호출/요약 추가 | `scripts/install-mac.sh` | 중 |
| 3 | 로컬 검증 (dry-run + 추출 확인) | - | 하 |

### 핵심 설계

#### 1) `opal/bootstrapper/gemini-hardening.md`

`gemini-bootstrap.md`와 동일한 파일 구조를 따른다:

```
# OPAL Gemini Hardening (Antigravity)

> 사용법: 이 내용이 ~/.gemini/GEMINI.md에 GEMINI HARDENING 마커 기반으로 자동 삽입된다.
> install-mac.sh에서 OPAL 설치 시 자동 처리.
>
> 버전: v1.0 (2026-04-09)

---

아래 내용이 `~/.gemini/GEMINI.md`에 삽입된다:

---

```markdown
## 제미나이 전용 하네스 강화 (Gemini Hardening v1.0)
...(프로젝트 루트 GEMINI.md 라인 11~181 본문 그대로 복사)...
```

---

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-09 | 최초 작성 — TASK-103 글로벌 배포 (HARDENING SSOT는 프로젝트 루트 GEMINI.md) |
```

- 추출 대상은 ` ```markdown ` 블록 1개. `extract_bootstrap_content()`가 그대로 사용 가능.
- 본문에는 라인 10의 START 마커와 라인 182의 END 마커는 **포함하지 않는다** (인스톨러가 마커를 자동 삽입).
- 본문 시작 라인은 GEMINI.md의 라인 11(`## 제미나이 전용 하네스 강화 ...`)부터, 마지막 라인은 라인 181까지.

#### 2) `scripts/install-mac.sh` 변경

**(a) 상수 추가** (`OPAL_START`/`OPAL_END` 블록 직후, 라인 26 부근):

```bash
HARDENING_START="# === GEMINI HARDENING START ==="
HARDENING_END="# === GEMINI HARDENING END ==="
```

**(b) 신규 함수 `install_gemini_hardening()`** (`install_opal_section()` 정의 직후 추가, 라인 254 부근):

- `install_opal_section()`을 그대로 복제하되:
  - `$OPAL_START`/`$OPAL_END` → `$HARDENING_START`/`$HARDENING_END`
  - **R2 호환 분기 제거** (R2 시절 HARDENING은 없었음)
  - 함수 시그니처: `install_gemini_hardening <snippet> <target> <label>`
  - 로직: 새 파일이면 마커 블록 단독 작성 / 마커 존재하면 in-section 교체 / 마커 없으면 파일 끝에 추가
  - 라벨 메시지: "HARDENING 설치/업데이트/추가"

**(c) `install_opal()` 내 호출 추가** (라인 457~458 직후):

```bash
install_opal_section "$opal_dir/bootstrapper/gemini-bootstrap.md" \
    "$USER_HOME/.gemini/GEMINI.md" "Gemini"

install_gemini_hardening "$opal_dir/bootstrapper/gemini-hardening.md" \
    "$USER_HOME/.gemini/GEMINI.md" "Gemini"
```

- 동일 파일 대상이지만 OPAL 마커와 HARDENING 마커는 독립적이므로 충돌 없음.
- 호출 순서: OPAL 먼저 → HARDENING 이후 (OPAL 부트스트래퍼가 위쪽에 위치).

**(d) `print_summary()` 요약 항목 추가** (라인 769 직후):

```bash
[[ -f "$USER_HOME/.gemini/GEMINI.md" ]] && grep -qF "$HARDENING_START" "$USER_HOME/.gemini/GEMINI.md" && \
    echo "    ~/.gemini/GEMINI.md          GEMINI HARDENING"
```

- TASK.md는 함수명을 `print_installed_summary`로 표기했으나 실제 코드는 `print_summary` — **코드 기준 적용**, 보고서에 불일치 명시.

---

## 3. 실행 체크리스트

> 총 3개 Step | Phase 2개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1     | 1    | 순차 | 신규 소스 파일 생성 (의존 없음) |
> | 2     | 2    | 순차 | 인스톨러 수정 (Step 1 산출물 참조) |
> | 3     | 3    | 순차 | 검증 (Step 1, 2 산출물 모두 의존) |

### Step 1: HARDENING 소스 파일 생성

- [x] 완료
- **파일**: `opal/bootstrapper/gemini-hardening.md`
- **작업 내용**: `gemini-bootstrap.md`와 동일한 파일 구조로 신규 생성. ` ```markdown ` 블록 안에 프로젝트 루트 `GEMINI.md` 라인 11~181 본문(GEMINI HARDENING START/END 마커 라인 제외)을 그대로 복사. 헤더/사용법 안내/변경이력 포함.
- **완료 기준**: (1) 파일이 생성됨 (2) `extract_bootstrap_content opal/bootstrapper/gemini-hardening.md` 실행 시 GUARD-1~5 본문이 추출됨 (3) 추출 결과가 프로젝트 루트 GEMINI.md의 마커 사이 본문과 1:1 일치
- **테스트**: `bash -c 'source scripts/install-mac.sh; extract_bootstrap_content opal/bootstrapper/gemini-hardening.md' | diff - <(sed -n '11,181p' GEMINI.md)` 결과 빈 차이
- **의존**: 없음

### Step 2: install-mac.sh 인스톨러 수정

- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**:
  1. `OPAL_END` 다음 줄에 `HARDENING_START`/`HARDENING_END` 상수 추가
  2. `install_opal_section()` 정의 직후 `install_gemini_hardening()` 함수 추가 (R2 분기 제외, 마커만 HARDENING)
  3. `install_opal()` 내 Gemini OPAL `install_opal_section` 호출 직후 `install_gemini_hardening` 호출 추가
  4. `print_summary()` 내 OPAL Gemini 요약 라인 직후 HARDENING 요약 라인 추가
- **완료 기준**: (1) `bash -n scripts/install-mac.sh` 신택스 통과 (2) `install_opal_section` 함수 본문은 변경 없음 (diff 확인) (3) 신규 함수가 마커 기반 3분기 로직(신규/교체/추가)을 모두 포함
- **테스트**: `bash -n scripts/install-mac.sh` + `grep -n "install_gemini_hardening\|HARDENING_START" scripts/install-mac.sh`로 4곳(상수 2 + 함수 정의 1 + 호출 1 + 요약 1) 확인
- **의존**: Step 1

### Step 3: 로컬 dry-run 검증

- [ ] 완료
- **파일**: 임시 검증 (USER_HOME을 임시 디렉토리로 설정)
- **작업 내용**: 임시 홈 디렉토리에 빈 `~/.gemini/GEMINI.md` / OPAL만 있는 / OPAL+HARDENING이 있는 3가지 케이스를 만들고, `install_gemini_hardening` 함수를 호출하여 결과 파일을 검증한다.
- **완료 기준**: (1) 신규 파일 케이스: HARDENING 마커와 본문만 작성됨 (2) OPAL만 있는 케이스: OPAL 섹션 보존 + HARDENING 섹션 추가됨 (3) HARDENING 이미 있는 케이스: 마커 사이 본문이 교체되며 OPAL 섹션 영향 없음
- **테스트**: 각 케이스 결과 파일에 대해 `grep -c "$OPAL_START"` = 0 또는 1, `grep -c "$HARDENING_START"` = 1 확인 + 본문 diff
- **의존**: Step 1, Step 2

---

## 4. QA 체크리스트

### 기능 테스트

- [ ] `opal/bootstrapper/gemini-hardening.md`가 존재하고 ` ```markdown ` 블록을 포함한다
- [ ] `extract_bootstrap_content`로 추출한 본문이 프로젝트 루트 `GEMINI.md`의 HARDENING 마커 사이 본문과 1:1 일치한다 (SSOT 보장)
- [ ] `install_gemini_hardening()` 함수가 정의되어 있고 `install_opal()`에서 호출된다
- [ ] 신규 파일/마커 존재/마커 부재 3가지 케이스 모두 정상 동작 (dry-run 검증 통과)
- [ ] `print_summary()`에 HARDENING 요약 라인이 추가되어, 설치 후 마커 존재 시 출력된다

### 일관성 테스트

- [ ] `install_opal_section()` 함수 본문은 변경되지 않았다 (하위 호환)
- [ ] `gemini-hardening.md`가 `gemini-bootstrap.md`와 동일한 파일 구조(헤더 → ```markdown 블록 → 변경이력)를 따른다
- [ ] HARDENING 마커가 OPAL 마커와 독립적으로 작동한다 (한쪽 업데이트가 다른 쪽에 영향 없음)
- [ ] `~/.opal/` 경로 직접 편집이 없다 (소스 경로 `opal/bootstrapper/`만 수정)

### 문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따른다
- [ ] kebab-case 파일/폴더 네이밍을 따른다 (`gemini-hardening.md`)
- [ ] 변경이력 테이블 포함 (v1.0)

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| HARDENING SSOT(루트 GEMINI.md)가 향후 갱신되어도 `gemini-hardening.md`는 자동 동기화되지 않음 | 중 — 두 파일이 다를 위험 | DONE 단계 보고에 SSOT 갱신 시 `gemini-hardening.md`도 함께 갱신해야 한다는 운영 노트 명시 + Step 1 테스트로 일치 검증 |
| `install_opal_section()` 복제로 코드 중복 발생 | 하 — 유지보수 비용 | 제약상 수정 금지이므로 수용. 향후 리팩토링 태스크에서 두 함수를 마커 파라미터화한 단일 헬퍼로 통합 제안 |
| TASK.md의 `print_installed_summary` 함수명이 실제 코드 `print_summary`와 다름 | 하 — 작업 위치 혼선 | 코드 기준으로 작업하고 보고서에 불일치 명시 (이미 본 PLAN에 기록) |
| 동일 파일(`~/.gemini/GEMINI.md`)에 두 함수가 순차 쓰기 → 임시 파일 처리 충돌 가능성 | 저 — bash sed/while 패턴은 동기 실행이라 충돌 없음 | Step 3 dry-run으로 OPAL→HARDENING 순차 실행 결과 검증 |
| 기존 사용자의 `~/.gemini/GEMINI.md`에 HARDENING 유사 수동 섹션이 있을 경우 마커가 없어 중복 추가됨 | 저 | 인스톨러 정책상 마커 기반만 인식. 사용자 안내 문구는 본 태스크 범위 외 |
