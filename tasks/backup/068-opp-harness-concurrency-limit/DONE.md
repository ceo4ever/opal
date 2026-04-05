# DONE: 하네스 병렬 실행 제한 및 리소스 관리 원칙 추가

> 완료일: 2026-04-02 | 스킬: opp --interactive

## 완료 내용

### T1. opal-harness.md §7.4, §7.5 추가

- **리소스 관리 (§7.4)**: 고부하 작업(파일 50KB 초과 또는 합산 200KB 초과) 시 병렬 개수를 Max 2개 또는 순차로 제한하는 원칙 수립.
- **런타임 폴백 (§7.5)**: 병렬 처리 중 리소스 오류(Memory Error, 타임아웃 등) 발생 시 자동으로 배치를 1/2로 분할하거나 순차 모드로 전환하여 재시도하는 자율 복구 프로세스 명시.
- v2.1 → v2.2

### T2. opwt 가이드 업데이트

- `network-guide.md` 배치 편성 규칙에 리소스 임계치 기반 제한 규정 추가.
- `diagnosis.json` 생성 시 대용량 파일에 대한 배치 제약 사유 명시 지침 추가.

## 산출물

| 파일 | 변경 |
|------|------|
| `opal/core/references/opal-harness.md` | §7.4-§7.5 추가, v2.2 |
| `opal/skills/opal-pilot-write-tech/references/network-guide.md` | 리소스 기반 배치 규칙 추가 |
| `tasks/068-opp-harness-concurrency-limit/QA-EXECUTE.md` | QA 검증 결과 (Pass) |
| `tasks/068-opp-harness-concurrency-limit/DONE.md` | 최종 보고서 |

## 특이 사항

- 병렬 실행 중 실패 시의 **자율 복구(Fallback)** 로직을 하네스에 명문화하여 향후 오케스트레이터의 안정성 대폭 강화.
- **QA Gate 통과**: `op-task-qa` 워커를 통한 검증 완료.
