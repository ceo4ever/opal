# ANALYSIS: ANALYSIS 분석 코어 공유 SSOT 신설 — 지식 선조회·확정 승계·중복 제거 (재생성)

> 작성일: 2026-08-24
> 입력: TASK.md
> 출력: ANALYSIS-REGEN.md
> 성격: 목표 달성 실측(R-12/AC-G) 대조용 재생성본 — 동일 TASK.md를 신규 절차(`op-dev-analysis/SKILL.md` v1.6 + `analysis-core.md`)로 재분석. 구 규범 산출물(ANALYSIS.md/ANALYSIS.baseline.md)·후속 산출물(PLAN.md 등)은 열지 않았다.
> 기록(PM): 워커가 Write 도구 차단(파일명 오탐)을 **우회하지 않고 텍스트로 반환**했고, PM이 그 본문을 그대로 이 파일에 기록했다. 내용 무편집.

## 확정 입력 판정

| 항목 | 판정 | 근거 |
|------|------|------|
| [결정] A~L·배치·역할분리·B흡수·측정·임계 (16건 전건) | 유효 | - |
| [사실] `verify --evidence-check`는 항목별 verdict·확정비율 반환 라우터, exit 0 유지 | 유효 | - |
| [사실] evidence-check 파싱 대상은 `## 명확화 결과` 표뿐 | 수정필요 | `opal/tools/state-tool/README.md:277` — 본 태스크 R-10이 파싱 대상을 확장해 TASK.md 진술과 현재 코드가 불일치. TASK 작성 시점엔 참이었으나 같은 태스크의 실행으로 갱신됨 |
| [사실] ANALYSIS는 `[결정]`만 재도출 면제, `[사실]`은 E1~E4 재확인 대상 | 유효 | - |
| [사실] PLAN의 ANALYSIS 재사용 지시는 `2.N.2`에만 있고 강도도 `[MUST]`가 아님 | 수정필요 | `opal/skills/op-dev-plan/references/plan-guide.md:92,98,102` — R-11이 `2.N.1`·`2.N.3`에도 `[MUST] 재도출 금지` 삽입 완료 |
| [사실] brain은 선별·stale 스냅샷이라 과거 산출물 직접 조회를 대체 못함 | 유효 | - |
| [사실] E5 단독 인용 금지, E1~E4 동반 필요 | 유효 | - |

> 위 두 건 `수정필요`는 TASK.md 작성 오류가 아니라 같은 태스크(R-10/R-11)의 실행으로 AS-IS가 바뀐 것이다. 확정 지위를 박탈하지 않는다 — 원문 갱신 여부는 §8 「PLAN 결정 필요」로 넘긴다.

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` | 원문 블록 금지·근거 등급·비소급 기준 |
| D-2 | 설계 | 분석 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | 확정 입력 소비 규약·통일 형식·체크리스트 포인터(v1.6) |
| D-3 | 설계 | 분석 가이드 | `opal/skills/op-dev-analysis/references/analysis-guide.md` | 절차가 analysis-core.md 포인터로 전환됐는지(v1.1) |
| D-4 | 설계 | 기술 컨텍스트 가이드 | `opal/skills/op-dev-analysis/references/tech-context-guide.md` | MCP 하드코딩 제거·SSOT+델타 템플릿 |
| D-5 | 설계 | 분석 코어 SSOT | `opal/core/references/harness/analysis-core.md` | §1~§7 실재, v1.1 3단-B 트리거화 반영 |
| D-6 | 설계 | PLAN 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | R-9·R-11 반영 확인 |
| D-7 | 설계 | Dev QA 가이드 | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | R-7·R-8·P-8 축 추가 |
| D-8 | 설계 | op-dev-qa 스킬 | `opal/skills/op-dev-qa/SKILL.md` | 거울 사본 R/P 번호 정합 |
| D-9 | 설계 | opd 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | STEP 2 분석 질문 슬롯(v5.6) |
| D-10 | 소스 | opd 파이프라인 스펙 | `opal/skills/opal-pilot-dev/references/pipeline.json` | pm_gate checklist 4항목 실채움 |
| D-11 | 소스 | state-tool 본체 | `opal/tools/state-tool/state_tool.py` | `_locate_confirmed_direction_items`·승계 verdict 구현 |
| D-12 | 소스 | state-tool README | `opal/tools/state-tool/README.md` | PD-1 분리형 계약 문서 정합 |
| D-13 | 소스 | state-tool 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | R-10 테스트 존재 |
| D-14 | 설계 | 하네스 모듈 표 | `opal/core/references/opal-harness.md` | §2 모듈 표 등록 |
| D-15 | 설계 | 프로젝트 SSOT | `docs/PROJECT.md` | 문서 레지스트리 조회 + 컴포넌트 등재 |
| D-16 | 소스 | pytest 실행 결과 | `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` (단일 파일) / `python3 -m pytest opal/tools/state-tool/ -q` (디렉토리) | R-10(d) 회귀 근거 — E1, 스코프·명령 병기 |
| D-17 | 소스 | brain 선조회 | `~/.opal/tools/brain-tool/run.sh search "analysis-core"` → total 0 | 선조회 1단 — 0건(3단-B 트리거 T1 성립) |
| D-18 | 소스 | code-scan 선조회 | `~/.opal/tools/code-scan/run.sh search "analysis-core"` → 0건 / `summary` → 102 files·18 domains | 선조회 2단 — 폴백 ① 적용 근거 |
| D-19 | 소스 | 과거 산출물(3단-B) | `tasks/098-260821-opds-근거등급-확정판정-트랙강등/DONE.md:48` | T1 트리거로 조회 — 098이 확정 입력 소비 규약을 신설했음 확인 |

> 지식 선조회 3단 수행 결과: 1단 brain 0건(D-17), 2단 code-scan 0건(D-18, 문서·규범 전용 태스크 특성), 3단 docs 레지스트리 상시 수행(D-15), 3단-B는 T1 트리거 성립으로 수행(D-19).

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

TASK.md 범위 15파일 전건 실측. `변경 필요` 열은 재생성 시점 기준이다(EXECUTE 완료 후라 대부분 완료로 관측).

| # | 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|---|------|------|----------|-------------|
| ① | `opal/core/references/harness/analysis-core.md` | 공유 분석 절차 SSOT(신규) | 완료 | `:1-184` §1~§7 실재, `:184` v1.1 3단-B 조건부 |
| ② | `opal/core/references/opal-harness.md` | §2 모듈 표 | 완료 | `:113`, `:135`, `:322` |
| ③ | `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS 스킬 본체 | 완료 | `:22-30`, `:184`, `:203-204` |
| ④ | `opal/skills/op-dev-analysis/references/analysis-guide.md` | 분석 절차 가이드 | 완료 | `:13-14,27,38,89,103`, `:109` |
| ⑤ | `opal/skills/op-dev-analysis/references/tech-context-guide.md` | 기술 컨텍스트 가이드 | 완료 | `:94-102`, `:117-141`, `:154` |
| ⑥ | `opal/skills/op-dev-plan/references/plan-guide.md` | PLAN 가이드 | 완료 | `:27`, `:92,98,102`, `:459` |
| ⑦ | `opal/skills/op-dev-qa/references/qa-dev-guide.md` | Dev QA 기준 | 완료 | `:77-78`, `:93`, `:164` |
| ⑧ | `opal/skills/op-dev-qa/SKILL.md` | QA 스킬(거울 사본) | 완료 | `:118-124`, `:198` |
| ⑨ | `opal/skills/opal-pilot-dev/SKILL.md` | opd 오케스트레이터 | 완료 | `:50`, `:426` |
| ⑩ | `opal/skills/opal-pilot-dev/references/pipeline.json` | PM Gate SSOT | 완료 | `:9-15` 4항목 실채움 |
| ⑪ | `opal/tools/state-tool/state_tool.py` | state-tool 본체 | 완료 | `:2271`, `:2278`, `:2579,2647` |
| ⑫ | `opal/tools/state-tool/tests/test_state_tool.py` | 단위 테스트 | 완료 | 파일 헤더 `100:` 구절 |
| ⑬ | `opal/tools/state-tool/README.md` | 계약 문서 | 완료 | `:277`, `:303-338`, `:460` |
| ⑭ | `docs/ARCHITECTURE.md` | 아키텍처 문서 | 완료 | `:478` |
| ⑮ | `docs/PROJECT.md` | 프로젝트 정의 SSOT | 완료 | `:199`, `:236,240` |

### 1.2 아키텍처 패턴

- **SSOT+포인터 분리**: `analysis-core.md`가 절차를 단독 소유하고 3개 스킬 문서는 산출물 형식만 소유한 채 Read 지시로 위임한다(D-5 서문, D-6 `:27`).
- **거울 사본 정합**: `op-dev-qa/SKILL.md`와 `qa-dev-guide.md`가 검증 ID 범위를 동일 버전(v1.4)으로 갱신 — 한쪽만 개정되는 재발 유형을 회피(D-7 `:164`, D-8 `:198`).
- **tool-gated PM Gate**: `pipeline.json`의 `gate.checklist`가 SSOT이며 SKILL.md에 복제하지 않는다(`docs/CONVENTIONS.md:231`).
- **배포 경계**: 변경이 프로젝트 소스에만 있고 `~/.opal/` 배포본은 미접촉(`docs/CONVENTIONS.md:248-253`).

### 1.3 의존성 맵

- 로드 순서: `opal-pilot-dev/SKILL.md`(STEP 2) → `op-dev-analysis/SKILL.md` → `tech-context-guide.md`/`analysis-guide.md` → `analysis-core.md`.
- PLAN 경로: `plan-guide.md`(D-6) → `analysis-core.md`(§1·§3·§5·§6 포인터) — opd·opds 양쪽이 동일 파일 공유.
- QA 경로: `op-dev-qa/SKILL.md` ↔ `qa-dev-guide.md` 거울 사본.
- State 경로: `state_tool.py` → `README.md` 계약 → `test_state_tool.py` 회귀.
- opds가 `op-dev-analysis` 없이 진입할 때도 `op-dev-plan`이 동일 `plan-guide.md`를 사용함을 `opal/skills/opal-pilot-dev-short/SKILL.md:45`로 확인 — 결정 J 성립.

### 1.4 테스트 현황

- 단일 파일: `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -q` → **347 passed, 3 skipped, 84 subtests**(D-16, E1).
- 디렉토리: `python3 -m pytest opal/tools/state-tool/ -q` → **364 passed, 3 skipped, 84 subtests**(D-16, E1).
- R-10(d)의 "감소 0건"은 개정 전 동일 스코프 수치가 있어야 대조 가능하다 — 재생성 시점은 이미 100 반영본이므로 본 문서는 현재 통과 수 확보에 그친다(§5 R-3).
- 마크다운·YAML 산출물에는 자동 테스트가 없다 — QA는 `qa-dev-guide.md` R/P 체크리스트로 수행된다.

## 2. 외부 조사 결과 (해당 시)

해당 없음 — 신규 외부 라이브러리·API 도입 없음.

## 3. 영향 범위

### 3.1 직접 영향

§1.1의 15개 파일(①~⑮) — 전건 반영 완료 상태로 관측됨.

### 3.2 간접 영향

- `opal-pilot-dev`(opd)·`opal-pilot-dev-short`(opds) — 둘 다 `op-dev-analysis`/`op-dev-plan` 경유 직접 소비자.
- `opal-task-agent`·`opal-plan-agent` — 신규 절차의 실행 주체.
- `opal-task-qa-agent` — R-7/R-8/P-8 신규 검증 축 수행.
- **영향 없음 확인**: opp·oppd가 쓰는 `op-task-plan/references/plan-guide.md`는 TASK.md에서 명시적으로 제외됐고 실제로 별도 파일이다.

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경 — 해당 없음
- [x] API 인터페이스 변경 — `verify --evidence-check` 응답에 `direction_confirmed_ratio` 추가(D-12 `:333-338`, 기존 분모 불변으로 하위 호환)
- [ ] 설정/환경변수 변경 — 해당 없음
- [ ] 빌드/배포 파이프라인 변경 — 해당 없음(배포는 이번 분석 범위 밖)
- [ ] 공유 라이브러리 변경 — 해당 없음

## 4. 핵심 발견 사항

1. R-1~R-11 전건이 코드·문서에 이미 반영된 상태로 관측됐다 — 재생성 시점이 EXECUTE 완료 이후다.
2. 선조회 1·2단 매칭 0건은 회피가 아니라 `header-rules.md` §빈 결과 폴백 ①이 정의한 정상 분기다(문서·규범 전용 태스크는 code-scan @header 대상이 아님).
3. TASK.md `[사실]` 2건이 같은 태스크의 R-10/R-11 실행으로 stale이 됐다 — 자기실행에 의한 갱신이므로 `사실오류`가 아니라 `수정필요`다.
4. AC-G1(승계 verdict 가용)·AC-G2(선조회 인용 존재)는 본 문서로 충족 가능하나, AC-G3·AC-G4는 baseline·PLAN.md 접근이 Guards로 금지되어 **이 산출물 단독으로는 측정 불가**다 — 별도 대조 단계가 필요하다.
5. 결정 J는 `opal/skills/opal-pilot-dev-short/SKILL.md:45`가 동일 `plan-guide.md`를 쓰는 것으로 코드 경로상 성립을 확인했다.

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| R-1 | TASK.md `[사실]` 2건 stale — 소유자 확인·문구 갱신 필요 | 낮음 | `opal/tools/state-tool/README.md:277`, `opal/skills/op-dev-plan/references/plan-guide.md:92` |
| R-2 | AC-G3·AC-G4는 본 디스패치 Guards로 측정 불가 — 문서 밖 별도 비교 단계 필요 | 중간 | TASK.md §R-12 선행조건 ③④ |
| R-3 | pytest "감소 0건" 판정은 개정 전 동일 스코프 수치를 요구하나 현재 HEAD가 이미 100 반영본 | 낮음 | D-16 |

## 6. 기술 컨텍스트

### 6.1 프로젝트 SSOT

전체 기술 스택은 `docs/PROJECT.md`(D-15)·`docs/ARCHITECTURE.md`를 참조한다. 이 섹션은 재기재하지 않는다.

### 6.2 이번 태스크 델타

변경 없음(SSOT 그대로) — `docs/PROJECT.md:199`가 이미 `analysis-core.md`를 컴포넌트 표에 등재했다.

### 6.3 추천 스킬

해당 없음 — 신규 기술 스택 도입이 없는 프레임워크 내부 작업이다.

### 6.4 추천 MCP

해당 없음 — `opal/core/references/mcps.md` 등록 4종 중 이번 태스크와 관련된 항목이 없다.

## 7. 지정 분석 질문 Q1~QN 답변

해당 없음 — 디스패치 프롬프트의 분석 질문 슬롯이 "없음"으로 지정됨.

## 8. 다음 단계 입력 — PLAN이 재조사 없이 쓸 수 있는 확정값

| 항목 | 확정값 | 근거 |
|------|--------|------|
| R-1~R-11 구현 상태 | 15개 대상 파일 전건 반영 완료(GREEN) | §1.1 각 행 근거 |
| R-12 측정 선행조건 | R-10 GREEN 완료 — `승계` verdict 사용 가능 | D-11 `:2647`, D-12 `:303-306` |
| pytest 회귀 스코프·수치 | 단일 파일 347 passed / 디렉토리 364 passed (각 3 skipped·84 subtests) | D-16(E1, 스코프+명령 병기) |
| opds Short 커버 경로 | `opal/skills/opal-pilot-dev-short/SKILL.md:45`가 `op-dev-plan` 디스패치 — 결정 J 성립 | 동 파일 |

### PLAN 결정 필요

| 항목 | 쟁점 | 근거 |
|------|------|------|
| TASK.md `[사실]` 2건 갱신 여부 | 원문을 최신화할지, 각주만 남길지 | 확정 입력 판정표 `수정필요` 2행 |
| AC-G3·AC-G4 측정 주체 | baseline·PLAN.md 접근 권한을 가진 PM이 별도 대조 단계로 수행 | 본 문서 §4-4, §5 R-2 |
