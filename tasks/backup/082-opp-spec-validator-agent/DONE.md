# DONE: SDD 명세 검증 전용 에이전트 분리

> 완료일: 2026-04-03 | 태스크: 082

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/op-spec-validator/SKILL.md` | 신규 생성 — P1~P6/T1~T5 이관 + opsdd 연동 가이드 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | 1-1b: "PM 직접 수행" → "op-spec-validator 디스패치" 방식으로 교체 |
| `opal/core/references/opal-skills-registry.json` | op-spec-validator 항목 추가 (alias 없음, 디스패치 전용) |
| `~/.opal/references/opal-skills-registry.json` | 배포 레지스트리 동기 |

## 결과

- `op-spec-validator`: OPAL 전용 워커 스킬 (alias 없음, 오케스트레이터 디스패치 전용)
- oppd 1-1b 흐름: PM 직접 판정 제거 → 에이전트 위임
- opsdd 구현 시 동일 에이전트 재사용 가능 (SKILL.md에 연동 가이드 포함)
