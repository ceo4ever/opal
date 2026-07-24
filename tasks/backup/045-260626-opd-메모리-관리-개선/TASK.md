# TASK: 메모리 관리 체계 개선 — 토큰 효율·라이프사이클 집행 + memory-tool 신설

> 작성일: 2026-06-26 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 프레임워크의 메모리 관리 체계를 **토큰 효율 + 라이프사이클 집행** 관점에서 개선한다. 자유 텍스트 컬럼의 무한 증식과 죽은 메모리 잔존을 막기 위해, `memory-learning.md`(SSOT)를 개정하고 신규 `memory-tool`로 갯수·길이·정리를 결정론적으로 집행한다.

## 배경

MAMS 프로젝트의 `.opal/MEMORY.md`가 ~40KB까지 비대해진 사건이 발단이다. 이 프레임워크 자신의 MEMORY.md도 같은 병을 앓고 있다(044 히스토리 행 하나가 600자 이상). 근본 원인은 SSOT 규칙 자체에 박혀 있어, 어느 프로젝트든 동일하게 재발한다.

## 배경 분석 (대화에서 도출)

MAMS PM 진단 + 본 프로젝트 SSOT(`opal/core/references/harness/memory-learning.md`) 직접 확인 결과, 3가지 구조적 결함을 식별했다:

1. **인덱스·히스토리 자유 텍스트 컬럼에 길이 제한이 없음** (`memory-learning.md:17-18`)
   - 인덱스 형식 `| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |`, 히스토리 형식 `| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |` 의 `설명`·`작업` 컬럼에 max 글자수 규칙 부재 → PM이 개별 `.md` 본문을 인덱스에 인라인하는 것이 규칙상 허용됨. 토큰 폭증의 직접 원인.
2. **메모리 라이프사이클·정리 트리거 부재** (`memory-learning.md:22`)
   - "작업 히스토리 10개 FIFO, 소유자 요청 시 정리 제안"이 정리 규칙의 전부. `상태` 컬럼은 존재하나 어떤 상태가 삭제·승격을 유발하는지 정의가 없음 → 죽은 메모리(흡수됨/진부화/완료)가 영원히 잔존.
3. **승격(promote) 개념 부재**
   - feedback이 AGENT.md/CONVENTIONS로 흡수돼도 메모리 파일이 SSOT 이중화된 채 남는다(예: `feedback_plan_cross_cut_grep_obligation` "AGENT.md 흡수" 표기만 있고 삭제 안 됨).

**역할 분담 원칙** (STATE.md ↔ state-tool 구조와 동일):
- **도구(memory-tool)** = MEMORY.md 테이블 변경(행 추가·정리·상태변경·이관) + 파일 라이프사이클 집행. LLM의 마크다운 직접 편집 금지.
- **PM** = 개별 `memory/*.md` 본문 작성 + promote/dead 의미 판단. 도구는 그 판단을 집행만 한다.

## 확정된 설계 방향 (대화에서 합의)

1. **제목 컬럼 맨 앞 추가** — 메모리 인덱스·작업 히스토리 양쪽 테이블 형식 맨 앞에 `제목` 컬럼 신설(스캔 효율 + 토큰 절감). 제목 = 짧은 명사구.
2. **형식 하드 캡** — 인덱스 요약 1줄(≤80자), 히스토리 핵심결과 ≤2줄. 상세는 개별 `.md` 본문 전용(인덱스=포인터).
3. **히스토리 FIFO 10→5** (캡틴 req3 "반드시").
4. **메모리 라이프사이클 상태머신** — `active` → `promoted`(docs 흡수 후 삭제) / `superseded`(대체됨 삭제) / `dead`(완료·진부화 삭제).
5. **신규 memory-tool** (state-tool 패턴: `run.sh` + `*.py` + `schema/` + `tests/`) — 메모리·히스토리 **양쪽 갯수 제한** 집행.
6. **메모리 갯수 제한 = blind FIFO 아님** — 상한 초과 시 `append`를 **차단**하고 PM에게 promote/dead 정리를 강제하는 게이트 방식(데이터 무손실). 히스토리는 소모성 로그이므로 FIFO 자동 정리 허용.
7. **project-init 템플릿 동기화** — 신규 프로젝트가 처음부터 신포맷 MEMORY.md로 출고되도록 템플릿 교체.
8. **집행 = "Enforce, don't advise"** (`PRINCIPLES.md` Core Stance) — "반드시"는 산문 규칙이 아니라 도구가 강제한다.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | memory-learning.md(SSOT) 개정 + 신규 memory-tool + project-init 템플릿 동기화로 메모리 토큰 효율·라이프사이클을 결정론 집행 | - | `memory-learning.md:17-22` |
| 범위 | **포함**: memory-learning.md 형식·라이프사이클·FIFO 개정 / memory-tool 신설(서브명령·갯수·길이·정리 집행) / project-init 템플릿 / install 등록 / tools.md·harness §9 drift 정합. **제외**: 기존 MAMS·타 프로젝트 MEMORY.md 실데이터 변환은 본 태스크에서 도구 제공까지(`migrate` 실행은 각 프로젝트에서) / 캡틴 install 재배포(소스가 SSOT) | 메모리 활성 상한 N(유형별 vs 전체), `migrate` 자동화 범위·제목 추출 방식, 제목 컬럼 최종 순서, memory-tool 최종 서브명령 셋 → **PLAN에서 결정** | 042 CLOSE 훅 선례, 044 tool-scan 신설 선례 |
| 제약 | 배포 경계(프로젝트 소스만 수정, `~/.opal/` 직접 편집 금지) / state-tool 패턴 준수 / 변경이력 행 추가 의무 / 메모리 blind 삭제 금지(무손실) / RED-first(도구 로직 고위험) | - | `.opal/AGENT.md` §금지사항, `PRINCIPLES.md` §4 |
| 완료기준 | 아래 요구사항 R1~R12 AC 전부 충족 + memory-tool 테스트 GREEN + 회귀 0 | - | - |

## 요구사항

- [ ] **R1 (제목 컬럼)**: `memory-learning.md`의 메모리 인덱스 형식과 작업 히스토리 형식 정의 양쪽에 `제목` 컬럼이 **맨 앞**에 추가되어 있다.
- [ ] **R2 (길이 캡)**: `memory-learning.md`에 인덱스 요약 ≤80자(1줄), 히스토리 핵심결과 ≤2줄 규칙이 명문화되어 있다.
- [ ] **R3 (FIFO 5)**: `memory-learning.md`의 작업 히스토리 FIFO 한도가 10→5로 변경되어 있다.
- [ ] **R4 (라이프사이클)**: `memory-learning.md`에 메모리 상태 4종(active/promoted/superseded/dead) 정의 + 각 상태의 삭제·승격 트리거가 기술되어 있다.
- [ ] **R5 (memory-tool 골격)**: `opal/tools/memory-tool/`에 `run.sh` + `*.py` + `schema/` + `tests/`가 state-tool 패턴으로 생성되고, 서브명령이 JSON(`{"ok":...}`)을 반환한다.
- [ ] **R6 (메모리 갯수 게이트)**: memory-tool이 메모리 활성 상한 초과 시 `append`를 거부하고 에러코드를 반환한다(blind FIFO 삭제 없음 — 데이터 무손실). 검증: 상한 초과 append 시 `ok:false` + 정리 유도 에러.
- [ ] **R7 (히스토리 FIFO 집행)**: memory-tool이 히스토리 6개째 추가 시 가장 오래된 1개를 결정론적으로 정리하여 항상 ≤5를 유지한다. 검증: 6개 append 후 히스토리 행 수 = 5.
- [ ] **R8 (promote/정리 서브명령)**: memory-tool이 메모리를 docs로 이관 후 인덱스 행 + `.md` 파일을 삭제하는 경로(promote)와 dead/superseded 정리 경로를 제공한다.
- [ ] **R9 (테이블 직접편집 금지 집행)**: MEMORY.md 인덱스·히스토리 행 변경은 memory-tool로만 가능하다(state-tool의 `marker_missing`류 가드 패턴 준용).
- [ ] **R10 (project-init 템플릿)**: `opal-project-init`가 출고하는 MEMORY.md 템플릿이 신포맷(제목 컬럼·길이 캡·FIFO 5·라이프사이클)을 반영한다.
- [ ] **R11 (install 등록)**: `scripts/install-mac.sh`가 memory-tool을 `~/.opal/tools/`로 배포하도록 등록되어 있다.
- [ ] **R12 (drift 정합)**: `tools.md`와 `opal-harness.md` §9 도구 테이블에 memory-tool 행이 동일하게 추가되어 있다.

## 제약 조건

- **배포 경계**: 프로젝트 소스(`opal/`, `scripts/` 등)만 수정한다. `~/.opal/` 배포 파일 직접 편집 금지. 워커가 동작 검증을 위해 `~/.opal/tools/`에 사전 배포하더라도 그것은 dev 아티팩트이며 SSOT는 소스다.
- **도구 패턴**: state-tool 구조(`run.sh` 래퍼, JSON 출력, 에러코드 카탈로그, `tests/` 단위테스트)를 준수한다.
- **데이터 무손실**: 메모리(지식)는 blind FIFO로 삭제하지 않는다. 갯수 상한은 정리를 강제하는 게이트일 뿐, 자동 삭제가 아니다.
- **변경이력**: 수정한 모든 스킬·참조 문서에 변경이력 행을 추가한다(일시 KST + 태스크 번호 045).
- **Enforce don't advise**: `PRINCIPLES.md` Core Stance — "반드시"는 도구로 집행한다.
- **RED-first**: 도구 로직은 self-confirming 고위험 영역(`PRINCIPLES.md` §4)이므로, 테스트 작성자(test-agent)와 구현자(be-agent)를 분리한다.

## 기술 스택

- Python 3 (memory-tool, state-tool 패턴 — pytest)
- Bash (run.sh 래퍼, install-mac.sh)
- Markdown / YAML (memory-learning.md, MEMORY.md 템플릿)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | memory-learning.md (SSOT) | `opal/core/references/harness/memory-learning.md` | 개정 대상 — 형식·FIFO·라이프사이클 |
| D-2 | 설계 | PRINCIPLES.md (헌법) | `opal/core/references/...PRINCIPLES.md` 또는 `~/.opal/PRINCIPLES.md` 소스 | Core Stance "Enforce, don't advise" / §4 self-confirming |
| D-3 | 소스 | state-tool | `opal/tools/state-tool/` | memory-tool 구현 패턴 레퍼런스 |
| D-4 | 소스 | tool-scan (044) | `opal/tools/tool-scan/` | 최근 신규 도구 선례 — RED-first·install·drift 정합 패턴 |
| D-5 | 설계 | opal-harness.md §9 | `opal/core/references/opal-harness.md` | 도구 테이블 drift 정합 대상 |
| D-6 | 설계 | tools.md | `~/.opal/references/tools.md` 소스 | 도구 테이블 drift 정합 대상 |
| D-7 | 소스 | opal-project-init 템플릿 | `opal/skills/opal-project-init/templates/` | MEMORY.md 템플릿 동기화 대상 |
| D-8 | 소스 | install-mac.sh | `scripts/install-mac.sh` | memory-tool 배포 등록 대상 |

> ANALYSIS 단계에서 D-1·D-3·D-7·D-8의 정확한 경로·줄번호를 확정한다.
