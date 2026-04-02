# DONE: wtm 스킬 개선 — Playwright MCP 전환 + browser 모드 + PM 사전 수집 패턴

> 완료일: 2026-04-02 | 적용 스킬: opp

## 변경 파일

- `skills/web-to-markdown/SKILL.md` (v1.3 → v1.4)

## 변경 요약

| # | 항목 |
|---|------|
| W1 | Phase 2 Crawl4AI → Playwright MCP 전환. Phase 3 Node Playwright 삭제. |
| W2 | `browser` 모드 추가. localhost/127.0.0.1/[::1] 자동 감지. |
| W3 | 복수 URL 처리에 PM 직접 순차 수집 패턴 추가. |

## 배포 대기

- `install-mac.sh` 실행으로 `~/.opal/skills/web-to-markdown/SKILL.md` 동기화 필요 (캡틴 판단)
