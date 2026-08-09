# TASK: OPAL FW 구조개선 청사진 정식화 + 잔여 실측 (P0)

> 작성일: 2026-08-09 | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 (Opus 5 프롬프팅 가이드 검토 → FW 전체 구조 AS-IS 분석 → TO-BE 전략 대화 확정)
> 출력: TASK.md

## 작업 목표

FW 구조개선 4-Phase 계획의 P0로서, AS-IS 분석에서 남은 갭 4건을 실측으로 해소하고, 대화로 확정한 AS-IS→TO-BE 청사진을 P1~P3의 참조 SSOT가 되는 정식 문서로 산출한다.

## 배경

- Opus 5 프롬프팅 가이드(platform.claude.com) 검토 결과, OPAL FW의 산문 스캐폴딩(과잉검증·무조건 디스패치·긴 산출물)이 최신 모델 동작과 겹치는 지점이 식별되었다.
- FW 전체 구조 심층 분석(2026-08-08~09 대화)에서 5층 구조·규모 실측·중복 3계열(P-1~P-3)·효율 2건(P-4~P-5)이 진단되었다.
- 개선 실행(P1~P3) 전에 근거 미확정 갭 4건을 실측으로 잠그는 선행 태스크가 본 태스크다.

## 배경 분석 (대화에서 도출)

- 규모 실측: 스킬 24,237줄(109md) / 레퍼런스 6,598줄(37md) / 에이전트 3,071줄(21md) / 도구 코드 ~19,300줄 / 레지스트리 49 스킬·pilot 10종·에이전트 15종.
- 중복: PLAN 스킬 3벌(214/450/428줄, 본문에 "차이점" 섹션 존재) / EXECUTE 2벌 / QA 2벌 / 액션 에이전트 3종 동형(281/272/379줄) / pipeline.json(4종)과 SKILL.md 산문의 파이프라인 정의 이중화.
- 로드: Eager 체인 ~1,040줄 + opd 완주 시 참조 사슬 16문서 3,144줄(정적 합산) / 위임 참조 2~3홉.
- 실사용: FW 레포 태스크 28건 중 opd 15·opds 11·opp 1 / 대형 pilot은 사용처 프로젝트에서 적극 사용 중(캡틴 인터뷰).
- 잔여 갭 4건: ①pipeline.json↔SKILL.md 중복률 미실측 ②미보유 6 pilot의 스키마 확장 소요 미도출 ③태스크당 스폰 수(K4) 미실측 ④로드 사슬 실효값 미보정.

## 확정된 설계 방향 (대화에서 합의)

- 전략: "산문 프레임워크 → 데이터+도구 프레임워크. 산문에는 WHY와 예외만" — WHAT=pipeline.json SSOT / ENFORCE=도구 / WHY=경량 발동층.
- 인터뷰 확정 4건: 대형 pilot 적극 사용(폐기 불가, 통합·개선 가능) / 최우선 가치=단순화·유지보수성(+토큰 효율·Opus 5 정합, 신뢰성 불변은 제약) / 통합 폭=데이터 주도 전환 / 하네스 감량=1차 산문 압축→2차 도구화 단계적.
- 이행: P0(본 태스크, 읽기 전용)→P1(하네스 압축+Opus 5 정합)→P2(데이터 주도 전환)→P3(액션 에이전트 통합+2차 도구화). Phase별 독립 롤백.
- 불변 제약: 도구 게이트(state/test/backlog-tool) 제거 0건 / pilot alias 진입점 무중단 / 하위호환 기본값 규율.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 갭 4건 실측 해소 + AS-IS→TO-BE 청사진 정식 문서화 (P1~P3 참조 SSOT) | - | 대화 확정 전략(위 §확정된 설계 방향) |
| 범위 | 포함: 실측 ①~④, 청사진 문서, P1~P3 범위·완료기준 초안 / 제외: 소스 수정·install 배포·스키마 변경·brain ingest 외 일체 변경 | - | 읽기 전용 태스크 원칙 |
| 제약 | FW 소스(opal/·skills/·agents/) 및 `~/.opal/` 무변경 / 산출물은 본 태스크 폴더에만 생성 / 커밋은 사용자 명시 요청 시만 | - | 하네스 Guards |
| 완료기준 | 갭 4건이 각각 실측값·근거 인용으로 대체되고, BLUEPRINT.md에 5층 진단·P-1~P-5·비교표·P1~P3 범위 초안이 포함되며, 실측 부록 4건이 첨부된다 | - | AC-1~AC-5 (아래) |

## 요구사항

- [ ] **AC-1 중복률 실측**: pipeline.json 보유 4 pilot(opp/opd/opds/opdw)의 SKILL.md를 WHAT/ENFORCE/WHY 3분류로 태깅한 비율표가 산출된다 — 각 pilot별 줄 수 기준 비율 + 근거(섹션 단위 분류표) 포함.
  - 무엇을: 산문↔JSON 중복률 측정표 / 어디에: `analysis/A1-중복률.md` / 왜: P2 발동층 절단선 확정
- [ ] **AC-2 스키마 확장 소요**: 미보유 6 pilot(oppd/oppl/opsdd/opwt/opgc/opdd)의 단계·게이트·디스패치 구조를 추출하고, 현행 pipeline-spec.schema.json으로 표현 가능/확장 필요 2분류표가 산출된다.
  - 무엇을: 스키마 갭 목록 / 어디에: `analysis/A2-스키마소요.md` / 왜: P2 스키마 확장 범위 확정
- [ ] **AC-3 스폰 수 실측**: 완료 태스크 표본(opd·opds 최소 10건)의 STATE.md/DONE.md에서 태스크당 디스패치 횟수·단계 분포가 집계된다 — 평균·최대·단계별 분포 수치 포함.
  - 무엇을: K4 위임 비용 기준선 / 어디에: `analysis/A3-스폰실측.md` / 왜: P1 디스패치 규모 조건부화 기준선
- [ ] **AC-4 로드 사슬 보정**: 최근 태스크 2~3건 기준 실효 로드 문서 목록·홉 깊이 Top 5가 재구성된다.
  - 무엇을: K3 실효값 + 1홉화 우선 대상 / 어디에: `analysis/A4-로드사슬.md` / 왜: P1 규칙 인덱스 단일화 대상 선정
- [ ] **AC-5 청사진 정식화**: BLUEPRINT.md에 ①AS-IS 5층 구조 ②문제 P-1~P-5 ③TO-BE 전략·계층 ④AS-IS/TO-BE 비교표 ⑤P1~P3 각 범위·완료기준 초안 ⑥실측 A1~A4 반영 결론이 모두 포함된다.
  - 무엇을: 개선 계획 SSOT 문서 / 어디에: `BLUEPRINT.md` / 왜: P1~P3 태스크의 참조 기준

## 제약 조건

- 읽기 전용: FW 소스·전역 배포본 수정 금지 (산출물은 태스크 폴더 내 md만)
- 근거 인용: citation-rules §2 형식 (`경로:줄번호` 또는 `문서 §섹션`)
- 실측 우선: 추정치는 "추정"으로 명시하고 실측값과 구분

## 기술 스택

- Markdown 문서 분석 (FW 자산), JSON 스키마 (pipeline-spec.schema.json), Bash 집계

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | pipeline-spec 스키마 | `opal/tools/state-tool/schema/pipeline-spec.schema.json` | AC-2 표현 가능성 판정 기준 |
| D-2 | 설계 | pilot pipeline.json 4종 | `opal/skills/opal-pilot-{project,dev,dev-short,dev-wireframe}/references/pipeline.json` | AC-1 대조 원본 |
| D-3 | 기획 | 프로젝트 정의 | `docs/PROJECT.md` | 컴포넌트 인벤토리 SSOT |
| D-4 | 외부 | Opus 5 프롬프팅 가이드 | [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5) | P-5 진단·P1 정합 근거 |
| D-5 | 설계 | 하네스 SSOT | `opal/core/references/opal-harness.md` | AC-4 로드 사슬 기점 |
