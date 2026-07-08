# TASK: 보고 형식 Eager 슬림화 + 헌법 문체 재작성

> 작성일: 2026-06-08 | 작업 유형: 개선 | 적용 스킬: opp | 모드: agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

세션 시작 시 Eager 로드되는 `reporting-template.md`(318줄/9KB)를 헌법 문체로 압축해 `AGENT.md §보고 형식`에 인라인하고, 단계전환 양식은 게이트 시점 문서로 이전, 예시 카드는 삭제하여 파일을 제거한다. 동시에 보고 형식 자체를 "결론·근거 통합 + 의사결정은 AskUserQuestion 도구 + 진행은 승인 대기"로 재설계한다.

## 배경

128 다이어트(AGENT.md v2.0)는 본문을 분리했을 뿐 Eager 로드 총량을 줄이지 못했고, 012(PRINCIPLES)·143(reporting-template) Eager 승격으로 오히려 증가했다. 측정 결과 Eager는 8개 파일·1,230줄·약 59KB이며, 그중 `reporting-template.md`가 318줄/9KB로 단일 최대 비중이다. 반면 이 문서의 65%(§8 128줄 + §9 78줄)는 매 응답에 필요하지 않다.

## 배경 분석 (대화에서 도출)

**1) 배포 검증 결과 (이번 세션 선행 작업)** — 014 변경 파일 41개는 정상 배포됨. 모든 diff는 install-mac.sh의 변경이력 strip 정책에 의한 것이며 본문은 완전 일치. → 배포는 별도 조치 불요.

**2) Eager 로드 실측** (`~/.opal/` 배포본 기준):

| 파일 | 줄수 | 바이트 |
|------|------|--------|
| AGENT.md(글로벌) | 324 | 19,428 |
| reporting-template.md | 318 | 8,993 |
| opal-harness.md | 251 | 12,739 |
| opal-pm.md | 138 | 6,704 |
| AGENT.md(프로젝트) | 73 | 4,903 |
| PRINCIPLES.md | 57 | 2,496 |
| MEMORY.md | 43 | 4,460 |
| identity.md | 26 | 453 |
| **합계** | **1,230** | **약 59KB** |

**3) reporting-template.md 섹션 분해**:

| 섹션 | 줄수 | 성격 | 처리 방침 |
|------|------|------|----------|
| §1~§7 핵심 규범 | ~104 | 매 응답 적용 (3블록·이모티·일목요연·자율성·적용범위·비보고) | 압축해 AGENT.md 인라인 |
| §8 단계전환 양식 | 128 | semi-agentic 캡틴 게이트 3종(PLAN/EXECUTE/CLOSE) 전용 | `opal-harness-semi-agentic.md`로 이전 |
| §9 예시 카드 | 78 | 문서 스스로 "비규범적 참고용" 명시 | 삭제 |

**4) 참조처 (grep 확인)** — `reporting-template`를 참조하는 곳: `AGENT.md`(Eager Step 6.6), `opal-pm.md`(§8), `opal-harness.md`(§2 모듈 테이블 + §보고 형식 stub). "3블록/보고 형식" 언급: 추가로 `opal-harness-interactive.md`. 파일 삭제 시 이 4곳을 함께 갱신해야 Read 깨짐을 방지.

## 확정된 설계 방향 (대화에서 합의)

**[방향 1] 결론·근거 통합 (1블록)** — 기존 `🎯 결론` + `🔍 근거` 2블록을 `🎯 결론·근거` 1블록으로 통합. 레이아웃은 **항상 들여쓰기 불릿**(캡틴 선택): 결론 항목 줄 + 하위 불릿으로 근거.

```
🎯 결론·근거

1) <결론 항목>
   - <근거/증거>
   - <근거/증거>

2) <결론 항목>
   - <근거/증거>
```

**[방향 2] 의사결정 → AskUserQuestion 도구** — 텍스트 `❓ 의사 결정해 주세요?` 블록을 폐지하고, 선택형 의사결정은 `AskUserQuestion` 도구 호출로 대체. 헌법 "Enforce with a tool, not prose"의 구현. 첫 옵션에 "(권고)" 표기. (열린 서술형 질의는 도구 "Other"로 커버하거나 텍스트 허용 — "선택형 의사결정"에 한해 도구 사용.)

**[방향 3] 단순 진행 → 승인 대기** — `▶️ 다음 진행 사항입니다.` 헤딩 유지하되 자동 진행 금지. "~ 승인(확인)해주시면 계속 진행하겠습니다" 형태로 캡틴 통제권을 넘긴다.

**[방향 4] 헌법 문체 재작성** — §1~§7을 PRINCIPLES.md와 같은 Karpathy식 압축 문체("골격 + 원칙 + 작동하는가")로 ~35줄로 재작성하여 AGENT.md `§보고 형식`에 인라인.

**[방향 5] 위치** — AGENT.md 인라인(신규 파일 0개). reporting-template.md 파일 자체는 삭제.

## 요구사항

- [ ] **R1. AGENT.md §보고 형식 인라인** — 무엇을: 헌법 문체 보고 형식(~35줄) 직접 삽입 / 어디에: `opal/core/AGENT.md` §보고 형식(207~225줄 영역) / 왜: 확정 방향 1·4·5 / AC: §보고 형식 섹션에 (a)결론·근거 통합 골격, (b)의사결정=AskUserQuestion 규칙, (c)진행=승인 대기 규칙, (d)이모티 헤딩(🎯/▶️)이 모두 명문화되어 있고, reporting-template.md를 Read하라는 지시가 제거되어 있다.
- [ ] **R2. §8 단계전환 양식 이전** — 무엇을: reporting-template §8(단계전환 5요소 양식 3종)을 이전 / 어디에: `opal/core/references/opal-harness-semi-agentic.md` / 왜: 게이트 시점에만 필요(확정 방향 5) / AC: semi-agentic.md에 PLAN/EXECUTE/CLOSE 5요소 양식이 존재하고, 통합 골격(🎯 결론·근거)과 정합한다.
- [ ] **R3. §9 삭제 + 파일 제거** — 무엇을: §9 예시 카드 삭제 후 reporting-template.md 파일 삭제 / 어디에: `opal/core/references/harness/reporting-template.md` / 왜: 헌법 §2 비규범적 예시 제거(확정 방향 5) / AC: 파일이 존재하지 않는다.
- [ ] **R4. 참조 4곳 갱신** — 무엇을: reporting-template 참조 제거/대체 / 어디에: ①`AGENT.md` Eager Step 6.6 ②`opal-harness.md` §2 모듈 테이블 + §보고 형식 stub ③`opal-pm.md` §8 ④`opal-harness-interactive.md` 보고형식 언급 / 왜: 파일 삭제 시 Read 깨짐 방지(배경 분석 4) / AC: 4개 문서 어디에도 `reporting-template` 경로 Read 지시가 남아있지 않으며, 각 참조가 "AGENT.md 인라인" 또는 "semi-agentic.md §단계전환"로 재지정되어 있다.
- [ ] **R5. install 배포 정합** — 무엇을: install 스크립트의 reporting-template.md 배포 항목 제거 / 어디에: `scripts/install-mac.sh`(+ `scripts/install/*.sh`, `install.ps1` 동기 지점) / 왜: 삭제 파일을 배포 목록에 남기면 install 오류 / AC: install 스크립트에 reporting-template.md를 복사/strip 대상으로 참조하는 라인이 없다 (PLAN에서 동기 지점 전수 조사).
- [ ] **R6. 변경이력 갱신** — 무엇을: 수정 문서에 변경이력 행 추가 / 어디에: 변경된 각 참조 문서 / 왜: 프로젝트 금지사항(변경이력 누락 금지) / AC: AGENT.md·opal-harness.md·opal-pm.md·opal-harness-interactive.md·opal-harness-semi-agentic.md 변경이력 표에 015 행(일시 KST + 태스크 번호)이 추가되어 있다.

## 제약 조건

- **배포 경계**: `~/.opal/` 배포본 직접 수정 금지. 프로젝트 소스(`opal/`, `scripts/`)만 수정 후 install로 재배포.
- **하네스 우회 금지**: AskUserQuestion 도구 도입은 보고 형식 규범 변경이지 게이트 우회가 아니다 — CLOSE 진입 게이트 등 기존 Guards는 불변.
- **동작검증 영역 불변**: 본 작업은 문서 보고 형식 변경이며, state-tool·게이트 코드 로직은 건드리지 않는다.
- **결론·근거 통합 후에도 §3 일목요연(항목 3개 이내)·§4 시각구분 원칙은 유지**.

## 기술 스택

- Markdown 문서 (프레임워크 참조 문서), Bash (install 스크립트)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | PRINCIPLES.md | `opal/core/references/PRINCIPLES.md` 또는 `~/.opal/PRINCIPLES.md` | 헌법 문체 기준 (§2 Simplicity, Enforce-with-tool, Governance) |
| D-2 | 설계 | reporting-template.md | `opal/core/references/harness/reporting-template.md` | 이전/삭제 대상 원본 (§1~§9) |
| D-3 | 설계 | AGENT.md | `opal/core/AGENT.md` | 인라인 대상 (§보고 형식, Eager Step 6.6) |
| D-4 | 설계 | opal-harness-semi-agentic.md | `opal/core/references/opal-harness-semi-agentic.md` | §8 이전 대상 (게이트 흐름 SSOT) |
| D-5 | 설계 | opal-harness.md / opal-pm.md / opal-harness-interactive.md | `opal/core/references/` | 참조 갱신 대상 4곳 |
| D-6 | 설계 | install-mac.sh | `scripts/install-mac.sh` | 배포 정합 (R5) |
