# DONE: OPPB Environment Probe 구조적 블로커 해결

## 결과

태스크 146을 HANDOFF 문서 개정이 아니라 태스크 142의 P2 Environment Probe를 실제로 재개 가능하게 하는 해결 태스크로 완료했다. 태스크 144가 이미 해결한 관측/판정 역할 분리는 유지했고, 그 뒤에 남아 있던 두 구조적 결함을 고쳤다.

- `git archive HEAD`가 `.gitattributes export-ignore`를 적용해 tracked 입력을 누락하던 문제를 임시 `GIT_INDEX_FILE` + `git read-tree HEAD` + `git checkout-index` 기반 전체 tracked-tree snapshot으로 교체했다.
- 각 명령이 새 snapshot에서 시작해 bootstrap 산출물이 후속 명령에 전달되지 않던 문제를 순차 bootstrap 준비 baseline으로 해결했다. 비-bootstrap 명령은 준비 baseline의 독립 복사본에서 실행되므로 bootstrap 산출물은 공유하지만 sibling 출력은 공유하지 않는다.
- `commands[].timeout_seconds`를 선택 계약으로 추가했다. 생략값과 explicit `180`은 같은 identity/hash를 만들고, bool·0 이하·비정수는 실행 전에 거부하며, timeout 실패는 command id를 보존한다.
- late discovery, `scope_violation`, budget charge, 공개 CLI exit 계약은 변경하지 않았다.

## 변경 파일

- `opal/tools/oppb-runtime-tool/probe.py`
- `opal/tools/oppb-runtime-tool/tests/test_probe.py`
- `opal/skills/op-oppb-project-slice/SKILL.md`
- `docs/proposals/opal-oppb-project-build-pilot.md`
- `tasks/146-260919-opds-프로브-핸드오프-계약개정/`의 TASK·PLAN·TEST-SCENARIO·게이트/검증 산출물

태스크 142의 파일·상태·profile은 수정하지 않았다.

## 검증

- RED 잠금: S-1 export-ignore 입력 누락과 S-3 bootstrap 전달 실패를 수정 전 `probe_command_failed`로 재현했다.
- 공개 CLI probe 테스트: `17 passed`.
- `oppb-runtime-tool` 전체 회귀: `139 passed`, 추가 subtest 13건 통과.
- 시나리오: S-1~S-9 `9/9 PASS`, FAIL 0, BLOCKED 0, RED 필수/확인 `2/2`.
- 목표 커버: AC 10건, C 8건, H 6건, 시나리오 9건 전부 연결·통과.
- PM Gate: PLAN 계약, code-scan 인용, scenario gate, state 정합 검증 통과.
- Convention: `PASS_WITH_ADVISORIES`, Critical 0 / High 0 / 신규 finding 0. Low 2건은 제안서 상태 어휘와 SKILL 변경이력 절에 대한 기존 baseline advisory다.

## 설치 및 태스크 142 재개 증거

`scripts/install-mac.sh`의 설치 경로로 전역 설치본을 갱신했다. source와 설치본 `probe.py` SHA-256은 모두 `a237f3ea17daa82ac7aa3dedffc9f208dacf6752aff8999174ff80032358c561`이며, slice skill §3.2 핵심 계약 hash도 양쪽 모두 `f890dcfd2022f6dbb990df92418d54cae5a8f9b44e318e46e8e6d680c10db415`다.

설치본 절대경로 CLI를 사용해 원본 밖 격리 fixture와 태스크 142 외부 clone을 검증했다.

- 태스크 142의 현행 probe 명령 8건 전부 exit 0.
- environment profile seal 성공.
- `verify_command`는 probe 명령으로 다시 편입하지 않았고 Supervisor 판정 책임을 유지했다.
- 태스크 142 원본의 capsule·state·profile 등 기준 파일 7개 hash와 전체 Git status signature는 작업 전후 동일했다.
- 태스크 146 원본 fixture도 HEAD·공유 index·tracked 파일이 실행 전후 동일했다.

따라서 태스크 142는 P2 probe를 성공·봉인할 수 있으며 다음 사용자 게이트부터 재개 가능하다.

## 문서·제안서 생명주기

구현으로 달라진 실행 사실은 slice skill §3.2와 OPPB 제안서 P2.2에 동기화했다. 제안서는 현재도 아래 3개 활성 문서가 참조하는 OPPB 설계 SSOT이므로 archive로 이동하지 않는다.

- `opal/tools/oppb-runtime-tool/README.md`
- `opal/agents/opal-evaluator-agent/AGENT.md`
- `opal/skills/opal-pilot-project-build/SKILL.md`

재사용 가능한 설계 WHY는 brain의 `environment-probe-baseline-isolation` concept으로 등록하고 index·ingest log를 갱신했다. brain 전체 validate에서 기존 골격의 빈 `sources/` 디렉터리 부재 1건이 보고됐지만, 신규 페이지 등록과 인덱싱은 성공했으며 페이지 자체 위반은 없다.

## 회고

작은 fixture에서 `.git` 디렉터리를 통째로 복사하는 방식은 통과했지만 실제 태스크 142 외부 clone에서는 loose object 복사 중 경쟁 조건이 드러났다. 최종 구현은 준비 baseline의 committed HEAD를 새 독립 repo에 다시 물질화하는 방식으로 바꿨다. 격리 실행 기능은 unit fixture만으로 닫지 말고, 실제 규모의 외부 clone과 설치본 CLI까지 같은 실패 모드로 검증해야 한다.

## 종료 경계

제안서의 기존 Low advisory 2건은 이번 변경이 새로 만든 문제가 아니며 기능·계약 통과를 막지 않는다. 이 워크트리에서는 commit·merge·push·worktree 제거와 허브 MEMORY 귀속을 수행하지 않는다. CLOSE 최종 상태는 `completed_unmerged`이며, merge 이후 허브가 finalize-attribution을 수행한다.
