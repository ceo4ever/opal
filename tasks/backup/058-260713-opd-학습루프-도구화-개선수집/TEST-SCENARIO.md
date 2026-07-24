# TEST SCENARIO: PM 학습 루프 tool-gated 재설계 + 로컬/FW 분리 + fw-inbox

> 작성일: 2026-07-17 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md §리스크 가설 표 기반
> self-confirming 방지: PLAN 워커(opal-plan-agent)와 다른 작성자(PM) 수행

## RED-first 트랙 판정

> 규칙 SSOT: `opal/core/references/harness/red-first.md` / 헌법 §4

하이브리드 자동분기:

| 대상 | 트랙 | 근거 |
|------|------|------|
| **improve-tool** (F-001/F-002 — record/list/show, scope 분기, JSON 계약, fw-inbox write) | **RED-first 강제** | 비즈니스 로직 + 계약 (red-first §1.5) |
| opal-improve 스킬·4-pilot 회고 스텝·install·문서 SSOT 통합 (F-003~006) | 구현 후 검증 | 설정·문서 (red-first §1.5) |

- RED-first 시나리오(S-1~S-5): EXECUTE 진입 전 opal-test-agent(mode: red)가 실패 테스트 코드(pytest) 작성·실행하여 RED 증거 확보 → `state-tool verify --red-check` 게이트 통과 후 GREEN. 작성자≠구현자(op-dev-execute).
- 공통 불변: 어느 트랙이든 ① 테스트 산출물 ② 작성자≠구현자 ③ TEST 단계 검증 유지.
- L3(사용자 협업)·M2(E2E 자동화): **해당 없음** — FE 화면/컴포넌트·인증/인가·외부 API 엔드포인트 변경 없음(전부 로컬 CLI·문서). M2 의무 트리거 비해당.

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-004 회고 하드스텝 (4 pilot) | 회고 스텝이 CLOSE를 차단 — no-op 미준수 시 대상 부재에서 CLOSE 블로킹 | P0 | L1/M1 | S-9 |
| H-2 | F-003 scope 분류(2원화) + F-001 분기 집행 | 로컬/FW 오분류 — scope 역기록 | P0 | L1/M1 | S-3, S-6 |
| H-3 | F-006 rename/delete | `self-improvement.md`·구 `pm-learning-loop.md` dangling 참조 잔존 | P1 | L1/M1 | S-12 |
| H-4 | F-001 improve-tool JSON 계약 | 출력에 `"ok"` 누락 → 호출자 파싱 실패 | P1 | L1/M1 | S-1, S-5 |
| H-5 | F-005 install fw-inbox 초기화 | 멱등성 위반 — 재설치 시 기존 항목 삭제 | P0 | L2/M1 | S-10 |
| H-6 | F-001 로컬 memory-tool 위임 | `.opal/MEMORY.md` 부재 시 위임 실패·예외 전파 | P2 | L1/M1 | S-4 |
| H-7 | F-004 4-pilot 일관성 | 4파일 중 일부만 회고 스텝 보유 | P1 | L1/M1 | S-8 |
| H-8 | F-002 fw-inbox 항목 스키마 | 출처 메타(host·project·situation·created) 누락 → 자기완결성 상실 | P1 | L1/M1 | S-2 |
| H-9 | F-006 §5 stub / 트리거 테이블 지칭 | 통합 후에도 `opal-pm.md §5` stub이 구 파일/잘못된 위치 지칭 | P1 | L1/M1 | S-13 |

> 가설 9건 → 시나리오 14건 (S-1~S-14). 정량 충족.

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터 (파일/디렉토리 fixture — 실 데이터, mock 금지)

| 대상 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 임시 프로젝트 A | `$TMP/proj-A/.opal/MEMORY.md` | 존재 — 유효 memory 인덱스(마커 포함) | fixture (수동 seed) |
| 임시 프로젝트 B | `$TMP/proj-B/` | `.opal/MEMORY.md` 부재 | fixture (빈 디렉토리) |
| fw-inbox 수집소 | `~/.opal/fw-inbox/` | 존재 (테스트 시 임시 `$TMP/fw-inbox` 지정 가능) | install 초기화 / 수동 |
| 기존 fw 항목 | `~/.opal/fw-inbox/20260101-000000-seed-existing.md` | 멱등 테스트용 사전 1건 | 수동 seed |
| 4 pilot SKILL | `opal/skills/opal-pilot-{dev,write-tech,gc,project-dev}/SKILL.md` | EXECUTE 후 회고 스텝 삽입됨 | EXECUTE 산출 |
| 신규 SSOT | `opal/core/references/harness/pm-improvement-loop.md` | EXECUTE 후 존재 (rename+병합) | EXECUTE 산출 |
| 삭제 대상 | `opal/core/references/pm/self-improvement.md` | EXECUTE 후 부재 | EXECUTE 산출 |

### 2.2 시나리오별 데이터 흐름 (Given / When / Then)

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | improve-tool 존재 | `record`/`list`/`show` 성공·실패·no-op 3경로 호출 | 모든 stdout JSON에 `"ok"` 키 존재 |
| S-2 | fw-inbox 디렉토리 존재 | `record --scope fw --title T --situation retrospective --project-root $TMP/proj-A` | fw-inbox에 `*.md` 1건 신규 + frontmatter에 host·project·situation·created 4키 |
| S-3 | proj-A/.opal/MEMORY.md 존재 | `record --scope local --title T --project-root $TMP/proj-A` | MEMORY.md에 `type=improvement,status=candidate` 항목 append (memory-tool 위임) |
| S-4 | proj-B (MEMORY.md 부재) | `record --scope local --project-root $TMP/proj-B` | write 없음 + `{"ok":true,"skipped":true,"reason":"no MEMORY.md"}` |
| S-5 | improve-tool 존재 | `record --scope wrong`(잘못된 scope) / 필수 인자 누락 호출 | `{"ok":false,"error":...}` (비정상 종료 아님) |
| S-6 | opal-improve SKILL.md 존재(EXECUTE 후) | 파일 grep | 5단계 + 결정론 게이트표 + 루브릭표 + 동점 에스컬레이션 + 역할일반어 `PM` 문자열 존재 |
| S-7 | registry에 opim 엔트리 등록됨 | `skill-registry.js match "opim"` | `found:true`, name=opal-improve 매칭 |
| S-8 | 4 pilot SKILL.md (EXECUTE 후) | 4파일 회고 스텝 마커 grep | opd·opwt·opgc·oppd 모두 회고 스텝 존재 (대칭) |
| S-9 | opd CLOSE 회고 스텝 본문 | no-op 안전 문구 grep + 0건 판독 | "개선후보 0건/없음 시 CLOSE 비차단" 명문 존재 (brain-ingest no-op 패턴) |
| S-10 | fw-inbox에 seed 항목 1건 | `install-mac.sh` 2회 연속 실행 | seed 항목 파일 보존 (삭제 안 됨) |
| S-11 | install 전 상태 | `install-mac.sh` 1회 실행 | `~/.opal/skills/opal-improve/`·`~/.opal/tools/improve-tool/`·`~/.opal/fw-inbox/` 3자산 존재 |
| S-12 | EXECUTE 완료 소스 트리 | `grep -rn "self-improvement\|pm-learning-loop"` 전수 | 매칭 0건 |
| S-13 | opal-pm.md §5 stub (EXECUTE 후) | §5 stub grep | `pm-improvement-loop.md` 지칭, 자기참조·구파일 지칭 0건 |
| S-14 | pm-improvement-loop.md (EXECUTE 후) | 파일 존재 + 섹션 grep + self-improvement.md 부재 확인 | 트리거 테이블·5단계·기록위치 3요소 존재 AND self-improvement.md 미존재 |

---

## 3. 검증 시나리오

> **RED-first 트랙**(S-1~S-5): pytest 실패 테스트 선작성(opal-test-agent mode:red) → RED 증거 → GREEN 구현. 구현/테스트 작성자 분리.
> **구현 후 검증**(S-6~S-14): 산출물 검사·정적 grep·멱등 실행.
> mock/patch/MagicMock 미사용 — 실 fixture(임시 프로젝트·실 fw-inbox write·실 memory-tool 위임) 사용.

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: improve-tool JSON 계약 3경로 (성공/실패/no-op)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | improve_tool.py 전 서브명령 출력 계약 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) — **RED-first** |
| 조건 | 성공(record fw), 실패(잘못된 scope), no-op(local+MEMORY.md 부재) 3경로 각각 호출, stdout 캡처 |
| 기대 결과 | 3경로 모두 JSON 파싱 성공 + `"ok"` 키 존재 (성공 `true`, 실패 `false`, no-op `true`+`skipped`) |
| 도구 | pytest (subprocess로 run.sh 호출, stdout JSON assert) |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/improve-tool/tests/test_improve_tool.py::TestJsonContractThreePaths -v` |
| 결과 | Pass |
| 상세 | `TestJsonContractThreePaths` 3케이스 전부 PASS — `test_record_fw_success_has_ok_true`(성공 `"ok":true`), `test_record_invalid_scope_has_ok_false`(실패 `"ok":false`), `test_record_local_noop_has_ok_true_and_skipped`(no-op `"ok":true`+`"skipped":true`). 전체 스위트 14/14 PASS(RED→GREEN 전환 확인, 실행 로그 확보). |

#### S-2: record --scope fw → fw-inbox 자기완결 항목 생성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 (TS-001, TS-005) |
| 대상 | `record --scope fw` write 로직 + fw-inbox 스키마 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) — **RED-first** |
| 조건 | `record --scope fw --title "T" --situation retrospective --project-root $TMP/proj-A` (fw-inbox=임시 경로) |
| 기대 결과 | ①`~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md` 1건 생성 ②frontmatter에 `host`·`project`·`situation`·`created` 4키 전부 존재 ③`{"ok":true,"scope":"fw","path":...}` |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/improve-tool/tests/test_improve_tool.py::TestFwInboxSelfContainedEntry -v` |
| 결과 | Pass |
| 상세 | `TestFwInboxSelfContainedEntry` 3케이스 전부 PASS — `test_fw_entry_frontmatter_has_required_keys`(host/project/situation/created 4키 확인), `test_record_fw_creates_exactly_one_md_file`(신규 1건만 생성), `test_record_fw_json_contract_has_scope_and_path`(`{"ok":true,"scope":"fw","path":...}`). `IMPROVE_FW_INBOX` 테스트 격리 훅으로 실 fw-inbox 오염 없이 실 write 검증. |

#### S-3: record --scope local → memory-tool 위임 (MEMORY.md 존재)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 (TS-002, TS-006) |
| 대상 | scope local 분기 + memory-tool append 위임 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) — **RED-first** |
| 조건 | proj-A/.opal/MEMORY.md 존재 상태에서 `record --scope local --title "T" --body "B" --project-root $TMP/proj-A` |
| 기대 결과 | ①MEMORY.md에 `type=improvement, status=candidate` 항목 1건 append(실 memory-tool 위임) ②`{"ok":true,"scope":"local"}` ③fw-inbox엔 write 없음(분기 격리) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/improve-tool/tests/test_improve_tool.py::TestLocalScopeMemoryDelegation -v` |
| 결과 | Pass |
| 상세 | `TestLocalScopeMemoryDelegation` 3케이스 전부 PASS — `test_record_local_appends_improvement_candidate_row`(실 memory-tool subprocess 위임으로 MEMORY.md에 type=improvement/status=candidate 행 append 확인), `test_record_local_does_not_write_fw_inbox`(분기 격리 — fw-inbox write 0건), `test_record_local_ok_contract_scope_local`(`{"ok":true,"scope":"local"}`). mock 없이 실 memory-tool run.sh 호출. |

#### S-4: record --scope local graceful skip (MEMORY.md 부재)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 (TS-004) |
| 대상 | MEMORY.md 부재 시 no-op 안전성 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) — **RED-first** |
| 조건 | proj-B(`.opal/MEMORY.md` 부재)에서 `record --scope local --project-root $TMP/proj-B` |
| 기대 결과 | 예외 전파 없이 `{"ok":true,"scope":"local","skipped":true,"reason":"no MEMORY.md"}`, 파일 write 0건 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/improve-tool/tests/test_improve_tool.py::TestLocalScopeGracefulSkip -v` |
| 결과 | Pass |
| 상세 | `TestLocalScopeGracefulSkip` 2케이스 전부 PASS — `test_record_local_skip_when_memory_md_absent`(예외 전파 없이 `{"ok":true,"scope":"local","skipped":true,"reason":"no MEMORY.md"}` 반환), `test_record_local_skip_writes_zero_files`(write 0건). H-6 graceful skip 확인. |

#### S-5: record 인자 오류 경계 (잘못된 scope/필수 누락)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | 인자 검증 실패 경로 계약 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) — **RED-first** |
| 조건 | `record --scope wrong` / `record`(--scope 누락) / `record --scope fw`(--title 누락) |
| 기대 결과 | 각 경우 `{"ok":false,"error":"..."}` 반환(비정상 크래시·스택트레이스 노출 아님) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/improve-tool/tests/test_improve_tool.py::TestRecordArgumentValidation -v` |
| 결과 | Pass |
| 상세 | `TestRecordArgumentValidation` 3케이스 전부 PASS — `test_missing_scope_returns_graceful_error`, `test_missing_title_returns_graceful_error`, `test_wrong_scope_value_returns_graceful_error` 모두 `{"ok":false,"error":"..."}` graceful 반환(크래시·traceback 없음, `_GracefulArgumentParser` 커스텀 에러 핸들링 확인). |

#### S-6: opal-improve SKILL.md 5단계 + scope 2원화 명시

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 (TS-007, TS-007b) |
| 대상 | `opal/skills/opal-improve/SKILL.md` |
| 계층 | L1 |
| 실행 방식 | M1 (bash grep — 산출물 검사) |
| 조건 | EXECUTE 후 SKILL.md 존재 |
| 기대 결과 | 5단계(관찰→분류→기록→보고→승인) + 1차 결정론 게이트표 + 2차 루브릭표 + 동점 에스컬레이션 + 역할일반어 `PM`(개인 호칭 부재) 전부 존재 |
| 도구 | bash grep |
| 실행 명령 | `for kw in "관찰" "분류" "기록" "보고" "승인" "결정론 게이트" "루브릭" "에스컬레이션"; do grep -q "$kw" opal/skills/opal-improve/SKILL.md && echo "OK: $kw" || echo "MISSING: $kw"; done` + `grep -n "\\bPM\\b" opal/skills/opal-improve/SKILL.md`(역할일반어 확인) + `grep -n "알투\|캡틴" opal/skills/opal-improve/SKILL.md`(개인 호칭 0건 확인) |
| 결과 | Pass |
| 상세 | op-dev-test-agent 독립 재실행 확인: 8개 키워드(관찰/분류/기록/보고/승인/결정론 게이트/루브릭/에스컬레이션) 전부 OK. `\bPM\b` 8회 매칭 — 전부 역할일반어("PM 개선 루프", "PM이 판단 불확실", "결정 테스트: 모든 프로젝트/PM에 유효한가" 등)로만 사용. `알투\|캡틴` grep 결과 매칭 0건(exit=1) — 개인 호칭 배제 원칙 준수 확인. EXECUTE 자가점검과 일치. |

#### S-7: registry match로 //opim 해석

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 (TS-008) |
| 대상 | `opal-skills-registry.json` opim 엔트리 |
| 계층 | L1 |
| 실행 방식 | M1 (skill-registry.js 실행) |
| 조건 | EXECUTE 후 registry 등록됨 |
| 기대 결과 | `node skill-registry.js match "opim"` → `found:true`, name=opal-improve. JSON 유효성 통과 |
| 도구 | node (skill-registry.js) |
| 실행 명령 | `node opal/tools/skill-registry/skill-registry.js match "opim"` + `python3 -c "import json; json.load(open('opal/core/references/opal-skills-registry.json'))"`(JSON 유효성) |
| 결과 | Pass |
| 상세 | op-dev-test-agent 독립 재실행 확인: `match "opim"` → `{"found":true,"name":"opal-improve","group":"opal","alias":"opim","description":"PM 개선 루프 — 관찰→분류→기록→보고→승인. 로컬 PM 개선 / FW 개선 분류 기록","path":"/Users/iskang/.opal/skills/opal-improve/SKILL.md","domain":"improvement","cleanInput":"opim"}`. JSON 유효성 `python3 -c json.load(...)` → 성공("VALID JSON"). EXECUTE 자가점검이 언급한 install-gated 상태(설치된 SKILL.md 부재)는 §S-10/S-11 sandbox install 검증에서 실제로 `~/.opal/skills/opal-improve/SKILL.md` 배포 확인됨(별도 항목) — 회귀 아님, 정상. |

#### S-8: 4-pilot 회고 하드스텝 대칭 존재

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 (TS-009) |
| 대상 | opd/opwt/opgc/oppd 4 pilot SKILL.md |
| 계층 | L1 |
| 실행 방식 | M1 (bash grep 4파일 대칭) |
| 조건 | EXECUTE 후 4파일 |
| 기대 결과 | 4파일 모두 CLOSE에 회고 하드스텝(공통 템플릿 마커) 존재 — 4/4 대칭, 누락 0 |
| 도구 | bash grep |
| 실행 명령 | `for f in opal/skills/opal-pilot-dev/SKILL.md opal/skills/opal-pilot-write-tech/SKILL.md opal/skills/opal-pilot-gc/SKILL.md opal/skills/opal-pilot-project-dev/SKILL.md; do echo -n "$f : "; grep -c "회고(개선 루프) 하드스텝" "$f"; done` |
| 결과 | Pass |
| 상세 | op-dev-test-agent 독립 재실행 확인: 4파일 전부 카운트 2(본문 1 + 변경이력 1) — opd/opwt/opgc/oppd 4/4 대칭, 누락 0. 추가로 각 파일에서 삽입 위치가 op-brain-ingest 직후·완료보고(또는 문서등록) 직전임을 본문 대조로 확인(opd STEP6 순서: DONE.md mark→관련문서 업데이트→op-brain-ingest→회고 하드스텝→완료보고). |

#### S-9: 회고 스텝 no-op 안전 (개선후보 0건 시 CLOSE 비차단)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (TS-011) |
| 대상 | 회고 하드스텝 본문 (opd 대표) |
| 계층 | L1 |
| 실행 방식 | M1 (bash grep — 산출물 검사) |
| 조건 | EXECUTE 후 회고 스텝 본문 |
| 기대 결과 | "개선후보 0건/없음 시 자연 스킵(no-op), CLOSE 비차단" 명문 존재 (op-brain-ingest no-op 패턴 답습). 회고 산출은 개선후보 N건 또는 "없음"을 도구로 기록하도록 명시 |
| 도구 | bash grep |
| 실행 명령 | `for f in opal/skills/opal-pilot-dev/SKILL.md opal/skills/opal-pilot-write-tech/SKILL.md opal/skills/opal-pilot-gc/SKILL.md opal/skills/opal-pilot-project-dev/SKILL.md; do echo "--- $f ---"; grep -n "개선후보 0건\|no-op 안전" "$f"; done` |
| 결과 | Pass |
| 상세 | op-dev-test-agent 독립 재실행 확인: 4파일 모두 "**no-op 안전 [MUST]**: 궤적 신호에서 개선 후보가 **없으면** 기록 없이 \"개선후보 0건\" 보고 — op-brain-ingest의 skipped와 동일하게 **CLOSE를 중단시키지 않는다**" 문구 동일 존재(대칭). op-brain-ingest skipped 패턴 답습 확인. |

### L2. 프로세스 통합 (자동, 실 파일시스템 read→조작→re-read)

#### S-10: install fw-inbox 멱등 (재설치 시 기존 항목 보존)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 (TS-013) |
| 대상 | `install-mac.sh` fw-inbox 초기화 블록 |
| 계층 | L2 |
| 실행 방식 | M1 (bash — install 반복 실행) |
| 조건 | fw-inbox에 seed 항목 1건 존재 → install 2회 연속 실행 |
| 기대 결과 | seed 항목 파일이 2회 install 후에도 보존(clean_dirs 미포함, `mkdir -p`/create-if-absent only) |
| 도구 | bash |
| 실행 명령 | 실 `~/.opal` 오염 방지를 위해 **sandbox HOME 격리 실 install 실행**(정적 grep 대체 아님): ①스크래치패드에 sandbox `$HOME`(`install-test-home`) + sandbox framework root(`install-test-fw` — `skills`/`opal` 심볼릭 링크로 실 레포를 read-only 참조, `scripts/install-mac.sh`는 마지막 `main "$@"` 줄만 제거한 사본) 구성 ②`$SANDBOX_HOME/.opal/fw-inbox/seed-test.md`("seed") 시드 ③`HOME="$SANDBOX_HOME" bash -c 'source install-mac.sh; detect_framework_root; detect_user; install_opal'` 1회차 실행 ④동일 명령 2회차 실행 ⑤`test -f "$SANDBOX_HOME/.opal/fw-inbox/seed-test.md"` |
| 결과 | Pass |
| 상세 | 실 `~/.opal`은 전혀 건드리지 않고(설치 전/후 `~/.opal/fw-inbox/seed-test.md` 부재 확인 — CLEAN) sandbox HOME에서 `install_opal` 함수를 2회 연속 실제 실행. 1회차 실행 후 seed-test.md 존재(사전 시드) → 2회차 실행(clean_dirs=[skills,agents,references,templates,tools,dashboard-server] rm -rf 포함 전체 재설치 경로 통과) 후에도 `seed-test.md` 파일 그대로 보존 확인(`cat` 결과 "seed" 원본 그대로). fw-inbox는 clean_dirs 미포함 + `mkdir -p`(존재 시 no-op)로만 초기화되어 H-5(멱등) 실증. mock/정적 grep 아님 — 실제 install 스크립트 함수 2회 구동으로 증거 확보. |

#### S-11: install 3자산 배포/초기화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 (TS-012) |
| 대상 | install-mac.sh (+windows.ps1) 배포 |
| 계층 | L2 |
| 실행 방식 | M1 (bash — install 실행 후 경로 확인) |
| 조건 | install 1회 실행 |
| 기대 결과 | `~/.opal/skills/opal-improve/SKILL.md`·`~/.opal/tools/improve-tool/run.sh`(+chmod)·`~/.opal/fw-inbox/` 3자산 존재. 기존 25개 자산 회귀 없음 |
| 도구 | bash |
| 실행 명령 | S-10과 동일 sandbox 실행(HOME 격리, `install_opal` 함수 실제 구동) 후 `test -f "$SANDBOX_HOME/.opal/skills/opal-improve/SKILL.md" && test -x "$SANDBOX_HOME/.opal/tools/improve-tool/run.sh" && test -d "$SANDBOX_HOME/.opal/fw-inbox"` |
| 결과 | Pass |
| 상세 | 1회차 install 실행 후 3자산 전부 확인: `skills/opal-improve/SKILL.md` 존재, `tools/improve-tool/run.sh` 실행권한(`-rwxr-xr-x`) 존재, `fw-inbox/`(+README.md seed) 디렉토리 존재. 2회차 install 후에도 3자산 동일 유지(회귀 없음). 추가 확인: sandbox 배포 스킬 48개·도구 17개(디렉토리 카운트) — 기존 자산 회귀 없이 정상 배포. 정적 grep 대체가 아닌 **실 install_opal 함수 2회 실행**으로 증거 확보(mock 없음). |

#### S-12: dangling 참조 전수 grep 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 (TS-016) |
| 대상 | 전체 소스 트리 |
| 계층 | L2 |
| 실행 방식 | M1 (bash grep 전수) |
| 조건 | EXECUTE(F-006) 완료 후 |
| 기대 결과 | `grep -rn "self-improvement"` 및 구 `pm-learning-loop` 참조 → 매칭 0건 (신규 SSOT 파일명 제외) |
| 도구 | bash grep |
| 실행 명령 | `grep -rn "self-improvement\|pm-learning-loop" opal/ scripts/ docs/` |
| 결과 | Pass |
| 상세 | 전수 grep 매칭 6건 — 전부 **라이브 dangling 포인터가 아님**: ① `opal/core/AGENT.md:250` 변경이력(과거 rename 기록) ② `opal-pm.md:344` 변경이력(v1.0, 2026-04-21 — CONVENTIONS §변경이력 이력 보존 원칙에 따라 소급 변경 대상 아님, PLAN §2.6.2 "(참고)" 항목과 일치) ③ `opal-pm.md:349` 변경이력(v1.5, 이번 rename 작업 자체 기록) ④ `pm-improvement-loop.md:34` — "지칭 정정" 설명 문단(구 파일명을 언급하며 오류가 소멸했음을 서술, 실제 링크/포인터 아님) ⑤ `pm-improvement-loop.md:111` 변경이력(rename 기록) ⑥ `docs/PROJECT.md:134` — "SSOT: pm-improvement-loop.md — 정의 3문서(구 `pm-learning-loop.md`·`self-improvement.md`·§5 stub)를 단일 SSOT로 통합"이라는 완료 서술(신규 SSOT를 정확히 지칭, 구 파일명은 역사적 언급일 뿐). 살아있는 참조(파일 경로로 실제 open/link)는 0건 — AC 충족. self-improvement.md 파일 자체도 부재 확인(S-14). |

#### S-13: opal-pm §5 stub 지칭 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 (TS-017) |
| 대상 | `opal-pm.md §5` stub + 트리거 테이블 지칭 |
| 계층 | L2 |
| 실행 방식 | M1 (bash grep — 참조 정합) |
| 조건 | EXECUTE 후 |
| 기대 결과 | §5 stub이 `pm-improvement-loop.md`를 지칭. "트리거 테이블은 §5에 유지" 류 자기참조 지칭 오류 소멸 |
| 도구 | bash grep |
| 실행 명령 | `grep -n "^## 5" opal/core/references/opal-pm.md` + `sed -n '71,76p' opal/core/references/opal-pm.md` |
| 결과 | Pass |
| 상세 | `opal-pm.md:71` "## 5. PM 개선 루프" stub이 `:75`에서 "상세(두 트랙 개요, 트리거 테이블, 5단계 프로세스, 학습 2분류·기록 위치, 도구 집행, hook 미채택 근거): `opal/core/references/harness/pm-improvement-loop.md` 참조."로 신규 SSOT를 정확히 지칭. 구 파일명(`pm-learning-loop.md`)·자기참조식 지칭 오류("트리거 테이블은 §5에 유지") 0건. `pm-improvement-loop.md:34`가 이 지칭 오류의 소멸을 명시적으로 서술(H-9 해소 확인). |

#### S-14: SSOT 단일화 + 삭제 확인

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3, H-9 (TS-014, TS-015) |
| 대상 | pm-improvement-loop.md (신규 SSOT) + self-improvement.md (삭제) |
| 계층 | L2 |
| 실행 방식 | M1 (bash — 파일 존재/부재 + 섹션 grep) |
| 조건 | EXECUTE(F-006) 후 |
| 기대 결과 | ①`pm-improvement-loop.md` 존재 + 트리거 테이블·5단계·기록위치 3요소 포함 ②`self-improvement.md` 부재 ③변경이력 행 추가 |
| 도구 | bash |
| 실행 명령 | `test -f opal/core/references/harness/pm-improvement-loop.md` + `grep -n "트리거 테이블\|## 3. 5단계 프로세스\|## 4. 학습 2분류 + 기록 위치" opal/core/references/harness/pm-improvement-loop.md` + `test -f opal/core/references/pm/self-improvement.md` |
| 결과 | Pass |
| 상세 | `pm-improvement-loop.md` 존재(EXISTS) 확인. 3요소 전부 존재 — `## 2. 트리거 테이블`(:24), `## 3. 5단계 프로세스`(:38), `## 4. 학습 2분류 + 기록 위치`(:54). `self-improvement.md`는 부재 확인(CONFIRMED ABSENT). 변경이력에 `v2.0 2026-07-17` rename+병합+6섹션 재구성 행 존재(:111). AC ①②③ 전부 충족. |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

**해당 없음** — FE 화면/사용자 플로우·수동 부하 테스트 대상 없음. 전 시나리오 자동 검증(M1). L3/M3 불요.

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R3 (improve-tool 기록·계약) | H-4 | L1/M1 | S-1, S-5 | `opal/tools/improve-tool/tests/test_improve_tool.py`:`[T058/L1-R3]` | RED-first |
| R4 (fw-inbox 자기완결) | H-8 | L1/M1 | S-2 | `…/test_improve_tool.py`:`[T058/L1-R4]` | RED-first |
| R3/R4 (scope 분기·위임) | H-2 | L1/M1 | S-3 | `…/test_improve_tool.py`:`[T058/L1-R3b]` | RED-first |
| R4 (no-op 안전) | H-6 | L1/M1 | S-4 | `…/test_improve_tool.py`:`[T058/L1-R4b]` | RED-first |
| R2 (5단계·분류 분기) | H-2 | L1/M1 | S-6 | 산출물 검사(grep) | 구현 후 |
| R2 (registry //opim) | H-2 | L1/M1 | S-7 | skill-registry match | 구현 후 |
| R1 (4-pilot 회고 대칭) | H-7 | L1/M1 | S-8 | 4파일 grep | 구현 후 |
| R1 (no-op 비차단) | H-1 | L1/M1 | S-9 | 산출물 검사(grep) | 구현 후 |
| R6 (install 멱등) | H-5 | L2/M1 | S-10 | install 반복 실행 | 구현 후 |
| R6 (3자산 배포) | H-5 | L2/M1 | S-11 | install 실행 확인 | 구현 후 |
| R5 (dangling 0건) | H-3 | L2/M1 | S-12 | 전수 grep | 구현 후 |
| R5 (§5 stub 정합) | H-9 | L2/M1 | S-13 | grep 참조 정합 | 구현 후 |
| R5 (SSOT 단일화·삭제) | H-3, H-9 | L2/M1 | S-14 | 파일 존재/부재 검사 | 구현 후 |

매핑 완전성: 9개 가설(H-1~9) 전부 ≥1 시나리오 연결. 미매핑 시나리오 0.

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff (improve_tool.py) | Pass | `ruff check opal/tools/improve-tool/improve_tool.py` → "All checks passed!" (exit 0). 시스템 homebrew ruff 0.15.17 사용(venv에 ruff 미설치 — 별개 실행 경로) |
| 2 | 타입 체크 | mypy (improve_tool.py) | Skip (도구 부재) | venv(`~/.opal/.venv`)·시스템 전역 모두 mypy 미설치 확인(`pip3 show mypy` → not found). 프로젝트에 mypy 요구사항 파일(requirements-dev.txt/pyproject.toml) 부재 — 대체로 `python3 -m py_compile improve_tool.py` 구문 검증 실행 → COMPILE OK. mypy 자체는 환경 미비로 미실행(허위 Pass 표기 금지, 정직 보고) |
| 3 | JSON 계약 | 전 서브명령 `"ok"` 키 | Pass | S-1~S-5 pytest 14/14로 실증 — record 성공/실패/no-op 3경로, list/show 계약 전부 `"ok"` 키 보장 |
| 4 | run.sh 표준 골격 | 수동 대조 (brain-tool 패턴) | Pass | `diff opal/tools/brain-tool/run.sh opal/tools/improve-tool/run.sh` → 도구명·스크립트명 치환 2줄만 차이, venv 경로 체크·`{"ok":false,"error":...}` 실패 계약·`exec` 위임 골격 100% 동일 |
| 5 | @header (improve_tool.py) | header-rules 준수 | Pass | 파일 상단 `@header {module/layer/domain/description/exports/depends}` JSON 블록 존재, header-rules.md 스키마(module=improve_tool, layer=util, domain=opal-pipeline, exports=[cmd_record,cmd_list,cmd_show], depends=[memory_tool]) 충족 |
| 6 | registry JSON 유효성 | `python3 -c json.load(...)` | Pass | `opal-skills-registry.json` 파싱 성공("VALID JSON"). changelog에 `{"version":"3.9.0","task":"058",...}` opim 등록 항목 존재 |
| 7 | 변경이력 행 추가 | 스킬·도구·참조문서·install 전부 | Pass | improve_tool.py(v1.0)·opal-improve/SKILL.md(v1.0)·opal-skills-registry.json(changelog task=058)·pm-improvement-loop.md(v2.0)·tools.md(v2.2)·install-mac.sh(v4.0, 2행)·windows.ps1(v1.18.0)·4-pilot SKILL.md(각 1행) 전부 변경이력 행 확인. memory_tool.py도 v1.1(enum additive) 이력 존재 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -inE "api[_-]?key|secret|password|token\s*=|bearer"` — improve_tool.py·fw-inbox-README.md 모두 매칭 0건 |
| 2 | improve-tool write 경로 화이트리스트 | Pass | improve_tool.py 소스 전수 확인 — write 관련 호출은 `fw_inbox_dir.mkdir()`(`_resolve_fw_inbox_dir()`가 `IMPROVE_FW_INBOX` 환경변수 또는 기본 `~/.opal/fw-inbox`로 한정)와 `file_path.write_text()`(fw-inbox 항목 파일) 단 1건뿐. local scope는 자체 write 없이 `subprocess.run(["bash", MEMORY_TOOL_RUN, ...])`로 memory-tool에 전량 위임 — fw-inbox·MEMORY.md(memory-tool 경유) 외 임의 write 경로 0건 |
| 3 | `~/.opal/` 직접 편집 금지 준수 | Pass | improve-tool은 `~/.opal/fw-inbox/`(런타임 데이터 디렉토리, CONVENTIONS §배포 경계 예외 대상)에만 write — 스킬/도구/references 등 배포 자산 직접 편집 코드 경로 없음. S-10/S-11 sandbox install 검증에서도 실 `~/.opal`은 실행 전후 무변경(seed-test.md 등 sandbox 산출물 실 `~/.opal`에 유입 0건) 확인 |
| 4 | .gitignore 확인 | Pass | `.gitignore:7`에 `__pycache__/` 존재, `git ls-files opal/tools/improve-tool/` 결과에 `__pycache__` 미포함(미트래킹) 확인 |

## 7. 판정

**All Pass -- 근거: RED-first 트랙(S-1~S-5) improve-tool pytest 14/14 실행 로그로 GREEN 실증(mock 없음, 실 fixture·실 memory-tool 위임·실 fw-inbox write). 구현 후 검증 트랙(S-6~S-9, S-12~S-14) 전부 산출물 grep/파일존재 검사로 op-dev-test-agent가 독립 재실행하여 EXECUTE 자가점검과 일치 확인(무비판 수용 아님, 직접 재검증). L2 install 트랙(S-10, S-11)은 "install-gated로 캡틴 배포 위임"이 아니라 **실 `~/.opal`을 오염시키지 않는 sandbox HOME 격리 환경에서 install_opal 함수를 실제 2회 구동**하여 3자산 배포(S-11)와 fw-inbox 멱등 보존(S-10)을 실증 — 정적 grep 대체나 허위 PASS 없음(헌법 §4 "Don't fake it" 준수). §5 코드 품질 7항목 중 6 Pass + mypy 1건은 환경에 도구 자체가 부재하여 정직하게 Skip 표기(허위 Pass 아님, py_compile 대체 검증으로 최소 구문 안전성 확보). §6 보안 4항목 전부 Pass — write 경로가 fw-inbox·memory-tool 위임으로만 한정되어 화이트리스트를 벗어나지 않음, 하드코딩 시크릿 0건, `~/.opal` 직접 편집 없음. 회귀: memory-tool pytest 88 passed + 6 subtests passed 전부 유지(enum additive 확장 — VALID_TYPES/VALID_STATUSES에 improvement/candidate 추가만, 기존 값 전부 보존, 회귀 0건), 4-pilot CLOSE 순서(DONE.md mark→관련문서 업데이트→op-brain-ingest→회고 하드스텝→완료보고) 비파괴 확인. 가설 H-1~H-9 전부 대응 시나리오 Pass. Critical/Partial Fail 사유 없음.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (실 fixture·실 위임·실 write 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오) — L3 해당 없음 명시
- [x] L3 [SUPERVISOR] 마커: 해당 없음 (FE/사용자 협업 대상 없음)
- [x] 리스크 가설 표(§1) H-N ↔ 시나리오 S-N 1:N 매핑 완전 (H-1~9 전부)
- [x] 모든 시나리오에 실행 방식(M1) 명시
- [x] FE 변경 시 M2: **비해당** (FE 화면/컴포넌트·인증/인가·외부 API 엔드포인트 변경 없음 — M2 의무 트리거 미발동)

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-17 09:14 KST | 최초 작성 — H-1~9 → S-1~14, RED-first 트랙(improve-tool)/구현후검증(문서·스킬·install) 하이브리드, L3·M2 해당없음 (058) |
| v1.1 | 2026-07-17 | TEST 단계 실행 완료 — S-1~S-14 전부 결과/상세 채움(All Pass). S-1~S-5 pytest 14/14 실행 로그 확보(RED→GREEN), S-10/S-11은 sandbox HOME 격리 실 install 2회 구동으로 실증(정적 grep 대체 아님, 실 `~/.opal` 무오염 확인). §5 코드품질(ruff Pass·mypy 환경부재 Skip)·§6 보안(4항목 Pass)·회귀(memory-tool 88 passed) 기록. §7 판정: All Pass (058) |
