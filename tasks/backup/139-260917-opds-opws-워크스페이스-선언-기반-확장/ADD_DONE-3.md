# ADD_DONE-3: deferred-present pull 실증과 undeclared skip 운영 영향 명시

| 항목 | 내용 |
|------|------|
| 추가작업 번호 | ADD-3 |
| 일시 | 2026-09-17 17:12 ~ 17:16 (KST) |

## 사유

실사용 검증의 남은 지적 4건 중 2건을 적용했다.

| 제기 | 판정 | 처리 |
|---|---|---|
| 판정명 `undeclared-active`가 사실과 어긋난다 | 타당 | **ADD-2에서 이미 처리** — `deferred-present`로 개명 완료. 해당 실행은 개명 전 배포본이었다 |
| `deferred`+디스크 O가 upstream 정상일 때 실제로 pull하는지 미확인 | **타당 — 실제 공백** | 테스트 1건 추가 (아래) |
| 매니페스트 부재 시 폴백 정상 | 확인 | 무조치 — S-8이 이미 회귀로 고정한 구간이다 |
| `undeclared`가 skip이라 새 레포는 선언 전까지 sync 안 됨 | 동작은 의도대로, **문서가 비어 있었다** | README·SKILL에 명시 |

### deferred-present의 sync 절반이 미검증이었다

이 판정의 존재 이유는 "**sync는 하되** 선언 어긋남을 보고한다"다. 그런데 S-9는 `status`가 `updated` 또는 `already-current`임만 확인했고 실제 관측값은 `already-current`뿐이었다 — `behind > 0`에서 ff pull이 수행되는지는 한 번도 관측되지 않았다. 제기자의 픽스처도 upstream이 없어 `no-upstream`에서 멈춰 확인하지 못했다.

계약의 핵심 절반이 실증 없이 통과하고 있었다.

### undeclared skip은 문서 공백이었다

`undeclared` → 보류는 6상태표에 있고 의도된 설계(선언이 권위)다. 하지만 **운영상 무엇이 달라지는지**가 어디에도 없었다 — 선언을 도입한 프로젝트에서는 새 레포를 clone해도 선언에 넣기 전까지 최신화되지 않는다. 사용자가 "왜 pull이 안 되나"로 막히는 지점이다.

## 변경 내용

| 변경 | 내용 |
|---|---|
| 테스트 추가 | `test_add3_deferred_present_actually_pulls_when_behind` — `deferred` 선언 + 디스크 존재 + `behind 2`에서 `status: updated`·`pulled_commits: 2`·HEAD 전진을 단언 |
| README | 선언 도입 시 선언이 권위가 된다는 운영 변화 명시. 새 레포는 선언에 넣기 전까지 최신화되지 않는다 |
| SKILL | `undeclared` 보고 시 "선언에 추가해야 sync 대상이 된다"를 함께 알리도록 지시 |

구현 변경 없음 — 동작은 처음부터 의도대로였고, 검증과 문서만 채웠다.

## 변경 파일

- `opal/tools/git-sync-tool/tests/test_git_sync_tool.py`
- `opal/tools/git-sync-tool/README.md`
- `opal/skills/opal-workspace-sync/SKILL.md`
- `tasks/139-260917-opds-opws-워크스페이스-선언-기반-확장/ADD_DONE-3.md` (신규)

## 검증 결과

- `pytest tests/test_git_sync_tool.py -q` → **50 passed** (49 + ADD-3 1건)
- 신규 테스트 관측값: `declaration: deferred-present` · `status: updated` · `behind: 2` · `pulled_commits: 2` · `prev_head ≠ new_head`
  - **`deferred-present`가 실제로 ff pull까지 간다는 것이 처음으로 실증됐다**
