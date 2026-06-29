# opal Memory Index

> 최종 갱신: 2026-06-26 (044 도구·MCP·스킬 통합 검색·사용법·활용 체계 — TASK)
> last_task_number: 47
> ⚠️ 채번 충돌: 015·016이 양 PC에서 중복 사용됨 (main: 015 보고형식·016 TDD·017 가드 / brain 라인: 015 brain 코어·016 wiki 지능화). 다음 채번은 018부터.


| 카테고리 | 설명 | 완료 시 |
|----------|------|---------|
| task | 일회성 작업 계획/예정 | 삭제 |
| project | 프로젝트 비전, 방향성 등 지속 지식 | 유지 (폐기 시 삭제) |
| architecture | 아키텍처 설계 결정과 근거 | 유지 (변경 시 갱신) |
| feedback | 캡틴의 작업 방식 피드백 | 유지 (철회 시 삭제) |
| preferences | 이 프로젝트에서 캡틴이 선호하는 방식 | 유지 |
| issues | 반복되는 이슈와 해결법 | 유지 |

> 메모리 파일은 `memory/` 디렉토리에 저장한다.
> 새 메모리가 생기면 이 인덱스에 파일 경로와 설명을 추가한다.
> **task 타입은 완료 시 메모리 파일 + 인덱스 항목을 삭제한다.**





> v0.5.0 베이스라인 시작 — 이전 작업 히스토리는 git log + tasks/ 폴더(삭제됨)에서 추적
> 새 태스크는 001부터 채번

## 메모리
<!-- memory:index:start -->
| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
|------|--------|------|------|------|------|
| Console 브레인 구독 인증 | 2026-06-22 | project | active | `memory/console-brain-subscription-auth.md` | Console 브레인 질의는 종량제 API 아닌 사용자 Claude 구독(로컬 claude -p). API키·SDK 금지 |
| 브레인 질의 콜드 경량화(037후속) | 2026-06-23 | task | active | `memory/follow-up-brain-query-lite.md` | 브레인 질의 콜드 latency 경량화 — 검색을 LLM 밖 brain-tool로. opbr --lite 권고 |
<!-- memory:index:end -->

## 작업 히스토리 (최대 5개, FIFO)
<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
| 045 메모리 관리 개선 + memory-tool 신설 | 2026-06-26 | 완료 | tasks/045-260626-opd-메모리-관리-개선/ | memory-tool 9서브명령 + memory-learning.md 개정(제목·길이캡·FIFO5·라이프사이클·docs/brain 졸업·자가검토). 88 GREEN, .opal/MEMORY.md 56%↓. 후속=install 재배포·커밋 |
| 044 도구·MCP·스킬 통합 검색·사용법·활용 체계 | 2026-06-26 | 완료 | tasks/044-260626-opd-도구-검색-사용법-활용/ | [REVIEW] 044 도구·MCP·스킬 통합 검색·사용법·활용 체계 (opd, agentic) — 발단=MAMS cmux 사건(없는 `take-screenshot` 추측→무분별 playwright 폴백). **신규 `tool-scan` 도구**(`opal/tools/tool-scan/`, 5서브명령 list/which/usage/resolve/check): capability(도구/MCP/스킬) 상황검색+**권위출처 live `--help` 확인**. **thin manifest**(usage 텍스트 미저장·`usage_source` 포인터만=drift 표면≈0, OPAL 7도구만 SSOT) + **federation 읽기**(MCP=mcps.md/스킬=skills-registry.json 불파괴·MD5검증, MCP=ToolSearch 포인터·op-skill=dispatched_by). usage=대상도구 `--help` 셸실행(정적캐시 금지, OPAL=exit code 판정으로 cmux `ok:false+exit0` 함정 회피/외부=stdout+stderr 병합). 결정론 라우팅(`(-score,kind,name)`). **인지맵 정비**(AGENT.md localhost→cmux-tool 오라우팅 수정+cmux-tool·tool-scan 행+사용규율 사용법선확인·에러종류 진단후폴백) + **drift 정합**(tools.md↔harness §9 7도구 동일화) + install 등록 + ARCHITECTURE 반영. **RED-first**(작성자 test-agent≠구현자 be-agent, RED 25 FAIL→GREEN). **🐛핵심버그**=`usage`가 대상도구 아닌 tool-scan 자기 help 반환(`tool_scan.py:275` `_TOOL_DIR/run.sh`)→**PM 직접실행 검증이 테스트 맹점(stub env 주입으로 실제경로 미검증) 포착**(agentic 직접검증 가치)→fix1/3(`~/.opal/tools/<name>/run.sh`)+RED회귀 TS-024. TEST **22/22 GREEN**, 회귀0(state-tool·test-tool 2건=043 이전 pre-existing), 보안(shell=False·경로화이트리스트·ReDoS·시크릿0) Pass, 스모크6/6. 후속=**캡틴 install 재배포**(소스 SSOT, 워커 ~/.opal 사전배포는 dev아티팩트)·커밋·ruff2경고. 커밋 안 함 |
| 042 CLOSE 단계 관련 문서 업데이트 스텝 추가 | 2026-06-24 | 완료 | tasks/042-260624-opds-close-문서업데이트/ | [REVIEW] 042 CLOSE 단계 관련 문서 업데이트 스텝 추가 (opds, agentic) — 8개 pilot CLOSE에 brain ingest 직전 "관련 문서 업데이트" 스텝 삽입(PROJECT.md 레지스트리+changed_files 기반, PM 판단+직접 수정/워커 호출, 없으면 no-op). 3패턴(A:6개/B:opsdd/C:opgc) 분류 적용. 변경이력 8파일 추가. opal-brain-design.md §8.2 CLOSE 흐름 갱신. brain concept 1건 ingest. 커밋 미수행 |
| 043 부트스트랩 게이트 설정파일 전환 (opds | 2026-06-24 | 완료 | tasks/043-260624-opds-부트스트랩-게이트-설정파일-전환/ | [REVIEW] 043 부트스트랩 게이트 설정파일 전환 (opds, agentic) — 040 후속. 환경변수 게이트(`echo $OPAL_BOOTSTRAP`)가 simple_expansion이라 매 세션 권한 프롬프트 유발(허용규칙도 자동승인 불가, claude-code-guide 권위확인). **배포 설정파일 `~/.opal/setting.json` Read 게이트로 전환** — 핵심: 부트스트랩이 이미 무프롬프트로 쓰는 `Read(~/.opal/**)` 경로에 얹어 **새 권한 표면 0**. 신규 `opal/core/setting.default.json`(`{"bootstrap":"on"}`)+`install_opal_setting` create-if-absent(멱등, 사용자 토글 보존)+windows 미러+linux exec위임 자동상속. 게이트 5곳(AGENT.md step0+부트스트래퍼 claude/gemini/codex/cursor) echo→setting.json Read, fail-safe(부재·파싱실패=정상) 040 계승. install perm `Bash(echo $OPAL_BOOTSTRAP)` 제거(직전 L2 미커밋 reconcile). RED-first(install 동작계약 TS-002 멱등/TS-003 생성, 작성자≠구현자). 🐛 macOS bash3.2서 `source <(sed)` 함수정의 불가→test-agent가 named temp file source로 하네스 수정(assertion 불변, RED 유지가드). **TEST 14/0 All Pass**+3 pending(캡틴 L2/L3 실세션). PM 슬립=state mark `>/dev/null` 출력억제로 PLAN행 누락→stage guard 후속행 조용히 거부→순차 reconcile(교훈: state mark 출력억제 금지). 후속=캡틴 install 재배포·실세션 off/on/부재 검증·프로젝트 오버라이드(H-8). 커밋 안 함 |
| 041 E2E 테스트 실행 개선 (opd | 2026-06-24 | 완료 | tasks/041-260624-opd-e2e-테스트-실행-개선/ | [REVIEW] 041 E2E 테스트 실행 개선 (opd, agentic) — E2E 미실행 3개 원인 해소. ①EXECUTE: op-dev-execute Step 3-S-1에 `test-tool unit --scope be/fe` 명시 호출 추가(v2.3). ②TEST FE: e2e_adapter.py playwright fallback에 `mcp_action:"browser_navigate"`/`mcp_url` 필드 추가 + opal-test-agent AGENT.md playwright MCP 4단계 분기 배선(v1.7). ③TEST BE: test-scenario-guide.md BE API M2 Swagger via cmux 의무 트리거 추가(v2.6) + AGENT.md 분기 1-b(Swagger URL 패턴 감지→Try it out 플로우). ④OPAL_TEST_TOOLS_GLOBAL: install-mac.sh `register_test_tools_global_in_shell_rc` 신설+shell rc 멱등 등록(v3.4). ⑤SKILL.md PM Gate FE→M2 의무 체크박스(v1.7). pytest 12/12 PASS. 커밋 미수행 |
<!-- memory:history:end -->
