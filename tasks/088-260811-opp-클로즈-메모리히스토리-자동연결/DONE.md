# DONE: CLOSE 완료 시 메모리 히스토리 자동 연결

> 완료일: 2026-08-11 12:51 KST | 태스크: 088 | 파이프라인: opp (agentic)
> 산출물: TASK.md · PLAN.md · AGENTIC-LOG.md · GC-CONVENTION-2026-08-11T11-47-35.md · DONE.md

---

## 1. 무엇을 해결했나

태스크를 마칠 때마다 커밋이 두 번 발생했다. CLOSE에서 산출물을 확정하고 커밋한 뒤, 작업 히스토리를 갱신하느라 `chore: 메모리 히스토리 단계 갱신` 커밋이 한 건 더 붙는 구조였다.

원인은 히스토리 갱신이 **어느 CLOSE 스펙에도 하드스텝으로 없었다**는 것이다. `harness/memory-learning.md`의 "태스크 완료" ambient 트리거로만 걸려 있어 실행 시점이 PM 재량이었고, 자연히 커밋 뒤로 밀렸다.

이제 CLOSE 마지막 행을 `state-tool mark`로 완료하는 순간, 도구가 히스토리 행을 직접 생성한다. 히스토리가 커밋 이전에 확정되므로 DONE.md·관련 문서·brain·히스토리가 한 커밋으로 묶인다.

---

## 2. 왜 이 설계인가 — 3안 채택

캡틴과의 대화에서 3개 안을 비교했고 3안으로 확정했다.

| 안 | 내용 | 판정 |
|----|------|------|
| 1안 | pilot 10종 CLOSE 스펙에 히스토리 스텝을 삽입 | ✗ SKILL.md 10개 + 변경이력 10행의 복제 세금 |
| 2안 | PostToolUse 훅으로 CLOSE 직후 리마인더 주입 | ✗ 훅 미설정·타 플랫폼에서 강제력 소멸 |
| **3안** | **state-tool이 memory-tool을 직접 호출, 훅은 보조** | **✓ 채택** |

3안 채택 근거는 헌법 Core Stance다 — "Enforce, don't just advise: if a rule must always hold, a tool gates it, not prose." 훅 유무·플랫폼 종류와 무관하게 히스토리 행 생성이 100% 집행된다.

**역할 분담**은 판단 개입 여부로 갈랐다.

| 필드 | 주체 | 이유 |
|------|------|------|
| title·date·stage·path | 도구 | state.json에서 결정론적으로 파생 — 판단이 개입하지 않는다 |
| result (핵심결과) | PM | 무엇을 바꿨고 어떤 결과였는지는 LLM 판단의 산출물이라 도구가 대신 쓸 수 없다 |

도구는 `result`를 `"(PM 보강 대기)"` 플레이스홀더로 채우고, 보강 명령을 리마인더로 안내한다.

---

## 3. 무엇을 바꿨나

### 변경 파일 5건

| # | 파일 | 변경 |
|---|------|------|
| M-1 | `opal/tools/state-tool/state_tool.py` | 상수 3종 + 함수 5종 신설, `cmd_mark` 접합 1블록, `ok()` stdout에 `history_link` 조건부 추가 |
| M-2 | `opal/tools/state-tool/todo_mirror_hook.py` | `_extract_payload` 일반화 + `extract_history_link` 신설 + `build_additional_context` 선택 인자 |
| M-3 | `opal/tools/state-tool/tests/test_state_tool.py` | `TestCloseHistoryLink` 7건 (TS-1~TS-7) |
| M-4 | `opal/tools/state-tool/tests/test_todo_mirror_hook.py` | `TestHistoryLinkRelay` 3건 (TS-8~TS-10) |
| M-5 | `opal/core/references/harness/memory-learning.md` | "CLOSE 자동 연결" 절 신설 + 갱신 트리거 문구 정정 + 변경이력 v1.4 |

**pilot 10종 SKILL.md는 한 줄도 바뀌지 않았다.** 도구 계층 단일 지점 변경으로 전 pilot에 동시 적용되는 것이 이 설계의 핵심 이점이다.

### 신설 심볼 (`state_tool.py`)

| 심볼 | 역할 |
|------|------|
| `HISTORY_STAGE_DONE` | `"완료"` — 단계값 상수 |
| `HISTORY_RESULT_PLACEHOLDER` | `"(PM 보강 대기)"` |
| `HISTORY_TITLE_PATTERN` | task_id 분해 정규식 |
| `find_project_root()` | 조상 디렉토리에서 `.opal/MEMORY.json` 앵커 탐색 |
| `derive_history_title()` | `088-260811-opp-클로즈-...` → `088 클로즈 ...` |
| `build_history_reminder()` | 즉시 실행 가능한 보강 명령 문자열 |
| `_run_memory_tool()` | 형제 `memory_tool.py` subprocess 실행 |
| `link_memory_history()` | 오케스트레이션 — 항상 dict 반환, 예외 무전파 |

---

## 4. 설계 쟁점 8종 결정

| # | 쟁점 | 결정 | 배제한 대안과 이유 |
|---|------|------|-------------------|
| 1 | 트리거 판정 | `cmd_mark`의 기존 `is_close_last` + `status == "done"` 재사용 | 프론티어 소진 신호는 agentic `na` 행 때문에 mark 대상 외 행에 좌우됨 |
| 2 | 호출 방식 | `sys.executable` + 형제 `memory_tool.py` subprocess | import는 memory-tool `err()`의 `sys.exit`이 부모를 죽여 비차단 위반 / `run.sh`는 venv 경로 강제 |
| 3 | 경로 해석 | 조상 앵커 탐색, 부재 시 subprocess 미기동 조기 반환 | 환경변수·설정 키 신설은 불필요한 추상화 |
| 4 | 멱등 키 | `path` — `show` 사전 조회로 판정 | `title`은 PM이 정정할 수 있어 불안정 / memory-tool 신규 옵션 추가는 Simplicity 위반 |
| 5 | 실패 표면화 | stdout 전용 `history_link.{status, warning}` | state.json 영속은 `additionalProperties:false` 동반 갱신을 강제 (076 선례 답습) |
| 6 | result 초기값 | `"(PM 보강 대기)"` | 빈 문자열은 미기재/의도된 공란을 구분 불가 |
| 7 | 리마인더 | 실제 title이 박힌 실행 가능 명령, 훅은 병존 확장 | 훅 모듈 개명은 배포된 `settings.json` 경로를 깨뜨림 |
| 8 | 회귀 경계 | 임시 폴더 = 앵커 미탐지 → 무발동 | — |

### 락 상호작용 검증

`state_tool.py`는 어떤 파일 락도 획득하지 않는다. `memory_tool.py`는 자식 프로세스 안에서 `<MEMORY.json>.lock`을 획득·해제한다. 부모가 락을 보유하지 않으므로 **중첩 락·데드락이 성립하지 않는다**. 자식의 락 대기 상한 5초 < 부모 subprocess 타임아웃 10초라, 경합 시에도 부모가 먼저 죽지 않고 자식의 `lock_timeout` JSON을 정상 수신한다.

---

## 5. 동작 증거

### 회귀 — 284건 전건 PASS

```
python3 -m unittest test_state_tool        → Ran 269 tests, OK
python3 -m unittest test_todo_mirror_hook  → Ran 15 tests,  OK
```

RED 단계에서 실패했던 신규 10건(TS-1~TS-10)이 전부 GREEN으로 전환됐고, 기존 274건은 영향받지 않았다.

### E2E 4종 — PM 직접 실증 (샌드박스 프로젝트 루트)

| # | 시나리오 | 결과 |
|---|---------|------|
| ① | CLOSE 마지막 행 mark | `status=created`, `title="090 이투이 검증"`, `path="tasks/090-260811-opp-이투이-검증/"`, `stage="완료"`, `result="(PM 보강 대기)"`, `date="2026-08-11"` |
| ② | 동일 mark 재실행 | `status=duplicate_skipped`, history 행수 1 유지 |
| ③ | MEMORY.json 손상 주입 | `ok=true`, `status=failed`, warning `"MEMORY.json 파싱 실패 (손상된 JSON) — 파일 변경 없음"` |
| ④ | 앵커 부재(비프로젝트) | `ok=true`, `status=skipped`, `.opal` 폴더 미생성 확인 |

③·④가 핵심이다 — 히스토리 연동이 실패해도 `mark`는 항상 성공하므로 CLOSE가 막히지 않는다.

### 배포 정합

`install-mac.sh` 재실행 후 `state_tool.py`·`todo_mirror_hook.py` 배포본 diff **0줄**, `~/.opal/references/harness/memory-learning.md`에 신규 절 반영 확인. `~/.opal/` 직접 편집 0건.

### 컨벤션 자동 진단

Critical 0 / High 0 / Medium 0 / Low 0 / Info 1. Info는 `memory-learning.md` changelog가 날짜만 기재한 건인데, v1.0~v1.3 기존 선례를 승계한 것이라 조치 불요로 판정했다.

### 자기 적용 (dogfooding)

이 태스크 자신의 CLOSE 행 mark가 첫 실사용이다. 088 히스토리 행이 도구에 의해 생성되고 PM이 `result`를 보강하는 흐름으로 마감했다.

---

## 6. PM 판단 기록 (agentic)

| # | 판단 | 근거 |
|---|------|------|
| 1 | Step 10(`docs/ARCHITECTURE.md`) 불채택 | TASK §범위 밖. CLOSE 표준 스텝 "관련 문서 업데이트"가 동일 역할을 이미 소유 |
| 2 | RED 워커의 TS-5·TS-9 강화 승인 | 원문대로 "무발동만 단언"하면 기능 부재 시에도 통과해 RED가 성립하지 않음 |
| 3 | 구현 워커 중단분을 PM 실측 판정으로 종결 | 워커가 Step 9 대기 상태로 멈췄으나 산출물 결손 없음. 재개 0회 |
| 4 | Known Issue 2건 무대응 승인 | 희박 케이스 매트릭스 낮음/낮음, 데이터 손실 없음 |

---

## 7. Known Issues

| # | 내용 | 판정 |
|---|------|------|
| K-1 | FIFO=5로 이미 밀려난 과거 태스크를 재mark하면 신규 행으로 재삽입될 수 있다 | 발생가능성 낮음·영향 낮음. 정보 재게시일 뿐 데이터 손실 없음 |
| K-2 | `show`→`append` 사이 TOCTOU — 두 subprocess 사이에 타 프로세스가 같은 행을 추가하면 중복 1건 | mark는 PM 단일 세션의 순차 명령이라 동시 실행 시나리오 없음 |

---

## 8. 파급 — 다음 태스크부터 달라지는 것

1. CLOSE 마지막 행을 mark하면 히스토리 행이 자동 생성된다. PM이 `memory-tool append`를 손으로 칠 일이 없다.
2. PM은 `result` 보강만 하면 된다 — 명령은 mark 응답에 그대로 붙여넣을 수 있는 형태로 나온다.
3. 히스토리 단계값은 `완료`로 통일된다. `완료·커밋` 표기는 폐기됐다.
4. 커밋은 한 번이면 된다. 히스토리 전용 후속 커밋이 사라진다.
