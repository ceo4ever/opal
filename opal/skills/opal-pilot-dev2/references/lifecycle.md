# 생명주기와 상태

INTENT → DESIGN → PLAN → BUILD → VERIFY → REVIEW → RELEASE → OBSERVE → CLOSED.
delivery=build는 REVIEW 뒤 CLOSED/ready_for_merge, release는 OBSERVE 뒤 CLOSED/observed.

| 단계 | 전이 근거 |
|---|---|
| INTENT | intent 구조·AC·미결 질문 해소·필요 승인 |
| DESIGN | intent 해시를 참조하는 spec·정책 적용·필요 승인 |
| PLAN | spec 해시를 참조하는 plan·파일 범위·독립 역할·검증 명령·필요 승인 |
| BUILD | 승인된 모든 명령의 Builder 성공 로그 |
| VERIFY | 동일 코드와 계약의 독립 Verifier 성공 로그 |
| REVIEW | 최신 독립 리뷰 pass·검증·DONE 또는 릴리스 승인 |
| RELEASE | 승인된 배포 실행 증거·확인 |
| OBSERVE | 관측 실행 증거·운영 확인·DONE |

.sdlc/events.jsonl은 상태 전체가 담긴 append-only 논리 journal이다.
파일 lock과 atomic replace로 쓰고 이전 이벤트 해시를 연결한다.
.sdlc/state.json은 조회 사본이다. journal 손상은 중단, stale projection은 journal에서 복구한다.
해시 체인은 우발적 손상 탐지이며 파일 소유자에 대한 암호학적 인증은 아니다.
STATE.md는 사람이 보는 현황이다. agentic은 초기화부터, semi-agentic은 BUILD 진입부터
AGENTIC-LOG.md를 도구가 렌더링한다. 두 Markdown 파일도 projection이므로 직접 상태를 수정하지 않는다.
응답의 transition_action=continue/complete/await_user/blocked와 report_type을 소비한다.

transition은 한 단계만 이동한다. 실패 exit 2이면 상태 유지.
검증 실패는 수정 요청 후 rewind --gate BUILD. 요구 변경은 INTENT, 설계 변경은 DESIGN,
계획 변경은 PLAN으로 rewind한다. 이후 증거·승인·리뷰는 무효화한다.
최초 baseline은 유지하며 전체 변경 범위를 검사한다. 재작업은 누적 3회까지다.

block --reason은 차단을 기록하고 unblock --reference ... --reason ...은 해결 근거를 기록한다.
정상 전이는 계속 진행한다. 실제 외부 계약·권한 결정은 모드에 관계없이 차단한다.
