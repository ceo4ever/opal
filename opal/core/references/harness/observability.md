# Observability (관측)

> 출처: opal-harness.md §5
> 로드 시점: 워커 디스패치 직전 (매 디스패치마다)
> 역할: 스킬 탐색 경로 + 프로젝트 메모리 동기화 + 타임스탬프 취득 + 행위 주체 표시

---

### 스킬 탐색 경로

| 유형 | 탐색 경로 (1. 프로젝트 → 2. 배포본) |
|------|------------------------------------|
| dev 단계 스킬 | `{프로젝트}/.opal/skills/op-dev-{stage}/SKILL.md` → `~/.opal/skills/op-dev-{stage}/SKILL.md` |
| 범용 단계 스킬 | `{프로젝트}/.opal/skills/op-task{-suffix}/SKILL.md` → `~/.opal/skills/op-task{-suffix}/SKILL.md` |
| 에이전트 | `{프로젝트}/.opal/agents/{agent-name}/AGENT.md` → `~/.opal/agents/{agent-name}/AGENT.md` |

### 프로젝트 메모리 동기화

`{프로젝트}/.opal/MEMORY.json`이 존재하면, 단계 완료 시 작업 히스토리를 memory-tool로 갱신한다:

```
~/.opal/tools/memory-tool/run.sh append --file .opal/MEMORY.json --kind history \
  --title "<태스크명>" --stage "<단계>" --path "tasks/<폴더>/" --summary "<핵심결과>"
```

- [MUST] 표·파일 직접 편집 금지 — 도구 호출만 사용한다.
- **FIFO 규칙**: 히스토리는 **최대 5개**이며 도구가 추가 시점에 결정론적으로 집행한다(`prune` 불필요).

#### 타임스탬프 취득 규칙 (필수)

시작일시/완료일시 기록 시 반드시 bash 명령을 실행하여 KST 현재 시각을 취득한다:
- 일시 (`YYYY-MM-DD HH:mm`): `node ~/.opal/tools/date/date.js datetime`
- 일자 (`YYYY-MM-DD`): `node ~/.opal/tools/date/date.js date`
- 폴더명용 (`YYMMDD`): `node ~/.opal/tools/date/date.js yymmdd`

**bash 생략 금지**: 컨텍스트에 날짜가 있어도 bash 실행은 필수다. 시간(HH:mm)까지 정확히 기록해야 한다.

### 행위 주체 표시 — PM은 툴 호출 직전/직후 한 줄 선언으로 행위 주체를 명시한다

#### 아이콘 룩업

**트리거**: PM이 Agent 도구로 에이전트를 디스패치할 때(아이콘 룩업·아래 선언 형식 모두 이 트리거 — PM 발화 + Agent 도구 — 에만 적용). 디스패치 시 해당 에이전트 AGENT.md의 frontmatter `icon` 필드를 읽어 사용하고, 없으면 디폴트 아이콘 `✨`을 사용한다.

**적용 범위 제외 — opal-agent 내부 채널**: 루프 액션 에이전트(`opal-loop-action-agent`) 등 서브에이전트가 opal-agent(headless CLI) 채널로 내부 디스패치하는 경우는 (a) PM 발화가 아니고 (b) Agent 도구 호출도 아니므로 위 트리거에 해당하지 않으며, 본 절 적용 범위 밖이다 — 아이콘 룩업·선언 형식의 대상이 아니다. 해당 채널의 관측성은 이 문서가 아니라 호출 주체(예: 루프 액션 에이전트)가 소유하며, 그 규약은 `opal/agents/opal-loop-action-agent/AGENT.md` §결과 파일 규약이 결과 파일(`.oppl-run/*`)·결과 요약으로 자체 확보한다.

| 선언 형식 | 사용 시점 |
|----------|---------|
| `📋 {name}[PM] 직접:` | PM이 직접 툴을 호출하기 직전 (Edit, Write, Read 등) |
| `{icon} 디스패치: {단계명} — {설명}` | Agent 도구로 에이전트를 디스패치하기 직전 (워커 · QA · 테스트 · 액션 등 모든 에이전트) |
| `{icon} 완료: {단계명} — {결과 요약}` | 에이전트 결과 수신 직후, 결과 요약 전 |

**규칙**:
- 선언은 한 줄을 초과하지 않는다
- 기존 응답 첫 줄 표시(`📋 {name}[PM]: {NNN} {태스크명} | {단계}`)는 유지되며(대체 아닌 추가), PM 직접 툴 호출이 연속될 때는 매 호출 직전 선언한다
- Agent 도구로 디스패치되는 모든 에이전트(워커, 테스트 에이전트, 액션 에이전트 등)에 적용된다 (문서 QA는 PM Gate가 직접 흡수하므로 QA 에이전트 디스패치는 없음)

---

변경이력:

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — 선언 형식 표기 "알투[PM]" → "{name}[PM]" placeholder 치환 (139) |
| v1.1 | 2026-06-07 | QA→PM Gate 통합 정합화 — 디스패치 대상 에이전트 예시 목록에서 "QA 에이전트" 제거(문서 QA는 PM Gate가 직접 흡수, QA 에이전트 디스패치 없음). 동작 검증(테스트 에이전트) 영역 불변 (014 Phase 4-2) |
| v1.2 | 2026-07-17 14:24 | 아이콘 룩업 트리거를 "PM 발화 + Agent 도구"로 명확화 + 적용 범위 제외 문단 신설 — 루프 액션 에이전트 등 서브에이전트의 opal-agent(headless CLI) 내부 채널 디스패치는 아이콘 룩업·선언 형식 대상이 아니며, 관측성은 결과 파일·결과 요약으로 자체 확보함을 명시 (066) |
| v1.3 | 2026-07-28 22:47 | 프로젝트 메모리 동기화 절 정정(기존 결함 교정, memory-tool 도입(045) 이전 관행의 표 편집·구건수 서술 잔존분) — `MEMORY.json` + `append --kind history` 도구 호출·FIFO 5(도구 결정론 집행)로 교체, 직접 편집 금지 명시 (078) |
| v1.4 | 2026-08-09 21:08 | 서술 중복 압축(스킬 탐색 경로 표 전환, 아이콘 룩업·규칙 문단 통합) + `opal-loop-action-agent/AGENT.md` 참조를 "본 절 적용 범위 밖 — 해당 규약은 그 문서가 소유" 형태로 정합(단순 인용, 홉 미계상) (087) |
