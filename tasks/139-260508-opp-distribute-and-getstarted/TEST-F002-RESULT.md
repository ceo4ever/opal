# TEST-F002-RESULT: F-002 Get Started UX 통합 검증 (139)

> 작성일: 2026-05-09 | 단계: Step 12 (F-002 통합 검증)
> 검증 방법: 정적 검증 (grep/Python 시뮬레이션) — 새 파일 생성·기존 파일 변경 없음
> 검증 대상: TS-012 / TS-013 / TS-014 / TS-015 / TS-016 / TS-017

---

## 시나리오별 검증 결과

| TS | 시나리오 | 결과 | 비고 |
|----|---------|------|------|
| TS-012 | 부트스트랩 보고 next-action 라인 추가 (형식 비파괴) | **PASS** | |
| TS-013 | identity 미존재 → onboarding 자동 발화 비파괴 | **PASS** | |
| TS-014 | (a) 분기 — `.opal/AGENT.md` 존재 시 메시지 정확 | **PASS** | |
| TS-015 | (b) 분기 — `.opal/AGENT.md` 미존재 시 메시지 정확 | **PASS** | |
| TS-016 | `//start` 매칭 — skill-registry | **PASS** | 소스 JSON 시뮬레이션 기준 |
| TS-017 | opal-onboarding triggers 등록 | **PASS (Partial)** | `//onboarding` SKILL.md triggers 등록 확인, JSON registry 매칭은 별도 주의 필요 |

---

## 상세 검증 근거

### TS-012: 부트스트랩 보고 next-action 라인 추가 (형식 비파괴)

**기대**: `[부트스트랩] ...` 한 줄 + `[안내] {next-action}` 별도 줄 추가. 기존 형식 변경 0건.

**검증 명령**:
```
grep -n '\[부트스트랩\]' opal/core/AGENT.md
grep -n '\[안내\]' opal/core/AGENT.md
```

**결과**:
- `opal/core/AGENT.md:53` — `[부트스트랩] ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ⏳ references ⏳ model-mapping`
- `opal/core/AGENT.md:54` — `[안내] {next-action}` (신규 추가)
- 변경이력 `opal/core/AGENT.md:314` — `(139)` 행 존재 확인

**판정**: PASS — 기존 `[부트스트랩]` 라인(53행)이 유지되고, 신규 `[안내]` 라인(54행)이 별도 줄로 추가됨. 형식 비파괴 의무 충족.

---

### TS-013: identity 미존재 → onboarding 자동 발화 비파괴

**기대**: `opal/core/AGENT.md` 내 opal-onboarding 자동 호출 경로가 변경 없이 유지.

**검증 명령**:
```
grep -n 'opal-onboarding' opal/core/AGENT.md
```

**결과**:
- `opal/core/AGENT.md:14` — `2. identity.md가 없으면 ~/.opal/skills/opal-onboarding/SKILL.md를 Read로 읽어 온보딩을 시작한다.`

**판정**: PASS — Eager 단계 Step 2의 onboarding 자동 호출 경로가 원본 그대로 유지됨. 신규 Step 6.5 삽입이 Step 2 경로에 영향 없음.

---

### TS-014: (a) 분기 — `.opal/AGENT.md` 존재 시 메시지 정확

**기대**: Step 6.5 a 분기 next-action = "프로젝트 작업이라면 `//opi` 또는 `//opp/opd/opds` 등으로 진입하세요" (PLAN §3.2.2 정합)

**검증 명령**:
```
grep -n -A 2 '6\.5' opal/core/AGENT.md
```

**결과**:
- `opal/core/AGENT.md:20` — `.opal/AGENT.md`가 존재 → 이 cwd는 OPAL 프로젝트 → next-action = "프로젝트 작업이라면 `//opi` 또는 `//opp/opd/opds` 등으로 진입하세요"

**PLAN §3.2.2 예시**: "프로젝트 작업이라면 `//opi` 또는 `//opp/opd/opds` 등으로 진입하세요"

**판정**: PASS — 실제 파일의 a 분기 메시지가 PLAN §3.2.2 예시와 정확히 일치.

---

### TS-015: (b) 분기 — `.opal/AGENT.md` 미존재 시 메시지 정확

**기대**: Step 6.5 b 분기 next-action = "프로젝트 초기화는 `//opi`, 일반 비서 작업은 자연어로 요청하세요" (PLAN §3.2.2 정합)

**검증 명령**:
```
grep -n -A 2 '6\.5' opal/core/AGENT.md
```

**결과**:
- `opal/core/AGENT.md:21` — `.opal/AGENT.md` 미존재 → 이 cwd는 비프로젝트 → next-action = "프로젝트 초기화는 `//opi`, 일반 비서 작업은 자연어로 요청하세요"

**PLAN §3.2.2 예시**: "프로젝트 초기화는 `//opi`, 일반 비서 작업은 자연어로 요청하세요"

**판정**: PASS — 실제 파일의 b 분기 메시지가 PLAN §3.2.2 예시와 정확히 일치.

---

### TS-016: `//start` 매칭 — skill-registry

**기대**: `//start` 입력 → `opal-start` 스킬 매칭

**검증 방법**: 소스 JSON(`opal/core/references/opal-skills-registry.json`) 기반 Node.js 매칭 시뮬레이션

**검증 결과**:

| 입력 | 매칭 결과 | 매칭 trigger |
|------|----------|-------------|
| `//start` | MATCH: opal-start (group: opal) | `^start$` (alias 추출 후) |
| `start` | MATCH: opal-start (group: opal) | `^start$` |
| `어디서부터 시작` | MATCH: opal-start (group: opal) | `(?i)(어디서부터\s*시작\|...)` |

**JSON SSOT 정합성**:
- `opal/core/references/opal-skills-registry.json` version: **3.4.0**
- opal 그룹 entries: 9개 (3.3.0 대비 opal-start 추가)
- opal-start 항목: name=`opal-start`, alias=`start`, triggers 3개

```json
{
  "name": "opal-start",
  "alias": "start",
  "triggers": [
    "^opal-start$",
    "^start$",
    "(?i)(어디서부터\\s*시작|다음에\\s*뭐\\s*해야|온보딩\\s*다시\\s*보고싶어)"
  ]
}
```

**주의**: `~/.opal/references/` (배포본) CLI 직접 실행 시 `found: false` 반환됨 — install 시 소스 JSON이 배포본으로 동기화되지 않은 현재 상태에서의 결과. 소스 JSON 자체는 정상 등록.

**판정**: PASS (소스 JSON 기준) — `//start` → alias `start` 추출 → `^start$` 매칭으로 opal-start 확인됨.

---

### TS-017: opal-onboarding triggers 등록

**기대**: `opal/skills/opal-onboarding/SKILL.md` frontmatter에 `triggers:` 키 존재 + `//onboarding`, `정체성 재설정`, `온보딩 다시` 3개 항목 존재

**검증 명령**:
```
grep -n -A 4 'triggers' opal/skills/opal-onboarding/SKILL.md
```

**결과**:
```yaml
# opal/skills/opal-onboarding/SKILL.md:6-9
triggers:
  - "//onboarding"
  - "정체성 재설정"
  - "온보딩 다시"
```

**3개 항목 존재 확인**: 완료

**변경이력 (139) 확인**:
- `opal/skills/opal-onboarding/SKILL.md:265` — `v1.1 | 2026-05-09 09:00 | triggers 신설 (//onboarding·정체성 재설정·온보딩 다시) + Step 9 //start·//onboarding 재호출 안내 추가 (139)`

**skill-registry CLI 매칭 (`//onboarding`) 분석**:

skill-registry.js 매칭 메커니즘 시뮬레이션:
1. `extractAlias("//onboarding")` → alias=`onboarding`, cleanInput=``
2. `matchByAlias(skills, "onboarding")` → opal-onboarding name=`opal-onboarding` (불일치), alias=`onb` (불일치) → **NO MATCH**
3. `matchByTriggers(skills, "//onboarding")` → JSON triggers = `["^opal-onboarding$"]` → **NO MATCH**

**결론**: skill-registry.js는 JSON SSOT triggers만 참조하며, SKILL.md frontmatter triggers는 참조하지 않음. `//onboarding` 입력이 skill-registry CLI에서 opal-onboarding에 매칭되지 않는 **잠재적 결함** 존재.

**SKILL.md frontmatter triggers 목적**: harness/skill-commands.md §쌍슬래시 커맨드 섹션에서 "스킬명(정식 또는 약식) 추출" 시 사람이 읽는 참조용. skill-registry CLI의 JSON triggers와는 별도 레이어.

**판정**: PASS (Partial) — SKILL.md frontmatter triggers 3개 항목 등록 완료. 단, skill-registry CLI의 `//onboarding` 매칭을 위해서는 JSON `opal-onboarding` triggers에 `"^onboarding$"` 추가 필요 (별도 태스크 권고).

---

## 추가 검증: 변경이력 (139) 일관성

**검증 명령**:
```
grep -n '(139)' opal/core/AGENT.md opal/skills/opal-onboarding/SKILL.md opal/skills/opal-start/SKILL.md
```

**결과**:
- `opal/core/AGENT.md:314` — v2.1 변경이력 (139) 존재
- `opal/skills/opal-onboarding/SKILL.md:265` — v1.1 변경이력 (139) 존재
- `opal/skills/opal-start/SKILL.md:72` — v1.0.0 초기 작성 (139) 존재

**판정**: PASS — F-002 영역 3개 파일 모두 (139) 변경이력 행 확인.

---

## 추가 검증: JSON SSOT 정합성

| 항목 | 기대 | 실제 | 결과 |
|------|------|------|------|
| version | 3.4.0 | 3.4.0 | PASS |
| opal 그룹 opal-start 존재 | 있음 | 있음 (name=opal-start, alias=start) | PASS |
| opal-start triggers 수 | 3개 | 3개 (`^opal-start$`, `^start$`, `(?i)...`) | PASS |

---

## //start 매칭 정규식 시뮬레이션 결과

```python
# 소스 JSON 정규식 기준 (opal/core/references/opal-skills-registry.json)
입력 "//start"    → alias="start" → ^start$ MATCH → opal-start
입력 "start"      → triggers ^start$ MATCH → opal-start
입력 "어디서부터 시작" → (?i)(어디서부터\s*시작) MATCH → opal-start
# 모두 PASS
```

---

## F-002 통합 검증 결론

| 항목 | 결과 |
|------|------|
| TS-012 ~ TS-016 | **PASS** |
| TS-017 | **PASS (Partial)** |
| 변경이력 (139) 일관성 | **PASS** |
| JSON SSOT 정합성 | **PASS** |

**종합 판정: F-002 통합 검증 완료 (TS-017 Partial — 기능 파생 결함 1건)**

### 발견된 주의 사항 (블로커 아님)

**[주의 1] `//onboarding` skill-registry CLI 미매칭**

- 원인: `opal-skills-registry.json`의 opal-onboarding `triggers` 배열에 `"^onboarding$"` 항목 미등록
- 현황: SKILL.md frontmatter triggers에는 `"//onboarding"` 등록됨. skill-commands.md §쌍슬래시 커맨드 흐름 (alias 추출 → matchByAlias → name/alias 비교)에서 `onboarding`은 `opal-onboarding` name 및 `onb` alias 모두 불일치
- 영향: `//onboarding` 직접 입력 시 skill-registry CLI 미매칭. PM이 수동으로 SKILL.md를 로드하거나 `//opal-onboarding` 정식명 입력 필요
- 해결 방안: `opal/core/references/opal-skills-registry.json` opal-onboarding triggers에 `"^onboarding$"` 추가 (본 태스크 범위 밖 — 별도 fix 권고)

**[주의 2] 배포본(~/.opal/references/) skill-registry 미동기화**

- 원인: 소스 수정 후 install 미실행 상태
- 영향: `node ~/.opal/tools/skill-registry/skill-registry.js match "//start"` → `found: false`. 소스 JSON은 정상
- 해결 방안: install-mac.sh 1회 실행 시 자동 동기화됨 (정상 배포 후 해소)
