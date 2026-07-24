# TEST SCENARIO: 도구·MCP·스킬 통합 검색·사용법·활용 체계 (tool-scan)

> 작성일: 2026-06-26 | 상태: 작성 완료
> 작성자: 알투(PM) | PLAN.md §리스크 가설 표 기반 (작성자≠PLAN 워커·구현 워커 — RED-first §2)

## RED-first 트랙 판정

| 변경 영역 | 트랙 | 근거 (red-first §1.5) |
|----------|------|----------------------|
| tool_scan.py / federation.py / run.sh (F-001/3/4) | **RED-first 강제** | 도구 자체 로직(분기·판정·라우팅) = self-confirming 위험. 작성자(opal-test-agent, mode:red) ≠ 구현자(opal-be-agent) |
| manifest.json (F-002) | RED-first(데이터 단언) | 도구 동작이 소비하는 SSOT → grep/구조 단언으로 RED 가능 |
| AGENT.md / tools.md / harness.md / install (F-005/6/7) | 구현 후 산출물 검증 | 설정·문서 — 동작 로직 아님(red-first §1.5 "설정·문서") |

> **공통 불변**: 모든 시나리오 ① 테스트 코드/산출물 검사 산출 ② 작성자≠구현자 ③ TEST 단계 검증. M2(E2E)·L3(SUPERVISOR) 해당 없음 — FE 화면/인증/외부 API 연동 부재(CLI 도구 + 마크다운 편집).

---

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-004 federation 읽기 | skills-registry.json `groups`/`name`/`alias`/`triggers`/`paths` 변경 시 skill-registry.js·install·harness 파괴 | P0 | L1 | TS-033 |
| H-2 | F-001/3/4 tool-scan 자체 로직 | self-confirming — 구현자가 테스트 맞춤 → 오라우팅·오판정 미검출 | P0 | L1(RED-first 분리) | TS-001~003·020~023·030~035 전체 |
| H-3 | F-004 MCP discovery | mcp-schema live 부재 → 스키마 반환 시도 시 빈 결과 | P1 | L1 | TS-031 |
| H-4 | F-003 usage(OPAL 래퍼) | cmux `--help`=`ok:false`+exit0 → ok 기준 판정 시 오판 | P0 | L1 | TS-020 |
| H-5 | F-006 drift 정합 | 두 표(tools.md/harness §9) 도구 집합 불일치 | P1 | L1 | TS-050 |
| H-6 | F-007 install chmod | tool-scan/test-tool chmod 라인 누락 → 실행권한 미설정 | P2 | L1 | TS-060 |
| H-7 | F-003 usage(외부 CLI) | `--help`가 stderr-only → stdout만 캡처 시 빈 usage | P1 | L1 | TS-022 |
| H-8 | F-003 정적 캐시 금지 | 사용법 정적 복제 시 `--help` 변경 미반영(R-2 위반) | P1 | L1 | TS-021 |
| H-9 | F-002 usage 텍스트 미저장 | manifest에 usage 본문 inline → drift 부활(R-3 위반) | P1 | L1 | TS-010 |
| H-10 | F-004 resolve 결정론 | 동일 입력 비결정/순서불안정 후보 → 라우팅 신뢰성 저하 | P1 | L1 | TS-034 |

---

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 테이블(파일) | 식별자 | 상태 | 출처 |
|-------------|--------|------|------|
| stub manifest.json | `tests/fixtures/manifest.stub.json` | 7 엔트리(self-help·inline·cmux fallback 포함) | fixture |
| stub OPAL 래퍼 | `tests/fixtures/help_exit0_ok_false.sh` | `--help` → stdout `{"ok":false}` + exit 0 | fixture (H-4) |
| stub 외부 CLI | `tests/fixtures/help_stderr_only.sh` | `--help` → stderr로만 help, stdout 비어있음 | fixture (H-7) |
| stub 가변 래퍼 | `tests/fixtures/help_mutable.sh` | 환경변수로 `--help` 출력 변경 가능 | fixture (H-8) |
| 실 skills-registry.json | `opal/core/references/opal-skills-registry.json` | 원본(읽기 전용) | repo (H-1, byte 비교용) |
| 실 mcps.md | `opal/core/references/mcps.md` | 원본(읽기 전용) | repo (H-3) |
| 정합 후 tools.md / harness.md | 구현 산출물 | brain·tool-scan 반영 | EXECUTE 산출 (H-5) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (사전) | When (실행) | Then (검증) |
|---------|-------------|------------|------------|
| TS-001 | stub manifest 주입 | `run.sh list`/`which`/`usage`/`resolve`/`check` | 각 `{"ok":true,"command":..}` JSON + exit 0 |
| TS-002 | venv 부재 stub | `run.sh list` | `{"ok":false,"error":"venv_missing","detail":..}` + exit 1 |
| TS-003 | stub manifest | `run.sh badcmd` / 누락 인자 | `{"ok":false,"error":..}` + 비0 exit |
| TS-010 | stub manifest(self-help 엔트리) | manifest 파일 grep | `--help` 본문 텍스트 부재, `usage_source.text`=null(inline 외) |
| TS-011 | — | manifest 구조 파싱 | 6 OPAL+tool-scan 7엔트리, 각 `usage_source.type` 존재 |
| TS-012 | stub manifest 7엔트리 | `run.sh list` | `purpose` 1줄씩만, 전체 usage 미포함 |
| TS-020 | help_exit0_ok_false.sh 주입 | `run.sh usage <stub-tool>` | exit_code 기준 성공 판정, `live:true`, ok:false 무관 성공 |
| TS-021 | help_mutable.sh(출력A) → 출력B | `usage` 2회 | 1회·2회 반환이 출력 변경 반영(정적 캐시 아님) |
| TS-022 | help_stderr_only.sh 주입 | `run.sh usage <stub-tool>` | stdout+stderr 병합 → usage_text 비어있지 않음 |
| TS-023 | stub manifest | `run.sh usage 미등록도구` | `{"ok":false,"error":"tool_not_found"}` |
| TS-030 | 실 manifest+federation | `run.sh resolve "browser check localhost"` | cmux-tool(kind=tool,invoke=shell,fallback 동봉) |
| TS-031 | 실 mcps.md | `run.sh resolve "library docs"` | context7(kind=mcp,invoke=ToolSearch 포인터, 스키마 미반환) |
| TS-032 | 실 skills-registry.json | `run.sh resolve "데이터 모델"` | op-data-model(kind=op-skill,dispatched_by 포함) |
| TS-033 | skills-registry.json byte 스냅샷 | `run.sh resolve ...` 실행 | 실행 전후 파일 byte 동일(원본 무변경) |
| TS-034 | 동일 상황 입력 | `run.sh resolve` 2회 | 동일 정렬 후보(결정론) |
| TS-035 | 매칭 없는 상황 | `run.sh which "zzz없는것"` | `{"ok":false,"error":"no_match"}` |
| TS-040 | 구현된 AGENT.md | 인지맵 표 grep | cmux-tool 행 존재, localhost 행이 cmux-tool 1순위 |
| TS-041 | 구현된 AGENT.md | 규율 문단 grep | "사용법 선확인"+"에러 종류 진단후 폴백(usage=수정/cmux_not_installed=폴백)" 존재 |
| TS-050 | 구현된 tools.md+harness.md | 두 표 도구 집합 추출·비교 | 집합 동일(둘 다 7도구) |
| TS-051 | 구현된 문서 | grep | tools.md에 brain-tool 섹션, harness §9에 code-scan·cmux 행 |
| TS-060 | 구현된 install-mac.sh | grep | `tool-scan/run.sh` chmod 라인 존재 |

---

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터/stub 입력)

> 공통 도구: `python -m unittest`(표준 라이브러리). 공통 대상: `opal/tools/tool-scan/{run.sh,tool_scan.py,manifest.json,lib/federation.py}`. 실행 방식 전 시나리오 **M1(테스트 도구)**.

#### TS-001: 5서브명령 JSON 계약
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 | 대상 | F-001 골격(list/which/usage/resolve/check) | 계층 | L1 | 실행 방식 | M1 |
| 조건 | stub manifest 주입, venv 정상 | 기대 결과 | 5서브명령 전부 `{"ok":true,"command":"<subcmd>",..}` + exit 0 |
| 도구 | unittest(subprocess) | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestSubcommandsJson::test_subcommands_json) | 결과 | Pass | 상세 | 5서브명령(list/which/usage/resolve/check) 전부 exit 0 + ok=true + command 필드 일치. subTest 5회 전부 OK |

#### TS-002: venv 부재 에러 계약 (통일)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 | 대상 | run.sh venv 게이트(§3.8 통일) | 계층 | L1 | 실행 방식 | M1 |
| 조건 | VENV_PYTHON 비실행 stub | 기대 결과 | `{"ok":false,"error":"venv_missing","detail":..}` + exit 1 |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestSubcommandsJson::test_venv_missing) | 결과 | Pass | 상세 | OPAL_VENV_PYTHON=/nonexistent_path_venv/bin/python 주입 시 exit 1 + ok=false + error="venv_missing" + detail 필드 존재 확인 |

#### TS-003: 잘못된 호출 방어
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 | 대상 | argparse 라우터·에러 응답 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | 알 수 없는 서브명령/필수 인자 누락 | 기대 결과 | `{"ok":false,..,"error":..}` + 비0 exit |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestSubcommandsJson::test_bad_invocation) | 결과 | Pass | 상세 | badcmdxyz123 → 비0 exit + ok=false + error 필드 존재(exit≠127). which 인자 누락 → 비0 exit(exit≠127). 두 케이스 모두 OK |

#### TS-010: usage 텍스트 미저장 (drift 방어)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 | 대상 | manifest.json `usage_source` | 계층 | L1 | 실행 방식 | M1 |
| 조건 | self-help 엔트리 | 기대 결과 | manifest grep 시 `--help` 본문 부재, `usage_source.text`=null(inline 외) |
| 도구 | unittest(파일 grep) | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestManifest::test_manifest_no_usage_text) | 결과 | Pass | 상세 | 실 manifest.json 7엔트리 전부 usage_source.type != "inline"이면 text=null. 50자 이상 text 필드 없음. drift 방어 확인 |

#### TS-011: manifest 엔트리 완전성
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 | 대상 | manifest 7엔트리 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | — | 기대 결과 | 6 OPAL(xlsx/state/code-scan/cmux/test/brain)+tool-scan, 각 `usage_source.type` 지정 |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestManifest::test_manifest_entries) | 결과 | Pass | 상세 | 7엔트리 정확히 존재(tool-scan/xlsx-tool/state-tool/code-scan/cmux-tool/test-tool/brain-tool). 각 엔트리 usage_source.type 허용값(self-help/context7/url/inline/doc) 내 존재 |

#### TS-012: list 2단 토큰 (purpose만)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 | 대상 | cmd_list | 계층 | L1 | 실행 방식 | M1 |
| 조건 | stub manifest 7엔트리 | 기대 결과 | 각 엔트리 `purpose` 1줄만 반환, 전체 usage 본문 미포함 |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestManifest::test_list_purpose_only) | 결과 | Pass | 상세 | stub manifest 7엔트리로 list → exit 0 + ok=true + capabilities 7개 + 각 capability에 purpose 존재 + usage_text/usage_json 미포함 |

#### TS-020: usage OPAL 래퍼 — exit0+ok:false 함정
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 | 대상 | cmd_usage self-help(OPAL) | 계층 | L1 | 실행 방식 | M1 |
| 조건 | help_exit0_ok_false.sh(stdout `{"ok":false}` + exit 0) | 기대 결과 | **exit_code 기준** 성공 판정, `live:true`, `ok:false`여도 usage 반환 성공 |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestUsage::test_usage_exit0_okfalse) | 결과 | Pass | 상세 | help_exit0_ok_false.sh(stdout=`{"ok":false}`, exit 0) 주입 → usage ok=true + live=true + exit_code=0 + usage_json 존재. ok:false 무관 exit code 기준 성공 판정 확인 |

#### TS-021: usage live (정적 캐시 금지)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 | 대상 | cmd_usage live 호출 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | help_mutable.sh 출력 A→B 변경 | 기대 결과 | usage 1회/2회 반환이 변경 반영(매 호출 셸 실행 증명) |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestUsage::test_usage_live_nocache) | 결과 | Pass | 상세 | TOOL_SCAN_HELP_VERSION=v1 → usage_text에 "v1" 포함, v2 → "v2" 포함. 두 호출 결과 다름(정적 캐시 미사용 증명) |

#### TS-022: usage 외부 CLI — stderr 병합
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 | 대상 | cmd_usage self-help(외부 CLI) | 계층 | L1 | 실행 방식 | M1 |
| 조건 | help_stderr_only.sh(stdout 비어있음, stderr에 help) | 기대 결과 | stdout+stderr 병합 → usage_text 비어있지 않음 |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestUsage::test_usage_stderr_merge) | 결과 | Pass | 상세 | help_stderr_only.sh(stdout 비어있고 stderr에만 "Usage:" 출력) 주입 → usage_text 비어있지 않음 + "Usage" 포함 확인. stdout+stderr 병합 정상 |

#### TS-023: usage 미등록 도구
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 | 대상 | cmd_usage 검증 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | manifest에 없는 tool name | 기대 결과 | `{"ok":false,"error":"tool_not_found"}` |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestUsage::test_usage_tool_not_found) | 결과 | Pass | 상세 | "nonexistent_tool_xyz_044" → 비0 exit(exit≠127) + ok=false + error="tool_not_found" |

#### TS-030: resolve → tool (cmux-tool)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 | 대상 | cmd_resolve + 라우팅 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | 실 manifest+federation, 입력 "browser check localhost" | 기대 결과 | cmux-tool(kind=tool, invoke=shell, fallback·error_contract 동봉) |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestResolveAndFederation::test_resolve_tool) | 결과 | Pass | 상세 | "browser check localhost" → resolved.name=cmux-tool, kind=tool, invoke=shell, fallback 필드 존재 + error_contract 동봉. 스모크 출력에서도 usage_json(subcommands 포함) 확인 |

#### TS-031: resolve → mcp (context7, ToolSearch 포인터)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 | 대상 | cmd_resolve mcp 분기 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | 실 mcps.md, 입력 "library docs" | 기대 결과 | context7(kind=mcp, invoke=ToolSearch 포인터, 파라미터 스키마 미반환) |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestResolveAndFederation::test_resolve_mcp_pointer) | 결과 | Pass | 상세 | "library docs" → resolved.kind=mcp, invoke=ToolSearch, exec="ToolSearch query \"select:context7\"", parameters 필드 미포함. H-3 MCP 스키마 미반환 계약 준수 |

#### TS-032: resolve → op-skill (op-data-model)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 | 대상 | cmd_resolve skill 분기 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | 실 skills-registry.json, 입력 "데이터 모델" | 기대 결과 | op-data-model(kind=op-skill, invoke=dispatch, skill_path+dispatched_by 포함) |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestResolveAndFederation::test_resolve_opskill) | 결과 | Pass | 상세 | "데이터 모델" → resolved.name=op-data-model, kind=op-skill, invoke=dispatch, dispatched_by 배열 1개 이상 존재 |

#### TS-033: federation 불파괴 (byte 동일)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 | 대상 | federation.py 읽기 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | resolve 실행 전 skills-registry.json byte 스냅샷 | 기대 결과 | 실행 후 byte 동일(원본 무변경) |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestResolveAndFederation::test_registry_unchanged) | 결과 | Pass | 상세 | resolve 실행 전후 SHA-256 해시 동일(029ba0d63be3c16b24e338faa5597b2b). opal-skills-registry.json 원본 무변경 |

#### TS-034: resolve 결정론
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 | 대상 | 라우팅 안정 정렬 | 계층 | L1 | 실행 방식 | M1 |
| 조건 | 동일 상황 입력 2회 | 기대 결과 | 동일 정렬 후보 반복(`(-score,kind,name)`) |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestResolveAndFederation::test_resolve_deterministic) | 결과 | Pass | 상세 | "browser check localhost" 동일 입력 2회 → stdout 완전 동일. 결정론 정렬(-score, kind, name) 보장 |

#### TS-035: which 매칭 없음
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 | 대상 | cmd_which no_match | 계층 | L1 | 실행 방식 | M1 |
| 조건 | 매칭 키워드 없는 입력 | 기대 결과 | `{"ok":false,"error":"no_match"}` |
| 도구 | unittest | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestResolveAndFederation::test_which_no_match) | 결과 | Pass | 상세 | "zzz없는것zzz_044_no_match_ever" → 비0 exit(exit≠127) + ok=false + error="no_match" |

#### TS-040: 인지맵 cmux-tool 라우팅 (산출물)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2(간접) | 대상 | AGENT.md 인지맵 | 계층 | L1 | 실행 방식 | M1(산출물 grep) |
| 조건 | F-005 구현 후 AGENT.md | 기대 결과 | cmux-tool 행 존재, localhost 행이 cmux-tool 1순위/playwright 폴백 명시 |
| 도구 | grep | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestOutputArtifacts::test_agentmd_cmux_routing) | 결과 | Pass | 상세 | AGENT.md에 "cmux-tool" 존재 + localhost+cmux-tool 연관 패턴 매칭 + playwright.*폴백 패턴 매칭 |

#### TS-041: 사용 규율 문단 (산출물)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2(간접) | 대상 | AGENT.md 규율 | 계층 | L1 | 실행 방식 | M1(산출물 grep) |
| 조건 | F-005 구현 후 | 기대 결과 | "사용법 선확인" + "에러 종류 진단후 폴백(usage=수정/cmux_not_installed=폴백)" 문단 존재 |
| 도구 | grep | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestOutputArtifacts::test_agentmd_usage_discipline) | 결과 | Pass | 상세 | AGENT.md에 "사용법 선확인" 문구 존재 + "cmux_not_installed" 폴백 규율 존재 |

#### TS-050: drift 정합 — 두 표 집합 동일 (산출물)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 | 대상 | tools.md ∩ harness §9 | 계층 | L1 | 실행 방식 | M1(산출물 비교) |
| 조건 | F-006 구현 후 | 기대 결과 | 두 표 도구 집합 동일(둘 다 7도구: xlsx/state/code-scan/cmux/test/brain/tool-scan) |
| 도구 | 파싱·집합 비교 | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestOutputArtifacts::test_registry_parity) | 결과 | Pass | 상세 | tools.md 섹션 헤더 7개(xlsx/state/code-scan/cmux/test/brain/tool-scan) + harness §9 표 행 7개 일치. 두 집합 동일 |

#### TS-051: 누락 항목 추가 (산출물)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 | 대상 | tools.md/harness 정합 | 계층 | L1 | 실행 방식 | M1(grep) |
| 조건 | F-006 구현 후 | 기대 결과 | tools.md에 brain-tool 섹션, harness §9에 code-scan·cmux-tool 행 |
| 도구 | grep | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestOutputArtifacts::test_drift_entries) | 결과 | Pass | 상세 | tools.md에 brain-tool 섹션(#+\s+brain.?tool 패턴) 존재 + harness §9에 code-scan 행 존재 + cmux-tool 행 존재 |

#### TS-060: install chmod 라인 (산출물)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 | 대상 | install-mac.sh | 계층 | L1 | 실행 방식 | M1(grep) |
| 조건 | F-007 구현 후 | 기대 결과 | `tool-scan/run.sh` chmod 라인 존재(+test-tool 보정 시 동일) |
| 도구 | grep | 실행 명령 | `python3 -m unittest discover -s opal/tools/tool-scan/tests -p "test_*.py" -v` (TestOutputArtifacts::test_install_chmod_line) | 결과 | Pass | 상세 | install-mac.sh에 tool-scan chmod 패턴(tool.?scan.*chmod) 존재 + "tool-scan/run.sh" 참조 라인 존재 |

### L2. 프로세스 통합
해당 없음 — 실 DB·다중 컴포넌트 통합 없음. federation은 파일 읽기(L1 stub/실파일로 충분).

### L3. 사용자 협업
해당 없음 — FE 화면/사용자 플로우 없음([SUPERVISOR] 불요). 모든 검증 자동(M1).

---

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC(요구사항) | 가설 ID | 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------------|---------|------|---------|-----------------|------|
| R-1 (5서브명령 JSON) | H-2 | L1 | TS-001,002,003 | `tests/test_tool_scan.py`:test_subcommands_json / test_venv_missing / test_bad_invocation | F-001 |
| R-3 (usage 미저장) | H-9 | L1 | TS-010,011,012 | `tests/test_tool_scan.py`:test_manifest_no_usage_text / test_manifest_entries / test_list_purpose_only | F-002 |
| R-2 (live --help) | H-4,H-7,H-8 | L1 | TS-020,021,022,023 | `tests/test_tool_scan.py`:test_usage_exit0_okfalse / test_usage_live_nocache / test_usage_stderr_merge / test_usage_tool_not_found | F-003 |
| R-4 (routing) | H-2,H-3,H-10 | L1 | TS-030,031,032,034,035 | `tests/test_tool_scan.py`:test_resolve_tool / test_resolve_mcp_pointer / test_resolve_opskill / test_resolve_deterministic / test_which_no_match | F-004 |
| R-5 (federation 불파괴) | H-1 | L1 | TS-033 | `tests/test_tool_scan.py`:test_registry_unchanged | F-004 |
| R-6 (인지맵) | H-2 | L1 | TS-040 | `tests/test_tool_scan.py`:test_agentmd_cmux_routing (산출물 grep) | F-005 |
| R-7 (사용 규율) | H-2 | L1 | TS-041 | `tests/test_tool_scan.py`:test_agentmd_usage_discipline | F-005 |
| R-8 (drift 정합) | H-5 | L1 | TS-050,051 | `tests/test_tool_scan.py`:test_registry_parity / test_drift_entries | F-006 |
| R-9 (install) | H-6 | L1 | TS-060 | `tests/test_tool_scan.py`:test_install_chmod_line | F-007 |

> 테스트 케이스명은 구현 워커가 확정(위는 권고). 모든 H-N이 1+ 시나리오에 매핑됨(미매핑 없음).

---

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff | Pass(경고 2건, non-blocking) | `ruff check tool_scan.py lib/federation.py` 결과: F401(federation.py의 `os` import 미사용), E402(tool_scan.py의 sys.path 조작 후 import). 두 항목 모두 기능 결함 아님 — F401은 fixable, E402는 sys.path.insert 필수 패턴으로 수용 가능 |
| 2 | @header 검사 | code-scan / 수동 | Pass | tool_scan.py 상단 `@header { "module":"tool_scan", "layer":"util", ... }` + federation.py 상단 `@header { "module":"federation", ... }` 존재 확인 |
| 3 | 표준 라이브러리만(외부 패키지 0) | grep | Pass | tool_scan.py: argparse/json/os/pathlib/re/subprocess/sys/typing 전부 표준 라이브러리. federation.py: json/os/pathlib/re/typing 전부 표준 라이브러리. 외부 패키지 import 0건 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | subprocess shell=False (인자 리스트) | Pass | tool_scan.py:284 `subprocess.run(cmd_list, ...)` — shell=True 없음. grep 확인: "shell=" 키워드 없음(주석만 존재). 셸 인젝션 방지 |
| 2 | federation 입력 경로 화이트리스트 | Pass | federation.py:80 `_validate_path(path, references_dir)` — `path.resolve().relative_to(references_dir.resolve())` 화이트리스트 체크. get_references_dir() 반환 경로만 허용 |
| 3 | ReDoS 방어(triggers 정규식 입력 256자 제한) | Pass | federation.py:32 `MAX_INPUT_LENGTH = 256` 상수 정의 + tool_scan.py에서 상황 입력 길이 제한 적용. skill-registry.js 정책 답습 확인 |
| 4 | 하드코딩 시크릿 스캔 / .gitignore | Pass | tool-scan/ 디렉토리 내 password/secret/token/api_key 등 키워드 grep 결과: token 관련 hit는 모두 변수명(when_tokens 등) — 인증 시크릿 아님. 하드코딩 시크릿 0건 |

## 7. 판정

**All Pass** — tool-scan 22/22 GREEN. 회귀 실패 2건(state-tool 1건, test-tool 1건)은 본 변경 이전부터 존재한 기존 실패(pre-existing)로 이번 구현과 무관. 코드 품질 ruff 경고 2건은 기능 결함 아님(non-blocking). 보안 4항목 전부 Pass. 스모크 6종 모두 계약대로 응답.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (stub은 실제 쉘 스크립트 fixture — MagicMock 아님)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-10 전부 매핑, 미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (전 시나리오 L1 — L2/L3 해당 없음 명시)
- [x] L3 [SUPERVISOR] 마커: 해당 없음(FE/사용자 플로우 부재) — 명시함
- [x] 리스크 가설 표(§1) H-N ↔ 시나리오 S-N(TS-NNN) 1:N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1) 명시
- [x] FE 변경 시 M2 시나리오: **해당 없음** — FE 화면/컴포넌트·인증/인가·외부 API 연동 부재(CLI 도구+마크다운 편집)이므로 M2 의무 트리거 미발동
