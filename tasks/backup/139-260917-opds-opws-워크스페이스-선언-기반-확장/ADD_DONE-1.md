# ADD_DONE-1: 선언 파일 위치 판정 · init 컨테이너 가드 · deferred 가시화

| 항목 | 내용 |
|------|------|
| 추가작업 번호 | ADD-1 |
| 일시 | 2026-09-17 16:20 ~ 16:24 (KST) |

## 사유

실사용 워크스페이스에서 검증하던 PM이 3건을 제기했다. 두 건은 실제 결함이었고 한 건은 환경 사실이었다. 셋 다 직접 재현해 확인했다.

| 제기 | 판정 |
|---|---|
| (가) `init .`이 레포 밖에 설정 경로를 잡고 빈 초안을 낸다 | **결함 2건** — 원인이 서로 다르다 |
| (나) `deferred`·`undeclared`가 보고에 안 보인다 | **결함 1건** — `deferred`가 출력에서 사라졌다. `undeclared`는 정상 보고된다 |
| (다) `--root`로 넘긴 루트 레포가 `no-upstream`으로 skip됐다 | **도구 정상** — 해당 저장소에 원격이 설정돼 있지 않다 |

### (가) 두 원인

1. **설정 경로가 레포 밖으로 샜다.** 선언 파일 위치를 `순회경로/../.opal/`로 고정한 탓에, 프로젝트 경로를 직접 주면 한 단계 위를 가리켰다. `//opws`는 `<프로젝트>/workspace`를 넘기므로 스킬 경유는 정상이었고, 사람이 직접 치는 경로에서만 어긋났다.
2. **빈 초안은 별개 원인이다.** 경로에 `.git`이 있어 단일 루트 모드로 그 저장소 자신을 유일한 자식으로 훑었고, 그 저장소에 원격이 없어 좌표가 환원되지 않아 `org: ""`가 됐다. (다)와 같은 뿌리다.

### (나) 설계 오류

TASK는 `deferred`를 "경고 없이 지나간다"로 규정했는데 나는 **출력에서 제거**로 구현했다. 경고를 내지 않는 것과 보고에 없는 것은 다르다. 지우면 선언해 둔 레포가 어디에도 나타나지 않아 "선언은 했는데 아무도 안 본다"가 되고, 드리프트 탐지가 절반만 작동한다. 제기가 정확했다.

TEST-SCENARIO S-9와 그 테스트가 "항목 자체가 없어야 한다"를 단언하고 있었다 — 잘못된 계약을 잠근 것이므로 함께 교정했다.

## 변경 내용

| 변경 | 내용 |
|---|---|
| `resolve_project_root()` 신설 | `<path>/.opal/`이 디렉토리면 `<path>` 자신이 프로젝트 루트, 아니면 부모. `sync`·`init` 공통 적용 |
| `init` 컨테이너 가드 | `<path>/.git`이 있으면 `NOT_A_WORKSPACE_CONTAINER`로 거부. 컨테이너 경로를 추측해 내려가지 않는다 |
| `deferred` 가시화 | 선언됐는데 디스크에 없는 레포를 `state` 무관하게 전부 보고한다. `active`→`not-cloned`(조치 필요), `deferred`→`deferred`(조치 없음) |
| SKILL | 선언 파일 탐색 위치, `deferred` 보고 행, "조치 제안에 올리지 않는다" 명시, `init`에 컨테이너 경로를 넘기라는 지시 |
| README | 선언 파일 위치 판정 2단계 표, 6상태표 `deferred` 행, `reason` enum 5종, `NOT_A_WORKSPACE_CONTAINER` 오류 코드 |

`undeclared`와 `--root`의 동작은 바꾸지 않았다 — 각각 이미 정상이었고 환경 사실이었다.

## 변경 파일

- `opal/tools/git-sync-tool/git_sync_tool.py`
- `opal/tools/git-sync-tool/README.md`
- `opal/tools/git-sync-tool/tests/test_git_sync_tool.py`
- `opal/skills/opal-workspace-sync/SKILL.md`
- `tasks/139-260917-opds-opws-워크스페이스-선언-기반-확장/ADD_DONE-1.md` (신규)

## 검증 결과

- `pytest tests/test_git_sync_tool.py -q` → **49 passed** (45 + ADD-1 4건)
  - A-1 순회 경로 자신의 `.opal` 우선 / A-2 없으면 부모 폴백(회귀 방지) / A-3 저장소 경로 거부 / A-4 초안이 컨테이너 자신의 `.opal`에 기록
  - S-9의 `deferred` 단언을 "출력에 없어야 한다" → "`reason: deferred`로 보고에 남아야 한다"로 교체
- 실환경 재현 검증 (읽기 전용)

| 재현 | 수정 전 | 수정 후 |
|---|---|---|
| `init .` | `config_path`가 레포 밖 + 빈 초안 | `NOT_A_WORKSPACE_CONTAINER` 거부 + 조치 안내 |
| `init workspace --dry-run` | — | `config_path`가 프로젝트 `.opal/`, 자식 4건 환원 |
| `sync workspace --root .` | `total 5`, `backend_ocr` 부재 | `total 6`, `backend_ocr \| skipped \| deferred` 표시 |

- 배포: `install-mac.sh` 재실행
