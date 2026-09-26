# DONE: 001-260926-oppb-재고부족-조회 프로젝트 빌드

> 완료일: 2026-09-26 | 스킬: //oppb

## 완료조건 판정

| ID | 완료조건 | 결과 | evidence |
|---|---|---|---|
| C-1 | stockctl low-stock --below N은 수량이 N 미만인 품목을 SKU 오름차순으로 SKU\tQTY 한 줄씩 stdout에 출력하고 exit 0으로 끝난다. | PASS | evidence/T01/integration-T01.p4-integration.a2.json (045e338c2dd7354318b5a8c0380b96568fb23c6a815c023c5922df8dcfa6f3ea)<br>evidence/T01/security-T01.p4-security.a2.json (85a471941e4060dd49c967edfab494dbf77a18830cf49112f579a8f26a6d4604)<br>evidence/T01/convention-T01.p4-convention.a2.json (adff2febddfe35baf794ff56a7fbb640b05a5e09ea877918416d1944e1f63ac0)<br>evidence/T01/integration-T01.p4-integration.a3.json (5ea04d01e85ce4c86fef1648d40b1fde2126d9ea1ac814c32d4cec5f39024589)<br>evidence/T01/security-T01.p4-security.a3.json (56571b3262396cbc42ac154b72badbbc3575aacb8e89ec05d6c104a98f87c42e)<br>evidence/T01/convention-T01.p4-convention.a3.json (a91a4e02552ad9f2051f0db486b18bd29c226a4278e2d4732ddade7c58789a7a) |
| C-2 | 해당 품목이 없으면 stdout에 아무것도 출력하지 않고 exit 0으로 끝난다. | PASS | evidence/T01/integration-T01.p4-integration.a2.json (045e338c2dd7354318b5a8c0380b96568fb23c6a815c023c5922df8dcfa6f3ea)<br>evidence/T01/security-T01.p4-security.a2.json (85a471941e4060dd49c967edfab494dbf77a18830cf49112f579a8f26a6d4604)<br>evidence/T01/convention-T01.p4-convention.a2.json (adff2febddfe35baf794ff56a7fbb640b05a5e09ea877918416d1944e1f63ac0)<br>evidence/T01/integration-T01.p4-integration.a3.json (5ea04d01e85ce4c86fef1648d40b1fde2126d9ea1ac814c32d4cec5f39024589)<br>evidence/T01/security-T01.p4-security.a3.json (56571b3262396cbc42ac154b72badbbc3575aacb8e89ec05d6c104a98f87c42e)<br>evidence/T01/convention-T01.p4-convention.a3.json (a91a4e02552ad9f2051f0db486b18bd29c226a4278e2d4732ddade7c58789a7a) |
| C-3 | N이 정수가 아니거나 0 이하이면 stderr에 invalid:로 시작하는 한 줄을 쓰고 exit 5로 끝난다. | PASS | evidence/T01/integration-T01.p4-integration.a2.json (045e338c2dd7354318b5a8c0380b96568fb23c6a815c023c5922df8dcfa6f3ea)<br>evidence/T01/security-T01.p4-security.a2.json (85a471941e4060dd49c967edfab494dbf77a18830cf49112f579a8f26a6d4604)<br>evidence/T01/convention-T01.p4-convention.a2.json (adff2febddfe35baf794ff56a7fbb640b05a5e09ea877918416d1944e1f63ac0)<br>evidence/T01/integration-T01.p4-integration.a3.json (5ea04d01e85ce4c86fef1648d40b1fde2126d9ea1ac814c32d4cec5f39024589)<br>evidence/T01/security-T01.p4-security.a3.json (56571b3262396cbc42ac154b72badbbc3575aacb8e89ec05d6c104a98f87c42e)<br>evidence/T01/convention-T01.p4-convention.a3.json (a91a4e02552ad9f2051f0db486b18bd29c226a4278e2d4732ddade7c58789a7a) |
| C-4 | low-stock 실행 전후 저장소 파일이 바이트 단위로 동일하다(파일이 없으면 생성하지 않는다). | PASS | evidence/T01/integration-T01.p4-integration.a2.json (045e338c2dd7354318b5a8c0380b96568fb23c6a815c023c5922df8dcfa6f3ea)<br>evidence/T01/security-T01.p4-security.a2.json (85a471941e4060dd49c967edfab494dbf77a18830cf49112f579a8f26a6d4604)<br>evidence/T01/convention-T01.p4-convention.a2.json (adff2febddfe35baf794ff56a7fbb640b05a5e09ea877918416d1944e1f63ac0)<br>evidence/T01/integration-T01.p4-integration.a3.json (5ea04d01e85ce4c86fef1648d40b1fde2126d9ea1ac814c32d4cec5f39024589)<br>evidence/T01/security-T01.p4-security.a3.json (56571b3262396cbc42ac154b72badbbc3575aacb8e89ec05d6c104a98f87c42e)<br>evidence/T01/convention-T01.p4-convention.a3.json (a91a4e02552ad9f2051f0db486b18bd29c226a4278e2d4732ddade7c58789a7a) |
| C-5 | 기존 add·remove·list 동작과 tests/test_basic.py가 계속 통과한다. | PASS | evidence/T01/integration-T01.p4-integration.a2.json (045e338c2dd7354318b5a8c0380b96568fb23c6a815c023c5922df8dcfa6f3ea)<br>evidence/T01/security-T01.p4-security.a2.json (85a471941e4060dd49c967edfab494dbf77a18830cf49112f579a8f26a6d4604)<br>evidence/T01/convention-T01.p4-convention.a2.json (adff2febddfe35baf794ff56a7fbb640b05a5e09ea877918416d1944e1f63ac0)<br>evidence/T01/integration-T01.p4-integration.a3.json (5ea04d01e85ce4c86fef1648d40b1fde2126d9ea1ac814c32d4cec5f39024589)<br>evidence/T01/security-T01.p4-security.a3.json (56571b3262396cbc42ac154b72badbbc3575aacb8e89ec05d6c104a98f87c42e)<br>evidence/T01/convention-T01.p4-convention.a3.json (a91a4e02552ad9f2051f0db486b18bd29c226a4278e2d4732ddade7c58789a7a) |
| C-6 | docs/CLI.md에 low-stock 명령·출력 형식·종료 코드가 문서화된다. | PASS | evidence/T01/integration-T01.p4-integration.a2.json (045e338c2dd7354318b5a8c0380b96568fb23c6a815c023c5922df8dcfa6f3ea)<br>evidence/T01/security-T01.p4-security.a2.json (85a471941e4060dd49c967edfab494dbf77a18830cf49112f579a8f26a6d4604)<br>evidence/T01/convention-T01.p4-convention.a2.json (adff2febddfe35baf794ff56a7fbb640b05a5e09ea877918416d1944e1f63ac0)<br>evidence/T01/integration-T01.p4-integration.a3.json (5ea04d01e85ce4c86fef1648d40b1fde2126d9ea1ac814c32d4cec5f39024589)<br>evidence/T01/security-T01.p4-security.a3.json (56571b3262396cbc42ac154b72badbbc3575aacb8e89ec05d6c104a98f87c42e)<br>evidence/T01/convention-T01.p4-convention.a3.json (a91a4e02552ad9f2051f0db486b18bd29c226a4278e2d4732ddade7c58789a7a) |

## 미니 태스크

| task_id | capability | profile | 결과 | attempt |
|---|---|---|---|---|
| T01 | 재고 부족 품목 조회 | standard | accepted | T01.runner.2 |

## evidence manifest

| 경로 | content hash | 생성 시각 |
|---|---|---|
| evidence/T01/convention-T01.p4-convention.a2.json | adff2febddfe35baf794ff56a7fbb640b05a5e09ea877918416d1944e1f63ac0 | 2026-09-26T10:48:54.968708Z |
| evidence/T01/convention-T01.p4-convention.a3.json | a91a4e02552ad9f2051f0db486b18bd29c226a4278e2d4732ddade7c58789a7a | 2026-09-26T10:48:54.968708Z |
| evidence/T01/integration-T01.p4-integration.a2.json | 045e338c2dd7354318b5a8c0380b96568fb23c6a815c023c5922df8dcfa6f3ea | 2026-09-26T10:48:54.968708Z |
| evidence/T01/integration-T01.p4-integration.a3.json | 5ea04d01e85ce4c86fef1648d40b1fde2126d9ea1ac814c32d4cec5f39024589 | 2026-09-26T10:48:54.968708Z |
| evidence/T01/security-T01.p4-security.a2.json | 85a471941e4060dd49c967edfab494dbf77a18830cf49112f579a8f26a6d4604 | 2026-09-26T10:48:54.968708Z |
| evidence/T01/security-T01.p4-security.a3.json | 56571b3262396cbc42ac154b72badbbc3575aacb8e89ec05d6c104a98f87c42e | 2026-09-26T10:48:54.968708Z |

## 회고적 학습 후보

- `.opal/MEMORY.json`

## 남은 위험

- 차단 결함 없음. knowledge receipt에 기존 MEMORY·brain 진단을 보존함.
