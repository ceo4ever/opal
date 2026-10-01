# TASK: AGENTIC-LOG 시간순 덧붙이기 규칙

- 실행 형태: `//oppm`(PM 직접 수행) — 캡틴 지시 "직접 수정해줘"(2026-10-01, 허브 세션)
- 실행 ID: `run_13736313-42a3-4d1a-9f9b-9180c8086cb1`
- 기록: `self-pm-tool`(이 폴더), `run-log-tool`(이 폴더 `run/`)

## 요청과 배경

태스크 170에서 AGENTIC-LOG.md에 새 기록을 덧붙일 때 편집 앵커를 마지막 항목이 아닌 중간 항목으로 잡아 #13이 #9보다 앞에 들어갔고, 사후에 순서를 재정렬했다(`fd2fa3cb` "AGENTIC-LOG 순서 정정"). 170이 이 교훈을 메모리로 요청했으나 본문 파일이 생성되지 않아 반영되지 못했다(`tasks/170-261001-opds-설계-게이트-회차-단축/memory-index-request.json`, body_sha256이 빈 본문 해시). 캡틴은 메모리 대신 규칙으로 바로 반영하기로 결정했다.

## 작업 계약(6항목)

1. 목표·완료 조건: AGENTIC-LOG 기록 규칙의 원문에 "시간순 덧붙이기" [MUST] 규칙 1개가 추가되고, agentic·semi-agentic 두 모드에 적용된다.
2. 포함·제외: 포함 — `opal/core/references/opal-harness-agentic.md` §8 기록 의무 규칙. 제외 — 도구 집행(로그 번호 순서 검사), 170 메모리 본문 복원, 다른 로그(brain log·STATE.md 저널).
3. 변경 대상: `opal/core/references/opal-harness-agentic.md` 1개 파일.
4. 결정·가정: 원문은 agentic §8 한 곳(semi-agentic은 `opal-harness-semi-agentic.md` §7 "생성 이후 기록 방식은 opal-harness-agentic.md §8 동일"로 참조). 기존 행 수정 금지·정정은 새 기록, "요약" 표 갱신만 예외. 남은 가정 없음.
5. 검증 방법: 규칙 문구 존재 grep, semi-agentic 참조 유지 확인, `git diff`로 변경 범위가 해당 절 1곳인지 확인, `code-scan validate --changed`.
6. 예상 영향: 프로젝트 문서·CONVENTIONS 영향 없음 예상(AGENTIC-LOG 기록 규칙의 owner는 하네스), brain은 규범 변경이라 WHY 기록 필요 여부 판정, memory는 170 미반영 요청과의 관계 기록.

승인 근거: 캡틴이 문구 초안(시간순 덧붙이기·편집 직전 재Read·마지막 번호+1·기존 행 수정 금지·요약 표 예외)과 반영 위치를 검토 응답으로 받은 뒤 "직접 수정해줘"로 지시했다. 커밋 여부는 직전 질문("반영하고 커밋까지 할까요?")에 대한 같은 응답으로 승인되었으나, 허브 `main` 커밋은 최종 확인 후 수행한다.

## 참조 문서와 제약

- `opal/core/references/opal-harness-agentic.md` §8 AGENTIC-LOG.md (기록 의무 규칙 174~178행) — 변경 대상 원문.
- `opal/core/references/opal-harness-semi-agentic.md` §7 — 원문 참조 관계 확인용.
- `docs/CONVENTIONS.md` §파일 구조 §태스크 산출물 구조(162행 `AGENTIC-LOG.md agentic 실행 로그`) — 산출물 목록, 기록 규칙은 소유하지 않음.
- [MUST] `.opal/AGENT.md` §금지사항: `~/.opal/` 직접 수정 금지(배포는 캡틴이 install로 수행), 수기 누적 이력 절 생성 금지.

## 영향 후보 집합

| 대상 | 선별 근거 | 예상 영향 | 상태 |
|---|---|---|---|
| `opal/core/references/opal-harness-agentic.md` | 기록 규칙 owner | 규칙 1개 추가 | pending |
| `opal/core/references/opal-harness-semi-agentic.md` | §7이 agentic §8을 참조 | 참조 유지(무변경) 확인 | pending |
| `docs/CONVENTIONS.md`·`docs/PROJECT.md` | 산출물 목록·레지스트리 | 규칙 미소유, 변경 불필요 예상 | pending |
| `.opal/brain` | 규범 변경의 WHY | 170 사건 근거로 판정 | pending |
| `.opal/MEMORY.json` | 170 미반영 메모리 요청 | 규칙 반영으로 대체됨을 기록 | pending |
