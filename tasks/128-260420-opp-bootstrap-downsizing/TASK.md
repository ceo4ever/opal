# TASK: 부트스트랩 다운사이징 — Eager 로드 최적화

> 작성일: 2026-04-20 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 캡틴 요청 + 사전 분석
> 출력: TASK.md

## 작업 목표

세션 시작 시 Eager 로드되는 부트스트랩 파일들의 총 토큰 소비(현재 ~18,500)를 절반 수준(~9,500)으로 줄인다. 소스에는 정보를 보존하되 배포 버전에서 불필요한 내용을 제거하고, Lazy 로드 가능한 섹션을 분리한다.

## 배경

세션 시작 시 6개 파일이 Eager 로드되어 약 18,500 토큰을 소비한다. 이는 전체 컨텍스트의 상당 부분을 차지하며, 실제 작업 시작 전부터 불필요한 내용(변경이력, 런타임 비활성 섹션)을 포함한다.

## 배경 분석 (대화에서 도출)

### 현재 Eager 로드 파일 및 토큰

| 파일 | 추정 토큰 | 비고 |
|------|----------|------|
| `~/.opal/AGENT.md` | ~5,000 | opal/core/AGENT.md → 배포 |
| `~/.opal/references/opal-harness.md` | ~5,500 | opal/core/references/opal-harness.md → 배포 |
| `.opal/AGENT.md` (프로젝트) | ~3,600 | 프로젝트별, 최적화 범위 외 |
| `~/.opal/references/opal-pm.md` | ~2,600 | opal/core/references/opal-pm.md → 배포 |
| `.opal/MEMORY.md` | ~1,500 | 프로젝트별, 최적화 범위 외 |
| `~/.opal/identity.md` | ~330 | 사용자 데이터, 최적화 범위 외 |
| **합계** | **~18,500** | |

### install-mac.sh 배포 구조 분석

- `install_opal_references()`: `cp -Rf "$ref_src"/. "$ref_dst"/` — 단순 복사, 전처리 없음
- AGENT.md: `cp "$opal_dir/core/AGENT.md" "$opal_home/AGENT.md"` — 단순 복사
- → 배포 시 전처리(strip) 함수를 추가하면 소스에는 정보를 유지하면서 배포 버전에서만 제거 가능

### opal-harness.md 섹션별 분석

| 섹션 | 줄 수 | 현재 구조 | 최적화 방향 |
|------|-------|----------|------------|
| §0 용어 정의 | ~20 | FULL 콘텐츠 | **제거** — 런타임 불참조, 개발자 문서용 |
| §1 Guards | ~47 | FULL 콘텐츠 | **유지** — 세션 시작부터 활성 필수 |
| §2 모듈 구조 | ~46 | FULL 콘텐츠 | **유지** — 서브 하네스 로딩 규칙 필수 |
| §3 State 관리 | ~100 | FULL 콘텐츠 | **분리** → `harness/state.md` Lazy |
| §4 TASK 공통 프로세스 | ~45 | FULL 콘텐츠 | **분리** → `harness/task-process.md` Lazy |
| §5~§9 | ~40 | 이미 stub | 유지 (stub만 있음) |
| 변경이력 | ~28 | FULL | **배포 시 strip** |

### opal-pm.md 섹션별 분석

| 섹션 | 줄 수 | 현재 구조 | 최적화 방향 |
|------|-------|----------|------------|
| §1 PM 역할 개요 | ~10 | FULL | **AGENT.md 인라인** 후 제거 |
| §2 PM 컨텍스트 로드 | ~14 | FULL | **AGENT.md 인라인** — PM 활성화에 필수 |
| §3 디스패치 전 프로세스 | ~5 | stub | 유지 (stub) |
| §4 PM 검토 게이트 | ~45 | FULL 콘텐츠 | **분리** → `harness/pm-review-gate.md` Lazy |
| §7 문서/코드 불일치 | ~20 | FULL 콘텐츠 | **분리** → `harness/doc-code-mismatch.md` Lazy |
| §5,§6,§9,§10,§11 | ~25 | stub | 유지 (stub) |

→ **opal-pm.md 전체를 Lazy**로 전환 가능: §2의 핵심(PM 활성화 절차 14줄)만 AGENT.md에 인라인

### AGENT.md 분석

| 섹션 | 줄 수 | 최적화 방향 |
|------|-------|------------|
| 부트스트랩 절차 | ~40 | **유지** |
| 정체성 적용, 핵심 역할, 행동 규칙 | ~80 | **유지** |
| code-scan 활용 규칙 | ~15 | **유지** |
| 기억과 학습 | ~20 | **유지** (자주 참조) |
| 보고 형식 | ~35 | **유지** |
| PM 행동 프로세스 요약 | ~11 | **제거** — opal-pm.md Lazy화 후 AGENT.md에 §2 인라인하면 중복 |
| 모델 매핑 자동 적용 절차 | ~20 | **제거** — opal-model-mapping.md에 내용 있음, trigger만 유지 |
| 프로젝트 부트스트래퍼 자동 관리 | ~33 | **Lazy화** — 이미 부트스트래퍼 있는 프로젝트에선 미발동 |
| 변경이력 | ~14 | **배포 시 strip** |

### 죽은 지침 (Dead Instructions) 목록

| # | 위치 | 내용 | 사유 |
|---|------|------|------|
| D-1 | AGENT.md § 변경이력 | 전체 변경이력 테이블 | 런타임 미참조 |
| D-2 | opal-harness.md § 변경이력 | 전체 변경이력 테이블 (28줄) | 런타임 미참조 |
| D-3 | opal-harness.md §0 | 용어 정의 테이블 | 개발자 문서용, 런타임 무관 |
| D-4 | AGENT.md § 부트스트래퍼 > Cursor | Cursor 부트스트래퍼 절차 | Claude Code에서 절대 실행 안 됨 |
| D-5 | AGENT.md § 부트스트래퍼 > Antigravity | Antigravity 부트스트래퍼 절차 | Claude Code에서 절대 실행 안 됨 |
| D-6 | AGENT.md § PM 행동 프로세스 요약 | opal-pm.md 요약 5줄 | opal-pm.md Lazy화 + §2 인라인하면 중복 |
| D-7 | AGENT.md § 모델 매핑 절차 | 플랫폼 감지 + Cursor 특이사항 절차 | opal-model-mapping.md에 있음, trigger만 필요 |
| D-8 | opal-harness.md §3 레거시 호환 노트 | 3개의 `> 레거시 호환` 박스 | 하위호환 유지 완료, 신규 파일 작성 기준 이미 적용 |

## 확정된 설계 방향 (대화에서 합의)

1. **3가지 방향 모두 적용** — 변경이력 strip, Lazy 분리, slim화
2. **소스 보존** — 소스(`opal/`)에는 변경이력 등 정보 유지, 배포(`~/.opal/`) 시에만 제거
3. **죽은 지침 제거** — 분석에서 확인된 8개 항목 제거

## 요구사항

### Track A: install-mac.sh 배포 시 strip

- [x] **A-1** `strip_deploy_md()` 함수를 install-mac.sh에 추가
  - 무엇을: `## 변경이력` 섹션부터 파일 끝까지 제거하는 bash 함수 추가
  - 어디에: `scripts/install-mac.sh` → `install_opal()` 내 AGENT.md 복사 라인, `install_opal_references()` 함수
  - 왜: 소스에는 변경이력 유지하면서 배포 버전에서 불필요한 내용 제거
  - AC: 배포 후 `~/.opal/AGENT.md`, `~/.opal/references/opal-harness.md`에 `## 변경이력` 섹션이 존재하지 않는다

- [x] **A-2** strip 대상 파일 범위 정의
  - 무엇을: strip 적용 대상을 `AGENT.md` + `references/opal-harness.md` 2개 파일로 한정
  - 어디에: `install-mac.sh` strip 로직
  - 왜: 다른 references 파일들은 변경이력 없음
  - AC: 나머지 references/*.md 파일들은 strip 미적용(원본 그대로 배포)

### Track B: opal-harness.md 슬림화

- [x] **B-1** `harness/state.md` 신설
  - 무엇을: opal-harness.md §3 State 관리 전체 내용을 `harness/state.md`로 이동
  - 어디에: `opal/core/references/harness/state.md` (신규 파일)
  - 왜: §3는 태스크 실행 중에만 필요 — Eager 불필요
  - AC: `harness/state.md` 파일 존재, opal-harness.md §3은 stub 2줄로 교체

- [x] **B-2** `harness/task-process.md` 신설
  - 무엇을: opal-harness.md §4 TASK 공통 프로세스 전체를 `harness/task-process.md`로 이동
  - 어디에: `opal/core/references/harness/task-process.md` (신규 파일)
  - 왜: §4는 태스크 시작 시에만 필요
  - AC: `harness/task-process.md` 파일 존재, opal-harness.md §4는 stub 2줄로 교체

- [x] **B-3** opal-harness.md 죽은 섹션 제거
  - 무엇을: §0 용어 정의 제거, §3 레거시 호환 노트 3개 제거
  - 어디에: `opal/core/references/opal-harness.md`
  - 왜: §0은 런타임 미참조(D-3), 레거시 호환 노트는 이미 완료(D-8)
  - AC: §0 섹션 없음, `> 레거시 호환` 블록 없음

- [x] **B-4** opal-harness.md의 하네스 모듈 테이블에 신규 파일 항목 추가
  - 무엇을: §2 하네스 모듈 테이블에 `state.md`, `task-process.md` 행 추가
  - 어디에: `opal/core/references/opal-harness.md` §2 Lazy 로드 모듈 테이블
  - 왜: 새 모듈의 로드 시점과 경로를 명시
  - AC: 테이블에 두 항목 존재, 로드 시점/탐색 경로 명시

### Track C: opal-pm.md Lazy 전환

- [x] **C-1** PM 컨텍스트 로드 절차 AGENT.md 인라인
  - 무엇을: opal-pm.md §2 핵심(절차 1-2단계 + 프로젝트 설정 적용 설명)을 AGENT.md 부트스트랩 Eager 4단계에 인라인
  - 어디에: `opal/core/AGENT.md` Eager 5단계(현재 `.opal/AGENT.md` Read)를 4단계로 조정, 기존 4단계(opal-pm.md Read) 제거
  - 왜: PM 모드 활성화 절차(§2)는 Eager 필수지만 나머지는 불필요
  - AC: AGENT.md Eager에 opal-pm.md Read 지시 없음, PM 컨텍스트 로드 2단계 절차가 AGENT.md에 직접 명시

- [x] **C-2** `harness/pm-review-gate.md` 신설
  - 무엇을: opal-pm.md §4 PM 검토 게이트 전체를 `harness/pm-review-gate.md`로 이동
  - 어디에: `opal/core/references/harness/pm-review-gate.md` (신규 파일)
  - 왜: 검토 게이트는 디스패치 직전/PM Gate 수행 시에만 필요
  - AC: `harness/pm-review-gate.md` 파일 존재, opal-pm.md §4는 stub으로 교체

- [x] **C-3** `harness/doc-code-mismatch.md` 신설
  - 무엇을: opal-pm.md §7 문서/코드 불일치 전체를 `harness/doc-code-mismatch.md`로 이동
  - 어디에: `opal/core/references/harness/doc-code-mismatch.md` (신규 파일)
  - 왜: 불일치 판단은 EXECUTE 검토 시에만 필요
  - AC: 파일 존재, opal-pm.md §7은 stub으로 교체

- [x] **C-4** opal-pm.md Lazy 트리거 테이블 갱신
  - 무엇을: AGENT.md의 Lazy 트리거 테이블에 `opal-pm.md` 항목 추가 (트리거: 디스패치 전 또는 PM Gate 수행 시)
  - 어디에: `opal/core/AGENT.md` Lazy 트리거 테이블
  - 왜: Eager에서 내린 opal-pm.md의 로드 시점을 명확히 정의
  - AC: Lazy 트리거 테이블에 opal-pm.md 행 존재, 트리거 조건 명시

### Track D: AGENT.md 죽은 지침 정리

- [x] **D-1** PM 행동 프로세스 요약 섹션 제거
  - 무엇을: AGENT.md의 "PM 행동 프로세스" 섹션(opal-pm.md 요약 5줄) 제거
  - 어디에: `opal/core/AGENT.md`
  - 왜: opal-pm.md Lazy화 + §2 인라인으로 대체됨(D-6)
  - AC: "## PM 행동 프로세스" 섹션 없음

- [x] **D-2** 모델 매핑 절차 섹션 제거
  - 무엇을: AGENT.md의 "모델 매핑 자동 적용" 상세 절차(3단계 + Cursor 특이사항) 제거, Lazy 트리거 테이블 항목만 유지
  - 어디에: `opal/core/AGENT.md`
  - 왜: 절차는 opal-model-mapping.md에 있음, trigger만 있으면 충분(D-7)
  - AC: "## 모델 매핑 자동 적용" 전체 섹션 없음 (Lazy 트리거 테이블 행만 존재)

- [x] **D-3** 부트스트래퍼 자동 관리 Cursor/Antigravity 절 제거
  - 무엇을: "프로젝트 부트스트래퍼 자동 관리" 섹션 내 `### Cursor`, `### Antigravity` 하위 섹션 제거
  - 어디에: `opal/core/AGENT.md`
  - 왜: Claude Code에서 실행되지 않음(D-4, D-5)
  - AC: `### Cursor` / `### Antigravity` 절 없음, `### Claude Code` 절만 존재

## 제약 조건

- `~/.opal/` 직접 수정 금지 — 모든 변경은 `opal/` 소스에서 수행, 배포는 install-mac.sh로
- opal-harness.md에서 §1 Guards와 §2 모듈 구조는 반드시 Eager 유지 (세션 시작부터 활성 필요)
- PM 컨텍스트 로드 절차(§2)는 AGENT.md에 인라인 유지 — Lazy opal-pm.md로 대체되지 않도록
- harness/ 신규 모듈 파일들은 탐색 경로 규칙(`{프로젝트}/.opal/references/harness/` → `~/.opal/references/harness/`) 준수
- 기존 하네스 §2 모듈 테이블을 신규 파일로 갱신하여 오케스트레이터가 새 경로를 찾을 수 있게 보장

## 기술 스택

- Markdown (AI 지시문)
- Bash (install-mac.sh 수정)
- Python3 (strip 로직 구현 선택지)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | OPAL AGENT.md (소스) | `opal/core/AGENT.md` | 수정 대상 — 부트스트랩 절차, 죽은 섹션 |
| D-2 | 소스 | opal-harness.md (소스) | `opal/core/references/opal-harness.md` | 수정 대상 — §0/§3/§4 분리 |
| D-3 | 소스 | opal-pm.md (소스) | `opal/core/references/opal-pm.md` | 수정 대상 — Lazy 전환, §4/§7 분리 |
| D-4 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 수정 대상 — strip 함수 추가 |
| D-5 | 소스 | opal-harness 모듈들 | `opal/core/references/harness/` | 신규 파일 위치 |
