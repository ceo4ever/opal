---
module: red-first
role: RED-first TDD 트랙 규칙 SSOT
load: TEST-SCENARIO 작성·EXECUTE 진입 시
상속: opal/core/PRINCIPLES.md (헌법) §4 — 원칙 자체는 헌법이 SSOT
---

# RED-first 트랙 — TDD RED→GREEN 규칙

> **행동 원칙 자체는 `opal/core/PRINCIPLES.md`(헌법)가 SSOT다.**
> 이 문서는 헌법 §4의 RED-first 트랙 운용 규칙만 정의한다.

---

## 0. 상속

[MUST] 헌법 §4(`~/.opal/PRINCIPLES.md:35-40`) 상속. 헌법 원칙을 재서술하지 않는다.

---

## 1. RED→GREEN 순서

[MUST] RED 단계에서 실패 테스트 코드를 작성·실행하여 실패(exit code≠0)를 증거로 기록한 뒤 GREEN(구현) 진입. RED 증거 없이 GREEN 진입 금지.

---

## 1.5 적용 기준 (하이브리드 자동분기)

**RED-first 강제** (self-confirming 위험 높음):
- 비즈니스 로직
- DB 스키마·마이그레이션
- API 계약
- 인증·인가
- 버그 수정(회귀 방지)

**구현 후 시나리오 검증 허용** (탐색·시각):
- 탐색적 프로토타입
- UI 화면·컴포넌트
- 행위 불변 리팩터
- 설정·문서

**판단 주체**: PM이 변경 영역으로 판단(TEST-SCENARIO 작성 시점). 모호하면 RED-first 기본(안전측).

**공통 불변**: 어느 트랙이든 ① 테스트 코드 산출물 ② 작성자≠구현자 ③ TEST 단계 검증을 유지한다.

**state-tool 연동**: RED-first 트랙 → `verify --red-check` ON / 구현-후-검증 트랙 → 기존 동작(`--red-check` OFF). 이 분기로 opt-in 구조가 정책을 그대로 집행.

---

## 2. 작성자≠구현자

[MUST] RED 테스트 코드 작성 주체는 EXECUTE 구현 워커(op-dev-execute)와 분리한다. RED 작성은 opal-test-agent(mode: red)가 담당한다.

---

## 3. 테스트 불변성

[MUST] GREEN/fix 루핑 중 RED 테스트 파일 수정 금지. 위반 시 블로커.

> reward hacking 방어: 테스트 약화·삭제·조건 완화로 통과를 유도하는 행위를 차단한다.

---

## 4. 공개 인터페이스 검증

내부 구현/private 결합 금지, 공개 인터페이스·관찰 행위(반환값/exit code/관측 출력)로 검증.

---

## 5. graceful skip

테스트 인프라 부재 프로젝트/문서 전용 태스크는 RED 트랙 자동 우회 금지 — 인프라 부재 시 사용자 에스컬레이션. state-tool RED 게이트는 산출물 부재 시 skip.

---

## 6. STATE 행 정책

RED는 EXECUTE 내부 서브스텝으로 흡수한다. 별도 STATE 행을 추가하지 않는다 (opds 10행/opd 15행 SSOT 보존).

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-06-09 18:42 | 초기 작성 — RED-first 트랙 SSOT 신설 (016) |
