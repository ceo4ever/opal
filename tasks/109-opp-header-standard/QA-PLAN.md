# QA-PLAN 109 — @header 표준 + code-scan 통합 워크플로우

**검증 대상**: `tasks/109-opp-header-standard/PLAN.md`  
**검증 기준**: `tasks/109-opp-header-standard/TASK.md` + PLAN.md §4 QA 체크리스트  
**검증일**: 2026-04-11  
**상태**: QA 완료

---

## 사전 검토 — §1 개요 오류

- [x] **§1 개요 오기 (Minor)**: PLAN.md §1 첫 문장이 "6개 파일을 변경/신규 작성한다"로 되어 있으나, §1 변경 대상 요약 테이블에는 7개 항목(#1~#7)이 포함되어 있다. 실제 변경 대상이 7개이므로 "6개"는 오기이다.
  - **권고**: EXECUTE 시 §1 첫 문장을 "7개 파일을 변경/신규 작성한다"로 수정할 것.

---

## §4 QA 체크리스트 전체 검증

### QA-1. header-standard.md 완결성

- [x] 7개 필드 모두 정의되었는가 (module / layer / domain / description / exports / depends / note)
  - 이유: §2-1 §2 필드 정의 테이블에 7개 필드 모두 명시됨.
- [x] exports 필드의 layer별 분기(최소 5개 layer 유형)가 명시되었는가
  - 이유: §2-1 §4 exports 작성 가이드에 router/controller/service/util/page/component/repository/model+schema/spec/analysis/report/skill 등 12개 이상 layer 유형이 명시됨.
- [x] 5개 언어 모두 예시가 제공되었는가 (TypeScript, Python, Vue, Kotlin, Swift)
  - 이유: §2-1 §3에 TypeScript/JavaScript, Python, Vue, Kotlin, Swift 5개 예시가 모두 포함됨. 추가로 md(HTML comment) 예시도 포함됨.
- [x] 삽입 위치 규칙에 shebang 예외가 명시되었는가
  - 이유: §2-1 §5에 shebang(`#!/...`)이 있으면 shebang 바로 다음 줄, 없으면 파일 첫 줄로 분기 규칙이 명시됨.
- [x] 적용 대상 확장자 목록이 code-scan.js `DEFAULT_CONFIG.extensions`와 일치하는가
  - 이유: §2-1 §6에 `.py .js .ts .jsx .tsx .vue .svelte .kt .kts .java .swift`로 명시. code-scan.js DEFAULT_CONFIG.extensions는 `['.py', '.js', '.ts', '.vue', '.jsx', '.tsx', '.svelte', '.kt', '.kts', '.java', '.swift']`로 동일한 11개 확장자 집합 확인됨. (md는 선택 확장자로 별도 분리하여 일치)
- [x] layer 표준값 테이블이 포함되었는가 (코드 layer + 문서 layer 구분)
  - 이유: §2-1 §2 "layer 표준값" 항목에 코드 layer와 문서 layer를 구분하여 명시됨.
- [x] module unique 권장 규칙이 명시되었는가
  - 이유: §2-1 §2 필드 정의 테이블의 module 필드 설명에 "프로젝트 내 unique를 권장한다"와 중복 시 의존 관계 추적 부정확 경고가 명시됨.
- [x] md 파일 HTML comment 예시가 포함되었는가
  - 이유: §2-1 §3에 md(HTML comment) 예시가 포함됨.
- [x] md 삽입 위치(YAML frontmatter 이후) 규칙이 명시되었는가
  - 이유: §2-1 §5에 "md 파일: YAML frontmatter(`---`) 다음에 삽입. frontmatter 없으면 파일 첫 줄"이 명시됨.

**QA-1 판정: PASS (9/9)**

---

### QA-2. opal-harness.md 수정 정합성

- [x] 새 §8이 §8 OPAL Tools 앞에 위치하는가
  - 이유: §2-2에 "§8 OPAL Tools 바로 앞에 새 섹션 `## 8. EXECUTE @header 규칙`을 삽입"으로 명시됨.
- [x] 기존 §8이 §9로 올바르게 번호 변경되었는가
  - 이유: §2-2에 "기존 §8을 `## 9. OPAL Tools`로 번호를 변경한다"고 명시됨.
- [x] 적용 대상 확장자 목록이 header-standard.md §6과 동일한가
  - 이유: §2-2 추가할 내용에 `.py .js .ts .jsx .tsx .vue .svelte .kt .kts .java .swift`로 명시. §2-1 §6과 동일함.
- [x] 파일 생성/수정 시 분기가 명확히 구분되는가
  - 이유: §2-2에 "### 파일 생성 시"와 "### 파일 수정 시" 두 하위 절로 분기가 명확히 구분됨.
- [x] 변경이력에 v3.6이 추가되었는가
  - 이유: §2-2 변경이력 추가에 v3.6 행이 명시됨.

**주의 (Minor)**: §2-2의 "Step 2 체크리스트 추가 항목"으로 "opal/core/AGENT.md에서 harness §8 참조 여부 확인 → 있으면 §9로 갱신"이 §2-2 내부에만 기술되어 있고 §3 Step 2 실행 체크리스트에는 누락되어 있다. EXECUTE 시 이 항목이 빠질 수 있음.
- **권고**: §3 Step 2 체크리스트에 "opal/core/AGENT.md harness §8 참조 존재 시 §9로 갱신" 항목 추가 필요.

**QA-2 판정: PASS (5/5, Minor 1건)**

---

### QA-3. opal-pm.md 수정 정합성

- [x] §4 검토 절차에 8번 항목이 추가되었는가
  - 이유: §2-3 수정 1에 8번 항목(code-scan.json 갱신 확인) 추가가 명시됨. 현재 opal-pm.md §4 검토 절차는 1~7번까지만 있어 8번 추가가 필요한 상태이며 PLAN에 반영됨.
- [ ] 8번 항목에 "EXECUTE 결과에 새 도메인 또는 폴더가 추가된 경우만 확인"이라는 범위 제한이 명시되었는가
  - 이유: §2-3 수정 1의 8번 항목 텍스트는 모든 code-scan 대상 확장자 파일에 @header 확인을 요구하는 방향으로 작성되어 있다. "EXECUTE 결과에 새 domain/scope 추가 시 code-scan.json 갱신 여부도 함께 확인"은 code-scan.json 갱신 확인의 조건부 언급이며, @header 확인 자체의 범위 제한이 아님. QA 체크리스트가 요구하는 "폴더 추가된 경우만"이라는 범위 제한이 명시적으로 없음.
  - **권고**: 8번 항목 문구에 "새 domain, scope, 또는 주요 폴더 추가 시"와 같이 폴더 추가 범위를 명시하거나, PM이 "모든 변경 파일 확인"으로 범위를 확정하고 §2-3 계획대로 진행할 것.
- [x] §9가 §8 다음에 위치하는가
  - 이유: §2-3 수정 2에 "§8 워커 행동 규칙 다음에 신규 `## 9. code-scan.json PM 관리 의무` 섹션을 추가한다"로 명시됨. 현재 opal-pm.md §8이 마지막 섹션이므로 §9 추가 위치가 정확함.
- [x] §9에 생성 시점, 갱신 트리거, PM Gate 확인 절차 3가지가 모두 포함되었는가
  - 이유: §2-3 수정 2 추가할 내용에 "### 생성 시점", "### 갱신 트리거", "### PM Gate 확인 절차" 3개 하위 절이 모두 포함됨.
- [x] 변경이력에 v1.1이 추가되었는가
  - 이유: §2-3 변경이력 갱신에 v1.1 행이 명시됨.

**QA-3 판정: FAIL (4/5)**
- 실패 항목: 8번 항목의 범위 제한 문구에 "폴더 추가" 명시 누락. EXECUTE 시 워커가 보완하거나 PM이 범위를 명확히 결정해야 함.

---

### QA-4. tools.md 수정 정합성

- [x] PM 관리 방안 서브섹션이 "프로젝트 설정" 바로 아래에 위치하는가
  - 이유: §2-4에 "'프로젝트 설정' 바로 아래에 `### PM 관리 방안` 서브섹션을 추가한다"로 명시됨. 현재 tools.md code-scan 섹션 구조("프로젝트 설정" → "사용 예시")를 확인한 결과, 추가 위치가 정확함.
- [x] opal-pm.md §9 교차 참조가 포함되어 있는가
  - 이유: §2-4 추가할 내용에 "상세 관리 절차: `opal-pm.md` §9 참조"가 명시됨.
- [x] 변경이력에 v1.2가 추가되었는가
  - 이유: §2-4 변경이력 갱신에 v1.2 행이 명시됨.

**QA-4 판정: PASS (3/3)**

---

### QA-5. 문서 간 일관성

- [x] header-standard.md 적용 대상 확장자 ↔ opal-harness.md §8 적용 대상 확장자 일치
  - 이유: §2-1 §6과 §2-2 추가할 내용 모두 동일한 11개 확장자 목록 사용.
- [x] opal-pm.md §9 생성/갱신 규칙 ↔ tools.md PM 관리 방안 내용 일치
  - 이유: §2-3 §9의 생성 시점, 갱신 트리거 내용이 §2-4 PM 관리 방안(생성 시점, 갱신 트리거, PM Gate 확인)과 일치함.
- [ ] opal-pm.md §9 교차 참조(tools.md) ↔ tools.md 교차 참조(opal-pm.md §9) 쌍방 포함 여부
  - 이유: §2-4 tools.md에 "opal-pm.md §9 참조"가 있으나, §2-3 opal-pm.md §9 추가할 내용에는 tools.md에 대한 역참조가 없다. 단방향 참조이므로 쌍방 참조 요건을 충족하지 못함.
  - **권고**: §2-3 §9 내용에 "도구 사용법: `opal/core/references/tools.md` code-scan 섹션 참조" 또는 유사한 역참조 추가 필요.
- [x] op-task/dev-execute의 대상 확장자 ↔ header-standard.md §6 일치
  - 이유: §2-5/§2-6 추가할 내용에 `.py .js .ts .vue .jsx .tsx .svelte .kt .kts .java .swift`로 명시됨. 순서에 일부 차이가 있으나 확장자 집합은 동일함.
- [x] opal-pm.md §4 8번 확인 방법(code-scan scan --json) ↔ tools.md PM 관리 방안 일치
  - 이유: §2-3 8번 항목에 "확인 방법: code-scan scan <file> --json 실행"이 명시됨. §2-4 PM 관리 방안에 "PM Gate 확인" 항목 포함됨.

**QA-5 판정: FAIL (4/5)**
- 실패 항목: opal-pm.md §9 → tools.md 역참조 누락 (단방향만 존재). EXECUTE 시 워커가 opal-pm.md §9 본문에 tools.md 역참조를 추가해야 함.

---

### QA-6. op-task-execute/op-dev-execute SKILL.md 수정 정합성

- [x] header-standard.md Read 지시가 포함되었는가
  - 이유: §2-5 추가할 내용에 "1. `~/.opal/references/header-standard.md` Read" 지시가 포함됨. §2-6도 동일.
- [x] 필수 필드 목록이 명시되었는가
  - 이유: §2-5에 "생성: 필수 필드 모두 작성 (module, layer, domain, description, exports)"가 명시됨.
- [x] 대상 확장자 목록이 header-standard.md §6과 동일한가
  - 이유: §2-5에 `.py .js .ts .vue .jsx .tsx .svelte .kt .kts .java .swift`로 명시됨. header-standard.md §6과 동일한 확장자 집합임.
- [x] 삽입 위치 규칙이 포함되었는가
  - 이유: §2-5에 "삽입 위치: 파일 최상단 (shebang/frontmatter 다음, 없으면 첫 줄)"이 포함됨.

**QA-6 판정: PASS (4/4)**

---

### QA-7. code-scan.js exports 커맨드

- [x] USAGE에 exports 커맨드 설명이 추가되었는가
  - 이유: §2-7에 USAGE 추가 내용으로 `exports <keyword>     Search within exports field only`가 명시됨.
- [x] cmdExports 함수가 exports 필드 배열을 대상으로 검색하는가 (전체 JSON 검색 아님)
  - 이유: §2-7 함수 구현 계획에서 `r.header.exports.some(e => e.toLowerCase().includes(kw))`로 exports 배열만 필터링함. 기존 code-scan.js의 `cmdSearch`와 달리 exports 필드 전용임.
- [x] domain/layer 필터(--domain, --layer)가 cmdExports에도 적용되는가
  - 이유: §2-7 구현 계획에서 `const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null })`로 전체 스캔 후 `opts.domain`/`opts.layer` 조건으로 재필터링하는 로직이 포함됨.
- [x] commands 객체에 exports가 등록되었는가
  - 이유: §2-7에 "`commands` 객체에 `exports: cmdExports` 등록"이 명시됨.
- [x] 변경이력 v1.1이 추가되었는가
  - 이유: §2-7 변경이력 추가에 v1.1 행이 명시됨.

**QA-7 판정: PASS (5/5)**

---

## 추가 확인 — TASK.md 요구사항 반영 여부

### 변경 대상 7개가 §1 테이블과 §2-1~§2-7에 모두 반영되었는가

| TASK.md 요구사항 | §1 테이블 | §2 상세 계획 |
|----------------|---------|------------|
| 2-1. header-standard.md 신규 | #1 포함 | §2-1 포함 |
| 2-2. opal-harness.md 수정 | #2 포함 | §2-2 포함 |
| 2-3. opal-pm.md 수정 | #3 포함 | §2-3 포함 |
| 2-4. tools.md 수정 | #4 포함 | §2-4 포함 |
| 2-5. op-task-execute/SKILL.md 수정 | #5 포함 | §2-5 포함 |
| 2-6. op-dev-execute/SKILL.md 수정 | #6 포함 | §2-6 포함 |
| 2-7. code-scan.js exports 커맨드 | #7 포함 | §2-7 포함 |

- [x] 7개 변경 대상 모두 §1 테이블과 §2-1~§2-7에 반영됨.

### §3 체크리스트 Step 1~7이 모두 있는가

- [x] Step 1 (header-standard.md): 있음
- [x] Step 2 (opal-harness.md): 있음
- [x] Step 3 (opal-pm.md): 있음
- [x] Step 4 (tools.md): 있음
- [x] Step 5 (op-task-execute/SKILL.md): 있음
- [x] Step 6 (op-dev-execute/SKILL.md): 있음
- [x] Step 7 (code-scan.js): 있음

### TASK.md 요구사항 2-1~2-7이 PLAN에 반영되었는가

- [x] 2-1 필드 정의 (module/layer/domain/description/exports/depends/note): PLAN §2-1 §2에 반영
- [x] 2-1 exports 통합 필드 layer별 분기: PLAN §2-1 §4에 반영
- [x] 2-1 언어별 주석 포맷 예시 5개: PLAN §2-1 §3에 반영
- [x] 2-1 삽입 위치(shebang 다음, 없으면 첫 줄): PLAN §2-1 §5에 반영
- [x] 2-2 파일 생성/수정 시 @header 규칙: PLAN §2-2에 반영
- [x] 2-2 적용 확장자 목록: PLAN §2-2에 반영
- [x] 2-3 §4 PM Gate 체크 항목 추가: PLAN §2-3 수정 1에 반영
- [x] 2-3 PM code-scan.json 관리 의무 섹션: PLAN §2-3 수정 2에 반영
- [x] 2-4 tools.md code-scan PM 관리 방안: PLAN §2-4에 반영
- [x] 2-5 op-task-execute @header 규칙: PLAN §2-5에 반영
- [x] 2-6 op-dev-execute @header 규칙: PLAN §2-6에 반영
- [x] 2-7 exports 커맨드: PLAN §2-7에 반영

---

## 종합 판정

| QA 항목 | 판정 | 비고 |
|---------|------|------|
| QA-1. header-standard.md 완결성 | PASS | 9/9 |
| QA-2. opal-harness.md 수정 정합성 | PASS | 5/5 (Minor 1건) |
| QA-3. opal-pm.md 수정 정합성 | FAIL | 4/5 — 8번 항목 범위 제한 문구 미완성 |
| QA-4. tools.md 수정 정합성 | PASS | 3/3 |
| QA-5. 문서 간 일관성 | FAIL | 4/5 — opal-pm.md §9 단방향 참조 |
| QA-6. SKILL.md 수정 정합성 | PASS | 4/4 |
| QA-7. code-scan.js exports 커맨드 | PASS | 5/5 |
| §1 개요 오기 | 경고 | "6개" → "7개" 수정 필요 |
| §3 Step 2 누락 항목 | 경고 | AGENT.md §8→§9 갱신 체크 누락 |

**최종 판정: CONDITIONAL PASS** — 2개 FAIL 항목을 EXECUTE 시 보완 적용 조건부 통과.

---

## EXECUTE 시 보완 사항

1. **[FAIL — QA-3]** §2-3 8번 항목 문구에 폴더 추가 범위 명시 또는 PM 범위 확정 필요
   - 현행 문구: "EXECUTE 결과 changed_files 중 code-scan 대상 확장자 파일에 @header가 올바르게 작성되었는가"
   - 권고 추가: "EXECUTE에서 변경된 code-scan 대상 확장자 파일에 한해 @header 확인 수행" 또는 "새 domain, scope, 또는 주요 폴더 추가 시" 범위 제한 명시
   - 대안: PM이 "모든 변경 파일 확인"으로 범위를 확정하고 §2-3 계획대로 진행

2. **[FAIL — QA-5]** opal-pm.md §9 추가 내용에 tools.md 역참조 추가 필요
   - 권고 추가 위치: §9 "PM Gate 확인 절차" 하위 또는 §9 말미
   - 권고 문구: "도구 사용법: `opal/core/references/tools.md` code-scan 섹션 참조"

3. **[Minor — QA-2]** §3 Step 2 체크리스트에 항목 추가 필요
   - 추가 항목: "[ ] `opal/core/AGENT.md`에서 harness §8 참조 여부 확인 → 있으면 §9로 갱신"

4. **[경고 — §1]** §1 개요 첫 문장 수정 필요
   - "6개 파일을 변경/신규 작성한다" → "7개 파일을 변경/신규 작성한다"
