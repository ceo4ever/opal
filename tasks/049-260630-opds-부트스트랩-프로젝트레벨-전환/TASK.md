# TASK: 부트스트랩 진입 모델을 사용자레벨 상시 → 프로젝트레벨 opt-in 으로 전환 (2-tier)

> 작성일: 2026-06-30 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 부트스트랩을 **2-tier**로 분리한다 — **비서(Lite) tier는 전역 상시 로딩**하여 어디서나 알투 비서를 유지하고, **PM(Full) tier는 `opi`로 초기화된 프로젝트에서만 로딩**한다. 이로써 "프레임워크는 사용자레벨 설치 + 부트스트랩(PM)은 프로젝트레벨 opt-in"을 달성한다.

## 배경

현재 `install-mac.sh`가 전역 마커를 4곳(`~/.claude/CLAUDE.md`·`~/.cursor/rules/000-opal-agent.mdc`·`~/.gemini/GEMINI.md`·`~/.codex/AGENTS.md`)에 삽입하여, **어느 디렉토리에서든 무거운 풀 부트스트랩(PRINCIPLES·harness·PM)이 무조건 로딩**된다. 캡틴은 OPAL 프레임워크를 사용자레벨에 설치하되, OPAL 프로젝트로서의 작동(PM·파이프라인)은 `opi`를 수행한 프로젝트에 한정하고 싶어한다. 단 전역 "알투 비서" 기능은 유지를 원한다.

## 배경 분석 (대화에서 도출)

- **현행 진입 메커니즘**: 전역 마커(install 삽입) → `~/.opal/AGENT.md` + `identity.md` Read → Eager 단계에서 PRINCIPLES·harness·opal-pm을 **무조건** 로드 (`~/.opal/AGENT.md` Eager step 2.5/3/4). 프로젝트 `.opal/AGENT.md`는 step 5에서 조건부 Read.
- **opi 현황**: `opi`(opal-project-init)는 이미 프로젝트 `CLAUDE.md`·`GEMINI.md`·`.cursorrules`에 OPAL 마커를 생성한다 (`opal/skills/opal-project-init/SKILL.md:561-568`). **Codex `AGENTS.md`는 누락**.
- **역할 전환 기준**: 현 AGENT.md 역할전환 표가 이미 `.opal/AGENT.md` 존재 여부로 비서/PM을 구분한다 (`~/.opal/AGENT.md` §행동 규칙 역할 전환 표). 즉 무거운 Eager 로드만 이 신호 뒤로 게이팅하면 된다.
- **install 마커 삽입 지점**: `scripts/install-mac.sh:1167-1186`(claude/cursor/gemini/codex), `scripts/install/windows.ps1` Register-Bootstrapper. 삽입이 `# === OPAL START === / END ===` 마커 단위 치환이므로, 마커 내용 교체만으로 구버전 능동 제거가 자동 충족된다.
- **`//opi` 발동 메커니즘**: `//` 커맨드 Lazy 트리거의 전제조건은 없음(`~/.opal/AGENT.md` Lazy 트리거 표: `| // 커맨드 입력 | harness/skill-commands.md | - |`). 따라서 비서 tier만으로도 `//opi`가 발동 가능 — 비-opi 폴더를 OPAL 프로젝트로 초기화하는 진입점이 보존된다.
- **setting.json**: 스킵게이트+머지는 부트스트랩 step 0(최초)에서 수행되며 비서 tier에 속한다. `bootstrap: off`(전역/프로젝트)와 models 우선순위는 본 작업으로 변경되지 않아야 한다.

## 확정된 설계 방향 (대화에서 합의)

1. **2-tier 모델**:
   - **비서(Lite) tier** — 전역 마커로 모든 세션 상시 로딩. 로드 대상: 스킵게이트(setting.json 머지) + `identity.md` + `PRINCIPLES.md`(헌법, 경량) + 보고 형식 + 도구·MCP 인지맵 + **`//` 커맨드/스킬 레지스트리 해석 능력**. (harness·opal-pm·프로젝트 컨텍스트는 로드하지 않음)
   - **PM(Full) tier** — `.opal/AGENT.md` **존재 시 승격**. 추가 로드: `opal-harness.md` + `opal-pm.md` + 프로젝트 `.opal/AGENT.md` + `PROJECT.md`/`MEMORY.md` 브리핑.
2. **PM 승격 게이트 = `.opal/AGENT.md` 존재** (가장 견고, opi가 생성, 현 역할전환 표와 정합). 프로젝트 마커는 Claude에선 보조(중복·무해), Gemini/Antigravity·Codex 이식성·폴백 트리거로 유지.
3. **전역 마커 = 경량 비서 마커로 교체** (Q2 "능동 제거" 재해석). 전역 비서를 유지하려면 전역 마커는 남아야 하므로, install이 구 무거운 마커를 신 경량 마커로 치환한다.
4. **opi 프로젝트 마커 = 전 플랫폼 생성 + Codex `AGENTS.md` 보강** (Q3 확정).
5. **setting.json 포맷·게이트·models 우선순위 불변** (Q 확인). `bootstrap: off`는 비서·PM 둘 다 스킵하는 전역/프로젝트 킬스위치로 그대로 동작.

> 캡틴 답변 3건: ① "전역 비서는 유지" ② 기존 전역 마커 "능동 제거(→경량 교체)" ③ opi "전 플랫폼 생성 + Codex 보강".

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 부트스트랩을 비서(전역)/PM(opi 프로젝트 한정) 2-tier로 분리. 비서는 전역 유지, PM은 `.opal/AGENT.md` 존재 시 승격 | - | `~/.opal/AGENT.md` Eager step 2.5/3/4 무조건 로드 |
| 범위 | **포함**: `~/.opal/AGENT.md`(소스) Eager 2-phase 재구성 + 부트스트래퍼 관리 절 논리 반전 / bootstrapper 소스 4종 / `install-mac.sh`+`windows.ps1` 마커 교체 / opi Codex AGENTS.md 보강·전 플랫폼 마커 / docs 정합. **제외**: setting.json 스키마 변경, models 매핑 로직 변경, 신규 게이트 값 도입, AGENT.md 물리 파일 분할 | - | - |
| 제약 | 배포 경계(`~/.opal/` 직접 편집 금지 — 소스만 수정 후 install 재배포) / 플랫폼 분기는 어댑터 계층(install)에만 / setting.json 동작 불변(회귀 0) / `//opi`는 비-opi 폴더에서 발동 가능해야 함(불변식) / 변경이력 행 추가 의무 | - | `.opal/AGENT.md` §금지사항 |
| 완료기준 | 아래 요구사항 AC + 동작검증: ①비서 전역 로드 ②비-opi 폴더에서 PM tier 미로드 ③비-opi 폴더에서 `//opi` 발동 가능 ④opi 후 PM tier 승격 ⑤setting.json off 스위치 정상 | - | - |

## 요구사항

- [ ] **R-1 (비서 tier 정의)**: `~/.opal/AGENT.md`(소스: `opal/` 내 해당 파일) Eager 단계를 2-phase로 재구성한다. **무엇을**: Phase A(비서, 항상)=스킵게이트+identity+PRINCIPLES+보고형식+도구맵 / Phase B(PM, 조건부)=harness+opal-pm+프로젝트 AGENT.md+컨텍스트. **어디에**: AGENT.md §부트스트랩 Eager 단계. **왜**: 확정 방향 §1. **AC**: AGENT.md Eager 절에 Phase A/B 구분이 명시되고, Phase B 진입 조건이 "`.opal/AGENT.md` 존재"로 기재된다.
- [ ] **R-2 (PM 승격 게이트)**: PM tier 로드(harness/opal-pm/프로젝트 컨텍스트)를 `.opal/AGENT.md` 존재 조건 뒤로 게이팅한다. **AC**: `.opal/AGENT.md` 부재 시 harness·opal-pm을 Read하지 않는 절차가 AGENT.md에 명문화된다.
- [ ] **R-3 (`//` 커맨드 불변식)**: 비서 tier가 `//` 커맨드/스킬 레지스트리 해석 능력을 보유함을 명문화한다. **AC**: AGENT.md에 "비서 tier에서 `//`(opi 포함) 발동 가능" 취지가 명시되고, 비-opi 폴더에서 `//opi`가 동작한다(동작검증).
- [ ] **R-4 (전역 마커 경량 교체)**: `install-mac.sh` + `windows.ps1`의 전역 마커 삽입을 경량 비서 마커로 교체한다(4 플랫폼). **AC**: install 재실행 시 `~/.claude/CLAUDE.md` 등 마커 내용이 신 경량 버전으로 치환되고 사용자 본인 내용은 보존된다.
- [ ] **R-5 (bootstrapper 소스 정합)**: `opal/bootstrapper/{claude,cursor,gemini,codex}-bootstrap.*` 4종을 2-tier 모델에 정합하도록 갱신한다(로직은 AGENT.md 보유, 마커 문구 정합). **AC**: 4개 파일 마커 문구가 경량 비서 진입과 일치하고 변경이력 행이 추가된다.
- [ ] **R-6 (opi 프로젝트 마커)**: opi가 전 플랫폼 프로젝트 마커를 생성하고 Codex `AGENTS.md` 템플릿을 보강한다. **AC**: opi 실행 시 `CLAUDE.md`+`GEMINI.md`+`.cursorrules`(또는 `.cursor/rules`)+`AGENTS.md`가 마커와 함께 생성되고, opi SKILL.md 산출물 표·변경이력에 반영된다.
- [ ] **R-7 (AGENT.md 부트스트래퍼 관리 절 반전)**: "프로젝트 부트스트래퍼 자동 관리" 절의 논리("프로젝트 마커는 잉여")를 2-tier 모델("전역=비서, 프로젝트=PM")로 반전 서술한다. **AC**: 해당 절이 Claude/Cursor/Codex/Gemini 각각에 대해 신 모델을 반영한다.
- [ ] **R-8 (setting.json 불변 — 회귀 0)**: setting.json 스키마·`bootstrap` 게이트·models 2-레이어 우선순위가 변경되지 않음을 보장한다. **AC**: 전역 `bootstrap: off`=전 세션 스킵, 프로젝트 `setting.local.json bootstrap: off`=해당 프로젝트만 스킵이 그대로 동작(동작검증).
- [ ] **R-9 (docs 정합)**: `docs/ARCHITECTURE.md`·`docs/CONVENTIONS.md`(해당 시)·`docs/PROJECT.md` 변경이력에 2-tier 모델을 반영한다. **AC**: ARCHITECTURE에 2-tier 부트스트랩 구조가 기술되고 PROJECT.md 변경이력 행이 추가된다.

## 제약 조건

- **배포 경계**: `~/.opal/` 배포 파일 직접 편집 금지. 소스(`opal/`, `scripts/`, `opal/skills/`)만 수정 후 install 재배포는 캡틴이 수행 (`.opal/AGENT.md` §금지사항).
- **플랫폼 분기 격리**: Claude/Cursor/Gemini/Codex 분기는 install 어댑터 계층에서만.
- **setting.json 동작 불변**: 회귀 0.
- **`//opi` 발동 불변식**: 비-opi 폴더(비서 tier만 로드)에서 `//opi`가 동작해야 한다.
- **변경이력 의무**: 수정한 스킬·참조·부트스트래퍼·문서에 변경이력 행(일시 KST + 태스크 번호 049) 추가.

## 기술 스택

- Markdown(부트스트래퍼·AGENT.md·docs), Bash(`install-mac.sh`), PowerShell(`windows.ps1`), 스킬 정의(opi SKILL.md + 템플릿)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL AGENT.md (부트스트랩 SSOT) | `opal/` 내 AGENT.md 소스 (배포본 `~/.opal/AGENT.md`) | Eager 2-phase 재구성·부트스트래퍼 관리 절 반전 대상 |
| D-2 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 전역 마커 삽입 지점(1167-1186) |
| D-3 | 소스 | windows.ps1 | `scripts/install/windows.ps1` | 전역 마커 삽입(Register-Bootstrapper) |
| D-4 | 소스 | bootstrapper 4종 | `opal/bootstrapper/{claude,cursor,gemini,codex}-bootstrap.*` | 전역 마커 콘텐츠 SSOT |
| D-5 | 소스 | opi 스킬 | `opal/skills/opal-project-init/SKILL.md` + `templates/` | 프로젝트 마커 생성·Codex 보강 대상 |
| D-6 | 설계 | PROJECT/ARCHITECTURE/CONVENTIONS | `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md` | docs 정합 대상 |
| D-7 | 설계 | 헌법 | `~/.opal/PRINCIPLES.md` | 비서 tier 포함 대상(경량) |
