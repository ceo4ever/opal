# DONE: opws 워크스페이스 선언 기반 확장

## 결과

`//opws`가 "디스크에 있는 것"만 보던 구조에, **"있어야 하는 것"의 선언**을 더했다. `{프로젝트}/.opal/workspace.json`이 있으면 `git-sync-tool sync`가 선언과 디스크를 대조해 6상태를 판정한다.

| 선언 | 디스크 | 판정 | pull |
|------|--------|------|------|
| `active` | 있음·좌표 일치 | `match` | 수행 |
| `active` | 있음·좌표 불일치 | `mismatch` | **보류** |
| `active`/`deferred` | 있음·환원 불가 | `unknown` | **보류** |
| `active` | 없음 | `not-cloned` | 승인 후 `clone` |
| `deferred` | 없음 | 보고하지 않음 | — |
| `deferred` | 있음 | `undeclared-active` | 수행 + 어긋남 보고 |
| 미선언 | 있음 | `undeclared` | **보류** |

클론되지 않은 자식이 조용히 사라지던 문제와, 멤버십 선언이 `.gitignore` 주석·구조도 산문으로 새어나가 낡아도 아무도 모르던 문제가 함께 닫힌다.

**유지한 기존 동작**: 선언 파일이 없으면 대조 분기를 타지 않는다. 응답 키 집합이 도입 전과 동일하고 `undeclared` 판정 자체를 하지 않는다(C-1). 회귀 테스트로 고정했다.

**적용한 경계**:
- 정체성 키는 **host를 뺀 경로 전체**다. host·프로토콜·후행 `.git`·대소문자는 판정에서 배제하고, 계층(`org/subgroup/repo`)은 자르지 않는다.
- 환원 대상은 원격 좌표 3형식뿐이다. 로컬 파일시스템 경로는 환원하지 않고 `unknown`으로 보류한다.
- 판정은 3진(`match`/`mismatch`/`unknown`)이며 확정되지 않으면 일치로 간주하지 않는다(fail-closed).
- 도구 응답 어디에도 원격 URL 원문을 싣지 않는다. URL이 필요한 진단은 호출자가 렌더 시점에 읽어 화면에만 표시한다.
- `state`는 도구가 자동으로 바꾸지 않는다. 선언 변경은 사람 결정이다.
- `clone`은 전용 서브명령이며 `sync`는 클론하지 않는다.

**PLAN 대비 강화된 계약 2건** (문서만 보고 구현을 읽으면 어긋나는 구간이라 명시한다):

1. 정체성 키가 `org/repo` 2세그먼트에서 **경로 전체**로 확장됐다. 2세그먼트로 자르면 GitLab subgroup류에서 `orgA/team/repo`와 `orgB/team/repo`가 같은 키가 되어 서로 다른 조직의 저장소를 조용히 pull한다(H-1 미탐). 독립 검증이 실증해 수정했다.
2. 선언의 `repo`는 **항상 최상위 `org` 아래 경로**다. `/` 포함을 "전체 좌표"로 달리 해석하던 규칙을 제거했다 — 같은 문자열이 선언 위치에 따라 다른 조직을 가리키면 사람이 읽는 의미와 도구 판정이 갈린다. 부작용으로 한 선언 파일은 `org` 하나만 표현하며, 다른 조직의 자식은 `other_org[]`·`undeclared`로 드러나되 `match`로 만들 수는 없다.

## 변경 파일

- `opal/tools/git-sync-tool/git_sync_tool.py`
- `opal/tools/git-sync-tool/schema/workspace.schema.json` (신규)
- `opal/tools/git-sync-tool/README.md`
- `opal/tools/git-sync-tool/tests/test_git_sync_tool.py`
- `opal/tools/git-sync-tool/tests/conftest.py`
- `opal/skills/opal-workspace-sync/SKILL.md`

## 검증

- `~/.opal/.venv/bin/python -m pytest tests/test_git_sync_tool.py -q` → **45 passed**
  - RED 단계: `14 failed, 17 passed` — 실패 사유가 전부 선언 로더·정규화 부재였고, 도달 불가 URL로 인한 fetch 실패가 단독 사유인 케이스는 0건이었다(무효 RED 아님)
  - 기존 17건(052 자산)은 무수정 회귀 기준선으로 유지
- `code-scan validate opal/tools/git-sync-tool` → OK
- 독립 검증(`opal-test-agent`, 생성자≠평가자) 2회
  - 1차 **fail** — H-1 미탐(계층 절단) Critical 1건 실증
  - 2차 **pass** — blocker 0건. 원 재현 입력이 `mismatch`+HEAD 불변으로 막히는 것, 계층 깊이 불일치 양방향·self-hosted 서브패스·2세그먼트 선언 회귀·`init`→`sync` 왕복·C-1 키 집합 동일성을 직접 실행해 확인
- 실환경 읽기 전용 실행: 자식 4건의 SSH 별칭 remote를 전부 환원, 손으로 쓴 선언과 좌표 완전 일치, `unresolved` 0건
- 배포 검증: `install-mac.sh` 재실행 후 `~/.opal/tools/git-sync-tool/schema/workspace.schema.json` 실재. 구현·README·스키마 3파일이 소스와 diff 동일하고 배포본 실행 정상(H-4 해소)

## 회고적 학습 후보

없음

## 참고

- **실환경 `sync` 실호출은 수행하지 않았다.** 다른 프로젝트의 저장소를 실제로 pull하므로 이 태스크의 변경 범위를 벗어난다. 읽기 전용 `init --dry-run`으로만 실환경을 검증했다.
- 실사용 중인 선언 파일이 `schema_version: "1.0"`(문자열)과 `_help`·`clone_branch`를 쓰고 있어, 거부 기준을 "판정을 바꾸는 위반"으로 좁혔다. 표기 차이와 사람용 필드는 수용하고, 알려지지 않은 키(`stat` 같은 오타)는 계속 거부한다.
- `install-mac.sh`가 비대화형 모드 마지막에 홈 디렉토리 전체를 스캔해 매 실행이 15분 이상 걸린다. 도구 배포 자체는 수초인데 배포 검증까지의 대기가 이 스캔에 묶인다. 이 태스크 범위 밖이며 개선 후보로 남긴다.
- TASK가 명시한 범위 제외 항목(우산 프로젝트의 문서 정합, 접속 방식의 설정 파일화)은 그대로 미처리다.
