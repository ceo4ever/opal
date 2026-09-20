# GC CONVENTION REPORT — 2026-09-03T11-10-00

## 1. 헤더

- 실행 일시: 시작 2026-09-03 11:10:00 / 완료 2026-09-03 11:10:00 / 소요 -
- 범위: `backend` (셸 스크립트 + 프레임워크 참조 문서, FE·모바일 없음) / 대상 파일 4개
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 확인 — 허브+링크 모델 미적용(OPAL 자체는 단일 허브 문서, scope 값과 무관하게 허브 전체 적용, §참고 — 허브+링크 모델)
- APPLY 수행 여부: N (읽기 전용 진단 — 수정 없음)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 3 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 0 / Info 3 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 0 (Info 항목은 조치 불요, 참고용) |
| 파일별 상위 Top 5 | scripts/tests/test_agent_adapter_fields.sh (1건) / scripts/install-mac.sh (1건) / scripts/install/windows.ps1 (1건) |
| 카테고리별 빈도 | 네이밍 (1 파일) / 문서화(변경이력 규정 공백) (2 파일) |
| Critical/High 수 | **0** |
| 문서 업데이트 제안 수 | 1 (새 카테고리 1건) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

없음.

### High (0건)

없음.

### Medium (0건)

없음.

### Low (0건)

없음.

### Info (3건)

- [ ] GC-C001 [scripts/tests/test_agent_adapter_fields.sh:1] 신규 테스트 파일명이 snake_case
  - 카테고리: 네이밍
  - 위반 기준: 참고 — docs/CONVENTIONS.md §네이밍 규칙 "파일/폴더: kebab-case 사용 (Python 파일은 snake_case)"
  - 설명: 본 규칙은 일반 파일 kebab-case, Python 파일만 snake_case 예외로 명시한다. 본 파일은 `.sh`이므로 원칙상 kebab-case(`test-agent-adapter-fields.sh`) 대상이나 snake_case로 작성되었다. 다만 `scripts/tests/` 디렉토리의 기존 5개 시블링 파일(`test_archive_contents.sh`, `test_console_scan.sh`, `test_download_contract.sh`, `test_merge_hooks.py`, `test_version_stamp.sh`) 전부가 동일하게 snake_case이며, 신규 파일 헤더 주석도 "관용 근거: scripts/tests/test_archive_contents.sh"를 명시적으로 인용해 기존 디렉토리 관행을 의도적으로 답습했다.
  - 해결 방안: 이번 태스크 범위에서 조치 불요(기존 5개 파일과의 일관성이 개별 리네이밍보다 우선). CONVENTIONS.md §네이밍 규칙에 "쉘 스크립트 테스트 파일(`scripts/tests/*.sh`)은 예외적으로 snake_case"를 명문화할지는 별도 문서화 결정 사항 — §4 참조.
  - 자동 수정: N
  - 참조: docs/CONVENTIONS.md §네이밍 규칙 (프로젝트 문서 내 규정, 외부 URL 없음)

- [ ] GC-C002 [scripts/install-mac.sh:46-48] 변경이력 일시 표기에 "KST" 리터럴 접미사 포함
  - 카테고리: 문서화
  - 위반 기준: docs/CONVENTIONS.md §변경이력 "일시 형식: `YYYY-MM-DD HH:mm` (KST 기준)"
  - 설명: v4.6~v4.8 행이 "2026-09-02 18:00 KST" 형식으로 시각 뒤에 "KST" 문자열을 덧붙였다. 규칙 문언은 형식을 `YYYY-MM-DD HH:mm`로 규정하고 "(KST 기준)"은 그 시각이 KST 기준임을 설명하는 괄호 주석이지, "KST" 리터럴을 값에 포함하라는 지시는 아니다. 다만 파일 내 기존 행(v3.6 "2026-05-09 15:00 KST" 등 다수)도 동일하게 "KST" 접미사를 이미 사용 중이라 이번 3행만의 신규 이탈이 아니라 파일 전체의 기존 관행이다. windows.ps1도 동일 패턴(v1.20.0/v1.21.0 "... KST:").
  - 해결 방안: 조치 불요 — 파일 전체 기존 관행과의 일관성이 우선. 규칙 문언의 모호성(값 포함 여부 불명)을 CONVENTIONS.md에서 명확히 할지는 §4 문서 업데이트 제안 참조.
  - 자동 수정: N
  - 참조: docs/CONVENTIONS.md §변경이력 (프로젝트 문서 내 규정, 외부 URL 없음)

- [ ] GC-C003 [scripts/install-mac.sh 전체, scripts/install/windows.ps1 전체] 셸/PowerShell 스크립트의 변경이력 기재 위치·포맷 규정 공백
  - 카테고리: 문서화
  - 위반 기준: 규정 없음(참고: docs/CONVENTIONS.md §변경이력 작성 의무는 "스킬, 에이전트, 참조 문서"만 명시하고, §@header 규칙은 "변경이력은 별도 표(스킬·에이전트·참조 문서) 또는 헤더 내 변경이력 라인으로 갱신한다"고만 언급 — 셸/PowerShell 스크립트가 이 "헤더 내 변경이력 라인" 대안에 해당하는지 명문 규정 없음)
  - 설명: 두 스크립트는 실제로는 파일 상단 주석 블록에 버전별 변경이력 라인을 일관되게 기재해왔고(install-mac.sh v1.1~v4.8, windows.ps1 v1.0~v1.21.0), 이번 태스크의 3행(install-mac.sh)·2행(windows.ps1) 추가도 동일 포맷·KST 표기·태스크 번호 `(105)` 포함까지 기존 패턴을 정확히 따른다. 다만 이 포맷이 CONVENTIONS.md §@header 규칙의 "헤더 내 변경이력 라인" 문구가 지칭하는 대상인지, 아니면 `.sh`/`.ps1`이 `.opal/code-scan.json`의 `extensions`(.py/.js/.ts/.jsx/.tsx/.vue/.svelte/.kt/.kts/.java/.swift/.md만 등재, `.sh`/`.ps1` 미등재)에 없어 @header 규정 적용 대상 자체가 아닌지 문서상 불명확하다. 이번 변경 자체는 기존 파일 관행을 정확히 답습했으므로 위반으로 판정하지 않는다.
  - 해결 방안: 조치 불요(이번 변경분 자체는 기존 관행 준수). 문서 공백은 §4 새 카테고리 트리거로 제안.
  - 자동 수정: N
  - 참조: TBD — docs/CONVENTIONS.md §@header 규칙 개정 시 참조 추가

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

- [ ] GC-DP-C001 [새 카테고리 트리거] "셸/PowerShell 스크립트 변경이력 규정" → CONVENTIONS.md §변경이력 작성 의무 보강 제안
  - 근거: GC-C002·GC-C003 — 현재 §변경이력 작성 의무 원문은 "스킬, 에이전트, 참조 문서"만 명시 대상으로 열거하고, 일시 형식에 "KST" 리터럴 포함 여부가 불명확하다. `install-mac.sh`/`windows.ps1`은 이미 안정적으로 파일 헤더 변경이력 관행을 운영 중이나 명문 근거가 약하다.
  - 제안 내용: "스킬·에이전트·참조 문서 외에 `scripts/*.sh`, `scripts/*.ps1` 등 헤더 주석 기반 변경이력을 쓰는 코드 파일도 동일 의무 대상이며, 형식은 파일 헤더 주석 내 `v{semver} {YYYY-MM-DD HH:mm} KST: {변경내용} ({태스크번호})` 한 줄로 갈음할 수 있다"는 문구 추가 검토.

---

## 5. 문서 작성 유도 (해당 시)

존재 — 작성 유도 생략 (`docs/CONVENTIONS.md` 존재 확인됨).

---

## 결론

- **Critical/High 판정: 0건** — PM Gate 통과 조건(Critical/High 0건) 충족.
- Medium/Low: 0건. Info 3건(위 §3 참조)은 모두 "조치 불요, 참고용" 판정 — 신규 변경이 기존 프로젝트 관행(시블링 파일 패턴)과 일관되거나, CONVENTIONS.md에 해당 항목에 대한 명문 규정이 없어(§규정 없음) 위반으로 단정할 근거가 없음.
- 확인한 4개 대상 파일(`scripts/install-mac.sh`, `scripts/install/windows.ps1`, `scripts/tests/test_agent_adapter_fields.sh`, `opal/core/references/agents.md`) 모두에서 변경이력 행 추가(태스크 번호 `(105)` 포함, KST 일시 표기) 확인, 플랫폼(Claude/Cursor/Gemini/Codex) 분기는 전량 `OPAL_ADAPTER_FIELD_SPEC`/`$OpalAdapterFieldSpec` 센티넬 블록(어댑터 계층) 내부에만 위치해 §플랫폼 분기 격리 준수 확인, `git status`/`git diff --stat` 기준 `~/.opal/` 경로 직접 편집 없음 확인(§배포 경계 준수).
