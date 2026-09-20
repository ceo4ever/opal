# DONE: 142-260918-oppb-E2E-여정조각-라이브러리 프로젝트 빌드

> 완료일: 2026-09-20 | 스킬: //oppb

## 완료조건 판정

| ID | 완료조건 | 결과 | evidence |
|---|---|---|---|
| AC-STORAGE-LIFECYCLE | INTENT C-11·C-13 — docs/e2e/·.opal/e2e/는 추적되고 .e2e/는 .gitignore 1줄로 전량 무시되어 git status를 더럽히지 않으며, .e2e/artifacts/ 보존 정책이 집행되어 무한 증가하지 않는다. | PASS | evidence/T01/integration-P4.integration.T01.json (5d5cdecb150b9d55d6a30c36c10d7507b34225eb2a965633d06e65288873cf40)<br>evidence/T01/security-P4.security.T01.json (775c36a8f5f86c6f6da429a2124811f66386a89389d20b31621ef0eaa04e2b55)<br>evidence/T01/convention-P4.convention.T01.json (4cba9cf3972e419110cb566dd8677c24155eb4df14d5eb80741c4cf2f2cf4140) |
| AC-EVIDENCE-SECRET | INTENT C-1 — fill 계열 action의 입력값이 actions.jsonl에 원문으로 남지 않고, 마스킹 실패 시 원문을 남기지 않고 infra_error로 끝나는 기존 계약이 유지된다. | PASS | evidence/T02/integration-P4.integration.T02.json (a765cde1194ad686f733e7d239ba227b23ffc641947bb8b6787b3575e08ef07d)<br>evidence/T02/security-P4.security.T02.json (f86870ea57bb7fa78dcbc4bfee81c33f5098b2c03957fc14393e4bc96f9cb6f4)<br>evidence/T02/convention-P4.convention.T02.json (33f88a482012eb3824d5be9d03466f7f3c8795307c51553300557b41279aaf74) |
| AC-DRIVER-CONFORMANCE | INTENT C-2·C-3 — 시나리오 step이 요구하는 연산을 제공하지 않는 driver 후보가 실행 전에 걸러지고, e2e driver-verify가 8연산 이행을 실제 실행으로 검사해 부분 driver를 통과시키지 않는다. | PASS | evidence/T03/integration-P4.integration.T03.json (a1e1133ed8c738573942fded1334e194f3133a57c67fe5ae9e82eb6374eeff54)<br>evidence/T03/security-P4.security.T03.json (f245a8b57116d5bfc302a5bac66437245f6ffa1cf9780928dc95628615b0232e)<br>evidence/T03/convention-P4.convention.T03.json (397e772cd12cf15442a53b4e892b343565cb92ab2e120a40d43b150c7e8eb06d) |
| AC-DECLARATIVE-DRIVER | INTENT C-5·C-6 — .opal/e2e/drivers/의 매니페스트 JSON 한 장으로 driver가 등록되고 driver-verify를 통과해야 후보가 되며, .opal/e2e/order.json 값이 resolve_candidates(candidate_order=...)에 전달되어 후보 우선순위를 재정의한다. | PASS | evidence/T04/integration-P4.integration.T04.json (4042e7caea034936bf8eecb41f0c546e10fdbd03d09c8900a3f69fec41e8a39f)<br>evidence/T04/security-P4.security.T04.json (5a58809fb436c0b42479fcf2b6da75f11b2d05141442b3fe59aba0ff0dff7585)<br>evidence/T04/convention-P4.convention.T04.json (e66e17570b028fe730225404db31c716c4476814ca94dea26704fc1fd036407e) |
| AC-FRAGMENT-LIBRARY | INTENT C-4·C-7 — 사후 조건 없는 조각은 등록이 거부되고 전개 결과가 actions.jsonl에 실제 연산 단위로 남으며, 전개분과 본문에 같은 연산 signature가 함께 나타나도 재시도로 오판되지 않는다(동결 RED S-27 기대 계약 불변). | PASS | evidence/T05/integration-P4.integration.T05.json (adb5fcb57280a8ff59e947453553057b64bea8aa7c34912290e90093584b3c0a)<br>evidence/T05/security-P4.security.T05.json (0459b727ed72a1feb1bff564fd1ebdd5a37c6c73554ca18180767ad54482fd46)<br>evidence/T05/convention-P4.convention.T05.json (f028c97e1bf0e219f31c972cc3a05b08d29cbf0d9a3a286bd2004d62e6d33fb9) |
| AC-FRESHNESS-SKIP | INTENT C-8·C-9 — 신선도 키가 (여정 해시, 조각 해시 집합, surface_id, 대상 commit, 선택 driver 정체, 달성 충실도)로 판정되어 order.json만 바꿔 이전 pass 증적을 재인용하는 경로가 막히고, 생략이 '이전 증적 재인용'으로 기록되어 보인다. | PASS | evidence/T06/integration-P4.integration.T06.json (2be36c52b91e095843b6855efc63b40f48fccb509566e7c1de4abcde504a1d00)<br>evidence/T06/security-P4.security.T06.json (fbda955348d21837398639c7c793a5ede3b60530ec450ac7da11dcbb103a8d3b)<br>evidence/T06/convention-P4.convention.T06.json (b3138b324227816744633513a27edbe09cd2faad2f1e852fbdb50f96332f97d2) |
| AC-E2E-OPERATOR | INTENT C-10·C-12 — opal-e2e 스킬(alias //e2e)이 author·run·status 3모드로 동작하고 레지스트리에서 매칭되며 판정은 test-tool 호출 결과 해석만 하고, docs/e2e/ 승격 자격을 도구가 pass 증적으로 판정한다. | PASS | evidence/T07/integration-P4.integration.T07.json (79e3882ab29648a34a890396f0a2e42ade53fd8479588606d9ae324f61427b4e)<br>evidence/T07/security-P4.security.T07.json (25efff55d4911d923778e015dfe3808ad5ac3fd565fe7b91d064c7694ff485aa)<br>evidence/T07/convention-P4.convention.T07.json (ae514a64bbb7fa8505a2f0a072d128bdb861958e84c4e2a5d37a401b80130e53) |
| AC-NO-REGRESSION | INTENT C-14 — test-tool 기존 테스트와 E2E 계약 테스트가 프로젝트 전후로 모두 통과한다. 모든 미니 태스크의 verify_command 말미가 전체 스위트를 재실행해 이 조건을 태스크마다 확인한다. | PASS | evidence/T01/integration-P4.integration.T01.json (5d5cdecb150b9d55d6a30c36c10d7507b34225eb2a965633d06e65288873cf40)<br>evidence/T01/security-P4.security.T01.json (775c36a8f5f86c6f6da429a2124811f66386a89389d20b31621ef0eaa04e2b55)<br>evidence/T01/convention-P4.convention.T01.json (4cba9cf3972e419110cb566dd8677c24155eb4df14d5eb80741c4cf2f2cf4140)<br>evidence/T02/integration-P4.integration.T02.json (a765cde1194ad686f733e7d239ba227b23ffc641947bb8b6787b3575e08ef07d)<br>evidence/T02/security-P4.security.T02.json (f86870ea57bb7fa78dcbc4bfee81c33f5098b2c03957fc14393e4bc96f9cb6f4)<br>evidence/T02/convention-P4.convention.T02.json (33f88a482012eb3824d5be9d03466f7f3c8795307c51553300557b41279aaf74)<br>evidence/T03/integration-P4.integration.T03.json (a1e1133ed8c738573942fded1334e194f3133a57c67fe5ae9e82eb6374eeff54)<br>evidence/T03/security-P4.security.T03.json (f245a8b57116d5bfc302a5bac66437245f6ffa1cf9780928dc95628615b0232e)<br>evidence/T03/convention-P4.convention.T03.json (397e772cd12cf15442a53b4e892b343565cb92ab2e120a40d43b150c7e8eb06d)<br>evidence/T04/integration-P4.integration.T04.json (4042e7caea034936bf8eecb41f0c546e10fdbd03d09c8900a3f69fec41e8a39f)<br>evidence/T04/security-P4.security.T04.json (5a58809fb436c0b42479fcf2b6da75f11b2d05141442b3fe59aba0ff0dff7585)<br>evidence/T04/convention-P4.convention.T04.json (e66e17570b028fe730225404db31c716c4476814ca94dea26704fc1fd036407e)<br>evidence/T05/integration-P4.integration.T05.json (adb5fcb57280a8ff59e947453553057b64bea8aa7c34912290e90093584b3c0a)<br>evidence/T05/security-P4.security.T05.json (0459b727ed72a1feb1bff564fd1ebdd5a37c6c73554ca18180767ad54482fd46)<br>evidence/T05/convention-P4.convention.T05.json (f028c97e1bf0e219f31c972cc3a05b08d29cbf0d9a3a286bd2004d62e6d33fb9)<br>evidence/T06/integration-P4.integration.T06.json (2be36c52b91e095843b6855efc63b40f48fccb509566e7c1de4abcde504a1d00)<br>evidence/T06/security-P4.security.T06.json (fbda955348d21837398639c7c793a5ede3b60530ec450ac7da11dcbb103a8d3b)<br>evidence/T06/convention-P4.convention.T06.json (b3138b324227816744633513a27edbe09cd2faad2f1e852fbdb50f96332f97d2)<br>evidence/T07/integration-P4.integration.T07.json (79e3882ab29648a34a890396f0a2e42ade53fd8479588606d9ae324f61427b4e)<br>evidence/T07/security-P4.security.T07.json (25efff55d4911d923778e015dfe3808ad5ac3fd565fe7b91d064c7694ff485aa)<br>evidence/T07/convention-P4.convention.T07.json (ae514a64bbb7fa8505a2f0a072d128bdb861958e84c4e2a5d37a401b80130e53) |

## 미니 태스크

| task_id | capability | profile | 결과 | attempt |
|---|---|---|---|---|
| T01 | E2E 저장소 경계와 산출물 수명 | standard | accepted | T01.runner.1 |
| T02 | 증적 비밀 마스킹 | standard | accepted | T02.runner.1 |
| T03 | driver 연산 이행 검증과 실행 전 후보 게이트 | standard | accepted | T03.runner.1 |
| T04 | 선언형 driver 등록과 후보 순서 데이터화 | standard | accepted | T04.runner.1 |
| T05 | 여정·조각 라이브러리 | standard | accepted | T05.runner.1 |
| T06 | 신선도 원장과 재실행 생략 기록 | standard | accepted | T06.runner.1 |
| T07 | //e2e 발동층과 여정 승격 판정 | standard | accepted | T07.runner.1 |

## evidence manifest

| 경로 | content hash | 생성 시각 |
|---|---|---|
| evidence/T01/convention-P4.convention.T01.json | 4cba9cf3972e419110cb566dd8677c24155eb4df14d5eb80741c4cf2f2cf4140 | 2026-09-20T08:10:08.389691Z |
| evidence/T01/integration-P4.integration.T01.json | 5d5cdecb150b9d55d6a30c36c10d7507b34225eb2a965633d06e65288873cf40 | 2026-09-20T08:10:08.389691Z |
| evidence/T01/security-P4.security.T01.json | 775c36a8f5f86c6f6da429a2124811f66386a89389d20b31621ef0eaa04e2b55 | 2026-09-20T08:10:08.389691Z |
| evidence/T02/convention-P4.convention.T02.json | 33f88a482012eb3824d5be9d03466f7f3c8795307c51553300557b41279aaf74 | 2026-09-20T08:10:08.389691Z |
| evidence/T02/integration-P4.integration.T02.json | a765cde1194ad686f733e7d239ba227b23ffc641947bb8b6787b3575e08ef07d | 2026-09-20T08:10:08.389691Z |
| evidence/T02/security-P4.security.T02.json | f86870ea57bb7fa78dcbc4bfee81c33f5098b2c03957fc14393e4bc96f9cb6f4 | 2026-09-20T08:10:08.389691Z |
| evidence/T03/convention-P4.convention.T03.json | 397e772cd12cf15442a53b4e892b343565cb92ab2e120a40d43b150c7e8eb06d | 2026-09-20T08:10:08.389691Z |
| evidence/T03/integration-P4.integration.T03.json | a1e1133ed8c738573942fded1334e194f3133a57c67fe5ae9e82eb6374eeff54 | 2026-09-20T08:10:08.389691Z |
| evidence/T03/security-P4.security.T03.json | f245a8b57116d5bfc302a5bac66437245f6ffa1cf9780928dc95628615b0232e | 2026-09-20T08:10:08.389691Z |
| evidence/T04/convention-P4.convention.T04.json | e66e17570b028fe730225404db31c716c4476814ca94dea26704fc1fd036407e | 2026-09-20T08:10:08.389691Z |
| evidence/T04/integration-P4.integration.T04.json | 4042e7caea034936bf8eecb41f0c546e10fdbd03d09c8900a3f69fec41e8a39f | 2026-09-20T08:10:08.389691Z |
| evidence/T04/security-P4.security.T04.json | 5a58809fb436c0b42479fcf2b6da75f11b2d05141442b3fe59aba0ff0dff7585 | 2026-09-20T08:10:08.389691Z |
| evidence/T05/convention-P4.convention.T05.json | f028c97e1bf0e219f31c972cc3a05b08d29cbf0d9a3a286bd2004d62e6d33fb9 | 2026-09-20T08:10:08.389691Z |
| evidence/T05/integration-P4.integration.T05.json | adb5fcb57280a8ff59e947453553057b64bea8aa7c34912290e90093584b3c0a | 2026-09-20T08:10:08.389691Z |
| evidence/T05/security-P4.security.T05.json | 0459b727ed72a1feb1bff564fd1ebdd5a37c6c73554ca18180767ad54482fd46 | 2026-09-20T08:10:08.389691Z |
| evidence/T06/convention-P4.convention.T06.json | b3138b324227816744633513a27edbe09cd2faad2f1e852fbdb50f96332f97d2 | 2026-09-20T08:10:08.389691Z |
| evidence/T06/integration-P4.integration.T06.json | 2be36c52b91e095843b6855efc63b40f48fccb509566e7c1de4abcde504a1d00 | 2026-09-20T08:10:08.389691Z |
| evidence/T06/security-P4.security.T06.json | fbda955348d21837398639c7c793a5ede3b60530ec450ac7da11dcbb103a8d3b | 2026-09-20T08:10:08.389691Z |
| evidence/T07/convention-P4.convention.T07.json | ae514a64bbb7fa8505a2f0a072d128bdb861958e84c4e2a5d37a401b80130e53 | 2026-09-20T08:10:08.389691Z |
| evidence/T07/integration-P4.integration.T07.json | 79e3882ab29648a34a890396f0a2e42ade53fd8479588606d9ae324f61427b4e | 2026-09-20T08:10:08.389691Z |
| evidence/T07/security-P4.security.T07.json | 25efff55d4911d923778e015dfe3808ad5ac3fd565fe7b91d064c7694ff485aa | 2026-09-20T08:10:08.389691Z |

## 회고적 학습 후보

- `.opal/MEMORY.json`

## 남은 위험

- 차단 결함 없음. knowledge receipt에 기존 MEMORY·brain 진단을 보존함.
