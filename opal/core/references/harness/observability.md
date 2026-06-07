# Observability (관측)

> 출처: opal-harness.md §5
> 로드 시점: 워커 디스패치 직전 (매 디스패치마다)
> 역할: 스킬 탐색 경로 + 프로젝트 메모리 동기화 + 타임스탬프 취득 + 행위 주체 표시

---

### 스킬 탐색 경로

dev 단계 스킬:
1. `{프로젝트}/.opal/skills/op-dev-{stage}/SKILL.md`
2. `~/.opal/skills/op-dev-{stage}/SKILL.md`

범용 단계 스킬:
1. `{프로젝트}/.opal/skills/op-task{-suffix}/SKILL.md`
2. `~/.opal/skills/op-task{-suffix}/SKILL.md`

에이전트:
1. `{프로젝트}/.opal/agents/{agent-name}/AGENT.md`
2. `~/.opal/agents/{agent-name}/AGENT.md`

### 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.md`가 존재하면, 단계 완료 시 작업 히스토리를 갱신한다:
- 단계 완료: `단계` 컬럼 -> `{단계} -> {다음} 대기`
- DONE.md 생성: `단계` 컬럼 -> `완료`

**FIFO 규칙**: 항목 추가 후 작업 히스토리가 10개를 초과하면 가장 오래된 행(테이블 맨 아래)을 즉시 삭제한다. 추가와 삭제를 같은 시점에 수행한다.

#### 타임스탬프 취득 규칙 (필수)

시작일시/완료일시 기록 시 반드시 bash 명령을 실행하여 KST 현재 시각을 취득한다:
- 일시 (`YYYY-MM-DD HH:mm`): `node ~/.opal/tools/date/date.js datetime`
- 일자 (`YYYY-MM-DD`): `node ~/.opal/tools/date/date.js date`
- 폴더명용 (`YYMMDD`): `node ~/.opal/tools/date/date.js yymmdd`

**bash 생략 금지**: 컨텍스트에 날짜가 있어도 bash 실행은 필수다. 시간(HH:mm)까지 정확히 기록해야 한다.

### 행위 주체 표시

PM은 툴 호출 직전/직후 한 줄 선언으로 행위 주체를 명시한다.

#### 아이콘 룩업

Agent 도구로 에이전트를 디스패치할 때, 해당 에이전트 AGENT.md의 frontmatter `icon` 필드를 읽어 사용한다.
`icon` 필드가 없으면 디폴트 아이콘 `✨`을 사용한다.

| 선언 형식 | 사용 시점 |
|----------|---------|
| `📋 {name}[PM] 직접:` | PM이 직접 툴을 호출하기 직전 (Edit, Write, Read 등) |
| `{icon} 디스패치: {단계명} — {설명}` | Agent 도구로 에이전트를 디스패치하기 직전 (워커 · QA · 테스트 · 액션 등 모든 에이전트) |
| `{icon} 완료: {단계명} — {결과 요약}` | 에이전트 결과 수신 직후, 결과 요약 전 |

**규칙**:
- 선언은 한 줄을 초과하지 않는다
- 기존 응답 첫 줄 표시(`📋 {name}[PM]: {NNN} {태스크명} | {단계}`)는 유지된다 (대체 아닌 추가)
- PM 직접 툴 호출이 연속될 때는 매 호출 직전 선언한다
- Agent 도구로 디스패치되는 모든 에이전트(워커, 테스트 에이전트, 액션 에이전트 등)에 적용된다 (문서 QA는 PM Gate가 직접 흡수하므로 QA 에이전트 디스패치는 없음)

---

변경이력:

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — 선언 형식 표기 "알투[PM]" → "{name}[PM]" placeholder 치환 (139) |
| v1.1 | 2026-06-07 | QA→PM Gate 통합 정합화 — 디스패치 대상 에이전트 예시 목록에서 "QA 에이전트" 제거(문서 QA는 PM Gate가 직접 흡수, QA 에이전트 디스패치 없음). 동작 검증(테스트 에이전트) 영역 불변 (014 Phase 4-2) |
