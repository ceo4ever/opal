# DONE: 이벤트 로더 보안 보강(GC-004·006·011·012) + 절 단위 로딩(P3) 실험

## 결과

태스크 175가 남긴 보안 권고 4건을 해소하고, 절 단위 로딩을 명시적으로 켠 호출에서만 동작하는 실험 모드로 구현해 측정했다. 측정 결과 권고는 **기본값 전환 보류**다. 시나리오 14건이 모두 통과했고(RED 8건 포함), 컨벤션 검사는 0건, 보안 검사는 차단 지적 없음(`PASS_WITH_ADVISORIES`)으로 끝났다.

**달라진 것**

- **GC-006 원장 override.** `OPAL_EVENT_LOADER_LEDGER`·`OPAL_EVENT_LOADER_NOW`는 `OPAL_EVENT_LOADER_TEST_MODE=1`일 때만 적용된다. 그 밖에는 무시하고 응답 `warnings`에 `ledger_override_ignored`를 남긴다. 원장 쓰기 실패와 override 사용은 원장 옆 `legacy-dispatch.integrity.jsonl`(→ 임시 폴더 0600 → stderr 순서)에 남고 `legacy-report`가 `integrity`와 `reliable`로 보여준다. 원장 경로는 `--deployed-root`·`OPAL_DEPLOYED_ROOT`로 옮겨지지 않는다.
- **GC-011 매니페스트 정규화.** 기본 `events.json` 경로를 실제 경로로 정규화해, 심볼릭 링크 설치에서도 정상 receipt가 통과하고 다른 매니페스트를 가리키는 receipt는 계속 `stale_receipt`로 거부된다.
- **GC-004 `--role-doc`.** 프로젝트·소스·설치 루트 안의 일반 파일이고 1,048,576바이트 이하일 때만 받는다. 위반은 `contract_arg_invalid`에 `cause`(`outside_allowed_roots`·`not_regular_file`·`too_large`·`unreadable`)를 붙여 거부하며 FIFO·장치 파일은 열지 않는다.
- **GC-012 게이트.** `verify --require-default-manifest`가 실행 경계 매니페스트와 문서 루트가 설치본 정본과 다르면 `manifest_not_default`로 거부하고 통과 시 `manifest_default: true`를 남긴다. `state-tool event-verify`가 이를 전달하고, PM 디스패치 Step 0·워커 진입 게이트 16종·하위 디스패치 3종이 이 플래그와 성공 조건(`manifest_path`가 `~/.opal/references/events.json`의 실제 경로와 같고 `manifest_default`가 `true`)을 갖는다. `static-check`가 플래그 누락·override 인자를 `dispatch_gate_default_manifest_missing`·`dispatch_gate_manifest_override`로 잡는다.
- **절 단위 로딩 실험(AC-5).** `--section-mode lazy --section-context KEY=VALUE`로만 켜진다. `events.json`의 `sectioning`과 `opal/core/references/sections/*.json` 선언(절 id·분류 always/conditional/on_demand·의존·조건)에 따라 `[MUST` 포함 절·항상 필수 절·조건 성립 절·의존 절과 목차만 전달한다. 필요한 절은 `section` 서브명령으로 가져오며 별도 receipt가 부모 receipt에 묶이고 `verify --parent-receipt`로 검증된다. 대상은 프레임워크 문서 4종(`citation-rules`·`design-gate`·`pm-review-gate`·`opal-pm.md`)이다.
- **측정(AC-6).** `MEASURE.md`. `stage.design` 본문 53,305 → 48,059바이트(9.84% 감소), 나머지 3개 이벤트는 0%, 4개 이벤트 합계 2.34% 감소이며 응답 바이트는 모든 이벤트에서 오히려 늘었다(+2.7~12.4%). `[MUST` 보존 316/316줄. 프로브 40호출: 엄격 채점 켬 19/20 대 끔 20/20(의미 기준 20/20 대 20/20, 차이 1건은 채점 정규식 미스). 판정 기준(실행 전 고정)을 하나도 못 채우는 항목이 있어 **보류**. 4문서가 대부분 규범이라 `[MUST` 보존을 지키면 뺄 수 있는 절이 `design-gate` 4개(5,628B)뿐이었다.

**유지한 것(C-1):** 끈 호출의 응답·receipt·verify 결과는 시작 커밋 loader와 같다(`worker.dispatch`는 의도한 문서 수정 +186B만 다름). 계약 v2와 구형 호환, 대상 문서 본문은 수정하지 않았다.

**제외한 범위:** 제안서 2차(제한된 P2), 실험 모드 기본값 전환, 호환 종료 플래그, `docs/PROJECT.md`·`.opal/AGENT.md`의 절 분할(프로젝트별 구조라 이번 실험에서 제외, `pm.activate` 본문의 67.6%가 여기에 해당).

## 변경 파일

- `opal/agents/*/AGENT.md` (16종)
- `opal/core/references/events.json`
- `opal/core/references/pm/dispatch-process.md`
- `opal/core/references/sections/citation-rules.json`
- `opal/core/references/sections/design-gate.json`
- `opal/core/references/sections/pm-review-gate.json`
- `opal/core/references/sections/pm-process.json`
- `opal/tools/event-loader/event_loader.py`
- `opal/tools/event-loader/lazy_sections.py`
- `opal/tools/event-loader/README.md`
- `opal/tools/event-loader/tests/conftest.py`
- `opal/tools/event-loader/tests/test_event_loader_security.py`
- `opal/tools/event-loader/tests/test_lazy_sections.py`
- `opal/tools/event-loader/tests/test_event_loader_lazy_mode.py`
- `opal/tools/event-loader/tests/test_event_loader_section_declarations.py`
- `opal/tools/event-loader/tests/test_event_loader_dispatch_contract.py`
- `opal/tools/event-loader/tests/test_event_loader_static_and_index.py`
- `opal/tools/event-loader/tests/test_event_loader_extended.py`
- `opal/tools/state-tool/state_tool_parts/cli.py`
- `opal/tools/state-tool/state_tool_parts/gates.py`
- `opal/tools/state-tool/tests/test_event_verify.py`
- `docs/proposals/261001_이벤트_문서_로딩_경량화.md`

## 검증

- 시나리오: `test-scenario.json` 14/14 PASS (RED 대상 S-1~S-5·S-8·S-10·S-11 확인·잠금).
- 회귀: `pytest opal/tools/event-loader/tests opal/tools/state-tool/tests` — 913 passed, 4 failed. 4건은 시작 커밋 `e501bdb0`에서도 같은 실패다(`test_static_check_ok`, `test_project_brief_cli_preserves_inputs_and_multitask_counts`, 세션 환경변수 의존 state-tool 2건).
- 정적 검사: 소스 `static-check`는 시작 커밋부터 있던 `opal/skills/opal-pilot-dev2/SKILL.md`의 `event_contract_missing` 3건(`stage.analysis`·`stage.test_scenario`·`stage.close`)만 남고 새 위반 0건(선언 검사 포함).
- 끈 호출 불변: 시작 커밋 loader와 `session.assistant`·`pm.activate`·`stage.task`·`stage.plan`·`stage.design`·`worker.dispatch`의 load·verify 출력·receipt 비교 일치.
- 컨벤션: 최초 High 4(테스트 4파일 `@header` `exports` 비어 있음) → 수정 → 최종 Critical·High·Medium·Low 0건.
- 보안: 최초 FAIL(신규 GC-001 medium: lazy receipt의 `unit_sha256`·`delivered` 미결속으로 위조 통과 재현) → `per_doc` 전 필드 대조·추가 절 본문을 현재 문서 재계산과 비교·이미 전달된 id 거부, GC-012 잔여(문서 루트 미결속) 수정 → 최종 `PASS_WITH_ADVISORIES`(차단 0건, 재현으로 해소 확인).
- 설치: 실제 `~/.opal` 설치는 하지 않았다(클린 재배포가 이 세션이 쓰는 도구·문서를 교체하는 전역 변경). 설치 레이아웃을 임시 루트에 재현해 설치본 loader·state-tool로 load·verify·lazy·게이트 통과와 사본 매니페스트 거부를 확인했다.

## 회고적 학습 후보

.opal/brain/pages/concept/section-lazy-loading-experiment-hold.md
.opal/brain/pages/concept/lazy-receipt-full-field-recompute.md
.opal/brain/pages/concept/default-manifest-gate-flag.md
.opal/brain/pages/concept/test-mode-bound-override-integrity-record.md
.opal/brain/pages/concept/lazy-loading-scope-framework-docs-only.md
.opal/brain/pages/concept/worker-dispatch-contract-v2-binding.md
.opal/brain/pages/concept/legacy-dispatch-compat-sunset-observation.md
.opal/brain/pages/concept/event-response-single-body.md

## 참고

- **실제 설치 필요(캡틴 결정).** merge 후 `scripts/install-mac.sh`로 loader와 문서를 한 번에 배포해야 한다. 설치본 loader가 구버전이면 새 게이트 문서의 `--require-default-manifest`가 알 수 없는 인자로 실패한다(fail-closed). 설치 직전 `~/.opal/tools/event-loader`를 `cp -R`로 보존한다(install은 백업을 만들지 않는다).
- **남은 보안 advisory(low, 의도적 미수정):** test-mode override 사용이 기본 `legacy-report`에 보이지 않음, `--role-doc` 허용 루트가 `--project-root /`·cwd 폴백으로 넓어질 수 있음, 임시 폴백 무결성 파일 읽기 시 소유자·권한 미검사(공유 `/tmp` 환경 한정), 소스 실행 시 `deployed_root` 미결속, `events.json` 단독 심볼릭 링크일 때 `--require-default-manifest` 오거부(fail-closed), 켠 응답에서 최상위 `section_mode` 삭제 시에도 통과(receipt·문서 해시는 검증됨), 켠 receipt에서 `section_mode`를 지우고 source 해시를 복사하는 평문 다운그레이드(기존 평문 모드 성질).
- **범위 밖 기존 이슈(후속 후보):** `opal/skills/opal-pilot-dev2/SKILL.md`의 소비자 계약 누락 3건, 기존 실패 테스트 4건.
- **절 단위 로딩 후속 후보:** 감소율을 올리려면 `pm-review-gate`의 `검토 절차`(문서의 71%, `[MUST` 포함 단일 level-3 단위)와 `citation-rules` §8 등 큰 단위를 더 잘게 쪼개야 하며, 같은 `measure/` 하니스로 재측정한다. 기본값 후보로 올리려면 opst 반복 실행(비용·승인 필요)이 전제다. `docs/PROJECT.md` 절 분할은 프로젝트 소유 선언 구조가 필요하다.
- **제안서 아카이브:** `docs/proposals/261001_이벤트_문서_로딩_경량화.md`는 2차(제한된 P2)와 P3 후속 결정이 남아 있어 아카이브하지 않는다.
- 증거: `MEASURE.md`, `measure/`, `GC-SECURITY-2026-10-02T11-30-00.md`, `GC-CONVENTION-2026-10-02T11-30-00.md`, `AGENTIC-LOG.md`.
