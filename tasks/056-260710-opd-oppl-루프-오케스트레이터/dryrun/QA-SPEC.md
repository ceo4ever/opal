# QA-SPEC: hello-cli 명세 리뷰 (spec-review / G 게이트 재현)

## 1. 헤더

| 항목 | 값 |
|------|-----|
| 실행 일시 | 2026-07-10 17:03 |
| phase | spec-review (oppl 태스크 파이프라인 G 게이트 재현) |
| target_artifacts | dryrun/PRD.md, dryrun/TRD.md, dryrun/CONTRACT.md, dryrun/backlog.json (T01 수용기준) |
| 기준 문서 상태 | CONTRACT.md 로드됨 — §5 루브릭절 병합 적용 (계약 완전성·일관성·설계 정합 프로젝트 앵커 우선) |
| 판정 범위 | 루브릭절(주관 판단 차원)만. §4 기계검증절은 판정 대상 제외 (opal-test-agent 소관) |
| 판정 주체 | opal-evaluator-agent (verdict-only, mutate 금지) |

> CONTRACT.md §5 루브릭절이 존재하여 계약 완전성·계약 일관성·설계 정합 3차원에 프로젝트 고유 앵커를 적용했다. Base 루브릭의 나머지 차원(컨벤션 정신·아키텍처 적합·drift 필요성)은 Base 앵커를 유지했다.

## 2. 차원별 판정

| item | result | reason (근거 인용) | suggestion |
|------|--------|--------------------|------------|
| CONTRACT.md::계약 완전성 | 5 | §1 스키마(입력 `name` string 필수 `$1` / 출력 stdout `Hello, <name>!` / exit 0), §2 시그니처(`bash dryrun/src/hello.sh <name>`), §3 경계(hello.sh는 stdout+exit code까지만 책임, 인자 검증은 범위 밖)가 초소형 CLI 구현에 필요한 정보를 빠짐없이 담음 — 앵커 5("모든 경계·데이터형·에러규약 정의") 충족 | — |
| CONTRACT.md::계약 일관성 | 4 | PRD 수용기준·TRD 수용기준·§4 기계검증절이 모두 `bash dryrun/src/hello.sh World` → stdout `Hello, World!` + exit 0 으로 완전 일치(§5 일관성 앵커 충족). 다만 backlog.json T01 수용기준은 `bash src/hello.sh World`로 `dryrun/` 경로 접두어가 누락되어 나머지 3개 산출물과 미세 불일치 | backlog.json T01 acceptance_criteria의 경로를 `bash dryrun/src/hello.sh World`로 통일해 PRD/TRD/CONTRACT 삼자와 문자열 일치시킬 것 (또는 태스크 폴더 기준 상대경로 규약을 명시) |
| CONTRACT.md::설계 정합 | 5 | §3 경계가 인자 검증·에러 처리를 명시적으로 범위 밖으로 밀어내 드라이런 목적(최소 규모 재현)에 맞게 과설계 없이 단순 — §5 설계 정합 앵커("과설계 없이 단순") 충족 | — |
| PRD.md::컨벤션 정신 | 5 | 목표·배경·범위·수용기준·비범위 구조가 명료하고 네이밍(hello-cli, name)이 일관. 가독성 높음 | — |
| TRD.md::컨벤션 정신 | 5 | 기술 선택·구현 방식·수용기준이 간결하며 PRD와 용어 정합. `echo "Hello, $1!"` 구현 방식이 명확 | — |
| TRD.md::아키텍처 적합 | 5 | 단일 bash 스크립트, 외부 의존성 없음, 레이어/의존 역전 이슈 없음 — 드라이런 규모에 적합 | — |
| 전체::drift 필요성 | no | 계약 자체는 내부 모순 없이 완전. backlog 경로 불일치는 계약 변경이 아니라 backlog 산출물 정합의 문제이므로 CONTRACT 변경 불필요 | — |

## 3. 종합 verdict

**verdict: pass**

- 모든 Likert 차원이 통과선(≥4)을 만족한다 (최저 4점: 계약 일관성).
- Likert 미달(<4) 항목: **0건**.
- 유일한 감점 요인(계약 일관성 4점)은 backlog.json T01의 경로 접두어 누락이며, 통과선을 넘긴 개선 제안 수준이다. 구현 착수 전 정렬을 권고한다.

## 4. drift 필요성

**drift: no** — CONTRACT.md 변경 불필요. 거버넌스 에스컬레이션 대상 없음.

> backlog.json 경로 불일치는 계약 인터페이스 변경이 아니라 backlog 산출물 내부 정합 수정이므로, CONTRACT 거버넌스 계층(무변경/내부조정/인터페이스변경/외부노출) 에스컬레이션 대상이 아니다. 반영은 PM(오케스트레이터) 책임이며 본 에이전트는 판정만 반환한다.
