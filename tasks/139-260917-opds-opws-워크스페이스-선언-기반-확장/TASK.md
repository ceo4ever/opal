---
template: sdlc-v2
---
# TASK: opws 워크스페이스 선언 기반 확장

## Problem

`opal-workspace-sync`(opws)는 디스크에 이미 존재하는 저장소만 순회해 최신화한다. "어떤 레포가 있어야 하는가"라는 선언이 없어 다음 세 가지가 발생한다.

1. 클론되지 않은 자식 레포는 순회에서 보이지 않고 누락 보고도 되지 않는다. 조용히 사라진다.
2. 우산 프로젝트는 `workspace/`를 `.gitignore`로 제외하므로 git 이력이 자식 레포의 추가·삭제를 한 건도 기록하지 못한다. 멤버십 기록이 들어갈 자리가 프로젝트 안에 없다.
3. 그 결과 멤버십 선언이 `.gitignore` 주석·`PROJECT.md` 구조도 같은 산문으로 새어나가고, 코드가 읽지 않으므로 낡아도 아무도 탐지하지 못한다.

실제 사례가 존재한다. 우산 프로젝트 blend는 `.gitignore` 주석이 자식 레포를 5개로 선언하지만 디스크에는 4개가 있고, 이 불일치가 문서를 직접 읽기 전까지 드러나지 않았다.

## Proposed outcome

`{프로젝트}/.opal/workspace.json`에 자식 레포의 정규 좌표(`org/repo`)와 상태를 선언하면, `//opws` 실행 시 선언과 디스크를 대조해 다음을 얻는다.

- 선언됐지만 클론되지 않은 레포를 `not-cloned`로 보고하고, 승인 후 clone한다.
- 디스크에 있지만 선언되지 않은 레포를 `undeclared`로 보고해 선언 드리프트를 드러낸다.
- 의도적으로 두지 않은 레포(`deferred`)는 경고 없이 지나가고, 그것이 디스크에 나타나면 선언 어긋남으로 보고한다.
- 디렉토리는 맞지만 다른 레포가 클론된 경우를 `mismatch`로 차단해 엉뚱한 저장소를 pull하지 않는다.
- 선언 파일이 없는 프로젝트에서는 현행 동작이 그대로 유지된다.

## Affected users and systems

- `opal/skills/opal-workspace-sync/` — 대상 결정·보고서·승인 게이트
- `opal/tools/git-sync-tool/` — 순회·판정·pull 집행, `init` 서브명령 신설
- 새 스키마 파일 1종 — 선언 형식 계약
- `//opws`를 쓰는 모든 프로젝트 — 선언 파일이 없는 프로젝트는 영향받지 않아야 한다

범위 제외: 우산 프로젝트 blend의 문서 정합(`PROJECT.md`·`.gitignore`·`code-scan.json`)은 별도 후속이다. 접속 방식(SSH 별칭·HTTPS)을 설정 파일로 관리하는 것도 범위 밖이며 실행 시점 대화로 정한다.

## Constraints

- C-1: 선언 파일이 없으면 현행 동작과 100% 동일해야 한다. 조건부 분기가 실행되지 않으며 `undeclared` 판정 자체를 하지 않는다.
- C-2: 정체성 비교 키는 `org/repo`이며 host는 비교에 사용하지 않는다. 사용자별 SSH 호스트 별칭이 판정 결과를 바꾸지 않아야 한다.
- C-3: 도구가 반환하는 JSON에 원격 URL 원문을 싣지 않는다. 사용자별 값이 영속 산출물로 흘러갈 통로를 구조적으로 만들지 않는다.
- C-4: 대조 결과가 확정되지 않으면 일치로 간주하지 않는다. 판정은 `match`/`mismatch`/`unknown` 3진이며 `unknown`은 sync를 보류한다.
- C-5: clone은 사용자 승인 없이 실행하지 않는다. 기존 승인 게이트 구조(보고 → 제안 → 승인 → 실행)를 그대로 쓴다.
- C-6: 선언 파일의 `state`를 도구가 자동으로 변경하지 않는다. 선언 변경은 사람 결정이다.
- C-7: 기존 프로젝트 규칙을 유지한다 — 배포 경계(`~/.opal/` 직접 수정 금지, 프로젝트 소스 수정 후 install), 플랫폼 분기 금지, 도구 JSON `ok` 계약.

## Acceptance criteria

- AC-1: 서로 다른 레포 쌍(`storelink-io/blend` vs `storelink-io/blend-admin`, `storelink-io/blend` vs `other-org/blend`)을 입력하면 정규화 비교가 `mismatch`를 반환하는 테스트가 존재하고 통과한다.
- AC-2: `git@alias:org/repo`, `git@github.com:org/repo`, `https://github.com/org/repo.git`, `ssh://git@github.com/org/repo`가 모두 같은 `org/repo`로 환원되는 테스트가 통과한다.
- AC-3: 원격이 0개이거나 파싱 불가한 형식일 때 `unknown`을 반환하고 해당 저장소를 sync하지 않는 테스트가 통과한다.
- AC-4: 선언 파일이 없는 워크스페이스에 대한 `sync` 출력이 이 태스크 착수 전 출력과 동일하다(회귀 테스트로 확인).
- AC-5: 선언 × 디스크 6상태(active·있음 → sync / active·없음 → not-cloned / deferred·없음 → skip / deferred·있음 → sync+어긋남 보고 / 미선언·있음 → undeclared / 판정불가 → unknown)가 각각 판정되는 테스트가 통과한다.
- AC-6: `git-sync-tool init`이 기존 remote를 파싱해 선언 초안을 생성하고, 기존 파일이 있으면 `--force` 없이 거부하며, `--dry-run`은 파일을 쓰지 않고 초안만 반환한다.
- AC-7: 도구가 반환하는 JSON 어디에도 원격 URL 원문 문자열이 포함되지 않음을 검사하는 테스트가 통과한다.
- AC-8: `not-cloned` 저장소에 대해 승인 없이 clone이 실행되지 않고, 보고서 조치 제안 섹션에 나타남을 확인한다.
- AC-9: 접미사 `.git`이 붙은 remote와 붙지 않은 remote가 한 워크스페이스에 공존할 때 둘 다 `match`로 판정된다.
- AC-10: 선언 파일의 `state`가 허용값(`active`/`deferred`) 밖이거나 `dir`이 basename이 아니거나 `dir`·`repo`가 중복되면 스키마 검증이 거부한다.
