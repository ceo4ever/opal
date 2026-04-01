# QA: TODO — Antigravity 플랫폼 지원 추가 및 QA 호출 구조 개선

> 검토일: 2026-03-07 | 판정: ⚠️ Needs Revision → ✅ Pass (지적 사항 반영 완료)

## 1. 요약

TODO.md는 PLAN의 10개 구현 순서를 10개 Step으로 1:1 매핑하여 실행 체크리스트를 잘 구성하였다. Part B QA 체크리스트도 TASK의 모든 요구사항(A-1~A-6, B-0, C-1~C-3)을 빠짐없이 포함하고 있다. 복잡도 판별은 형식 기준으로 "복잡 모드"로 판정하되, 실제 Markdown 작업이므로 Planner 생략을 권장하는 합리적 판단을 내렸다.

다만 2건의 수정 필요 사항이 발견되었다: (1) Step 3에서 PLAN이 명시한 STEP 1~5 범위를 STEP 1~4로 축소한 점, (2) Step 6에서 references 파일 수를 실제 5개가 아닌 6개로 기재한 점. 이 외에 경고 수준의 개선 사항이 2건 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| D-1 | Step 완전성 | ✅ Pass | PLAN의 N-1~N-19, M-1~M-9, D-1~D-3 모든 항목이 Step 1~10에 빠짐없이 매핑됨 |
| D-2 | 완료 기준 명확성 | ✅ Pass | 10개 Step 모두 Grep/diff/ls 등 검증 가능한 기준을 제시. Step 8의 "알투 핵심 요소"가 다소 모호하나 B-1 체크리스트에서 보완 |
| D-3 | 의존성 순서 | ✅ Pass | PLAN의 "소스 원본 → Cursor → Antigravity → 템플릿/문서" 원칙과 Step 간 의존성이 일치 |
| D-4 | QA 체크리스트 커버리지 | ✅ Pass | B-1에서 TASK A-1~A-6, B-0, C-1~C-3 모두 개별 항목으로 확인 가능 |
| D-5 | 회귀 테스트 포함 | ✅ Pass | B-2에서 claude/agents/ 구조, claude/skills/ 5개 스킬, 기존 워크플로우, templates/ 원본 유지 확인 |
| D-6 | 보안 체크 포함 | ✅ Pass | B-4에서 민감 정보 확인 + .gitignore 불필요 명시. Markdown 전용 작업에 적합한 수준 |
| D-7 | 실행 방법 지정 | ✅ Pass | 10개 Step 모두 "실행 방법: direct" 명시 |
| D-8 | 복잡도 판별 정확성 | ✅ Pass | 5개 기준 중 4개가 복잡으로 판정되어 "복잡 모드" 결론은 기준에 부합. Planner 생략 권장은 실질적 난이도를 반영한 합리적 판단 |
| D-9 | Part C 완전성 (복잡 모드) | ✅ Pass (해당 없음) | Planner/Part C 생략 권장을 채택한 경우 해당 없음. 모든 Step이 direct 실행이고 외부 의존성이 없으므로 생략 근거가 타당 |

## 3. 지적 사항

### 3.1 [수정 필요] Step 3: STEP 범위 누락 (STEP 5 미포함)

**현재**: Step 3 완료 기준이 "STEP 1~4 각각에 '### ⚠️ QA 에이전트 호출' 서브섹션 존재"로 기재. 테스트도 "4회 이상 확인".

**문제**: PLAN 3.1절 M-1은 **"각 STEP(1~5)의 마지막 한 줄 QA 호출 지시를 별도 서브섹션 블록으로 교체"**라고 명시하여 STEP 5(EXECUTE)를 포함한다. TASK C-3도 **"SKILL.md 각 STEP의 QA 호출 지시를 별도 서브섹션으로 강조"**라고 되어 있어 모든 STEP을 대상으로 한다.

**참고**: STEP 5의 QA 호출은 STEP 1~4와 다른 형태(단순/복잡 모드 실행 흐름 내 번호 리스트에 내장)이므로, 동일한 서브섹션 패턴을 적용하기 어려울 수 있다. 그러나 PLAN이 명시한 범위와 다르게 축소한 것은 근거 없이 이루어졌다.

**권장 조치**: 다음 중 하나를 선택:
- (A) Step 3에 STEP 5 처리를 추가하고 완료 기준을 "STEP 1~5"로, 테스트를 "5회 이상"으로 수정
- (B) STEP 5의 QA 호출이 이미 충분히 강조되어 있어 제외한다는 근거를 명시

### 3.2 [수정 필요] Step 6: references 파일 수 오류

**현재**: Step 6 완료 기준에 "references/ 6개 파일 존재"로 기재.

**문제**: 실제 `claude/skills/task-flow/references/` 디렉토리에는 5개 파일만 존재한다:
1. `research-guide.md`
2. `plan-guide.md`
3. `todo-guide.md`
4. `execute-guide.md`
5. `execute-plan-guide.md`

PLAN에서도 N-2~N-6으로 5개를 나열한다. "6개"는 사실과 다르다.

**권장 조치**: "6개 파일"을 "5개 파일"로 수정.

### 3.3 [경고] Step 5: 테스트에서 하위 파일 검증 부족

**현재**: Step 5 테스트가 "diff로 claude/skills/{name}/SKILL.md와 antigravity/skills/{name}/SKILL.md 비교"로 SKILL.md만 비교.

**문제**: 일부 스킬(doc-writer 등)에 `references/` 하위 디렉토리가 있을 수 있다. 작업 내용에는 "전체 디렉토리(SKILL.md + 하위 파일)를 복사"라고 되어 있으나, 테스트는 SKILL.md만 확인한다. PLAN T-5도 "3-플랫폼 동일한지 diff 비교"를 요구한다.

**권장 조치**: 테스트를 `diff -r`(재귀 비교)로 변경하거나, SKILL.md와 하위 파일 모두 비교하도록 보완.

### 3.4 [경고] PLAN T-2 탐색 경로 일관성 검증 미반영

**현재**: PLAN T-2는 "SKILL.md에 명시된 모든 탐색 경로에 대응하는 파일이 존재하는지 확인"을 요구한다. 이 검증은 개별 Step의 테스트에 부분적으로 분산되어 있으나, 최종적으로 **모든 탐색 경로의 파일 실존을 일괄 확인**하는 통합 테스트가 없다.

**권장 조치**: Step 10 또는 Part B에 "탐색 경로에 명시된 모든 파일 경로가 실제 파일과 대응하는지 확인" 항목 추가를 고려.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK A-1~A-6 | Part B B-1에서 6개 항목 모두 개별 확인 가능 | ✅ Pass |
| TASK B-0 | Part B B-1에서 Cursor 플랫 파일 확인 항목 존재 | ✅ Pass |
| TASK C-1~C-3 | Part B B-1에서 3개 항목 모두 개별 확인 가능 | ✅ Pass |
| TASK 제약 조건 (하위 호환) | B-2 회귀 테스트 5개 항목으로 커버 | ✅ Pass |
| TASK 제약 조건 (소스 원본 유지) | B-2 항목 1~3에서 claude/ 구조/내용 유지 확인 | ✅ Pass |
| PLAN N-1~N-6 (task-flow+refs) | Step 6에 매핑. 단, references 파일 수 6→5 오류 | ⚠️ Warning |
| PLAN N-7~N-11 (단순 복사) | Step 5에 매핑 | ✅ Pass |
| PLAN N-12~N-14 (에이전트→스킬) | Step 7에 매핑 | ✅ Pass |
| PLAN N-15~N-17 (Cursor 플랫 파일) | Step 4에 매핑 | ✅ Pass |
| PLAN N-18~N-19 (템플릿) | Step 8에 매핑 | ✅ Pass |
| PLAN M-1 (SKILL.md QA+경로) | Step 3에 매핑. 단, STEP 범위 1~5→1~4 축소 | ⚠️ Warning |
| PLAN M-2~M-5 (가이드 QA 추가) | Step 1에 매핑 | ✅ Pass |
| PLAN M-6 (AGENT.md 수정) | Step 2에 매핑 | ✅ Pass |
| PLAN M-7~M-8 (문서 업데이트) | Step 10에 매핑 | ✅ Pass |
| PLAN M-9 (cursor/skills/ 동기화) | Step 9에 매핑 | ✅ Pass |
| PLAN D-1~D-3 (Cursor 디렉토리 삭제) | Step 4에 매핑 | ✅ Pass |
| PLAN T-1 (YAML frontmatter) | Step 7 테스트 + B-3 항목 1 | ✅ Pass |
| PLAN T-2 (탐색 경로 일관성) | 개별 Step에 분산. 통합 검증 미비 | ⚠️ Warning |
| PLAN T-3 (가이드 QA 섹션) | Step 1 테스트 + B-1 C-1 | ✅ Pass |
| PLAN T-4 (Cursor 플랫 파일) | Step 4 테스트 + B-1 B-0 | ✅ Pass |
| PLAN T-5 (3-플랫폼 동기화) | Step 5 + Step 9 (전이적 비교) | ✅ Pass |
| PLAN T-6 (문서 상호 참조) | Step 10 테스트 | ✅ Pass |
| PLAN T-7 (GEMINI.md 유효성) | Step 8 테스트 + B-1 A-3 | ✅ Pass |
| PLAN T-8 (알투 페르소나 동일성) | Step 8 테스트 + B-1 A-4 | ✅ Pass |
| PLAN T-9 (Claude Code 하위 호환) | B-2 항목 1 | ✅ Pass |

## 5. 판정

**⚠️ Needs Revision → ✅ Pass (지적 사항 반영 완료)**

수정 필요 2건 + 경고 2건 중 4건 모두 반영 완료:

1. ~~Step 3 STEP 범위~~ → STEP 1~5로 확장, STEP 5는 실행 흐름 내 강조 블록으로 적용. 테스트 기준도 5회 이상으로 수정.
2. ~~Step 6 파일 수 오류~~ → "6개 파일"을 "5개 파일"로 수정.
3. ~~Step 5 테스트 범위~~ → `diff -r`로 디렉토리 전체 재귀 비교로 변경.
4. 3.4절 탐색 경로 통합 검증은 Step 간 분산 검증으로 커버되며, 실제 실행 시 최종 점검에서 확인 가능하므로 현재 수준으로 Pass.
