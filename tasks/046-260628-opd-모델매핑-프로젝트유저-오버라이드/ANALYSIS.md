# ANALYSIS: 모델 매핑 provider별·등급별 오버라이드 (프로젝트/유저 2계층 setting)

> 작성일: 2026-06-28
> 입력: TASK.md
> 출력: ANALYSIS.md

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | 모델 매핑 SSOT — §5 오버라이드 스펙 현황 + 변경이력 v1.6 확인 |
| D-2 | 설계 | AGENT.md | `opal/core/AGENT.md` | §모델 매핑 자동 적용 섹션(v3.8 머지 지시 초안) + 변경이력 확인 |
| D-3 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §6 Model Mapping — 참조 구조 + 정합성 검증 |
| D-4 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 모델 베이킹 위치(563-567: mapping dict, 738-741: codex_model_map) + 전역성 확인 |
| D-5 | 설계 | agents.md | `opal/core/references/agents.md` | 모델 매핑 참조 타 문서로서 정합 확인 |
| D-6 | 설계 | setting.default.json | `opal/core/setting.default.json` | 현재 setting 스키마 키 확인 |
| D-7 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | ANALYSIS 인용 규칙(근거 제시 원칙, 포맷, 영역 간 용어 일관성) |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/references/opal-model-mapping.md` | 모델 매핑 SSOT — §1 레벨 정의 / §2 플랫폼별 매핑 표 / §5 오버라이드(신설) | ✅ 기존 작성됨, §5.1 폴백 입도 정밀화 필요 | `opal/core/references/opal-model-mapping.md:74-111` |
| `opal/core/AGENT.md` | 디스패치 직전 매핑 적용 지시 위치 — §모델 매핑 자동 적용(v3.8 머지 지시 초안) | ✅ 기존 작성됨, 본체 상세 보강 필요 | `opal/core/AGENT.md:371` + `:464` v3.8 변경이력 |
| `scripts/install-mac.sh` | Bash install 스크립트 — 글로벌 모델 베이킹(전역 설정만) | ❌ 변경 금지 (R-4) | `scripts/install-mac.sh:563-567`, `:738-741` |
| `opal/core/setting.default.json` | 기본 setting 스키마 — 현재 `{"bootstrap":"on"}` 하나만 | 선택 (`models` 키 예시 추가 가능) | 현재 1줄 파일 |
| `opal/core/references/agents.md` | 에이전트 레지스트리 — Codex tool-backed 인라인 주입 섹션 | ✅ 정합 확인 필요 | `opal/core/references/opal-model-mapping.md:29` 참조 기록 |
| `opal/core/references/opal-harness.md` | §6 Model Mapping — SSOT 참조만, 오버라이드 미언급 | 선택 (포인터 추가 여부 PLAN 판단) | `opal/core/references/opal-harness.md:178-187` |

### 1.2 아키텍처 패턴

**모델 매핑 결정 경로 (2가지)**:

**경로 1 — Install 시점 (전역 베이킹, 1회)** (`scripts/install-mac.sh:563-567`, `:738-741`)
- install-mac.sh가 opal-model-mapping.md §2 표 기본값을 읽어 각 에이전트 frontmatter의 model 필드를 실모델명으로 치환
- 결과: `~/.opal/agents/{agent_name}/AGENT.md` frontmatter에 `model: haiku` 등으로 베이킹
- **범위**: 플랫폼 전역만 가능(머신 wide). 프로젝트별 구분 불가
- **결론**: 프로젝트 오버라이드는 이 경로로 불가능

**경로 2 — 런타임 (디스패치 직전, 매번)** (`opal/core/AGENT.md:371`, v3.8 머지 지시)
- 오케스트레이터가 워커 디스패치 직전, 두 setting 파일 `models` 블록을 읽어 표 기본값 위에 머지
- 우선순위(셀 단위 deep merge): `{프로젝트}/.opal/setting.local.json` → `~/.opal/setting.json` → §2 표
- 폴백: 셀이 없거나 `"default"`이면 다음 우선순위로 폴백 (`opal/core/references/opal-model-mapping.md:86-87`)
- **결론**: 프로젝트별 세밀한 오버라이드가 가능한 유일한 경로

**핵심 제약**: install은 머신 전역이라 프로젝트를 알 수 없다 → 프로젝트 단위 오버라이드는 **런타임 해석(LLM이 파일 Read)으로만 가능**. 별도 실행 코드 경로 신설 금지 (OPAL 지시 기반 원칙).

### 1.3 의존성 맵

```
opal-model-mapping.md (SSOT, §2 표 기본값)
  ↓ 참조
AGENT.md (§모델 매핑 자동 적용, v3.8 머지 지시)
  ↓ 적용
워커 디스패치 직전 (runtime)
  ↓ 읽기 순서
1. {프로젝트}/.opal/setting.local.json (models 블록)
2. ~/.opal/setting.json (models 블록)
3. opal-model-mapping.md §2 표 (기본값)
  ↓ 결과
워커에 주입된 effective model 값

install-mac.sh (scripts/install-mac.sh:563-567, 738-741)
  ↓ 베이킹 (1회, 전역)
~/.opal/agents/*/AGENT.md frontmatter (전역 기본값)
  ↓ 런타임 오버라이드 미적용 시 fallback
```

**참조 의존성**:
- `install-mac.sh` → `opal-model-mapping.md` (READ 의존, `scripts/install-mac.sh:562`)
- `AGENT.md` → `opal-model-mapping.md` (READ 의존, v3.8 `opal/core/AGENT.md:464`)
- `agents.md` → `opal-model-mapping.md` (포인터 기록, `opal/core/references/opal-model-mapping.md:29`)
- `opal-harness.md` → `opal-model-mapping.md` (포인터, `opal/core/references/opal-harness.md:181`)

### 1.4 테스트 현황

**현재 상태**: 런타임 오버라이드 기능은 신설이므로 기존 테스트 없음.

**EXECUTE 후 검증 대상**:
- 셀 단위 deep merge (provider 블록 전체 누락 vs 특정 level 셀 누락의 폴백 차이)
- `setting.local.json` 미존재 시 유저→표 폴백
- `"default"` 값 처리 (폴백 트리거)
- `platform: "auto"` vs 강제 provider 설정 분기

---

## 2. 외부 조사 결과

해당 사항 없음. 외부 라이브러리 신규 도입 없이 프레임워크 내 문서 수정만 수행.

---

## 3. 영향 범위

### 3.1 직접 영향

| 파일 | 변경 내용 | 변경 사유 |
|------|----------|---------|
| `opal/core/references/opal-model-mapping.md` | §5.1 폴백 입도 정밀화 + §5.2 Cursor 처리 방식 주석 | R-1, R-T1, R-T3 |
| `opal/core/AGENT.md` | §모델 매핑 자동 적용 본체 상세 보강(셀 입도 폴백 명시) | R-2, R-T2 |
| `opal/core/references/opal-model-mapping.md` 변경이력 | v1.6 이미 갱신됨, 필요 시 추가 버전 | R-3 |
| `opal/core/AGENT.md` 변경이력 | v3.8 이미 기록됨, 보강 시 버전 추가 | R-3 |

### 3.2 간접 영향

| 문서 | 영향 분석 |
|------|---------|
| `opal/core/references/agents.md` | Codex tool-backed 인라인 주입 섹션 위치·내용 확인 후 모순 여부 판단 필요 (R-5) |
| `opal/core/references/opal-harness.md` | §6 현재 SSOT 참조만. 오버라이드 포인터 1줄 추가 여부 PLAN에서 판단 권고 |
| 배포본 (`~/.opal/references/opal-model-mapping.md`) | 소스 수정 후 install로 동기화 필요 (`opal/core/references/opal-model-mapping.md §6`) |

### 3.3 영향 범위 요약

- [x] DB 스키마 변경 — **없음**
- [x] API 인터페이스 변경 — **없음** (런타임 해석, 에이전트 호출 인터페이스 무변)
- [x] 설정/환경변수 변경 — **있음** (`models` 블록 신설, 기존 `bootstrap` 키와 독립)
- [x] 빌드/배포 파이프라인 변경 — **없음** (install 스크립트 불변, R-4)

---

## 4. 핵심 발견 사항

### 4.1 스펙 완성도 — spike 편집 현황 평가

| 항목 | 설계 선택 | 문서 현황 | 완성도 |
|------|---------|---------|--------|
| §5 오버라이드 섹션 신설 | 필수 | ✅ v1.6 (`opal/core/references/opal-model-mapping.md:74-111`) | 완성 |
| 스키마 코드블록 | 필수 | ✅ v1.6 (`opal/core/references/opal-model-mapping.md:90-100`) | 완성 |
| 3단 우선순위 명시 | 필수 | ✅ v1.6 (`opal/core/references/opal-model-mapping.md:80-86`) | 완성 |
| 셀 단위 폴백 규칙 | 필수 | ✅ v1.6 (`opal/core/references/opal-model-mapping.md:86-87`) | 완성 (입도 정밀화 필요 → R-T3) |
| 적용 경계(install 전역) | 필수 | ✅ v1.6 (`opal/core/references/opal-model-mapping.md:108-110`) | 완성 |
| AGENT.md 머지 지시 | 필수 | ⚠️ v3.8 변경이력 + 본체 초안 (`opal/core/AGENT.md:371`) | 부분 완성 (→ R-T2) |
| 타 문서 정합 | 필수 | ⏳ 미검증 | 미확인 (→ R-T5) |

### 4.2 AGENT.md v3.8 본체 내용 (실제 확인)

`opal/core/AGENT.md:368-373` §모델 매핑 자동 적용 섹션 현재 내용 (인용):

```markdown
> **오버라이드 (셀 단위, 위가 우선)**: `{프로젝트}/.opal/setting.local.json` → `~/.opal/setting.json` → 매핑 표.
>   디스패치 직전 두 setting 파일의 `models` 블록을 Read해 표 기본값 위에 머지한다
>   (셀이 없거나 `"default"`면 다음 우선순위로 폴백). `setting.local.json`은 사용자가 생성했을 때만 존재한다.
```

→ R-2 AC "≥1줄" 충족. 단, "셀이 없거나"의 입도(provider 블록 전체 vs level 셀 단위)가 미명시 → EXECUTE에서 보강 필요.

### 4.3 용어 일관성 점검 (`opal/core/references/harness/citation-rules.md` §7)

| 토큰 | §2 표 | install:563-567 | install:738-741 | AGENT.md 지시 | 일치성 |
|------|------|-----------------|-----------------|-------------|--------|
| provider 키 | `claude` `gemini` `openai` `codex` | `claude` `cursor` `gemini` `codex` | (codex 전용) | (미명시, "매핑 표" 참조) | ⚠️ cursor 처리 방식 명시 필요 |
| 레벨 키 | `light` `standard` `advanced` | `light` `standard` `advanced` | `light` `standard` `advanced` | `셀 단위` | ✅ 일치 |
| 설정 키 | `models` | (해당 없음, 베이킹) | (해당 없음, 베이킹) | `models` | ✅ 일치 |

### 4.4 Cursor provider inherit 처리 방식 상세 분석

- `scripts/install-mac.sh:565`: `'cursor': {'light': 'inherit', 'standard': 'inherit', 'advanced': 'inherit'}` — 모든 레벨이 `inherit` (IDE 위임)
- `opal/core/references/opal-model-mapping.md:64-73` §4 "Cursor 특이사항": 사용자가 설정한 모델 제공자(Claude/Gemini/OpenAI)에 따라 매핑이 달라지므로 provider를 추가 확인하거나 사용자에게 질문
- **결론**: Cursor는 레벨→모델 핀 자체가 없음(IDE 위임). 설정 스키마에 `cursor` 블록을 강제할 필요가 없음. 단, `platform: "cursor"` 강제 옵션 사용 시 "cursor=inherit, 등급핀 N/A" 처리를 §5.2 또는 §5.3에 명시하는 방안을 PLAN 결정사항으로 제시

---

## 5. 제약/리스크

| # | 항목 | 설명 | 심각도 | 근거 |
|---|------|------|--------|------|
| R-T1 | Cursor provider 스키마 처리 | cursor는 install에서 모든 레벨 `inherit`(IDE 위임, `scripts/install-mac.sh:565`). 등급별 모델 핀 대상이 없으므로 setting.json 스키마에 cursor provider 블록을 강제 추가할 필요 없음. 단, `platform: "cursor"` 강제 옵션 사용 시 "cursor=inherit(IDE 위임), 등급별 모델 핀 N/A" 주석 1줄을 §5.2 또는 §5.3에 추가하는 방안을 PLAN 결정사항으로 제시 | 낮음 (설계 명확화 사항) | `scripts/install-mac.sh:565` + `opal/core/references/opal-model-mapping.md §4:64-73` |
| R-T2 | AGENT.md 머지 지시 입도 불충분 | `opal/core/AGENT.md:371` 현재 지시가 "셀이 없거나 default면 폴백"까지는 있으나, provider 블록 전체 누락 vs level 셀 단위 누락의 폴백 입도가 미명시. EXECUTE 워커가 모호한 지시로 해석 오류 가능 | 중간 | `opal/core/AGENT.md:371` vs `opal/core/references/opal-model-mapping.md:86-87` |
| R-T3 | 폴백 입도 정밀화 필요 | `opal/core/references/opal-model-mapping.md:86-87` "각 `[provider][level]` 셀은 독립적으로 해석"의 "셀" 범위가 불명확. **정밀화 권고**: provider 블록 전체가 없으면 그 provider의 모든 level 셀이 폴백된다. 블록은 있고 특정 level 키만 없거나 `"default"`이면 그 셀만 폴백된다. PLAN에서 §5.1 문구를 이 입도로 정밀화 권고 | 중간 | `opal/core/references/opal-model-mapping.md:86-87` |
| R-T4 | setting.local.json 사용자 경험 | 설계(`opal/core/references/opal-model-mapping.md:108-110`)는 "사용자가 직접 만들었을 때만 동작"이나, 파일 생성 방법·위치·스키마 학습 부담이 문서화 부족으로 인한 기능 미활용 위험. setting.local.json 예제 스니펫 또는 사용자 가이드 1절 추가 권고 | 낮음 | `opal/core/references/opal-model-mapping.md:74-111` |
| R-T5 | 타 문서 정합 미검증 | `opal/core/references/opal-model-mapping.md:29` "agents.md §Codex tool-backed 인라인 주입" 참조 기록만 있음. agents.md 실제 섹션 위치·내용 미확인. `opal/core/references/opal-harness.md:181` §6는 현재 SSOT 참조만 — 오버라이드 도입 후 포인터 추가 필요 여부 미판단 | 낮음 | `opal/core/references/opal-model-mapping.md:29` + `opal/core/references/opal-harness.md:181` |
| R-T6 | setting.local.json gitignore 권고 | `opal/core/references/opal-model-mapping.md:110` "권장한다"는 문구만. 프로젝트 `.gitignore` 관리 책임·project init 스킬 연동이 미명시. 사용자가 실수로 커밋 가능 | 낮음 | `opal/core/references/opal-model-mapping.md:110` |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전/특성 |
|----------|------|----------|
| 문서 형식 | Markdown | SSOT — `opal/core/references/` |
| 설정 파일 | JSON | `setting.json` / `setting.local.json` 오버라이드 스키마 |
| 베이킹 스크립트 | Bash + Python 3 | `scripts/install-mac.sh:563-567` |
| LLM 플랫폼 | Claude / Gemini / OpenAI / Codex / Cursor | 플랫폼별 모델 매핑 |
| 런타임 해석 방식 | 에이전트 LLM이 파일 Read (지시 기반) | 별도 실행 코드 경로 신설 금지 |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| op-dev-execute | opal-model-mapping.md §5 및 AGENT.md 지시 정밀화 구현 |
| op-dev-plan | PLAN.md 수립 — §5.1 폴백 입도 정밀화, Cursor 처리 설계 결정, 타 문서 정합 체크리스트 |

### 6.3 추천 MCP

| MCP | 용도 |
|-----|------|
| (없음) | 외부 라이브러리 불필요 — JSON 표준 스키마, 프레임워크 내 문서 수정만 |

---

## 7. TASK 요구사항 커버리지

| 요구사항 | 현황 | 평가 |
|---------|------|------|
| R-1: opal-model-mapping.md §5 신설 (§5.1·§5.2·§5.3 + 셀 단위 폴백) | v1.6 `opal/core/references/opal-model-mapping.md:74-111` 완성 | ✅ 충족 (입도 정밀화만 필요) |
| R-2: AGENT.md 머지 지시 추가 (프로젝트→유저→표 + 셀 폴백 ≥1줄) | v3.8 `opal/core/AGENT.md:371` 본체 초안 있음, 상세 보강 필요 | ⚠️ 부분 충족 |
| R-3: 변경이력 갱신 + 헤더 버전 정합 | v1.6·v3.8 모두 기록됨 | ✅ 충족 |
| R-4: install 불변 검증 | `scripts/install-mac.sh:563-567`·`:738-741` 미변경 확인 | ✅ 충족 |
| R-5: 타 문서 정합 (agents.md Codex, opal-harness.md §6) | agents.md 위치 미확인, opal-harness.md 추가 필요성 미판단 | ⏳ 미완 |

---

## 8. PLAN 결정 사항 목록

EXECUTE 진입 전 PLAN에서 확정이 필요한 사항:

**P-1. §5.1 폴백 입도 정밀화 문구** (R-T3 해소)

PLAN에서 `opal/core/references/opal-model-mapping.md §5.1` 문구를 아래 입도로 정밀화 권고:
> "provider 블록 전체가 없으면 해당 provider의 모든 level 셀이 폴백된다. 블록은 있고 특정 level 키만 없거나 `"default"`이면 그 셀만 폴백된다."

**P-2. Cursor provider 처리 방안** (R-T1 해소)

cursor는 install에서 모든 레벨 `inherit`(IDE 위임)이므로 등급별 모델 핀 대상이 없다. 설정 스키마에 cursor 블록 강제 불필요. 권고 처리안: `platform` 강제 옵션 설명(`§5.2` 또는 `§5.3`)에 아래 주석 1줄 추가.
> `"cursor"`: IDE 위임(inherit) — 등급별 모델 핀 N/A. platform 강제 시에도 실모델 지정 불가.

**P-3. opal-harness.md §6 오버라이드 포인터 추가 여부**

현재 `opal/core/references/opal-harness.md:181`은 SSOT 참조만. 오버라이드 도입 후 "setting.local.json→setting.json→표 순 머지 적용" 1줄 포인터 추가 여부 결정 필요.

---

## 변경이력

| 버전 | 작성일 | 변경내용 |
|------|--------|---------|
| v1.0 | 2026-06-28 | 초기 작성 — TASK.md R-1~R-5 기반 분석. 모델 매핑 2가지 결정 경로(install 베이킹 / 런타임 해석) 구조 파악. §5 스펙 현황(v1.6 완성) + AGENT.md v3.8 초안(본체 보강 필요) 평가. Cursor inherit 처리 방식 명확화(R-T1). 폴백 입도 정밀화 권고(R-T3). 타 문서 정합 미검증(R-T5). 6종 리스크 + 3종 PLAN 결정사항 기록. |
