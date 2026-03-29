---
name: otp 범용 하네스 + 버티컬 전문 스킬 아키텍처
description: otp를 범용 프로세스 하네스로 분리하고, 도메인별 버티컬 스킬(otp-dev, otp-write 등)을 전문 확장으로 구성하는 아키텍처 방향
type: architecture_decisions
---

## 배경

036~039 태스크를 거치며 발견된 구조적 문제:
- otp-dev/otp-dev-short/otp-wf/otp-write의 TASK/PLAN 단계가 90% 동일
- 새 도메인(스킬 개발 등)이 나올 때마다 otp를 복제해야 하는 패턴
- 캡틴이 "스킬 개발"에 `//otpd`를 호출한 것은, 프로세스(TASK→ANALYSIS→PLAN→EXECUTE)를 원한 것이지 "코드 개발"을 원한 게 아니었음
- 알투도 거부하지 않고 자연스럽게 진행 → 프로세스와 도메인이 결합된 구조의 한계

## 아키텍처 방향

```
otp (범용 하네스 — 프로세스 제공)
  → TASK (공통)
  → ANALYSIS (공통, 조사 방식만 분기)
  → PLAN (공통, 설계 방식만 분기)
  → EXECUTE (도메인별 분기)

버티컬 전문 스킬 (필요 시 otp 확장)
  ├── otp-dev / otp-dev-short — 코드 개발 전문
  ├── otp-write — 문서 작성 전문
  ├── otp-wf — 와이어프레임 전문
  └── ... (향후 확장)
```

**Why:** 프로세스(어떻게 일하나)와 도메인(뭘 만드나)을 분리하면, 범용 otp로 모든 작업을 시작할 수 있고, 전문성이 필요한 경우에만 버티컬 otp를 사용.

**How to apply:** 별도 태스크(040)에서 설계 검토 예정. 현재 otp-dev/otp-write 등은 그대로 유지하면서 범용 otp 레이어를 추가하는 방향.
