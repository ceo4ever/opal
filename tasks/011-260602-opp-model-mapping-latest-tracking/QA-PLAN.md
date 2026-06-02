# QA: PLAN — OPAL 모델 매핑 최신화 + 최신 추종 전략 도입

> 검토일: 2026-06-02 | 판정: Needs Revision

---

## 1. 요약

PLAN.md는 OPAL의 모델 매핑 SSOT(`opal-model-mapping.md`)와 어댑터 4곳(install-mac.sh, windows.ps1, agents.md, codex TOML)을 동기화하는 계획이다. Gemini는 `-latest` 부동 별칭으로 전환, Codex는 gpt-5.4-mini/gpt-5.5/gpt-5.3-codex로 갱신, OpenAI 컬럼은 `install-mac.sh` 코드 근거로 미배선 판정 후 "참조 전용" 명시로 처리한다. TASK에서 3곳으로 인식했던 동기화 지점을 windows.ps1(L-4)을 포함한 4곳으로 확대 식별하는 것이 PLAN의 핵심 기여다. 전체 구조와 제약 준수는 우수하나 Gemini `-latest` 별칭 형식의 공식 실재 여부에 Critical 수준의 근거 불일치가 발견되었다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | Step 1~5 순차/병렬 구조 명확, agent·완료기준·테스트·의존성 전 Step에 기재 |
| GP-2 | 의존성 순서 | Pass | SSOT(Step 1) → 어댑터(Step 2~4 병렬) → 교차검증(Step 5) 순서 합리적 |
| GP-3 | TASK 반영 | Pass | R-1~R-6 전항이 §3 요구사항 충족 매핑 표로 커버됨, windows.ps1(L-4) 추가 발견도 반영 |
| GP-4 | 파일 목록 완전성 | Pass | 4개 수정 파일 식별(opal-model-mapping.md / install-mac.sh / agents.md / windows.ps1), 신규 생성·삭제 없음 확인 |
| GP-5 | 설계 구체성 | Warning | 파일별 변경 위치(줄번호) + 목표값이 상세하나, Gemini `-latest` 별칭 3개 중 `gemini-pro-latest`의 공식 실재 여부가 WebFetch 대조 결과 미확인 상태 (하단 상세 참조) |
| GP-6 | 체크리스트 커버리지 | Pass | R-1~R-6 모두 Step으로 분해됨 (R-5는 Step 5, R-6은 각 Step 내 변경이력 행 추가) |
| QA-C1 | 모델 ID 근거성 (Codex) | Pass | gpt-5.4-mini / gpt-5.5 / gpt-5.3-codex 모두 D-7([Codex Models](https://developers.openai.com/codex/models)) WebFetch 대조에서 실재 확인 |
| QA-C2 | 모델 ID 근거성 (Gemini `-latest` 형식) | Fail | `gemini-flash-lite-latest` / `gemini-flash-latest`는 D-5 문서에서 패턴 언급 확인. 그러나 `gemini-pro-latest`는 공식 docs에서 명시적으로 열거되지 않음. 현재 pro 라인 stable ID는 `gemini-2.5-pro`이며 preview는 `gemini-3.1-pro-preview`이나 `-latest` 별칭으로의 공식 URL이 미확인 |
| QA-C3 | R-2 OpenAI 처리 명확성 | Pass | install-mac.sh:557(model_value = mapping.get), :608-660(호출처 4곳 모두 "claude"/"cursor"/"gemini"/codex 전용) 코드 근거로 `openai` 키 부재 확정. "참조전용 각주 + 모호한 죽은 컬럼 제거" AC 충족 설계 |
| QA-C4 | R-5 동기화 범위 | Pass | TASK 배경분석 3곳 → 4곳(L-4 windows.ps1:1302-1317,1335) 확대 반영. Step 4 + Step 5 검증 양쪽에 windows.ps1 포함 |
| QA-C5 | 제약 위반 없음 | Pass | `~/.opal/` 직접 수정 계획 없음 / `openai` 키 신규 추가 금지 명시(Step 2) / 레벨 정의 불변(§1 표 구조 유지) / R-6 변경이력 계획(D-1 v1.3 / D-3 v1.5 / install-mac.sh 헤더) 존재 |
| QA-C6 | citation-rules §0 근거 제시 | Pass | M-1~M-5 결정 각각에 D-N 인라인 단축 참조 기재. [MUST] 인용 5건 모두 원문 포함 |
| QA-C7 | OpenAI 컬럼 값 혼선 | Warning | §2 M-2 본문 "advanced=`gpt-5.3`"(접미 없음)과 §3 최종 확정 테이블 "advanced=`gpt-5.3`(OpenAI)/`gpt-5.3-codex`(Codex)"가 다름. §2 핵심 설계(파일1) "advanced: `gpt-5.3`"도 OpenAI 컬럼 값으로 기재되어 Codex의 `gpt-5.3-codex`와 혼동 가능 |

---

## 3. 지적 사항

### 심각도 분류

---

#### [Fail — Critical] QA-C2: `gemini-pro-latest` 공식 실재 미확인

**문제**: PLAN §2 M-1은 Gemini advanced 값으로 `gemini-pro-latest`를 채택하고 D-5([Gemini API Models](https://ai.google.dev/gemini-api/docs/models)) 근거로 주장한다. 그러나 QA WebFetch 대조 결과:
- D-5 페이지가 명시적으로 열거하는 `-latest` 별칭 예시는 `gemini-flash-latest` 단 1건이다.
- `gemini-pro-latest`는 D-5에서 명시적으로 확인되지 않는다. Pro 라인의 current stable ID는 `gemini-2.5-pro`이며, 최신 preview는 `gemini-3.1-pro-preview`이다.
- D-5 문서는 "Points to the latest release for a specific model variation"이라고 설명하고 Flash 예시만 제공하므로, `gemini-pro-latest`가 실제 API에서 수용되는 별칭인지 공식 문서로 확증되지 않는다.

**왜 Critical인가**: citation-rules §0 [MUST] "상상·추정·기억 기반 기재 금지 — 모든 분석·설계 결정은 문서 근거를 인용해야 한다." PLAN이 근거로 인용한 D-5에서 해당 별칭이 명시적으로 확인되지 않는 상태로 EXECUTE 진입하면, `gemini-pro-latest`를 실제 API 호출에 사용하는 어댑터 코드가 invalid model ID를 포함하게 된다.

**권장 수정**:
- 옵션 A: D-5 문서를 직접 재검증하여 `gemini-pro-latest`가 실재함을 확인하는 공식 인용 링크(또는 API 응답)를 PLAN에 추가한다.
- 옵션 B: 실재가 확인되지 않을 경우, advanced는 현재 stable GA인 `gemini-2.5-pro`로 핀하거나, PLAN에 "(API 실재 여부 EXECUTE에서 재검증 후 확정)" 조건부 표기를 추가한다.
- 옵션 C: `gemini-2.5-flash-latest`, `gemini-3.5-flash-latest` 등 버전 포함 `-latest` 형식 중 공식 문서에서 명시적으로 확인된 형식으로 전환한다.

---

#### [Warning] QA-C7: OpenAI 컬럼 advanced 값 표기 불일치

**문제**: PLAN 내 OpenAI 컬럼 advanced 값이 위치에 따라 다르게 기재된다.
- §2 M-2 본문: "light=`gpt-5.4-mini`, standard=`gpt-5.5`, advanced=`gpt-5.3`"
- §3 최종 확정 테이블: OpenAI(참조전용) advanced = `gpt-5.3`
- §2 핵심 설계(파일1) 명세: "advanced: `gpt-5.3`"(OpenAI), "advanced: `gpt-5.3-codex`"(Codex) — 두 값이 시각적으로 인접하여 혼동 가능

`gpt-5.3`과 `gpt-5.3-codex`는 다른 모델이다. D-7([Codex Models](https://developers.openai.com/codex/models))에서 확인된 정확한 OpenAI/Codex 구분은:
- Codex advanced = `gpt-5.3-codex` (코딩 특화)
- 일반 OpenAI advanced = `gpt-5.3`(비공식, D-6에서 별도 확인 필요)

OpenAI 컬럼은 참조 전용이므로 install에 영향은 없다. 그러나 참조 정보로서의 정확성을 위해 `gpt-5.3`이 D-6에서 실재 확인된 ID인지 명시가 필요하다. PLAN 내부 표기 통일도 권장된다.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 (Gemini 최신화 AC) | PLAN이 공식 docs 실재 GA 모델 ID를 기재하는가 → `gemini-pro-latest` 미확인으로 부분 미충족 | Warning |
| TASK.md R-2 (OpenAI 처리 AC) | 코드 근거로 미배선 판정 후 "모호한 죽은 컬럼 없음" → M-2 설계 충족 | Pass |
| TASK.md R-3 (Codex AC) | D-7 대조 gpt-5.4-mini/gpt-5.5/gpt-5.3-codex 실재 확인, dict+TOML+기본값 3위치 반영 | Pass |
| TASK.md R-4 (부동 별칭 AC) | 플랫폼별 별칭 지원 여부를 공식 docs 근거로 판정(M-3). Gemini `-latest` 실재 이슈는 R-1과 공유 | Warning |
| TASK.md R-5 (3곳 동기 AC) | PLAN이 4곳으로 확대(L-4 추가) + Step 5 교차검증 설계 | Pass (상위 기여) |
| TASK.md R-6 (변경이력 AC) | D-1 v1.3 / D-3 v1.5 / install-mac.sh 헤더 계획 존재. windows.ps1은 형식 확인 후 조건부 | Pass |
| TASK.md 제약 (배포 경계) | `~/.opal/` 직접 수정 없음, 소스 한정 변경 | Pass |
| TASK.md 제약 (레벨 불변) | light/standard/advanced 3레벨 구조 유지 계획 | Pass |
| PLAN §2 M-1 vs §3 최종 테이블 | 값 일치 여부 — Gemini/Codex/Claude 일치. OpenAI advanced `gpt-5.3` 일치(표기 혼동 있으나 값 자체는 일관) | Pass (Warning 동반) |

---

## 5. 판정

**Needs Revision**

`gemini-pro-latest`가 Gemini 공식 docs(D-5)에서 명시적으로 확인되지 않은 채로 EXECUTE에 진입하면, citation-rules §0 [MUST](상상 기반 기재 금지)를 위반하는 상태로 코드가 작성된다. Critical 1건에 따라 Needs Revision 판정을 내린다. Codex 모델 ID(gpt-5.4-mini/gpt-5.5/gpt-5.3-codex)는 D-7 WebFetch에서 실재 확인됐으므로 R-3은 이상 없다. `gemini-pro-latest` 실재 확증 또는 대안 ID 선택 후 PLAN §2 M-1을 보강하면 EXECUTE 진입 가능하다.
