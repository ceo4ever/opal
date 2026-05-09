# TASK: opal-harness.md 모듈화 — harness/ 폴더 분리

> 작성일: 2026-04-12 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

`opal-harness.md`에서 Lazy 로딩 가능한 섹션, 템플릿, 가이드를 `references/harness/` 폴더의 개별 파일로 분리한다. 메인 하네스는 핵심 규칙 + 모듈 매핑 테이블만 남겨 허브 역할로 전환한다.

## 배경

110번 태스크(§3 정리)로 ~95줄을 감축했으나, 메인 하네스가 여전히 ~651줄 / Eager 1회 로드 부담. 세션마다 전체를 읽으므로 컨텍스트 비용이 크고, 템플릿·가이드·프로세스 정의가 핵심 규칙과 혼재되어 가독성이 낮다.

## 배경 분석 (대화에서 도출)

### 현재 하네스 구조 (110번 리팩토링 후)

| § | 섹션 | 줄 수 | Eager 필수 여부 |
|---|------|------|---------------|
| 0 | 용어 정의 | ~20 | 필수 |
| 1 | Guards | ~45 | 필수 |
| 2 | 모듈 구조 | ~70 | 로딩 규칙은 필수, QA 표준은 Lazy 가능 |
| 3 | State | ~155 | 이벤트 테이블/전이/Gate는 필수, 템플릿/행 규칙/추가작업은 Lazy 가능 |
| 4 | TASK 공통 프로세스 | ~45 | 필수 |
| 5 | Observability | ~55 | Lazy — 워커 디스패치 시 |
| 6 | Model Mapping | ~10 | 유지 (이미 짧고 참조형) |
| 7 | 병렬 처리 원칙 | ~80 | Lazy — 병렬 디스패치 시 |
| 8 | @header 규칙 | ~66 | Lazy — EXECUTE 코드 변경 시 |
| 9 | OPAL Tools | ~30 | 유지 (이미 stub 형태) |

### 외부 참조 현황
- `하네스 §N` 형태 참조: 62개+ (주로 §3, §5, §7, §8)
- §번호 stub을 남기면 기존 참조 전부 유효

## 확정된 설계 방향 (대화에서 합의)

1. `references/harness/` 폴더를 생성하고 모듈 파일을 배치한다
2. 메인 하네스에는 §번호 stub을 남겨 기존 참조를 유지한다 (stub = §헤더 + 1-2줄 요약 + 참조 링크)
3. §2에 모듈 매핑 테이블을 추가하여 로드 시점을 명시한다
4. §6 Model Mapping과 §9 OPAL Tools는 이미 짧으므로 분리하지 않는다
5. 완벽하게 작동해야 한다 — 기존 파이프라인 정합성이 최우선 기준
6. **하네스가 SSOT** — 스킬은 `하네스 §N`만 참조. harness/ 파일명을 스킬이 직접 언급하지 않는다. 하네스 stub이 Read 대상 파일을 지시한다. 파일명/구조 변경 시 하네스 stub만 수정, 스킬 무수정.
7. **stub에 필수 로드 강제 + PM Gate 검증 항목을 명시** — 각 stub이 (a) 적용 주체, (b) 적용 시점, (c) PM Gate 검증 항목을 포함하여, PM이 해당 §를 만나면 자동으로 Read 트리거 + Gate에서 적용 여부 검증
8. **PM Gate에 하네스 모듈 체크포인트 추가** — 모든 관련 모듈의 적용 여부를 PM Gate에서 검증하고, 누락 시 Fail + 재작업

## 요구사항

- [ ] R-1: `opal/core/references/harness/` 폴더를 생성하고 6개 모듈 파일을 작성한다
  - **무엇을**: state-template.md, additional-work.md, qa-standards.md, observability.md, parallel-execution.md, header-rules.md
  - **어디에**: `opal/core/references/harness/`
  - **왜**: Lazy 로딩 가능한 내용을 개별 파일로 분리하여 Eager 부담 감소
  - **AC**: 6개 파일이 존재하고, 각 파일이 현재 하네스의 해당 섹션 내용을 온전히 포함한다

- [ ] R-2: 메인 하네스(opal-harness.md)에서 분리된 내용을 제거하고 §번호 stub으로 교체한다
  - **무엇을**: §2 QA 표준 → stub, §3 템플릿/행 규칙/추가작업 → stub, §5 전체 → stub, §7 전체 → stub, §8 전체 → stub
  - **어디에**: `opal/core/references/opal-harness.md`
  - **왜**: Eager 로드 시 핵심 규칙만 로드하여 컨텍스트 절감
  - **AC**: 메인 하네스가 ~300줄 이하이고, 모든 §번호(§0~§9)가 유지되어 있다

- [ ] R-3: §2에 하네스 모듈 매핑 테이블을 추가한다
  - **무엇을**: 모듈명, 파일 경로, 로드 시점을 명시한 테이블
  - **어디에**: `opal/core/references/opal-harness.md` §2
  - **왜**: PM/오케스트레이터가 언제 어떤 모듈을 로드해야 하는지 명확하게 안내
  - **AC**: §2에 6개 모듈 + 로드 시점이 기재된 매핑 테이블이 존재한다

- [x] R-4: 기존 §번호 참조(`하네스 §N`)가 모두 유효하게 유지된다
  - **무엇을**: 모든 외부 참조 검증 — stub이 존재하여 §번호로 찾아갈 수 있는지
  - **어디에**: `opal/` 전체 + `.opal/AGENT.md`
  - **왜**: 기존 파이프라인이 깨지면 안 됨 (완벽 작동 기준)
  - **AC**: Grep으로 `하네스 §[0-9]` 참조를 검색했을 때, 모든 참조 대상이 메인 하네스에 stub으로 존재한다

- [ ] R-5: 각 harness/ 모듈 파일이 단독으로 의미가 통한다 (자기 완결적)
  - **무엇을**: 각 파일 상단에 출처(하네스 §번호), 로드 시점, 역할을 명시
  - **어디에**: `opal/core/references/harness/*.md`
  - **왜**: 워커나 PM이 해당 파일만 Read해도 작업 가능해야 함
  - **AC**: 각 파일 상단에 출처/로드 시점/역할 헤더가 있고, 외부 참조 없이 읽어도 이해 가능하다

- [ ] R-6: 변경이력을 기록한다
  - **무엇을**: 메인 하네스 변경이력에 v4.0 행 추가
  - **어디에**: `opal/core/references/opal-harness.md` 변경이력
  - **왜**: 변경 추적 + 메이저 구조 변경 표시
  - **AC**: 변경이력에 111번 태스크 내용이 기록되어 있다

- [x] R-7: install-mac.sh에 harness/ 폴더 배포 경로를 추가한다
  - **무엇을**: `references/harness/` → `~/.opal/references/harness/` 배포 항목 추가
  - **어디에**: `scripts/install-mac.sh`
  - **왜**: 배포 시 harness/ 모듈이 누락되면 런타임에 Read 실패
  - **AC**: install-mac.sh에 harness/ 폴더 복사 로직이 존재한다

- [ ] R-8: 각 §stub에 `[필수 로드]` 블록을 작성한다 — 적용 주체, 적용 시점, PM Gate 검증 항목을 포함
  - **무엇을**: 하네스가 모듈 로드를 강제하는 stub 구조. 스킬은 `하네스 §N 참조`만 하면 되고, harness/ 파일명은 하네스 stub만 관리
  - **어디에**: `opal/core/references/opal-harness.md` 각 §stub
  - **왜**: 스킬 → 하네스 → harness/ 파일 1방향 참조로 SSOT 유지. 파일명/구조 변경 시 stub만 수정, 스킬 무수정
  - **AC**: 모든 분리된 § stub에 `[필수 로드]` + 적용 주체 + 적용 시점 + PM Gate 검증 항목이 명시되어 있다. 스킬 파일에 harness/ 파일명이 직접 언급되지 않는다

- [ ] R-9: PM Gate에 하네스 모듈 체크포인트를 추가한다
  - **무엇을**: 각 단계의 PM Gate에서 관련 하네스 모듈의 적용 여부를 검증하는 체크리스트. 누락 시 Fail + 재작업
  - **어디에**: `opal/core/references/opal-pm.md` §4 또는 `opal/core/references/opal-harness-interactive.md` §3
  - **왜**: Lazy 로드 누락의 안전망 — PM Gate에서 반드시 검증되어야 파이프라인 정합성 보장
  - **AC**: PM Gate 절차에 하네스 모듈 체크포인트 테이블이 존재하고, 각 모듈별 적용 조건/검증 항목/Fail 시 조치가 명시되어 있다

- [ ] R-10: opal-harness-agentic.md의 깨진/부정확한 참조를 수정한다
  - **무엇을**: (1) line 51 `하네스 §2.5 참조` — 106번에서 삭제된 Artifact Gate 참조 제거. (2) line 101 `공통 하네스 §7.6 준수` — §7 모듈화 후 정확한 참조로 갱신
  - **어디에**: `opal/core/references/opal-harness-agentic.md`
  - **왜**: (1)은 기존 버그(106번 미갱신), (2)는 모듈화로 §7.6이 harness/parallel-execution.md로 이동하므로 참조 갱신 필요
  - **AC**: agentic.md에 `§2.5` 참조가 없고, §7.6 참조가 모듈화 후 구조와 정합한다

## 제약 조건

- 배포본(`~/.opal/`) 직접 수정 금지 — 소스에서만 수정
- §번호(§0~§9) 변경 금지 — stub으로 유지
- 기존 오케스트레이터(opp/opds/opd/opdw/opwt/opsdd/oppd) 동작에 영향 없어야 함
- 각 모듈 파일은 현재 하네스의 해당 내용을 의미 손실 없이 이관

## 기술 스택

- Markdown 문서
- Shell script (install-mac.sh)

## 관련 문서

- `opal/core/references/opal-harness.md` — 변경 대상 (R-1~R-4, R-6, R-8)
- `opal/core/references/opal-pm.md` 또는 `opal/core/references/opal-harness-interactive.md` — R-9 PM Gate 체크포인트 추가
- `scripts/install-mac.sh` — R-7 배포 경로 추가
- `docs/PROJECT.md` — 프로젝트 원칙
- `.opal/AGENT.md` — PM 검토 기준
- `tasks/110-260412-opp-harness-restructure/` — 선행 태스크 (§3 정리)
