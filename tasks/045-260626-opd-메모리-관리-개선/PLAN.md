# PLAN: 메모리 관리 체계 개선 — 토큰 효율·라이프사이클 집행 + memory-tool 신설

> 작성일: 2026-06-26 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature
> 페르소나: software-architect | 가이드: op-dev-plan/references/plan-guide.md

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL 메모리 관리 체계를 **토큰 효율 + 라이프사이클 집행 + 영구 거처 졸업(promote)** 관점에서 개선한다. SSOT인 `memory-learning.md`를 개정(제목 컬럼·길이 캡·FIFO 5·라이프사이클 4상태 + **메모리 이관 워크플로우**)하고, 신규 `memory-tool`(state-tool 패턴: `run.sh`+`*.py`+`schema/`+`tests/`)로 히스토리 FIFO·요약 길이캡·테이블 직접편집 금지를 **결정론적으로 집행**하며, 매 변경 명령 후 **자가검토(`review`) 블록**을 자동으로 덧붙여 메모리 정리·졸업을 ambient하게 강제한다. 핵심 철학은 `PRINCIPLES.md` Core Stance "Enforce, don't just advise" — "반드시"는 산문이 아니라 도구가 강제한다.

**1순위 산출물 = 메모리 → 영구 거처 졸업(promote) 워크플로우.** 메모리는 임시 보관소이며, 성숙한 지식은 영구 거처(`docs` 규범 / `brain` 설명)로 졸업한다. promote는 영구 거처 이전을 **확인한 후** 메모리 행+`.md` 파일을 삭제하고 provenance(어디로 갔는지)를 기록한다 — blind 삭제가 아니라 무손실 이전이다. brain 이관은 기존 `//opbr ingest`/`brain-tool add-page`를 재사용한다(중복 파이프라인 금지 — Simplicity). **메모리 갯수 상한은 캡틴 지시(2026-06-26)로 전면 제외**한다 — 졸업·자가검토·길이캡으로 비대화를 막고, 갯수 게이트라는 별도 강제는 두지 않는다. 메모리(지식)는 **blind 삭제 금지**, 히스토리(소모성 로그)만 FIFO=5 자동 정리한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | memory-learning.md SSOT 개정 (제목 컬럼·길이캡·FIFO5·라이프사이클 **+ 이관 워크플로우·자가검토**) | R1, R2, R3, R4, R8', R6' | P0 | 없음 |
| F-002 | memory-tool 도구 골격 (run.sh·*.py·schema·tests, ok/err/ERROR_CODES 재사용) | R5 | P0 | F-001 (형식 계약) |
| F-003 | 마커 직접편집 금지 가드(R9) + 요약 길이캡 검증(R2) **(갯수 게이트 제외 — 캡틴 지시)** | R9, R2 | P0 | F-002 |
| F-004 | 히스토리 FIFO=5 자동 정리 (prune) | R7 | P0 | F-002 |
| F-005 | **promote `--to docs\|brain` 워크플로우** (영구 거처 이전 확인 → 행+파일 삭제 + provenance) + update(dead·superseded) | R8 | P0 | F-002, F-003 |
| F-006 | init / migrate 서브명령 (마커 삽입·구포맷→신포맷 변환) | R9(마커), U-3 | P1 | F-002, F-003 |
| F-007 | project-init MEMORY.md 템플릿 신포맷 동기화 | R10 | P1 | F-001 |
| F-008 | install 등록 (memory-tool run.sh chmod +x) | R11 | P1 | F-002 |
| F-009 | drift 정합 (tools.md + harness §9 도구 테이블) | R12 | P1 | F-002 |
| F-010 | **자가검토 `review` 서브명령** (매 변경 명령 후 review 블록 자동 첨부 + 단독 health 명령, validate 대체) | R6', R5 | P0 | F-002, F-003, F-004, F-005 |

> **요구사항 표기**: R6(메모리 갯수 게이트)은 캡틴 지시(2026-06-26)로 **제외** — §9 요구사항 맵 참조. 신규 요구사항 **R6'**(자가검토 트리거), **R8'**(promote 라우팅: 메모리 성격별 졸업지 매핑)은 §9에 정의.

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ──┬─ F-002 ─┬─ F-003 ─┬─ F-005 (promote --to docs|brain)
(SSOT)  │ (골격)  ├─ F-004  ├─ F-006
+이관/  │         │         └─ F-010 (review: F-003·004·005 후보 표면화)
자가검토 │         ├─ F-008 (install)
        │         └─ F-009 (drift)
        └─ F-007 (project-init 템플릿)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-005 promote 무손실 이전 | promote가 영구 거처 이전을 **확인하지 않고** 행+파일을 삭제하면 살아있는 지식 소실(blind 삭제) | P0 | L1(단위, 이전 미확인 시 거부 + 행/파일 불변 assert) | S-후보: `--ref` 미지정·대상 부재 시 promote → `ok:false` + 행·파일 불변; 정상 경로 → provenance 기록 후 삭제 |
| H-2 | F-004 prune FIFO=5 | 6번째 append 시 정확히 가장 오래된 1개만 삭제(off-by-one·정렬 오류) | P1 | L1(단위, 6개 append 후 행수=5 + 최신 5개 보존) | S-후보: 6개 append → 행수 5 + row[0]이 2번째였던 행 |
| H-3 | F-003 마커 가드 (`marker_missing`) | 마커 부재 MEMORY.md에 도구가 작동하면 자유 텍스트 영역 파괴 (state_tool.py:302/307 동형) | P0 | L1(단위, 마커 없는 파일 → 모든 mutating 명령 거부) | S-후보: 마커 제거된 MEMORY.md에 append → `ok:false` + `marker_missing`, 파일 바이트 불변 |
| H-4 | F-005 promote 행+파일 원자성 | 인덱스 행 + `.md` 파일 동시 삭제 — 행만 삭제·파일 고아 / 파일만 삭제·행 dangling 모두 손상 | P1 | L1(단위, promote 후 행 부재 AND 파일 부재 AND provenance 기록 존재) | S-후보: promote → 인덱스 행 사라짐 + `memory/X.md` 부재 + provenance 로그 1행 |
| H-5 | F-006 migrate 구→신 변환 | 구포맷 행을 신포맷으로 변환 시 데이터 손실(설명 truncate로 정보 소실, 상태 매핑 오류) | P1 | L1(단위, 구포맷 fixture → 행수 보존 + 제목 비어있지 않음 + 원설명 별도 보존) | S-후보: 구포맷 6행 MEMORY.md migrate → 신포맷 6행 + 각 행 제목 비공백 + `[REVIEW]` 플래그 |
| H-6 | F-001 형식 정의 | memory-tool 파서 정규식이 memory-learning.md 형식 정의와 컬럼 수·순서 불일치 → 파싱 0건 | P0 | L1(단위) + 문서-코드 cross-check (PM Gate) | S-후보: 신포맷 템플릿을 도구로 파싱 → 컬럼 매핑 정확 |
| H-7 | F-009 drift 정합 | tools.md ↔ harness §9 memory-tool 행 불일치(044 7도구 정합 선례) | P2 | 문서 cross-check (PM Gate) | S-후보: 두 테이블 memory-tool 행 동일 문자열 |
| H-8 | F-010 review 자가검토 | review가 휴리스틱이 아닌 **판단**을 침범(졸업지 docs/brain·성숙 결정을 도구가 단정)하면 역할 경계 붕괴 / 또는 매 변경 명령 후 review 블록 누락으로 ambient 강제 실패 | P1 | L1(단위, review 출력이 후보만 표면화·결정 단정 없음 + 모든 변경 명령 응답에 review 블록 존재) | S-후보: append/update/promote/prune/migrate 각 응답 JSON에 `review` 키 존재 + `promote_candidates`는 졸업지 단정 없이 후보 행만 |
| H-9 | F-005 promote 라우팅 vs brain 재사용 | promote brain 경로가 별도 파이프라인을 재발명(중복) — `//opbr ingest`/`brain-tool add-page` 미재사용 | P2 | 설계 cross-check (PM Gate) + L1(promote --to brain이 brain-tool 경로를 호출/안내) | S-후보: `--to brain` 경로가 brain-tool add-page/ingest를 재사용(자체 brain 쓰기 구현 부재) |

**가설 도출 근거**: H-1·H-3은 TASK [MUST] 데이터 무손실·테이블 직접편집 금지의 직접 반영(`PRINCIPLES.md` Core Stance) — 단 H-1은 갯수 게이트 제외(캡틴 지시)에 따라 **promote 이전 확인**으로 무손실 초점 이동. H-2·H-4는 도구 로직 정확성(self-confirming 고위험 → RED-first 분리). H-8은 자가검토의 역할 경계(도구=표면화, PM=판단) + ambient 강제 계약. H-9는 Simplicity(brain 재사용·재발명 금지). H-6·H-7은 044 tool-scan 선례의 문서-코드 drift 패턴.

---

## 2. 기능별 분석

### F-001: memory-learning.md SSOT 개정

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/harness/memory-learning.md` | 메모리 형식·FIFO·라이프사이클 SSOT | 수정 |

#### 2.1.2 현재 구현
(ANALYSIS.md §1.1 + 직접 Read 검증)
- `memory-learning.md:17` 인덱스 형식 `| 등록일시 | 카테고리 | 상태 | 파일 | 설명 |` — 제목 없음, `설명` 길이 무제한.
- `memory-learning.md:18` 히스토리 형식 `| 등록일자 | 작업 | 단계 | 경로 | 시작일시 | 완료일시 |` — `작업` 길이 무제한.
- `memory-learning.md:22` 정리 규칙 `작업 히스토리 10개 FIFO, 소유자 요청 시 정리 제안` — 라이프사이클·상태 트리거 없음.
- baseline 실증(`.opal/MEMORY.md:42` 044 행): 단일 셀 ~1,500자, 상태값 `대기/폐기 기록/예정/완료/~~완료~~/유지` 혼재.

#### 2.1.3 영향 범위
- **하위 의존**: 이 형식 정의가 F-002 memory-tool 파서 정규식의 계약(H-6). 컬럼 수·순서가 코드와 1:1 일치해야 함.
- **하위 의존**: F-007 project-init 템플릿(`opal-project-init/SKILL.md:408`)이 이 형식을 미러링.
- **상위 소비**: AGENT.md 부트스트랩 메모리 브리핑(`docs/PROJECT.md:129`)이 이 형식의 인덱스를 읽음.

---

### F-002: memory-tool 도구 골격

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/memory-tool/run.sh` | venv python 래퍼 (state-tool 동형) | 신규 |
| 도구 | `opal/tools/memory-tool/memory_tool.py` | 서브명령 디스패처 + ok/err/ERROR_CODES | 신규 |
| 도구 | `opal/tools/memory-tool/schema/memory.schema.json` | MEMORY.md 행 스키마(문서용 SSOT) | 신규 |
| 도구 | `opal/tools/memory-tool/tests/test_memory_tool.py` | pytest 단위 테스트 (RED-first) | 신규 |
| 도구 | `opal/tools/memory-tool/README.md` | 사용법(state-tool README 동형) | 신규 |

#### 2.2.2 현재 구현 (재사용 패턴)
state-tool 재사용 진입점(직접 Read 검증):
- `state_tool.py:121` `ok(command, **kwargs)` — `{"ok":True,"command":...}` 단일라인 JSON, exit 0.
- `state_tool.py:125` `err(command, code, ...)` — `ERROR_CODES` 키 참조, 단일라인 JSON, `sys.exit(exit_code)`.
- `state_tool.py:68` `ERROR_CODES = {...}` dict SSOT 패턴.
- `state_tool.py:229` `replace_pipeline_section` + `:302/:307` `marker_missing` err — 마커 가드 패턴.
- `state-tool/run.sh:1-12` — `$HOME/.opal/.venv/bin/python` + `SCRIPT_DIR/*.py "$@"` exec.
- import는 **표준 라이브러리만**(`state_tool.py:14-23`: argparse/json/os/pathlib/re/sys/datetime). `trailofbits/modern-python` 미적용 — state-tool은 venv stdlib-only, 동일 유지(Simplicity).

#### 2.2.3 영향 범위
- **상위 의존**: F-003~F-006 모든 서브명령이 이 골격 위에 구현.
- **install**: `install-mac.sh:1044` `install_dir "$opal_dir/tools"`가 디렉토리 통째 복사 → memory-tool 디렉토리는 자동 배포됨. F-008은 `chmod +x run.sh`만 추가.

---

### F-003: 마커 직접편집 금지 가드 + 요약 길이캡 검증 (갯수 게이트 제외)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/memory-tool/memory_tool.py` | `cmd_append`(메모리) + 마커 파싱/렌더 헬퍼 + 요약 길이캡 검증 | 신규(F-002 내) |

#### 2.3.2 현재 구현
- **갯수 게이트 제외(캡틴 지시 2026-06-26)**: 메모리 활성 상한·`MEMORY_LIMITS`·`memory_limit_exceeded`는 본 태스크에서 다루지 않는다. 비대화 방지는 졸업(F-005)·자가검토(F-010)·요약 길이캡(R2)이 담당.
- 마커 가드는 `state_tool.py:229/302` 패턴 직접 차용: 마커 영역 `find()` → -1이면 `marker_missing` err.
- 요약 길이캡(R2): append 시 `요약` 셀 ≤80자 검증(`summary_too_long`).

#### 2.3.3 영향 범위
- `.opal/MEMORY.md`(이 프로젝트) 및 모든 프로젝트 MEMORY.md가 마커를 가져야 동작 → F-006 `init`/`migrate`가 마커 삽입 보장(R-2 대응).
- append는 갯수 차단 없이 무제한 추가 가능하되, 길이캡·자가검토가 비대화를 억제.

---

### F-004: 히스토리 FIFO=5 자동 정리 (prune)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/memory-tool/memory_tool.py` | `cmd_append`(history 모드) + `cmd_prune` | 신규(F-002 내) |

#### 2.4.2 현재 구현
- 히스토리는 소모성 로그 → FIFO 자동 정리 허용(TASK 확정 #6). 한도 5(R3).
- append(history)가 6번째 추가 시 가장 오래된 1개 자동 제거. 별도 `prune`도 idempotent 정리 경로 제공.

#### 2.4.3 영향 범위
- 메모리 append(F-003)와 코드 경로 공유하되 게이트 분기(`--kind memory` 차단 vs `--kind history` FIFO).

---

### F-005: 메모리 → 영구 거처 졸업(promote) 워크플로우 ★1순위

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/memory-tool/memory_tool.py` | `cmd_update`(상태전이) + `cmd_promote`(`--to docs\|brain` + provenance + 행+파일 삭제) | 신규(F-002 내) |
| 도구(재사용) | `opal/tools/brain-tool/brain_tool.py` | `cmd_add_page`(:465) / `//opbr ingest` — brain 이관 재사용 | 변경 없음(재사용) |

#### 2.5.2 현재 구현
- **졸업(promote) = 본 태스크 1순위 산출물.** 메모리는 임시 보관소이며, 성숙한 지식은 영구 거처로 이전한다. 라우팅 표(§3.1.2 신설 워크플로우): 규범(행동 지배)은 `docs`(AGENT.md/CONVENTIONS.md/PROJECT.md), 설명(왜·어떻게)은 `brain`. 메모리 `유형`이 기본 졸업지 힌트.
- **역할 분담**: PM=판단(성숙 여부·docs냐 brain이냐) + authoring(docs 규칙 반영 / brain ingest 트리거), 도구=집행(영구 거처 이전 **확인** → 행+파일 삭제 → provenance 기록). brain 이관은 기존 `//opbr ingest`/`brain_tool.py:465 cmd_add_page` 재사용 — 중복 파이프라인 금지(Simplicity).
- promote = 영구 거처 이전 확인 후 인덱스 행 삭제 + `memory/<file>.md` 파일 삭제(원자적) + provenance(삭제 전 위치·대상 로그). **무손실**: 지식이 이미 영구 거처로 이전됐기에 blind 삭제가 아니다.
- dead/superseded는 상태 변경(`update`)이며 행 보존(추적용, 로드 제외). 실제 삭제는 자가검토(F-010) `cleanup_candidates`로 표면화 후 명시 정리.

#### 2.5.3 영향 범위
- promote는 파일시스템 삭제 + 영구 거처 검증 동반 → H-1(이전 미확인 거부), H-4(행/파일 원자성 + provenance), H-9(brain 재사용).
- brain 이관 경로는 brain-tool에 의존(`.opal/brain/` 부재 프로젝트는 no-op — `tools.md:473`).

---

### F-006: init / migrate 서브명령

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/memory-tool/memory_tool.py` | `cmd_init`(마커 삽입) + `cmd_migrate`(구→신) | 신규(F-002 내) — 정합성 검증은 F-010 `review`로 통합(validate 제거) |

#### 2.6.2 현재 구현
- `init`: 마커 부재 MEMORY.md(또는 신규)에 신포맷 마커·헤더 삽입(state-tool `cmd_init` create-if-absent 정신).
- `migrate`(U-3): 구포맷 표 정규식 파싱(`state_tool.py:579 parse_existing_state_md` 동형) → 신포맷 표 재작성. **제목 자동 추출 + `needs_review` 플래그**(아래 §3.6.2 결정).

#### 2.6.3 영향 범위
- 본 태스크 범위 = **도구 제공까지**(실제 실행은 각 프로젝트, TASK 범위 확정). 이 프로젝트 `.opal/MEMORY.md` 실데이터 변환은 본 PLAN의 EXECUTE 범위 밖(별도 운영).

---

### F-007: project-init MEMORY.md 템플릿 동기화

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-project-init/SKILL.md` | `2-4. MEMORY.md 형식` 인라인 템플릿(:408) | 수정 |

#### 2.7.2 현재 구현
- `SKILL.md:408-415` 인라인 템플릿(★`templates/` 아님 — ANALYSIS §1.4 검증):
  ```
  # {프로젝트명} 프로젝트 Memory Index
  ## 프로젝트
  {빈 상태 — 프로젝트 진행하며 축적}
  ```
- 신포맷(제목 컬럼·길이캡·FIFO5·라이프사이클·마커) 미반영 → 교체.

#### 2.7.3 영향 범위
- 신규 프로젝트는 `//opi`로 이 템플릿을 출고 → 처음부터 신포맷 + memory-tool 호환 마커 포함.

---

### F-008: install 등록

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `scripts/install-mac.sh` | memory-tool run.sh chmod +x 블록(:1087 tool-scan 블록 직후) | 수정 |

#### 2.8.2 현재 구현
- `install-mac.sh:1044` `install_dir "$opal_dir/tools"`가 전체 복사 → memory-tool 디렉토리 자동 배포.
- `install-mac.sh:1087-1091` tool-scan chmod 블록이 선례. state-tool(`:1060`)·brain-tool(`:1066`)·cmux(`:1072`)와 동형.

#### 2.8.3 영향 범위
- chmod 블록 추가만으로 완결. install_dir 추가 불필요(자동 복사).

---

### F-009: drift 정합 (tools.md + harness §9)

#### 2.9.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 가이드 | `opal/core/references/tools.md` | 도구 전체 사용법 SSOT(소스 실재 확인) | 수정 |
| 가이드 | `opal/core/references/opal-harness.md` | §9 "현재 등록된 도구" 7행 테이블(:242-248) | 수정 |

#### 2.9.2 현재 구현
- `opal-harness.md` §9 현재 7행(xlsx/state/brain/test/code-scan/cmux/tool-scan). memory-tool 행 추가 → 8행.
- `tools.md` 소스 실재 확인(`opal/core/references/tools.md`, 23KB). 044가 두 파일 7도구 동일화한 선례.

#### 2.9.3 영향 범위
- 두 테이블의 memory-tool 행이 동일 문자열이어야 함(H-7).

---

### F-010: 자가검토 review 서브명령

#### 2.10.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/memory-tool/memory_tool.py` | `cmd_review`(단독 health) + `build_review_block()`(매 변경 명령 응답에 첨부) | 신규(F-002 내) |

#### 2.10.2 현재 구현
- `validate`(기존 U-2 설계)를 **제거**하고 `review`로 통합 — format 위반(violations) + 라이프사이클 후보를 단일 health 명령으로 반환(Simplicity). state-tool `cmd_validate`(`state_tool.py:1076`)의 violations[] 패턴을 차용하되 라이프사이클 후보를 함께 반환.
- **매 변경 명령(`init`/`append`/`update`/`promote`/`prune`/`migrate`) 완료 후 도구가 응답 JSON에 `review` 블록을 자동 첨부** → "memory-tool 호출 후 매번 기존 메모리·히스토리 검토"가 ambient하게 강제(별도 CLOSE 훅·pilot 변경 불요).

#### 2.10.3 영향 범위
- `review`는 read-only 휴리스틱만 — 변경 없음. 호출자(PM)가 블록을 보고 promote/정리 실행.
- **역할 경계**: 도구는 후보 표면화만(졸업지·성숙 판단은 PM) → H-8.

> 각 설계 결정 뒤 인라인 인용. 필수 제약은 `[MUST]`. (citation-rules.md §2)

### F-001: memory-learning.md SSOT 개정

#### 3.1.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/memory-learning.md` | 가이드 | 인덱스/히스토리 형식 제목 컬럼·길이캡, FIFO 10→5, 라이프사이클 4상태 신설 + 마커 규약 + 변경이력 행 | `memory-learning.md:17,18,22` (→ D-1) |

#### 3.1.2 설계 — 신 형식 정의 (구체 마크다운 문안 초안)

**[MUST] `PRINCIPLES.md` Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose."** — 아래 형식 규칙(길이캡·FIFO·라이프사이클)은 memory-tool이 집행하며, 문서는 그 규약을 기술한다.

**(a) 신 인덱스 형식 (R1·R2)** — `memory-learning.md:17` 교체:
```markdown
- **메모리 인덱스 형식**: `| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |`
  - `제목`: 짧은 명사구(≤30자). 스캔 1순위 키.
  - `등록일`: `YYYY-MM-DD` (KST).
  - `유형`: project / architecture / feedback / preferences / issues / task.
  - `상태`: active / promoted / superseded / dead (§라이프사이클).
  - `파일`: `memory/<name>.md` 상대경로(포인터).
  - `요약`: **≤80자, 1줄** [MUST]. 상세는 개별 `.md` 본문 전용. 인덱스는 포인터이지 본문이 아니다.
```

**(b) 신 히스토리 형식 (R1·R2)** — `memory-learning.md:18` 교체:
```markdown
- **작업 히스토리 형식**: `| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |`
  - `제목`: 태스크 명사구(맨 앞). 예: "045 메모리 관리 개선".
  - `등록일`: `YYYY-MM-DD` (TASK 시작일, KST).
  - `단계`: 진행중 `PLAN ✅ → TODO 대기` / 완료 `완료`.
  - `경로`: `tasks/<폴더>/`.
  - `핵심결과`: **≤2줄** [MUST]. 무엇을 바꿨는지 + 결과(테스트/회귀). 설계 전문·버그 서사는 금지(개별 메모리 또는 brain으로).
```

**(c) FIFO 5 (R3)** — `memory-learning.md:22` 교체:
```markdown
- **정리**:
  - 작업 히스토리는 **최대 5개 FIFO** [MUST] — 6번째 추가 시 가장 오래된 1개를 memory-tool이 결정론적으로 제거. 이전 히스토리는 git log + tasks/ 폴더에서 추적.
  - 메모리(지식)는 **blind 삭제 금지** [MUST] — 갯수 상한을 두지 않는 대신, 성숙한 지식은 `promote`로 영구 거처(docs/brain)로 졸업한 뒤 삭제하고, 진부화는 `dead`/`superseded` 전이 후 자가검토(`review`)로 정리한다(데이터 무손실).
```

**(d) 라이프사이클 4상태 + 트리거 (R4)** — 신설 섹션:
```markdown
## 메모리 라이프사이클

| 상태 | 의미 | 진입 트리거 | 도구 동작 |
|------|------|-----------|----------|
| `active` | 살아있는 지식. 인덱스에 노출·로드 대상 | 신규 등록(append) | 인덱스 행 유지 |
| `promoted` | 영구 거처(docs/brain)로 졸업 완료 | PM이 본문을 docs 규칙/brain 페이지로 이전했다고 판단 | `promote --to <docs\|brain>`: 이전 확인 후 인덱스 행 + `.md` 파일 삭제 + provenance 기록(SSOT 이중화 해소) |
| `superseded` | 더 새로운 메모리/결정이 대체 | PM이 대체 관계 식별 | `update --status superseded`: 행 보존(추적용), 로드 제외. 자가검토 `cleanup_candidates`로 표면화 후 명시 정리 |
| `dead` | 완료·진부화(task 완료, 이슈 해소) | task 완료 / 이슈 해소 / 철회 | `update --status dead`: 로드 제외. 자가검토 `cleanup_candidates`로 표면화 후 명시 정리 |

> **갯수 상한 없음**: 본 체계는 메모리 활성 갯수 상한을 두지 않는다(캡틴 지시 2026-06-26). 비대화 방지는 **졸업(promote)·자가검토(review)·요약 길이캡**이 담당하며, promoted/superseded/dead는 로드 대상에서 제외되어 토큰을 잠식하지 않는다.
```

**(e) 메모리 이관(졸업) 워크플로우 (R8') — 신설 섹션** ★1순위:
```markdown
## 메모리 이관(졸업) 워크플로우

메모리는 **임시 보관소**다. 성숙한 지식은 영구 거처로 졸업(promote)한다.
핵심 구분: **docs = 규범(행동을 지배)**, **brain = 설명(왜·어떻게)**.

### 라우팅 표 (졸업지 결정)

| 메모리 성격 | 졸업지 | 비고 |
|------------|--------|------|
| 행동 규칙·금지·확정 기준·선호 | `docs/AGENT.md` | feedback / preferences 유형 |
| 코드·문서 컨벤션 | `docs/CONVENTIONS.md` | — |
| 프로젝트 정의·범위 | `docs/PROJECT.md` | — |
| 설계 WHY·도메인 지식·비자명 해법 | `brain` (`//opbr ingest` / `brain-tool add-page` 재사용) | architecture / issues 유형 |
| 완료·진부화·철회 | 삭제(`dead` / `superseded` → 정리) | task 유형 |

> 메모리 `유형`이 기본 졸업지 힌트다(feedback/preferences→docs/AGENT.md, architecture/issues→brain, task→삭제).
> 최종 졸업지·성숙 여부 판단은 **PM**이 한다. 도구는 후보를 표면화(자가검토)하고 이전을 집행(promote)할 뿐이다.

### 졸업 절차 (역할 분담)

1. **PM 판단**: 자가검토 `promote_candidates`를 보고 성숙 여부 + 졸업지(docs냐 brain이냐) 결정.
2. **PM authoring**: docs면 해당 문서에 규칙 반영, brain이면 `//opbr ingest` / `brain-tool add-page`로 페이지 작성(기존 brain 파이프라인 재사용 — 중복 금지).
3. **도구 집행**: 이전 완료 확인 후 `promote --to <docs|brain> --ref <위치>`로 메모리 행 + `.md` 삭제 + provenance(삭제 전 위치·대상) 기록. 이전 미확인이면 거부(무손실).

### 자가검토 트리거

memory-tool의 모든 변경 명령(`init`/`append`/`update`/`promote`/`prune`/`migrate`) 응답 JSON에는 `review` 블록이 자동 첨부된다 → "호출할 때마다 기존 메모리·히스토리를 검토"가 ambient하게 강제된다. 단독 `review` 명령으로도 같은 health 점검을 수행한다.
```

> **[MUST] `PRINCIPLES.md` §2 Simplicity**: brain 이관은 기존 `//opbr ingest` / `brain_tool.py:465 cmd_add_page`를 재사용한다 — memory-tool에 별도 brain 쓰기 파이프라인을 재발명하지 않는다.

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음 (실데이터 변환은 F-006 도구 제공 범위).

#### 3.1.5 테스트 시나리오 (AC ↔ TS)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R1 | 산출물 검사 | 인덱스·히스토리 형식 정의 양쪽에 `제목` 컬럼이 맨 앞에 존재 |
| TS-002 | R2 | 산출물 검사 | 요약 ≤80자(1줄)·핵심결과 ≤2줄 규칙이 [MUST]로 명문화 |
| TS-003 | R3 | 산출물 검사 | 히스토리 FIFO 한도 = 5 (10 표기 부재) |
| TS-004 | R4 | 산출물 검사 | active/promoted/superseded/dead 4상태 + 각 진입 트리거·도구 동작 기술 (갯수 상한 표기 부재) |
| TS-004a | R8' | 산출물 검사 | "메모리 이관 워크플로우" 섹션에 라우팅 표(5행: docs/AGENT.md·CONVENTIONS.md·PROJECT.md·brain·삭제) + docs=규범/brain=설명 구분 + brain 재사용([MUST]) 명문화 |
| TS-004b | R6' | 산출물 검사 | 자가검토 트리거 설명(매 변경 명령 후 `review` 블록 자동 첨부) 존재 |

---

### F-002: memory-tool 도구 골격

#### 3.2.1 파일 변경 계획
**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/memory-tool/run.sh` | 도구 | venv python 래퍼 | `state-tool/run.sh:1-12` 동형 |
| 2 | `opal/tools/memory-tool/memory_tool.py` | 도구 | 디스패처 + ok/err/ERROR_CODES + 헬퍼 | `state_tool.py:121,125,68` (→ D-3) |
| 3 | `opal/tools/memory-tool/schema/memory.schema.json` | 도구 | 행 스키마 문서용 SSOT | `state-tool/schema/state.schema.json` 동형 |
| 4 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 도구 | pytest 단위 테스트 | `tool-scan/tests/` 선례 (→ D-4) |
| 5 | `opal/tools/memory-tool/README.md` | 도구 | 서브명령 사용법 | `state-tool/README.md` 동형 |

#### 3.2.2 설계 — 공통 골격 (state-tool 재사용)

**[MUST] `PRINCIPLES.md` Simplicity (§2): state-tool 함수·구조를 재사용하고 재발명 금지.** `ok`/`err`/`ERROR_CODES`/마커가드/`run.sh`를 그대로 차용한다.

**run.sh** (`state-tool/run.sh:1-12` 그대로, 스크립트명만 교체):
```bash
#!/bin/bash
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
[[ -x "$VENV_PYTHON" ]] || { echo '{"ok":false,"error":"OPAL .venv not found."}' >&2; exit 1; }
exec "$VENV_PYTHON" "$SCRIPT_DIR/memory_tool.py" "$@"
```

**memory_tool.py 응답 헬퍼** (`state_tool.py:121-139` 복사):
- `ok(command, **kwargs)` → `{"ok":True,"command":...}` 단일라인 JSON, exit 0.
- `err(command, code, message=None, exit_code=1, **kwargs)` → `ERROR_CODES[code]` 참조, `sys.exit`.

**ERROR_CODES (SSOT, memory-tool 전용)** — `state_tool.py:68` 패턴:
```python
ERROR_CODES = {
  "marker_missing":        "MEMORY.md에 <!-- memory:index:start/end --> 또는 <!-- memory:history:start/end --> 마커 누락",
  "memory_file_not_found": "<file>에 해당하는 메모리 파일이 없음: {path}",
  "row_not_found":         "--title '{title}'에 해당하는 인덱스 행이 없음",
  "memory_md_not_found":   "MEMORY.md가 존재하지 않음 — init을 먼저 실행하세요: {path}",
  "already_initialized":   "MEMORY.md 마커가 이미 존재합니다 — --force로 재삽입",
  "invalid_kind":          "--kind는 memory 또는 history 중 하나여야 함: {kind}",
  "invalid_type":          "--type {value}는 유형 enum(project/architecture/feedback/preferences/issues/task)에 없음",
  "invalid_status":        "--status {value}는 라이프사이클 enum(active/promoted/superseded/dead)에 없음",
  "summary_too_long":      "요약 {length}자 > 80자 제한 (R2) — 상세는 개별 .md 본문으로",
  "title_required":        "--title은 필수 비공백 문자열",
  "invalid_promote_target":"--to는 docs 또는 brain 중 하나여야 함: {value}",
  "promote_ref_missing":   "--ref(영구 거처 위치) 필수 — 이전 미확인 promote 거부 (무손실, H-1)",
  "import_failed":         "구포맷 MEMORY.md 파싱 실패 — 표 정규식 매칭 0건",
  "date_tool_failed":      "node ~/.opal/tools/date/date.js 호출 실패 — MEMORY.md 변경 없음(원자성)",
}
```
> `memory_limit_exceeded`는 갯수 게이트 제외(캡틴 지시)로 **삭제**. `promote --to/--ref` 무손실 가드 코드를 신설.

**마커 규약 (R9)** — `state_tool.py:105/229/302` 패턴:
```
<!-- memory:index:start -->   ... 메모리 인덱스 표 ...   <!-- memory:index:end -->
<!-- memory:history:start --> ... 작업 히스토리 표 ...   <!-- memory:history:end -->
```
- 헬퍼 `replace_marker_section(md, start, end, new_table)` (`state_tool.py:225` `replace_pipeline_section` 동형) → 마커 미발견 시 `None` 반환 → 호출자가 `marker_missing` err. **[MUST] R9: 마커 부재 시 모든 mutating 명령(append/update/promote/prune/migrate)은 `marker_missing`으로 거부한다 — LLM 직접편집 금지를 도구가 집행** (`state_tool.py:302,307` 패턴).

**서브명령 디스패처** (argparse subparsers, `state_tool.py` 하단 main 동형). **최종 서브명령 셋 8종 확정** (U-2):

| 서브명령 | 역할 | F |
|---------|------|---|
| `init` | MEMORY.md 신포맷 마커·헤더 삽입(create-if-absent) | F-006 |
| `append` | 메모리/히스토리 행 추가(`--kind` 분기, 요약 길이캡·히스토리 FIFO) | F-003/F-004 |
| `update` | 메모리 상태/요약 수정(라이프사이클 전이) | F-005 |
| `promote` | 메모리 영구 거처 졸업(`--to docs\|brain --ref` → 이전 확인 후 행+파일 삭제 + provenance) | F-005 |
| `prune` | 히스토리 FIFO=5 결정론 정리 | F-004 |
| `migrate` | 구포맷→신포맷 변환(제목 추출 + `[REVIEW]`) | F-006 |
| `show` | 인덱스/히스토리 현황 출력(read-only) | F-002 |
| `review` | 자가검토 단독 health 명령 — violations[] + 라이프사이클 후보(promote/cleanup/history/위반) 반환 | F-010 |

> **U-2 최종 결정 (8종 확정)**: `init`·`append`·`update`·`promote`·`prune`·`migrate`·`show`·`review`. 기존 `validate`는 **제거**하고 `review`가 format 위반(violations) + 라이프사이클 후보를 함께 반환하는 단일 health 명령으로 통합(Simplicity). `show`는 state-tool `show` 선례(`state_tool.py:782`)대로 read-only 조회로 유지.
> **[MUST] 자가검토 ambient 강제**: 모든 변경 명령(`init`/`append`/`update`/`promote`/`prune`/`migrate`) 응답 JSON에 `build_review_block()` 결과를 `review` 키로 자동 첨부한다 — 호출자가 매번 메모리·히스토리를 검토하도록 강제(별도 CLOSE 훅·pilot 변경 불요). 상세 설계 §3.6.2(review).

#### 3.2.3 환경 변경
- pytest는 기존 `~/.opal/.venv`에 존재(state-tool·tool-scan 동일 사용). `opal/tools/requirements.txt`(`install-mac.sh:1210`) 변경 불필요(표준 라이브러리만 사용).

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R5 | 기능 테스트 | `run.sh <서브명령>`이 `{"ok":...}` 단일라인 JSON 반환, exit code 일관 |
| TS-006 | R5 | 기능 테스트 | `ERROR_CODES` 키 외 임의 error 문자열 부재(SSOT 준수). `memory_limit_exceeded` 코드 부재(갯수 게이트 제외) |
| TS-007 | R5 | 기능 테스트 | 8개 서브명령(init/append/update/promote/prune/migrate/show/review) 모두 argparse 등록·`--help` 노출. `validate` 부재 |

---

### F-003: 마커 직접편집 금지 가드 + 요약 길이캡 검증 (갯수 게이트 제외)

#### 3.3.1 파일 변경 계획
**수정(F-002 파일 내)**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` | 도구 | `cmd_append`(memory 분기) 마커 가드 + 요약 길이캡(≤80) | R9·R2 |

#### 3.3.2 설계 — append 마커 가드 + 길이캡 (갯수 게이트 없음)

> **메모리 갯수 게이트 제외 (캡틴 지시 2026-06-26)**: 메모리 활성 상한·`MEMORY_LIMITS` 상수·`memory_limit_exceeded` 에러코드·append의 갯수 차단 로직을 **본 태스크에서 전면 제외**한다. 비대화 방지는 **졸업(promote, F-005) + 자가검토(review, F-010) + 요약 길이캡(R2)** 으로 달성한다(별도 갯수 강제 불요). 따라서 U-1(유형별 상한 12/12/8/8/8/5) 결정은 철회됐다.

append(memory)에 남는 강제는 두 가지뿐:
1. **마커 가드 (R9)**: 마커 부재 시 `marker_missing` err — LLM 직접편집 금지(`state_tool.py:302,307` 패턴). **[MUST] H-3: 마커 부재 파일은 1바이트도 건드리지 않고 거부.**
2. **요약 길이캡 (R2)**: `요약` 셀 ≤80자 위반 시 `summary_too_long` err.

**append 동작 (함수 시그니처)**:
```python
def cmd_append(args):
    # args.kind ∈ {memory, history}, args.title(필수), ...
    # 1. MEMORY.md 로드 + 마커 검증 → 부재 시 marker_missing err (R9)
    # 2. kind=memory:
    #    - args.type enum 검증 (invalid_type)
    #    - args.status default 'active', enum 검증
    #    - args.summary 길이 ≤80 검증 (summary_too_long, R2)
    #    - (갯수 게이트 없음 — 무제한 추가 허용)
    #    - 인덱스 표에 행 추가 (replace_marker_section)
    # 3. kind=history: F-004 경로(FIFO)
    # 4. 반환: ok(command, kind, title, active_count) + review 블록 자동 첨부 (F-010)
```
> `active_count`는 보고용 메타데이터일 뿐 게이트 임계값이 아니다(자가검토 `promote_candidates` 판단에만 참고).

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R2 | 기능 테스트 | summary 81자 append → `ok:false` + `summary_too_long` |
| TS-009 | R9 | 보안/기능 테스트 | 마커 제거된 MEMORY.md에 append → `ok:false` + `marker_missing`, **파일 바이트 불변** (H-3) |
| TS-010 | R9 | 기능 테스트 | 정상 append → 인덱스 행 1개 증가 + 갯수 차단 없음(다수 append 모두 성공) |
| TS-011 | R6' | 기능 테스트 | append 응답 JSON에 `review` 블록 자동 첨부(F-010 연계) |

---

### F-004: 히스토리 FIFO=5 자동 정리

#### 3.4.1 파일 변경 계획
**수정(F-002 파일 내)**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` | 도구 | `cmd_append`(history 분기) FIFO + `cmd_prune` | R7 |

#### 3.4.2 설계
```python
HISTORY_FIFO_LIMIT = 5  # SSOT (R3)

def _enforce_history_fifo(rows):
    # rows = 히스토리 표 행 리스트(추가 순서 = 표 순서, 위가 최신).
    # 추가 후 len > 5 이면 가장 오래된(맨 아래) 행부터 제거하여 정확히 5 유지.
    # 결정론: 정렬 의존 없이 표 위치(append는 맨 위 삽입) 기반.
    return rows[:HISTORY_FIFO_LIMIT]
```
- `append --kind history`: 새 행을 맨 위 삽입 → `_enforce_history_fifo` → ≤5 유지. **[MUST] R7: 6번째 추가 시 가장 오래된 1개 결정론적 제거.**
- `prune`: idempotent 정리 경로(이미 ≤5면 no-op). 

> **메모리 vs 히스토리 비대칭 [MUST]**: 메모리는 blind FIFO **금지**(차단 게이트, F-003), 히스토리는 소모성 로그라 FIFO **허용**(자동 정리). 이 비대칭은 TASK 확정 #6·R-1 근거.

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R7 | 기능 테스트 | 6개 history append 후 히스토리 행 수 = 5 (H-2) |
| TS-013 | R7 | 기능 테스트 | 6개 append 후 최초 1개가 제거되고 최신 5개 보존(순서·내용) |
| TS-014 | R7 | 기능 테스트 | `prune`이 ≤5 상태에서 no-op(idempotent) |

---

### F-005: 메모리 → 영구 거처 졸업(promote) 워크플로우 ★1순위

#### 3.5.1 파일 변경 계획
**수정(F-002 파일 내)**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` | 도구 | `cmd_update`(상태전이) + `cmd_promote`(`--to docs\|brain --ref` 이전 확인 → 행+파일 삭제 + provenance) | R8·R8' |

#### 3.5.2 설계 — promote 라우팅 + provenance + brain 재사용

**라우팅 (PM 판단, §3.1.2 (e) 라우팅 표 집행)**: `docs`=규범(AGENT.md/CONVENTIONS.md/PROJECT.md), `brain`=설명. 메모리 `유형`이 기본 졸업지 힌트. 최종 졸업지·성숙 판단은 PM, 도구는 이전 확인·삭제·provenance만 집행(역할 경계).

```python
def cmd_update(args):
    # --title 로 행 식별 (row_not_found) → --status / --summary 갱신
    # status enum 검증(invalid_status). summary 갱신 시 ≤80 검증.
    # superseded/dead 전이 = 행 보존(추적), 로드 제외. review가 cleanup 후보로 표면화.
    # 반환: ok(...) + review 블록 자동 첨부

def cmd_promote(args):
    # --to ∈ {docs, brain} 검증 (invalid_promote_target)
    # --ref 필수(영구 거처 위치: 예 'AGENT.md#금지사항' 또는 brain page 슬러그)
    #   → 미지정 시 promote_ref_missing err (이전 미확인 거부, 무손실 H-1)
    # --title 로 행 식별 → memory/<file>.md 경로 확인 (memory_file_not_found 가드)
    # [brain 경로 주의] 도구는 brain 쓰기를 재발명하지 않는다 —
    #   --to brain은 PM이 //opbr ingest / brain-tool add-page로 이미 페이지를
    #   만들었음을 전제(--ref=brain page)하고, 메모리 측 행+파일 삭제 + provenance만 집행.
    # 원자적: 인덱스 행 삭제 AND memory/<file>.md 삭제 AND provenance 기록
    #   (셋 중 하나라도 실패 시 모두 미수행 — H-4)
    # provenance: <!-- memory:provenance --> 로그(또는 인접 .promoted 노트)에
    #   '삭제 전 제목/유형/요약 + to + ref + 일시(KST)' 1행 추가 → 어디로 갔는지 추적.
    # 반환: ok(command, title, to, ref, file_deleted=True, row_removed=True, provenance_logged=True)
```
- **[MUST] promote 무손실 (H-1)**: `--ref`(영구 거처 위치)와 `--to`가 모두 주어지고 대상 메모리 파일이 실재할 때만 삭제한다. 이전 미확인 시 거부 — blind 삭제 절대 금지. 지식은 영구 거처로 이미 이전됐기에 무손실.
- **[MUST] `PRINCIPLES.md` §2 Simplicity (H-9)**: brain 이관은 `//opbr ingest` / `brain_tool.py:465 cmd_add_page` 재사용. memory-tool은 brain 쓰기 파이프라인을 자체 구현하지 않는다.
- dead/superseded 행의 실제 삭제는 promote 미해당 — `update`로 상태만 전이하고 자가검토 `cleanup_candidates`로 표면화 후 명시 정리.

#### 3.5.3 환경 변경 / 3.5.4 배치
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-015 | R8/R8' | 기능 테스트 | `promote --to docs --ref AGENT.md#금지사항` → 인덱스 행 부재 AND `memory/X.md` 부재 AND provenance 1행 기록 (H-4) |
| TS-016 | R8'/H-1 | 기능 테스트 | `--ref` 미지정 promote → `ok:false`+`promote_ref_missing`, **행·파일 불변**(무손실) |
| TS-017 | R8' | 기능 테스트 | `--to brain` 경로가 brain 쓰기를 자체 구현하지 않음(메모리 측 삭제+provenance만) — brain 페이지 생성은 brain-tool 재사용 전제 (H-9) |
| TS-018 | R8 | 기능 테스트 | promote 대상 파일 부재 시 `ok:false`+`memory_file_not_found`, 행 보존(원자성) |
| TS-019 | R8/`--to` | 기능 테스트 | `--to` enum 외 값 → `ok:false`+`invalid_promote_target` |
| TS-020 | R4/R8 | 기능 테스트 | `update --status dead`/`superseded` → 행 보존 + 로드 제외 표시 |

---

### F-006: init / migrate

#### 3.6.1 파일 변경 계획
**수정(F-002 파일 내)**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` | 도구 | `cmd_init`(마커 삽입) + `cmd_migrate`(구→신) | R9·U-3 |

> `validate`는 제거하고 정합성 검증을 `review`(F-010)로 통합 — 설계는 §3.10.2(review) 참조.

#### 3.6.2 설계

**U-3 결정 — migrate 범위 (도구 제공까지)**:

> **제목 자동 추출 + `needs_review` 플래그 (반자동)** — 완전 자동도 PM 수동도 아닌 중간.

- 구포맷 표를 정규식 파싱(`state_tool.py:579 parse_existing_state_md` 동형: `^\|\s*([^|]+?)\s*\|...`).
- **제목 자동 추출 규칙**: 기존 `설명`/`작업` 셀의 **첫 문장 또는 첫 30자**(구두점·줄바꿈 전까지)를 제목 후보로 추출. 추출 행에 `<!-- needs_review -->` 인라인 마커 또는 `요약` 셀 접두 `[REVIEW] `를 부착하여 PM 보정 필요를 명시.
- **상태 매핑**: 구포맷 자유 상태값 → 신 enum 보수 매핑:
  | 구 상태값 | 신 상태 |
  |----------|--------|
  | `대기`/`예정`/`유지`/`active`/`진행` | `active` |
  | `완료`/`~~완료~~` | `dead` |
  | `폐기 기록`/`폐기` | `superseded` |
  | (불명) | `active` + `[REVIEW]` |
- **무손실**: 원 `설명`/`작업` 전문은 truncate하지 않고 신 `요약`(≤80 초과 시) 대신 **개별 `.md` 본문으로 이동하거나 `[REVIEW]` 표기 후 PM이 분할**. migrate는 80자 초과 시 자동 truncate 금지(`[REVIEW]` + 원문은 별도 보존 노트). **[MUST] H-5: migrate는 행수를 보존하고 어떤 셀도 정보 소실 없이 변환 — 길이 초과는 truncate가 아니라 review 플래그.**
- **범위 한계**: migrate는 **도구 제공까지**. 실제 실행(이 프로젝트 `.opal/MEMORY.md` 변환 포함)은 각 프로젝트 운영(TASK 범위 확정). EXECUTE에서 도구만 만들고 실데이터는 안 건드린다.

```python
def cmd_init(args):
    # MEMORY.md 부재/마커 부재 시 신포맷 마커·헤더·빈 표 삽입.
    # 마커 이미 존재 + not --force → already_initialized.

def cmd_migrate(args):
    # 1. 기존 MEMORY.md 로드 (memory_md_not_found 가드)
    # 2. 구포맷 인덱스/히스토리 표 정규식 파싱 (import_failed if 0건)
    # 3. 제목 추출 + 상태 매핑 + [REVIEW] 플래그
    # 4. 신포맷 마커·표로 재작성 + 히스토리 FIFO=5 적용
    # 5. 반환: ok(command, memory_rows, history_rows, review_count)
    #    + review 블록 자동 첨부. migrate가 단 [REVIEW] 행은 review의
    #      promote_candidates에 표면화되어 PM 보정을 유도.
```
> 정합성 검증(`validate`)은 별도 명령으로 두지 않고 `review`(§3.10.2)가 violations로 흡수한다 — 단일 health 명령(Simplicity).

#### 3.6.3 환경 변경 / 3.6.4 배치
해당 없음.

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-021 | R9(마커) | 기능 테스트 | `init` → MEMORY.md에 4개 마커(index/history start·end) 삽입 |
| TS-022 | R9 | 기능 테스트 | 마커 존재 + `init`(no --force) → `already_initialized` |
| TS-023 | U-3 | 기능 테스트 | 구포맷 6행 fixture → migrate → 신포맷 6행 + 각 제목 비공백 + review_count 보고 (H-5) |
| TS-024 | U-3 | 기능 테스트 | 80자 초과 구 설명 → truncate 없이 `[REVIEW]` 플래그 (무손실) |

---

### F-010: 자가검토 review 서브명령

#### 3.10.1 파일 변경 계획
**수정(F-002 파일 내)**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` | 도구 | `build_review_block()` 헬퍼 + `cmd_review`(단독 health) + 매 변경 명령 응답에 자동 첨부 | R6'·R5 |

#### 3.10.2 설계 — review 블록 (결정론적 휴리스틱)

**[MUST] 역할 경계 (H-8)**: review는 *후보 표면화*만 한다 — 졸업지(docs냐 brain이냐)·성숙 여부 판단은 PM. 도구는 결정론적 휴리스틱(임계값 상수 SSOT)만 적용하고 어떤 행도 단정하지 않는다.

```python
PROMOTE_AGE_DAYS = 30   # SSOT 임계값 — 이보다 오래된 active는 promote 후보

def build_review_block(md):
    # 결정론적 휴리스틱만. read-only. 반환 dict:
    # {
    #   "promote_candidates": [...],   # 오래된 active(등록일 diff ≥ PROMOTE_AGE_DAYS)
    #                                  #  + migrate가 단 [REVIEW] 플래그 행
    #   "cleanup_candidates": [...],   # 물리적으로 남은 dead/superseded 행
    #   "history_status": {"fifo_trimmed": bool, "count": int},
    #   "violations": [...],           # 마커·요약 길이>80·type/status enum format 위반
    # }
    # ※ 졸업지·성숙은 판단하지 않는다(후보만). 라우팅 힌트로 유형만 같이 노출.

def cmd_review(args):
    # 단독 health 명령: build_review_block 결과를 ok(...)로 반환.
    # project-init 검증(구 TS-024)은 violations == [] 로 확인.
```
- **[MUST] ambient 강제 (R6')**: `init`/`append`/`update`/`promote`/`prune`/`migrate` 각 `cmd_*`의 `ok(...)` 반환 직전에 `build_review_block(md)`를 호출해 `review` 키로 첨부 → 호출자가 매번 메모리·히스토리를 검토하게 강제(별도 CLOSE 훅·pilot 변경 불요).
- **validate 흡수**: 기존 `validate`의 violations 검출을 `review.violations`가 담당(단일 health 명령, Simplicity).

#### 3.10.3 환경 변경 / 3.10.4 배치
해당 없음.

#### 3.10.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-025 | R6' | 기능 테스트 | 모든 변경 명령(init/append/update/promote/prune/migrate) 응답 JSON에 `review` 키 존재 (ambient 강제) |
| TS-026 | R6' | 기능 테스트 | `review`가 마커 부재·요약>80·enum format 위반을 `violations[]`로 검출 (validate 흡수) |
| TS-027 | R6'/H-8 | 기능 테스트 | `review.promote_candidates`는 후보 행만 표면화(졸업지 docs/brain 단정 없음) — 역할 경계 |
| TS-028 | R6' | 기능 테스트 | `cleanup_candidates`가 물리적으로 남은 dead/superseded 행을 표면화 |

---

### F-007: project-init MEMORY.md 템플릿 동기화

#### 3.7.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-project-init/SKILL.md` | 스킬 | `2-4. MEMORY.md 형식` 인라인 템플릿 교체(:408) | `opal-project-init/SKILL.md:408` (→ D-7) |

#### 3.7.2 설계 — 신포맷 템플릿 초안
`SKILL.md:410-415` 교체:
```markdown
**2-4. MEMORY.md 형식** (memory-tool 호환 신포맷 — 045)

\`\`\`markdown
# {프로젝트명} 프로젝트 Memory Index

> 최종 갱신: {YYYY-MM-DD}
> last_task_number: 0

## 메모리
<!-- memory:index:start -->
| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
|------|--------|------|------|------|------|
<!-- memory:index:end -->

## 작업 히스토리 (최대 5개, FIFO)
<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
<!-- memory:history:end -->
\`\`\`

> 메모리 행 추가·정리·이관은 **memory-tool로만** 수행한다(직접 편집 금지). 상세 형식·라이프사이클: `memory-learning.md`.
```

> **[MUST] 변경이력**: `opal-project-init/SKILL.md` §변경이력에 045 행 추가.

#### 3.7.3 환경 변경 / 3.7.4 배치
해당 없음.

#### 3.7.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-029 | R10 | 산출물 검사 | 템플릿에 제목 컬럼·4개 마커·FIFO5·직접편집 금지 안내 존재 |
| TS-030 | R10/R9 | 통합 테스트 | 템플릿으로 만든 MEMORY.md를 memory-tool `review` → `violations == []` (형식 호환, 구 project-init 검증) |

---

### F-008: install 등록

#### 3.8.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 환경 | memory-tool run.sh chmod +x 블록 추가 | `install-mac.sh:1087-1091` (→ D-8) |

#### 3.8.2 설계
`install-mac.sh:1091` tool-scan 블록 직후 삽입(동형):
```bash
# ── memory-tool 실행 권한 (045) ──
local memory_run="$opal_home/tools/memory-tool/run.sh"
if [[ -f "$memory_run" ]]; then
    chmod +x "$memory_run"
    success "memory-tool run.sh 실행 권한 설정"
fi
```
> install_dir(`:1044`)가 전체 복사하므로 디렉토리 추가 불필요. chmod만 추가.

#### 3.8.3 환경 변경 / 3.8.4 배치
해당 없음. (캡틴 install 재배포는 별도 — 소스가 SSOT, 배포 경계 제약)

#### 3.8.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-031 | R11 | 산출물 검사 | install-mac.sh에 memory-tool chmod 블록 존재 + tool-scan 블록 패턴 동형 |

---

### F-009: drift 정합 (tools.md + harness §9)

#### 3.9.1 파일 변경 계획
**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-harness.md` | 가이드 | §9 도구 테이블 memory-tool 행 추가(:248 이후) | `opal-harness.md:242-248` (→ D-5) |
| 2 | `opal/core/references/tools.md` | 가이드 | 도구 테이블 + 사용법 섹션 memory-tool 추가 | `opal/core/references/tools.md` (→ D-6) |

#### 3.9.2 설계 — 동일 행 문안
harness §9 + tools.md 양쪽 동일:
```markdown
| memory-tool | 프로젝트 메모리 인덱스·히스토리 결정론적 집행 — 8서브명령 init/append/update/promote/prune/migrate/show/review. 메모리 → docs/brain 졸업(promote, 무손실+provenance)·자가검토(review 매 호출 첨부)·히스토리 FIFO5·라이프사이클·마커 직접편집 금지 | 메모리 등록·정리·이관 시 |
```
> **[MUST] H-7: 두 테이블의 memory-tool 행은 동일 문자열** (044 7도구 정합 선례).
> tools.md 사용법 섹션도 8서브명령(특히 `promote --to docs\|brain --ref`·`review`)을 반영하고 "갯수 게이트" 문구를 쓰지 않는다.

#### 3.9.3 환경 변경 / 3.9.4 배치
해당 없음.

#### 3.9.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-032 | R12 | 산출물 검사 | tools.md ↔ harness §9 memory-tool 행 동일 + 8서브명령(init/append/update/promote/prune/migrate/show/review) 명시, "갯수 게이트" 문구 부재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 순차 | SSOT 형식 + 이관 워크플로우·자가검토 먼저 확정(파서·계약) |
| 2 | F-002~F-006, F-010 | 2(RED), 3(GREEN) | opal-test-agent → opal-be-agent | RED→GREEN 순차 | 작성자≠구현자(self-confirming 고위험) |
| 3 | F-007, F-008, F-009 | 4, 5, 6 | opal-task-agent | 병렬 가능 | 도구 완성 후 독립 정합 |
| 4 | 회귀·문서 | 7, 8 | opal-task-agent / PM 직접 | 순차 | docs 갱신 + 회귀 |

### 4.2 실행 체크리스트

> 총 8개 Step | Phase 4개 | 실행 모드: **복잡**

#### Step 1: memory-learning.md SSOT 개정
- [x] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/memory-learning.md`
- **작업 내용**: §3.1.2 (a)~(d) 문안으로 인덱스/히스토리 형식 제목 컬럼·길이캡(요약 ≤80/핵심결과 ≤2줄) 교체, FIFO 10→5, 라이프사이클 4상태 섹션 신설, 마커 규약 기술. 변경이력 v1.1 행 추가.
- **완료 기준**: TS-001~004 산출물 검사 통과 — 제목 컬럼 맨앞·[MUST] 길이캡·FIFO5·4상태+트리거 모두 존재.
- **테스트**: TS-001, TS-002, TS-003, TS-004
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: memory-tool RED 테스트 작성 (작성자)
- [ ] 완료
- **소속 기능**: F-002, F-003, F-004, F-005, F-006, F-010
- **영역**: 도구
- **agent**: opal-test-agent
- **파일**: `opal/tools/memory-tool/tests/test_memory_tool.py` (+ fixtures)
- **작업 내용**: TS-005~028(골격/마커가드·길이캡/FIFO/promote 라우팅·provenance/migrate/자가검토 review) 전부에 대해 **실패하는** pytest 테스트 작성. 구현 부재 상태에서 RED 확인. 마커가드(H-3)·promote 무손실(H-1, `--ref` 미지정 거부+행/파일 불변)·FIFO(H-2)·promote 원자성+provenance(H-4)·migrate 무손실(H-5)·자가검토 역할경계+ambient(H-8)는 강한 assertion(행수/바이트 불변, review 키 존재)으로. **갯수 게이트 TS 없음**(`memory_limit_exceeded` 부재 검증 포함).
- **완료 기준**: 모든 테스트가 RED(import/구현 부재로 FAIL) — RED 증거 캡처. 테스트 자체에 mock으로 자기검증 금지(헌법 §4).
- **테스트**: RED 증거 = 실패 출력 캡처
- **실행 방법**: sub-agent
- **의존**: Step 1 (형식·이관 워크플로우·자가검토 계약 확정 후 테스트 작성)

#### Step 3: memory-tool 구현 GREEN (구현자)
- [x] 완료
- **소속 기능**: F-002, F-003, F-004, F-005, F-006, F-010
- **영역**: 도구(BE/Python)
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/{run.sh, memory_tool.py, schema/memory.schema.json, README.md}`
- **작업 내용**: §3.2~§3.6 + §3.10 설계대로 8서브명령(init/append/update/promote/prune/migrate/show/review) 구현. state-tool `ok`/`err`/`ERROR_CODES`/`replace_marker_section`/`run.sh` 재사용. HISTORY_FIFO_LIMIT=5·PROMOTE_AGE_DAYS 상수 SSOT. **갯수 상한 상수(MEMORY_LIMITS) 없음**. promote brain 경로는 brain-tool 재사용(자체 brain 쓰기 금지, H-9). 매 변경 명령 응답에 `review` 블록 자동 첨부. 표준 라이브러리만.
- **완료 기준**: Step 2의 RED 테스트 전부 GREEN. **테스트 파일 미수정**(RED 불변 가드).
- **테스트**: TS-005~028 GREEN
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: project-init 템플릿 동기화
- [x] 완료
- **소속 기능**: F-007
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-project-init/SKILL.md`
- **작업 내용**: §3.7.2 신포맷 템플릿으로 `2-4. MEMORY.md 형식`(:408) 교체. 변경이력 045 행 추가.
- **완료 기준**: TS-029 통과 + TS-030(템플릿→`review` violations == []).
- **테스트**: TS-029, TS-030
- **실행 방법**: sub-agent
- **의존**: Step 1(형식), Step 3(review 도구)

#### Step 5: install 등록
- [x] 완료
- **소속 기능**: F-008
- **영역**: 환경
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: §3.8.2 memory-tool chmod 블록을 tool-scan 블록(:1091) 직후 삽입.
- **완료 기준**: TS-028 — 블록 존재 + 동형 패턴.
- **테스트**: TS-028
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 6: drift 정합 (tools.md + harness §9)
- [ ] 완료
- **소속 기능**: F-009
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-harness.md`, `opal/core/references/tools.md`
- **작업 내용**: §3.9.2 동일 행으로 양쪽 도구 테이블에 memory-tool 추가. tools.md에 8서브명령(promote --to docs|brain·review 포함) 사용법 섹션 추가, "갯수 게이트" 문구 미사용. 변경이력 045 행.
- **완료 기준**: TS-029 — 두 테이블 동일 문자열 + 8서브명령 + "갯수 게이트" 부재.
- **테스트**: TS-029
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 7: 회귀 + 보안 점검
- [ ] 완료
- **소속 기능**: 전체
- **영역**: 도구
- **agent**: opal-test-agent
- **파일**: `opal/tools/` 전체 pytest
- **작업 내용**: state-tool·tool-scan·brain-tool 등 기존 pytest 전체 실행으로 회귀 0 확인. memory-tool 보안 점검(경로 화이트리스트·파일 삭제 경로 검증·시크릿 0·ReDoS 없는 정규식).
- **완료 기준**: 기존 테스트 회귀 0(pre-existing 실패는 명시 구분), memory-tool 보안 항목 Pass.
- **테스트**: 전체 pytest GREEN + 보안 체크리스트(§5.4)
- **실행 방법**: sub-agent
- **의존**: Step 3, 4, 5, 6

#### Step 8: docs/ 갱신 (새 도구 등록)
- [ ] 완료
- **소속 기능**: 전체
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md` (도구 컴포넌트), 필요 시 `docs/CONVENTIONS.md`(메모리 관리 규칙)
- **작업 내용**: memory-tool 신설을 시스템 구조 문서에 반영(새 패턴/도구 도입 → ARCHITECTURE/CONVENTIONS). docs/PROJECT.md MEMORY.md 설명 정합 확인.
- **완료 기준**: ARCHITECTURE.md에 memory-tool 도구 행/설명 반영, drift 0.
- **테스트**: 문서 cross-check (PM Gate)
- **실행 방법**: direct
- **의존**: Step 6

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 형식 정의(F-001)가 파서 테스트 계약 — 형식 확정 후 RED 작성 |
| Step 2 → Step 3 | RED-first: 작성자(test)≠구현자(be). RED 캡처 후 GREEN |
| Step 3 → Step 4·5·6 | 도구 완성 후 정합 작업(review 도구 의존·chmod·테이블) |
| Step 4 ∥ Step 5 ∥ Step 6 | 독립 파일(스킬/install/문서) — 병렬 가능 |
| Step 4·5·6 → Step 7 | 모든 변경 후 회귀 |
| Step 6 → Step 8 | drift 정합 후 docs 반영 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 제목 컬럼·길이캡·FIFO5·라이프사이클·이관 워크플로우·자가검토 명문화 | TS-001~004, TS-004a, TS-004b | 6항목 모두 존재 + [MUST] 토큰 + 라우팅 표 5행 |
| F-002 | 도구 골격(JSON·ERROR_CODES·8서브명령) | TS-005~007 | ok/err 계약 + 임의 error 부재 + `memory_limit_exceeded`/`validate` 부재 |
| F-003 | 마커 가드·요약 길이캡 (갯수 게이트 제외) | TS-008~011 | 마커 부재 거부+바이트 불변, summary>80 거부, 다수 append 무차단 |
| F-004 | 히스토리 FIFO=5 | TS-012~014 | 6개 후 5개, 최신 보존, prune idempotent |
| F-005 | promote 라우팅·무손실·provenance·원자성·brain 재사용 | TS-015~020 | --ref 미지정 거부+불변, 행+파일+provenance 원자, brain 자체구현 부재 |
| F-006 | init 마커·migrate 무손실 | TS-021~024 | 마커 삽입, migrate 행수 보존+제목 추출+`[REVIEW]` |
| F-007 | project-init 템플릿 신포맷 | TS-029~030 | 컬럼·마커 존재 + review violations 0 |
| F-008 | install 등록 | TS-031 | chmod 블록 동형 |
| F-009 | drift 정합 | TS-032 | 두 테이블 동일 + 8서브명령 + "갯수 게이트" 부재 |
| F-010 | 자가검토 review(ambient 첨부·역할 경계·validate 흡수) | TS-025~028 | 모든 변경 명령 응답에 review 키, 후보만 표면화, violations 검출 |

### 5.2 회귀 테스트
- [ ] state-tool 기존 pytest 회귀 0 (pre-existing 실패 명시 구분)
- [ ] tool-scan / brain-tool / test-tool pytest 회귀 0
- [ ] `.opal/MEMORY.md` 실데이터는 EXECUTE에서 미변경(도구 제공까지 — TASK 범위)

### 5.3 코드/문서 품질
- [ ] memory_tool.py 표준 라이브러리만 import (state-tool 동형)
- [ ] ruff 경고 신규 0 (불가피 시 명시)
- [ ] 변경 문서(memory-learning.md / project-init SKILL / harness / tools.md) 변경이력 045 행 추가
- [ ] 영역 간 용어 일관(active/promoted/superseded/dead, 요약 ≤80, 핵심결과 ≤2줄)

### 5.4 보안
- [ ] `.env`/시크릿 파일 .gitignore 포함 (해당 없음 — 신규 시크릿 없음)
- [ ] 하드코딩 토큰/시크릿 0
- [ ] promote 파일 삭제 경로 화이트리스트(`memory/` 하위만, 경로 탈출 `..` 차단)
- [ ] migrate/append 정규식 ReDoS 없음(state-tool 파서 패턴 동형, 백트래킹 폭발 없는 형태)
- [ ] 도구가 MEMORY.md 외 임의 파일 쓰기·삭제 불가(경로 가드)
- [ ] promote `--to brain`이 brain 디렉토리에 직접 쓰지 않음(brain-tool 재사용 전제, 자체 brain 쓰기 경로 부재 — H-9)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 8개 | 복잡 |
| 변경 파일 수 | 신규 5 + 수정 5 = 10개 | 복잡 |
| 모듈 범위 | 도구 신설 + 가이드 + 스킬 + install (다중) | 복잡 |
| 작업 유형 | 신규 도구 개발 + SSOT 개정 (대규모 개선) | 복잡 |
| 외부 의존성 | 신규 도구(memory-tool) | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
```
Batch 1: [opal-task-agent: Step 1 (F-001 SSOT + 이관 워크플로우·자가검토)]
            ↓ (형식·계약 확정)
Batch 2: [opal-test-agent: Step 2 (RED, F-002~006·F-010)] → [opal-be-agent: Step 3 (GREEN)]
            ↓ (도구 완성: 8서브명령 + review ambient 첨부)
Batch 3: [opal-task-agent: Step 4 ∥ Step 5 ∥ Step 6]  (병렬)
            ↓
Batch 4: [opal-test-agent: Step 7 회귀·보안] → [PM 직접: Step 8 docs]
```
- **파일 충돌 방지**: Step 2·3은 동일 memory-tool 디렉토리 → 순차 분리(RED 작성자 ≠ GREEN 구현자, 자기검증 회피).
- **F-010(review)는 별도 Step 아님**: 모든 변경 명령(F-002~006) 구현 안에 `build_review_block` 첨부가 녹아 있어 Step 3에 포함.
- **모듈 응집**: 정합 작업(4/5/6)은 서로 다른 파일 → 병렬.

### C-2. 스킬 요구사항
- 기존 스킬로 충분: op-dev-execute(BE/도구 구현), op-dev-test-agent(RED·회귀). 신규 스킬 갭 없음.
- 도구 구현 패턴은 state-tool/tool-scan 소스가 레퍼런스 — 별도 스킬 불요.

### C-3. 도구 요구사항
- CLI: 기존 `~/.opal/.venv` pytest. 신규 패키지 없음(표준 라이브러리만).
- `node ~/.opal/tools/date/date.js`(append 등록일 — KST). state-tool 동형.
- MCP: 불요(내부 도구, federation 불필요 — ANALYSIS §1.3).

### C-4. 테스트 전략 (opal-test-agent)
- **RED-first**(Step 2): TS-005~028, 작성자=opal-test-agent, mock 자기검증 금지(헌법 §4).
- **GREEN**(Step 3): 구현자=opal-be-agent, 테스트 파일 불변 가드.
- **회귀**(Step 7): `opal/tools/*/tests/` 전체 pytest. pre-existing 실패(state-tool·test-tool 등 043 이전) 명시 구분(044 선례).
- **보안**: 경로 화이트리스트·시크릿 스캔·ReDoS·파일 삭제 경로 가드 + brain 자체쓰기 부재(§5.4).
- **무손실 강조 검증**: H-1(promote `--ref` 미지정 거부+행/파일 불변)·H-3(바이트 불변)·H-5(정보 소실 0)는 byte/count assertion으로 강하게. H-8(자가검토 ambient 키 존재·후보만 표면화)은 review 키·후보 단정 부재로 검증.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 구현 | Python 3 (표준 라이브러리만, pytest) | state-tool 소스 패턴 (modern-python 미적용 — venv stdlib-only 유지) |
| 래퍼 | Bash (run.sh) | state-tool/run.sh 동형 |
| 형식 정의 | Markdown / 정규식 파서 | memory-learning.md |
| 배포 | Bash (install-mac.sh) | tool-scan install 블록 선례 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 내부 도구라 외부 라이브러리 API 조회 불요. context7/shadcn 해당 없음. |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | memory-learning.md (SSOT) | `opal/core/references/harness/memory-learning.md:17,18,22` | 개정 대상 — 형식·FIFO·라이프사이클 |
| D-2 | 설계 | PRINCIPLES.md (헌법) | Core Stance "Enforce, don't advise" / §2 Simplicity / §4 self-confirming | 집행 철학·재사용·RED-first 근거 |
| D-3 | 소스 | state-tool | `opal/tools/state-tool/state_tool.py:68,121,125,229,302` | ok/err/ERROR_CODES/마커가드 재사용 |
| D-4 | 소스 | tool-scan (044) | `opal/tools/tool-scan/` | 신규 도구 선례 — RED-first·install·drift |
| D-5 | 설계 | opal-harness.md §9 | `opal/core/references/opal-harness.md:242-248` | 도구 테이블 drift 정합 |
| D-6 | 설계 | tools.md | `opal/core/references/tools.md` (소스 실재 확인) | 도구 테이블 drift 정합 |
| D-7 | 소스 | opal-project-init | `opal/skills/opal-project-init/SKILL.md:408` (★인라인) | MEMORY.md 템플릿 동기화 |
| D-8 | 소스 | install-mac.sh | `scripts/install-mac.sh:1044,1087-1091` | memory-tool chmod 등록 |
| D-9 | 소스 | brain-tool | `opal/tools/brain-tool/brain_tool.py:465 cmd_add_page` + `//opbr ingest` | promote `--to brain` 이관 재사용(Simplicity, 재발명 금지) |

> **[MUST] `docs/CONVENTIONS.md` 참조**: 도구·배포 경계 규칙 — 프로젝트 소스(`opal/`,`scripts/`)만 수정, `~/.opal/` 직접 편집 금지(`.opal/AGENT.md` §금지사항). 워커 dev 배포는 아티팩트, SSOT는 소스.
> **[MUST] `PRINCIPLES.md` Core Stance**: "Enforce, don't just advise" — 자가검토 `review`는 매 변경 명령 응답에 자동 첨부되어 메모리 검토를 ambient하게 집행한다(산문 안내 아님).
> **[MUST] 데이터 무손실**: 메모리 blind 삭제 금지. `promote`는 영구 거처 이전(`--to`+`--ref`) 확인 후에만 삭제하며 provenance를 기록한다.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | promote가 이전 미확인 상태에서 메모리 삭제(blind) | F-005 | P0 | `--to`+`--ref` 필수 게이트(미지정 거부), TS-016 행/파일 불변 + provenance 기록 |
| H-2 | FIFO off-by-one | F-004 | P1 | HISTORY_FIFO_LIMIT 상수 + TS-012/013 |
| H-3 | 마커 부재 파일 파괴 | F-003/F-006 | P0 | marker_missing 가드(state_tool.py:302 동형), TS-009 바이트 불변 |
| H-4 | promote 행/파일 비원자 + provenance 누락 | F-005 | P1 | 원자적 삭제(셋 다 또는 미수행), TS-015 |
| H-5 | migrate 정보 소실 | F-006 | P1 | truncate 금지+[REVIEW] 플래그, TS-023/024 행수 보존 |
| H-6 | 형식-파서 컬럼 불일치 | F-001/F-002 | P0 | Step1→Step2 순서(형식 먼저), 문서-코드 cross-check |
| H-7 | tools.md↔harness drift | F-009 | P2 | 동일 문자열 행, TS-032, 044 선례 |
| H-8 | 자가검토 역할 경계 붕괴(도구가 판단 침범) / review 블록 누락 | F-010 | P1 | review는 후보만 표면화(판단=PM), 매 변경 명령 응답에 review 키, TS-025/027 |
| H-9 | promote brain 경로 재발명(중복 파이프라인) | F-005 | P2 | brain-tool `add-page`/`//opbr ingest` 재사용, TS-017 자체쓰기 부재 |
| R-3 | self-confirming 거짓 GREEN | F-002~006, F-010 | P0 | RED-first 작성자≠구현자(044/039 선례), mock 자기검증 금지 |
| R-4 | 배포본만 수정·소스 누락 | 전체 | P1 | 배포 경계 — 소스만 수정, install 재배포는 캡틴 |

### 9.1 요구사항 매핑 (R↔F↔상태)
| R | 내용 | F | 상태 |
|---|------|---|------|
| R1 | 제목 컬럼 | F-001 | 채택 |
| R2 | 길이 캡(요약≤80·핵심결과≤2줄) | F-001, F-003 | 채택 |
| R3 | 히스토리 FIFO 5 | F-001, F-004 | 채택 |
| R4 | 라이프사이클 4상태 | F-001, F-005 | 채택 |
| R5 | memory-tool 골격 | F-002 | 채택 |
| **R6** | **메모리 갯수 게이트** | — | **제외 (캡틴 지시 2026-06-26)** — 졸업·자가검토·길이캡으로 대체 |
| **R6'** | **자가검토 트리거** (매 변경 명령 후 `review` 블록 자동 첨부 + 단독 health 명령) | F-010 | **신규 채택** |
| R7 | 히스토리 FIFO 집행 | F-004 | 채택 |
| R8 | promote/정리 서브명령 | F-005 | 채택 |
| **R8'** | **promote 라우팅** (메모리 성격별 졸업지: docs=규범 / brain=설명, 유형 힌트, 라우팅 표) | F-001, F-005 | **신규 채택** |
| R9 | 테이블 직접편집 금지 집행(마커 가드) | F-003, F-006 | 채택 |
| R10 | project-init 템플릿 | F-007 | 채택 |
| R11 | install 등록 | F-008 | 채택 |
| R12 | drift 정합 | F-009 | 채택 |
