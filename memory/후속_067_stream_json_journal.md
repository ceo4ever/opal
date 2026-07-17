# 후속 태스크 067 — opal-agent stream-json 개조 + journal 규약

> 등록: 2026-07-17 | 유형: task | 상태: active | 출처: 066 CLOSE 시 캡틴 확정

## 내용

캡틴 확정(066 CLOSE 시 AskUserQuestion): 루프 액션 에이전트 투명 모니터링 완전판.

1. **opal-agent stream-json 모드 개조**: `claude --output-format stream-json` 지원 — 블로킹 `subprocess.run` → 스트리밍 실행, `events.jsonl` 증분 기록, 최종 result 이벤트에서 5필드 추출. 이벤트 스키마 실측 검증 필요.
2. **결과 파일 규약 v2**: 066의 `.oppl-run/<phase>.result.json` 3-분리 → events.jsonl 편입 개정 (`opal/agents/opal-loop-action-agent/AGENT.md` §결과 파일 규약).
3. **journal 규약**: 루프 액션 에이전트 자신의 판단 일지(`.oppl-run/journal.md` — 게이트 판단·재시도 사유·단계 전환). stream으로 대체 불가(워커 이벤트가 아닌 루프 액션 에이전트 행동).

## 배제 (설계 논의 결론)

- 3종 경량판(heartbeat·prompt 규약·journal) 중 heartbeat/prompt는 stream-json이 상위 호환이라 건너뜀 — journal만 유효.
- "실행 중 에이전트 직접 질의" 채널은 배제 — 파일 경유(PM이 journal/events를 읽고 답변)로 릴레이 마찰 회피.

## 추가 백로그 (066 DONE.md §후속)

- 레포 `.gitignore`에 `.oppl-run/` 반영 (커밋 시)
- oppl 풀 런 실전 검증 + 구독 rate limit 실측(R-4)
