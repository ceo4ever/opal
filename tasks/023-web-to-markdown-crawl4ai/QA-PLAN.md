# QA: PLAN -- web-to-markdown 스킬 Phase 2 백엔드를 Crawl4AI로 교체

> 검토일: 2026-03-20 | 판정: **Pass**

## 1. 요약

Phase 2 브라우저 폴백을 Playwright(MCP + 스크립트 2분기)에서 Crawl4AI Python 스크립트 단일 경로로 교체하는 계획이다. 변경 대상은 SKILL.md 1개 + 워커 에이전트 3개(Claude/Cursor/Antigravity) 총 4개 파일이며, Phase 1(WebFetch)과 스킬 인터페이스(full/clean 모드, 저장 경로, 산출물 형식)는 그대로 유지한다. Crawl4AI의 `raw_markdown`/`fit_markdown`을 full/clean 모드에 매핑하고, Playwright MCP 분기를 제거하여 아키텍처를 단순화한다. 실행 체크리스트 4단계, QA 체크리스트 13항목이 정의되어 있다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| SP-1 | 코드 분석 충분성 | ✅ | 4개 파일 모두 현재 구현을 구체적으로 기술. Phase 2 분기 로직, 의존성, 산출물 메타데이터, 영향 범위(상위/하위)까지 분석됨 |
| SP-2 | 구현 계획 구체성 | ✅ | 파일별 변경 내용이 명확하고, Crawl4AI 스크립트 코드, 의존성 테이블 변경안, 메타데이터 변경 전후가 모두 명시됨 |
| SP-3 | 체크리스트 완전성 | ✅ | TASK.md 5개 요구사항이 Step 1~4에 빠짐없이 분해됨. Step 1(SKILL.md)에 세부 수정 포인트 7개가 나열되어 구체적 |
| SP-4 | QA 항목 커버리지 | ✅ | 기능 6항목 + 회귀 5항목 + 코드 품질 3항목으로 요구사항 전체를 커버. 특히 "Playwright 잔여 참조 없는가" 항목이 좋음 |
| SP-5 | Short Task 적정성 | ✅ | 문서 4개 파일의 Phase 2 섹션 교체로, 로직 변경 없이 기술 내용만 바꾸는 작업. Short Task에 적합 |

## 3. 지적 사항

### 3-1. Antigravity 워커의 Phase 1 method 명칭 불일치

- **심각도**: Info
- **내용**: 현재 Antigravity 워커(`agents/antigravity/wtm-worker/SKILL.md`)는 Phase 1 방식을 `fetch`로 표기하고 있다(산출물 형식의 "추출 방식": `fetch | Playwright MCP | Playwright Script`, 반환 형식의 method: `fetch | ...`). PLAN은 모든 워커의 method를 `WebFetch | Crawl4AI`로 통일하겠다고 하는데, Antigravity에서는 `fetch`가 플랫폼 고유 명칭이므로 `fetch | Crawl4AI`로 유지하는 것이 맞을 수 있다. 실행 시 의도적 통일인지 확인 필요.

### 3-2. SKILL.md "콘텐츠 추출 및 MD 정제" 섹션 처리 미언급

- **심각도**: Info
- **내용**: Crawl4AI는 마크다운 변환을 자체적으로 수행하므로, SKILL.md의 "MD 변환 규칙" 테이블(HTML -> Markdown 매핑)과 "공통 제거 대상"/"clean 모드 추가 제거 대상" 규칙은 Phase 2에서는 Crawl4AI가 대체한다. PLAN에서는 이 섹션의 처리 방침(그대로 유지 = Phase 1 전용, 또는 Phase 2 적용 제외 명시)이 언급되지 않았다. Phase 1에서는 여전히 에이전트가 MD 정제를 하므로 섹션 자체를 유지하는 것이 맞지만, "Phase 2에서는 Crawl4AI가 변환을 담당하므로 이 규칙은 Phase 1에만 적용된다" 등의 문구 추가를 고려할 만하다.

### 3-3. SKILL.md "결과 보고" 테이블의 방식 값

- **심각도**: Info
- **내용**: SKILL.md 282행 부근의 결과 보고 예시 테이블에서 `| 2 | {url} | Playwright | ...`로 표기되어 있다. PLAN의 변경 범위에 이 테이블의 값 업데이트(`Playwright` -> `Crawl4AI`)가 명시적으로 포함되어 있지 않다. Step 1의 "Phase 2 섹션" 교체 범위에 포함될 수 있으나 명시하면 누락 방지에 도움이 된다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | "Phase 2 백엔드를 Crawl4AI Python 스크립트로 교체" | ✅ PLAN Section 2에 스크립트 코드까지 명시 |
| TASK.md | "Crawl4AI의 result.markdown 활용하여 마크다운 변환" | ✅ raw_markdown/fit_markdown 매핑 명시 |
| TASK.md | "기존 스킬 인터페이스(full/clean 모드, 저장 경로 규칙) 유지" | ✅ 영향 범위 분석에서 인터페이스 유지 확인, 회귀 테스트 항목에 포함 |
| TASK.md | "Crawl4AI 미설치 시 설치 안내 메시지 업데이트" | ✅ pip install 안내 메시지 구체적으로 명시 |
| TASK.md | "Phase 1(WebFetch) 로직은 그대로 유지" | ✅ 회귀 테스트 첫 번째 항목으로 명시 |
| TASK.md | "wtm-worker 에이전트의 Phase 2 부분도 동일하게 업데이트" | ✅ Step 2~4에서 3개 워커 모두 포함 |
| TASK.md 제약조건 | "Python 3.x 필요, Node.js 의존성 제거" | ✅ Crawl4AI Python 스크립트 사용, Playwright npm 의존 제거 |

## 5. 판정

**Pass**

모든 검증 항목이 통과했다. 지적 사항 3건은 모두 Info 수준으로, 실행 단계에서 참고하면 충분하다. TASK.md의 5개 요구사항과 4개 제약조건이 빠짐없이 PLAN에 반영되어 있으며, 즉시 구현에 착수할 수 있는 구체성을 갖추고 있다.
