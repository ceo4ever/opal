# DONE: OPAL Project Brain — 프로젝트 지식 위키 시스템 (코어)

> 완료일: 2026-06-11 | 스킬: opp | 모드: agentic | 상태: 코어 완료 (지능화·배포는 016 이월)

## 완료 산출물

### 신규 (5)
- `opal/tools/brain-tool/` — 지식 위키 결정론적 집행 CLI (Python, 8 서브명령 + 4 페이지 템플릿 + 66 단위테스트)
- `opal/skills/opal-brain/` — 단일 pilot 4모드(init/ingest/query/lint) 스킬 + references
- `opal/skills/op-brain-ingest/` — CLOSE 자동 ingest 경량 워커
- `docs/proposals/opal-brain-design.md` — 설계 SSOT (13절)
- `.opal/brain/` — 현 프로젝트 brain 시드 (entity 2 + concept 1, validate/lint clean)

### 수정 (8)
- `opal/core/AGENT.md` — Lazy 트리거 + opal-brain 활용 규칙(code-scan 동형)
- `opal/core/references/pm/dispatch-process.md` — brain 사전 참조 단계
- `opal/core/references/opal-skills-registry.json` — opal-brain·op-brain-ingest 등록
- `opal/core/references/opal-harness.md` — §9 brain-tool 도구표
- `opal/skills/opal-pilot-project/SKILL.md` — CLOSE 자동 ingest 훅 (STATE 9행 불변)
- `scripts/install-mac.sh` — brain-tool chmod
- `docs/PROJECT.md` — Project Brain 컴포넌트
- `.opal/MEMORY.md` — 채번

## 검증 결과

| 항목 | 결과 |
|------|------|
| brain-tool 단위테스트 | 66 passed |
| PM 독립 실행 검증 | 8커맨드 happy/error 정상 |
| brain 시드 | validate valid / lint 0 / sync-header drift 0 |
| STATE 9행 정합 | rows_count 9 유지 (회귀 없음) |
| 레지스트리 JSON | 유효 |

## 요구사항 충족 (R1~R7)

- R1 brain-tool ✅ / R2 SCHEMA ✅ / R3 스킬+레지스트리 ✅ / R4 PM 융합 ✅ / R5 CLOSE 훅 ✅(opp 파일럿) / R6 외부소스 ✅ / R7 배포코드 ✅ + brain 시드 ✅

## 016 이월 (wiki 지능화 — 캡틴 명확화)

태스크 016 `opp`로 진행:

1. **init 동적 구조 제안** — origin(docs/tasks/소스) 분석 → 프로젝트별 최적 wiki 도메인·구성 제안 (페이지 타입 4종 고정 + 도메인·카테고리 동적)
2. **ingest --all 문서 전체** — code-scan @header(코드)뿐 아니라 docs·스킬·참조(.md) 전체를 요약 페이지로 적재 (origin=SSOT, wiki=요약+참조 파생, 단방향)
3. **tasks 장기기억 통합** — MEMORY(단기 FIFO) → brain(장기 검색) → tasks/(장기 원본) 3계층. 기존 001~015 소급 백필 + `task:NNN` drill-down
4. **ingest 3트리거** — 태스크 종료(자동, 구현됨) + 사용자 요청(구현됨) + **PM 판단(신규, 모드 연동: agentic 자율/그 외 제안)**
5. **search 4시점** — 작업·분석·설계 전 / 워커 디스패치 시 / 사용자 질의 / 부트스트랩 (R4 기반 강화)
6. **전체 pilot CLOSE ingest 확산** — opp 파일럿(015) → 나머지 7 pilot
7. **install 통합 배포** — 016 코드 완료 후 install 실행 (brain-tool·스킬 글로벌 배포, //opbr 매칭 활성화). 이름 정리(opal-brain vs opal-wiki) 포함

## Known Issue / 잔여

- 실제 install 미실행 — brain-tool·스킬이 `~/.opal`에 미배포 (016 통합 배포 예정). 현재는 소스 경로로 동작.
- CLOSE 자동 ingest는 opp만 (나머지 pilot 016 확산).

> 상세 PM 대행 일지: `AGENTIC-LOG.md`
