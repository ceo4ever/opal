# DONE: AGENTIC-LOG 시간순 덧붙이기 규칙

> 상태: 완료(캡틴 최종 확인 2026-10-01)

## 결과

`opal/core/references/opal-harness-agentic.md` §8 "기록 의무 규칙"에 `[MUST] 시간순 덧붙이기` 1개를 추가했다. 새 엔트리는 `## 대행 일지` 표의 마지막 행 바로 뒤에만 추가하고, 편집 직전에 파일을 다시 읽어 마지막 번호를 확인해 1을 올린다. 기존 행 사이 삽입·기존 행 수정을 금지하고, 정정도 새 엔트리로 남긴다. "요약" 표 갱신만 예외다. semi-agentic 하네스는 §7에서 이 절을 그대로 참조하므로 두 모드에 함께 적용된다.

## 변경 파일

- `opal/core/references/opal-harness-agentic.md` (+1행, §8 기록 의무 규칙)
- `tasks/171-261001-oppm-AGENTIC-LOG-시간순-덧붙이기-규칙/` (TASK.md·DONE.md·실행 기록)
- `.opal/MEMORY.json` (채번 `last_task_number` 170→171)

## 검증

| 방법 | 결과 |
|---|---|
| `grep -n "시간순 덧붙이기" opal/core/references/opal-harness-agentic.md` | 179행에 규칙 존재 |
| `grep -n "opal-harness-agentic.md §8" opal/core/references/opal-harness-semi-agentic.md` | 93행 참조 유지 |
| `git diff --unified=0 opal/core/references/opal-harness-agentic.md` | `@@ -178,0 +179 @@` 1행 추가, 다른 절 무변경 |
| `code-scan validate --changed opal/core/references/opal-harness-agentic.md` | OK |
| GC 컨벤션 검사 | 미호출 — 문서 1행 추가로 위 기계 검증이 충분 |
| opal-e2e | 미적용 — 실행 표면이 없는 규범 문서 변경 |

## 지식 동기화(8영역)

| 영역 | 판정 | 근거 |
|---|---|---|
| 기획 | no-op | FW 실행 규칙 변경, 기획 산출물 대상 아님 |
| 설계 | no-op | `docs/ARCHITECTURE.md`에 AGENTIC-LOG 언급 0건 |
| 프로젝트 문서 | no-op | `docs/PROJECT.md` 언급 0건, 레지스트리 변경 불필요 |
| CONVENTIONS | no-op | `docs/CONVENTIONS.md:162`는 산출물 목록만 소유 |
| SECURITY | no-op | 보안 기준 무관(`docs/SECURITY.md` 언급 0건) |
| brain | 보류 | 규범 변경 WHY(170 사건) 기록 필요. 기존 `concept/self-edit-line-anchor-drift`는 검증 앵커 행번호에 관한 다른 WHY. 허브 brain을 다른 세션이 동시 수정 중이라 충돌 방지를 위해 캡틴 결정 대기 |
| memory | no-op | 170 메모리 요청은 본문 부재로 반영 불가, 이 규칙이 그 교훈을 대체 |
| code-scan | no-op | validate OK, 코드맵 영향 없음 |

## 미해결·후속

- brain WHY 기록(위 보류 항목).
- 허브 작업본에 이 태스크와 무관한 brain 변경 276개 파일(`related` 표기 일괄 변환 등, 12:37:29부터)이 있다. 이 태스크 커밋에서 제외한다.
- 배포(install 재실행)는 캡틴이 수행한다.

## 사용자 확인

캡틴 확인("커밋 해줘"). brain WHY 기록은 응답이 없어 보류로 남기고 후속 작업 목록에 등록했다.
