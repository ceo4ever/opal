# opal-agent-creator

커뮤니티 create-subagents로 서브에이전트를 설계한 뒤, OPAL 프레임워크 규격에 맞게 등록까지 마무리하는 에이전트 생성 파이프라인입니다.

## 개요

에이전트 콘텐츠 설계(create-subagents에 위임)와, 그 결과를 OPAL 규격(파일 배치, frontmatter, 레지스트리 등록, 버전 태깅)에 맞추는 후처리를 2단계로 이어서 수행합니다. 새 에이전트를 만들 때뿐 아니라 기존 에이전트를 개선할 때도 사용합니다.

## 트리거

- "에이전트 만들어줘"
- "에이전트 생성"
- "서브에이전트 추가"
- "에이전트 작성해줘"
- "에이전트 개선해줘"
- 기존 에이전트 수정/개선 요청
- "에이전트 만들고 등록해줘"
- "OPAL 에이전트 추가"

## 사용법

| 요청 형태 | 진입 모드 |
|-----------|-----------|
| "만들어줘" / "생성" / "추가" | 신규 생성 모드 |
| "개선해줘" / "수정해줘" / 에이전트명 지정 | 개선 모드 |

## 동작 흐름

### Phase 1 — 에이전트 콘텐츠 생성 (create-subagents 위임)

1. 커뮤니티 create-subagents의 SKILL.md를 읽고, 아래 7개 참조 문서를 설계 품질 근거로 활용합니다.
   - `subagents.md` (파일 형식·모델 선택·도구 보안)
   - `writing-subagent-prompts.md` (프롬프트 작성·XML 구조)
   - `orchestration-patterns.md` (순차/병렬/계층 패턴)
   - `context-management.md` (메모리 아키텍처·컨텍스트 전략)
   - `error-handling-and-recovery.md` (실패 모드·복구 전략)
   - `evaluation-and-testing.md` (평가 메트릭·테스트 전략)
   - `debugging-agents.md` (로깅·진단 절차)
2. 신규 생성 모드에서는 name(kebab-case, `{워크플로우}-{역할}` 패턴 권장), description, tools(최소 권한), model(레벨 기반: advanced/standard/light), system prompt(역할·프로세스·반환 형식·실행 규칙)를 순서대로 확정합니다.
3. 개선 모드에서는 기존 `agents/{name}/AGENT.md`를 읽고 create-subagents의 설계 원칙에 따라 사용자 피드백을 반영해 반복 개선합니다.
4. 이때 한국어 본문/영어 코드 규칙, 명령형 문체, 시스템 프롬프트 필수 구성 요소, XML 또는 Markdown 구조 선택 같은 OPAL 규칙을 create-subagents에 전달합니다.

### Phase 2 — OPAL 규격 후처리

1. **에이전트 파일 저장**: 완성된 AGENT.md를 `agents/{name}/AGENT.md` 단일 경로에 저장합니다(플랫폼별 변환 불필요).
2. **YAML frontmatter 보정**: `name`(kebab-case·디렉토리명 일치), `description`(역할+호출 시점), `model`(inherit/light/standard/advanced), `tools`(최소 권한)를 검증·보정합니다.
3. **에이전트 레지스트리 등록**: `~/.opal/references/agents.md`에 역할·호출 시점·입력·출력을 명시한 항목을 추가하거나(신규), 변경된 부분을 갱신합니다(개선).
4. **버전 태깅**: 신규 생성 시 상단에 `> 작성일: {날짜} | 버전: v1.0`을 기록합니다. 개선 시 구조적 변경은 Major, 내용 수정은 Minor로 버전을 올립니다.
5. **탐색 경로 안내**: 이 에이전트를 호출하는 스킬이 있으면, 해당 SKILL.md에 `{프로젝트}/.opal/agents/{name}/AGENT.md` → `~/.opal/agents/{name}/AGENT.md` 순서의 탐색 경로를 추가하도록 안내합니다.

완료 후 체크리스트(경로, frontmatter, 레지스트리 등록, 버전 태깅, 네이밍 패턴, 언어 규칙)를 검증하고 결과를 보고합니다.

## 산출물

- `agents/{name}/AGENT.md` (신규 생성/개선)
- `~/.opal/references/agents.md`에 등록된 항목
- (해당 시) 호출 스킬의 SKILL.md에 추가된 탐색 경로 안내

## FAQ

### create-subagents 자체를 직접 수정하나요
아니요. opal-agent-creator는 커뮤니티 create-subagents를 래핑만 하며, create-subagents 자체는 수정하지 않습니다.

### 에이전트 이름은 어떻게 지어야 하나요
`{워크플로우}-{역할}` 패턴의 kebab-case를 권장합니다 (예: `op-task-qa`, `opal-wtm-agent`).
