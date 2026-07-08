# QA-PLAN: 009-260524-opp-codex-bootstrapper-integration

> 검증 일시: 2026-05-24 (KST) | QA 워커: opal-task-qa-agent | 대상: PLAN.md

---

## 1. 요약

- **전체 판정**: CONDITIONAL_PASS
- **검증 항목**: 33개 / 통과 30개 / 미충족 3개
- **Blocker**: 0건
- **Major (보강 권고)**: 1건 — R-3 AC 충족 방식이 PLAN에 명시되었으나 TASK.md AC 원문과의 乖離에 대한 공식 설명이 명확하지 않음
- **Minor**: 2건

PLAN.md는 M-1~M-6 미확정 사항 전체를 공식 출처 URL + 파일 경로 인용으로 확정한 의사결정 문서로, 구조·인용 품질·실행 체크리스트 상세도 모두 우수하다. 8개 Step에 파일/작업 내용/완료 기준/테스트/의존이 명확히 기재되어 있고, R-T5 리스크(경로 표기 불일치)도 스스로 식별하여 대응 방안을 제시했다. 다만 R-3 AC와 PLAN 위임 전략 간 해석 차이가 EXECUTE 단계에서 오해를 유발할 가능성이 있어 보강을 권고한다.

---

## 2. 검증 결과 — 항목별

### A. 의사결정 품질 (§2 M-1~M-6)

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| A-1 | M-1~M-6 결정값 명확성 — 각 M-N이 1가지 결정으로 확정 | Pass | PLAN.md §2 결정 사항 요약 표: M-1~M-6 모두 단일 결정값 기재 |
| A-2 | 공식 URL/문서 인용 — 추측·미인용 주장 없음 | Pass | M-1: D-13 URL + 원문 인용. M-3: D-15 URL. M-4: D-17 + D-14 URL. M-5: D-14 URL + D-12 환경 근거. M-6: D-14 URL + 비교 근거 |
| A-3 | [MUST] §0 위반 여부 — 상상·추정·기억 기반 기재 없음 | Pass | M-5의 light 슬롯에서 `gpt-5-nano` 후순위 이유를 추론으로 보완했으나 주된 근거(`gpt-5-mini`는 D-14 명시 모델)로 뒷받침됨. citation-rules §5 "추론/경험 기반 결정" 예외 허용 범위 내 |
| A-4 | [MUST] 인용 토큰 — sub-agent 필수 3필드에 [MUST] 포맷 부착 | Pass | PLAN.md §3.3 U-1: `[MUST] [Subagents — Codex](...): "Every custom agent file must include three mandatory fields: name, description, developer_instructions."` |
| A-5 | M-2~M-6 결정값이 TASK.md M-1~M-6 미확정 사항과 1:1 매칭 | Pass | PLAN §2 각 M-N이 TASK.md 미확정 항목 표와 1:1 대응. 모든 조사 의무 사항이 PLAN에서 처리됨 |

### B. 실행 가능성 (§4 실행 체크리스트)

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| B-1 | 각 Step에 파일/작업 내용/완료 기준/테스트/의존 명확 | Pass | Step 1~8 전체에 5개 필드 모두 기재됨. grep 명령 기반 자동 검증 기준 포함 |
| B-2 | EXECUTE 워커가 PLAN.md만으로 작업 시작 가능 (추측 여지 없음) | Pass | §3.3 핵심 설계에 삽입될 코드 스니펫까지 명세. 줄번호 인용으로 편집 위치 명확 |
| B-3 | Phase 그룹핑(병렬/순차)이 의존 관계와 일치 | Pass | Phase 1: SSOT 5개 독립 병렬. Phase 2: install-mac.sh (Phase 1 의존). Phase 3: windows.ps1/linux.sh (독립 병렬). 의존 관계 정확 |
| B-4 | 완료 기준이 grep/명령으로 자동 검증 가능 (모호한 표현 없음) | Pass | 전 Step에 `grep -c`, `bash -n`, `python3 -c` 등 구체 검증 명령 포함 |

### C. TASK.md 요구사항 충족 (R-1~R-8)

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| C-1 | R-1 codex-bootstrap.md → Step 1 매핑 | Pass | PLAN §4 Step 1이 R-1 전체 AC를 커버 (파일 존재, 마커 블록, 변경이력 v1.0) |
| C-2 | R-2 install-mac.sh AC (a)(b)(c)(d) → Step 6 매핑 | Pass | PLAN §4 Step 6 완료 기준 항목 (a)~(d)가 R-2 AC 4개에 1:1 대응 |
| C-3 | R-3 linux.sh — 위임 패턴으로 AC 충족 주장의 명확성 | Warning | TASK.md R-3 AC: "linux.sh 실행 시 codex CLI가 PATH에 있으면 부트스트래퍼/어댑터/MCP 설치를 수행" — PLAN은 "install-mac.sh 위임으로 자동 상속"으로 처리하나, AC 원문의 "linux.sh 실행 시 codex 동작"을 위임 경로가 충족한다는 명시적 설명이 §4 Step 8 완료 기준에 없음. 위임 논리는 §1.3/§1.2/§3.1 U-2에 명시되어 있으나 완료 기준 자체에서 AC와의 연결을 한 문장으로 선언하지 않음 |
| C-4 | R-4 windows.ps1 → Step 7 매핑 | Pass | PLAN §4 Step 7 완료 기준 (a)~(d)가 R-4 AC 전체 커버 |
| C-5 | R-5 모델 매핑 → Step 2 매핑 | Pass | PLAN Step 2 완료 기준이 R-5 AC 전체 충족 (Codex 컬럼, 변경이력 v1.2) |
| C-6 | R-6 AGENT.md → Step 5 매핑 | Pass | PLAN Step 5가 R-6 AC 커버 (단, TASK.md R-6 AC의 파일 경로 `opal/AGENT.md`는 PLAN이 `opal/core/AGENT.md`로 보정 — R-T5에 리스크로 식별됨) |
| C-7 | R-7 PROJECT.md → Step 4 매핑 | Pass | PLAN Step 4 완료 기준이 R-7 AC 충족 |
| C-8 | R-8 변경이력 누락 금지 → 전체 수정 문서 명시 | Pass | PLAN §5.1 R-8: codex-bootstrap.md/opal-model-mapping.md/opal/core/AGENT.md/install-mac.sh/linux.sh/windows.ps1 나열. Step 2/4/5/6/7/8 각각에 변경이력 추가 명시 |

### D. 일관성 검증 항목 존재 여부 (§5.2)

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| D-1 | 모델 매핑 SSOT ↔ install-mac.sh ↔ windows.ps1 3곳 동기화 항목 존재 | Pass | PLAN §5.2 "모델 매핑 동기화" 항목 명시 (3곳 모두 명시) |
| D-2 | 마커 블록 문자 동일성 검증 항목 존재 | Pass | PLAN §5.2 "마커 블록 동일" 항목 명시 |
| D-3 | 함수 시그니처 일관성 검증 항목 존재 | Pass | PLAN §5.2 "함수 시그니처 일관성" 항목 + 기대 시그니처(인자 없음, warn+return) 명시 |
| D-4 | MCP 스코프 처리 일관성 검증 항목 존재 | Pass | PLAN §5.2 "MCP 스코프 처리 일관성" 항목 + 빈 문자열 처리 검증 방법 명시 |

### E. 리스크 식별 (§6)

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| E-1 | R-T1~R-T5 리스크 식별 + 구체적 대응 방안 | Pass | §6 리스크 표: 5개 리스크 모두 영향·대응 기재. R-T2 TOML escape 리스크 포함 |
| E-2 | TOML escape 리스크 다룸 | Pass | R-T2에서 `triple-quoted basic string + \ 및 " escape` 및 `tomllib.load` 파싱 검증 명시 |
| E-3 | Codex 모델 ID 변경 빈도 리스크 다룸 | Pass | R-T1에서 "D-16에서 사용자 UI에 gpt-5.5·gpt-5.3-Codex 등 새 ID 노출" + 분기마다 점검 대응 명시 |
| E-4 | nvm 경로 폴백 다룸 | Pass | R-T3에서 nvm 와일드카드 폴백 경로 명시 (`~/.nvm/versions/node/*/bin/codex`) |
| E-5 | 용어 일관성 — opal/AGENT.md vs opal/core/AGENT.md 다룸 | Pass | R-T5에서 경로 표기 혼선을 citation-rules §7 용어 일관성 위반으로 식별. PLAN §1.2 D-8 보정 기재 |

### F. 코딩 원칙 준수

| # | 검증 항목 | 결과 | 근거 |
|---|----------|------|------|
| F-1 | 사변적 추가 없음 — 범위 외 기능 없음 | Pass | Codex plugin 등록은 §7 남은 미확정 사항에서 "별도 태스크 후보"로 명시하고 현 PLAN 범위 제외 |
| F-2 | 인접 코드 개선 없음 — 기존 통합 리팩토링 없음 | Pass | §1.4 "무영향: Claude/Cursor/Gemini 기존 통합은 어댑터 계층 추가만". 각 Step도 기존 함수 분기 추가만 |
| F-3 | 불가능 시나리오 방어 코드 없음 | Pass | R-T1에서 모델 deprecation 가능성은 인정하되 방어 코드가 아닌 SSOT 갱신 지침으로 대응 |

---

## 3. TASK 요구사항 매핑 (R-1~R-8)

| TASK 요구사항 | PLAN.md 매핑 위치 | 충족 여부 | 비고 |
|--------------|------------------|----------|------|
| R-1 codex-bootstrap.md | §4 Step 1 / §3.3 N-1 | Pass | AC 3개 항목 모두 커버 |
| R-2 install-mac.sh | §4 Step 6 / §3.3 U-1 | Pass | AC (a)(b)(c)(d) 4개 항목 전체 커버 |
| R-3 linux.sh | §4 Step 8 / §3.3 U-2 / §1.2 D-5 / §1.3 | Warning | 위임 패턴 충족 근거는 §1.3에 있으나 Step 8 완료 기준에서 R-3 AC와의 명시적 연결 누락 |
| R-4 windows.ps1 | §4 Step 7 / §3.3 U-3 | Pass | AC 4개 항목 전체 커버 |
| R-5 opal-model-mapping.md | §4 Step 2 / §3.3 U-4 | Pass | AC 전체 커버 + 변경이력 v1.2 |
| R-6 opal/core/AGENT.md | §4 Step 5 / §3.3 U-5 | Pass | TASK.md 경로 표기 오류를 PLAN이 보정하여 올바른 경로 사용 |
| R-7 docs/PROJECT.md | §4 Step 4 / §3.3 U-6 | Pass | 변경이력 표 부재 조건 처리 명시 |
| R-8 변경이력 누락 금지 | §5.1 R-8 + 각 Step | Pass | 수정 대상 6개 파일 전체 명시 |

---

## 4. 발견사항

### 4.1 Blocker (PLAN 통과 불가)

없음.

### 4.2 Major (보강 권고)

**Major-1: R-3 AC와 위임 전략 연결 명시 미흡**

- **위치**: PLAN.md §4 Step 8 완료 기준
- **내용**: TASK.md R-3 AC는 "linux.sh 실행 시 codex CLI가 PATH에 있으면 부트스트래퍼/어댑터/MCP 설치를 수행"을 명시한다. PLAN은 linux.sh가 `exec bash install-mac.sh "$@"` 단순 위임이므로 install-mac.sh의 codex 분기가 자동 상속된다는 논리로 AC를 충족한다고 주장한다. 이 논리 자체는 타당하나, Step 8 완료 기준이 변경이력 1행 추가 여부(`grep -c 'v1.1 2026-05-24' scripts/install/linux.sh == 1`)와 구문 통과만 기재하고 있어, "linux.sh를 통한 codex 동작이 어떻게 보장되는지"를 EXECUTE 워커나 리뷰어가 Step 8만 보고 확인하기 어렵다.
- **권고**: Step 8 완료 기준 또는 테스트 항목에 다음 1문장 추가: "위임 검증: `bash scripts/install/linux.sh` 실행 시 install-mac.sh의 codex 분기가 실행되는 경로 확인 (`linux.sh:38` exec 위임으로 install-mac.sh codex 분기 자동 상속됨)"

### 4.3 Minor (개선 제안)

**Minor-1: Step 6 완료 기준 (b)의 grep 패턴 취약성**

- **위치**: PLAN.md §4 Step 6 완료 기준 (b)
- **내용**: `` `grep -c 'install_codex_agents' scripts/install-mac.sh` ≥ 3(정의 1 + 호출 1 + 헤더 변경이력 1) `` — 헤더 주석에 `install_codex_agents`가 실제로 들어가는지는 §3.3 U-1 (1)에서 명시된 변경이력 문자열에 따라 결정됨. 변경이력 주석 형식에 따라 count가 3보다 적을 수 있음.
- **권고**: 헤더 변경이력 주석에 `install_codex_agents` 단어가 포함된다는 것을 §3.3 U-1 (1)의 예시 문자열 `#   v2.6 2026-05-24: Codex CLI 통합 — install_codex_agents 신설 ...`에서 확인할 수 있음. 현재 예시에 명시되어 있어 실제 구현 시 count 3 달성 가능하나, 완료 기준에 "헤더 주석 포함 가정"을 각주로 추가하면 명확해짐.

**Minor-2: U-7 mcps/*.json 대상 파일 목록 미사전 확인**

- **위치**: PLAN.md §3.1 U-7 / §4 Step 3
- **내용**: `opal/core/mcps/*.json` 대상 파일들에 대한 조건 필터(install_type == config_merge AND command basename 화이트리스트)가 적시되어 있으나, 어떤 파일이 조건을 충족하는지 사전 목록이 없다. EXECUTE 워커가 직접 판단해야 함.
- **권고**: Step 3 작업 내용에 조건 충족 예상 파일 목록을 1회 나열하거나, 필터 명령(python3 one-liner)을 Step 3 완료 기준 테스트에 추가하여 EXECUTE 워커가 실행 전 대상을 확인할 수 있게 할 것.

---

## 5. 체크리스트 갱신 결과

- **PLAN.md §5 QA 체크리스트 총 14개 항목 중 5개 `[x]` 갱신** (§5.3 문서 품질 5개)
- §5.1 기능 테스트 10개: `[ ]` 유지 — EXECUTE 후 실측이 필요한 항목 (코드 구현 전)
- §5.2 일관성 테스트 5개: `[ ]` 유지 — EXECUTE 후 실측이 필요한 항목 (코드 구현 전)
- §5.3 문서 품질 5개: `[x]` 갱신 — PLAN.md 자체 내용으로 현 시점 검증 완료

**갱신 상세**:
| 항목 | 이전 | 이후 | 사유 |
|------|------|------|------|
| §5.3 한국어+영어 규칙 | `[ ]` | `[x]` | PLAN.md 전체 검토 — 규칙 준수 확인 |
| §5.3 kebab-case 파일명 | `[ ]` | `[x]` | codex-bootstrap.md, install_codex_agents 일관성 확인 |
| §5.3 변경이력 표 포맷 | `[ ]` | `[x]` | §8 변경이력 표 claude-bootstrap.md 패턴과 동일 |
| §5.3 §3.3 인라인 인용 의무 | `[ ]` | `[x]` | M-1~M-6 모든 결정에 D-N 단축 참조 + URL 확인 |
| §5.3 [MUST] 인용 | `[ ]` | `[x]` | §3.3 U-1에서 sub-agent 필수 필드 [MUST] 포맷 확인 |

---

## 6. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md M-1~M-6 | PLAN.md §2에서 모두 결정됨 (1:1 매핑) | Pass |
| TASK.md R-1~R-8 | PLAN.md §3~4에서 Step 1~8으로 분해 | Pass (R-3 Warning) |
| TASK.md 제약 조건 | 배포 경계/변경이력/하드코딩 금지/하네스 우회 금지 모두 PLAN에 반영 | Pass |
| citation-rules.md §0 | 상상·추정 기반 기재 없음 — M-1~M-6 모두 URL 인용 | Pass |
| citation-rules.md §2.4 | sub-agent 필수 필드 [MUST] 포맷 부착 확인 | Pass |
| citation-rules.md §7 | 용어 불일치(opal/AGENT.md vs opal/core/AGENT.md)를 R-T5로 식별 및 대응 | Pass |
| coding-principles.md §2 | 단순성 우선 — tomli_w 의존 회피, stdlib 문자열 빌딩 선택 (§3.3 U-1 명시) | Pass |
| coding-principles.md §4 | 외과적 변경 — linux.sh 코드 본문 무변경, 변경이력만 추가 | Pass |

---

## 7. 권고

**판정: CONDITIONAL_PASS**

PLAN.md는 M-1~M-6 미확정 사항을 공식 출처 인용으로 전부 확정하고, 8개 Step에 걸쳐 실행 체크리스트를 구체적으로 기술한 고품질 설계 문서다. Blocker가 없고 실행 가능성 측면에서 EXECUTE 워커가 PLAN.md만으로 작업을 시작할 수 있다.

다음 보강 사항을 적용 후 PM Gate 진입을 권고한다:

- **Major-1** (권고): Step 8 완료 기준에 "linux.sh 위임 경로가 R-3 AC를 충족함" 1문장 추가. 현재 EXECUTE 워커가 linux.sh 변경이력만 추가하고 "실제로 codex가 동작하는지" 검증하지 않을 위험.
- **Minor-2** (선택): Step 3에 대상 mcps/*.json 파일 목록 또는 필터 검증 명령 추가.

위 보강이 완료되면 PM Gate 진입을 권고한다. Major-1이 보강되지 않더라도, EXECUTE 워커가 §1.3의 위임 논리를 읽으면 충분히 이해 가능하므로 EXECUTE 진행 자체를 blocking하지는 않는다.
