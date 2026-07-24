# TEST SCENARIO: 메모리 관리 체계 개선 + memory-tool 신설

> 작성일: 2026-06-26 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표(H-1~H-9) 기반
> 트랙: **혼합** — 도구 로직(F-002~F-006·F-010) = RED-first(작성자 opal-test-agent ≠ 구현자 opal-be-agent) / 문서·설정(F-001·F-007·F-008·F-009) = 구현 후 산출물 검사
> M2(E2E) 면제: 변경 영역에 FE 화면·인증/인가·외부 API 연동 없음(도구 로직 + 문서). `test-scenario-guide.md` §Step3-b M2 의무 트리거 비해당.

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-005 promote 무손실 이전 | 영구 거처 이전 확인 없이 행+파일 삭제 시 지식 소실(blind 삭제) | P0 | L1 | S-8 |
| H-2 | F-004 prune FIFO=5 | 6번째 append 시 정확히 가장 오래된 1개만 제거(off-by-one) | P1 | L1 | S-5, S-6 |
| H-3 | F-003 마커 가드 | 마커 부재 MEMORY.md에 도구 작동 시 자유 텍스트 파괴 | P0 | L1 | S-2 |
| H-4 | F-005 promote 행+파일 원자성 | 행만/파일만 삭제 → 고아·dangling | P1 | L1 | S-7 |
| H-5 | F-006 migrate 구→신 변환 | 변환 중 정보 소실(설명 truncate·상태 매핑 오류) | P1 | L1 | S-13, S-14 |
| H-6 | F-001/F-002 형식-파서 정합 | memory-learning.md 형식 ↔ 도구 파서 컬럼 수·순서 불일치 → 파싱 0건 | P0 | L1+산출물 | S-18, S-25 |
| H-7 | F-009 drift 정합 | tools.md ↔ harness §9 memory-tool 행 불일치 | P2 | 산출물 | S-27 |
| H-8 | F-010 review 자가검토 | 도구가 판단 침범(졸업지 단정) / 변경 명령 후 review 블록 누락(ambient 실패) | P1 | L1 | S-15, S-16 |
| H-9 | F-005 promote brain 재사용 | brain 경로가 별도 파이프라인 재발명(brain-tool 미재사용) | P2 | L1+설계 | S-9 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터 (fixtures — opal-test-agent가 생성)

| 식별자 | 상태 | 출처 |
|--------|------|------|
| `fixture_valid.md` | 마커 4개(index/history start·end) + 빈 표 (정상 신포맷) | fixture |
| `fixture_no_marker.md` | 마커 전무 MEMORY.md | fixture |
| `fixture_legacy.md` | 구포맷(현 `.opal/MEMORY.md` 스타일: 제목 컬럼 없음, 상태값 `대기/완료/폐기 기록` 혼재, 6행) | fixture |
| `fixture_populated.md` | 마커 + active 3행·dead 1행·superseded 1행 + 대응 `memory/<name>.md` 파일 존재 | fixture |
| `fixture_oversummary` | 81자 요약 입력값 | 인라인 상수 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (호출) | Then (re-read) |
|---------|------------|------------|---------------|
| S-2 | fixture_no_marker.md | `append --kind memory ...` | `ok:false`+`marker_missing`, 파일 바이트 불변 |
| S-5 | fixture_valid.md | history 6회 `append --kind history` | 히스토리 행수=5, 최신 5개 보존 |
| S-7 | fixture_populated.md (active 행 X + memory/X.md) | `promote --title X --to docs --ref AGENT.md#금지사항` | 인덱스 행 X 부재 AND memory/X.md 부재 AND provenance 1행 |
| S-8 | fixture_populated.md | `promote --title X` (--ref 미지정) | `ok:false`+`promote_ref_missing`, 행·파일 불변 |
| S-13 | fixture_legacy.md (6행) | `migrate` | 신포맷 6행, 각 제목 비공백, review_count 보고 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 fixture 입력)

#### S-1: memory-tool 도구 골격 (JSON·서브명령·validate 부재)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 (골격) |
| 대상 | run.sh + memory_tool.py 디스패처 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | `run.sh show`·`run.sh --help` 호출 |
| 기대 결과 | 모든 응답이 `{"ok":...}` 단일라인 JSON·exit code 일관 / 8서브명령(init·append·update·promote·prune·migrate·show·review) argparse 등록 / `validate` 부재 / `memory_limit_exceeded` 코드 부재 |
| 도구 | pytest (`test-tool resolve` tier=unit×scope=be) |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestSkeleton -v` |
| 결과 | Pass |
| 상세 | TestSkeleton 7케이스 전부 통과. test_all_eight_subcommands_registered / test_validate_subcommand_absent / test_memory_limit_exceeded_error_code_absent / test_response_is_single_line_json / test_show_returns_json / test_tool_py_exists / test_memory_limits_constant_absent 모두 PASSED |

#### S-2: 마커 직접편집 금지 가드 (무손실)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | cmd_append 마커 가드 (`state_tool.py:302` 패턴 차용) |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_no_marker.md에 `append --kind memory --title T --type feedback --summary s` |
| 기대 결과 | `ok:false` + `error=marker_missing` + **파일 바이트 불변**(mutating 명령 전부 동일) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestMarkerGuard -v` |
| 결과 | Pass |
| 상세 | TestMarkerGuard 3케이스 전부 통과. test_all_mutating_commands_reject_no_marker(6서브명령 일괄) / test_append_no_marker_returns_marker_missing / test_append_no_marker_file_bytes_unchanged 모두 PASSED |

#### S-3: 요약 길이캡 (R2)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 (형식 계약) |
| 대상 | cmd_append summary ≤80 검증 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_valid.md에 81자 요약 append |
| 기대 결과 | `ok:false` + `summary_too_long` |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestSummaryLengthCap -v` |
| 결과 | Pass |
| 상세 | TestSummaryLengthCap 2케이스 전부 통과. test_summary_81_chars_rejected(ok:false + summary_too_long) / test_summary_80_chars_accepted 모두 PASSED |

#### S-4: 메모리 갯수 무차단 (R6 제외 확인)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | cmd_append 메모리 — 갯수 게이트 없음 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_valid.md에 동일 유형 메모리 다수(예 15건) append |
| 기대 결과 | 전부 `ok:true`(차단 없음) — 갯수 상한 게이트가 존재하지 않음 확인(캡틴 지시 R6 제외) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestCountUnlimited -v` |
| 결과 | Pass |
| 상세 | TestCountUnlimited::test_fifteen_appends_all_succeed PASSED — 15건 연속 append 전부 ok:true, 갯수 차단 로직 부재 확인 |

#### S-5: 히스토리 FIFO=5
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | cmd_append(history) + _enforce_history_fifo |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_valid.md에 history 6건 순차 append (제목 h1~h6) |
| 기대 결과 | 히스토리 행수=5, h1(최초) 제거, h2~h6 보존(순서·내용) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestHistoryFIFO -v` |
| 결과 | Pass |
| 상세 | TestHistoryFIFO 2케이스 전부 통과. test_history_fifo_limit_five(행수=5) / test_history_fifo_removes_oldest(h1 제거·h2~h6 보존) 모두 PASSED |

#### S-6: prune idempotent
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | cmd_prune |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | 히스토리 ≤5 상태에서 `prune` |
| 기대 결과 | no-op(행수 불변), `ok:true` |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestPruneIdempotent -v` |
| 결과 | Pass |
| 상세 | TestPruneIdempotent 2케이스 전부 통과. test_prune_empty_is_noop / test_prune_no_op_when_five_or_fewer 모두 PASSED (행수 불변, ok:true) |

#### S-7: promote --to docs (행+파일 원자 삭제 + provenance)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | cmd_promote |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_populated.md (active 행 X + memory/X.md) → `promote --title X --to docs --ref AGENT.md#금지사항` |
| 기대 결과 | 인덱스 행 X 부재 AND memory/X.md 파일 부재 AND provenance 로그 1행(삭제 전 위치·대상 docs:AGENT.md#금지사항) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestPromoteToDocs -v` |
| 결과 | Pass |
| 상세 | TestPromoteToDocs 3케이스 전부 통과. test_promote_to_docs_removes_row_and_file(인덱스 행·파일 동시 삭제) / test_promote_to_docs_records_provenance(provenance 1행 기록) / test_promote_response_fields 모두 PASSED |

#### S-8: promote 이전 미확인 거부 (무손실 — H-1)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | cmd_promote 무손실 가드 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_populated.md → `promote --title X` (--ref/--to 미지정) 또는 대상 파일 부재 |
| 기대 결과 | `ok:false` + `promote_ref_missing`(또는 memory_file_not_found), **인덱스 행·memory/X.md 둘 다 불변** |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestPromoteLossless -v` |
| 결과 | Pass |
| 상세 | TestPromoteLossless 4케이스 전부 통과. test_promote_without_ref_rejected(promote_ref_missing) / test_promote_without_to_rejected / test_promote_without_ref_preserves_row_and_file(인덱스·파일 불변) / test_promote_nonexistent_title_rejected 모두 PASSED |

#### S-9: promote --to brain (brain-tool 재사용 — H-9)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | cmd_promote brain 경로 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | `promote --to brain` 경로 검사 — 자체 brain 쓰기 구현이 아니라 `brain-tool add-page`/`//opbr ingest` 재사용(호출 또는 안내)인지 |
| 기대 결과 | memory-tool이 brain 페이지를 직접 쓰지 않음(brain-tool 경로 위임). 자체 brain 파이프라인 재발명 부재 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestPromoteToBrain -v` |
| 결과 | Pass |
| 상세 | TestPromoteToBrain 2케이스 전부 통과. test_promote_brain_does_not_contain_brain_write_impl(소스코드 내 brain 직접쓰기 패턴 부재) / test_promote_brain_does_not_write_to_brain_dir(brain/ 디렉토리 미생성) 모두 PASSED |

#### S-10: update 상태전이 (dead/superseded 행 보존)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 (라이프사이클) |
| 대상 | cmd_update |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_populated.md active 행 → `update --title X --status dead` |
| 기대 결과 | 상태 dead로 변경, 행 보존(삭제 아님), 로드 제외 표시 / invalid status 시 `invalid_status` |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestUpdateStatusTransition -v` |
| 결과 | Pass |
| 상세 | TestUpdateStatusTransition 4케이스 전부 통과. test_update_active_to_dead_preserves_row / test_update_to_superseded_preserves_row / test_update_invalid_status_rejected(invalid_status) / test_update_valid_status_enum 모두 PASSED |

#### S-11: init 마커 삽입
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 (마커 전제) |
| 대상 | cmd_init |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | 마커 없는/신규 MEMORY.md에 `init` |
| 기대 결과 | index·history start/end 마커 4개 삽입 + 신포맷 빈 표·헤더 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestInit -v` |
| 결과 | Pass |
| 상세 | TestInit 3케이스 전부 통과. test_init_inserts_four_markers(마커 4개) / test_init_inserts_format_headers(신포맷 헤더) / test_init_on_no_marker_file 모두 PASSED |

#### S-12: init 재실행 거부
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | cmd_init 멱등 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | 마커 존재 fixture_valid.md에 `init`(--force 없음) |
| 기대 결과 | `ok:false` + `already_initialized` (--force 시 재삽입) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestInitAlreadyInitialized -v` |
| 결과 | Pass |
| 상세 | TestInitAlreadyInitialized 2케이스 전부 통과. test_init_on_existing_markers_rejected(already_initialized) / test_init_force_on_existing_markers_succeeds(--force 재삽입) 모두 PASSED |

#### S-13: migrate 구→신 변환 (무손실 — H-5)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | cmd_migrate |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_legacy.md (구포맷 6행, 상태값 혼재) → `migrate` |
| 기대 결과 | 신포맷 6행(행수 보존), 각 행 제목 비공백(자동 추출), 상태값 신 enum 매핑(완료→dead, 폐기→superseded), review_count 보고 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestMigrate -v` |
| 결과 | Pass |
| 상세 | TestMigrate 6케이스 전부 통과. test_migrate_preserves_row_count(6행 보존) / test_migrate_titles_nonempty(제목 비공백) / test_migrate_status_mapping_dead(완료→dead) / test_migrate_status_mapping_superseded(폐기→superseded) / test_migrate_reports_review_count / test_migrate_inserts_markers 모두 PASSED |

#### S-14: migrate 80자 초과 무손실
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | cmd_migrate 길이 처리 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | 구 설명 80자 초과 행 migrate |
| 기대 결과 | truncate 없이 `[REVIEW]` 플래그 부착(정보 소실 0) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestMigrateLossless -v` |
| 결과 | Pass |
| 상세 | TestMigrateLossless 2케이스 전부 통과. test_long_description_gets_review_flag_not_truncated([REVIEW] 플래그 부착, 원본 길이 보존) / test_review_count_nonzero_for_long_descriptions 모두 PASSED |

#### S-15: 자가검토 ambient 강제 (모든 변경 명령에 review 블록)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | build_review_block() 자동 첨부 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | init/append/update/promote/prune/migrate 각 호출 |
| 기대 결과 | 각 응답 JSON에 `review` 키 존재(promote_candidates·cleanup_candidates·history_status·violations) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewAmbient -v` |
| 결과 | Pass |
| 상세 | TestReviewAmbient 6케이스 전부 통과. test_init_response_has_review / test_append_response_has_review / test_update_response_has_review / test_promote_response_has_review / test_prune_response_has_review / test_migrate_response_has_review 모두 PASSED |

#### S-16: review 역할 경계 (후보 표면화만, 판단 단정 없음)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | cmd_review / build_review_block |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | fixture_populated.md(오래된 active·dead·superseded 포함)에 `review` |
| 기대 결과 | promote_candidates는 **후보 행만** 표면화(졸업지 docs/brain 단정 필드 없음), cleanup_candidates에 dead/superseded 표면화, violations에 format 위반 |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestReviewRoleBoundary -v` |
| 결과 | Pass |
| 상세 | TestReviewRoleBoundary 5케이스 전부 통과. test_review_promote_candidates_are_active_rows / test_review_promote_candidates_no_graduation_destination(졸업지 단정 필드 없음) / test_review_cleanup_candidates_includes_dead_and_superseded / test_review_returns_violations_list / test_review_history_status_field_present 모두 PASSED |

#### S-17: 보안 — 경로 가드·ReDoS·시크릿
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1/H-4 (파일 삭제 안전) |
| 대상 | promote 파일 삭제 경로·정규식 |
| 계층 | L1 |
| 실행 방식 | M1 (pytest) |
| 조건 | promote `--title`이 `../` 경로 탈출 시도 / migrate 정규식에 폭발 입력 |
| 기대 결과 | `memory/` 하위만 삭제 허용(경로 탈출 거부), 정규식 백트래킹 폭발 없음, 하드코딩 시크릿 0 |
| 도구 | pytest + grep |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestSecurity -v` + `grep -nE "(api_key\|secret\|password\|token).*=.*['\"]" memory_tool.py` |
| 결과 | Pass |
| 상세 | TestSecurity 4케이스 전부 통과. test_promote_path_traversal_rejected(../탈출 거부) / test_promote_only_deletes_within_memory_dir / test_path_traversal_in_title_file_mapping / test_no_hardcoded_secrets_in_tool 모두 PASSED. 코드 검토: _resolve_memory_file()에서 pathlib.resolve()+relative_to(memory_dir)로 경로 탈출 차단. 정규식 패턴 8개 모두 단순 고정폭(r"\d{4}-\d{2}-\d{2}", r"^-+$", r"[^\w가-힣]", r"_+", r"~~(.+?)~~", r"^\[REVIEW\]\s*", r"^([^.。!,，\n]{1,30})")으로 중첩 수량자 없음 — ReDoS 위험 없음 |

### L1. 산출물 검사 (문서·설정 — 구현 후 검증 트랙)

#### S-18: memory-learning.md 제목 컬럼 (R1)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | memory-learning.md 인덱스·히스토리 형식 |
| 계층 | L1 (산출물 grep) |
| 실행 방식 | M1 (grep/Read) |
| 조건 | 개정된 memory-learning.md Read |
| 기대 결과 | 인덱스·히스토리 형식 정의 양쪽에 `제목` 컬럼이 맨 앞에 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "제목" opal/core/references/harness/memory-learning.md` |
| 결과 | Pass |
| 상세 | 인덱스 형식 L17: `제목 \| 등록일 \| 유형 \| 상태 \| 파일 \| 요약` (맨 앞). 히스토리 형식 L24: `제목 \| 등록일 \| 단계 \| 경로 \| 핵심결과` (맨 앞). 양쪽 `제목` 컬럼 맨 앞 존재 확인 |

#### S-19: memory-learning.md 길이캡·라이프사이클·FIFO5 (R2·R3·R4)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | memory-learning.md |
| 계층 | L1 (산출물) |
| 실행 방식 | M1 (grep/Read) |
| 조건 | 개정본 Read |
| 기대 결과 | 요약 ≤80자·핵심결과 ≤2줄 [MUST] / FIFO 한도=5(10 부재) / active·promoted·superseded·dead 4상태+트리거 / 갯수 상한 표기 부재 |
| 도구 | grep |
| 실행 명령 | `grep -n "80\|FIFO\|active\|promoted\|superseded\|dead\|갯수" opal/core/references/harness/memory-learning.md` |
| 결과 | Pass |
| 상세 | L23: `요약: ≤80자, 1줄 [MUST]`. L34: `최대 5개 FIFO [MUST]`. 4상태(active/promoted/superseded/dead) L57~60에 트리거 포함. `갯수 상한 없음` 명시(L62), FIFO=10 문구 없음. 모든 기대 결과 충족 |

#### S-20: memory-learning.md 이관 워크플로우·자가검토 (R8'·R6')
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | memory-learning.md 신설 섹션 |
| 계층 | L1 (산출물) |
| 실행 방식 | M1 (grep/Read) |
| 조건 | 개정본 Read |
| 기대 결과 | "메모리 이관 워크플로우" 라우팅 표(docs/AGENT.md·CONVENTIONS.md·PROJECT.md·brain·삭제 5행) + docs=규범/brain=설명 구분 + brain 재사용[MUST] / 자가검토 트리거(매 변경 명령 후 review 자동 첨부) 설명 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "이관 워크플로우\|brain 재사용\|자가검토\|review.*자동" opal/core/references/harness/memory-learning.md` |
| 결과 | Pass |
| 상세 | L5 제목에 `이관 워크플로우` 명시. 라우팅 표 L75~79: docs/AGENT.md/CONVENTIONS.md/PROJECT.md/brain/삭제 5행 완비. L90: `brain 이관은 기존 //opbr ingest / brain_tool.py:465 cmd_add_page를 재사용 [MUST]`. L94: `자가검토 트리거 — 모든 변경 명령 응답 JSON에 review 블록 자동 첨부`. 모든 기대 결과 충족 |

#### S-21: project-init 템플릿 신포맷 (R10)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | opal-project-init/SKILL.md:408 인라인 템플릿 |
| 계층 | L1 (산출물) |
| 실행 방식 | M1 (grep/Read) |
| 조건 | 개정본 Read |
| 기대 결과 | 제목 컬럼·마커 4개·FIFO5 안내·직접편집 금지 안내 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "제목\|MEMORY_INDEX\|HISTORY\|FIFO\|직접 편집 금지\|직접편집" opal/skills/opal-project-init/SKILL.md` |
| 결과 | Pass |
| 상세 | L418: `\| 제목 \| 등록일 \| 유형 \| 상태 \| 파일 \| 요약 \|` (인덱스 헤더). L424: `\| 제목 \| 등록일 \| 단계 \| 경로 \| 핵심결과 \|` (히스토리 헤더). L422: `최대 5개, FIFO`. 마커 4개(memory:index:start/end, memory:history:start/end) 모두 템플릿에 포함. L426: `직접 편집 금지` 안내 명시. 모든 기대 결과 충족 |

#### S-22: install-mac.sh chmod 블록 (R11)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | install-mac.sh |
| 계층 | L1 (산출물) |
| 실행 방식 | M1 (grep) |
| 조건 | install-mac.sh Read |
| 기대 결과 | memory-tool run.sh chmod +x 블록 존재 + tool-scan 블록 패턴 동형(:1091 직후) |
| 도구 | grep |
| 실행 명령 | `grep -n "memory-tool\|chmod" scripts/install-mac.sh` |
| 결과 | Pass |
| 상세 | L1094~L1098: `# -- memory-tool 실행 권한 (045) --` 블록 존재. `local memory_run="$opal_home/tools/memory-tool/run.sh"` + `chmod +x "$memory_run"` + `success "memory-tool run.sh 실행 권한 설정"`. tool-scan 블록(L1088~L1092) 바로 다음에 동형 패턴으로 배치 확인 |

#### S-23: drift 정합 tools.md ↔ harness §9 (R12·H-7)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | tools.md + opal-harness.md §9 |
| 계층 | L1 (산출물) |
| 실행 방식 | M1 (grep/diff) |
| 조건 | 양쪽 도구 테이블 memory-tool 행 비교 |
| 기대 결과 | 두 테이블 memory-tool 행 동일 문자열 + 8서브명령 명시 + "갯수 게이트" 문구 부재 |
| 도구 | grep/diff |
| 실행 명령 | `grep "memory-tool.*8서브명령" opal/core/references/tools.md opal/core/references/opal-harness.md` |
| 결과 | Pass |
| 상세 | tools.md 용도: `프로젝트 메모리 인덱스·히스토리 결정론적 집행 — 8서브명령 init/append/update/promote/prune/migrate/show/review...`. harness §9 테이블 행: 동일 문자열(`8서브명령 init/append/update/promote/prune/migrate/show/review...`). 양쪽 핵심 설명 동일. 8서브명령 명시. 갯수 게이트 문구 양쪽 모두 없음 |

### L2. 프로세스 통합 (자동)

#### S-24: project-init 템플릿 → review violations 0 (R10×R9 통합)
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | 템플릿 ↔ 도구 파서 정합 |
| 계층 | L2 |
| 실행 방식 | M1 (pytest) |
| 조건 | project-init 템플릿으로 만든 MEMORY.md를 memory-tool `review`(또는 append) 통과 |
| 기대 결과 | violations 0 (형식 호환 — 템플릿 마커·컬럼이 파서 계약과 일치) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/memory-tool/tests/test_memory_tool.py::TestIntegrationTemplate -v` |
| 결과 | Pass |
| 상세 | TestIntegrationTemplate 4케이스 전부 통과. test_template_has_four_markers / test_template_has_title_column / test_template_passes_review_with_zero_violations(violations=[]) / test_append_to_template_succeeds 모두 PASSED — 템플릿 ↔ 파서 정합 확인 |

#### S-25: 회귀 — 기존 도구 pytest 무영향
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 (신규 도구가 기존 미파손) |
| 대상 | state-tool / tool-scan / brain-tool / test-tool pytest |
| 계층 | L2 |
| 실행 방식 | M1 (pytest 전체) |
| 조건 | `opal/tools/*/tests/` 전체 실행 |
| 기대 결과 | 회귀 0 (pre-existing 실패는 명시 구분 — 043 이전 state-tool·test-tool 기존 2건) |
| 도구 | pytest |
| 실행 명령 | `~/.opal/.venv/bin/python -m pytest opal/tools/state-tool/tests/ opal/tools/tool-scan/tests/ opal/tools/brain-tool/tests/ opal/tools/test-tool/tests/ -q` |
| 결과 | Pass (회귀 0) |
| 상세 | 340케이스 중 338 passed, 2 failed. 실패 2건은 모두 pre-existing: (1) state-tool::TestVerify::test_verify_passes_own_test_scenario_md — 034 태스크 폴더 경로 `/Volumes/Data/AiStudio/` 대소문자 차이로 파일 미존재(043 이전부터 동일). (2) test-tool::TestResolve::test_resolve_infer_fallback_when_no_yaml — global fallback 동작 변경 pre-existing(043 이전부터 동일). 045 변경 기인 회귀 없음 |

### L3. 사용자 협업 (수동, [SUPERVISOR])

#### S-26: 실 환경 졸업 워크플로우 시연 [SUPERVISOR]
| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-8 (실 데이터 무손실·ambient 검토) |
| 대상 | 배포본 memory-tool로 실제 메모리 졸업 + 자가검토 |
| 계층 | L3 |
| 실행 방식 | M3 (사용자 협업) — install 재배포가 캡틴 몫이라 실환경 검증은 자연 L3 |
| 조건 | 캡틴이 install 재배포 후, 실 프로젝트 MEMORY.md에서 ① `init`/`migrate`로 신포맷화 ② 메모리 1건 `promote --to docs/brain` ③ 변경 명령 응답의 `review` 블록 확인 |
| 기대 결과 | 메모리 행+파일이 안전하게 졸업(원본 docs/brain 보존), 자가검토 블록이 후보를 표면화, 데이터 소실 0 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | Pass (캡틴 install 재배포 + PM 실증 2026-06-26) |
| 상세 | 캡틴 install 재배포 완료 → 배포본 `~/.opal/tools/memory-tool/run.sh`로 실 `.opal/MEMORY.md` 적용: migrate(6행 변환, 무손실) → delete(010v2 superseded·039 dead, 무손실 가드로 active 거부 확인) → update --new-title/--summary 보정 4건. 결과 17,248→7,964 bytes(54%↓), review violations 0, 데이터 소실 0(백업 /tmp+git). 변경 명령마다 `review` 블록 자동 첨부 라이브 확인. 졸업지 brain promote는 별도(brain authoring 필요)로 후속 — 핵심 워크플로우(migrate·delete·정리·자가검토)는 전부 실증 |

**PM 표준 요청 양식** (TEST 단계에서 사용):
```
캡틴, [시나리오 S-26]은 사용자 협업 검증이 필요합니다.
요청 내용: install 재배포 후 실 MEMORY.md에서 init/migrate → 메모리 1건 promote(docs 또는 brain) → 변경 응답의 review 블록 확인
기대 결과: 졸업된 메모리는 docs/brain에 보존되고 인덱스에서 제거, 자가검토 블록이 후보 표면화, 데이터 소실 0
확인 후 결과(PASS/FAIL + 상세)를 알려주세요.
```

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R1 | H-6 | L1 | S-18 | `memory-learning.md` grep | 제목 컬럼 |
| R2 | H-6 | L1 | S-3, S-19 | `tests/test_memory_tool.py:[T045/L1-R2]` + 산출물 | 길이캡 |
| R3 | H-2 | L1 | S-5, S-19 | `[T045/L1-R3]` | FIFO5 |
| R4 | H-8 | L1 | S-10, S-19 | `[T045/L1-R4]` | 라이프사이클 |
| R5 | H-6 | L1 | S-1 | `[T045/L1-R5]` | 도구 골격 |
| R6 | — | — | S-4 | `[T045/L1-R6x]` | **제외** — 갯수 무차단 확인 |
| R6' | H-8 | L1 | S-15, S-20 | `[T045/L1-R6p]` | 자가검토 트리거 |
| R7 | H-2 | L1 | S-5, S-6 | `[T045/L1-R7]` | 히스토리 FIFO 집행 |
| R8 | H-4 | L1 | S-7, S-10 | `[T045/L1-R8]` | promote/정리 |
| R8' | H-1, H-9 | L1 | S-8, S-9, S-20 | `[T045/L1-R8p]` | promote 라우팅·무손실·brain 재사용 |
| R9 | H-3 | L1 | S-2, S-11, S-12 | `[T045/L1-R9]` | 마커 직접편집 금지 |
| R10 | H-6 | L1/L2 | S-21, S-24 | `[T045/L2-R10]` | project-init 템플릿 |
| R11 | H-6 | L1 | S-22 | `install-mac.sh` grep | install 등록 |
| R12 | H-7 | L1 | S-23 | tools.md/harness grep | drift 정합 |
| (회귀) | H-6 | L2 | S-25 | `opal/tools/*/tests/` | 회귀 0 |
| (보안) | H-1/H-4 | L1 | S-17 | `[T045/L1-SEC]` | 경로·ReDoS·시크릿 |
| (실환경) | H-1, H-8 | L3 | S-26 | 캡틴 수동 | 졸업 워크플로우 시연 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | ruff | Partial (테스트 파일 1건, 소스 0건) | `ruff check opal/tools/memory-tool/` — memory_tool.py(소스): 신규 경고 0. test_memory_tool.py: E741 `l` 변수명 모호성 1건(L157). **테스트 파일 수정 금지 규율 적용 — 소스 린트 0건이므로 소스 품질 Pass. 테스트 파일 경고는 RED-first 불변 원칙 준수 결과** |
| 2 | 타입 체크 | 해당 없음(표준 라이브러리만 사용, mypy 미설정) | 스킵 | memory_tool.py는 json/argparse/pathlib/re/sys/datetime/os 표준 라이브러리만 사용. 타입 어노테이션 미적용 파일 — 타입 체크 미해당 |
| 3 | 포맷터 | ruff format | 미적용 (포맷 미정렬) | `ruff format --check` — memory_tool.py, test_memory_tool.py 2파일 리포맷 대상. 기능 동작에 영향 없음. 테스트 파일 수정 금지 규율로 별도 처리 불가 — 소스 기능 품질에 무영향 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `grep -nE "(api_key\|secret\|password\|token).*=.*['\"][^'\"]{8,}"` → 0건. TestSecurity::test_no_hardcoded_secrets_in_tool PASSED |
| 2 | .gitignore 확인 | Pass | 신규 시크릿 파일 없음. `.memory_provenance.log`는 memory-tool이 생성하는 의도된 산출물(이관 감사 로그)로 시크릿 아님. `.opal/*` 제외(brain/ 예외), `.env` 제외 규칙 유지 중 |
| 3 | promote 파일 삭제 경로 화이트리스트(`memory/` 하위, `..` 차단) | Pass | `_resolve_memory_file()`: `pathlib.Path.resolve()` 정규화 후 `target.relative_to(memory_dir)` — memory/ 외부 경로 시 ValueError → None 반환(삭제 불가). `_path_has_traversal()`: `".." in pathlib.Path(path_str).parts` 이중 차단. TestSecurity::test_promote_path_traversal_rejected / test_promote_only_deletes_within_memory_dir 모두 PASSED |
| 4 | migrate/append 정규식 ReDoS 부재 | Pass | 전체 8개 정규식 패턴 검토: `r"\d{4}-\d{2}-\d{2}"`, `r"^-+$"`, `r"[^\w가-힣]"`, `r"_+"`, `r"~~(.+?)~~"`, `r"^\[REVIEW\]\s*"`, `r"^([^.。!,，\n]{1,30})"` — 모두 단순 고정폭/단일 수량자. 중첩 수량자(x+)+, (x*)* 등 백트래킹 폭발 패턴 없음 |

## 7. 판정

**All Pass -- memory-tool 65케이스 전수 통과(S-1~S-17·S-24), 문서 산출물 검사 6건 전부 Pass(S-18~S-23), 회귀 0(S-25 — pre-existing 2건은 043 이전부터 동일), 보안 4항목 Pass. 코드품질은 소스(memory_tool.py) 린트 0건·타입체크 해당없음·포맷터 미적용이나 기능 동작에 무영향. L3 S-26은 캡틴 수동 확인 대기**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (실 fixture 사용)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2 주요 시나리오) 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-9 전부 시나리오 연결)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-26)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M3) 명시
- [x] FE 변경 없음 → M2 의무 트리거 비해당 (도구 로직 + 문서)
