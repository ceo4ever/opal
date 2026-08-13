# PLAN: 프로젝트 메모리 SSOT를 MEMORY.md → MEMORY.json으로 전환

> 작성일: 2026-07-28 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (F-001 ~ F-012)
> 실행 모드: **복잡** (§6)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

프로젝트 메모리 인덱스·히스토리의 SSOT를 `.opal/MEMORY.md`(마커+마크다운 표)에서 `.opal/MEMORY.json`(문서 스키마 검증 JSON)으로 전환한다. 1순위 정당화는 **도구 정확성**(마커·표 파싱 취약 계층 소멸)이며, 토큰 절약은 **브리핑을 `show --brief` 필터 조회로 교체**한 지분과 **규범 문서 슬림화** 지분에서 나온다.

> **[MUST] `TASK.md` §배경 분석 (2)**: "행 단위로는 JSON이 md보다 무겁다 — 키 이름이 행마다 반복되어 행당 약 45 B 손해." → 본 PLAN 어디에서도 토큰 절약을 JSON 포맷 자체의 효과로 서술하지 않는다. 절약 귀속은 ① 조회 경로 전환(`show --brief`) ② 규범 문서 슬림화(마커 규약 소멸) 두 가지뿐이다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 문서 스키마 재설계 + 표준 라이브러리 런타임 검증기 | R-1 | P0 | 없음 |
| F-002 | memory-tool JSON I/O 전환 (공통 로더·락·원자적 쓰기·8서브명령) | R-2 | P0 | F-001 |
| F-003 | `show --brief` 필터 신설 | R-3 | P0 | F-002 |
| F-004 | lazy 자동 마이그레이션 + `.bak` 보존 + 구 `migrate` 삭제 | R-5 | P0 | F-002 |
| F-005 | `task-number` 서브명령 신설 + 채번 절차 tool-gated 개정 | (D-1, R-2 확장) | P0 | F-002 |
| F-006 | PM 브리핑 경로 전환 (`show --brief`) | R-4 | P1 | F-003 |
| F-007 | `memory-learning.md` 슬림화 | R-6 | P1 | F-001 |
| F-008 | improve-tool 위임 경로 전환 | R-7 | P1 | F-002, F-004 |
| F-009 | dashboard 소비자 전환 (파서·라우터·doctor) | R-8 | P1 | F-002 |
| F-010 | `opal-project-init` 템플릿 전환 | R-9 | P1 | F-002 |
| F-011 | 구형 참조 전수 정리 + pre-045 stale 서술 정정 | R-10(a), D-5 | P1 | F-002~F-006 |
| F-012 | 배포 + 3프로젝트 마이그레이션 실증 + 신형 채택 검증 | R-10(b) | P0 | F-001~F-011 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ── F-002 ─┬─ F-003 ── F-006 ─┐
                │                   │
                ├─ F-004 ── F-008 ──┤
                │                   │
                ├─ F-005 ──────────-┤
                │                   ├── F-011 ── F-012
                ├─ F-009 ───────────┤
                │                   │
                └─ F-010 ───────────┤
                                    │
F-001 ── F-007 ─────────────────────┘
```

**병렬 가능 지점**: F-003 / F-004 / F-005는 F-002 완료 후 서로 독립이나 **동일 파일(`memory_tool.py`)을 수정**하므로 같은 에이전트에서 순차 처리한다(plan-guide C-1 §1 파일 충돌 방지). F-006~F-010은 서로 다른 파일이므로 진짜 병렬이다.

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. ANALYSIS §5 R-T1~R-T8을 전량 흡수한다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-004 lazy 변환기 (`_migrate_md_to_json`) | **무성 유실** — 히스토리 표 헤더 변형(invest-stock `#\|작업\|단계\|경로\|시작일시\|완료일시`)을 인식 못 해 3행이 조용히 0행이 된다 (R-T3) | **P0** | L1(변형별 단위) + L2(실 파일 3종 대조) | TS-015, TS-035 |
| H-2 | F-004 + F-008 경쟁조건 | improve-tool이 `record`를 연속 호출하면 최초 변환 도중 두 번째 프로세스가 동시 진입 → json 클로버(A가 append한 행이 B의 재변환으로 소실) (R-T ANALYSIS §A-4) | **P0** | L2(멀티프로세스 동시 실행 통합) | TS-018, TS-020 |
| H-3 | F-001 스키마 enum ↔ 코드 enum | 스키마에 `improvement`/`candidate`가 없어(R-T4) 런타임 검증 도입 즉시 improve-tool 위임이 `schema_validation_failed`로 거부된다 | **P0** | L1(enum 동일성 단정) + L2(improve-tool 왕복) | TS-005, TS-024 |
| H-4 | F-002 CLI 응답 계약 | `show`의 `index_rows`/`history_rows` 키 이름이 바뀌면 improve-tool `cmd_list`(`data.get("index_rows")`, `improve_tool.py:311`)가 조용히 빈 목록을 반환한다 | P1 | L1(키 이름 회귀) + L2(improve-tool list) | TS-007, TS-025 |
| H-5 | F-009 dashboard 파서 | 현행 `parse_memory_index`는 이미 오프바이원으로 깨져 있다(실측: `date="제목"`, `category="등록일"` — 헤더 행까지 데이터로 반환) (R-T1). "회귀 없음"을 기준선으로 잡으면 **깨진 동작을 보존**하게 된다 | P1 | L1(신규 정답 기대값) + L2(실 API 응답) | TS-027, TS-028 |
| H-6 | F-009 응답 스키마 | `MemoryRowResponse` 필드명을 바꾸면 `MemoryPage.tsx`가 `row.category`/`row.description`을 참조(`MemoryPage.tsx:50-53,129-139,263-269,305-319`)하므로 FE가 즉시 백지가 된다. FE는 TASK.md 범위 밖이다 | P1 | L1(응답 모델 필드 동일성) + L3(화면 육안) | TS-027 |
| H-7 | F-005 채번 원자성 | `task-number --bump`가 read-modify-write를 락 없이 하면 동시 실행 인스턴스 2개가 같은 번호를 받아 태스크 폴더가 충돌한다 (R-T2) | P1 | L2(N-프로세스 동시 bump) | TS-019, TS-020 |
| H-8 | F-002 원자적 쓰기 | 검증 실패·예외 시 파일이 부분 기록되면 SSOT가 파손된다. 기존 md 경로는 `write_text` 1회로 사실상 원자적이었으나 JSON은 검증 단계가 늘어 실패 지점이 많아진다 | P1 | L1(실패 주입 후 원본 불변) | TS-004, TS-009 |
| H-9 | F-002 테스트 이관 | 88건 중 24건 폐기/재작성 + 약 30건 어서션 치환(R-T5). "동작 재사용 가능"을 "테스트 무변경"으로 오해하면 회귀망이 비어 있는 채로 GREEN 선언된다 | P1 | L1(테스트 건수·커버 목록 대조) | TS-006, TS-008 |
| H-10 | F-011 `tools.md` 동시 편집 | 077이 `tools.md:202-289`(code-scan 절)를 EXECUTE 중이라 줄번호 오프셋이 어긋난다 (R-T6). 의미 충돌은 없다(본 태스크=542-639) | P2 | L1(편집 직전 재-Read 후 앵커 매칭) | TS-032 |
| H-11 | F-011 grep AC | R-10 AC(a) "전 경로 grep 0건"은 **문자 그대로는 달성 불가** — 변환기·`.bak`·마이그레이션 문서가 `MEMORY.md`를 정당하게 언급해야 한다. 또한 일반 명사 용법(`skills/html-mockup`, `system-architecture-html`)과 역사적 스냅샷(`docs/backup/`, `docs/proposals/`)이 섞여 있다 (R-T7, R-T8) | P2 | L1(제외 경로 명시 grep 명령) | TS-032 |
| H-12 | F-004 `.bak` 보존 | 이미 `.bak`이 있는 프로젝트에서 재변환 시 원본 백업을 덮어써 무손실 제약을 깬다 | P2 | L1(`.bak` 존재 시 타임스탬프 suffix) | TS-013 |
| H-13 | F-001 스키마 배포 | 검증기가 `schema/memory.schema.json`을 런타임 로드하는데, 배포본에 스키마가 누락되면 전 서브명령이 죽는다 | P1 | L1(스키마 부재 시 결정론 에러) + L2(install 후 배포본 실행) | TS-004, TS-037 |

---

## 2. 기능별 분석

### F-001: 문서 스키마 재설계 + 런타임 검증기

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/schema/memory.schema.json` | 행 스키마(문서용) → 문서 스키마(런타임) | 수정(전면 재작성) |
| BE | `opal/tools/memory-tool/memory_tool.py` | enum 상수 하드코딩 → 스키마 로드 | 수정 |

#### 2.1.2 현재 구현
- 스키마는 **인덱스 행 1개 + `_history_row_schema` 1개**만 정의하며 `version`/`last_task_number`/배열 컨테이너가 없다. 런타임에서 로드되지 않는다(`memory_tool.py` 전체에 `schema` 문자열 0건).
- enum이 코드와 어긋나 있다 — 스키마 `type` enum에 `improvement` 없음, `status` enum에 `candidate` 없음 vs `memory_tool.py:46-47` `VALID_TYPES`/`VALID_STATUSES`는 포함.
- 검증은 커맨드별 인라인 파이썬 코드(`memory_tool.py:507-519`, `626-635`)로 흩어져 있다.

#### 2.1.3 영향 범위
- 상위: 8개 `cmd_*` 전부가 enum·길이 검증에 의존.
- 하위: 없음(스키마는 리프).
- **[MUST] `ANALYSIS.md` §2.1**: `jsonschema` 등 외부 패키지 도입 금지 — 표준 라이브러리만으로 `enum`/`maxLength`/`pattern` 대조를 자체 구현해야 한다.

---

### F-002: memory-tool JSON I/O 전환

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` | 9서브명령 CLI, 마커·표 파싱 전담 | 수정(약 250줄 삭제, 로더 계층 신설) |
| BE | `opal/tools/memory-tool/tests/test_memory_tool.py` | 88테스트 23클래스 | 수정(24 폐기·재작성 / ~30 어서션 치환) |
| BE | `opal/tools/memory-tool/tests/fixtures/*.md` | md 픽스처 4종 | 삭제 + json 픽스처 신규 |
| BE | `opal/tools/memory-tool/README.md` | 서브명령 계약 문서 | 수정 |

#### 2.2.2 현재 구현
`replace_marker_section`(`memory_tool.py:145-155`) → `_parse_index_rows`/`_parse_history_rows`(`208-243`) → `_render_index_table`/`_render_history_table`(`246-270`) 호출 그래프가 8개 커맨드 전부에서 재사용된다. 각 `cmd_*`가 `pathlib.Path(args.file)` + `read_text()`를 직접 호출한다(`425,481,588,661,763,1078,1112,1176`). `build_review_block`(`328-414`)은 경로를 받아 파일을 스스로 다시 읽는다.

행 자료구조는 이미 `dict`이므로 **커맨드 본문의 리스트 조작 로직은 그대로 재사용 가능**하고, 교체 대상은 I/O 양끝(파싱·렌더)뿐이다.

#### 2.2.3 영향 범위
- 상위: improve-tool 서브프로세스 위임(`improve_tool.py:135-141`) — `show` 응답 키 `index_rows` 의존(`improve_tool.py:311`).
- 하위: `build_review_block`이 경로 대신 문서 dict를 받도록 시그니처 변경 필요(중복 로드 제거).
- 테스트: `test_memory_tool.py` 전량.

---

### F-003: `show --brief` 필터

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` `cmd_show` | 전량 반환 | 수정 |
| 문서 | `opal/tools/memory-tool/README.md`, `opal/core/references/tools.md` | 옵션 문서화 | 수정 |

#### 2.3.2 현재 구현
`cmd_show`(`memory_tool.py:1076-1098`)는 이미 `index_rows`/`history_rows` 구조화 JSON을 반환한다. **빠진 것은 필터뿐**이며 `dead`/`superseded`/`promoted`/`candidate`까지 전량 반환한다(TASK.md §배경 분석 (3)).

#### 2.3.3 영향 범위
- 상위: PM 브리핑(F-006), `core/AGENT.md` Lazy 트리거.
- **비영향 확인**: improve-tool `cmd_list`/`cmd_show`는 `--brief` 없이 호출하므로(`improve_tool.py:305,345`) `candidate` 행이 계속 보인다 — brief 필터가 improve 루프를 가리지 않는다.

---

### F-004: lazy 자동 마이그레이션

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` | `cmd_migrate`(구md→신md) 795-912 + legacy 파서 915-1069 | 삭제 후 `_migrate_md_to_json` 신규 |
| BE | `opal/tools/memory-tool/tests/fixtures/fixture_legacy.md` | 구포맷 픽스처 | 유지(변환 입력 픽스처로 용도 전환) + 변형 픽스처 5종 추가 |

#### 2.4.2 현재 구현 (실측)
3개 프로젝트 실물 대조 — ANALYSIS §A-1 재확인:

| 항목 | ai-framework | invest-stock | aos |
|------|:---:|:---:|:---:|
| 마커 | O(`.opal/MEMORY.md:28,34,37,45`) | **X** | O(`MEMORY.md:7,10,13,17`) |
| 섹션 헤딩 | `## 메모리` / `## 작업 히스토리` | `## 메모리 인덱스` / `## 작업 히스토리` | `## 메모리` / `## 작업 히스토리` |
| 인덱스 | 6컬럼 3행 | 5컬럼 3행(구포맷) | 6컬럼 0행 |
| 히스토리 헤더 | `제목\|등록일\|단계\|경로\|핵심결과` 5행 | `#\|작업\|단계\|경로\|시작일시\|완료일시` **3행** | 5컬럼 1행 |
| 상태값 | enum 정합 | `확정`/`승인대기` (LEGACY_STATUS_MAP 부재) | 해당 없음 |
| `last_task_number` | O(78) | **X** | O(1) |
| 구 잔존 텍스트 | O(`MEMORY.md:7-18` 죽은 카테고리 안내표) | 없음(전체가 구포맷) | 없음 |
| 백틱 file 필드 | 혼재(L31 백틱 / L33 비백틱) | 비백틱 | 해당 없음 |

**치명 결함(H-1)**: 현 `_parse_legacy_history`(`memory_tool.py:960-963`)는 헤더에 `등록일자`/`등록일시`와 `작업`과 `시작일시\|완료일시`가 **모두** 있어야 표를 인식한다. invest-stock 헤더는 첫 컬럼이 `#`이므로 `등록일자`/`등록일시` 문자열이 없어 **인식 실패 → 3행이 조용히 0행**이 된다.

#### 2.4.3 영향 범위
- 모든 서브명령(공통 로더 경유, D-2).
- improve-tool 과도기 시나리오(ANALYSIS §A-6 3행).
- 3개 실 프로젝트 파일.

---

### F-005: `task-number` 서브명령

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/memory-tool/memory_tool.py` | 신규 10번째 서브명령 | 수정 |
| 문서 | `opal/core/references/harness/task-process.md:19-22` | 채번 절차(직접 Read+Edit) | 수정 |
| 스킬 | `opal/skills/op-task/SKILL.md:174` | 채번 참조 | 수정 |
| 스킬 | `opal/skills/opal-pilot-gc/SKILL.md:79` | 채번 참조 | 수정 |

#### 2.5.2 현재 구현
`last_task_number`를 다루는 코드가 memory-tool에 **0건**이다. `task-process.md:19-22`는 오케스트레이터(LLM)가 `.opal/MEMORY.md` 헤더 주석을 직접 Read+Edit하도록 지시한다 — 마커 가드 보호 범위 밖의 **유일한 비게이트 쓰기 경로**(ANALYSIS §4 발견 2).

#### 2.5.3 영향 범위
- 채번 참조 3곳 + `.opal/MEMORY.md` 헤더 필드 → JSON 최상위 필드로 이관.
- 동시 실행 인스턴스 간 번호 중복 방지 책임이 LLM → 도구로 이동(H-7).

---

### F-006: PM 브리핑 경로 전환

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/opal-pm.md` §15(L284 부근), §17(L336 부근) | 브리핑 절차·프로젝트 컨텍스트 | 수정 |
| 문서 | `opal/core/AGENT.md:60` | Lazy 트리거 테이블 행 | 수정 |
| 문서 | `GEMINI.md:67`, `opal/bootstrapper/gemini-hardening.md:71`, `opal/skills/opal-project-init/templates/common/platform/GEMINI.md:67` | 동일 Lazy 행 3중 사본 | 수정 |

#### 2.6.2 현재 구현
`opal-pm.md §15 절차` 1~4단계가 "`{프로젝트}/.opal/MEMORY.md`를 Read로 읽는다"로 시작한다. 브리핑 형식은 `- [{type}] {description} ({date})`이며, **타입별 우선순위가 `feedback > project > user > reference`** 로 적혀 있다 — `user`/`reference`는 `VALID_TYPES`(`memory_tool.py:46`)에 존재하지 않는 **기존 drift**다.

#### 2.6.3 영향 범위
- PM 부트스트랩 전 세션. Gemini 3중 사본을 동시에 갱신해야 플랫폼 간 행위가 갈리지 않는다.
- **[MUST] `.opal/AGENT.md` §금지사항**: "하드코딩된 플랫폼 분기 추가 금지" → 3중 사본은 **새 분기를 만들지 말고 기존 사본을 동일 문구로 갱신**한다.

---

### F-007: `memory-learning.md` 슬림화

#### 2.7.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/harness/memory-learning.md` | 형식·라이프사이클 SSOT | 수정 |

#### 2.7.2 현재 구현
105줄. `## 마커 규약`(L40-49) 10줄 + 인덱스 표 형식 서술(L17-23) 7줄 + 히스토리 표 형식 서술(L24-29) 6줄이 삭제·이관 대상. 라이프사이클 표 4행(L55-60), `delete` 무손실 가드(L62), 이관 워크플로우(L68-96)는 **존치**.

#### 2.7.3 영향 범위
- Lazy 로드 대상(`core/AGENT.md` 마지막 행) — 메모리 쓰기 요청마다 로드되므로 슬림화가 곧 반복 토큰 절감이다(TASK.md §배경 분석 (2) "규범 문서 슬림화 ✅ JSON 귀속").

---

### F-008: improve-tool 위임 경로 전환

#### 2.8.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `opal/tools/improve-tool/improve_tool.py:213,291,337` | `.opal/MEMORY.md` 존재 판정 3곳 | 수정 |
| BE | `opal/tools/improve-tool/tests/test_improve_tool.py:117-122,162-163` | `_VALID_MEMORY_MD` 픽스처·`_memory_md_text()` 헬퍼 | 수정 |
| 문서 | `opal/core/references/harness/pm-improvement-loop.md:85`, `opal/skills/opal-improve/SKILL.md:99` | no-op 사유 문자열 서술 | 수정 |

#### 2.8.2 현재 구현
```
memory_md = proj_root_path / ".opal" / "MEMORY.md"
if not memory_md.exists():
    ok(scope="local", skipped=True, reason="no MEMORY.md")     # improve_tool.py:216-218
```
동일 패턴이 `_record_local`(213) / `cmd_list`(291) / `cmd_show`(337) 3곳에 있고, 위임 인자는 `--file str(memory_md)`이다.

#### 2.8.3 영향 범위
- 존재 판정이 md에 묶여 있어 전환 후 상시 no-op이 된다(TASK.md R-7 "왜").
- **과도기**: md만 있고 json이 아직 없는 프로젝트 — 판정을 `.json`으로 바꾸면 lazy 마이그레이션이 발동하기도 전에 no-op이 된다(ANALYSIS §A-6 3행). 판정 로직 자체가 md 폴백을 알아야 한다.

---

### F-009: dashboard 소비자 전환

#### 2.9.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/parsers/memory_parser.py` | md 표 파싱(구포맷 5컬럼 가정) | 수정(전면 교체) |
| BE | `dashboard/backend/routers/memory.py:40-78` | `GET /api/memory` | 수정 |
| BE | `dashboard/backend/routers/doctor.py:63` | 핵심 파일 존재 체크 | 수정 |
| BE | `dashboard/backend/models.py` | `MemoryRowResponse`/`HistoryRowResponse` | 수정(additive) |
| BE | `dashboard/backend/tests/test_parsers.py:24-87` | 파서 회귀 4건 | 수정 |
| FE | `dashboard/frontend/src/pages/memory/MemoryPage.tsx` | 소비처 | **무변경(범위 밖)** |

#### 2.9.2 현재 구현 — 실측 (H-5 근거)
현행 파서를 실 파일에 돌린 결과(`~/.opal/.venv/bin/python`으로 `parse_memory_index(.opal/MEMORY.md)` 직접 실행):

```json
{"rows": [
  {"date":"제목","category":"등록일","status":"유형","file":"상태","description":"파일"},
  {"date":"Console 브레인 구독 인증","category":"2026-06-22","status":"project","file":"active",
   "description":"`memory/console-brain-subscription-auth.md`"}, ...]}
```

즉 ① **헤더 행이 데이터 행으로 반환**되고(`memory_parser.py:119`의 스킵 조건 `cells[0] in ("등록일시","date","카테고리","---")`가 신포맷 첫 셀 `제목`을 못 걸러냄) ② **전 필드가 한 칸씩 밀려** `file`에 `active`가, `description`에 파일 경로가 들어가며 ③ `summary`(요약) 컬럼은 아예 버려진다. 히스토리도 동일하게 밀려 `start`에 핵심결과가 들어간다.

> **결론**: R-8은 "회귀 방지"가 아니라 **"이미 깨져 있던 파서를 처음 제대로 맞추는 수정"** 이다. 기준선을 현행 출력으로 잡으면 안 된다(H-5).

FE 소비 실측 — `MemoryPage.tsx:50-53`이 `MemoryRow { date, category, status, file, description }`를, `156-207`이 `HistoryRow { date, task, stage, path, start, end }`를 그대로 쓴다. `row.category`는 배지(`129-131,263-264`)·필터(`305-319,363-401`)에, `row.description`은 본문(`139,269`)에, `row.file`은 상세 조회 키(`227-231`)에 쓰인다.

#### 2.9.3 영향 범위
- 읽기 전용(mtime 불변) 원칙(`memory_parser.py:6` @header)은 `json.load`만 써도 유지된다.
- `routers/memory.py`는 `?file=` 상세 조회에서 `memory_file_parser`를 별도로 쓰며 이 경로는 개별 `memory/*.md` 대상이라 **무변경**(TASK.md 확정 방향 §2 "개별 본문 파일은 유지").

---

### F-010: `opal-project-init` 템플릿 전환

#### 2.10.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-project-init/SKILL.md:394` | 산출물 목록 3행 | 수정 |
| 스킬 | `opal/skills/opal-project-init/SKILL.md:427-448` | MEMORY.md 인라인 md 템플릿 | 삭제 → `memory-tool init` |
| 스킬 | `opal/skills/opal-project-init/SKILL.md:574-586` | 4-2 히스토리 기록 스니펫 | 수정 |
| 스킬 | `opal/skills/opal-project-init/SKILL.md:681-682` | 최신화 모드 직접 Read | 수정 |
| 스킬 | `opal/skills/opal-project-init/SKILL.md:950-956` | 최신화 4-2 히스토리 기록 | 수정 |

#### 2.10.2 현재 구현
- L427-448이 마커 4개 포함 md 블록을 인라인 리터럴로 들고 있다(`memory-tool init` 미사용).
- L579-586의 히스토리 스니펫은 **구 6컬럼**(`# \| 작업 \| 단계 \| 경로 \| 시작일시 \| 완료일시`)으로, 현행 5컬럼 히스토리 스키마와도 어긋난 **기존 drift**다.
- L681-682가 `.opal/MEMORY.md`를 직접 Read한다.

#### 2.10.3 영향 범위
- 신규 프로젝트가 구포맷으로 태어나면 전환이 무의미해진다(TASK.md R-9 "왜").
- 077 PLAN.md에서 이 파일 언급 0건(ANALYSIS §A-5) → **충돌 없음**.

---

### F-011: 구형 참조 전수 정리 + stale 정정

#### 2.11.1 관련 파일 맵 (grep 전수 실측 — `tasks/`·`.opal/brain/` 제외 39파일 중 변경 대상)
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/harness/observability.md:23-29` | **pre-045 stale** — "`단계` 컬럼 직접 갱신" + "FIFO 10" | 수정(D-5) |
| 스킬 | `opal/skills/opal-pilot-project-dev/SKILL.md:716-721` | 동일 계열 stale | 수정(D-5) |
| 스킬 | `opal/skills/opal-pilot-project-loop/SKILL.md:578-586` | 동일 계열 stale | 수정(D-5) |
| 문서 | `opal/tools/brain-tool/templates/schema-template.md:58` | "FIFO 10항목" 오기재 + MEMORY.md | 수정 |
| 문서 | `opal/core/references/tools.md:542-639` | memory-tool 절(서브명령·에러코드) | 수정 |
| 문서 | `opal/core/references/pm/context-injection.md:25` | 이전 태스크 결과 참조 | 수정 |
| 문서 | `opal/core/references/harness/pm-improvement-loop.md:85` | local scope 위임 서술 | 수정 |
| 스킬 | `opal/skills/opal-improve/SKILL.md:99` | no-op 사유 문자열 | 수정 |
| 스킬 | `opal/skills/opal-pilot-project-dev/references/{prd,roadmap,trd,wbs}-guide.md` (각 1줄: 127/206/190/331) | 체크리스트 "MEMORY.md 작업 히스토리를 갱신했는가" | 수정(문구 일반화) |
| 스킬 | `skills/html-mockup/SKILL.md:37,47` | 세션 컨텍스트 폴백 파일명 | 수정 |
| 스킬 | `skills/system-architecture-html/SKILL.md:69,81` | 동일 | 수정 |
| 문서 | `docs/PROJECT.md:170` | 문서 레지스트리 행 | 수정 |
| 문서 | `docs/ARCHITECTURE.md:61,94,247` | Phase B 브리핑·Project Layer·dashboard 파서 서술 | 수정 |
| — | `docs/backup/ARCHITECTURE_202605081743.md`, `docs/proposals/opal-brain-design.md` | 역사적 스냅샷 | **무변경(제외 확정, P-7)** |
| — | `.opal/brain/pages/**`(14파일), `tasks/**` | 과거 지식·이력 | **무변경(TASK.md AC 명시 제외)** |

#### 2.11.2 현재 구현
`observability.md:23-29`, `opal-pilot-project-dev/SKILL.md:716-721`, `opal-pilot-project-loop/SKILL.md:578-586` 3곳이 모두 "단계 컬럼을 직접 갱신"을 지시하고, `observability.md`는 "FIFO 규칙: 10개를 초과하면" 이라고 쓴다. 현행 SSOT는 `HISTORY_FIFO_LIMIT = 5`(`memory_tool.py:32`)이고 memory-learning.md L34가 "최대 5개 FIFO [MUST]"다.

> **분류(D-5)**: 이 3곳은 memory-tool 도입(045) 이전 관행이 남은 것으로 **"전환으로 생긴 문제"가 아니라 "전환 김에 바로잡는 기존 결함"** 이다.

#### 2.11.3 영향 범위
- 문서가 구형을 가리키면 에이전트가 구 관행(직접 표 편집)으로 회귀한다.
- `tools.md`는 077과 동일 파일(H-10) — 줄 구간 분리(077=202-289 / 본 태스크=542-639).

---

### F-012: 배포 + 실증

#### 2.12.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `./scripts/install-mac.sh` 실행 | `opal/` → `~/.opal/` 재배포 | 실행(파일 무변경) |
| 배치 | `/Volumes/.../ai-framework/.opal/MEMORY.md`, `invest-stock`, `aos` | lazy 변환 실증 대상 | 런타임 변환 |

#### 2.12.2 현재 구현
`install-mac.sh:1091-1147`이 `opal/tools/` 전체를 `~/.opal/tools/`로 복사하고 `memory-tool/run.sh`에 실행 권한을 부여한다 → `schema/` 하위 json도 함께 배포된다(H-13 완화). `clean_dirs`에 `tools`가 포함(`install-mac.sh:1015`)되어 구 파일 잔존은 없다.

#### 2.12.3 영향 범위
- **[MUST] `.opal/AGENT.md` §금지사항**: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다." → 모든 Step의 편집 대상은 `opal/`·`dashboard/`·`docs/`·`skills/`이고, 배포는 이 Step 하나로 격리한다.
- **[MUST] `TASK.md` §제약 조건 2-Layer**: install이 프로젝트 파일(`{프로젝트}/.opal/`)을 수정하지 않는다 → 3개 프로젝트 변환은 **도구 lazy 경로로만** 발생한다.

---

## 3. 기능별 설계

### F-001: 문서 스키마 재설계 + 런타임 검증기

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/memory-tool/schema/memory.schema.json` | BE | 행 스키마 → **문서 스키마**(`version`/`last_task_number`/`memories[]`/`history[]`), enum을 코드와 합치 | (→ D-5) ANALYSIS §4 발견 3 |
| 2 | `opal/tools/memory-tool/memory_tool.py` | BE | `VALID_TYPES`/`VALID_STATUSES`/길이 상수를 **스키마에서 파생**, 표준 라이브러리 검증기 신설 | `memory_tool.py:46-47`, (→ D-24 §2.1) |

#### 3.1.2 데이터 모델 — `.opal/MEMORY.json` 문서 스키마

**P-1 결정: 스키마 파일이 SSOT이고, 코드가 런타임에 로드해 enum·제약을 파생한다** (단일 출처 동기화 방식).

```python
# memory_tool.py
SCHEMA_PATH = pathlib.Path(__file__).resolve().parent / "schema" / "memory.schema.json"
SCHEMA = _load_schema()                       # 실패 시 err(..., "schema_load_failed") — 크래시 금지
_MEM = SCHEMA["$defs"]["memoryRow"]["properties"]
VALID_TYPES    = set(_MEM["type"]["enum"])     # 하드코딩 제거 — 스키마 파생
VALID_STATUSES = set(_MEM["status"]["enum"])
SUMMARY_MAX_LENGTH = _MEM["summary"]["maxLength"]
HISTORY_FIFO_LIMIT = SCHEMA["x-constants"]["HISTORY_FIFO_LIMIT"]
PROMOTE_AGE_DAYS   = SCHEMA["x-constants"]["PROMOTE_AGE_DAYS"]
CURRENT_VERSION    = SCHEMA["properties"]["version"]["const"]
```

문서 스키마 본문:

```jsonc
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "opal://memory-tool/memory.schema.json",
  "title": "OPAL Memory Document",
  "type": "object",
  "required": ["version", "last_task_number", "memories", "history"],
  "additionalProperties": false,
  "properties": {
    "version":          { "type": "integer", "const": 1 },
    "last_task_number": { "type": "integer", "minimum": 0 },
    "memories":         { "type": "array", "items": { "$ref": "#/$defs/memoryRow" } },
    "history":          { "type": "array", "items": { "$ref": "#/$defs/historyRow" } }
  },
  "$defs": {
    "memoryRow": {
      "type": "object", "additionalProperties": false,
      "required": ["title","date","type","status","file","summary"],
      "properties": {
        "title":   { "type": "string", "minLength": 1 },
        "date":    { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" },
        "type":    { "type": "string", "enum": ["project","architecture","feedback","preferences","issues","task","improvement"] },
        "status":  { "type": "string", "enum": ["active","promoted","superseded","dead","candidate"] },
        "file":    { "type": "string", "pattern": "^memory/[^/].*\\.md$" },
        "summary": { "type": "string", "maxLength": 80 }
      }
    },
    "historyRow": {
      "type": "object", "additionalProperties": false,
      "required": ["title","date","stage","path","result"],
      "properties": {
        "title":  { "type": "string", "minLength": 1 },
        "date":   { "type": "string", "pattern": "^\\d{4}-\\d{2}-\\d{2}$" },
        "stage":  { "type": "string" },
        "path":   { "type": "string" },
        "result": { "type": "string" }
      }
    }
  },
  "x-constants":  { "HISTORY_FIFO_LIMIT": 5, "SUMMARY_MAX_LENGTH": 80, "PROMOTE_AGE_DAYS": 30 },
  "x-advisory":   { "TITLE_MAX_LENGTH": 30, "RESULT_MAX_LINES": 2 }
}
```

**의도적 비강제 항목과 근거** (강제하면 실 데이터가 즉시 거부되므로 `review.violations` 권고로 내린다):

| 항목 | 강제 안 하는 이유 | 실측 근거 |
|------|-----------------|----------|
| `memoryRow.title` maxLength 30 | 현행 코드가 한 번도 강제한 적 없어 초과 행이 실재할 수 있다. 히스토리 제목은 30자를 상시 초과 | `.opal/MEMORY.md:41` 히스토리 제목 31자 |
| `historyRow.result` maxLength | "≤2줄"은 문자 수 규범이 아니고, 현행 result가 150자 내외 | `.opal/MEMORY.md:43` |
| `history` maxItems 5 | FIFO는 **쓰기 시** 집행하는 것이지 읽기 거부 사유가 아니다. 6행 문서를 읽지 못하면 `prune`으로 고칠 수도 없다 | `memory_tool.py:277-281`, `cmd_prune` 계약 |

> `x-advisory` 위반은 `build_review_block`의 `violations[]`로 표면화한다 — 기존 `summary_too_long` 위반 표면화 패턴(`memory_tool.py:376-377`)을 그대로 답습한다.

#### 3.1.3 검증기 설계 — 표준 라이브러리 전용

> **[MUST] `memory_tool.py` @header**: "표준 라이브러리만." → `jsonschema` 도입 금지 (→ D-24 §2.1).

```python
def validate_document(doc, schema=SCHEMA) -> list[dict]:
    """스키마 위반 목록 반환(빈 리스트=통과). 부작용 없음.
    지원 키워드(이 스키마가 실제로 쓰는 부분집합만):
      type / required / properties / additionalProperties:false /
      items / $ref(#/$defs/<name> 한정) / enum / const /
      minLength / maxLength / pattern / minimum
    반환 항목: {"path": "memories[2].summary", "keyword": "maxLength",
                "expected": 80, "actual": 85}
    """
```

- `pattern`은 `re.match`로 대조한다(표준 `re`는 JSON Schema의 ECMA-262 정규식 부분집합을 이 스키마 범위에서 동일하게 처리한다 — 사용 패턴이 `^...$` 앵커 + 문자 클래스뿐).
- **미지원 키워드가 스키마에 나타나면 조용히 무시하지 않고** `schema_unsupported_keyword`로 실패한다 — 스키마를 넓혔는데 검증이 따라오지 않는 무성 통과를 차단한다(H-3 계열 재발 방지).

**2계층 검증**:

| 계층 | 시점 | 대상 | 실패 코드 |
|------|------|------|----------|
| L-A 인자 검증 | 각 `cmd_*` 진입 직후 | CLI 인자 1개 | `invalid_type` / `invalid_status` / `summary_too_long` / `invalid_date` / `title_required` (기존 코드 유지 + `invalid_date` 신설) |
| L-B 문서 검증 | ① 로드 직후 ② **쓰기 직전(변형 후)** | 문서 전체 | `schema_validation_failed` (+ `violations[]`) |

R-1 AC("잘못된 `type`/`status` enum, `summary` 81자, `date` 형식 오류 → 각각 대응 에러 코드로 거부 + 파일 무변경")는 L-A가 정밀 코드로 충족하고, L-B가 어떤 경로로도 손상 문서가 기록되지 않음을 보증한다. **L-A의 enum·상한이 L-B와 같은 스키마에서 파생**되므로 두 계층이 어긋날 수 없다(H-3 해소).

#### 3.1.4 환경 변경
해당 없음 — 외부 패키지 추가 없음.

#### 3.1.5 배치/마이그레이션
해당 없음(F-004에서 처리).

#### 3.1.6 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC | 기능 | `append --type bogus` → `{"ok":false,"error":"invalid_type"}` + `MEMORY.json` mtime·내용 불변 |
| TS-002 | R-1 AC | 기능 | `append --summary <81자>` → `summary_too_long` + 파일 불변 |
| TS-003 | R-1 AC | 기능 | 잘못된 date를 가진 문서 로드 → `schema_validation_failed`, `violations[0].keyword=="pattern"` |
| TS-004 | R-1 AC / H-8 | 기능 | 손상 JSON(`{`만 있는 파일) → `invalid_json`, traceback 0건, exit 1, 파일 불변 |
| TS-005 | R-1 AC / H-3 | 회귀 | `VALID_TYPES == set(스키마 enum)` 및 `improvement`/`candidate` 포함 단정 |
| TS-037 | H-13 | 회귀 | `schema/memory.schema.json` 이동·삭제 시 전 서브명령이 `schema_load_failed` 단일라인 JSON 반환(크래시 없음) |

---

### F-002: memory-tool JSON I/O 전환

#### 3.2.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/memory-tool/tests/fixtures/fixture_doc_populated.json` | BE | 6행 인덱스(상태 다양) + 5행 히스토리 정상 문서 | §1.4 기존 픽스처 대체 |
| 2 | `opal/tools/memory-tool/tests/fixtures/fixture_doc_invalid.json` | BE | 스키마 위반 문서(enum·pattern·초과) | TS-003 |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` | BE | 마커·표 계층 삭제(`145-270`, `915-1069`), 공통 로더/락/원자적 쓰기 신설, 8서브명령 전환 | `memory_tool.py:145-270` |
| 2 | `tests/test_memory_tool.py` | BE | 24건 폐기·재작성, 약 30건 어서션 치환, 신규 케이스 추가 | (→ D-4) §1.4 분류표 |
| 3 | `tests/fixtures/{fixture_valid,fixture_populated,fixture_no_marker}.md` | BE | 삭제(마커 개념 소멸) | R-2 AC(a) |
| 4 | `README.md` | BE | 서브명령 계약·에러코드 갱신 | R-2 |

#### 3.2.2 API 설계 — I/O 계층

**삭제 심볼** (R-2 AC(a) "marker·표 파싱 관련 심볼 0건"):
`INDEX_MARKER_START/END`, `HISTORY_MARKER_START/END`, `INDEX_HEADER/SEPARATOR`, `HISTORY_HEADER/SEPARATOR`, `replace_marker_section`, `has_index_markers`, `has_history_markers`, `has_any_markers`, `_extract_section`, `_parse_table_rows`, `_parse_index_rows`, `_parse_history_rows`, `_render_index_table`, `_render_history_table`, `LEGACY_STATUS_MAP`(→ F-004 변환기 내부로 이동), `TEMPLATE_CONTENT`.

**신설 심볼**:

```python
def load_document(json_path: pathlib.Path, command: str, *, allow_migration: bool = True) -> dict:
    """단일 진입 로더 [D-2]. 반환: (doc, migration_report|None)
    1) json 존재      → read → invalid_json / unsupported_version / schema_validation_failed 검사 후 반환
    2) json 부재 + md 존재 → 락 획득 → 이중 확인 → _migrate_md_to_json (F-004)
    3) 둘 다 부재     → err(command, "memory_json_not_found", path=...)
    """

def atomic_write_json(json_path: pathlib.Path, doc: dict) -> None:
    """tmp(같은 디렉토리, 고유 suffix) → fsync → os.replace(원자적 교체).
    쓰기 실패 시 tmp 정리 후 예외 전파 — 원본 불변 [H-8]."""

@contextlib.contextmanager
def memory_lock(json_path: pathlib.Path, command: str):
    """os.open(<path>.lock, O_CREAT|O_EXCL) 배타 클레임.
    - 획득 실패 시 0.1s 간격 최대 50회(5s) 재시도
    - 락 파일 mtime이 60s 초과면 stale로 간주하고 제거 후 재클레임
    - 5s 초과 → err(command, "lock_timeout")
    - finally에서 반드시 unlink [H-2, H-7]"""

def build_review_block(doc: dict) -> dict:
    """시그니처 변경: 경로 → 문서 dict. 파일 재-Read 제거.
    violations에 x-advisory 위반(title>30자) 추가. marker_missing 항목 삭제."""
```

**모든 변경 명령의 공통 골격** (`init`/`append`/`update`/`promote`/`prune`/`delete`/`task-number --bump|--set`):

```python
with memory_lock(json_path, command):
    doc, migration = load_document(json_path, command)
    ...  # 기존 dict 리스트 조작 로직 재사용(변경 없음)
    violations = validate_document(doc)
    if violations:
        err(command, "schema_validation_failed", violations=violations)   # 쓰기 미수행
    atomic_write_json(json_path, doc)
review = build_review_block(doc)
ok(command, ..., review=review, **({"migration": migration} if migration else {}))
```

**읽기 명령**(`show`/`review`)은 **락을 잡지 않는다** — `os.replace`가 원자적이라 부분 파일을 볼 수 없다. 단 마이그레이션이 필요한 경우에만 `load_document` 내부에서 락을 획득한다(double-checked locking). 이로써 브리핑 hot path에 락 경합이 없다.

**응답 계약 보존** (H-4): `show`의 최상위 키 `index_rows` / `history_rows` / `active_count` / `total_count` / `history_count`는 **그대로 유지**한다 — `improve_tool.py:311`이 `data.get("index_rows")`에 의존한다. 내부 SSOT 필드명은 `memories`/`history`이지만 CLI 응답 키는 하위호환을 유지한다(의도적 비대칭, 여기 명시).

#### 3.2.3 ERROR_CODES 개정

| 코드 | 처리 | 근거 |
|------|------|------|
| `marker_missing` | **삭제** | R-2 AC(c) |
| `import_failed` | **삭제**(`cmd_migrate` 소멸) | R-5 AC(d) |
| `memory_md_not_found` | **개명** → `memory_json_not_found` ("MEMORY.json이 존재하지 않음 — init을 먼저 실행하세요: {path}") | R-2 |
| `already_initialized` | 유지, 메시지 변경("MEMORY.json이 이미 존재합니다 — --force로 재초기화") | `cmd_init` |
| `invalid_json` | **신설** — `json.JSONDecodeError` 포착 | H-8 |
| `unsupported_version` | **신설** — `version > 1` | 전방 호환 |
| `schema_validation_failed` | **신설** — `violations[]` 동반 | R-1 AC |
| `schema_load_failed` | **신설** — 스키마 파일 부재·파손 | H-13 |
| `schema_unsupported_keyword` | **신설** | §3.1.3 |
| `invalid_date` | **신설** — `--date`/변환 입력 형식 오류 | R-1 AC |
| `lock_timeout` | **신설** | H-2, H-7 |
| `migration_failed` | **신설** — F-004 §3.4.3 | D-3 |
| `task_number_regression` | **신설** — F-005 | H-7 |
| 그 외(`row_not_found`/`memory_file_not_found`/`invalid_kind`/`invalid_type`/`invalid_status`/`summary_too_long`/`title_required`/`invalid_promote_target`/`promote_ref_missing`/`date_tool_failed`/`delete_requires_dead_or_superseded`) | **불변** | 무손실 가드 유지 |

> **[MUST] `TASK.md` §제약 조건**: "`delete`의 `dead`/`superseded` 전용 가드는 그대로 유지한다." → `cmd_delete`의 상태 검사(`memory_tool.py:1142-1143`)와 `delete_requires_dead_or_superseded` 코드는 손대지 않는다.

#### 3.2.4 환경 변경 / 배치
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-2 AC(a) | 산출물 검사 | `grep -nE "marker\|MARKER\|_render_.*_table\|_parse_(index\|history)_rows" memory_tool.py` → 0건 |
| TS-007 | R-2 AC(b) | 기능 | 8서브명령이 `MEMORY.json`만으로 정상 동작 + `show` 응답 키 `index_rows`/`history_rows` 보존 |
| TS-008 | R-2 AC(c) | 산출물 검사 | `ERROR_CODES`에 `marker_missing`·`import_failed` 부재, 신설 코드 12종 존재 |
| TS-009 | H-8 | 기능 | 검증 실패 주입 시 `.json` mtime·내용 불변, `.tmp` 잔여 파일 0건 |
| TS-038 | H-9 | 회귀 | `unittest` 전량 통과 + 신규/이관 테스트 건수가 88건 이상 |

---

### F-003: `show --brief` 필터

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` `cmd_show` + argparse | BE | `--brief` / `--history N` 옵션 추가 | `memory_tool.py:1076-1098,1250-1253` |
| 2 | `README.md`, `opal/core/references/tools.md` | 문서 | 옵션·출력 예시 문서화 | R-3 |

#### 3.3.2 API 설계 — P-5 `show --brief` 계약 확정

```bash
run.sh show --file <MEMORY.json 경로> [--brief] [--history N]
```

| 항목 | 확정값 | 근거 |
|------|--------|------|
| 메모리 필터 | `status == "active"` **정확 일치**. `promoted`/`superseded`/`dead`/`candidate` 전부 제외 | memory-learning.md L57-60 — `active`만이 "인덱스에 노출·로드 대상". R-3 AC의 3종을 포함하고 `candidate`까지 자연히 배제 |
| 메모리 필드 | `title`, `date`, `type`, `file`, `summary` (5필드) — `status` 생략(brief에서 항상 `active`로 불변) | 브리핑 자립성: `file`이 있어야 PM이 본문을 온디맨드로 열 수 있다 |
| 히스토리 건수 | 기본 **3건**(최신순). `--history N`으로 재정의, `--history 0`이면 히스토리 생략 | TASK.md §배경 분석 (1) "필터 조회(active만 + 히스토리 3) = 1,889 B / −46%" |
| 히스토리 필드 | `title`, `date`, `stage`, `path`, `result` (전 필드 유지) | 최대 3건이라 절감 효과가 미미하고, `result`가 브리핑의 실질 정보 |
| 정렬 | 메모리·히스토리 모두 **`date` 내림차순**(동일 날짜는 문서 내 기존 순서 유지 — 안정 정렬) | `opal-pm.md` §15 규칙 "날짜순: 최신 메모리를 우선 표시" |
| 최상위 키 | `index_rows` / `history_rows` / `active_count` / `total_count` / `history_count` + `brief: true` + `history_truncated: bool` | H-4 하위호환 |
| 비-brief 추가 | `--brief` 미지정 시 `version`·`last_task_number`를 추가로 반환 | 진단·복구 편의 |

**브리핑 재현 가능성 검증** — `opal-pm.md §15 브리핑 형식`은 `- [{type}] {description} ({date})` 이며 규칙은 "타입별 우선순위, 날짜순, 3~5개". `--brief` 출력의 `type`/`summary`/`date`만으로 이 3요소가 모두 재현된다. `title`은 `summary`보다 짧은 스캔 키로 함께 제공되어 브리핑 품질이 오히려 올라간다.

> **동반 정정(F-006에서 반영)**: `opal-pm.md §15`의 우선순위 `feedback > project > user > reference`에서 `user`/`reference`는 `VALID_TYPES`에 없는 **기존 drift**다(`memory_tool.py:46`). 실 enum 기준으로 `feedback > preferences > project > architecture > issues > task`로 정정한다(`improvement`/`candidate`는 brief에서 배제되므로 미기재).

#### 3.3.3 환경 변경 / 배치
해당 없음.

#### 3.3.4 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-3 AC | 기능 | `dead`/`superseded`/`promoted`/`candidate` 각 1건 포함 픽스처 → `--brief` `index_rows`에 해당 status 0건 |
| TS-011 | R-3 AC | 기능 | `len(brief_stdout) < len(full_stdout)` (동일 픽스처) |
| TS-012 | R-3 | 기능 | 히스토리 5행 픽스처 → 기본 3건 + `history_truncated=true`; `--history 0` → 0건 |
| TS-039 | R-3 / F-006 | 회귀 | `--brief` 출력만으로 `opal-pm.md §15` 브리핑 3~5줄을 생성 가능(타입·날짜·요약 필드 존재 단정) |

---

### F-004: lazy 자동 마이그레이션 + `.bak` + 구 `migrate` 삭제

#### 3.4.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `tests/fixtures/fixture_md_no_marker_legacy.md` | BE | invest-stock 재현(마커 부재·5컬럼·자유 상태·`#` 히스토리 헤더) | §2.4.2 실측 |
| 2 | `tests/fixtures/fixture_md_marker_empty.md` | BE | aos 재현(마커 O·0행) | §2.4.2 |
| 3 | `tests/fixtures/fixture_md_marker_populated.md` | BE | ai-framework 재현(마커 O·백틱 혼재·구 잔존 표) | §2.4.2 |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` | BE | `cmd_migrate`(795-912)·`_parse_legacy_index`(915)·`_parse_legacy_history`(947)·`_strip_legacy_tables`(1006) 삭제, `_migrate_md_to_json` 신설, `migrate` 서브파서 제거 | R-5 AC(d) |
| 2 | `tests/fixtures/fixture_legacy.md` | BE | 유지하되 용도 전환(변환 입력 픽스처) | §1.4 "데이터 구성이 재사용 가치" |

#### 3.4.2 P-2 마이그레이션 변형 처리 확정표

**영역 분할 캐스케이드** — 변환기는 md를 인덱스 영역/히스토리 영역으로 먼저 분할한 뒤 그 영역 안에서만 표를 읽는다. 이로써 ai-framework `MEMORY.md:7-18`의 죽은 카테고리 안내표가 영역 밖으로 배제된다.

1. 마커 쌍이 있으면 마커 사이
2. 없으면 `## `로 시작하고 "메모리"를 포함하는 헤딩 ~ 다음 `## ` 직전 / "히스토리"를 포함하는 헤딩 ~ 다음 `## ` 직전
3. 둘 다 없으면 **전체 파일**을 대상으로 헤더 시그니처 매칭

| # | 변형 | 실측 출처 | 처리 | 결과 |
|---|------|----------|------|------|
| V-1 | **마커 완전 부재** | invest-stock | 캐스케이드 2단계(헤딩 기반)로 영역 확정. 마커 유무를 실패 사유로 삼지 않는다 | 정상 변환 |
| V-2 | **히스토리 헤더 변형**(`#\|작업\|단계\|경로\|시작일시\|완료일시` — "등록일자/등록일시" 문자열 없음) | invest-stock | 헤더 감지를 **문자열 AND 조건에서 컬럼 매핑 프로파일로 교체**. 프로파일 3종(신5컬럼 / 구6컬럼-# / 구6컬럼-등록일자)을 순서대로 시도하고, 어느 것도 안 맞으면 **컬럼 개수 기반 위치 폴백**을 쓰되 `[REVIEW]` 플래그 + `unrecognized_header` 경고 기록 | 3행 보존 |
| V-3 | **자유텍스트 상태값**(`확정`/`승인대기`) | invest-stock | `LEGACY_STATUS_MAP` 미포함 키 → `active`로 폴백하되 ① summary에 `[REVIEW]` 접두 ② 변환 리포트 `unmapped_statuses: [{"row":"...","raw":"확정"}]`에 전량 기록 | 값 보존 + 추적 가능 |
| V-4 | **`last_task_number` 부재** | invest-stock | ① md 헤더 `> last_task_number: N` → ② 없으면 `{프로젝트}/tasks/` 스캔 후 `^(\d{3})-` 최대값 → ③ 없으면 `0`. 리포트에 `last_task_number_source: "header"\|"tasks_scan"\|"default"` 명시 | 채번 충돌 방지 |
| V-5 | **빈 인덱스/히스토리** | aos | 영역은 있으나 데이터 행 0 → **정상 0행**. `empty_source_regions: ["memories"]`로 기록해 D-3 판정과 구분 | 성공(0행) |
| V-6 | **구 잔존 텍스트**(죽은 카테고리 안내표) | ai-framework `MEMORY.md:7-18` | 영역 분할로 파싱 대상에서 배제. 원문은 `.opal/MEMORY.md.bak`에 그대로 남으므로 **별도 보존 조치 불필요**. 신규 문서에 이 설명을 옮기지 않는다(README·memory-learning.md가 이미 SSOT) | 무손실(백업 경유) |
| V-7 | **백틱 감싼 file 경로** | ai-framework `MEMORY.md:31` | `.strip().strip("`").strip()`로 정규화 후 `^memory/.+\.md$` 검증. 기존 `_resolve_memory_file`(`memory_tool.py:304`)의 정규화 규칙을 재사용 | 정규 경로 |
| V-8 | **datetime 형식 날짜**(`2026-06-20 12:34`) | invest-stock | `[:10]` 절단 후 `pattern` 검증 | `YYYY-MM-DD` |
| V-9 | **`file` 필드 부재/공란** | 가능성 | `_title_to_filename(title)`(`memory_tool.py:288-294`)로 합성 + `[REVIEW]` 플래그 | 스키마 통과 |

#### 3.4.3 D-3 무성 유실 금지 판정 [MUST]

> **[MUST] PM 결정 D-3**: 변환기가 표를 인식하지 못하면 "0행 변환 성공"이 아니라 **명시적 실패**로 처리한다. "원본에 표가 없어서 0행"과 "인식 실패로 0행"을 반드시 구분한다.

**행 회계(row accounting) 불변식**:

```
영역별로:
  candidate_lines = 영역 내에서 '|'로 시작·종료하는 줄 - 구분선 줄 - 헤더로 판정된 줄
  parsed_rows     = 변환기가 실제로 산출한 행 수
  [MUST] parsed_rows == candidate_lines
```

| 상황 | `candidate_lines` | `parsed_rows` | 판정 |
|------|:---:|:---:|------|
| 정상 변환 | 3 | 3 | `ok` |
| **aos 빈 표**(V-5) | 0 | 0 | `ok` + `empty_source_regions` 기록 |
| **invest-stock 히스토리**(현행 버그) | 3 | 0 | **`migration_failed`** (`reason: "row_detection_failed"`) |
| 부분 유실 | 5 | 4 | **`migration_failed`** (`reason: "row_count_mismatch"`, `expected:5, parsed:4`) |
| 스키마 위반 | 3 | 3 | **`migration_failed`** (`reason: "schema_validation_failed"`, `violations[]`) |

`migration_failed`는 **`MEMORY.json`을 만들지 않고 `MEMORY.md`도 건드리지 않는다**(원본 무변경, R-5 AC(c)). 호출한 원 명령도 수행되지 않는다.

#### 3.4.4 변환 절차 (`_migrate_md_to_json`)

```
[락 보유 상태에서 실행]
1. md 텍스트 read
2. 영역 분할(캐스케이드)
3. 행 파싱 + candidate_lines 회계  ── 불일치 → migration_failed(원본 무변경)
4. 정규화 (V-3 상태 / V-7 백틱 / V-8 날짜 / V-9 file 합성 / [REVIEW] 플래그)
5. last_task_number 해석 (V-4)
6. history FIFO=5 절단 (절단분은 리포트 dropped_history 에 제목만 기록)
7. doc 조립 + validate_document ── 위반 → migration_failed(원본 무변경)
8. atomic_write_json(MEMORY.json)           ← json 먼저
9. os.replace(MEMORY.md → MEMORY.md.bak)    ← 그 다음 백업
   · .bak 이미 존재 → MEMORY.md.bak.<YYYYMMDDHHmmss> 사용 [H-12]
   · 9 실패는 비치명 → 리포트 backup_failed:true (json이 이미 SSOT이므로 다음 로드는 1단계에서 종료)
10. migration 리포트 반환 → 원 명령 응답에 "migration" 키로 첨부
```

**리포트 스키마**:
```json
{"performed": true, "source": ".../MEMORY.md", "backup": ".../MEMORY.md.bak",
 "memories": 3, "history": 3, "review_flagged": 3,
 "unmapped_statuses": [{"title":"...","raw":"확정"}],
 "last_task_number": 3, "last_task_number_source": "tasks_scan",
 "empty_source_regions": [], "dropped_history": [], "backup_failed": false}
```

#### 3.4.5 P-4 경쟁조건 가드 확정

> **단일 기전** — `memory_lock`(§3.2.2) 하나로 마이그레이션·일반 변경·채번 증가를 모두 덮는다. 별도 기전을 만들지 않는다.

- 로더는 **double-checked locking**을 쓴다: 락 밖에서 json 존재를 확인 → 없으면 락 획득 → **락 안에서 다시 확인** → 그래도 없을 때만 변환.
- 시나리오 H-2(improve-tool 연속 `record`): B가 락 대기 중 A가 변환+append 완료 → B가 락 획득 후 재확인 시 json이 이미 존재 → 변환 스킵, A의 행이 보존된 문서에 이어 append. **클로버 없음**.
- 락 파일: `<MEMORY.json 경로>.lock`, `O_CREAT|O_EXCL`. `finally` 해제. mtime 60s 초과 시 stale로 간주하고 제거 후 재클레임(프로세스 강제 종료 복구).
- 쓰기는 항상 `tmp → os.replace` — 락을 못 가진 독자도 부분 파일을 보지 않는다.

#### 3.4.6 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-013 | R-5 AC(a) / H-12 | 기능 | md만 있는 임시 프로젝트에서 `show` → `MEMORY.json` 생성 + `MEMORY.md.bak` 존재 + `show` 결과 정상. `.bak` 선점 시 `.bak.<ts>` 생성 |
| TS-014 | R-5 AC(b) | 통합 | ai-framework 픽스처: 변환 전후 메모리 3행·히스토리 5행 수 일치 + 각 필드 값 100% 일치(백틱 제거·날짜 절단만 허용 차이) |
| TS-015 | R-5 AC(c) / **H-1** | 기능 | invest-stock 픽스처(히스토리 3행, 헤더 변형) → V-2 프로파일로 3행 변환 성공. **프로파일을 강제로 무력화하면** `migration_failed(row_detection_failed)` + md 불변 + json 미생성 |
| TS-016 | R-5 / V-5 | 기능 | aos 픽스처(빈 인덱스) → `ok`, `memories: []`, `empty_source_regions:["memories"]` — 실패 아님 |
| TS-017 | R-5 AC(d) | 산출물 검사 | `grep -n "cmd_migrate\|_parse_legacy_\|_strip_legacy_tables" memory_tool.py` → 0건, `migrate` 서브명령 부재 |
| TS-018 | **H-2** | 통합(동시성) | md만 있는 디렉토리에 `append` 2프로세스 동시 기동 → json 1개, 두 행 모두 존재, `.bak` 1개, 락 파일 잔여 0 |
| TS-040 | V-3/V-4 | 기능 | invest-stock 변환 리포트에 `unmapped_statuses` 3건, `last_task_number_source` 명시 |

---

### F-005: `task-number` 서브명령 + 채번 절차 tool-gated 개정

> **PM 결정 D-1 반영** — A-2 옵션 (b) 채택. `last_task_number`를 memory-tool 서브명령으로 tool-gated 처리한다. JSON 파일을 LLM이 손으로 편집하는 것은 md 헤더 편집보다 파손 위험이 크며, 이 태스크의 목적(도구 정확성)과 정면으로 어긋나므로 존치할 수 없다.

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `memory_tool.py` | BE | `cmd_task_number` 신설 + argparse 서브파서 추가 | D-1 |
| 2 | `opal/core/references/harness/task-process.md:19-22` | 문서 | 채번 4단계를 도구 호출 절차로 개정 | `task-process.md:19-22` |
| 3 | `opal/skills/op-task/SKILL.md:174` | 스킬 | 채번 참조 문구 교체 | `op-task/SKILL.md:174` |
| 4 | `opal/skills/opal-pilot-gc/SKILL.md:79` | 스킬 | 채번 참조 문구 교체 | `opal-pilot-gc/SKILL.md:79` |
| 5 | `opal/core/references/tools.md` | 문서 | 10번째 서브명령 문서화 | R-3/D-1 |

#### 3.5.2 API 설계 — 서브명령 계약

```bash
run.sh task-number --file <MEMORY.json 경로> [--bump] [--set N]
```

| 모드 | 동작 | 응답 | 락 |
|------|------|------|:---:|
| (없음) 읽기 | 현재값 반환, 파일 무변경 | `{"ok":true,"command":"task-number","last_task_number":78}` | 미획득 |
| `--bump` | **원자적 증가** — 락 안에서 read-modify-write | `{"ok":true,"command":"task-number","last_task_number":79,"previous":78,"bumped":true,"review":{...}}` | 획득 |
| `--set N` | 복구·보정용. `N < 현재값`이면 `task_number_regression`으로 거부(무손실) | `{"ok":true,...,"last_task_number":N,"previous":78,"set":true,"review":{...}}` | 획득 |
| `--bump` + `--set` 동시 | `invalid_args` | — | — |

- 반환값 `last_task_number`가 **이번 태스크에 쓸 번호**다(bump 후 값). 호출자는 계산하지 않는다.
- `--bump`/`--set`은 변경 명령이므로 memory-learning.md §자가검토 트리거 규칙에 따라 `review` 블록을 첨부한다.
- `MEMORY.json`도 `MEMORY.md`도 없는 프로젝트: `memory_json_not_found` → 절차 문서에 "`init` 선행" 을 명시한다.

**원자성 보장 방식(H-7)**: `memory_lock` + `atomic_write_json`. N개 프로세스가 동시에 `--bump`해도 락 직렬화로 1..N이 중복 없이 배분된다. LLM의 read-then-write 왕복(현행 `task-process.md:19-22`)에서 발생하던 TOCTOU 창이 소멸한다.

#### 3.5.3 채번 절차 개정문 (3곳 공통 SSOT)

`task-process.md` 신 본문:

```markdown
#### 태스크 번호 채번 규칙

신규 태스크 생성 시:
1. 아래를 호출한다 — 도구가 원자적으로 증가·저장한다. **LLM 직접 편집 금지.**
   ```bash
   ~/.opal/tools/memory-tool/run.sh task-number --file .opal/MEMORY.json --bump
   ```
2. 응답 JSON의 `last_task_number` 값이 이번 태스크 번호다 (계산하지 않는다).
3. 태스크 폴더를 생성한다 (`tasks/{NNN}-{YYMMDD}-{스킬약어}-{태스크명}/`)
4. TASK.md를 작성한다

> `.opal/MEMORY.json`이 없고 `.opal/MEMORY.md`만 있으면 도구가 자동 변환 후 처리한다.
> 둘 다 없으면 `memory_json_not_found` — `memory-tool init`을 먼저 실행한다.
```

`op-task/SKILL.md:174` / `opal-pilot-gc/SKILL.md:79`는 위 절차를 **재서술하지 않고 포인터로 참조**한다: "`{NNN}`: `memory-tool task-number --bump` 응답의 `last_task_number` (절차: `harness/task-process.md` §태스크 번호 채번 규칙)".

#### 3.5.4 환경 변경 / 배치
해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-019 | D-1 | 기능 | `task-number`(읽기) 파일 mtime 불변 / `--bump` 후 값 +1, 파일 반영 |
| TS-020 | **H-7** | 통합(동시성) | 20개 프로세스 동시 `--bump` → 반환값 20개가 서로 중복 없음, 최종 `last_task_number == 초기+20` |
| TS-021 | D-1 | 기능 | `--set` 역행 시 `task_number_regression` + 파일 불변 / `--bump --set` 동시 → `invalid_args` |
| TS-041 | D-1 | 산출물 검사 | `task-process.md`·`op-task/SKILL.md`·`opal-pilot-gc/SKILL.md`에서 "직접 Read+Edit"류 채번 서술 0건, `task-number --bump` 지시 3곳 존재 |

---

### F-006: PM 브리핑 경로 전환

#### 3.6.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-pm.md` §15 | 문서 | 절차 1~3단계를 `show --brief` 호출로 교체 + 타입 우선순위 drift 정정 | `opal-pm.md` §15 |
| 2 | `opal/core/references/opal-pm.md` §17 | 문서 | 프로젝트 컨텍스트 목록 `.opal/MEMORY.md` → `.opal/MEMORY.json`(도구 조회) | `opal-pm.md` §17 |
| 3 | `opal/core/AGENT.md:60` | 문서 | Lazy 트리거 로드 대상 교체 | `AGENT.md:60` |
| 4 | `GEMINI.md:67` | 문서 | 동일 행(사본 1) | `GEMINI.md:67` |
| 5 | `opal/bootstrapper/gemini-hardening.md:71` | 문서 | 동일 행(사본 2) | `gemini-hardening.md:71` |
| 6 | `opal/skills/opal-project-init/templates/common/platform/GEMINI.md:67` | 스킬 | 동일 행(사본 3) | 해당 파일:67 |

#### 3.6.2 설계 — 개정문

`opal-pm.md §15 절차`:

```markdown
### 절차

1. `~/.opal/tools/memory-tool/run.sh show --file {프로젝트}/.opal/MEMORY.json --brief` 를 호출한다
2. `memory_json_not_found`이면 브리핑 생략 (인사만 하고 대기)
3. `index_rows`(status=active) + `history_rows`(최근 3건)로 브리핑을 구성한다
4. 첫 응답에 브리핑을 포함한다

> [MUST] `MEMORY.md`/`MEMORY.json`을 Read로 직접 읽지 않는다 — 도구 조회만 사용한다.
> `.opal/MEMORY.md`만 있는 프로젝트는 이 호출이 자동 변환을 수행한다(도구 lazy 경로).
```

`규칙` 절 정정: "**타입별 우선순위**: `feedback` > `preferences` > `project` > `architecture` > `issues` > `task`" (`user`/`reference`는 실 enum에 없는 기존 drift — `memory_tool.py:46` 대조 후 제거).

`core/AGENT.md:60` Lazy 행:

| 트리거 조건 | 로드 대상 | 전제 조건 | 트리거 전 로드 | 위반 시 조치 |
|------------|----------|----------|--------------|------------|
| PM 컨텍스트 로드 시 함께, 또는 소유자 요청 | `memory-tool show --brief` **호출 결과**(파일 Read 아님) | PM 컨텍스트(Eager) 로드 완료 | **금지** | 로드 중단, 트리거 발생 시 재로드 |

> **[MUST] `.opal/AGENT.md` §금지사항**: "하드코딩된 플랫폼 분기 추가 금지 — Claude/Cursor/Gemini 분기는 어댑터 계층에서만 수행한다." → Gemini 3중 사본은 **AGENT.md와 동일한 문구로만** 갱신하고 새 조건 분기를 추가하지 않는다.

#### 3.6.3 환경 변경 / 배치
해당 없음.

#### 3.6.4 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-022 | R-4 AC | 산출물 검사 | `opal-pm.md`·`core/AGENT.md`에서 "MEMORY.md를 Read"류 0건 + `show --brief` 지시 존재 |
| TS-042 | R-4 / 3.2 | 산출물 검사 | Lazy 트리거 행 4개 사본(AGENT.md·GEMINI.md 3종)이 **동일 문구**로 갱신됨 |

---

### F-007: `memory-learning.md` 슬림화

#### 3.7.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/harness/memory-learning.md` | 문서 | `## 마커 규약` 절 삭제, 표 형식 서술을 스키마 참조로 대체 | R-6, `memory-learning.md:17-29,40-49` |

#### 3.7.2 설계 — 삭제/존치 경계

| 구간 | 현행 | 처리 |
|------|------|------|
| L11 저장소 | `.opal/MEMORY.md` (인덱스) | `.opal/MEMORY.json` (인덱스, memory-tool 전용) |
| L14 활용 방법 | "MEMORY.md를 읽고" | "`memory-tool show --brief`로 조회하고" |
| L17-23 인덱스 표 형식 6줄 | 컬럼별 상세 서술 | **삭제** → "필드 정의는 `opal/tools/memory-tool/schema/memory.schema.json`(SSOT)" 1줄 |
| L24-29 히스토리 표 형식 6줄 | 컬럼별 상세 서술 | **삭제** → 위 1줄에 통합 |
| L34 FIFO 5 [MUST] | 유지 | **존치** |
| L35 blind 삭제 금지 [MUST] | 유지 | **존치** |
| L40-49 `## 마커 규약` 10줄 | 마커 4종·`marker_missing` | **절 전체 삭제** → "`[MUST]` 메모리 변경은 memory-tool로만 수행한다 — `MEMORY.json` 직접 편집 금지. 도구는 쓰기 전 스키마 검증에 실패하면 파일을 변경하지 않는다." 2줄 |
| L53-64 라이프사이클 표 4행 + delete 가드 + 갯수 상한 | 유지 | **존치**(R-6 AC) |
| L68-96 이관(졸업) 워크플로우 + 라우팅 표 | 유지 | **존치**(R-6 AC) |
| L96 자가검토 트리거 | `migrate` 포함 목록 | `migrate` 제거, `task-number` 추가 |

예상 감소: 105줄 → 약 82줄(−22%). R-6 AC "총 줄 수가 전환 전 대비 감소" 충족.

#### 3.7.3 환경 변경 / 배치
해당 없음.

#### 3.7.4 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-023 | R-6 AC | 산출물 검사 | "마커"·`<!-- memory:` 문자열 0건 + 라이프사이클 표 4행·라우팅 표 5행 보존 + 줄 수 감소 |

---

### F-008: improve-tool 위임 경로 전환

#### 3.8.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/tools/improve-tool/improve_tool.py:213,291,337` | BE | 존재 판정 + 위임 인자 경로 교체 + 과도기 폴백 | `improve_tool.py:213,291,337` |
| 2 | `opal/tools/improve-tool/tests/test_improve_tool.py:117-122,162-163` | BE | `_VALID_MEMORY_MD` → json 픽스처, `_memory_md_text()` → `_memory_doc()` | (→ D-8) |
| 3 | `opal/core/references/harness/pm-improvement-loop.md:85` | 문서 | 위임 서술 갱신 | 해당 줄 |
| 4 | `opal/skills/opal-improve/SKILL.md:99` | 스킬 | no-op 사유 문자열 갱신 | 해당 줄 |

#### 3.8.2 설계 — 과도기 폴백 (ANALYSIS §A-6 3행 대응)

3곳 공통 헬퍼로 통합한다:

```python
def _resolve_memory_target(proj_root: pathlib.Path) -> tuple[pathlib.Path | None, str]:
    """반환 (memory-tool --file 인자, reason).
    1) .opal/MEMORY.json 존재      → (json_path, "")
    2) .opal/MEMORY.md 존재(미변환) → (json_path, "")   # 도구가 lazy 변환 수행
    3) 둘 다 부재                  → (None, "no MEMORY.json")
    """
```

핵심: **md만 있어도 no-op하지 않고 `--file <json 경로>`로 위임**한다 — memory-tool의 lazy 로더가 md를 보고 변환한 뒤 `append`를 수행하기 때문이다(F-004 §3.4.4). 이것이 R-7 AC와 ANALYSIS §A-6 3행 시나리오를 동시에 충족하는 유일한 형태다.

- no-op 사유 문자열: `"no MEMORY.md"` → **`"no MEMORY.json"`** (`improve_tool.py:218,297,343`).
- `cmd_list`의 `data.get("index_rows")`(`improve_tool.py:311`)는 H-4 계약 보존으로 **무변경**.
- 위임 시 `show`는 `--brief` 없이 호출 유지 — `candidate` 행이 필터링되면 improve 루프가 자기 기록을 못 본다(F-003 §2.3.3).

#### 3.8.3 환경 변경 / 배치
해당 없음.

#### 3.8.4 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-024 | R-7 AC / **H-3** | 통합 | `MEMORY.json`만 있는 프로젝트에서 `record --scope local` → no-op 아님, `type=improvement`/`status=candidate` 행이 json에 기록됨 |
| TS-025 | ANALYSIS §A-6 / H-4 | 통합 | `MEMORY.md`만 있는 프로젝트에서 `record --scope local` → lazy 변환 발동 + append 성공 + `.bak` 존재. 이어서 `list --scope local`이 해당 행 1건 반환 |
| TS-026 | R-7 AC | 기능 | `.opal/` 자체가 없는 프로젝트 → `{"ok":true,"skipped":true,"reason":"no MEMORY.json"}` graceful no-op, 예외 전파 0 |

---

### F-009: dashboard 소비자 전환

#### 3.9.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/parsers/memory_parser.py` | BE | md 표 파싱 → `json.load` 매핑. 함수명 `parse_memory_index(content)` 유지(하위호환) | `memory_parser.py:82-152` |
| 2 | `dashboard/backend/routers/memory.py:40-78` | BE | 대상 파일 `.opal/MEMORY.md` → `.opal/MEMORY.json` | `memory.py:47-48` |
| 3 | `dashboard/backend/models.py` | BE | `MemoryRowResponse`에 `title`(기본 `""`), `HistoryRowResponse`에 `result`(기본 `""`) **additive** 추가 | P-3 |
| 4 | `dashboard/backend/routers/doctor.py:63` | BE | 핵심 파일 체크 `.opal/MEMORY.md` → `.opal/MEMORY.json` | `doctor.py:63` |
| 5 | `dashboard/backend/tests/test_parsers.py:24-87` | BE | 4건 기대값 재작성 | (→ D-10) |

#### 3.9.2 P-3 응답 스키마 결정

**조사 결과(grep 실측)**: `dashboard/frontend/src/pages/memory/MemoryPage.tsx`가 `category`/`description`을 **실제로 참조한다** — 타입 정의 `50-53`, 배지 `129-131`/`263-264`, 본문 `139`/`269`, 필터 상태·계산 `287,305,314-319`, 셀렉트·칩 `363,384,397,401`. 히스토리는 `task`/`stage`/`path`/`date`/`start`/`end`를 `156-207`에서 사용한다.

**결정: 응답 모델을 유지하고 신필드는 additive로만 추가한다** (교체 안 함).

| 근거 | 내용 |
|------|------|
| 계약 | R-8 AC가 "기존과 동일한 응답 스키마"를 요구한다 |
| 범위 | TASK.md §배경 분석 (5) dashboard 행에 FE 파일이 없다 — `MemoryPage.tsx`는 **본 태스크 비범위** |
| 리스크 | 필드명 교체 시 FE가 즉시 백지가 된다(H-6). 비범위 파일을 끌어들이면 077 외 두 번째 동시 편집 지점이 생긴다 |
| 확장성 | `title`·`result`는 optional additive이므로 기존 FE는 무시하고, 후속 FE 태스크가 채택할 수 있다 |

**필드 매핑**:

| JSON(`MEMORY.json`) | → 응답 모델 | 비고 |
|---|---|---|
| `memories[].date` | `date` | 그대로 |
| `memories[].type` | `category` | 의미 동일(045에서 카테고리→유형으로 개명된 같은 축) |
| `memories[].status` | `status` | 그대로 |
| `memories[].file` | `file` | 백틱 없음(스키마가 `^memory/...` 강제) |
| `memories[].summary` | `description` | 의미 동일(설명→요약 개명) |
| `memories[].title` | **`title`(신설, additive)** | FE 미사용 — 후속 채택 |
| `history[].date` | `date` | |
| `history[].title` | `task` | |
| `history[].stage` / `path` | `stage` / `path` | |
| `history[].result` | **`result`(신설, additive)** | |
| — | `start` / `end` | 항상 `None`. JSON 스키마에 대응 필드 없음(구 6컬럼 유물) |

> **[MUST] 기준선 주의(H-5)**: 현행 파서는 이미 오프바이원으로 깨져 있다(§2.9.2 실측 — 헤더 행 반환, `file`에 `active`, `description`에 파일 경로). 따라서 `test_parsers.py`의 기대값은 **현행 출력을 스냅샷하면 안 되고** JSON 원본 값과 대조해야 한다.

**읽기 전용 원칙 유지**: `json.load`만 사용, 쓰기·`memory-tool` CLI 호출 없음 — `memory_parser.py:6` @header "읽기 전용 — open(read)만 사용, mtime 불변(H-6)" 을 그대로 승계한다. dashboard가 CLI를 호출하면 lazy 마이그레이션이 발동해 프로젝트 파일을 변조하게 되므로 **직접 파싱 유지가 의도적 선택**이다.

**파서 graceful 동작**: 파일 부재/`JSONDecodeError`/스키마 불일치 시 `{"rows": [], "history": [], "warning": "..."}` 반환(현행 `parse_memory_index` try/except 계약 유지, `memory_parser.py:120-128`). dashboard가 memory-tool 검증기를 재구현하지 않는다(중복 금지).

**doctor**: 체크 라벨을 `MEMORY.json (메모리 인덱스)`로 바꾸고, `.opal/MEMORY.md`가 아직 남아 있으면 `warn`으로 "미변환 — memory-tool 첫 호출 시 자동 변환" 안내 항목을 **추가**한다(전환 관측성).

#### 3.9.3 환경 변경 / 배치
해당 없음.

#### 3.9.4 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-027 | R-8 AC / **H-5, H-6** | 통합 | `GET /api/memory` 응답의 `rows[]` 필드 집합이 기존 5필드 + `title`이고, 값이 `MEMORY.json` 원본과 1:1 일치(헤더 행 유입 0건, 오프바이원 해소) |
| TS-028 | R-8 AC | 회귀 | 파싱 전후 `MEMORY.json` mtime 불변 |
| TS-029 | R-8 AC | 산출물 검사 | doctor 응답에 `MEMORY.json` 점검 항목 존재, `MEMORY.md` 잔존 시 warn 항목 노출 |
| TS-043 | H-6 | 회귀 | `MemoryRowResponse`/`HistoryRowResponse`의 기존 필드명이 하나도 제거·개명되지 않음 |

---

### F-010: `opal-project-init` 템플릿 전환

#### 3.10.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-project-init/SKILL.md:394` | 스킬 | 산출물 3행 `.opal/MEMORY.md` → `.opal/MEMORY.json` (생성 방법: `memory-tool init`) | `SKILL.md:394` |
| 2 | `opal/skills/opal-project-init/SKILL.md:427-448` | 스킬 | 인라인 md 템플릿 22줄 **삭제** → 도구 호출 3줄 | `SKILL.md:427-448` |
| 3 | `opal/skills/opal-project-init/SKILL.md:574-586` | 스킬 | 구 6컬럼 히스토리 스니펫 삭제 → `append --kind history` | `SKILL.md:579-586` |
| 4 | `opal/skills/opal-project-init/SKILL.md:681-682` | 스킬 | 최신화 모드 직접 Read → `show --brief` | `SKILL.md:681-682` |
| 5 | `opal/skills/opal-project-init/SKILL.md:950-956` | 스킬 | 최신화 4-2 히스토리 기록 → `append --kind history` | `SKILL.md:950-956` |
| 6 | `opal/skills/opal-project-init/SKILL.md:5` | 스킬 | 서두 "`.opal/(AGENT.md, MEMORY.md)`를 직접 작성한다" 문구 수정 | `SKILL.md:5` |

#### 3.10.2 설계 — 개정문

`2-4` 절 대체 (인라인 템플릿 제거):

```markdown
**2-4. 메모리 인덱스 생성** (memory-tool 위임 — 인라인 템플릿 금지)

~/.opal/tools/memory-tool/run.sh init --file .opal/MEMORY.json

- 도구가 `{"version":1,"last_task_number":0,"memories":[],"history":[]}` 골격을 생성한다.
- [MUST] `.opal/MEMORY.json`을 손으로 작성하지 않는다. 형식·라이프사이클: `harness/memory-learning.md`.
```

`4-2` 절 대체:

```markdown
**4-2. 프로젝트 메모리 갱신**

~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.json --kind history \
  --title "opi 프로젝트 초기화" --stage "완료" --path "docs/, .opal/" \
  --summary "docs 4종 + AGENT/MEMORY/setting 생성"

최신화 모드는 `--title "opi 프로젝트 최신화"`로 동일하게 기록한다.
```

> 이로써 `SKILL.md:579-586`의 **구 6컬럼 스니펫(기존 drift)** 도 함께 소멸한다 — 현행 5필드 스키마와의 불일치가 해소된다.

`1-0 변경 맥락 수집` 대체: 1~2단계를 `show --brief` 1회 호출로 통합("작업 히스토리 최근 3건 + active 메모리를 함께 얻는다").

#### 3.10.3 환경 변경 / 배치
해당 없음. 077과 겹치지 않음(ANALYSIS §A-5 — 077 PLAN.md에서 이 파일 언급 0건).

#### 3.10.4 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R-9 AC | 통합 | 임시 디렉토리에서 opi 초기화 시뮬레이션(도구 호출 시퀀스 실행) → `.opal/MEMORY.json` 존재, `.opal/MEMORY.md` 부재 |
| TS-031 | R-9 AC | 산출물 검사 | `SKILL.md`에 `<!-- memory:` 및 md 인라인 표 템플릿 0건, 구 6컬럼 스니펫 0건 |

---

### F-011: 구형 참조 전수 정리 + pre-045 stale 정정

#### 3.11.1 파일 변경 계획

§2.11.1 표의 "수정" 대상 전체. 대표 개정문 3건:

**(a) `observability.md:23-29` (D-5)**
```markdown
### 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.json`이 존재하면, 단계 완료 시 작업 히스토리를 memory-tool로 갱신한다:

~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.json --kind history \
  --title "<태스크명>" --stage "<단계>" --path "tasks/<폴더>/" --summary "<핵심결과>"

- [MUST] 표·파일 직접 편집 금지 — 도구 호출만 사용한다.
- **FIFO 규칙**: 히스토리는 **최대 5개**이며 도구가 추가 시점에 결정론적으로 집행한다(`prune` 불필요).
```
> **분류(D-5)**: 기존 서술의 "`단계` 컬럼 직접 갱신"·"FIFO 10개"는 memory-tool(045) 도입 이전 관행이 남은 것으로, **전환으로 생긴 문제가 아니라 전환 김에 바로잡는 기존 결함**이다(현행 SSOT: `memory_tool.py:32` `HISTORY_FIFO_LIMIT = 5`, `memory-learning.md:34`).

**(b) `opal-pilot-project-dev/SKILL.md:716-721` / `opal-pilot-project-loop/SKILL.md:578-586`** — 동일 계열. "Phase/Loop 전환 시 `단계` 컬럼 → ..." 직접 갱신 서술을 `append --kind history --stage "<Phase N 확정>"` 도구 호출로 교체하고, 위 (a)와 동일한 [MUST] 1줄을 삽입한다.

**(c) `brain-tool/templates/schema-template.md:58`** — "`MEMORY.md` … FIFO 10항목(자동 rotate)" → "`MEMORY.json` … FIFO 5항목(memory-tool 결정론 집행)".

**(d) `skills/html-mockup/SKILL.md:37,47` / `skills/system-architecture-html/SKILL.md:69,81`** — 세션 컨텍스트 폴백 파일명 `MEMORY.md` → `MEMORY.json`. (일반 명사 용법이 아니라 **실재하지 않게 될 파일을 가리키는 stale 포인터**이므로 범위에 포함한다.)

#### 3.11.2 P-7 R-10 범위 경계 확정

**포함**: `opal/**`, `skills/**`, `dashboard/**`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, 루트 `GEMINI.md`.

**제외 + 근거**:

| 제외 대상 | 근거 |
|----------|------|
| `tasks/**` | TASK.md R-10 AC(a)가 명시적으로 제외 |
| `.opal/brain/**` (14파일) | TASK.md R-10 AC(a)가 명시적으로 제외 — 과거 지식 페이지 |
| `docs/backup/**` | **역사적 스냅샷** — 백업본을 고치면 백업의 의미가 소멸(R-T8) |
| `docs/proposals/opal-brain-design.md` | **설계 제안 히스토리** — 작성 시점 사실의 기록물(R-T8) |
| `opal/tools/memory-tool/**`, `opal/tools/improve-tool/**` 내 잔존 | **기능적 참조** — 변환기 원본 경로·`.bak` 명명·마이그레이션 문서는 `MEMORY.md`를 반드시 언급해야 한다. AC를 문자 그대로 적용하면 기능 구현이 불가능하다(H-11) |
| `dashboard/backend/routers/doctor.py` 내 warn 항목 | 미변환 프로젝트 관측 목적의 **의도적 잔존**(§3.9.2) |

**R-10 AC(a) 실행 가능 grep 명령 (재정의)**:

```bash
grep -rn "MEMORY\.md" \
  --exclude-dir=tasks --exclude-dir=.git --exclude-dir=node_modules \
  --exclude-dir=brain --exclude-dir=backup --exclude-dir=proposals \
  --exclude-dir=memory-tool --exclude-dir=improve-tool \
  . | grep -v "MEMORY\.md\.bak"
# 기대: 0건
```

보조 AC — 제외 경로 내 잔존은 **허용 목록 검토**로 대체한다: `memory-tool`/`improve-tool`/`doctor.py`의 각 잔존 라인이 "마이그레이션·백업·관측" 문맥임을 DONE.md에 열거한다(무근거 잔존 차단).

#### 3.11.3 환경 변경 / 배치
- **[D-4] 077 순서**: `tools.md`는 **편집 직전에 최신 내용을 재확인**한다(077 완료 대기 금지). 077은 `tools.md:202-289`(code-scan 절), 본 태스크는 `tools.md:542-639`(memory-tool 절)로 줄 구간이 분리되어 의미 충돌이 없다. 워커는 줄번호가 아니라 **`## memory-tool` 헤딩 앵커**로 편집 위치를 잡는다(H-10).

#### 3.11.4 변경이력 의무

> **[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무**: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다. 일시는 `YYYY-MM-DD HH:mm` (KST), 버전은 semver, 변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`."

→ F-006·F-007·F-010·F-011이 손대는 **모든 스킬·참조 문서**에 `(078)` 태그 변경이력 행을 추가한다. 각 Step의 완료 기준에 포함한다.

#### 3.11.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-032 | R-10 AC(a) / **H-11** | 산출물 검사 | §3.11.2의 grep 명령 결과 0건 |
| TS-033 | D-5 | 산출물 검사 | 3곳 stale 문서에서 "직접 갱신"·"10개" 서술 0건, "FIFO 5"·"도구 호출" 서술 존재 |
| TS-034 | CONVENTIONS §변경이력 | 산출물 검사 | 변경한 스킬·참조 문서 전량에 `(078)` 변경이력 행 존재 |

---

### F-012: 배포 + 3프로젝트 실증

#### 3.12.1 파일 변경 계획
파일 변경 없음(실행 Step). `./scripts/install-mac.sh` 실행으로 `opal/` → `~/.opal/` 재배포.

#### 3.12.2 설계

> **[MUST] `.opal/AGENT.md` §금지사항**: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
> **[MUST] `TASK.md` §제약 조건 2-Layer**: install이 프로젝트 파일(`{프로젝트}/.opal/`)을 수정하지 않는다.

실증 순서(각 프로젝트 독립):
1. **사전 스냅샷** — `cp .opal/MEMORY.md /tmp/<proj>-before.md` + 행 수 계수
2. **lazy 발동** — `~/.opal/tools/memory-tool/run.sh show --file <proj>/.opal/MEMORY.json --brief`
3. **사후 대조** — `MEMORY.json` 행 수·필드값 vs 스냅샷, `.bak` 존재, `migration` 리포트의 `unmapped_statuses`/`last_task_number_source` 확인
4. **실패 시** — `migration_failed`이면 원본 무변경을 확인하고 변환기 보강 후 재시도(무손실 유지)

invest-stock은 V-2/V-3/V-4가 동시에 걸리는 **최난도 케이스**이므로 실증 순서를 ai-framework → aos → invest-stock으로 잡아 난이도 오름차순으로 결함을 조기 노출한다.

#### 3.12.3 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-035 | R-10 AC(b) / **H-1** | 통합 | 3개 프로젝트 전부 변환 성공 + 행 수·필드 무손실 + `.bak` 존재. invest-stock 히스토리 **3행 보존**(0행 아님) |
| TS-036 | R-10 AC(b) | 통합 | 실세션: PM 부트스트랩이 `show --brief`로 브리핑 생성 → `append` → `show --brief` → `update --status dead` → `show --brief` 왕복이 `MEMORY.json`에 반영 |
| TS-044 | H-13 | 통합 | install 후 **배포본** `~/.opal/tools/memory-tool/run.sh`로 전 서브명령 스모크 통과(스키마 동반 배포 확인) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| **P1 계약 고정** | F-001 | 1 | opal-be-agent | 단독 | 스키마가 RED·구현의 공통 계약. 선행 필수 |
| **P1-RED** | F-001~F-005 | 2 | **opal-test-agent** (mode: red) | 단독 | [MUST] `red-first.md` §2 작성자≠구현자 |
| **P2 도구 본체** | F-001·F-002·F-003·F-004·F-005 | 3→4→5→6→7→8→9 | opal-be-agent | **순차(단일 에이전트)** | 전 Step이 `memory_tool.py` 동일 파일 — C-1 §1 파일 충돌 방지 |
| **P3-A 소비자 코드** | F-008, F-009 | 10 ∥ 11 | opal-be-agent | **병렬 2배치** | 서로 다른 패키지(improve-tool / dashboard) |
| **P3-B 규범 문서** | F-006, F-007 | 12 ∥ 13 | opal-task-agent | **병렬 2배치** | 서로 다른 파일 |
| **P3-C 스킬·인벤토리** | F-002·F-003·F-005·F-010 | 14 ∥ 15 ∥ 16 | opal-task-agent | **병렬 3배치** | `tools.md` / 채번 3곳 / opi SKILL — 파일 비중복 |
| **P4 잔존 정리** | F-011 | 17 ∥ 18 | opal-task-agent | **병렬 2배치** | stale 3곳 / 기타 참조. P3 완료 후(정리 대상 최종 문구 확정 필요) |
| **P5 docs·배포** | F-011, F-012 | 19 → 20 | PM 직접 | 순차 | docs/ 갱신 후 install |
| **P6 실증** | F-012 | 21 → 22 | opal-be-agent → PM 직접 | 순차 | 배포본 기준 실증 → 실세션 왕복 |

**[MUST] 의존 불변식**: 도구 본체(F-001~F-005, Step 1~9) 완료 전에는 소비자(F-006·F-008·F-009·F-010, Step 10~16)를 착수할 수 없다 — 소비자는 신 CLI 계약(`show --brief` 출력 형태, `task-number` 시그니처, 에러코드 목록)을 문서·코드에 고정하므로 계약이 흔들리면 전부 재작업된다.

### 4.2 실행 체크리스트

> 총 **22개 Step** | Phase **6개** | 실행 모드: **복잡**

#### Step 1: 문서 스키마 재설계
- [x] 완료
- **소속 기능**: F-001 (R-1)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/schema/memory.schema.json`
- **작업 내용**: §3.1.2 문서 스키마로 전면 재작성 — `version`/`last_task_number`/`memories[]`/`history[]` 컨테이너 + `$defs.memoryRow`/`$defs.historyRow`, enum을 `memory_tool.py:46-47`과 합치(`improvement`/`candidate` 포함), `x-constants`/`x-advisory` 블록 추가. `_history_row_schema`/`_constants` 구 키 제거.
- **완료 기준**: `json.load` 성공 + `$defs` 2종 존재 + `type` enum 7종·`status` enum 5종이 코드 상수와 정확히 일치 + 마커 관련 키(`INDEX_MARKERS`/`HISTORY_MARKERS`) 0건
- **테스트**: TS-005
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: RED 테스트 스위트 작성 + 실패 증거 기록
- [x] 완료
- **소속 기능**: F-001~F-005 (R-1·R-2·R-3·R-5, D-1)
- **영역**: BE
- **agent**: **opal-test-agent** (mode: red)
- **파일**: `opal/tools/memory-tool/tests/test_memory_tool.py`, `tests/fixtures/*.json`, `tests/fixtures/fixture_md_*.md`
- **작업 내용**: §3의 CLI 계약(§3.2.2 응답 키, §3.2.3 에러코드, §3.3.2 brief 계약, §3.4.2 변형표, §3.4.3 행 회계, §3.5.2 task-number)에 대한 실패 테스트를 먼저 작성한다. 픽스처 6종(json 2 + md 변형 3 + legacy 1 전용) 생성. 동시성 테스트(TS-018/TS-020)는 `subprocess` 병렬 기동으로 작성.
- **완료 기준**: `python -m unittest` 실행 시 신규 테스트가 **전량 실패(exit≠0)** 하고, 그 출력이 RED 증거로 STATE/DONE에 첨부됨. **테스트 파일에 구현 코드가 한 줄도 포함되지 않음**
- **테스트**: TS-001~TS-021, TS-037~TS-041 (RED)
- **실행 방법**: sub-agent
- **의존**: Step 1
- **비고**: `red-first.md` §1.5 판정 = **RED-first 강제**(비즈니스 로직 + API 계약 + 마이그레이션). §2 [MUST] "RED 작성 주체는 구현 워커와 분리" → 이 Step만 `opal-test-agent`를 쓴다(PM 후보 목록 예외, 근거 명시)

#### Step 3: 공통 로더 · 락 · 원자적 쓰기 · 검증기 신설
- [x] 완료
- **소속 기능**: F-001·F-002 (R-1·R-2)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/memory_tool.py`
- **작업 내용**: `_load_schema`/`validate_document`(§3.1.3 키워드 부분집합, 미지원 키워드 시 실패)·`load_document`·`atomic_write_json`·`memory_lock`(§3.2.2) 신설. 스키마 파생 상수(`VALID_TYPES`/`VALID_STATUSES`/`SUMMARY_MAX_LENGTH`/`HISTORY_FIFO_LIMIT`/`PROMOTE_AGE_DAYS`/`CURRENT_VERSION`)로 하드코딩 교체. ERROR_CODES에 신설 12종 추가.
- **완료 기준**: TS-004/TS-005/TS-009/TS-037 GREEN. `import jsonschema` 0건, 표준 라이브러리 외 import 0건
- **테스트**: TS-004, TS-005, TS-009, TS-037
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 4: 8서브명령 JSON I/O 전환 + 마커·표 계층 제거
- [x] 완료
- **소속 기능**: F-002 (R-2)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/memory_tool.py`
- **작업 내용**: `init`/`append`/`update`/`promote`/`prune`/`show`/`review`/`delete`를 §3.2.2 공통 골격으로 전환. §3.2.2 삭제 심볼 목록 전량 제거. `build_review_block(doc)` 시그니처 변경 + `marker_missing` violation 제거 + `x-advisory` violation 추가. `memory_md_not_found` → `memory_json_not_found` 개명, `marker_missing`·`import_failed` 삭제. `show` 응답 키 `index_rows`/`history_rows` 보존(H-4). `delete` dead/superseded 가드 무변경.
- **완료 기준**: TS-006(심볼 grep 0건)·TS-007·TS-008 GREEN. `cmd_delete`의 `delete_requires_dead_or_superseded` 경로 무변경 확인
- **테스트**: TS-006, TS-007, TS-008
- **실행 방법**: sub-agent
- **의존**: Step 3

#### Step 5: lazy 마이그레이션 + 변형 처리 + `.bak` + 구 `migrate` 삭제
- [x] 완료
- **소속 기능**: F-004 (R-5)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/memory_tool.py`
- **작업 내용**: `_migrate_md_to_json` 신설 — §3.4.2 변형 V-1~V-9 처리, §3.4.3 **행 회계 불변식**(D-3 무성 유실 금지), §3.4.4 10단계 절차, `.bak` 충돌 시 타임스탬프 suffix(H-12). `load_document`의 double-checked locking 결합(§3.4.5). `cmd_migrate`·`_parse_legacy_index`·`_parse_legacy_history`·`_strip_legacy_tables`·`migrate` 서브파서 삭제.
- **완료 기준**: TS-013~TS-018·TS-040 GREEN. **`migration_failed` 발생 시 `MEMORY.md` mtime 불변 + `MEMORY.json` 미생성** 단정 통과. `grep "cmd_migrate\|_parse_legacy_"` 0건
- **테스트**: TS-013, TS-014, TS-015, TS-016, TS-017, TS-018, TS-040
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: `show --brief` 필터 구현
- [x] 완료
- **소속 기능**: F-003 (R-3)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/memory_tool.py`
- **작업 내용**: §3.3.2 계약대로 `--brief`/`--history N` 추가. brief 시 `status=="active"` 정확 일치 필터 + 메모리 5필드 투영 + 히스토리 기본 3건 + `date` 내림차순 안정 정렬 + `brief`/`history_truncated` 키. 비-brief에 `version`/`last_task_number` 추가.
- **완료 기준**: TS-010~TS-012·TS-039 GREEN. brief 출력 바이트 < full 출력 바이트 실측치 기록
- **테스트**: TS-010, TS-011, TS-012, TS-039
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: `task-number` 서브명령 구현
- [x] 완료
- **소속 기능**: F-005 (D-1)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/memory_tool.py`
- **작업 내용**: §3.5.2 계약대로 `cmd_task_number` + argparse 서브파서 신설. 읽기는 무락, `--bump`/`--set`은 `memory_lock` + `atomic_write_json` + `review` 첨부. `task_number_regression`·`invalid_args` 처리.
- **완료 기준**: TS-019~TS-021 GREEN. **20 프로세스 동시 bump 시 중복 0건**(TS-020) 실측 통과
- **테스트**: TS-019, TS-020, TS-021
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: 테스트 이관 완결 + 픽스처 전환 (GREEN 수렴)
- [x] 완료
- **소속 기능**: F-002~F-005 (R-2 AC(b))
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/tests/test_memory_tool.py`, `tests/fixtures/`
- **작업 내용**: ANALYSIS §1.4 분류 집행 — ① **폐기/재작성 24건**: `TestMarkerGuard`(3)·`TestInit`(3)·`TestInitAlreadyInitialized`(2)·`TestMigrate`(6)·`TestMigrateLossless`(2)·`TestIntegrationTemplate`(4)·`TestBacktickFileFieldDeletion`(4) ② **어서션 치환 약 30건**: `content = md.read_text()` + `assertIn("문자열")` → `json.load()` + 필드 단위 비교(`TestPromoteToDocs`/`TestPromoteLossless`/`TestUpdateStatusTransition`/`TestDelete`/`TestUpdateNewTitle` 등) ③ md 픽스처 3종(`fixture_valid`/`fixture_populated`/`fixture_no_marker`) 삭제, `fixture_legacy.md`는 변환 입력으로 용도 전환.
- **완료 기준**: `python -m unittest discover` **전량 GREEN**, 총 테스트 수 ≥ 88건, `md.read_text()` 기반 어서션 0건. **[MUST] `red-first.md` §3: GREEN 루핑 중 Step 2가 만든 RED 테스트 파일의 단정을 약화·삭제하지 않는다** — 이관 대상은 기존 88건이며 RED 신규분은 불변
- **테스트**: TS-038 + Step 2 RED 전량 GREEN 전환
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 9: memory-tool README + @header 갱신
- [ ] 완료
- **소속 기능**: F-002·F-003·F-004·F-005 (R-2)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/memory-tool/README.md`, `memory_tool.py` @header
- **작업 내용**: README 서브명령 9종(migrate 제거, task-number 추가) + `--brief`/`--history` + 신 에러코드 표 + `MEMORY.json` 스키마 요약 + lazy 마이그레이션 절 신설. @header의 `description`을 "9서브명령 … JSON SSOT · 스키마 런타임 검증 · lazy 마이그레이션 · 파일 락 원자적 쓰기 · 표준 라이브러리만"으로 갱신하고 `exports`에 신설 심볼 반영, 변경이력 라인 `v2.0 2026-07-28 … (078)` 추가.
- **완료 기준**: README에 `marker`·`migrate` 서브명령 서술 0건 + `task-number`·`--brief` 문서화 존재. **[MUST] `docs/CONVENTIONS.md` §@header 규칙** 준수(`exports`·`description` 실제 코드와 일치)
- **테스트**: 산출물 검사
- **실행 방법**: sub-agent
- **의존**: Step 8

#### Step 10: improve-tool 위임 경로 전환
- [ ] 완료
- **소속 기능**: F-008 (R-7)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/improve-tool/improve_tool.py`, `tests/test_improve_tool.py`
- **작업 내용**: §3.8.2 `_resolve_memory_target` 헬퍼로 3곳(`213`/`291`/`337`) 통합 — **md만 있어도 json 경로로 위임**(lazy 변환 유도), 둘 다 없을 때만 no-op. 사유 문자열 `"no MEMORY.md"` → `"no MEMORY.json"`. 테스트 픽스처 `_VALID_MEMORY_MD` → json 문서, `_memory_md_text()` → `_memory_doc()`. @header 변경이력 추가.
- **완료 기준**: TS-024~TS-026 GREEN + `improve_tool.py`에 `MEMORY.md` 문자열이 **md 폴백 탐지 1곳에만** 잔존(허용 목록에 기재)
- **테스트**: TS-024, TS-025, TS-026
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 11: dashboard 파서·라우터·doctor·모델 전환
- [ ] 완료
- **소속 기능**: F-009 (R-8)
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `dashboard/backend/parsers/memory_parser.py`, `routers/memory.py`, `routers/doctor.py`, `models.py`, `tests/test_parsers.py`
- **작업 내용**: §3.9.2 매핑표대로 `json.load` 기반 파서로 교체(함수명 `parse_memory_index` 유지, graceful warning 계약 유지, `json.load`만 사용해 mtime 불변). `routers/memory.py`의 대상 경로 `.opal/MEMORY.md` → `.opal/MEMORY.json`. `models.py`에 `title`/`result` **additive** 추가(기존 필드 개명·삭제 금지). `doctor.py:63` 체크 대상 교체 + `MEMORY.md` 잔존 시 warn 항목 추가. `test_parsers.py` 기대값을 **JSON 원본 대조 기준**으로 재작성(현행 깨진 출력 스냅샷 금지 — H-5). 각 파일 @header 갱신.
- **완료 기준**: TS-027~TS-029·TS-043 GREEN + `dashboard/frontend/` 파일 변경 **0건**(범위 밖)
- **테스트**: TS-027, TS-028, TS-029, TS-043
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 12: PM 브리핑 경로 전환 (opal-pm + AGENT + Gemini 3중 사본)
- [ ] 완료
- **소속 기능**: F-006 (R-4)
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-pm.md`(§15·§17), `opal/core/AGENT.md:60`, `GEMINI.md:67`, `opal/bootstrapper/gemini-hardening.md:71`, `opal/skills/opal-project-init/templates/common/platform/GEMINI.md:67`
- **작업 내용**: §3.6.2 개정문 적용. §15 절차 4단계를 `show --brief` 호출로 교체 + 타입 우선순위 drift 정정(`user`/`reference` 제거). §17 컨텍스트 목록 갱신. Lazy 행 4개 사본을 **동일 문구**로 갱신. 변경이력 행 `(078)` 추가.
- **완료 기준**: TS-022·TS-042 통과 + 4개 사본 문구 diff 동일 + **[MUST] `.opal/AGENT.md` §금지사항 "하드코딩된 플랫폼 분기 추가 금지"** — 새 플랫폼 조건문 0건
- **테스트**: TS-022, TS-042
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 13: `memory-learning.md` 슬림화
- [ ] 완료
- **소속 기능**: F-007 (R-6)
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/memory-learning.md`
- **작업 내용**: §3.7.2 경계표대로 `## 마커 규약` 절 삭제, 표 형식 서술 13줄을 스키마 참조 1줄로 대체, 저장소·활용 방법 문구 갱신, 자가검토 트리거 명령 목록 갱신(`migrate` 제거 / `task-number` 추가). 라이프사이클 표·delete 가드·이관 워크플로우·라우팅 표 **존치**. 변경이력 `(078)` 추가.
- **완료 기준**: TS-023 통과 — "마커"·`<!-- memory:` 0건, 라이프사이클 4행·라우팅 5행 보존, 줄 수 감소(105 → 약 82)
- **테스트**: TS-023
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 14: `tools.md` memory-tool 절 갱신 (077 동시 편집 지점)
- [ ] 완료
- **소속 기능**: F-002·F-003·F-005 (R-3·R-10)
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/tools.md` (memory-tool 절)
- **작업 내용**: **[D-4] 편집 직전 `tools.md` 전문을 재-Read하여 최신 상태를 확인하고, 줄번호가 아니라 `## memory-tool` 헤딩 앵커로 위치를 잡는다**(077이 `tools.md:202-289` code-scan 절을 동시 편집 중, H-10). 용도 1줄·서브명령 블록(migrate 삭제 / task-number 추가 / `show --brief --history` 추가)·출력 형식 예시(`migration` 리포트 포함)·에러 코드 표(신설 12종 반영, `marker_missing`/`import_failed` 제거)·사용 예시 갱신. 변경이력 `(078)` 추가.
- **완료 기준**: memory-tool 절에 `marker`·`migrate` 0건 + `task-number`·`--brief` 문서화 존재 + **code-scan 절(202-289) diff 0줄**
- **테스트**: TS-032 부분
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 15: 채번 절차 3곳 tool-gated 개정
- [ ] 완료
- **소속 기능**: F-005 (D-1)
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/task-process.md:19-22`, `opal/skills/op-task/SKILL.md:174`, `opal/skills/opal-pilot-gc/SKILL.md:79`
- **작업 내용**: §3.5.3 개정문 적용 — `task-process.md`가 절차 SSOT를 보유하고, 나머지 2곳은 **재서술 없이 포인터 참조**. "헤더 필드를 읽는다/즉시 갱신한다" 직접편집 지시 제거. 변경이력 `(078)` 추가.
- **완료 기준**: TS-041 통과 — 3곳에서 직접 Read+Edit 채번 서술 0건, `task-number --bump` 지시 존재, 절차 본문 중복 서술 0건
- **테스트**: TS-041
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 16: `opal-project-init` 템플릿 전환
- [ ] 완료
- **소속 기능**: F-010 (R-9)
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-project-init/SKILL.md` (L5, 394, 427-448, 574-586, 681-682, 950-956)
- **작업 내용**: §3.10.2 개정문 적용 — 인라인 md 템플릿 22줄 삭제 → `memory-tool init` 호출, 산출물 목록 `.opal/MEMORY.json`, 히스토리 기록 2곳을 `append --kind history`로(구 6컬럼 스니펫 동시 소멸), 최신화 변경 맥락 수집을 `show --brief` 1회 호출로 통합. 변경이력 `v4.4 … (078)` 추가.
- **완료 기준**: TS-031 통과 — `<!-- memory:` 0건, md 인라인 표 템플릿 0건, 구 6컬럼 스니펫 0건. 077 미접촉 파일이므로 충돌 없음
- **테스트**: TS-030, TS-031
- **실행 방법**: sub-agent
- **의존**: Step 9

#### Step 17: pre-045 stale 서술 정정 (D-5 3곳 + FIFO 오기재)
- [ ] 완료
- **소속 기능**: F-011 (R-10, D-5)
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/observability.md:23-29`, `opal/skills/opal-pilot-project-dev/SKILL.md:716-721`, `opal/skills/opal-pilot-project-loop/SKILL.md:578-586`, `opal/tools/brain-tool/templates/schema-template.md:58`
- **작업 내용**: §3.11.1 (a)(b)(c) 개정문 적용 — "`단계` 컬럼 직접 갱신" → `append --kind history` 도구 호출, "FIFO 10" → "FIFO 5(도구 결정론 집행)", `[MUST] 직접 편집 금지` 1줄 삽입. **기술 시 "전환으로 생긴 문제"가 아니라 "전환 김에 바로잡는 기존 결함"으로 분류**하여 변경이력에 명시. 변경이력 `(078)` 추가.
- **완료 기준**: TS-033 통과 — 4개 파일에서 "직접 갱신"·"10개"·"10항목" 0건, 도구 호출 서술 존재
- **테스트**: TS-033
- **실행 방법**: sub-agent
- **의존**: Step 12, Step 13 (규범 문구 확정 후)

#### Step 18: 잔여 구형 참조 전수 정리
- [ ] 완료
- **소속 기능**: F-011 (R-10 AC(a))
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/pm/context-injection.md:25`, `opal/core/references/harness/pm-improvement-loop.md:85`, `opal/skills/opal-improve/SKILL.md:99`, `opal/skills/opal-pilot-project-dev/references/{prd,roadmap,trd,wbs}-guide.md`(각 1줄), `skills/html-mockup/SKILL.md:37,47`, `skills/system-architecture-html/SKILL.md:69,81`
- **작업 내용**: `MEMORY.md` → `MEMORY.json`(또는 도구 조회 서술) 치환. 4개 guide의 체크리스트 문구는 "메모리 작업 히스토리를 memory-tool로 갱신했는가"로 일반화. html-mockup·system-architecture-html의 세션 컨텍스트 폴백 파일명 갱신. §3.11.2 **제외 대상(`docs/backup/`·`docs/proposals/`·`tasks/`·`.opal/brain/`)은 손대지 않는다**. 변경이력 `(078)` 추가.
- **완료 기준**: TS-032·TS-034 통과 — §3.11.2 grep 명령 0건, 변경 문서 전량에 `(078)` 변경이력 행 존재
- **테스트**: TS-032, TS-034
- **실행 방법**: sub-agent
- **의존**: Step 12, Step 13

#### Step 19: docs/ 갱신 (PROJECT.md · ARCHITECTURE.md)
- [ ] 완료
- **소속 기능**: F-011 (R-10)
- **영역**: 문서
- **agent**: **PM 직접**
- **파일**: `docs/PROJECT.md:170`, `docs/ARCHITECTURE.md:61,94,247`
- **작업 내용**: 문서 레지스트리 행 `.opal/MEMORY.md` → `.opal/MEMORY.json`(참조 시점: "부트스트랩 시 `memory-tool show --brief`"), Phase B 브리핑 서술·Project Layer 표·dashboard 파서 서술(`ARCHITECTURE.md:247` "마크다운 파서: MEMORY.md…") 갱신. **[MUST] `docs/CONVENTIONS.md` §새 패턴/규칙 도입 → CONVENTIONS 갱신 판단**: 본 태스크는 새 컨벤션을 도입하지 않고 기존 "도구 우선 원칙"·"State 관리"의 적용 대상만 넓히므로 `CONVENTIONS.md`는 무변경으로 판단한다(판단 근거를 DONE.md에 기록).
- **완료 기준**: 두 문서에서 `MEMORY.md` 0건 + 문서 표 5컬럼 스키마 유지
- **테스트**: TS-032 부분
- **실행 방법**: direct
- **의존**: Step 17, Step 18

#### Step 20: install 재배포
- [ ] 완료
- **소속 기능**: F-012
- **영역**: 환경
- **agent**: **PM 직접**
- **파일**: (실행) `./scripts/install-mac.sh`
- **작업 내용**: 프로젝트 소스 변경 완료 후 `~/.opal/`로 재배포한다. **[MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지"** — 이 Step 이전 어떤 Step도 배포본을 수정하지 않았음을 확인한다(`git status` + `~/.opal/` 수동 편집 이력 없음).
- **완료 기준**: `~/.opal/tools/memory-tool/schema/memory.schema.json` 존재 + `run.sh` 실행 권한 + `run.sh show --help`에 `--brief` 노출 + `run.sh task-number --help` 동작
- **테스트**: TS-044
- **실행 방법**: direct
- **의존**: Step 19

#### Step 21: 3프로젝트 lazy 마이그레이션 실증 + R-10 grep AC
- [ ] 완료
- **소속 기능**: F-012 (R-10 AC(a)·R-5 AC(b))
- **영역**: 배치
- **agent**: opal-be-agent
- **파일**: (런타임) `ai-framework/.opal/MEMORY.md`, `invest-stock/.opal/MEMORY.md`, `aos/.opal/MEMORY.md`
- **작업 내용**: §3.12.2 절차를 적용하되, **[캡틴 결정 2026-07-28 (b)안] 실 파일 변환 대상은 `ai-framework` 1개로 한정한다.** `invest-stock`·`aos`는 이 태스크에서 건드리지 않고, 각 프로젝트에 다음 진입 시 lazy 자동 변환에 맡긴다.
  - **[MUST] 최난도 변형 검증은 유지한다** — `invest-stock/.opal/MEMORY.md`(마커 0·자유텍스트 상태값·히스토리 헤더 변형)를 **읽기 전용으로 복사**하여 임시 작업 경로의 픽스처로 삼고 변환을 실증한다. 원본 파일은 **읽기만 하고 절대 수정하지 않는다**(mtime 불변 확인 포함). H-1(P0 무성 유실)은 이 저장소 밖 파일을 변경하지 않고도 반드시 검증되어야 한다.
  - `aos`(빈 인덱스 변형)도 동일하게 복사본으로 검증한다.
  - 대상별 사전 스냅샷·사후 행 수/필드 대조·`.bak` 확인·`migration` 리포트 기록. 이어서 §3.11.2 grep 명령을 실행해 R-10 AC(a) 0건을 확인하고, 허용 목록 잔존 라인을 열거한다.
- **완료 기준**: TS-035 통과 — ① `ai-framework` 실 변환 1/1 성공 + `.bak` 생성 ② `invest-stock`·`aos` **복사본** 변환 2/2 무손실(특히 **invest-stock 히스토리 3행 보존**) ③ **두 원본 파일 mtime 불변** ④ grep 0건. 실패 시 원본 무변경 확인 후 블로커 보고
- **테스트**: TS-032, TS-035, TS-044
- **실행 방법**: sub-agent
- **의존**: Step 20

#### Step 22: 신형 채택 실세션 왕복 검증
- [ ] 완료
- **소속 기능**: F-012 (R-10 AC(b))
- **영역**: 공통
- **agent**: **PM 직접**
- **파일**: (런타임) `ai-framework/.opal/MEMORY.json`
- **작업 내용**: 실제 PM 세션에서 ① 부트스트랩 브리핑이 `show --brief`로 생성되는지 ② `append` → `show --brief` → `update --status dead` → `show --brief` 왕복이 `MEMORY.json`에 반영되는지 ③ `task-number --bump`로 다음 태스크 번호가 채번되는지 확인한다.
- **완료 기준**: TS-036 통과 — 4단계 왕복 결과가 파일에 반영되고, brief 출력에서 `dead` 전이 행이 사라짐. 브리핑 문구가 `opal-pm.md §15` 형식을 만족
- **테스트**: TS-036
- **실행 방법**: direct
- **의존**: Step 21

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | RED 테스트가 스키마 계약(enum·필드명)을 참조 |
| Step 2 → Step 3 | **[MUST] `red-first.md` §1**: RED 실패 증거 없이 GREEN 진입 금지 |
| Step 3 → 4 → 5 → 6 → 7 → 8 → 9 | **전부 `memory_tool.py` 단일 파일 수정** — C-1 §1 파일 충돌 방지로 같은 에이전트에서 순차 |
| Step 9 → Step 10 ∥ 11 ∥ 12 ∥ 13 ∥ 14 ∥ 15 ∥ 16 | 도구 CLI 계약이 §9에서 문서까지 고정된 뒤에야 소비자가 계약을 인용할 수 있다(§4.1 [MUST] 의존 불변식) |
| Step 10 ∥ 11 | 서로 다른 패키지(`improve-tool` / `dashboard`), 공유 파일 0 |
| Step 12 ∥ 13 ∥ 14 ∥ 15 ∥ 16 | 파일 집합 교집합 0 — `opal-pm.md+AGENT+GEMINI×3` / `memory-learning.md` / `tools.md` / `task-process+op-task+opal-pilot-gc` / `opal-project-init` |
| Step 12·13 → Step 17·18 | stale 정정 문구가 §12·§13에서 확정한 신 규범 표현을 따라야 일관성이 생긴다 |
| Step 17 ∥ 18 | 파일 집합 교집합 0 |
| Step 17·18 → Step 19 | docs/는 하위 문서 확정 후 갱신(plan-guide "docs/ 갱신 Step은 코드 변경 Step 완료 후") |
| Step 19 → 20 → 21 → 22 | 소스 확정 → 배포 → 배포본 실증 → 실세션. 역순 불가 |
| Step 14 ↔ 077 | 동일 파일 다른 절. **대기하지 않고**(D-4) 편집 직전 재-Read + 헤딩 앵커 편집으로 오프셋 리스크 흡수 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 문서 스키마가 런타임 검증에 실제로 쓰이고 코드 enum과 단일 출처인가 | TS-001, TS-002, TS-003, TS-004, TS-005, TS-037 | 잘못된 enum/81자 summary/date 형식오류가 각각 대응 코드로 거부 + 파일 불변. `VALID_TYPES`가 스키마 파생. 외부 패키지 0 |
| F-002 | 8서브명령이 JSON만으로 동작하고 마커 계층이 소멸했는가 | TS-006, TS-007, TS-008, TS-009, TS-038 | 마커·표 심볼 grep 0건, `marker_missing` 카탈로그 제거, `show` 응답 키 보존, 전량 GREEN |
| F-003 | `--brief`가 로드 대상만 반환하고 브리핑을 재현 가능한가 | TS-010, TS-011, TS-012, TS-039 | dead/superseded/promoted/candidate 0건, 출력 바이트 감소, 히스토리 기본 3건 |
| F-004 | lazy 변환이 무손실이며 인식 실패를 **명시적 실패**로 처리하는가 (D-3) | TS-013~TS-018, TS-040 | 행 회계 불일치 시 `migration_failed` + 원본 무변경. invest-stock 히스토리 3행 보존. `.bak` 보존·충돌 회피 |
| F-005 | 채번이 tool-gated이고 원자적인가 (D-1) | TS-019, TS-020, TS-021, TS-041 | 20 프로세스 동시 bump 중복 0. 문서 3곳 직접편집 지시 0건 |
| F-006 | 브리핑이 Read가 아니라 도구 조회로 전환되었는가 | TS-022, TS-042 | "MEMORY.md를 Read" 0건 + `show --brief` 지시 + Gemini 3중 사본 동일 문구 |
| F-007 | 규범 문서가 슬림해지고 보존 대상이 남았는가 | TS-023 | "마커"/`<!-- memory:` 0건, 라이프사이클 4행·라우팅 표 보존, 줄 수 감소 |
| F-008 | improve-tool이 과도기 포함 정상 위임하는가 | TS-024, TS-025, TS-026 | json/md/부재 3케이스 각각 위임·lazy위임·graceful no-op |
| F-009 | dashboard 응답이 FE를 깨지 않고 값이 정확한가 | TS-027, TS-028, TS-029, TS-043 | 기존 필드명 무변경 + 오프바이원 해소 + mtime 불변 + FE 파일 변경 0건 |
| F-010 | 신규 프로젝트가 신포맷으로 태어나는가 | TS-030, TS-031 | 산출물에 `MEMORY.json` 존재·`MEMORY.md` 부재, 인라인 템플릿 0건 |
| F-011 | 구형 잔존이 0이고 stale 결함이 교정되었는가 | TS-032, TS-033, TS-034 | 재정의 grep 0건, FIFO 5·도구 경유 서술, 변경이력 `(078)` 전량 |
| F-012 | 배포본에서 3프로젝트 실증과 실세션 왕복이 성립하는가 | TS-035, TS-036, TS-044 | 3/3 무손실 변환, 왕복 4단계 반영, 배포본 스모크 통과 |

### 5.2 회귀 테스트

- [ ] `python -m unittest discover opal/tools/memory-tool/tests` 전량 통과 (≥88건)
- [ ] `python -m unittest discover opal/tools/improve-tool/tests` 전량 통과 (14건)
- [ ] `pytest dashboard/backend/tests` 전량 통과 (기존 12건 중 memory 4건 재작성 포함)
- [ ] `state-tool`·`backlog-tool`·`brain-tool` 테스트 무영향 확인 (본 태스크 비범위 도구 회귀 0)
- [ ] `dashboard/frontend` 빌드·vitest 무영향 (파일 변경 0건이므로 실행만 확인)
- [ ] improve-tool `cmd_list`의 `index_rows` 키 계약 보존 (H-4)
- [ ] `delete`의 `dead`/`superseded` 전용 가드 동작 불변 (TASK.md 제약)
- [ ] `promote`의 `--ref` 필수 무손실 가드 동작 불변
- [ ] 히스토리 FIFO=5 집행 불변

### 5.3 코드/문서 품질

- [ ] **[MUST] `docs/CONVENTIONS.md` §@header 규칙**: 변경한 `.py` 전량(`memory_tool.py`, `improve_tool.py`, `memory_parser.py`, `memory.py`, `doctor.py`, `models.py`)의 @header `description`/`exports`/`depends`가 실제 코드와 일치
- [ ] **[MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무**: 변경한 스킬·참조 문서 전량에 `vX.Y \| YYYY-MM-DD HH:mm \| … (078)` 행 추가
- [ ] **[MUST] `docs/CONVENTIONS.md` §배포 경계**: `~/.opal/` 직접 편집 0건 — 모든 변경은 `opal/`·`skills/`·`dashboard/`·`docs/` 소스에서 수행 후 Step 20 install로 배포
- [ ] **[MUST] `docs/CONVENTIONS.md` §플랫폼 분기 격리**: Gemini 3중 사본 갱신 시 새 플랫폼 조건문 추가 0건
- [ ] **[MUST] `memory_tool.py` @header "표준 라이브러리만"**: `requirements.txt` 변경 0, 외부 import 0
- [ ] **[MUST] `docs/CONVENTIONS.md` §언어 규칙**: 코드/필드명 English(`memories`/`history`/`last_task_number`), 문서 본문 한국어
- [ ] **[MUST] `docs/CONVENTIONS.md` §네이밍 규칙**: Python 파일 snake_case, 스키마 파일 kebab/소문자 유지(`memory.schema.json`)
- [ ] **[MUST] `harness/citation-rules.md` §0**: PLAN·DONE의 모든 설계 주장에 경로·줄번호 근거 기재
- [ ] TASK.md §배경 분석 (2) 준수 — 토큰 절약을 JSON 포맷 자체의 효과로 서술한 문장 0건
- [ ] TASK.md 비범위(`STATE.md`/`state.json`, `brain/index.md`, `backlog.json`, `code-scan.json`) 파일 변경 0건

### 5.4 보안

- [ ] `_resolve_memory_file`의 `memory/` 경로 탈출 가드(`memory_tool.py:297-316`)가 JSON 전환 후에도 동일하게 동작 — `file` 필드 `pattern`(`^memory/[^/].*\.md$`)과 **이중 방어** 유지
- [ ] `_path_has_traversal` 기반 `promote` title 탈출 거부(`memory_tool.py:688-689`) 불변
- [ ] `delete --with-file` 삭제 경로가 화이트리스트를 벗어나지 않음
- [ ] 락 파일·tmp 파일이 `.opal/` 밖에 생성되지 않고, 실패 경로에서도 잔여물 0
- [ ] `.bak` 파일에 시크릿이 새로 노출되지 않음(원본 md의 사본이므로 권한 동일) + `.gitignore` 정책 확인(`.opal/` 추적 여부에 따라 `.bak` 커밋 여부 판단)
- [ ] 코드에 하드코딩된 토큰/시크릿 0건, 절대경로 하드코딩 0건(`pathlib` + `__file__` 기준 상대 해석)
- [ ] `json.load`가 신뢰 경계 밖 입력을 받지 않음(프로젝트 로컬 파일 전용) + 크기 무제한 로드로 인한 DoS 여지 없음(메모리 인덱스는 수십 행 규모)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 22개 | 복잡 |
| 변경 파일 수 | 약 34개 (도구 8 / dashboard 5 / 참조문서 9 / 스킬 10 / docs 2) | 복잡 |
| 모듈 범위 | 다중 (memory-tool · improve-tool · dashboard BE · 참조문서 · 스킬 · 부트스트래퍼) | 복잡 |
| 작업 유형 | SSOT 포맷 전환 + 마이그레이션 + 대규모 개선 | 복잡 |
| 외부 의존성 | 없음(표준 라이브러리만) | 단순 |
| **실행 모드** | **복잡** | 하나라도 복잡이면 복잡 모드 |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 ─ A1(opal-be-agent)     : Step 1                     [스키마 계약]
Batch 2 ─ A2(opal-test-agent)   : Step 2                     [RED — 작성자≠구현자 MUST]
Batch 3 ─ A3(opal-be-agent)     : Step 3→4→5→6→7→8→9        [memory_tool.py 단일 소유]
Batch 4 ─ A4(opal-be-agent)     : Step 10        ┐
         ─ A5(opal-be-agent)    : Step 11        │
         ─ A6(opal-task-agent)  : Step 12        │ 7-way 병렬
         ─ A7(opal-task-agent)  : Step 13        │ (파일 집합 교집합 0)
         ─ A8(opal-task-agent)  : Step 14        │
         ─ A9(opal-task-agent)  : Step 15        │
         ─ A10(opal-task-agent) : Step 16        ┘
Batch 5 ─ A11(opal-task-agent)  : Step 17        ┐ 2-way 병렬
         ─ A12(opal-task-agent) : Step 18        ┘
Batch 6 ─ PM 직접               : Step 19 → 20
Batch 7 ─ A13(opal-be-agent)    : Step 21 → PM 직접: Step 22
```

**그룹핑 근거**:
1. **파일 충돌 방지** — `memory_tool.py`를 건드리는 Step 3~9를 A3 하나에 몰았다. 병렬화 이득보다 충돌 비용이 크다.
2. **모듈 응집도** — A4(improve-tool) / A5(dashboard)는 독립 패키지.
3. **병렬 극대화** — Batch 4에서 7-way 병렬로 소비자 전환을 한 번에 흡수한다.
4. **검증 2원화** — A2(RED 작성)와 A3(구현)를 분리해 self-confirming을 차단한다.

### C-2. 스킬 요구사항

| 에이전트 | 스킬 | 갭 |
|---------|------|-----|
| A1, A3, A4, A5, A13 | `op-dev-execute` (BE 구현) | 없음 |
| A2 | `op-dev-test-agent` / `red` 모드 | 없음 |
| A6~A12 | `op-dev-execute` + `opal-doc-standard`(변경이력·버전 규칙) | 없음 — ANALYSIS §6.2 추천 스킬 채택 |

3개 이상 Step에서 반복되는 공통 패턴은 **"변경이력 `(078)` 행 추가 + [MUST] 인용 유지"** 하나이며, 신규 스킬을 만들 규모가 아니므로 각 Step 완료 기준에 인라인 지침으로 넣었다(plan-guide C-2 갭 판별 규칙).

### C-3. 도구 요구사항

| 항목 | 필요 여부 | 비고 |
|------|:---:|------|
| 새 패키지 | **없음** | 표준 라이브러리만 [MUST] |
| MCP | **없음** | ANALYSIS §6.3 — 외부 라이브러리 조사 불필요 |
| CLI | `~/.opal/.venv/bin/python`, `~/.opal/tools/memory-tool/run.sh`, `./scripts/install-mac.sh` | 기존 |
| 테스트 러너 | `unittest`(memory/improve), `pytest`(dashboard) | 기존 혼용 유지 |

### C-4. 테스트 전략

| 계층 | 대상 | 실행 |
|------|------|------|
| L1 단위 | 스키마 검증기·변환기 변형 V-1~V-9·brief 필터·행 회계 | `python -m unittest discover opal/tools/memory-tool/tests` |
| L2 통합 | 8+1 서브명령 왕복, improve-tool 위임 3케이스, dashboard API, **멀티프로세스 동시성**(TS-018/TS-020) | unittest subprocess + pytest |
| L2 실 데이터 | 3개 실 프로젝트 md → json 무손실 (TS-035) | Step 21 배치 |
| L3 실세션 | PM 부트스트랩 브리핑 + 왕복 (TS-036) | Step 22 PM 직접 |
| 회귀 | 비범위 도구·FE 무영향 | §5.2 |

**RED-first 판정**: `red-first.md` §1.5 기준 **RED-first 강제 트랙**(비즈니스 로직 + API 계약 + 마이그레이션 + 버그 수정). 적용 형태 —
- Step 2가 신규 계약 RED를 **선행 작성**하고 실패 증거를 남긴다 (§1 [MUST]).
- 작성 주체 A2 ≠ 구현 주체 A3 (§2 [MUST]).
- Step 8의 기존 88건 이관(어서션 치환)은 **행위 불변 리팩터**에 해당해 RED 강제 대상이 아니나, 이관 결과가 Step 2 RED와 함께 GREEN이 되어야 완료다.
- Step 3~8 루핑 중 Step 2 RED 파일의 단정을 약화·삭제하지 않는다 (§3 [MUST]).
- `state-tool verify --red-check` ON으로 설정한다 (§1.5 state-tool 연동).

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 도구 CLI | Python 3 표준 라이브러리(`json`/`argparse`/`pathlib`/`re`/`os`/`contextlib`/`datetime`) | op-dev-execute |
| 대시보드 BE | FastAPI + Pydantic + pytest | op-dev-execute |
| 테스트 | `unittest`(subprocess 기반), `pytest` | op-dev-test-agent(red/be) |
| 문서 | Markdown(OPAL 스킬·참조 SSOT) | opal-doc-standard |
| 셸 래퍼 | Bash `run.sh` | — |
| 배포 | `scripts/install-mac.sh` (2-Layer) | — |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| 해당 없음 | ANALYSIS §6.3 — 표준 라이브러리·내부 문서 작업만이라 외부 API 조사 불필요. context7/WebSearch 미사용 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 메모리 형식·라이프사이클 SSOT | `opal/core/references/harness/memory-learning.md` | F-007 슬림화 경계 + 라이프사이클 "active만 로드 대상"(§3.3.2 brief 필터 근거) |
| D-2 | 설계 | PM 행동 프로세스 | `opal/core/references/opal-pm.md` §15, §17 | F-006 브리핑 절차 + 타입 우선순위 drift 발견 |
| D-3 | 소스 | memory-tool 본체 | `opal/tools/memory-tool/memory_tool.py:1-1273` | F-001~F-005 주 변경 대상. 삭제 심볼·재사용 로직 식별 |
| D-4 | 소스 | memory-tool 테스트 | `opal/tools/memory-tool/tests/test_memory_tool.py` | Step 8 이관 분류(24 폐기 / ~30 치환) |
| D-5 | 소스 | memory-tool 스키마 | `opal/tools/memory-tool/schema/memory.schema.json` | F-001 현행 실태(행 스키마·enum 불일치) |
| D-6 | 소스 | memory-tool README | `opal/tools/memory-tool/README.md` | Step 9 계약 문서 |
| D-7 | 소스 | improve-tool 위임 | `opal/tools/improve-tool/improve_tool.py:213,291,337,311` | F-008 존재 판정 3곳 + `index_rows` 키 계약(H-4) |
| D-8 | 소스 | improve-tool 테스트 | `opal/tools/improve-tool/tests/test_improve_tool.py:117-122,162-163` | F-008 픽스처 교체 |
| D-9 | 소스 | dashboard 파서·라우터·doctor | `dashboard/backend/parsers/memory_parser.py:82-152`, `routers/memory.py:40-78`, `routers/doctor.py:63` | F-009 전환 대상 + 오프바이원 실측(H-5) |
| D-10 | 소스 | dashboard 파서 테스트 | `dashboard/backend/tests/test_parsers.py:24-87` | F-009 기대값 재작성 |
| D-11 | 소스 | dashboard FE 메모리 화면 | `dashboard/frontend/src/pages/memory/MemoryPage.tsx:50-53,129-139,227-231,263-269,305-319` | **P-3 근거** — `category`/`description` 실사용 확인 → 응답 모델 유지 결정(H-6) |
| D-12 | 설계 | 도구 인벤토리 | `opal/core/references/tools.md:542-639` | Step 14 대상 + 077 충돌 지점 |
| D-13 | 설계 | 태스크 채번 규칙 | `opal/core/references/harness/task-process.md:19-22` | F-005 직접편집 실태 + 개정 대상 |
| D-14 | 설계 | Observability | `opal/core/references/harness/observability.md:23-29` | D-5 stale 정정 대상(FIFO 10 오기재) |
| D-15 | 설계 | Lazy 트리거 테이블 | `opal/core/AGENT.md:48-63` | F-006 L60 행 변경 |
| D-16 | 설계 | 프로젝트 초기화 스킬 | `opal/skills/opal-project-init/SKILL.md:5,394,427-448,574-586,681-682,950-956` | F-010 전환 대상 |
| D-17 | 기획 | 프로젝트 정의·문서 레지스트리 | `docs/PROJECT.md:170` | Step 19 |
| D-18 | 설계 | 아키텍처 2-Layer | `docs/ARCHITECTURE.md:61,70,86,94,247` | 배포 경계 + Step 19 |
| D-19 | 설계 | 코드 컨벤션 | `docs/CONVENTIONS.md` §@header / §변경이력 / §배포 경계 / §플랫폼 분기 격리 / §도구 우선 원칙 / §네이밍 | §5.3 QA [MUST] 인용 원천 |
| D-20 | 설계 | RED-first 트랙 규칙 | `opal/core/references/harness/red-first.md` §1·§1.5·§2·§3 | P-6 트랙 판단(C-4) |
| D-21 | 인용규칙 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` §0·§2 | 본 산출물 인용 포맷 |
| D-22 | 소스 | state-tool 본체 | `opal/tools/state-tool/state_tool.py:144-151,197-222` | `ok`/`err`/`ERROR_CODES` 선례 대조. **`save_state_json`은 원자적 쓰기가 아님**(`open(w)` 직접) → 본 태스크는 선례를 답습하지 않고 `tmp+os.replace`를 새로 도입(H-8) |
| D-23 | 소스 | 실 프로젝트 MEMORY.md 3종 | `.opal/MEMORY.md`, `/Volumes/.../invest-stock/.opal/MEMORY.md`, `/Volumes/.../aos/.opal/MEMORY.md` | §2.4.2 변형 실측 + §3.4.2 변형표 |
| D-24 | 분석 | 본 태스크 ANALYSIS | `tasks/078-260728-opd-메모리-json전환/ANALYSIS.md` §1.4, §2.1, §4, §5, §A-1~A-6 | 테스트 분류·표준라이브러리 제약·핵심 발견·리스크 |
| D-25 | 소스 | 배포 스크립트 | `scripts/install-mac.sh:1015,1091-1147` | H-13 스키마 동반 배포 확인 |
| D-26 | 기획 | 본 태스크 TASK.md | `tasks/078-260728-opd-메모리-json전환/TASK.md` §확정된 설계 방향 §1~§8, §제약 조건 | 범위·제약 원천 |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 준수. 유형: `기획` / `설계` / `소스` / `외부` / `분석`.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 1 | 변환기가 히스토리 표를 인식 못 해 무성 유실 (H-1 / R-T3) | F-004 | **P0** | §3.4.3 행 회계 불변식 — `parsed != candidate`면 `migration_failed`. 헤더 프로파일 3종 + 위치 폴백(V-2). invest-stock을 실증 최종 관문으로 배치(Step 21) |
| 2 | 최초 변환 중 동시 진입으로 데이터 클로버 (H-2 / A-4) | F-004, F-008 | **P0** | 단일 기전 `memory_lock`(O_EXCL + stale 60s + 5s 타임아웃) + double-checked locking + `tmp→os.replace`. TS-018 2프로세스 실증 |
| 3 | 스키마 enum과 코드 enum 불일치로 improve-tool 위임 거부 (H-3 / R-T4) | F-001, F-008 | **P0** | 스키마를 SSOT로 삼고 코드가 파생(§3.1.2). TS-005가 동일성을 상시 단정 |
| 4 | 테스트 공수 과소추정으로 회귀망 공백 (H-9 / R-T5) | F-002 | P1 | Step 8을 독립 Step으로 분리하고 완료 기준에 "총 ≥88건 + `md.read_text()` 어서션 0건" 명시 |
| 5 | dashboard 응답 필드 교체로 FE 백지 (H-6) | F-009 | P1 | **P-3 결정: 응답 모델 유지 + additive만**. FE 파일 변경 0건을 완료 기준에 포함. `title`/`result`는 후속 FE 태스크 |
| 6 | 깨진 현행 파서를 기준선으로 삼아 오류 고착 (H-5 / R-T1) | F-009 | P1 | 실측 증거를 §2.9.2에 고정. `test_parsers.py` 기대값을 **JSON 원본 대조**로 강제 |
| 7 | 채번 경쟁으로 태스크 번호 중복 (H-7 / R-T2) | F-005 | P1 | `task-number --bump` tool-gated + 락. TS-020 20-프로세스 실증. 직접편집 지시 3곳 제거 |
| 8 | 쓰기 중 실패로 SSOT 파손 (H-8) | F-002 | P1 | 검증→쓰기 순서 고정 + `tmp→fsync→os.replace` + 실패 시 tmp 정리. TS-009 |
| 9 | 배포본에 스키마 누락으로 전 명령 사망 (H-13) | F-001, F-012 | P1 | `install_dir` 재귀 복사 확인(D-25) + `schema_load_failed` 결정론 에러(크래시 금지) + Step 20 완료 기준에 배포본 스키마 존재 확인 |
| 10 | 077과 `tools.md` 동시 편집 오프셋 (H-10 / R-T6) | F-011 | P2 | **D-4: 대기 금지** — 편집 직전 재-Read + `## memory-tool` 헤딩 앵커 편집 + code-scan 절 diff 0줄 확인 |
| 11 | R-10 grep AC가 문자 그대로는 달성 불가 (H-11 / R-T7·R-T8) | F-011 | P2 | §3.11.2에서 AC를 **실행 가능한 grep 명령 + 허용 목록**으로 재정의. 역사적 스냅샷 2종은 제외 확정, 일반 명사처럼 보이던 2개 스킬은 stale 포인터로 판정해 **포함** |
| 12 | `.bak` 덮어쓰기로 무손실 위반 (H-12) | F-004 | P2 | `.bak` 선점 시 `.bak.<YYYYMMDDHHmmss>`. TS-013 |
| 13 | 규범 문서만 바뀌고 에이전트 행동이 안 바뀜 | F-006, F-011 | P2 | R-10 AC(b) 실세션 왕복(Step 22)을 완료 조건에 포함 — 문서 검사만으로 끝내지 않는다 |
| 14 | "JSON이 곧 토큰 절약"이라는 잘못된 서사 확산 | 전체 | P2 | §1.1 [MUST] 인용으로 고정. §5.3 QA에 "포맷 자체의 효과로 서술한 문장 0건" 항목 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-28 | 최초 작성 — F-001~F-012 / 22 Step / 6 Phase. P-1 스키마 SSOT+파생 검증기, P-2 변형 V-1~V-9 확정표, P-3 dashboard 응답 모델 유지(FE 실사용 grep 실측), P-4 단일 `memory_lock` 기전, P-5 `show --brief` 계약, P-6 RED-first 강제+작성자≠구현자 분리, P-7 R-10 grep AC 재정의. PM 결정 D-1~D-5 반영 (078) |
