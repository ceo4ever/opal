# DONE: opal-pm.md 다운사이징 — pm/ 폴더 분리 최적화

> 완료일: 2026-04-17 | 태스크: 124 | 스킬: opp | 모드: agentic

## 완료 요약

`opal-pm.md`(559줄)의 Lazy 분리 가능 섹션 6개를 `opal/core/references/pm/` 폴더 개별 파일로 추출하고, `opal-pm.md`를 **201줄**로 슬림화했다. Eager 로드 컨텍스트 **64% 절감** 달성.

## 변경 파일

| 파일 | 변경 | Before | After |
|------|------|--------|-------|
| `opal/core/references/opal-pm.md` | 수정 | 559줄 | 201줄 |
| `opal/core/references/pm/dispatch-process.md` | 신규 | - | §3 Step 0~7 전체 |
| `opal/core/references/pm/specialist-agent.md` | 신규 | - | §11 전문 에이전트 관리 |
| `opal/core/references/pm/orchestration.md` | 신규 | - | §10 통합 조율 |
| `opal/core/references/pm/code-scan-management.md` | 신규 | - | §9 code-scan 관리 |
| `opal/core/references/pm/self-improvement.md` | 신규 | - | §5.2 자기 개선 세부 |
| `opal/core/references/pm/context-injection.md` | 신규 | - | §6 컨텍스트 주입 원칙 |

## Lazy 트리거 정의

| 파일 | 트리거 |
|------|--------|
| `pm/dispatch-process.md` | 워커 디스패치 직전 |
| `pm/specialist-agent.md` | 전문 에이전트 디스패치 직전 |
| `pm/orchestration.md` | 다중 에이전트 배치 구성 시 |
| `pm/code-scan-management.md` | code-scan.json 갱신 필요 시 |
| `pm/self-improvement.md` | 태스크 완료 또는 소유자 피드백 수신 시 |
| `pm/context-injection.md` | 디스패치 전 컨텍스트 주입 상세 판단 필요 시 |

## 주요 결정

- §3(디스패치 전 프로세스, 125줄)을 소유자 추가 지시로 추출 → 목표 ~220줄 달성 가능해짐
- §8 워커 행동 규칙 → §7 말미 1줄 blockquote로 병합 후 삭제
- 변경이력 섹션 삭제
- 배포본 (`~/.opal/references/opal-pm.md`) 미수정 — 소유자가 `install-mac.sh`로 별도 배포

## 후속 작업

- [ ] `install-mac.sh` 실행하여 pm/ 폴더 배포본에 동기화 (캡틴이 결정)
- [ ] `~/.opal/AGENT.md` Lazy 트리거 테이블에 pm/ 파일 6개 등록 고려 (현재는 opal-pm.md stub으로 안내)
