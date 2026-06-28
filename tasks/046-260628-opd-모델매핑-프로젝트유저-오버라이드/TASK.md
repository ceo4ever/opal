# TASK: 모델 매핑 provider별·등급별 오버라이드 (프로젝트/유저 2계층 setting)

> 작성일: 2026-06-28 | 작업 유형: 개선 | 적용 스킬: opd | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

OPAL 모델 매핑(레벨 light/standard/advanced ↔ 플랫폼 모델)을 사용자가 setting 파일로 **provider별·등급별로 오버라이드**할 수 있게 한다. 유저 전역(`~/.opal/setting.json`)과 프로젝트(`{프로젝트}/.opal/setting.local.json`) 2계층을 두고, **프로젝트 > 유저 > 매핑 표** 우선순위로 런타임에 해석한다.

## 배경

현재 레벨↔모델 매핑은 `opal-model-mapping.md` 표 + install 스크립트(`install-mac.sh`, `windows.ps1`)에 **하드코딩·이중 관리**되어 있다. 사용자가 특정 등급의 모델을 바꾸려면 프레임워크 마크다운/딕셔너리를 직접 수정해야 하며, 프로젝트마다 다른 모델을 쓰는 길이 없다. 외부 설정으로 분리해야 할 전형적 케이스다.

## 배경 분석 (대화에서 도출)

- `setting.json`이 프레임워크에서 실제로 읽히는 키는 `bootstrap` 하나뿐 (읽는 곳: `AGENT.md` 스킵 게이트 + 4개 bootstrapper). 기본값 `opal/core/setting.default.json` = `{"bootstrap":"on"}`.
- 모델 매핑 결정 경로는 둘:
  - **install 시점**: `install-mac.sh:563-567` `mapping` dict + `:738-741` `codex_model_map`가 각 에이전트 frontmatter·인라인 sub-dispatch 토큰을 실모델명으로 베이킹 (전역, 1회).
  - **런타임**: `AGENT.md:371` "워커 디스패치 직전" 트리거에서 오케스트레이터가 `opal-model-mapping.md`를 읽어 레벨→모델 적용.
- **핵심 제약 발견**: install은 머신 전역이라 프로젝트를 알 수 없다 → 프로젝트 단위 오버라이드는 install 베이킹으로 불가능하고 **런타임 해석으로만** 가능하다.
- 현재 파일별 상태(대화 중 spike 편집 적용됨, EXECUTE 워커가 검증·완성 대상):
  - `opal/core/references/opal-model-mapping.md` — §5 "사용자·프로젝트 오버라이드" 초안 추가됨, 헤더 v1.4→v1.6, 변경이력 v1.6 추가됨, 기존 §5 갱신 가이드라인 → §6 재번호.
  - `opal/core/AGENT.md` — §모델 매핑 자동 적용에 오버라이드 머지 지시 초안 추가됨, 변경이력 v3.8 추가됨.

## 확정된 설계 방향 (대화에서 합의)

1. **이번 태스크는 `models` 키만** 다룬다 (orchestration/update/language 등 다른 후보 키는 제외).
2. **스키마** (유저·프로젝트 동일):
   ```json
   {
     "models": {
       "platform": "auto",
       "claude": { "light": "haiku", "standard": "sonnet", "advanced": "opus" },
       "gemini": { "advanced": "gemini-pro-latest" },
       "openai": { "standard": "gpt-5.4", "advanced": "gpt-5.5" }
     }
   }
   ```
3. **우선순위(셀 단위 deep merge)**: `{프로젝트}/.opal/setting.local.json` → `~/.opal/setting.json` → `opal-model-mapping.md` §2 표. 셀이 없거나 `"default"`이면 다음 우선순위로 폴백.
4. **배포는 전역에만**: install은 §2 표 기본값을 전역 베이킹만 한다. 프로젝트 베이킹·`setting.local.json` 자동 생성은 하지 않는다.
5. **프로젝트 오버라이드는 사용자가 직접 생성 시에만 동작**, 런타임(디스패치 직전) 적용.
6. `setting.local.json`은 개인 per-project 오버라이드 성격 → 프로젝트 `.gitignore` 권장(문서 안내).

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정 | 의존 사실 |
|------|--------|--------|----------|
| 목표 | provider(claude/gemini/openai/codex)×등급(light/standard/advanced) 매핑을 유저·프로젝트 setting으로 오버라이드. 프로젝트>유저>표 우선순위로 런타임 해석. | - | - |
| 범위 | **포함**: `opal-model-mapping.md` §5 오버라이드 명세, `AGENT.md` 디스패치 직전 머지 지시, 우선순위·셀 단위 폴백 규칙, 모델 매핑 참조 타 문서 정합. **제외**: install 스크립트 변경(전역 베이킹 유지), `models` 외 설정 키, `setting.local.json` 자동 생성. | - | install 전역성(`install-mac.sh:563-567`) |
| 제약 | install은 전역에만 배포(프로젝트 베이킹 금지). `setting.local.json`은 사용자 생성 시에만 동작. OPAL 지시 기반 — 런타임 해석은 LLM의 파일 Read로 수행(실행 코드 경로 없음). 배포 소스(`~/.opal`) 직접 수정 금지, 프로젝트 소스(`opal/`)만 수정. | - | `feedback_deploy_boundary` 메모리 |
| 완료기준 | `opal-model-mapping.md`에 §5 존재 + 스키마 코드블록 + 3단 우선순위 명시 + 셀 단위 폴백 규칙 + 적용 경계(install 전역). `AGENT.md` §모델 매핑에 프로젝트→유저→표 머지 지시 ≥1줄. 두 파일 변경이력 갱신. 모델 매핑 참조 타 문서와 모순 0건. | - | - |

## 요구사항

- [ ] **R-1**: `opal-model-mapping.md`에 §5 "사용자·프로젝트 오버라이드" 섹션 작성 — 무엇을: 오버라이드 명세(파일 위치·우선순위·스키마·적용 경계) / 어디에: `opal/core/references/opal-model-mapping.md` §5 / 왜: 확정 방향 §1~§6 / AC: §5.1 우선순위 3단(프로젝트→유저→표)·§5.2 스키마 코드블록·§5.3 적용 경계(install 전역) 3개 하위 섹션이 모두 존재하고 셀 단위 폴백 규칙이 명시된다.
- [ ] **R-2**: `AGENT.md` §모델 매핑 자동 적용에 머지 지시 추가 — 무엇을: 디스패치 직전 두 setting 파일 `models` 머지 지시 / 어디에: `opal/core/AGENT.md` §모델 매핑 자동 적용 / 왜: 런타임 해석이 유일한 프로젝트 오버라이드 경로(배경 분석) / AC: "프로젝트 setting.local.json → 유저 setting.json → 매핑 표" 우선순위와 셀 폴백이 기술된 지시 문장이 ≥1줄 존재한다.
- [ ] **R-3**: 변경이력 갱신 — 무엇을: 두 문서 변경이력 행 추가 + 헤더 버전 정합 / 어디에: `opal-model-mapping.md` 변경이력·헤더, `AGENT.md` 변경이력 / 왜: 문서 표준 / AC: 두 파일 모두 신규 버전 행이 추가되고 헤더 버전과 일치한다.
- [ ] **R-4**: install 전역 베이킹 불변 검증 — 무엇을: install 스크립트가 변경되지 않았음을 확인 / 어디에: `scripts/install-mac.sh`, `scripts/windows.ps1` / 왜: 확정 방향 §4 "배포는 전역에만" / AC: install 스크립트 diff 0건이며, §5.3에 "install은 전역 베이킹만" 경계가 문서화되어 있다.
- [ ] **R-5**: 모델 매핑 참조 타 문서 정합 — 무엇을: 모델 매핑을 참조하는 타 문서와 모순 없음 확인, 필요 시 포인터 1줄 보강 / 어디에: `agents.md`, `opal-harness.md` §6 등 / 왜: 일관성 / AC: 오버라이드 도입으로 기존 서술과 충돌하는 문장이 0건이다.

## 제약 조건

- install(배포)은 전역(`~/.opal`)에만 작용 — 프로젝트 단위 베이킹·파일 생성 금지.
- `setting.local.json`은 install이 생성하지 않으며, 사용자가 직접 만들었을 때만 런타임에서 동작.
- OPAL은 지시(instruction) 기반 — 모델 해석을 위한 별도 실행 코드 경로를 신설하지 않는다(LLM이 파일 Read로 해석).
- 배포 소스(`~/.opal/...`) 직접 수정 금지. 반드시 프로젝트 소스(`opal/...`)만 수정하고 install로 배포.

## 기술 스택

- Markdown 지시 문서 (OPAL 프레임워크 — `opal/core/...`)
- Bash/PowerShell install 스크립트 (참조·불변 확인 대상)
- JSON 설정 파일 (`setting.json` / `setting.local.json` 스키마)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | 모델 매핑 SSOT — §5 오버라이드 추가 대상 |
| D-2 | 설계 | AGENT.md | `opal/core/AGENT.md` | 디스패치 직전 매핑 적용 지시 위치 |
| D-3 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §6 Model Mapping 공통 인프라 (정합 확인) |
| D-4 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 전역 베이킹 위치(:563-567, :738-741) — 불변 확인 |
| D-5 | 설계 | agents.md | `opal/core/references/agents.md` | 모델 매핑 참조 타 문서 (정합 확인) |
