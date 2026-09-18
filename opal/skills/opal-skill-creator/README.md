# opal-skill-creator

커뮤니티 skill-creator로 새 스킬 콘텐츠를 만든 뒤, OPAL 프레임워크 규격에 맞게 자동으로 마무리해 주는 스킬 생성 파이프라인입니다.

## 개요

스킬 본문을 작성하는 작업(skill-creator에 위임)과, 그 결과를 OPAL 규격(디렉토리 배치, frontmatter, 레지스트리 등록, 문서 표준)에 맞추는 후처리 작업을 2단계로 이어서 수행합니다. 새 스킬을 만들 때뿐 아니라 기존 프레임워크 스킬을 개선할 때도 사용합니다.

## 트리거

- "새 스킬 만들어줘"
- "스킬 생성"
- "프레임워크 스킬 추가"
- "스킬 작성해줘"
- "스킬 개선해줘"
- 기존 프레임워크 스킬 수정/개선 요청
- "스킬 만들고 등록해줘"
- "OPAL 스킬 추가"

## 사용법

| 요청 형태 | 진입 모드 |
|-----------|-----------|
| "만들어줘" / "생성" / "추가" | 신규 생성 모드 |
| "개선해줘" / "수정해줘" / 스킬명 지정 | 개선 모드 |

신규 생성 시 스킬 유형을 확인합니다. 명시하지 않으면 프레임워크 스킬로 기본 설정됩니다.

| 유형 | 저장 경로 | 기준 |
|------|----------|------|
| 프레임워크 스킬 | `skills/{name}/SKILL.md` | 3개 플랫폼 공용, install-mac.sh로 배포 |
| OPAL 전용 스킬 | `~/.opal/skills/{name}/SKILL.md` | OPAL 에이전트에서만 사용 |

## 동작 흐름

### Phase 1 — 콘텐츠 생성 (skill-creator 위임)

1. 커뮤니티 skill-creator의 SKILL.md를 읽고 그 프로세스를 그대로 따릅니다.
2. 신규 생성 모드: Capture Intent → Interview and Research → Write the SKILL.md → (선택) Test Cases → (선택) 실행/평가 → (선택) 반복 개선 순서로 진행합니다.
3. 개선 모드: 기존 SKILL.md를 읽고 skill-creator의 improve 플로우로 사용자 피드백에 따라 반복 개선합니다.
4. 이때 한국어 본문/영어 코드 규칙, 명령형 문체, SKILL.md 500줄 이하 유지, 필요 시 `references/`로 상세 분리 같은 OPAL 규칙을 skill-creator에 전달합니다.

### Phase 2 — OPAL 규격 후처리

Phase 1에서 완성된 SKILL.md에 아래 5가지를 순서대로 적용합니다.

1. **디렉토리 구조 확정**: 스킬 유형에 맞는 경로(`skills/{name}/` 또는 `~/.opal/skills/{name}/`)에 SKILL.md를 저장합니다.
2. **YAML frontmatter 보정**: `name`을 kebab-case·디렉토리명 일치로 맞추고, `description`을 "**한줄 요약**. ... 반드시 이 스킬을 사용해야 하는 상황: ..." 구조로 정리합니다.
3. **레지스트리 등록**: `~/.opal/references/skills.md`의 해당 섹션 표에 새 행을 추가하거나(신규), 변경된 트리거·설명을 갱신합니다(개선).
4. **문서 이력·버전 정합**: 수기 누적 이력 절이나 단순 작성 횟수용 버전을 만들지 않습니다. 개선 모드에서는 기존 이력 절을 제거하고 제자리에서 갱신합니다.
5. **에이전트 생성 (선택)**: 스킬이 독립 컨텍스트 실행을 필요로 할 때만, 사용자 확인 후 Claude Code/Cursor/Antigravity 3개 플랫폼 에이전트 파일을 생성합니다.

완료 후 체크리스트(경로, frontmatter, 트리거 패턴, 레지스트리 등록, 문서 표준, 줄 수, 언어 규칙)를 검증하고 결과를 보고합니다.

## 산출물

- `skills/{name}/SKILL.md` 또는 `~/.opal/skills/{name}/SKILL.md` (신규 생성/개선)
- `~/.opal/references/skills.md`에 등록된 항목
- (선택) `agents/claude/{name}/AGENT.md`, `agents/cursor/{name}.md`, `agents/antigravity/{name}/SKILL.md`

## FAQ

### skill-creator 자체를 직접 수정하나요
아니요. opal-skill-creator는 커뮤니티 skill-creator를 래핑만 하며, skill-creator 자체는 수정하지 않습니다.

### 스킬 개선 시 이전 버전 이력이 남나요
아니요. 변경 경위는 git과 태스크 기록이 소유하므로, SKILL.md 안에 수기 이력 절을 만들지 않습니다.
