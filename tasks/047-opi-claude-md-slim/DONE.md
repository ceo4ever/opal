# DONE: 플랫폼 파일 슬림화 + PM 컨텍스트 로드 최적화

> 완료일: 2026-03-30

## 변경 요약

### 수정
- **CLAUDE.md** — 203줄 → 20줄 슬림화 (부트스트래퍼 + docs/ 참조 포인터만 유지)
- **opal/core/AGENT.md** — PM 컨텍스트 로드에서 CONVENTIONS.md 자동 Read 제거 (PROJECT.md만 자동 로드, 나머지는 PM이 필요 시 Read)

### 효과
- CLAUDE.md 컨텍스트 소비: 203줄 → 20줄 (90% 감소)
- 부트스트랩 흐름: CLAUDE.md → AGENT.md → PROJECT.md → PM이 필요 docs/ 선택적 Read
- 정보 손실 없음 (docs/에 모든 정보 존재)
