# 검증 증거

## 재현 조건

- 실행일: 2026-09-28 KST
- 작업 디렉터리: `/Volumes/Data/AIStudio/workspace/ai-framework`
- 대상: `opal/skills/op-task/` 문서 3개
- 변경 유형: TASK 작성 규범 문서 변경, 런타임 코드 변경 없음

## V-1 관련 계약 테스트

```bash
~/.opal/.venv/bin/python -m pytest \
  opal/tools/state-tool/tests/test_state_tool_verification_gates.py \
  opal/tools/state-tool/tests/test_state_tool_extended_contracts.py \
  -q -k 'clarification'
```

- 기대: sdlc-v2 TASK 필수 절과 AC/C 식별자 관련 기존 계약 회귀 없음
- 관측: `13 passed, 158 deselected in 0.19s`
- 판정: PASS

## V-2 전체 관련 파일 테스트 참고

동일한 두 테스트 파일 전체를 실행한 결과 `169 passed, 30 subtests passed, 2 failed`였다.
실패 2건은 현재 Codex 세션 ID가 실제로 존재하는 환경에서 `session_id is None`과 lease 미생성을
기대하는 테스트로, 변경 문서와 무관하다.

- `TestT138W9OwnershipClaimBoundary::test_session_env_absent_skips_claim_without_blocking`
- `TestT138W9ActorSessionId::test_session_id_stays_none_without_env`

## V-3 문서 계약 정적 검사

```bash
git diff --check
rg -n '출처성|필수성|관찰성|해법 독립성|비중복성|같은 요구를 unit|AC가 아닌 정보의 위치' \
  opal/skills/op-task/references/task-guide.md
```

- 기대: whitespace 오류 없음, 다섯 채택 조건·중복 금지·라우팅 기준 존재
- 관측: exit 0, 필수 문구 전부 확인
- 판정: PASS

## V-4 code-scan 완료 게이트

```bash
~/.opal/tools/code-scan/run.sh validate \
  --changed 'opal/skills/op-task/references/task-guide.md,opal/skills/op-task/SKILL.md,opal/skills/op-task/README.md' \
  --json
```

- 관측: exit 0, `ok:true`, `newly_uncovered:0`, 세 파일은 모두 `pre_existing`
- 판정: PASS — 기존 헤더 미보유 문서의 비차단 계약

## V-5 태스크 164 적용 점검

새 기준으로 기존 AC를 재분류했다.

- AC-3·AC-4·AC-8: 동일한 쓰기 권한 요구를 명령 구성·실측·설치본 검증 단계로 나눈 중복 → 핵심 AC 1개와 환경별 시나리오로 통합
- AC-2: 공통 경로 계산은 PLAN 구현 결정, 구 구조 비채택만 AC 결과로 유지
- AC-7: 문서 동기화 Work item으로 이동
- AC-5·AC-6: 기동 전 차단/경고라는 하나의 독립 수용 결정으로 통합 가능

- 판정: 다섯 채택 조건과 비중복 검사가 실제 중복·오배치를 구분함

## E2E 적용 검토

- 미실행
- 이유: 런타임 코드·API·화면·통합 동작을 바꾸지 않는 TASK 작성 규범 문서 변경이다.
- 대체 검증: 관련 상태 도구 계약 테스트, 정적 문구 검사, code-scan validate, 기존 TASK 재분류 적용 점검
- 미검증 범위: 실제 다음 TASK 작성 세션에서 PM이 의미 중복을 올바르게 판단하는지에 대한 장기 사용 관측

## V-6 brain 동기화

```bash
~/.opal/tools/brain-tool/run.sh add-page pages/concept/ac-core-acceptance-requirement.md \
  --type concept --title 'AC는 비중복 핵심 수용 요구사항이다' \
  --tags 'task,requirements,workflow' --sources 'task:165' \
  --body-file tasks/165-260928-oppm-AC-핵심-요구사항-작성-기준/evidence/brain-concept-body.md \
  --brain-path .opal/brain --allocator-root /Volumes/Data/AIStudio/workspace/ai-framework
```

- 관측: `ok:true`, concept 페이지 생성 및 index 등록 성공
- 후속: `update-page`로 `status: active`, `related: [op-task]`를 확정하고 본문에 `[[op-task]]` 연결을 추가했다.
- 검색: `brain-tool search '요구사항'`에서 새 concept가 첫 결과로 반환됐다.
- lint: 전체 brain의 기존 이슈와 분리해 확인했으며, 새 페이지 관련 이슈는 0건이다.
- 색인·로그: `brain-tool index` 382페이지 스캔 성공, `brain-tool log --op ingest` 성공
- 판정: PASS
