# GC CONVENTION REPORT — 2026-08-10T23-28

## 1. 헤더

- 실행 일시: 2026-08-10 23:28 (KST)
- 범위: `changed_files` 지정 (`all` 아님) / 대상 파일 6개
  - `scripts/install-mac.sh`
  - `scripts/install/windows.ps1`
  - `scripts/install/linux.sh`
  - `opal/tools/doctor/lib/checks.sh`
  - `opal/tools/requirements.txt`
  - `docs/ARCHITECTURE.md`
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 — 단일 허브 문서(다중 구성 아님, 허브+링크 모델 미적용 대상 — 문서 §참고 명시)
- 제외: 작업트리에 혼재된 086 태스크 미커밋 변경(`docs/architecture-diagram/`, `.opal/brain/`)은 `git diff -- <6개 경로>` 로 범위를 한정하여 진단 대상에서 배제함
- APPLY 수행 여부: N (본 에이전트는 진단 전담 — 소스 파일 미수정)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 1 / Info 1 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 1 (판단 필요, 강제 아님) |
| 파일별 상위 Top 5 | `scripts/install/linux.sh` (1건) / `docs/ARCHITECTURE.md` (1건) |
| 카테고리별 빈도 | 문서화(변경이력 형식) 2건 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 1 (빈도 트리거 1건) |

**총평**: 6개 파일 모두 언어 규칙(코드=English/문서=한국어), 신설 함수·상수 네이밍 정합성, 변경이력 기재, 배포 경계·플랫폼 분기 격리 규칙을 준수함. 신설 함수(bash 8종, PowerShell 1종 + 판정 로직 확장)는 전부 호출 경로가 확인되어 죽은 코드·미사용 변수 없음. 아래 2건은 위반이 아니라 문서 범위 해석 관련 참고 사항임.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (1건)

- [ ] GC-C001 [`scripts/install/linux.sh:23`] 변경이력 항목에 시각(HH:mm) 누락
  - 카테고리: 문서화 (변경이력)
  - 위반 기준: 프로젝트(docs/CONVENTIONS.md §변경이력 — "일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)")
  - 설명: 신설 항목 `v1.2 2026-08-10: Python 하한 게이트 소재 명시 주석 추가 ... (087)`이 날짜만 기재하고 시각이 없음. 단, CONVENTIONS.md §변경이력·§구현 규칙-변경이력 작성 의무 조항은 "스킬, 에이전트, 참조 문서"를 대상으로 명시하고 있어 설치 스크립트(`scripts/`)에 문자 그대로 적용되는지는 범위가 불명확함. 또한 해당 파일의 기존 항목(v1.0, v1.1)도 동일하게 시각 없이 기재되어 있어, 이번 변경이 새로 도입한 이탈은 아니고 파일 자체의 기존 관례를 따른 것임.
  - 해결 방안: (강제 아님) 향후 일관성을 위해 시각까지 기재하거나, 혹은 CONVENTIONS.md §변경이력 대상 범위에 스크립트/도구 파일을 포함할지 여부를 문서에서 명확히 할 것 — §4 문서 업데이트 제안 참조.
  - 자동 수정: N (문서 범위 확정이 선행되어야 함)
  - 참조: `docs/CONVENTIONS.md` §변경이력 (내부 문서, URL 없음)

### Info (1건)

- [ ] GC-C002 [`docs/ARCHITECTURE.md:405`] 변경이력 태스크 표기가 `(Task 087)` 형태 — CONVENTIONS.md 예시(`(138)`)와 접두어 차이
  - 카테고리: 문서화 (변경이력)
  - 위반 기준: 프로젝트(docs/CONVENTIONS.md §구현 규칙 > 변경이력 작성 의무 — "변경내용은 태스크 번호를 괄호로 포함 — 예: `(138)`")
  - 설명: 신설 행이 `(Task 087)`로 표기되어 CONVENTIONS.md 예시의 `(NNN)` 단독 표기와 접두어가 다름. 다만 `docs/ARCHITECTURE.md`의 기존 변경이력 표 전체가 이미 `(Task 085)`, `(Task 083)`, `(Task 082)` 형태를 일관되게 사용 중이라, 이번 변경은 파일 고유 관례를 그대로 따른 것이며 새로 도입된 이탈이 아님. 위반이 아닌 참고 사항으로만 기록.
  - 해결 방안: 조치 불필요 — 파일 내 기존 관례와 정합. 문서 전체 표기를 통일하고 싶다면 별도 태스크에서 전체 표 일괄 정정 검토.
  - 자동 수정: N
  - 참조: `docs/CONVENTIONS.md` §구현 규칙 > 변경이력 작성 의무 (내부 문서, URL 없음)

---

## 4. 문서 업데이트 제안 (트리거 발동 시만)

- [ ] GC-DP-C001 [빈도 트리거] "스크립트/도구 파일(.sh/.ps1) 헤더 인라인 변경이력 형식" (4개 파일: `scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/install/linux.sh`, `opal/tools/doctor/lib/checks.sh`) → CONVENTIONS.md §변경이력 대상 범위 명시 제안
  - 근거: 단일 실행 내 4개 파일 — 빈도 임계값 N=3 초과. 4개 파일 모두 동일한 "버전 vX.Y 일시 KST: 설명 (태스크번호)" 인라인 주석 패턴을 이미 광범위하게 사용 중이며, `.opal/code-scan.json`의 `headerSource: "inline"` 설정과도 부합함.
  - 제안 내용: CONVENTIONS.md §변경이력(및 §구현 규칙 > 변경이력 작성 의무)의 적용 대상을 "스킬, 에이전트, 참조 문서"에서 "스킬, 에이전트, 참조 문서, 배포·도구 스크립트(`scripts/`, `opal/tools/**/*.sh`, `*.ps1` 등 헤더 인라인 변경이력을 사용하는 파일)"로 명확히 확장할지 여부를 소유자가 결정. 확장 시 기존 파일들(linux.sh 등)의 시각 누락 항목을 정정 대상으로 지정할 수 있음.

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
