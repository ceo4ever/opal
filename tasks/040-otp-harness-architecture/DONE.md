# DONE: OPAL Harness Architecture — opal-harness.md + otp 슬림화

> 완료일: 2026-03-29

## 변경 요약

### 신규 생성
- **opal/core/references/opal-harness.md** (142줄) — 5개 otp 공통 하네스 인프라 (Guards, Gates, State, TASK, Observability)

### 슬림화 (5개 otp)

| 파일 | Before | After | 감소율 |
|------|--------|-------|--------|
| otp-dev | 265줄 | 105줄 | -60% |
| otp-dev-short | 235줄 | 95줄 | -60% |
| otp-wf | 189줄 | 76줄 | -60% |
| otp-write | 163줄 | 80줄 | -51% |
| otp-write-tech | 132줄 | 90줄 | -32% |
| **합계** | 984줄 | 446줄 + 142줄(harness) = **588줄** | **-40%** |

### install-mac.sh
opal/core/references/ 전체 복사 로직이 이미 존재 — 추가 수정 불필요

## 검증

- [x] opal-harness.md 142줄 (150줄 이내)
- [x] 5개 otp 모두 105줄 이하
- [x] 도메인 고유 기능 보존 (에스컬레이션, FE/BE 병렬, 입력물 분기, 소스 조사, 4 Phase 등)
- [x] YAML frontmatter 변경 없음 (트리거 유지)
- [x] install-mac.sh 자동 배포 확인
- [x] 전체 588줄 (기존 984줄 대비 -40%)
