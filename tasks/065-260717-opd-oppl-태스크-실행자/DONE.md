# DONE: oppl 태스크 실행자(opal-loop-action-agent) 도입 — 태스크 단위 컨텍스트 격리

> 완료일: 2026-07-17 12:54 | 스킬: //opd (agentic) | 태스크: 065

## 요약

oppl Loop 2의 태스크 내부 파이프라인(T1~T5+G)을 태스크당 1회 디스패치되는 일회용 실행자 `opal-loop-action-agent`에 위임했다. PM은 L0 태스크 선택·L∞ 관찰·done-check·사람 게이트·소유자 보고를 유지하고, 태스크당 노미널 4~5회였던 PM 개입이 결과 보고 1건으로 압축되어 롱런 워크플로우의 PM 컨텍스트 누적이 태스크 단위로 격리된다.

## 완료 기준 대비 결과 (TASK.md §명확화 결과)

| 완료기준 | 결과 |
|---------|------|
| ① AGENT.md 존재 + 입력·파이프라인·계약 정의 | ✅ `opal/agents/opal-loop-action-agent/AGENT.md` (163줄, S-1~S-4 검증) |
| ② SKILL.md 실행자 1회 디스패치 구조 개편 | ✅ 11지점 + idiom + PM 소유 불변 (v1.2, S-5) |
| ③ 실행자 디스패치 실증 | ✅ S-7 완주(순서 evidence·tool-gated red 2/2·pass 2/2) + S-8 blocked |
| ④ 상한·에스컬레이션 계약 문서 명시 | ✅ harness §1 포인터(리터럴 0)·blocked 7종 트리거 (S-2·S-3) |

## 변경 파일 (프로젝트 소스만 — ~/.opal/ 미접촉)

| 파일 | 변경 |
|------|------|
| `opal/agents/opal-loop-action-agent/AGENT.md` | 신규 — 실행자 정의 v1.0 (+G단계 QA-SPEC 산출 의무 fix) |
| `opal/skills/opal-pilot-project-loop/SKILL.md` | v1.2 — 실행자 위임 개편 11지점 + 루프제어 §2 예산 문구 정합 |
| `opal/skills/opal-pilot-project-loop/references/loop-control.md` | v1.1 — §3 예산 실행자 1회 기준 |
| `opal/skills/opal-pilot-project-loop/references/contract.md` | v1.1 — §4 실행자 경계(직접수정 금지·drift blocked) |
| `docs/PROJECT.md` / `docs/ARCHITECTURE.md` | 실행자 행 + 변경이력 |
| `tasks/065-*/samples/` | 실증 fixture 2종 + 실증 산출물(증거 5종) |

verification.md는 주체 중립 확인 후 무변경(M-10).

## 검증

- TEST-SCENARIO.md 종합 판정 **All Pass (S-9 제외 8/8)** — L1 6/6(test-agent 독립) + L2 2/2(실 디스패치 실증) + 품질·보안 Pass
- fix 루핑 1회: QA-SPEC 산출 의무 누락(규정 구멍) → AGENT.md 보강 → 재실증 Pass
- 상세 과정: AGENTIC-LOG.md (게이트 판단·오류·폴백 승인 전체 이력)

## 미완료·후속

| # | 항목 | 성격 |
|---|------|------|
| 1 | **S-9 install 배포** — `./scripts/install-mac.sh` 실행(스크립트 수정 불필요 확인됨). 배포 전까지 실행자는 신규 세션 oppl에서 미등록 상태 | 사람 게이트 — 캡틴 승인 대기 |
| 2 | 실행자 내부 비동기 릴레이 마찰 — 부모 턴 조기 종료 반복, PM 재개 지시로 커버. AGENT.md/SKILL.md 릴레이 지침(동기 완주 또는 결과 파일 경유) 보강 | 후속 태스크 후보 |
| 3 | 워커 산출물 파일 검증 의무(Write 후 자체 확인) 프레임워크 SSOT 반영 — ANALYSIS 워커 파일 미저장 2회 재발 방지 | 후속 태스크 후보 |
| 4 | oppl 세션 관리 A(--resume 재개 프로토콜)·컨텍스트 감지 자동화 | 보류 — 캡틴 추가 검토 예정 |
| 5 | opal-evaluator-agent 등 내부 워커의 플랫폼 subagent_type 등록 여부 점검 (실증에서는 AGENT.md 주입으로 대체) | 후속 확인 |

## 커밋

미수행 — 커밋 규칙(사용자 명시 요청 시에만).
