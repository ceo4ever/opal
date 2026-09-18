---
template: sdlc-v2
---
# TEST-SCENARIO: opws 워크스페이스 선언 기반 확장

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS · `~/.opal/.venv/bin/python` · git 2.22+ · pytest. 기존 `opal/tools/git-sync-tool/tests/conftest.py`의 실 git 저장소 fixture를 재사용한다.
- 공통 데이터: fixture가 임시 디렉토리에 실제 `git init` 저장소를 만들고 `origin`을 로컬 bare 저장소로 붙인다. 원격 주소는 테스트 안에서 `git remote set-url`로 형식만 바꿔 넣는다(네트워크 접근 없음).
- 대역 사용과 한계: 사용하지 않음. 052 자산의 규율(mock·patch 금지, CLI subprocess 공개 인터페이스로만 검증)을 그대로 따른다. 단 원격 호스트 실재는 검증 대상이 아니므로 `git@github-iskang:...` 같은 별칭 URL은 문자열로만 주입하고 실제 fetch를 수행하지 않는다.
- 실행 조건: 자동 실행. S-12만 install 이후 수동 확인이 필요하다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, H-1, C-4 | 선언 `storelink-io/blend`, 실제 origin이 `storelink-io/blend-admin` | `compare_repo_coord`를 CLI 경유로 태우는 `sync`를 실행한다 | 해당 저장소가 `mismatch`로 판정되고 pull이 수행되지 않는다 | unit + CLI subprocess | 구현 전 RED |
| S-2 | AC-1, H-1 | 선언 `storelink-io/blend`, 실제 origin이 `other-org/blend` (org만 다름) | 동일 | `mismatch` | unit + CLI subprocess | 구현 전 RED |
| S-3 | AC-1, H-1 | 선언 `storelink-io/blend`, 실제 origin이 `storelink-io/blend2` (접두 유사) | 동일 | `mismatch`. 접두 일치를 동일로 보지 않는다 | unit + CLI subprocess | 구현 전 RED |
| S-4 | AC-2, C-2 | 같은 레포를 `git@alias:org/repo`, `git@github.com:org/repo`, `https://github.com/org/repo.git`, `ssh://git@github.com/org/repo` 4형식으로 각각 설정 | 각 형식에 대해 선언 `org/repo`와 대조한다 | 4형식 모두 `match`. host·프로토콜 차이가 판정을 바꾸지 않는다 | unit + CLI subprocess | 구현 전 RED |
| S-5 | AC-9, C-2 | 한 워크스페이스에 `.git` 접미사가 있는 origin과 없는 origin이 공존한다 | `sync` 실행 | 둘 다 `match`. 접미사 유무가 판정을 바꾸지 않는다 | integration (실 fixture) | 구현 전 RED |
| S-6 | AC-3, C-4 | 자식 저장소에 `origin`이 없거나 파싱 불가한 remote 문자열이 설정됨 | `sync` 실행 | `unknown`으로 보고되고 해당 저장소는 pull되지 않는다. `match`로 간주되지 않는다 | integration | 구현 전 RED |
| S-7 | AC-10, C-6 | `workspace.json`에 (a) `state: "actve"` 오타 (b) `dir: "../x"` (c) `dir` 중복 (d) `repo` 중복 각각을 담은 4파일 | 각 파일로 `sync` 실행 | 4건 모두 `WORKSPACE_CONFIG_INVALID`로 거부되고 순회를 시작하지 않는다 | unit + CLI subprocess | 구현 전 RED |
| S-8 | AC-4, C-1, H-3 | `workspace.json`이 존재하지 않는 워크스페이스 | `sync` 실행 후 응답 JSON의 키 집합과 값을 이번 변경 이전 출력과 비교한다 | 최상위·`repositories[]`·`summary` 키 집합이 동일하고 `undeclared` 판정이 1건도 발생하지 않는다 | integration 회귀 | 구현 후 |
| S-9 | AC-5 | 선언 4건(`active` 3 + `deferred` 1)과 디스크 상태를 조합해 6상태를 각각 재현한다 — `active`·있음 / `active`·없음 / `deferred`·없음 / `deferred`·있음 / 미선언·있음 / 환원 불가 | `sync` 실행 | 순서대로 sync 수행 · `not-cloned` · 보고 없는 정상 skip · sync + `undeclared-active` 보고 · `undeclared` 보고 · `unknown` 보고 | integration | 구현 후 |
| S-10 | AC-7, C-3 | 자식 origin이 `git@github-iskang:storelink-io/blend`인 상태 | `sync`·`init`·`clone` 각 응답 JSON 전문을 문자열 검색한다 | `github-iskang`과 전체 URL 문자열이 어느 응답에도 등장하지 않는다. `repo` 필드에는 `storelink-io/blend`만 있다 | unit + CLI subprocess | 구현 후 |
| S-11 | AC-6 | (a) `workspace.json` 부재 (b) 이미 존재 (c) 존재 + `--force` (d) `--dry-run` | 각각 `init` 실행 | (a) 파일 생성 (b) `CONFIG_EXISTS` 거부 + 기존 파일 무변경 (c) 덮어씀 (d) 파일 미생성 + 최상위 `draft` 키 반환 | integration | 구현 후 |
| S-12 | AC-8, C-5 | 선언에 `active`인데 디스크에 없는 레포가 1건 존재 | `sync` 실행 후 보고서를 확인하고, 승인 없이 대기한다 | `not-cloned`가 조치 제안 섹션에 나타나고 `clone`이 실행되지 않는다. 디스크에 새 디렉토리가 생기지 않는다 | manual (승인 게이트 관찰) | 구현 후 |
| S-13 | H-4, C-7 | 소스에 `opal/tools/git-sync-tool/schema/workspace.schema.json`이 있는 상태 | `scripts/install-mac.sh` 실행 후 `~/.opal/tools/git-sync-tool/schema/workspace.schema.json` 실재를 확인한다 | 배포 경로에 스키마 파일이 존재한다 | manual | 설치 후 |
| S-14 | H-2, C-2 | 같은 `org/repo`를 `https://github.com/org/repo`와 `https://gitlab.com/org/repo`로 각각 설정 | 선언 `org/repo`와 대조하고, 이어서 `README.md`와 `workspace.schema.json`의 `_help`에 이 동작이 기술되어 있는지 확인한다 | 두 호스트 모두 `match`로 판정된다(수용한 트레이드오프). 그리고 README와 스키마 `_help` 양쪽에 host 미비교와 그 결과가 명시되어 있다 | unit + 문서 확인 | 구현 후 |
| S-15 | AC-8, C-5 | 선언에 `active`이고 디스크에 없는 레포가 있으나, 대상 디렉토리 이름이 이미 다른 내용으로 점유되어 있다 | 승인 후 `clone` 서브명령을 실행한다 | 거부되고 기존 디렉토리 내용이 변경되지 않는다. 파괴적 덮어쓰기가 발생하지 않는다 | integration | 구현 후 |
| S-16 | AC-2, C-2 | 선언 `Storelink-IO/Blend`, 실제 origin이 `git@github.com:storelink-io/blend` | `sync` 실행 | `match`. 대소문자 차이가 `mismatch` 오탐을 만들지 않는다 | unit + CLI subprocess | 구현 후 |
| S-17 | AC-8, C-5 | 선언에 `active`이고 디스크에 없는 레포 1건, 승인 완료 상태 | `clone` 서브명령을 실행한다 | 대상 디렉토리에 저장소가 생성되고 이후 `sync`가 해당 레포를 `match`로 판정한다 | integration | 구현 후 |
