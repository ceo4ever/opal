# QA: PLAN — opal-harness.md 모듈화 — harness/ 폴더 분리

> 검토일: 2026-04-12 | 판정: Pass

## 1. 요약

`opal-harness.md`(651줄)에서 Lazy 로딩 가능한 6개 섹션을 `opal/core/references/harness/` 폴더의 개별 파일로 분리하는 계획이다. 메인 하네스에는 §번호 stub + `[필수 로드]` 블록을 남겨 SSOT 원칙을 유지한다. `install-mac.sh`의 `cp -Rf` 재귀 복사가 이미 harness/ 자동 배포를 충족하므로 배포 스크립트 수정은 불필요하다. Phase 3단계(1: 6개 모듈 병렬 → 2: 메인 하네스 순차 → 3: interactive 하네스 순차)로 의존관계를 정확히 반영했다. 분리 후 추정 줄 수(~351줄)가 AC 목표(~300줄)를 소폭 초과할 가능성이 있으며, PLAN에서 이를 인식하고 완화 방안을 명시했다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | 라인 범위, stub 설계, 모듈 파일 내용이 모두 명세됨. 이 PLAN만으로 실행 가능 |
| GP-2 | 의존성 순서 | Pass | Phase 1(병렬 6개) → Phase 2(메인 하네스) → Phase 3(interactive) 순서가 의존관계와 일치 |
| GP-3 | TASK 반영 | Pass | R-1~R-9 전체가 Step 1~8로 매핑됨 (상세: §3 검증 참조) |
| GP-4 | 파일 목록 완전성 | Pass | 신규 6개 + 수정 2개 명시. R-7 install-mac.sh는 불필요 판단이 근거와 함께 기재됨 |
| GP-5 | 설계 구체성 | Pass | 라인 범위 단위 분리 경계 + stub 전문 + 모듈 매핑 테이블 + PM Gate 테이블까지 명세 |
| GP-6 | 체크리스트 커버리지 | Pass | §3 실행 체크리스트 8개 Step이 R-1~R-9를 빠짐없이 커버 |
| R-1 매핑 | 6개 모듈 파일 생성 | Pass | Step 1~6에 각 파일 경로, 라인 범위, 완료 기준, 의존성 명시 |
| R-2 매핑 | 메인 하네스 stub 교체 | Pass | Step 7에서 각 §별 교체 라인 범위 지정 + §번호 유지 확인 방법 명시 |
| R-3 매핑 | §2 모듈 매핑 테이블 | Pass | §2 설계 섹션에 6개 모듈 + 로드 시점 테이블 명세 |
| R-4 매핑 | 기존 §N 참조 유효성 | Pass | stub이 §번호를 유지하여 252개 참조가 모두 유효함을 근거 기재 |
| R-5 매핑 | 모듈 파일 자기 완결성 | Pass | 공통 헤더 형식(출처/로드 시점/역할) 명세됨. 각 Step 완료 기준에 포함 |
| R-6 매핑 | 변경이력 v4.0 | Pass | Step 7 완료 기준에 변경이력 v4.0 기재 명시 |
| R-7 매핑 | install-mac.sh 배포 | Pass | `cp -Rf "$ref_src"/. "$ref_dst"/` 재귀 복사 근거 제시. .gitignore harness 제외 없음 확인 |
| R-8 매핑 | stub `[필수 로드]` 블록 | Pass | 5개 §stub 전문이 명세됨. 적용 주체/적용 시점/PM Gate 검증 항목 포함 |
| R-9 매핑 | PM Gate 체크포인트 | Pass | 6개 모듈 체크포인트 테이블(모듈/적용 조건/검증 항목/Fail 시) 전문 명세 |
| SSOT | 스킬 파일 harness/ 직접 참조 | Pass | `opal/skills/` 전체 검색 결과 harness/ 파일명 직접 참조 없음 확인 |

## 3. 지적 사항

### Warning 1 (Warning): R-2 AC "~300줄 이하" 목표 달성 불확실

**심각도**: Warning

PLAN §1에서 분리 후 추정 줄 수를 `~351줄`로 계산하여 목표(~300줄) 초과 가능성을 인식하고 있다. PLAN이 "stub을 최대한 간결하게 작성(헤더 라인 포함 8줄 이내)"을 완화 방안으로 제시했고, "불가피 시 PM에 보고하여 AC 기준 조정 협의"도 명시했으므로 리스크가 관리되고 있다. 단, 실행 시 달성 여부를 반드시 확인하고, 초과 시 PM에게 즉시 보고해야 한다.

**수정 불필요**: PLAN에 완화 방안이 이미 포함되어 있으므로 PLAN 수정 없이 진행 가능. 실행 단계에서 검증 필요.

### 확인 사항 (Info): R-9 PM Gate 체크포인트 위치 결정

PLAN에서 R-9를 `opal-harness-interactive.md §3`에 추가하기로 결정했고, `opal-pm.md §4`는 변경 없음이 명시되어 있다. TASK.md의 R-9 설명에는 "opal-pm.md §4 또는 opal-harness-interactive.md §3"으로 선택지를 제시했으나 PLAN에서 interactive.md §3으로 확정했다. 이는 기존 PM Gate 구조(자가 진단 절차 아래 추가)에 적합한 결정이다.

**수정 불필요**: 합리적 설계 결정.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1~R-9 | PLAN Step 1~8과 1:1 매핑 여부 | Pass — R-1(Step 1~6), R-2(Step 7), R-3(Step 7), R-4(Step 7), R-5(Step 1~6), R-6(Step 7), R-7(§1 분석 + Step 없음), R-8(Step 7), R-9(Step 8) |
| opal-harness.md (실제 파일) | PLAN 라인 범위와 실제 섹션 위치 일치 여부 | Pass — §2 line 90/141, §3 line 182/233/286, §5 line 370/426, §7 line 439/523, §8 line 523/592 전부 일치 |
| install-mac.sh (실제 파일) | line 621 `cp -Rf "$ref_src"/. "$ref_dst"/` 존재 여부 | Pass — 재귀 복사 확인됨. harness/ 관련 .gitignore 제외 없음 |
| opal-harness-interactive.md (실제 파일) | R-9 추가 대상(§3 PM Gate) 구조 확인 | Pass — "PM Gate 자가 진단 절차" 하위에 추가 위치 명확 |
| opal/skills/ 전체 | harness/ 파일명 직접 참조 여부 | Pass — 직접 참조 없음. SSOT 원칙 현재 충족됨 |

## 5. 판정

**Pass**

R-1~R-9 전체가 PLAN Step으로 매핑되었고, 각 stub 설계(R-8)와 PM Gate 체크포인트(R-9)가 구체적으로 명세되었다. 라인 단위 분리 경계가 실제 파일과 정확히 일치하며, install-mac.sh R-7 자동 충족 판단도 근거가 확인된다. Warning 1건(300줄 초과 가능성)은 PLAN 내에서 완화 방안이 포함되어 있어 실행 단계로 진행 가능하다.
