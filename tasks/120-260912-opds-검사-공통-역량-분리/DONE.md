# DONE: GC 검사 역량의 공통 스킬 분리

## 결과

보안 검사·컨벤션 검사·결과 통합이 `opal-pilot-gc` 수명주기에서 분리되어 각각 독립 호출 가능한 단계 스킬이 됐다. `op-gc-security`·`op-gc-convention`은 read-only finding을 생성하고, `op-gc-report`는 검사하지 않고 결과 정규화와 릴리스 판정만 담당한다. 세 스킬은 Pilot 없이 단독 호출되며, 태스크 채번·`state.json` 생성 없이 보고서와 finding JSON을 산출한다.

finding 필드·envelope·fingerprint·source_tier·최종 판정·baseline delta의 원문은 `opal/core/references/harness/gc-finding-schema.md` 한 곳이 소유한다. 이전에 pilot references·두 checker AGENT.md·pilot SKILL.md 세 군데에 중복돼 있던 규칙은 이동으로 정리됐고 축약 잔존도 남기지 않았다. 두 checker는 검사 기준을 보유하지 않고 지정된 `skill_path`를 읽어 수행하는 role이 됐다(212→69행, 250→87행).

판정에 `INCOMPLETE`가 신설되어 검사기가 실행되지 못한 상태가 통과와 구조적으로 분리된다. `docs/CONVENTIONS.md`가 없을 때 검사를 통째로 생략하던 동작은 폐기되고, 관측 기반 advisory 수행 + `status: partial` + 결측 기록으로 바뀌었다. advisory는 차단 사유로 계산하지 않으므로 기존 호출자(oppl T4b·PM Gate)의 흐름은 막히지 않는다.

유지된 것 — `opal-pilot-gc`의 SCAN→CHECK→REPORT→CLOSE 4단계, 사용자 Gate 문안, CLOSE 진입 게이트·DONE.md·op-brain-ingest 훅·회고 하드스텝·opds 체인 안내, `references/pipeline.json` 7행(한 글자도 변경하지 않았다). SCAN에는 범위 5경로(staged·all·untracked·commit[:ref]·explicit)와 baseline 탐색이 추가됐고, 하위 스킬의 대상 재선별을 금지하는 `[MUST]`가 명시됐다.

## 변경 파일

- `opal/core/references/harness/gc-finding-schema.md` (신규)
- `opal/skills/op-gc-security/SKILL.md` (신규)
- `opal/skills/op-gc-security/references/security-baseline.md` (이동 ← `opal-pilot-gc/references/base-security-checklist.md`)
- `opal/skills/op-gc-security/references/report-template.md` (이동 ← `report-security-template.md`)
- `opal/skills/op-gc-security/references/sample-report.md` (이동 ← `sample-report-security.md`)
- `opal/skills/op-gc-convention/SKILL.md` (신규)
- `opal/skills/op-gc-convention/references/convention-categories.md` (이동 ← `base-convention-checklist.md`)
- `opal/skills/op-gc-convention/references/report-template.md` (이동 ← `report-convention-template.md`)
- `opal/skills/op-gc-convention/references/sample-report.md` (이동 ← `sample-report-convention.md`)
- `opal/skills/op-gc-report/SKILL.md` (신규)
- `opal/skills/op-gc-report/references/report-template.md` (신규)
- `opal/skills/opal-pilot-gc/SKILL.md`
- `opal/agents/opal-security-checker/AGENT.md`
- `opal/agents/opal-convention-checker/AGENT.md`
- `opal/core/references/agents.md`
- `opal/core/references/opal-skills-registry.json`
- `scripts/tests/task113_bootstrap_audit.py`
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `docs/CONVENTIONS.md`
- `docs/proposals/archives/opal-gc-capability-refactor.md` (이동 ← `docs/proposals/`)

## 검증

- `test-tool scenario-status` — 17/17 PASS, failed 0, blocked 0, locked. 1차 실행에서 S-13 FAIL 후 fix 1/3으로 해소, 회귀 대상 S-6·S-9·S-12를 실제 검사 실행으로 재확인.
- `git diff --exit-code -- opal/skills/opal-pilot-gc/references/pipeline.json` — exit 0 (행 구성 불변)
- `python3 -m unittest discover -s opal/tools/state-tool/tests -t opal/tools/state-tool/tests` — OK (skipped 3)
- `python3 -m unittest discover -s opal/tools/memory-tool/tests -t opal/tools/memory-tool/tests` — 202 tests OK (opgc 채번 지시 문구 보존)
- `python3 scripts/tests/task113_bootstrap_audit.py --mode source` — exit 0 (이관 체크리스트 경로 갱신 확인)
- `node opal/tools/skill-registry/skill-registry.js validate` — `valid: true`, errors 0, unregistered 0 (배포 후)
- 구형 잔존 grep — 구 체크리스트·템플릿 경로 0건, 두 AGENT.md의 `OWASP`/`CWE-`/`SANS`/`fingerprint`/`auto_fixable`/트리거 0건
- Gate 문안 보존 grep — `close.done_md`·`--owner user`·`CLOSE로 진행할까요` 7건 매칭
- S-17 E2E — `--scope commit:81363d1`로 배포본 SCAN→CHECK→REPORT 실행. SCAN 29파일과 최종 `checked_files` 완전 일치, 두 checker가 스킬 부재 없이 로드, verdict `INCOMPLETE`가 schema §6에 부합
- 컨벤션 자동 진단 — `GC-CONVENTION-20260912-1648.md` Critical 0 / High 0 (Medium 1·Low 1은 처리 완료)
- `scripts/install-mac.sh` — exit 0, 신설 3스킬과 schema 문서 배포 확인

## 회고적 학습 후보

.opal/brain/pages/concept/skill-opal-pilot-gc.md
.opal/brain/pages/concept/gc-finding-schema.md
.opal/brain/pages/concept/opal-skill-classification-system.md

## 참고

- 미적용 범위: 제안서 §11 마이그레이션 6단계(`opal-self-pm` 연결)는 해당 컴포넌트가 실재하지 않아 제외했고, 7단계(reference registry)는 외부 공급망 축이라 별도 태스크가 적합하다. 제안서는 `docs/proposals/archives/`로 이관하며 적용 범위를 상단에 명시했다.
- 잔여 링크 1건: `docs/proposals/opal-pm-direct-execution.md:6`이 `./opal-gc-capability-refactor.md`를 상대 경로로 가리켜 이관 후 깨진다. 해당 파일은 다른 작업이 수정 중이라 이번 태스크에서 건드리지 않았다. `../archives/opal-gc-capability-refactor.md`로 갱신이 필요하다.
- 별도 태스크 필요 (보안): `~/.opal/`·`~/.claude/agents/`로 배포되는 checker 어댑터 파일에 `tools` frontmatter가 없어 런타임 워커가 read-only 계약과 달리 Write/Edit 권한을 보유한다. 어댑터 계층의 계약 누수이며 이번 태스크 AC/C 범위 밖이다.
- 선행 이슈: `opal/tools/tool-scan/tests` 4건 실패는 클린 baseline에서도 동일 재현하며 이번 변경과 무관하다.
- 프레임워크 개선 후보: 단일 `execute.implement` 행을 여러 Work item 워커가 공유하는데 `op-dev-execute`는 워커마다 mark를 지시한다. 첫 워커가 EXECUTE를 조기에 닫으며, `advance` 되감기 경로가 없어 복구도 불가능하다.
