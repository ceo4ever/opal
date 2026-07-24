# DONE: 도구·MCP·스킬 통합 검색·사용법·활용 체계 (tool-scan)

> 완료일: 2026-06-26 | 스킬: //opd (agentic) | 태스크: 044

## 1. 목표 달성

PM이 작업 중 필요한 capability(OPAL/외부 CLI 도구·MCP·스킬)를 **상황 검색 → 권위 출처(live) 사용법 확인 → 정확 사용**하도록 하는 결정론적 체계를 구축했다. 발단은 MAMS cmux 사건(존재하지 않는 `take-screenshot` 추측 호출 → 무분별 Playwright 폴백). 핵심 목적 = "정확한 *그 도구의* 사용법 확보" — 검증에서 `usage cmux-tool`이 cmux의 실제 12 서브명령을 반환함을 실증.

## 2. 산출물

| 영역 | 산출물 | 비고 |
|------|--------|------|
| 신규 도구 | `opal/tools/tool-scan/` (run.sh·tool_scan.py·manifest.json·lib/federation.py·tests/) | 5서브명령 list/which/usage/resolve/check |
| 인지맵 | `opal/core/AGENT.md` | localhost→cmux-tool 오라우팅 수정 + cmux-tool·tool-scan 행 + 도구 사용 규율(사용법 선확인·에러 진단후 폴백) |
| drift 정합 | `opal/core/references/tools.md` (brain-tool·tool-scan 섹션) + `opal-harness.md §9` (code-scan·cmux·tool-scan 행) | 두 표 7도구 동일화 |
| 배포 | `scripts/install-mac.sh` | tool-scan chmod 블록 |
| 문서 | `docs/ARCHITECTURE.md` | tools/ 목록에 tool-scan 반영 |

### 핵심 설계
- **thin manifest** — usage 텍스트 미저장, `usage_source` 포인터만(drift 표면 ≈ 0). OPAL 도구 7종만 SSOT.
- **federation 읽기** — MCP=mcps.md / 스킬=skills-registry.json 읽기 전용(불파괴, MD5 검증). MCP는 ToolSearch 포인터, op-skill은 dispatched_by 포함.
- **usage = live** — 매 호출 대상 도구 `--help` 셸 실행(정적 캐시 금지). OPAL=exit code 판정(cmux `ok:false+exit0` 함정 회피) / 외부 CLI=stdout+stderr 병합.
- **결정론 라우팅** — `(-score, kind우선순위, name)` 안정 정렬.

## 3. 검증 결과

- **tool-scan 22/22 GREEN** (TS-001~060 + 버그회귀 TS-024)
- **RED-first** 적용 — 작성자(opal-test-agent) ≠ 구현자(opal-be-agent). RED 25 FAIL 증거 후 GREEN.
- **회귀 0** — 기존 state-tool/test-tool 실패 2건은 git stash 교차확인 결과 043 이전 pre-existing(이번 무관). skills-registry.json MD5 불변.
- **보안** — subprocess shell=False, 경로 화이트리스트(`_validate_path`), ReDoS 256자 가드, 시크릿 0.
- **실증 스모크 6/6** — usage가 대상 도구 사용법 정확 반환, resolve가 tool/mcp/op-skill 정확 분기.

## 4. 특이사항 — 핵심 버그 (PM 직접 검증이 포착)

워커는 22/22 GREEN을 보고했으나, **PM의 실제 실행 검증에서 `usage <tool>`이 대상 도구가 아니라 tool-scan 자기 자신의 `--help`를 반환하는 버그**를 발견(`tool_scan.py:275` `_TOOL_DIR/run.sh`). 단위 테스트가 항상 `TOOL_SCAN_HELP_CMD` env로 stub을 주입해 실제 경로 해석을 검증하지 않은 맹점. fix 루프 1/3으로 해결(`~/.opal/tools/<name>/run.sh` 해석). **이 작업의 주제(정확한 도구 사용)가 작업 과정에서 그대로 재현된 사례** — agentic 산출물 직접 검증 의무의 가치.

## 5. 후속/Known Issues

| # | 항목 | 조치 |
|---|------|------|
| 1 | **install 재배포 필요** | AGENT.md·tools.md·harness·tool-scan 변경은 캡틴이 `install-mac.sh` 재실행해야 실세션 발효. 워커가 ~/.opal에 사전배포한 사본은 dev 아티팩트(install로 정합) |
| 2 | 커밋 미수행 | 캡틴 명시 지시 시 수행 (커밋 규칙) |
| 3 | ruff 2경고(F401 os·E402) | 비차단 — 후속 클린업 가능 |
| 4 | TS-001 배포 의존(비-hermetic) | 프로덕션 무해(tool-scan은 배포본 실행). 후속 hermetic 개선 여지 |
| 5 | pre-existing 회귀 2건(state-tool·test-tool) | 044 무관 — 별건 추적 |
| 6 | TS-050/051 테스트 regex 크루드 | 소스를 계약에 맞춰 해소(백틱 제거). 테스트 품질 개선 여지(별건) |

## 6. 상태판

TASK→ANALYSIS→PLAN→TEST-SCENARIO→EXECUTE→TEST 전부 ✅, 게이트 판단 3 Pass / 오류 1 검출·수정 / PM 의사결정 5건 (AGENTIC-LOG.md 참조).
