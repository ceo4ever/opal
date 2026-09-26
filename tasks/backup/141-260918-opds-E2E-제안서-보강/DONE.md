# DONE: E2E 여정·조각 라이브러리 제안서 검토 지적 5건 반영

## 결과

`docs/proposals/e2e-journey-fragment-library.md`(상태 `검토`)의 §2·§3·§4·§5·§9와 상단 머리글을 개정해, PM 검토에서 나온 지적 5건을 문서에 반영했다.

- **착수 선행 조건이 요약 표에서 읽힌다.** §2 해법 요약 표에 `착수 선행 조건` 열을 신설했다. 재사용(조각) 축에 Q-1과 증적 마스킹 보강(§4), 확장(driver wrapper) 축에 Q-6과 driver 적합성 스위트(§7)를 배치하고 나머지 5행은 `없음`으로 채웠다. 종전에는 선행 조건이 §4·§7 본문 깊숙이 흩어져 있어 표만 읽으면 바로 착수 가능한 제안으로 읽혔다.
- **Q-1이 열린 쟁점에서 착수 선행 조건으로 승격됐다.** §9 자리와 ID는 그대로 두고 `[착수 선행 조건]` 등급 표기만 부여했다. 승격 근거로 §1 표 1행(동결 spec은 `scenario-lock` 이후 변경 불가)과 동결 RED S-27을 인용해, "조각 전개가 S-27에 걸리면 조각 기능 자체가 구현 불가"라는 인과를 문서가 스스로 말하게 했다.
- **신선도 키가 실행 정체를 포함한다.** §5 키에 선택 driver 정체(`driver`+`session_mode`)와 달성 충실도를 추가하고 생략 허용 조건을 4개에서 5개로 늘렸다. `.opal/e2e/order.json`(§7)으로 후보 순서를 바꾸면 키가 불일치해 이전 `pass` 증적을 재인용할 수 없다는 판정을 명시했다. 충실도 등급 정의는 복제하지 않고 `FIDELITY_ORDER`를 참조만 한다. `api` profile 상한(`real-http`) 함정과 driver 정체 흔들림 한계도 같은 절에 남겼다.
- **자격증명 노출을 고칠 지점이 증적 층으로 지목됐다.** §4에 `value_ref`가 조각 안 step만 덮고 조각 밖 본문 `fill`은 못 덮는다는 적용 범위 한계를 적고, 고쳐야 할 지점을 `redaction.py`의 키 이름 기반 판정으로 경로·줄번호와 함께 지목했다.
- **승격이 도구 게이트가 됐다.** §3에 `(태스크)/e2e/` → `docs/e2e/` 승격 자격은 `test-tool` exit 계약의 `pass` 증적을 도구가 확인한 뒤에만 성립하며 사람의 산문 판단만으로는 승격할 수 없다는 [MUST]를 넣었다. §6이 이미 세운 판정 소유 경계를 승격 지점까지 이은 것이며 새 규범이 아니다.
- **Q-5 결번이 해소됐다.** git 이력으로 확정했다 — 커밋 `6d1c8f1`까지 Q-5는 "`import` 모드의 한계"였고, `28e91e1`(ADD-1 반영)에서 Q-4가 Ego Lite로 재배정되며 구 Q-4·구 Q-5가 각각 Q-8·Q-9로 이관되어 번호만 비었다. 내용 소실이 없으므로 "이력 확인 불가"가 아니라 "결번(번호 이관, 내용 소실 없음)"으로 Q-4와 같은 표기 방식으로 적었다.

유지된 것: 제안서 상태는 `검토` 그대로다. 절 번호 §1~§9와 쟁점 ID Q-1~Q-9를 재배치·재번호하지 않아 이 문서를 인용하는 후속 참조가 끊기지 않는다. 제안을 채택하거나 E2E 기능을 구현하지 않았고, `opal/tools/test-tool/` 코드와 `docs/e2e/`·`.opal/e2e/`·`.e2e/` 폴더는 만들지도 고치지도 않았다.

## 변경 파일

- `docs/proposals/e2e-journey-fragment-library.md`

## 검증

- `test-tool scenario-status` — `locked: true`, `total: 13`, `passed: 13`, `failed: 0`, `blocked: 0`. S-1~S-13 전건 PASS.
- `test-tool scenario-fidelity-check` — `all_met: true`, 13/13.
- `test-tool scenario-coverage-check` — exit 0, `all_covered: true`. AC 7건·C 5건·H 3건 전건 시나리오 연결.
- `op-scenario-gate` iteration 1 — `verdict: pass`, `reason: converged`. 결정론 검사 exit 0 + 독립 evaluator 루브릭 goal 2 / adoption 2 / boundary 2(평균 2.0, gaps 0) 2증거 충족.
- `state-tool verify --plan-contract-check` / `--code-scan-citation-check` / `validate` — 전건 pass, violations 0.
- `code-scan validate --changed docs/proposals/e2e-journey-fragment-library.md --json` — exit 0, `newly_uncovered: 0`. `pre_existing: 1`은 비차단 보고 항목이다.
- `git status --porcelain` — `M docs/proposals/e2e-journey-fragment-library.md`와 태스크 캡슐 폴더 2건뿐. `git status --porcelain opal/`과 `git diff --stat -- opal/`은 빈 출력으로 코드 무수정을 확인했다.
- `sed -n '3p'` — `> 상태: 검토` 유지. `grep -nE '변경이력|변경 이력|Changelog'` 적중 0건. `grep -cE '^\| Q-[0-9]'` → 9.

## 회고적 학습 후보

.opal/brain/pages/concept/skip-gate-key-must-include-execution-identity.md

## 참고

- **제안서 아카이브 이관은 하지 않는다.** `harness/proposal-lifecycle.md`의 발동 조건(`changed_files`에 `docs/proposals/` 포함)에는 해당하나, 이 태스크는 제안을 **소비**한 것이 아니라 제안서 자체를 개정했다. 같은 문서 §상태 어휘가 `검토`를 `docs/proposals/`에 두도록 규정하므로 상태·위치를 그대로 유지한다. 참고로 잔여 인용 판정 명령(`opal/ docs/ skills/ README.md`, archives·backup·tasks 제외)은 적중 0건이다 — 채택 후 이관 시점에 걸림돌이 없다.
- **`docs/PROJECT.md` 갱신 없음.** 문서 레지스트리가 `docs/proposals/`를 Glob 단위로 등재하고 있어 이번 개정으로 레지스트리 내용이 달라지지 않는다.
- **제안 자체는 여전히 미채택이다.** 이 태스크는 착수 판단에 필요한 정보를 문서에 갖춘 것이며, Q-1·Q-6·driver 적합성 스위트·증적 마스킹 보강 4건은 채택 시 선행 과제로 남는다.
