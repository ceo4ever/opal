# STATE: 검증도구-실행정확성-복구

> 최종 갱신: 2026-09-27 20:10:34
> 파이프라인 현황(rows/상태/다음 액션)의 SSOT는 `state.json`입니다.
> 조회: `~/.opal/tools/state-tool/run.sh show <task-path>`

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | 2026-09-27 07:46:15 | design-decision(external): test-tool unit 공개 결과 계약 변경: 계층 상태 6종·전체 상태 pass/fail/incomplete, incomplete=exit 21(unit_incomplete), run 없는 구형 설정은 명령 미실행+incomplete(자동 이관 없음), 정식 설치는 소스 검증 뒤 작업본에서 사용자 승인 후 수행 | PLAN.md D-2·D-4·D-6·D-9·D-11. TASK C-2·AC-2·AC-8이 요구를 고정했으나 상태값·exit·구형 설정 동작·공유 전역 배포 시점은 외부 동작·계약 결정(track-routing §2) |
| 2 | 2026-09-27 20:04:49 | current_status changed: blocked → in_progress | 캡틴 결정: 외부 설계 결정 A안 전부 채택(결과 상태·exit 21, 구형 설정 미실행+안내, 작업본 설치는 실행 직전 승인) |

## 블로커
없음
