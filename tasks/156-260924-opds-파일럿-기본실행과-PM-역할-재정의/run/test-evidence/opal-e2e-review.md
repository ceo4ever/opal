# S-12: opal-e2e 적용 검토

## 관측
- `.opal/e2e/` 내용: `README.md`, `order.json`, `drivers/ego-lite.json`만 존재. 등록된 여정(journey)·조각(fragment) 파일 없음 (`docs/e2e/journeys/`, `docs/e2e/fragments/` 부재).
- `opal-e2e` SKILL.md 모드: author(초안 작성) | run(`test-tool e2e run --scenario <journey-id>`) | status. `run`은 기존 journey-id를 전제로 하고, 이 태스크(156)를 위한 journey가 작성/승격된 바 없다.

## 판정
- **미실행(스킵)** — 이번 태스크는 신규 E2E 여정을 작성·승격하지 않았고, 대상 journey-id가 없어 `//e2e run`을 호출할 대상이 없다. 강제로 journey를 새로 author하는 것은 TEST 단계 범위(검증)를 벗어나 EXECUTE급 산출물 생성이 되므로 수행하지 않는다.
- 근거: opal-e2e는 "실행·판정·승격 자격은 test-tool이 소유"하는 별도 operator이며, TEST-SCENARIO S-1~S-11이 이미 실제 CLI(state-tool, worktree-tool, brain-tool, code-scan, git)로 전체 사용자 여정(신규 태스크 3축 판정 → worktree 격리 → 문서 계약 → 회귀 → 배포 후 검증 → 커밋 위생)을 실제 프로세스 실행으로 커버했다.

## 대체 검증 시나리오 ID
S-1, S-2, S-3, S-4, S-5, S-6, S-8, S-9, S-11 — 모두 실제 CLI subprocess/integration 실행으로 이번 변경의 종단 행동을 검증했으므로 opal-e2e 미실행의 대체 근거로 충분하다고 판단.
