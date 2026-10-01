# EXECUTE W-5 — 161/162/167 누락 brain 후보 허브 백필 보고

## 건드린 정확한 경로 (허브 `/Volumes/Data/AiStudio/workspace/opal` 기준 상대경로)

- `.opal/brain/pages/flow/test-cycle-early-human-handoff.md` (신규, task:162)
- `.opal/brain/pages/concept/scenario-economy-advisory-gate.md` (신규, task:167)
- `.opal/brain/pages/entity/test-tool.md` (갱신, task:161 + task:167 병합 반영)
- `.opal/brain/pages/concept/scenario-goal-coverage-gate-loop.md` (갱신, task:167)
- `.opal/brain/pages/entity/op-scenario-gate-skill.md` (갱신, task:167)
- `.opal/brain/pages/entity/state-tool.md` (갱신, task:167)
- `.gitattributes` (갱신 — 4줄 추가)
- 부수 산출물(brain-tool 자동 갱신, 사람 편집 아님): `.opal/brain/index.md`, `.opal/brain/log.md`, `.opal/MEMORY.json`(`last_task_number` 167→170, `--allocator-root` 지정 add-page 2건·update-page 4건 호출에 따른 도구 내부 번호 예약 부작용으로 관측됨 — 이번 작업이 직접 편집한 필드 아님)

## 경고

이 백필은 `.gitattributes` 4줄을 포함해 허브 작업트리에 파일로만 쓰여 있고 아직 커밋되지 않았다 — 이 묶음을 먼저 커밋한 뒤에만(그래야 log.md·index.md의 merge=union이 활성화된다) 태스크 169를 포함해 어떤 브랜치든 허브 main에 merge하라.

## 실행한 brain-tool 명령 요약

- `add-page pages/flow/test-cycle-early-human-handoff.md --type flow ...` → `ok: true`
- `add-page pages/concept/scenario-economy-advisory-gate.md --type concept ...` → `ok: true`
- `update-page pages/entity/test-tool.md ...` → `ok: true` (updated_fields: tags, sources, related, body)
- `update-page pages/concept/scenario-goal-coverage-gate-loop.md ...` → `ok: true` (updated_fields: sources, related, body)
- `update-page pages/entity/op-scenario-gate-skill.md ...` → `ok: true` (updated_fields: sources, related, body)
- `update-page pages/entity/state-tool.md ...` → `ok: true` (updated_fields: sources, related, body)
- `index --brain-path /Volumes/Data/AiStudio/workspace/opal` → `ok: true` (pages_scanned: 384)
- `log --op ingest --brain-path /Volumes/Data/AiStudio/workspace/opal --summary "CLOSE 누락 백필 — 태스크 161·162·167 brain 후보 반영" --new "<2개 신규 경로>" --updated "<4개 갱신 경로>" --sources "task:161,task:162,task:167"` → `ok: true`

## 내용 반영 근거

각 태스크의 DONE.md·PLAN.md를 직접 읽어 다음 결정을 본문에 반영했다.

- **task:161** (검증 도구 실행 정확성 복구): `test-tool unit`의 `check`(설치 확인)/`run`(실제 검사) 분리, 계층 상태 폐쇄 목록(pass/fail/tool_unavailable/not_configured/not_applicable/not_run), 전체 status(pass/fail/incomplete), 파일 단위 검사(`run_files`/`file_globs`) — `test-tool.md`에 반영.
- **task:162** (TEST 단계 소요시간 단축): 사람 협업 선요청+자동 검사 병행, fix/requirement_change 분리 계측, `test-clock`/`test-metrics` 실제 사건 시각 계측, `worktree-tool divergence` 분기 선확인, 영향 범위 재검증+최종 전체 회귀 — `test-cycle-early-human-handoff.md`(신규)에 반영.
- **task:167** (테스트 시나리오 작성 기준 개선): 유형 열 전달·check+RED 모순 차단·정확 중복 차단, evaluator `advisories[]` 계약과 ID 단위 응답 게이트, advisory 반영 refinement(상한 비소비), `scenario-gate-record`/`scenario-gate-verify` 신설과 `state-tool mark` 가드 — `scenario-economy-advisory-gate.md`(신규), `scenario-goal-coverage-gate-loop.md`·`op-scenario-gate-skill.md`·`state-tool.md`(갱신)·`test-tool.md`(갱신, 161과 병합)에 반영.

## 검증

- brain-tool 6개 페이지 호출 전부 `ok: true` 확인(위 요약 참조).
- `index`·`log` 각 1회 `ok: true` 확인.
- `cd /Volumes/Data/AiStudio/workspace/opal && git status --short` 결과:
  ```
   M .gitattributes
   M .opal/MEMORY.json
   M .opal/brain/index.md
   M .opal/brain/log.md
   M .opal/brain/pages/concept/scenario-goal-coverage-gate-loop.md
   M .opal/brain/pages/entity/op-scenario-gate-skill.md
   M .opal/brain/pages/entity/state-tool.md
   M .opal/brain/pages/entity/test-tool.md
  ?? .opal/brain/pages/concept/scenario-economy-advisory-gate.md
  ?? .opal/brain/pages/flow/test-cycle-early-human-handoff.md
  ```
  이 목록은 이번 작업이 변경한 파일과 정확히 일치한다(다른 미커밋 변경과 섞이지 않음). `.gitattributes`는 요청된 4줄만 파일 끝에 추가했다(바이트 확인: 빈 줄 1 + `# brain 공유 파일 merge 전략` + `.opal/brain/log.md merge=union` + `.opal/brain/index.md merge=union`).
- 커밋하지 않았다 — 허브 작업트리에 파일로만 남아 있다.
