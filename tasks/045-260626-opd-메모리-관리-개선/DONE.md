# DONE: 메모리 관리 체계 개선 — 토큰 효율·라이프사이클 집행 + memory-tool 신설

> 완료일: 2026-06-26 | 스킬: opd (agentic) | 태스크: 045
> 입력: TASK.md · ANALYSIS.md · PLAN.md(개정) · TEST-SCENARIO.md · AGENTIC-LOG.md

## 작업 목표 (달성)

OPAL 메모리 관리 체계를 **토큰 효율 + 라이프사이클 집행** 관점에서 개선. `memory-learning.md`(SSOT)를 개정하고 신규 `memory-tool`로 형식·정리·이관을 결정론적으로 집행. 핵심은 **메모리 → docs/brain 졸업 워크플로우** + **자가검토 ambient 트리거**.

## 산출물

### 신규
- `opal/tools/memory-tool/` — run.sh + memory_tool.py + schema/ + tests/ + README.md
  - **9 서브명령**: init · append · update(+`--new-title`) · promote(`--to docs|brain`) · prune · migrate · show · review · **delete**
  - state-tool 패턴 재사용(ok/err/ERROR_CODES/마커가드/run.sh), 표준 라이브러리만

### 수정
- `opal/core/references/harness/memory-learning.md` — 제목 컬럼·길이캡(요약 ≤80자·핵심결과 ≤2줄)·FIFO 10→5·라이프사이클 4상태(active/promoted/superseded/dead)·이관 워크플로우(라우팅 표)·자가검토 트리거·마커 규약 (v1.1)
- `opal/skills/opal-project-init/SKILL.md` — MEMORY.md 템플릿 신포맷(마커·제목 컬럼·FIFO5)
- `scripts/install-mac.sh` — memory-tool run.sh chmod 등록
- `opal/core/references/opal-harness.md` §9 + `opal/core/references/tools.md` — memory-tool 행/섹션(9서브명령) drift 정합

## 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | 메모리 갯수 상한 **제외** (캡틴 지시) | 비대화 방지는 졸업·자가검토·길이캡이 담당. 갯수 게이트는 불필요 강제 |
| 2 | 히스토리만 FIFO=5 자동 정리, 메모리는 blind 삭제 금지 | 히스토리=소모성 로그 / 메모리=지식(무손실) |
| 3 | 졸업 라우팅: docs=규범(행동 지배) / brain=설명(WHY·HOW) | 메모리 유형이 기본 졸업지 힌트 |
| 4 | 자가검토 = 매 변경 명령 응답에 `review` 블록 자동 첨부 | 캡틴 안 — CLOSE 훅 불요, ambient 강제 (8 pilot 미변경) |
| 5 | 역할 분담: 도구=집행(행·파일·provenance) / PM=판단(성숙·졸업지) | self-confirming 회피 + 무손실 |

## 검증 (TEST: All Pass)

- memory-tool pytest **88 passed** (초기 65 + 추가작업 delete/new-title 19 + 버그 회귀 3 + 전제 1)
- 회귀 **426 passed / 2 failed**(pre-existing state-tool·test-tool, 043 이전·045 무관)
- 보안 Pass(promote 경로 화이트리스트 이중 차단·ReDoS 8정규식·시크릿 0)
- RED-first 전 구간 적용(작성자 opal-test-agent ≠ 구현자 opal-be-agent), 테스트 불변 가드

## 추가작업 + 버그 (캡틴 지시·지적)

1. **추가작업**: `delete`(dead/superseded만 제거, 무손실 가드 `delete_requires_dead_or_superseded`) + `update --new-title`(migrate crude 제목 보정) — 이관 워크플로우 "삭제" 다리 완결
2. **🐛 버그 수정**: delete/promote `--with-file`이 migrate 백틱 file 필드(`` `memory/x.md` ``)를 못 풀어 실파일 미삭제(orphan) → `_resolve_memory_file` strip 1줄 수정. fixture-vs-real 맹점(039/044 교훈 반복), PM 직접 재현 검증

## 라이브 적용 (S-26 실증)

- 캡틴 install 재배포 후 실 `.opal/MEMORY.md` 정리: migrate → delete(promoted/dead/superseded/dangling) → 제목·요약 보정
- **17,248 → 7,535 bytes (56% 감소)**, 인덱스 6→2행, 인덱스↔파일 정합, review violations 0
- 백업: `/tmp/MEMORY_045_backup.md` + git

## 후속 (캡틴)

- **install 재배포** — delete·`--new-title`·백틱 수정이 배포본에 미반영(캡틴 직전 배포는 그 이전). 재배포로 동기화. 소스가 SSOT
- **커밋** — 미수행(지시 대기)
- `Console 브레인 구독 인증` 메모리 → brain 졸업(선택, brain authoring 필요)
- ruff가 `~/.opal/.venv` 미설치 — lint 검증 불가(비차단), venv ruff 설치 검토
- 히스토리 5행 [REVIEW] 잔존 — 행 편집 명령 부재, FIFO로 자연 정리(045부터 ≤2줄)
