# QA: EXECUTE — opal-harness.md 모듈화 — harness/ 폴더 분리

> 검토일: 2026-04-12 | 판정: Pass (Warning 1건 있음)

## 1. 요약

`opal/core/references/harness/` 폴더에 6개 모듈 파일이 신규 생성되었으며, 메인 하네스(`opal-harness.md`)에서 Lazy 로딩 대상 섹션(§2 QA 표준, §3 템플릿/추가작업, §5 Observability, §7 병렬 처리, §8 @header 규칙)이 stub으로 교체되었다. 각 stub에는 `[필수 로드]` + 적용 주체 + 적용 시점 + PM Gate 검증 항목이 명시되어 있다. §2에 모듈 매핑 테이블이 추가되었고, interactive 하네스에 PM Gate 모듈 체크포인트 테이블이 추가되었으며, agentic 하네스의 깨진 참조(§2.5)도 수정되었다. 메인 하네스는 364줄로 R-2의 목표치(~300줄 이하)를 초과하였으나, PLAN.md 리스크 대응에서 예고된 범위 내 결과다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | 6개 모듈 파일이 `harness/`에 존재하는가 | Pass | state-template.md, additional-work.md, qa-standards.md, observability.md, parallel-execution.md, header-rules.md 6개 확인 |
| R-2 | 메인 하네스 ~300줄 이하이고 §0~§9 모두 유지되는가 | Warning | 364줄로 목표치(~300줄) 초과. §0~§9 10개 섹션 전부 확인. PLAN.md §5 리스크 대응에 "불가피 시 PM 보고" 예고됨 |
| R-3 | §2에 6개 모듈 + 로드 시점 매핑 테이블이 존재하는가 | Pass | `harness/` 모듈 매핑 테이블 6행 + 탐색 경로 note 확인 |
| R-4 | `하네스 §[0-9]` 참조가 모두 유효한가 | Pass | §0~§9 stub 모두 존재, 기존 참조 유효 |
| R-5 | 각 모듈 파일 상단에 출처/로드 시점/역할 헤더가 있는가 | Pass | 6개 파일 전부 `> 출처:` / `> 로드 시점:` / `> 역할:` 3항목 헤더 확인 |
| R-6 | 변경이력에 v4.0 행이 존재하는가 | Pass | opal-harness.md line 364에 v4.0 행 확인 |
| R-7 | install-mac.sh `cp -Rf` 재귀 복사로 harness/ 자동 배포 확인 | Pass | line 621 `cp -Rf "$ref_src"/. "$ref_dst"/` — 재귀 복사로 harness/ 자동 배포 |
| R-8 | 모든 § stub에 `[필수 로드]` + 적용 주체 + 적용 시점 + PM Gate 검증이 있는가 | Pass | 6개 stub 전부 `[필수 로드]` 포함 (총 6건 Grep 확인). 적용 주체/시점/PM Gate 검증 항목 모두 명시 |
| R-9 | PM Gate에 6개 모듈 체크포인트 테이블이 존재하는가 | Pass | opal-harness-interactive.md §3에 "하네스 모듈 적용 확인" 서브섹션 + 6행 테이블 확인 |
| R-10 | agentic.md에 `§2.5` 참조 없고 §7.6 참조가 모듈화 구조와 정합하는가 | Pass | 본문에 `§2.5` 없음 확인. `§7.6` 참조 → `하네스 §7 병렬 처리 모듈 §7.6 준수`로 갱신 확인. 변경이력에 v1.3 기록 |
| C-1 | 분리된 모듈 내용이 원본과 의미 손실 없이 일치하는가 | Pass | state-template(템플릿 코드블록 + 행 규칙 + 산출물 행 규칙), additional-work(ADD_DONE 템플릿 + 감지 조건 + 진입 절차 + 스킬별 테이블), qa-standards(2단계 갱신 구조 + 파일명 표 + 스킬별 테이블 + 갱신 의무), observability(4개 서브섹션), parallel-execution(7.4~7.6 포함), header-rules — 핵심 항목 대조 Pass |
| C-2 | stub 탐색 경로가 실제 파일 경로와 일치하는가 | Pass | 6개 stub의 `탐색:` 필드가 `harness/{file}.md` 형식으로 일치. 모듈 매핑 테이블 하단 note에 2단계 탐색 경로 통합 명시 |
| C-3 | 모듈 매핑 테이블의 파일명/로드 시점이 각 stub과 일치하는가 | Pass | 매핑 테이블과 각 stub의 `탐색:` / `적용 시점:` 1:1 대조 Pass |
| C-4 | PM Gate 체크포인트 테이블의 모듈명이 매핑 테이블과 일치하는가 | Pass | interactive §3 테이블 6행(state-template, qa-standards, observability, header-rules, parallel-execution, additional-work)이 매핑 테이블과 일치 |
| C-5 | 스킬 파일에 harness/ 파일명이 직접 언급되지 않는가 (SSOT) | Pass | `opal/skills/` 전체 Grep — harness/ 파일명 직접 참조 0건 |
| Q-1 | 한국어 본문 + 영어 코드/필드명 규칙을 따르는가 | Pass | 6개 모듈 파일 전부 한국어 본문 + 영어 필드명/코드 규칙 준수 |
| Q-2 | kebab-case 파일/폴더 네이밍을 따르는가 | Pass | `harness/`, `state-template.md`, `additional-work.md` 등 kebab-case 확인 |
| Q-3 | 각 모듈 파일이 단독으로 읽어도 이해 가능한가 | Pass | 출처/로드 시점/역할 헤더 포함 + 독립 내용 구성 확인 |

## 3. 지적 사항

### Warning

**W-1: 메인 하네스 줄 수 R-2 AC(~300줄) 초과**

- **위치**: `opal/core/references/opal-harness.md`
- **현황**: 364줄 — R-2 AC "~300줄 이하" 목표 64줄 초과
- **원인**: PLAN.md §5 리스크 표에서 "stub을 최대한 간결하게 작성하여 달성 목표로 함. 불가피 시 PM에 보고하여 AC 기준 조정 협의"로 예고된 결과임
- **영향**: §0~§9 모두 유지되고 핵심 기능(stub, 모듈 매핑, [필수 로드])은 완전히 구현됨. Eager 로드 크기는 651줄 → 364줄로 44% 감소하여 목적(컨텍스트 절감)은 달성
- **권장 조치**: PM이 소유자에게 줄 수 초과 사실을 보고하고 R-2 AC 기준 조정(~400줄 이하 등) 여부를 협의

### Info

없음

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 | 6개 모듈 파일 존재 | Pass |
| TASK.md R-2 | 메인 하네스 줄 수 + §번호 유지 | Warning (364줄 / §0~§9 Pass) |
| TASK.md R-3 | §2 모듈 매핑 테이블 존재 | Pass |
| TASK.md R-4 | §번호 stub 유지로 외부 참조 유효 | Pass |
| TASK.md R-5 | 각 모듈 파일 자기 완결적 헤더 | Pass |
| TASK.md R-6 | 변경이력 v4.0 기록 | Pass |
| TASK.md R-7 | install-mac.sh 재귀 복사 확인 | Pass |
| TASK.md R-8 | stub에 [필수 로드] + 메타정보 | Pass |
| TASK.md R-9 | PM Gate 모듈 체크포인트 | Pass |
| TASK.md R-10 | agentic.md 참조 수정 | Pass |
| PLAN.md §3 Step 1~9 | 모든 Step 완료 여부 | Pass (9/9 완료) |

## 5. 판정

**Pass**

R-10개 기능 테스트, 5개 일관성 테스트, 3개 문서 품질 테스트 전부 통과. Warning 1건(R-2 줄 수 초과, 64줄)이 있으나, PLAN.md에서 예고된 리스크 범위 내이며 목적(컨텍스트 절감 44%)은 충분히 달성됨. 다음 단계(PM Gate) 진행 가능. PM은 소유자에게 줄 수 초과(364줄) 사실을 보고하고 AC 기준 조정 여부를 확인할 것을 권장한다.
