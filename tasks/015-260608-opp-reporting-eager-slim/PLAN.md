# PLAN: 보고 형식 Eager 슬림화 + 헌법 문체 재작성

> 작성일: 2026-06-08
> 입력: `tasks/015-260608-opp-reporting-eager-slim/TASK.md`
> 출력: PLAN.md
> 모드: agentic | 적용 스킬: opp | 작업 유형: 개선(문서 보고 형식 변경, 코드 로직 불변)

---

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | TASK.md | `tasks/015-260608-opp-reporting-eager-slim/TASK.md` | 요구사항 R1~R6·확정 방향 5개·배경 분석 |
| D-2 | 설계 | PRINCIPLES.md (헌법) | `opal/core/PRINCIPLES.md` | 문체 기준 (§2 Simplicity / Core Stance "Enforce, don't just advise" / Governance "stays short") |
| D-3 | 설계 | reporting-template.md | `opal/core/references/harness/reporting-template.md` | 이전/삭제 대상 원본 (§1~§9 전체) |
| D-4 | 설계 | AGENT.md | `opal/core/AGENT.md` | 인라인 대상 §보고 형식(207~225) + Eager Step 6.6(24행) |
| D-5 | 설계 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` | §8 단계전환 양식 이전 대상 (게이트 흐름 SSOT) |
| D-6 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §2 모듈 테이블 reporting-template 행(98) + §1 Guards |
| D-7 | 설계 | opal-pm.md | `opal/core/references/opal-pm.md` | §8 보고 형식 트리거(100~108) |
| D-8 | 설계 | opal-harness-interactive.md | `opal/core/references/opal-harness-interactive.md` | R4 ④ 대상 — grep 결과 reporting-template 참조 **0건** (§4 참고) |
| D-9 | 소스 | install-mac.sh | `scripts/install-mac.sh` | R5 배포 정합 — references/ 클린·복사 메커니즘 |
| D-10 | 소스 | windows.ps1 / linux.sh / macos.sh / install.ps1 | `scripts/install/`, `scripts/` | R5 동기 지점 전수 조사 |
| D-11 | 설계 | citation-rules.md | `opal/core/references/harness/citation-rules.md` | 인용 포맷 (§2 4종 / §2.4 [MUST]) |

> 인용 형식: `citation-rules.md` §3.1. 유형: 기획/설계/소스/외부.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/core/AGENT.md` | Eager 부트스트랩 + §보고 형식 인라인 대상 | ✅ 수정 | `AGENT.md:24` Step 6.6 / `AGENT.md:207-225` §보고 형식 / `AGENT.md:55` 부트스트랩 완료 보고 |
| `opal/core/references/harness/reporting-template.md` | 삭제 대상 원본 (318줄) | ✅ 삭제 | `reporting-template.md:1-325` 전체 |
| `opal/core/references/opal-harness-semi-agentic.md` | §8 단계전환 양식 이전처 | ✅ 수정 | `opal-harness-semi-agentic.md:91-101` §8 차이표(삽입 인접 지점) |
| `opal/core/references/opal-harness.md` | §2 모듈 테이블 행 | ✅ 수정 | `opal-harness.md:98` reporting-template 행 |
| `opal/core/references/opal-pm.md` | §8 보고 형식 트리거 | ✅ 수정 | `opal-pm.md:100-108` §8 |
| `opal/core/references/opal-harness-interactive.md` | R4 ④ 명시 대상 | ❌ 변경 불요 | grep `reporting-template` **0건** — 본 PLAN §4 M-7 참조 |
| `scripts/install-mac.sh` | references/ 클린+복사 | ❌ 변경 불요 | `install-mac.sh:866-872` rm -rf references / `:1144` cp -Rf / `reporting-template` literal **0건** |
| `scripts/install/windows.ps1` | references/ 클린+복사 | ❌ 변경 불요 | `windows.ps1:425` $cleanDirs / `:520-526` 복사 / literal **0건** |
| `scripts/install/{linux,macos}.sh`, `scripts/install.ps1` | install-mac.sh / windows.ps1 위임 래퍼 | ❌ 변경 불요 | `linux.sh:39` exec 위임 / `install.ps1` tarball 부트스트랩 |

### 현재 상태

**Eager 로드 실측** (TASK.md 배경 §2): 8개 파일·1,230줄·약 59KB. `reporting-template.md`(318줄/9KB)가 단일 최대 비중이며, 그중 §8(128줄)+§9(78줄)=65%가 매 응답에 불필요.

**reporting-template.md 구조** (`reporting-template.md:1-325` Read 확인):
- §1~§7 (1~111): 핵심 규범 — 3블록 구조, 다음 블록 2갈래, 일목요연, 시각 구분, 형식 자율성, 적용 범위, 비보고 예시. **매 응답 적용** → 압축해 AGENT.md 인라인.
- §8 (113~239): 단계 전환 보고 양식 3종(PLAN/EXECUTE/CLOSE 5요소). **게이트 시점 전용** → semi-agentic.md 이전.
- §9 (241~317): 예시 카드 — 문서 스스로 "비규범적 참고용"(`:243`) 명시. → 삭제.
- 변경이력 (319~325).

**참조처 전수 (grep `reporting-template` over `opal/` `scripts/`)**:
- `AGENT.md:24` (Eager Step 6.6 Read 지시)
- `AGENT.md:210` (§보고 형식 stub 탐색 경로)
- `opal-pm.md:105` (§8 탐색 경로)
- `opal-harness.md:98` (§2 모듈 테이블 행)
- `reporting-template.md:183,225` (자기 문서 내부 예시 텍스트 — 삭제와 함께 소멸)
- 변경이력 행 3건(`AGENT.md:343`, `opal-pm.md:144`, `opal-harness.md:284`) — **과거 이력이므로 불변 보존**.
- **`opal-harness-interactive.md`: 0건.**

**install 배포 메커니즘** (`install-mac.sh:866-872, 1144`): references/는 매 install마다 `rm -rf "$opal_home/references"` 후 `cp -Rf "$ref_src"/. "$ref_dst"/`로 **통째 클린+복사**된다. `reporting-template` literal은 어떤 install 스크립트에도 없다. windows.ps1(`:425,520-526`)도 동일 클린+복사. linux/macos.sh·install.ps1은 위임 래퍼.

**AskUserQuestion 도구**: grep 결과 `opal/` 전체에 기존 참조 **0건** → 본 태스크가 도입하는 신규 보고 규범.

### 영향 범위

- **Eager 절감**: reporting-template.md(318줄) 제거 + AGENT.md §보고 형식에 ~35줄 인라인 = 순 약 -283줄 / 약 -8KB Eager 감소.
- **Read 깨짐 리스크**: AGENT.md/opal-pm.md/opal-harness.md 3곳의 reporting-template Read 지시를 갱신하지 않으면 삭제 후 Read 실패. (interactive·install은 참조 없음 → 무영향.)
- **게이트 흐름 정합**: §8 단계전환 양식의 `🎯 결론`/`🔍 근거` 2블록 표기가 신규 통합 골격(🎯 결론·근거 1블록)과 어긋나므로, 이전 시 표기 갱신 필수.
- **동작검증 영역 불변**: state-tool·게이트 코드 로직 미변경. TEST-SCENARIO 불요 (TASK.md 제약).

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성
| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| — | (없음) | 확정 방향 5 "신규 파일 0개" | `TASK.md:64` |

#### 수정
| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| 1 | `opal/core/AGENT.md` | §보고 형식(207~225) → 헌법 문체 인라인(~35줄) 대체 / Eager Step 6.6(24) reporting-template Read 지시 → "§보고 형식 인라인 활성화"로 치환 / 변경이력 015 행 | R1, R4①, R6 |
| 2 | `opal/core/references/opal-harness-semi-agentic.md` | §8 단계전환 5요소 양식 3종 삽입(신규 §10) + 🎯 결론·근거 통합 표기로 갱신 / 변경이력 015 행 | R2, R6 |
| 3 | `opal/core/references/opal-harness.md` | §2 모듈 테이블 reporting-template 행(98) 제거·재지정 / 변경이력 015 행 | R4②, R6 |
| 4 | `opal/core/references/opal-pm.md` | §8 탐색 경로(105) → "AGENT.md §보고 형식 인라인"으로 재지정 / 변경이력 015 행 | R4③, R6 |

#### 삭제
| # | 파일 경로 | 사유 |
|---|----------|------|
| 1 | `opal/core/references/harness/reporting-template.md` | §1~§7 인라인 이전 + §8 semi-agentic 이전 + §9 비규범 예시 폐기 → 잔여 0 (R3) |

> **R4④·R5는 "변경 불요" 결론**: interactive.md엔 reporting-template 참조가 없고(M-7), install 스크립트는 references/ 통째 클린+복사라 삭제가 자동 전파된다(M-8). 단, §3 체크리스트에 **잔존 참조 0건 grep 검증 Step**으로 명시 확인한다.

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | §8 양식 semi-agentic.md 이전 + 통합 표기 갱신 | opal-harness-semi-agentic.md | 중 (§8 본문 이전 + 표기 일괄 치환) |
| 2 | AGENT.md §보고 형식 인라인 + Step 6.6 치환 | AGENT.md | 상 (R1 핵심 — 헌법 문체 신규 작성) |
| 3 | opal-harness.md §2 행 재지정 | opal-harness.md | 하 |
| 4 | opal-pm.md §8 재지정 | opal-pm.md | 하 |
| 5 | reporting-template.md 삭제 | (삭제) | 하 |
| 6 | 잔존 참조 0건 grep 검증 | (전체) | 하 |

> 원칙: 이전처(semi-agentic §8)·인라인처(AGENT.md)를 **먼저 완성**한 뒤(Step 1·2), 참조 갱신(Step 3·4) → 마지막에 원본 삭제(Step 5) → 잔존 검증(Step 6). 삭제 전 모든 콘텐츠가 새 위치에 존재함을 보장한다.

---

### 핵심 설계

#### M-1. [R1 핵심] AGENT.md §보고 형식 인라인 초안 (헌법 문체, ~35줄)

`AGENT.md:207-225`의 기존 §보고 형식(reporting-template.md Read 지시 + 3블록 stub + 역할별 표기 + Observability)을 아래 인라인 본문으로 **대체**한다. 역할별 응답 표기 표(`AGENT.md:215-221`)와 Observability 선언(`:223-225`)은 보고 형식 규범과 별개이므로 **그대로 유지**하고, 그 위의 stub(`:209-213`)만 교체한다.

문체 기준: `opal/core/PRINCIPLES.md` 구조 — "골격(고정) → 원칙 → 작동하는가". (→ D-2)
설계 근거: 확정 방향 1·2·3·4·5 (`TASK.md:45-64`).
[MUST] `opal/core/PRINCIPLES.md` §Core Stance: "Enforce, don't just advise: if a rule must always hold, a tool gates it — not prose." → 의사결정을 AskUserQuestion 도구로 강제(방향 2)하는 직접 구현.

**삽입 본문 전문** (AGENT.md `### 보고 형식` 헤딩 하위, 역할별 표기 표 위에 위치):

````markdown
> 적용 범위: PM(태스크) · PM(대화) · 비서 모드 모든 응답. 게이트 3종 보고는 `references/opal-harness-semi-agentic.md` §단계전환 양식.
> 골격·AskUserQuestion은 PM(태스크)·PM(대화)·비서 전 모드 적용. ▶️ 승인 대기는 다음 액션(수정·제안·단계 진행)이 있는 응답에만 적용하고, 단순 정보·확인·인사는 비보고 자유 형식.

**골격 (고정)**

🎯 결론·근거 → ▶️ 진행 (또는 AskUserQuestion 도구). 블록 사이 `---` 구분선.

🎯 결론·근거 — 결론과 근거를 한 블록에 통합한다. 레이아웃은 **항상 들여쓰기 불릿**: 결론 항목 줄 + 하위 `-` 근거.

```
🎯 결론·근거

1) <결론 항목>
   - <근거/증거>
   - <근거/증거>

2) <결론 항목>
   - <근거/증거>
```

**원칙**

- 의사결정은 도구로 강제한다 — 선택형 의사결정은 텍스트 질문이 아니라 `AskUserQuestion` 도구를 호출한다. 첫 옵션에 "(권고)"를 붙이고 권고 이유를 짧게 단다. (열린 서술형 질의는 도구의 Other 또는 텍스트로 허용 — 도구는 "선택형"에 한한다.)
- 진행은 자동으로 넘기지 않는다 — 단순 진행은 `▶️ 다음 진행 사항입니다.` 헤딩 + 번호 리스트로 제시하되, 끝에 "~ 승인(확인)해주시면 계속 진행하겠습니다"로 통제권을 소유자에게 넘긴다. 자동 진행 금지.
- 한눈에 본다 — 결론·근거 항목은 3개 이내, 표·리스트 우선·산문 최소, ASCII 박스 금지. 항목 사이는 빈 줄로 분리.
- 자율을 보존한다 — 골격·원칙 외 표현(표/리스트/산문 선택, 용어 풀이, 다음 블록 생략)은 자율 판단한다. 단순 확인·단문 답변·인사 등 비보고 응답은 골격을 적용하지 않고 자유 형식으로 처리한다.

**작동하는가**

- 결론만 읽고 판단할 수 있고, 근거가 바로 아래 붙어 있는가.
- 선택이 필요한 순간 도구가 떴는가 (텍스트 ❓로 묻지 않았는가).
- 소유자 승인 없이 다음 단계로 자동 진행하지 않았는가.
````

> 위 본문은 약 35줄(코드블록 포함)이다. 기존 `🎯 결론`+`🔍 근거`+`❓`/`▶️` 4종 헤딩을 `🎯 결론·근거`(1블록)+`▶️ 진행`/AskUserQuestion(도구)로 통합한다. (→ M-2, M-3)

#### M-2. [방향 1] 결론·근거 통합 = 1블록 + 항상 들여쓰기 불릿

기존 2블록(`reporting-template.md:23-24` `🎯 결론` / `🔍 근거`)을 1블록 `🎯 결론·근거`로 통합. 레이아웃은 캡틴 확정에 따라 **항상 들여쓰기 불릿**으로 고정 (`TASK.md:45`). 일목요연(항목 3개 이내)·시각 구분(빈 줄 분리)은 `reporting-template.md:55-75` §3·§4에서 압축 계승 (`TASK.md:80` 제약 — 통합 후에도 유지).

#### M-3. [방향 2·3] 의사결정=AskUserQuestion / 진행=승인 대기

- **의사결정**: 텍스트 `❓ 의사 결정해 주세요?` 블록(`reporting-template.md:27,45`)을 **폐지**하고 `AskUserQuestion` 도구 호출로 대체. 첫 옵션 "(권고)" 표기. (`TASK.md:58`) — 헌법 "Enforce with a tool, not prose"의 구현(M-1 [MUST]).
- **진행**: `▶️ 다음 진행 사항입니다.` 헤딩 유지하되 자동 진행 금지, "~ 승인(확인)해주시면 계속 진행하겠습니다" 형태로 통제권 이양 (`TASK.md:60`).
- **하네스 우회 아님**: AskUserQuestion 도입은 보고 형식 규범 변경이며 CLOSE 진입 게이트 등 기존 Guards는 불변 (`TASK.md:78` 제약). [MUST] `opal/core/references/opal-harness.md` §1 Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내릴 때까지 코드를 작성하거나 파일을 생성/수정하지 않는다."

#### M-4. [R1] AGENT.md Eager Step 6.6 치환

`AGENT.md:24`:
- **Before**: `6.6. `~/.opal/references/harness/reporting-template.md`를 Read한다 → 3블록 구조(결론·근거·다음)를 세션 시작부터 활성화한다.`
- **After**: `6.6. (삭제 — 보고 형식은 본 AGENT.md §보고 형식에 인라인되어 별도 Read 불요. Eager 로드 대상에서 제외한다.)` → 실제로는 **Step 6.6 자체를 삭제**하고 Step 번호 흐름(6.5 → 7)을 보존. 단, 부트스트랩 완료 보고(`AGENT.md:55`)의 `✅ reporting` 칼럼은 **유지**한다(인라인이 곧 reporting 활성화이므로 의미 보존) — 또는 칼럼 제거. → **M-4-a 결정 필요** (아래).

> **M-4-a (설계 결정)**: 부트스트랩 완료 보고 `[부트스트랩] ✅ ... ✅ reporting ...`(`AGENT.md:55`)에서 `✅ reporting`을 **유지**할지 제거할지. **권고: 유지** — reporting은 이제 AGENT.md 인라인으로 항상 활성(Eager 본문의 일부)이므로 `✅ reporting`은 여전히 참이다. 제거하면 부트스트랩 산출물 포맷이 바뀌어 회귀 비교가 깨진다. 따라서 Step 6.6 Read만 제거하고 완료 보고 칼럼은 그대로 둔다.

#### M-5. [R2] §8 단계전환 양식 → semi-agentic.md 이전 위치·형태

**삽입 위치**: `opal-harness-semi-agentic.md`의 현행 §9(유지 규칙, `:103-106`) **뒤, 변경이력(`:108-`) 앞**에 신규 **§10. 단계 전환 보고 양식 (캡틴 게이트 3종)**으로 삽입.

근거: semi-agentic.md는 §6 CLOSE 진입 게이트(`:58-75`)·§8 차이 표(`:91-101`)로 게이트 흐름 SSOT를 보유 → 게이트 시점 보고 양식의 자연스러운 귀속처. §9(유지 규칙) 뒤가 "규칙류"의 마지막이므로 양식 블록을 그 뒤에 부록처럼 배치하면 흐름 단절이 없다.

**이전 내용**: `reporting-template.md:119-239` §8.1/§8.2/§8.3의 5요소 표준 표 + 양식 예시 3종을 그대로 이전하되, **양식 예시의 블록 표기를 통합 골격으로 갱신**한다:
- `reporting-template.md:133` `🎯 결론` + `:140` `🔍 근거` 2블록 → `🎯 결론·근거` 1블록(들여쓰기 불릿)으로 병합.
- 각 §8.x 예시에서 결론 항목 + 하위 근거 불릿 구조로 재배치 (M-2 골격 정합).
- `▶️ 다음 진행 사항입니다.` 블록은 유지하되 "승인(확인)해주시면 ~" 어미로 통일 (M-3).

**5요소 표준 표는 불변 이전** (PLAN 5요소 / EXECUTE 5요소 / CLOSE 5요소 — `reporting-template.md:123-129, 162-168, 206-212`). semi-agentic.md §3 모드 경계·§6 CLOSE 게이트와 교차 참조되도록 도입 문단에 "이 3 게이트 보고만 본 양식을 따른다 (§3 모드 경계 / §6 CLOSE 게이트 참조)"를 명시.

#### M-6. [R3] §9 삭제 + 파일 제거

§9 예시 카드(`reporting-template.md:241-317`)는 문서 스스로 "비규범적 참고용"(`:243`)으로 명시 → 헌법 §2 Simplicity("No abstractions for single-use code" / 비규범 예시 제거)에 따라 폐기. §1~§7은 M-1 인라인으로, §8은 M-5 이전으로 모두 귀속 완료되므로 **파일 전체 삭제**(`git rm` 또는 Write 도구 미사용·OS rm). 변경이력(`:319-325`)도 파일과 함께 소멸.

#### M-7. [R4④] opal-harness-interactive.md — 변경 불요 (명시 확인)

grep `reporting-template` over `opal-harness-interactive.md` = **0건**. "보고 형식" 문자열은 §사용자 에스컬레이션의 `에스컬레이션 보고 형식:`(`opal-harness-interactive.md:151`) 1건뿐이며 이는 Gate Fail 보고 양식으로 reporting-template과 무관. → **interactive.md는 수정 대상 아님.** TASK.md R4 ④가 "보고형식 언급 참조"로 지목했으나 실제 코드에는 reporting-template Read 지시가 없어 갱신할 대상이 없음. AC("4개 문서 어디에도 reporting-template Read 지시가 남아있지 않다")는 interactive.md에서 이미 충족(0건). → 본 결론을 §5 설계 피드백에 기록하여 PM Gate 확인을 요청한다.

#### M-8. [R5] install 동기 지점 전수 — 스크립트 변경 불요 (자동 전파)

전수 조사 결과 (`grep reporting-template scripts/` = 0건):

| 스크립트 | references/ 처리 방식 | reporting-template literal | 조치 |
|---------|---------------------|---------------------------|------|
| `scripts/install-mac.sh` | `:866-872` `rm -rf $opal_home/references` (clean_dirs) → `:1144` `cp -Rf "$ref_src"/. "$ref_dst"/` (통째 복사) | 없음 | **불요** — 소스 삭제가 자동 전파, 구 배포본은 clean으로 purge |
| `scripts/install/windows.ps1` | `:425` `$cleanDirs=@(...'references'...)` → `:520-526` references 복사 | 없음 | **불요** — 동일 메커니즘 |
| `scripts/install/linux.sh` | `:39` `exec bash install-mac.sh` 위임 | 없음 | **불요** |
| `scripts/install/macos.sh` | `:44` `exec bash install-mac.sh` 위임 | 없음 | **불요** |
| `scripts/install.ps1` | tarball 다운로드 → windows.ps1 호출 (참조 처리 없음) | 없음 | **불요** |

결론: install 스크립트는 references/를 **파일 목록 없이 통째 클린+복사**하므로 `reporting-template.md` 소스 삭제만으로 배포 정합이 자동 달성된다. AC("install 스크립트에 reporting-template.md를 복사/strip 대상으로 참조하는 라인이 없다")는 이미 충족(0건). 단, §3 체크리스트에 grep 0건 재확인 Step을 둔다.

> 배포 경계 (`TASK.md:77`): `~/.opal/` 배포본은 직접 수정 금지. 본 PLAN 변경 파일 목록은 프로젝트 소스만 포함하며, 배포 동기화는 후속 install 재실행이 담당한다(본 태스크 범위 외).

#### M-9. [R6] 변경이력 015 행 추가 대상

수정되는 문서에만 변경이력 행 추가 (삭제 파일·미변경 파일 제외). 일시 `2026-06-08`, 태스크 `015`:

| 문서 | 변경이력 위치 | 신규 행 내용(요지) |
|------|-------------|------------------|
| `AGENT.md` | `:329` 표 (다음 버전 v3.1) | §보고 형식 reporting-template 참조 → 헌법 문체 인라인 대체 + Eager Step 6.6 제거 (015) |
| `opal-harness-semi-agentic.md` | `:113` 표 (v1.4) | §10 단계전환 보고 양식 3종 신설 — reporting-template §8 이전 + 🎯 결론·근거 통합 표기 (015) |
| `opal-harness.md` | `:284` 표 (다음 버전) | §2 모듈 테이블 reporting-template 행 제거 — 보고 형식 AGENT.md 인라인화 (015) |
| `opal-pm.md` | `:141` 표 (v1.2) | §8 탐색 경로 reporting-template → AGENT.md §보고 형식 인라인 재지정 (015) |

> interactive.md·install 스크립트는 **변경 없음**이므로 변경이력 행 미추가 (M-7·M-8). TASK.md R6은 5개 문서를 나열했으나 interactive.md는 실제 변경이 없어 행 추가 대상에서 제외 — §5 설계 피드백에 명시.

---

## 3. 실행 체크리스트

> 총 6개 Step | Phase 4개
>
> | Phase | Step | 실행 | 비고 |
> |-------|------|------|------|
> | 1 | 1, 2 | 병렬 | 독립 파일 (semi-agentic.md / AGENT.md) — 이전처·인라인처 선완성 |
> | 2 | 3, 4 | 병렬 | 독립 파일 (opal-harness.md / opal-pm.md) — Phase 1 완료 후(인라인 대상 확정) |
> | 3 | 5 | 순차 | 삭제 — Phase 1·2 완료(모든 콘텐츠 새 위치 보장) 후 |
> | 4 | 6 | 순차 | 잔존 참조 0건 검증 — Step 5 완료 후 |

### Step 1: semi-agentic.md §10 단계전환 양식 이전 + 통합 표기 갱신
- [x] 완료
- **파일**: `opal/core/references/opal-harness-semi-agentic.md`
- **작업 내용**: §9(유지 규칙) 뒤·변경이력 앞에 **§10. 단계 전환 보고 양식 (캡틴 게이트 3종)** 신설. `reporting-template.md:119-239` §8.1/§8.2/§8.3의 5요소 표 3종 + 양식 예시 3종을 이전하되, 예시의 `🎯 결론`+`🔍 근거` 2블록을 `🎯 결론·근거` 1블록(들여쓰기 불릿)으로 병합하고 `▶️` 블록 어미를 "승인(확인)해주시면 ~"로 통일. 도입 문단에 "§3 모드 경계 / §6 CLOSE 게이트 참조" 교차 링크 추가. 변경이력 v1.4(015) 행 추가. (→ M-5, M-9)
- **완료 기준**: semi-agentic.md에 PLAN/EXECUTE/CLOSE 5요소 양식이 §10으로 존재하고, 모든 예시가 🎯 결론·근거 통합 골격(들여쓰기 불릿)을 사용하며, `🔍 근거` 단독 헤딩이 0건이다.
- **테스트**: `grep -c "🔍 근거" opal-harness-semi-agentic.md` = 0 / `grep "🎯 결론·근거" opal-harness-semi-agentic.md` 존재 / §10.1·§10.2·§10.3 헤딩 존재.
- **의존**: 없음

### Step 2: AGENT.md §보고 형식 인라인 + Step 6.6 제거
- [x] 완료
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: (1) §보고 형식 stub(`:209-213`)을 M-1 인라인 본문 전문(~35줄: 골격→원칙→작동하는가)으로 대체. 역할별 표기 표(`:215-221`)·Observability(`:223-225`)는 유지. (2) Eager Step 6.6(`:24`) 삭제 — Step 6.5→7 흐름 보존. 부트스트랩 완료 보고(`:55`) `✅ reporting` 칼럼은 유지(M-4-a 권고). (3) 변경이력 v3.1(015) 행 추가. (→ M-1, M-2, M-3, M-4, M-9)
- **완료 기준**: §보고 형식에 (a)🎯 결론·근거 통합 골격 (b)AskUserQuestion 의사결정 규칙+"(권고)" (c)▶️ 승인 대기 규칙(자동 진행 금지) (d)이모티 헤딩(🎯/▶️) (e)일목요연·자율성 보존이 모두 명문화되고, reporting-template.md Read 지시가 제거되어 있다.
- **테스트**: `grep "reporting-template" AGENT.md` = 변경이력 1행(`:343` v2.4 과거 이력)만 잔존, Step 6.6·§보고 형식 영역엔 0건 / `grep "AskUserQuestion" AGENT.md` 존재 / `grep "결론·근거" AGENT.md` 존재 / `grep "승인(확인)" AGENT.md` 존재.
- **의존**: 없음

### Step 3: opal-harness.md §2 모듈 테이블 행 재지정
- [x] 완료
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §2 하네스 모듈 테이블의 `| 보고 형식 | harness/reporting-template.md | Eager 단계 ... | §보고 형식 |` 행(`:98`)을 **제거**한다 (reporting-template 파일이 삭제되고 보고 형식은 AGENT.md 인라인으로 이동했으므로 모듈 테이블 항목 부적격). 변경이력(`:284`) 다음 버전 행(015) 추가. (→ M-9)
- **완료 기준**: §2 모듈 테이블에 reporting-template 행이 없고, 다른 행은 불변이다.
- **테스트**: `grep "reporting-template" opal-harness.md` = 변경이력 1행(`:284` v4.8 과거 이력)만 잔존, §2 테이블엔 0건.
- **의존**: Step 2 (AGENT.md 인라인이 확정되어야 "AGENT.md 이동" 표현이 유효)

### Step 4: opal-pm.md §8 탐색 경로 재지정
- [x] 완료
- **파일**: `opal/core/references/opal-pm.md`
- **작업 내용**: §8(`:100-108`)의 `> 탐색: harness/reporting-template.md`(`:105`)를 `> 보고 형식 본문: AGENT.md §보고 형식 (Eager 인라인 — 별도 Read 불요)`로 재지정. 핵심 라인(`:108`)의 "결론 → 근거 → 다음 3블록 구조"를 "🎯 결론·근거 통합 + 의사결정=AskUserQuestion + 진행=승인 대기"로 갱신. 변경이력(`:141`) v1.2(015) 행 추가. (→ M-9)
- **완료 기준**: §8에 reporting-template 경로가 없고 AGENT.md §보고 형식 인라인으로 재지정되어 있다.
- **테스트**: `grep "reporting-template" opal-pm.md` = 변경이력 1행(`:144` v1.1 과거 이력)만 잔존, §8엔 0건.
- **의존**: Step 2

### Step 5: reporting-template.md 파일 삭제
- [x] 완료
- **파일**: `opal/core/references/harness/reporting-template.md` (삭제)
- **작업 내용**: §1~§7(인라인 완료) + §8(semi-agentic 이전 완료) + §9(비규범 폐기) 귀속 확인 후 파일 삭제. (→ M-6)
- **완료 기준**: `opal/core/references/harness/reporting-template.md` 파일이 존재하지 않는다.
- **테스트**: `test ! -f opal/core/references/harness/reporting-template.md && echo OK`
- **의존**: Step 1, Step 2 (콘텐츠 새 위치 보장 후 삭제 — 순서 역전 금지)

### Step 6: 잔존 참조 0건 검증 (Read 깨짐·install 정합)
- [x] 완료
- **파일**: (전체 — `opal/`, `scripts/`)
- **작업 내용**: 삭제 후 잔존 활성 참조 전수 검증. `grep -rn "reporting-template" opal/ scripts/` 실행 → 결과가 **변경이력 과거 행 3건(`AGENT.md` v2.4 / `opal-harness.md` v4.8 / `opal-pm.md` v1.1)으로만 한정**되고, 활성 Read 지시·모듈 테이블·탐색 경로·install 복사 라인엔 0건임을 확인. (→ M-7, M-8)
- **완료 기준**: reporting-template를 가리키는 **활성** 참조(Read 지시/탐색 경로/모듈 테이블/install 라인)가 0건이다 (변경이력 보존 행은 허용).
- **테스트**: `grep -rn "reporting-template" opal/ scripts/` 결과가 변경이력 행 3건뿐 / `grep -rn "🔍 근거" opal/core/AGENT.md` = 0 (구 2블록 잔재 없음).
- **의존**: Step 3, 4, 5

---

## 4. QA 체크리스트

### 기능 테스트 (요구사항 대응)
- [x] R1 — AGENT.md §보고 형식에 (a)결론·근거 통합 골격 (b)AskUserQuestion 규칙 (c)승인 대기 규칙 (d)이모티 헤딩(🎯/▶️) (e)자율성 보존이 모두 명문화되고 reporting-template Read 지시 제거 (Step 2)
- [x] R1 — 인라인 본문이 헌법 문체("골격→원칙→작동하는가") 구조이고 ~35줄 압축형 (Step 2)
- [x] R2 — semi-agentic.md §10에 PLAN/EXECUTE/CLOSE 5요소 양식 존재 + 통합 골격(🎯 결론·근거) 정합 (Step 1)
- [x] R3 — reporting-template.md 파일 부재 (Step 5)
- [x] R4 — AGENT.md / opal-harness.md / opal-pm.md 3곳 재지정 완료 + interactive.md 무참조 확인 (Step 2·3·4·6)
- [x] R5 — install 스크립트 reporting-template 참조 0건 (Step 6, M-8)
- [x] R6 — AGENT.md·opal-harness-semi-agentic.md·opal-harness.md·opal-pm.md 4개 문서에 015 변경이력 행 추가 (Step 1·2·3·4)

### 일관성 테스트
- [x] §8 이전 후 양식 예시의 `🔍 근거` 단독 헤딩이 전 문서에서 0건 (통합 골격 정합)
- [x] AGENT.md §보고 형식 ↔ semi-agentic.md §10 게이트 양식이 동일 통합 골격(🎯 결론·근거 + ▶️ 진행) 사용
- [x] AGENT.md Eager Step 번호 흐름(6.5 → 7)이 6.6 제거 후에도 단절 없음
- [x] 부트스트랩 완료 보고(`AGENT.md:55`) `✅ reporting` 칼럼 의미 보존 (M-4-a)
- [x] 변경이력 과거 행(reporting-template 언급 3건)은 불변 보존 — 활성 참조와 구분

### 문서 품질
- [x] 한국어 본문 + 영어 코드/필드명(AskUserQuestion, Eager, references 등) 규칙 준수
- [x] kebab-case 파일 네이밍 준수 (변경 파일 모두 기존 네이밍 유지)
- [x] 이모티 헤딩·`---` 구분선·들여쓰기 불릿 표기 일관
- [x] 헌법 §2 Simplicity·Governance("stays short") 정합 — 인라인 본문이 한 화면 내 압축

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| 삭제 후 Read 깨짐 (활성 참조 잔존) | 세션 부트스트랩 실패 / Lazy Read 오류 | Step 6 grep 0건 검증을 CLOSE 전 필수 게이트로. 삭제(Step 5)는 인라인·이전(Step 1·2) 완료 후에만 |
| 변경이력 과거 행 오삭제 | 이력 추적성 손실 | Step 3·4·6에서 "변경이력 행은 불변 보존, 활성 참조만 0건"으로 명시 분리 |
| §8 이전 시 2블록 표기 잔존 | 신규 통합 골격과 불일치 | Step 1 완료 기준에 `grep "🔍 근거"=0` 강제 |
| R4④/R6 interactive.md 불일치 (TASK는 지목, 실제 무참조) | AC 해석 충돌 | M-7에 명시 + §설계 피드백에서 PM Gate 확인 요청 — interactive.md 무변경이 AC를 이미 충족 |
| 배포본 stale reporting-template 잔존 | 구 ~/.opal 캐시 혼동 | M-8: install이 references/ 통째 clean+copy로 자동 purge (본 태스크 범위 외, 후속 install 재실행) |
| AskUserQuestion 신규 도입 오해 (게이트 우회로) | Guards 약화 우려 | M-3에 "보고 형식 규범 변경이며 CLOSE 게이트 등 Guards 불변"을 [MUST] 인용으로 명문화 |

---

## 설계 피드백 (PM Gate 확인 요청)

미해결·해석 분기 항목을 명시한다. PM Gate에서 확정 후 EXECUTE 진입을 권고한다.

1. **R4④ interactive.md — 변경 대상 없음** (M-7): TASK.md R4가 `opal-harness-interactive.md`를 "보고형식 언급 참조" 4번째 대상으로 지목했으나, grep `reporting-template` = 0건이며 "보고 형식" 문자열은 §사용자 에스컬레이션의 Gate Fail 보고 양식(`:151`) 1건으로 무관하다. → **interactive.md는 무변경**이 AC("4곳 어디에도 reporting-template Read 지시 없음")를 이미 충족. PM 확인 요청: 이 결론 수용 여부.

2. **R6 변경이력 5개 → 4개** (M-9): TASK.md R6은 5개 문서(interactive.md 포함)에 015 행을 요구하나, interactive.md는 실제 변경이 없어 변경이력 행만 추가하는 것은 "변경 없는 이력 추가"가 되어 부적절. → **4개 문서**(AGENT.md / semi-agentic.md / opal-harness.md / opal-pm.md)에만 추가 권고. PM 확인 요청.

3. **R5 install — 스크립트 무변경** (M-8): install이 references/를 파일 목록 없이 통째 clean+copy하므로 소스 삭제만으로 정합 달성. install 스크립트 편집 0건. → AC("install에 reporting-template 참조 라인 없음") 이미 충족. PM 확인 요청: 스크립트 무변경 수용.

4. **M-4-a 부트스트랩 완료 보고 `✅ reporting` 칼럼**: 인라인화 후에도 reporting은 항상 활성이므로 **칼럼 유지** 권고. 제거 시 부트스트랩 산출물 포맷 회귀. PM 확인 요청: 유지 vs 제거.

5. **§10 위치 확정**: §8 양식을 semi-agentic.md **신규 §10**(§9 뒤·변경이력 앞)에 배치 권고. 대안으로 §8 차이표 직후(§8.x 하위 섹션)도 가능하나, 차이표와 양식은 성격이 달라 별도 섹션이 명확. PM 확인 요청.
