# TASK: 작업 히스토리 오기재 정정 명령 신설 (`update --kind history`)

> 작성일: 2026-07-30 | 작업 유형: 개선 | 적용 스킬: opds | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`memory-tool update`에 `--kind history`를 신설하여, 잘못 기재된 작업 히스토리 행을 **삭제 없이 정정**할 수 있게 한다.

## 배경

태스크 078에서 메모리 SSOT를 `MEMORY.json`으로 전환하면서 히스토리 관리가 전량 tool-gated가 되었다. 그 결과 **오기재를 되돌릴 경로가 사라졌다.**

현행 히스토리 명령:

| 작업 | 명령 | 상태 |
|------|------|------|
| 추가 | `append --kind history` | ✅ (FIFO 5 자동 적용) |
| 회전 삭제 | `append` 내부 / `prune` | ✅ (도구 결정론, `before`/`after`/`trimmed` 반환) |
| 조회 | `show --brief` / `--history N` | ✅ |
| **정정** | **없음** | ❌ |
| 지목 삭제 | 없음 (설계상 의도) | ❌ |

**문제**: 히스토리에 오타·잘못된 `stage`·잘못된 `path`를 넣으면 되돌릴 방법이 없다. 남는 선택지는 ① 5건을 더 추가해 FIFO로 밀어내기 ② `MEMORY.json` 손편집 두 가지뿐이며, ②는 078이 없애려 한 바로 그 행위다.

**지목 삭제(`delete --kind history`)를 택하지 않은 이유**: `delete`의 무손실 가드는 `status`(`dead`/`superseded`)에 걸려 있는데 히스토리 행에는 `status` 필드가 없다. 가드 없는 삭제 명령을 노출하면 오히려 위험하다. 히스토리는 FIFO 5 회전 로그이므로 **삭제가 아니라 정정이 필요한 지점**이다(소유자 결정 2026-07-30).

## 배경 분석 (대화에서 도출)

### (1) 현행 `update` 계약

```
usage: memory_tool update [-h] --file FILE --title TITLE [--status STATUS] ...
```

`--kind` 인자가 없고 **메모리 인덱스 행만** 대상으로 한다. 히스토리 제목을 넘기면 `row_not_found`로 거부된다(078 실측).

### (2) 히스토리 행 스키마 (`schema/memory.schema.json` `$defs.historyRow`)

| 필드 | 의미 | 정정 필요성 |
|------|------|------------|
| `title` | 태스크 명사구 | 높음 (오타·번호 오기) |
| `date` | 등록일 `YYYY-MM-DD` | 낮음 (자동 기록) |
| `stage` | 진행 단계 (`완료`·`완료·커밋(sha)` 등) | **가장 높음** — 커밋 sha·배포 여부가 사후 확정된다 |
| `path` | `tasks/<폴더>/` | 중간 (폴더명 오기) |
| `result` | 핵심결과 | 높음 (사후 보강) |

> `stage`가 실제 운영에서 가장 자주 바뀐다 — 078 히스토리도 현재 `완료·미커밋`으로 기재돼 있으나 이후 `d7a8ce0`·`447ff09` 커밋이 완료되어 **이미 stale**하다. 이 태스크의 첫 실사용 대상이 된다.

### (3) 참고 선례

`update`에는 이미 `--new-title`(078 이전부터 존재, migrate crude 제목 보정용)이 있다. 히스토리 정정도 동일 패턴으로 확장 가능하다.

## 확정된 설계 방향 (대화에서 합의)

| # | 확정 사항 | 근거 |
|---|----------|------|
| 1 | `update --kind history` 신설 — **정정 전용**, 삭제 없음 | 소유자 결정 (1번 안) |
| 2 | `delete --kind history`는 **신설하지 않는다** | 무손실 가드 근거 부재. 히스토리는 FIFO 회전 로그 |
| 3 | `--kind`의 기본값은 `memory` — **기존 호출 호환 유지** | 하위호환. 기존 `update --title … --status …` 호출이 그대로 동작해야 한다 |
| 4 | `--status`는 히스토리에 적용 불가 (히스토리 행에 `status` 필드 없음) | 스키마 정합 |

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `update --kind history`로 히스토리 행의 `stage`/`result`/`path`/`title`을 정정할 수 있게 한다 | - | 배경 분석 (2) |
| 범위 | **포함**: `memory_tool.py` `cmd_update` 확장 + argparse `--kind`, 테스트, `README.md`, `tools.md` memory-tool 절, `memory-learning.md` 정리 규정 1줄, install 재배포. **제외**: `delete --kind history`(확정 §2), 히스토리 스키마 변경, 다른 서브명령의 `--kind` 확장 | - | 확정 방향 §1·§2 |
| 제약 | 하위호환(`--kind` 기본 `memory`) / 표준 라이브러리만 / 응답 `{"ok":…}` 단일라인 JSON / 원자적 쓰기·락 기존 경로 재사용 / `@header`·변경이력 갱신 / `~/.opal/` 직접 편집 금지 | - | `.opal/AGENT.md` 금지사항 |
| 완료기준 | R-1~R-5 AC 전부 충족 + 078 히스토리 `stage`를 실제로 정정해 실사용 검증 | - | 배경 분석 (2) 주석 |

## 요구사항

- [ ] **R-1. `update --kind {memory,history}` 인자 신설**
  - 무엇을: `cmd_update`와 argparse에 `--kind` 추가, 기본값 `memory`
  - 어디에: `opal/tools/memory-tool/memory_tool.py`
  - 왜: 확정 방향 §1·§3
  - AC: (a) `--kind` 미지정 시 기존과 동일하게 메모리 행을 대상으로 동작 — **기존 테스트 전량 GREEN 유지** (b) `--kind history` 지정 시 히스토리 행을 대상으로 동작 (c) `--kind` 에 `memory`/`history` 외 값 지정 시 `invalid_kind`로 거부

- [ ] **R-2. 히스토리 정정 필드 지원**
  - 무엇을: `--stage` / `--result` / `--path` / `--new-title` 로 히스토리 행을 정정한다
  - 어디에: 동일 파일
  - 왜: 배경 분석 (2) — `stage`가 실운영에서 가장 자주 변한다
  - AC: (a) 4개 필드를 개별·복합 지정해 정정 가능 (b) 지정하지 않은 필드는 **불변** (c) 정정 후 문서가 스키마 검증을 통과 (d) 히스토리 행 수 **불변**(정정은 추가·삭제가 아니다)

- [ ] **R-3. 오용 거부**
  - 무엇을: 히스토리에 적용 불가한 조합을 결정론적으로 거부한다
  - 어디에: 동일 파일 + `ERROR_CODES`
  - 왜: 확정 방향 §4 — 히스토리 행에는 `status` 필드가 없다
  - AC: (a) `--kind history --status dead` → 거부(에러코드 반환, 파일 불변) (b) `--kind memory --stage …` → 거부 (c) 존재하지 않는 히스토리 제목 → `row_not_found` + 파일 불변 (d) 정정 필드를 하나도 안 주면 `invalid_args`

- [ ] **R-4. 무손실·원자성 보존**
  - 무엇을: 기존 `memory_lock` + `atomic_write_json` 경로를 재사용한다
  - 어디에: 동일 파일
  - 왜: 078 §제약 — 부분 기록으로 SSOT 파손 금지
  - AC: (a) 검증 실패·거부 경로에서 `MEMORY.json` mtime·내용 **불변** + `.tmp`·락 잔여 0건 (b) 동시 2프로세스 정정 시 클로버 0

- [ ] **R-5. 문서·배포 반영 + 실사용 검증 (교체형 AC)**
  - 무엇을: `README.md`·`tools.md` memory-tool 절·`memory-learning.md`에 정정 경로를 반영하고 배포한다
  - 어디에: `opal/tools/memory-tool/README.md`, `opal/core/references/tools.md`, `opal/core/references/harness/memory-learning.md`
  - 왜: 078에서 CLI help·문서 drift가 실제 결함으로 드러났다
  - AC: (a) **구형 서술 잔존 0** — "히스토리는 정정 불가"류 서술이 없고, `--kind`·정정 필드가 3개 문서와 `--help`에 문서화됨 (b) **신형 채택** — install 후 배포본으로 `.opal/MEMORY.json`의 078 히스토리 `stage`를 `완료·미커밋` → `완료·커밋(d7a8ce0, 447ff09)`으로 실제 정정하고, `show --brief`로 반영을 확인

## 제약 조건

- **하위호환** — `--kind` 기본값 `memory`. 기존 `update` 호출·기존 테스트가 무변경으로 통과해야 한다.
- **표준 라이브러리만** (`memory_tool.py` @header).
- **원자성·락 재사용** — 새 쓰기 경로를 만들지 않는다.
- **응답 계약** — `{"ok": true|false, ...}` 단일라인 JSON, traceback 금지.
- **배포 경계** — `~/.opal/` 직접 편집 금지. 프로젝트 소스 수정 후 install.
- **`@header`·변경이력** — 변경 파일에 갱신 의무.
- **동시 태스크 주의** — 077이 같은 워킹트리에서 진행 중일 수 있다. 공유 파일(`tools.md`)은 `Edit` 전용·헤딩 앵커로 편집한다(078 §8 규율 승계).

## 기술 스택

- Python 3 (표준 라이브러리 전용) — `memory_tool.py`
- `unittest` (subprocess 기반)
- 마크다운 문서 (참조 문서·README)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | memory-tool 본체 | `opal/tools/memory-tool/memory_tool.py` | R-1~R-4 주 변경 대상. `cmd_update`·`memory_lock`·`atomic_write_json` |
| D-2 | 소스 | 문서 스키마 | `opal/tools/memory-tool/schema/memory.schema.json` | `$defs.historyRow` 필드 정의 (읽기) |
| D-3 | 소스 | memory-tool 테스트 | `opal/tools/memory-tool/tests/test_memory_tool.py` | 132건 회귀 기준선 |
| D-4 | 설계 | 메모리 형식·라이프사이클 SSOT | `opal/core/references/harness/memory-learning.md` | R-5 정리 규정 반영 |
| D-5 | 설계 | 도구 인벤토리 | `opal/core/references/tools.md` | R-5 문서화 + 077 공유 파일 |
| D-6 | 소스 | memory-tool README | `opal/tools/memory-tool/README.md` | R-5 서브명령 계약 |
| D-7 | 기획 | 선행 태스크 완료 보고 | `tasks/078-260728-opd-메모리-json전환/DONE.md` | 전환 결과·잔여 후속(§7)·운영 규율(§8) |
