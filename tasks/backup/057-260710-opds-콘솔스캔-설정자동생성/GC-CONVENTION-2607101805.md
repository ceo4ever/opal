# GC CONVENTION REPORT — 2607101805

<!--
  체크박스 5단계 상태 기호 (APPLY 단계가 기입):
  [ ]  open    — 미처리 (신규)
  [x]  done    — 적용 완료  ← 주석: 적용 시각 YYYY-MM-DD HH:mm + 수정 요약
  [~]  pending — 보류       ← 주석: 보류 사유
  [?]  review  — 확인 필요  ← 주석: 판단 근거 / 해결 방안
  [!]  failed  — 실패       ← 주석: 실패 사유 / 권장 대안
-->

## 1. 헤더

- 실행 일시: 완료 2026-07-10 18:05 (KST)
- 범위: 태스크 057 변경분(unstaged working tree diff, `git diff <파일>` 기준) / 대상 파일 6개
  - `opal/tools/opal-cli/lib/console.sh`
  - `opal/tools/opal-cli/run.sh`
  - `dashboard/backend/config.py`
  - `scripts/install-mac.sh` (056 소속 backlog-tool chmod 블록은 제외 — 별개 태스크 변경분)
  - `scripts/install/windows.ps1`
  - `scripts/tests/test_console_scan.sh` (신규 파일)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 해당 문서 전체 로드 (허브+링크 모델 미적용, OPAL 자체 단일 문서 케이스)
- APPLY 수행 여부: N (수동 대기, 소스 수정 없음)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 3 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 2 / Info 1 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 3 |
| 파일별 상위 Top 5 | console.sh (2건) / run.sh (1건) / install-mac.sh (1건) / windows.ps1 (1건) / test_console_scan.sh (1건) |
| 카테고리별 빈도 | 문서화(변경이력 시각) (4 파일) / 네이밍 (1 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 1 (빈도 1건 + 새 카테고리 0건) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (2건)

- [ ] GC-C001 [opal/tools/opal-cli/lib/console.sh:25 · opal/tools/opal-cli/run.sh:19 · scripts/install-mac.sh:261 · scripts/install/windows.ps1:96] 변경이력 라인에 KST 시각(HH:mm) 누락
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(CONVENTIONS.md §변경이력 — "일시 형식: YYYY-MM-DD HH:mm (KST 기준)")
  - 설명: 4개 파일 모두 이번 태스크(057)에서 추가한 변경이력 라인이 날짜만 기록하고 시각(HH:mm)을 생략했다 (`v1.3 2026-07-10 scan 서브명령 신설...`, `v1.3 2026-07-10 usage()...`, `v3.9 2026-07-10: install_dashboard()...`, `v1.17.0 2026-07-10        Install-Dashboard...`). CONVENTIONS.md §변경이력 예시는 `2026-03-30 14:00`처럼 시각을 포함한다. 다만 @header 규칙(CONVENTIONS.md §@header 규칙)은 코드 파일에 한해 "헤더 내 변경이력 라인" 형식을 허용하며 표 형식을 강제하지 않아, 시각 표기 의무가 코드 파일 헤더 라인에도 동일하게 적용되는지는 문서상 명확하지 않다. 다만 동일 파일들의 과거 커밋(예: console.sh v1.0/v1.1, run.sh v1.0.1~v1.0.3)은 `KST` 시각을 포함해왔으므로, 057 라인들이 그 선례에서 벗어난 것은 사실이다.
  - 해결 방안: 각 변경이력 라인에 `HH:mm KST` 시각을 추가하거나(예: `v1.3 2026-07-10 18:00 KST: ...`), CONVENTIONS.md §변경이력에 "코드 파일 헤더 라인은 날짜만 허용"이라는 예외를 명시적으로 추가한다(§4 참고).
  - 자동 수정: N (시각 정보는 실제 작업 시각 확인 필요)
  - 참조: `docs/CONVENTIONS.md` §변경이력 (본 리포지토리 내부 문서, 외부 URL 없음)

- [ ] GC-C002 [scripts/install/windows.ps1:314] 변수명 `$optDir`가 실제로는 `.opal` 마커 디렉토리를 가리켜 의미가 불명확
  - 카테고리: 네이밍
  - 위반 기준: 프레임워크 base-convention-checklist §카테고리1(네이밍) — 참조용(CONVENTIONS.md에 변수 네이밍 세부 규칙 없음이므로 "추가 제안"에 준하는 낮은 근거)
  - 설명: `$optDir = $marker.DirectoryName` 이후 `.opal` 디렉토리인지 검사하는데, mac 스크립트의 대응 변수는 `project_dir`(정확히는 `.opal`의 부모)과 별도로 마커 디렉토리 자체를 가리키는 이름이 없다. `$optDir`이라는 이름은 "opal" 오타로 보이며 역할(마커가 위치한 `.opal` 디렉토리)을 드러내지 않아 가독성이 떨어진다.
  - 해결 방안: `$optDir` → `$markerOpalDir` 또는 `$opalDir`로 개명해 의미를 명확히 한다. (동작에는 영향 없음, 순수 가독성 이슈)
  - 자동 수정: Y (단순 변수명 치환, 같은 함수 스코프 내 3회 참조 전체 치환)
  - 참조: TBD — PSScriptAnalyzer 변수 네이밍 가이드라인 (사내 PS 린트 도구 미도입, 확인 필요)

### Info (1건)

- [ ] GC-C003 [scripts/tests/test_console_scan.sh] 파일명이 snake_case — CONVENTIONS.md §네이밍 규칙(파일/폴더: kebab-case, Python만 snake_case) 문면과 형식상 불일치
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(CONVENTIONS.md §네이밍 규칙 - 파일/폴더) — 단, 신규 위반 아님(선례 있음)
  - 설명: `docs/CONVENTIONS.md`는 비-Python 파일에 kebab-case를 규정하지만, `scripts/tests/` 디렉토리는 이미 `test_version_stamp.sh` 등 기존 테스트 스크립트 전부가 snake_case를 사용 중이다. 이번에 추가된 `test_console_scan.sh`는 그 기존 디렉토리 선례를 그대로 따른 것으로, 057이 새로 만든 이탈이 아니라 기존 관행의 연장이다.
  - 해결 방안: 위반으로 처리하지 않음 — 다만 `scripts/tests/`가 kebab-case 예외 디렉토리임을 CONVENTIONS.md에 명문화할지 여부를 캡틴 판단에 맡긴다(§4 참고, 새 카테고리는 아니고 기존 규칙의 예외 조항 추가 성격).
  - 자동 수정: N (선례 유지가 목적이므로 파일명 변경 비권장)
  - 참조: TBD — 프로젝트 내부 관행, 외부 링크 없음

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

- [ ] GC-DP-C001 [빈도 트리거] 이슈 "변경이력 시각(HH:mm) 생략" (4개 파일: console.sh, run.sh, install-mac.sh, windows.ps1) → CONVENTIONS.md §변경이력 규칙 추가 제안
  - 근거: 단일 실행 내 4개 파일 — 빈도 임계값 N=3 초과. 모두 057에서 추가된 라인이며, 코드 파일(.sh/.ps1) 헤더 변경이력 라인에 시각 표기가 반복적으로 생략되고 있어 우연이 아닌 관행으로 굳어지는 중.
  - 제안 내용: "CONVENTIONS.md §변경이력에 코드 파일(.sh/.ps1/.py 등) 헤더 내 변경이력 라인의 시각 표기 의무 여부를 명확화한다 — (안A) 스킬/에이전트/참조문서 표 형식과 동일하게 `HH:mm KST` 시각을 코드 파일 헤더 라인에도 의무화, 또는 (안B) 코드 파일 헤더 라인은 날짜만 허용하는 예외를 명시."

---

## 5. 문서 작성 유도 (해당 시)

- 존재 — 작성 유도 생략 (`docs/CONVENTIONS.md` 존재, Phase 1 허브 전체 로드 완료)

---

## 부록: 점검 방법 메모

- 대상 파일의 "이번 태스크 변경분"은 `git diff -- <파일...>` (unstaged working tree 기준)으로 한정했다. `scripts/install-mac.sh`에 섞여 있는 `# ── backlog-tool 실행 권한 (056) ──` 블록은 주석 자체가 (056) 소속임을 명시하고 있어 057 점검 대상에서 제외했다.
- bash 3.2 호환: `console.sh`(scan 브랜치)·`run.sh`·`test_console_scan.sh` 전체에서 `declare -A`/`mapfile`/`readarray` 사용 없음을 grep으로 확인 (인덱스 배열 `local -a`만 사용, 3.2 호환).
- `shellcheck`로 `console.sh` 전체 및 `install-mac.sh`의 057 신규 라인(약 1170행대, 1406행대) 범위를 점검 — 신규 추가 라인에서 신규 경고 없음(기존 파일의 사전 경고는 057 범위 밖이라 별도 카운트하지 않음).
- 하드코딩 시크릿: diff 전체에서 API 키/비밀번호/토큰 패턴 없음.
- 플랫폼 분기 격리: 신규 로직은 `scripts/install-mac.sh`(mac 어댑터)·`scripts/install/windows.ps1`(windows 어댑터)에만 위치하고, `opal/tools/opal-cli/lib/console.sh`·`run.sh`(플랫폼 중립 OPAL 도구)에는 플랫폼 조건문이 추가되지 않았다 — CONVENTIONS.md §플랫폼 분기 격리 준수.
