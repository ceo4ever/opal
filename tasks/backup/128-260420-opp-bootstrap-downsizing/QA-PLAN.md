# QA: PLAN — 부트스트랩 다운사이징 — Eager 로드 최적화

> 검토일: 2026-04-20 | 판정: Pass

## 1. 요약

부트스트랩 Eager 로드 토큰을 ~18,500 → ~9,500으로 절반 수준으로 줄이기 위한 4-Track(A/B/C/D) 구현 계획이다. Track A는 install-mac.sh에 `strip_deploy_md()` bash 함수를 추가하여 배포 시 변경이력 섹션을 제거하고, Track B는 opal-harness.md §3/§4를 harness/ 개별 모듈로 분리하며, Track C는 opal-pm.md를 Lazy 전환(PM 컨텍스트 로드 §2만 AGENT.md에 인라인), Track D는 AGENT.md 내 죽은 지침 3개를 제거한다. 현황 조사에서 실제 소스 파일 줄 번호까지 확인하였고, 신규 4개 모듈 파일과 4개 기존 파일 수정의 구현 순서·완료 기준·테스트 방법·의존성이 Step별로 명세되어 있다. TASK.md 요구사항 13개 항목과 PLAN 구현 항목이 모두 매핑된다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | Step 1~5가 파일 경로·작업 내용·완료 기준·테스트·의존성을 모두 포함. `awk` 구현 코드까지 명세 |
| GP-2 | 의존성 순서 | Pass | Phase 1(Step 1·2 병렬) → Phase 2(Step 3·4 병렬) → Step 5 자체 검증. 하위 레이어 먼저 생성 원칙 명시 |
| GP-3 | TASK 반영 | Pass | TASK.md A-1/A-2 → M-4, B-1~B-4 → N-1/N-2+M-2, C-1~C-4 → N-3/N-4+M-1/M-3, D-1~D-3 → M-1 매핑 완전 |
| GP-4 | 파일 목록 완전성 | Warning | 부트스트랩 완료 보고 체크리스트(`[부트스트랩] ... ✅ PM`)의 `PM` 항목 의미 갱신이 §5 리스크로만 언급되고 Step 작업 항목에 미포함 |
| GP-5 | 설계 구체성 | Pass | N-1~N-4 헤더 포맷·본문 이동 규칙·변경이력 양식, M-1~M-4 라인 번호 기반 변경 지시, `strip_deploy_md()` awk 구현 코드 모두 명세 |
| GP-6 | 체크리스트 커버리지 | Pass | §3 실행 체크리스트 5 Step + §4 QA 체크리스트(기능 13개·일관성 6개·문서 품질 5개)가 요구사항을 빠짐없이 커버 |

## 3. 지적 사항

### GP-4: 부트스트랩 완료 보고 `PM` 항목 갱신 누락 (Warning)

**위치**: `opal/core/AGENT.md` §부트스트랩 완료 보고 섹션

**내용**: AGENT.md에는 부트스트랩 완료 보고 형식에 `PM` 항목이 포함되어 있다.

```
[부트스트랩] ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ...
```

현재 `PM` 항목의 설명은 "AGENT.md 부트스트랩 완료 시 표시"로, Eager 4단계인 opal-pm.md Read 완료를 의미한다. opal-pm.md가 Lazy로 내려가면 `PM` 항목은 "프로젝트 PM 컨텍스트(`.opal/AGENT.md`) 활성화 여부"로 의미가 바뀐다.

PLAN §5 리스크 테이블에서 이 문제를 인지하고 "AGENT.md 내 해당 문구 갱신" 대응 방안을 명시했으나, Step 3(M-1 작업 내용)에는 이 갱신이 명시적 항목으로 포함되지 않았다. EXECUTE 단계에서 누락될 수 있다.

**권장 조치**: Step 3 작업 내용에 "부트스트랩 완료 보고 `PM` 항목 설명 갱신 (Eager opal-pm.md → PM 컨텍스트 활성화 여부로 재정의)"을 항목으로 추가.

### 심각도 분류

- Warning: GP-4 — 수정 권장. 실행 단계에서 작업자가 리스크 테이블을 참조하면 자체 보완 가능하나, Step 명세에서 빠질 경우 누락 리스크가 있음

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md §요구사항 | A-1/A-2/B-1~B-4/C-1~C-4/D-1~D-3 13개 항목 ↔ PLAN M-1~M-4/N-1~N-4 매핑 완전성 | Pass |
| TASK.md §제약 조건 | `~/.opal/` 직접 수정 금지 → PLAN §2 `[MUST]` 박스로 명시. Guards 항목 일치 | Pass |
| TASK.md §배경 분석 | 토큰 추정치, 줄 번호, 섹션별 분석 → PLAN §1 현황 조사에서 실제 소스 확인 후 반영 | Pass |
| TASK.md §죽은 지침 목록 | D-1~D-8 → PLAN M-1/M-2에서 각각 처리(D-3·D-4·D-5·D-6·D-7·D-8 → M-2 §0 제거/레거시 호환 노트 제거, M-1 섹션 제거) | Pass |
| opal/core/AGENT.md (실제 소스) | 부트스트랩 Eager 4단계 opal-pm.md Read 지시 존재 확인 — PLAN 변경 대상과 일치 | Pass |
| opal/core/references/opal-pm.md (실제 소스) | §1 PM 역할 개요·§2 PM 컨텍스트 로드·§4 PM 검토 게이트·§7 문서/코드 불일치 Full 콘텐츠 존재 확인 — PLAN stub 대상과 일치 | Pass |
| scripts/install-mac.sh (실제 소스) | AGENT.md 단순 cp(:416), references cp -Rf(:635) 확인 — PLAN strip 훅 삽입 지점과 일치 | Pass |

## 5. 판정

**Pass**

TASK.md 요구사항 13개 항목이 PLAN 구현 계획에 완전히 반영되었으며, 현황 조사에서 실제 소스 줄 번호 기반으로 검증되었다. Warning 1건(부트스트랩 완료 보고 `PM` 항목 갱신 누락)은 §5 리스크에서 이미 인지된 사항으로, EXECUTE 단계 진입 전 Step 3 작업 내용에 명시하면 충분히 보완 가능하다.
