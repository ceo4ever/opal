# ADD_DONE-2: `undeclared-active` 개명과 `declaration` 독립 소비 계약

| 항목 | 내용 |
|------|------|
| 추가작업 번호 | ADD-2 |
| 일시 | 2026-09-17 16:58 ~ 17:10 (KST) |

## 사유

실사용 검증에서 합성 워크스페이스로 6상태를 전부 강제한 결과, `deferred` 선언인데 디스크에 존재하는 경우의 판정값 `undeclared-active`가 지적됐다.

**이름이 사실과 반대로 읽힌다.** 이 레포는 선언돼 **있다**(`deferred`로). 그런데 `undeclared-active`는 "선언 안 됨"으로 읽히고, 진짜 미선언인 `undeclared`와 한 단어 차이로 붙어 있어 더 헷갈린다. PLAN 단계에서 지은 이름을 구현 중에 어색하다고 느끼고도 계약 이름이라는 이유로 그대로 뒀다 — 판단 착오였다.

## 변경 내용

| 변경 | 내용 |
|---|---|
| 개명 | `undeclared-active` → `deferred-present` (구현·테스트·README·SKILL 10개소) |
| 축 구분 계약 명시 | `reason`은 `status`의 사유, `declaration`은 선언 대조 결과. 겹치는 구간과 겹치지 않는 구간을 README·구현 주석에 기술 |
| SKILL `[MUST]` | `declaration`을 `reason`과 별개로 읽으라는 지시 추가. `reason`만 훑어 보고서를 만들면 이 행이 화면에서 사라진다 |

### 철회한 수정안 1건

당초 `deferred-present`를 `reason`에도 싣기로 했으나 **철회했다.**

`reason`은 "`status`가 그렇게 된 사유"다. `deferred-present` 저장소는 정상 순회되므로 `status`의 사유가 따로 있고(`updated`/`already-current`/`dirty`…), 거기에 선언 대조 결과를 끼워 넣으면 `reason`의 의미가 무너진다.

"`deferred`(디스크 없음)는 `reason`에 실리는데 이건 안 실린다"를 불일치로 봤던 것이 착각이었다. 전자는 **선언이 곧 skip의 사유**여서 두 축이 겹치는 것이고, 후자는 겹치지 않는 것이다. 축이 다른 두 필드에서 겹치는 구간이 판정마다 다른 것은 일관성 위반이 아니다.

실제 위험은 이름이나 필드 배치가 아니라 **소비 규칙**이었다 — `reason`만 읽는 호출자가 이 드리프트를 놓친다. 그래서 필드를 늘리는 대신 소비 계약을 명시했다.

## 변경 파일

- `opal/tools/git-sync-tool/git_sync_tool.py`
- `opal/tools/git-sync-tool/README.md`
- `opal/tools/git-sync-tool/tests/test_git_sync_tool.py`
- `opal/skills/opal-workspace-sync/SKILL.md`
- `tasks/139-260917-opds-opws-워크스페이스-선언-기반-확장/ADD_DONE-2.md` (신규)

## 검증 결과

- `pytest tests/test_git_sync_tool.py -q` → **49 passed** (건수 불변 — 동작 변경 없는 개명·문서 변경)
- `grep -rn "undeclared-active" opal/` → 잔여 0건
- 배포: `install-mac.sh` 재실행 후 소스 대비 diff 동일

## 참고

`repos[].repo` 중복 거부는 AC-10의 기존 방어이며 스키마 검증이 순회 시작 전에 잡는다. 이번 변경 대상이 아니다.
