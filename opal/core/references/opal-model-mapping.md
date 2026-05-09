# OPAL 모델 매핑 (opal-model-mapping)

> 작성일: 2026-03-29 | 버전: v1.0
> 참조 전용 — 오케스트레이터/에이전트가 워커 디스패치 시 이 매핑을 따른다.
> 탐색 경로: ~/.opal/references/opal-model-mapping.md

## 1. 레벨 정의

스킬과 에이전트에서 model을 지정할 때 플랫폼 중립적인 레벨명을 사용한다.

| 레벨 | 용도 | 특성 |
|------|------|------|
| `light` | 단순 작업: 분류, 포맷 변환, 검색 기반 분석 | 빠르고 저렴, 간단한 추론 |
| `standard` | 범용 작업: 코드 작성, 문서 작성, 일반 분석 | 균형 잡힌 성능 |
| `advanced` | 복잡 추론: 아키텍처 설계, 깊은 분석, 전략 수립 | 최고 추론 능력 |

## 2. 플랫폼별 매핑 테이블

| 레벨 | Claude | Gemini | OpenAI |
|------|--------|--------|--------|
| `light` | haiku | gemini-2.5-flash-lite | gpt-4.1-mini |
| `standard` | sonnet | gemini-2.5-flash | gpt-4.1 |
| `advanced` | opus | gemini-2.5-pro | o3 |

> 플랫폼별 최신 모델이 출시되면 이 테이블을 갱신한다.

### 공식 모델 목록

| 플랫폼 | URL |
|--------|-----|
| Claude | https://docs.anthropic.com/en/docs/about-claude/models |
| Gemini | https://ai.google.dev/gemini-api/docs/models |
| OpenAI | https://developers.openai.com/api/docs/models |

## 3. 스킬에서의 참조 형식

스킬(SKILL.md)이나 에이전트(AGENT.md)에서 model을 지정할 때 레벨명을 사용한다:

```markdown
워커 디스패치. **model**: standard.
```

```markdown
**model**: advanced
```

에이전트 frontmatter:

```yaml
model: standard
```

## 4. 플랫폼 감지 및 자동 적용

부트스트랩 시 에이전트가 다음 순서로 모델 매핑을 적용한다:

1. **플랫폼 감지**: 부트스트래퍼 파일로 현재 플랫폼을 판별
   - `CLAUDE.md` → Claude
   - `.cursorrules` / `.cursor/rules/` → Cursor
   - `GEMINI.md` → Gemini
2. **매핑 로드**: 이 문서의 플랫폼별 매핑 테이블에서 해당 컬럼을 세션 컨텍스트에 로드
3. **자동 치환**: 스킬의 레벨명(`light`/`standard`/`advanced`)을 현재 플랫폼의 실제 모델명으로 적용

> **Cursor 특이사항**: Cursor는 사용자가 설정한 모델 제공자(Claude/Gemini/OpenAI)에 따라 매핑이 달라진다. Cursor 감지 시 모델 제공자를 추가 확인하거나 사용자에게 질문한다.

## 5. 갱신 가이드라인

- 새 모델 출시 시 해당 플랫폼 컬럼만 갱신한다
- 레벨 정의(light/standard/advanced)는 변경하지 않는다
- 갱신 후 변경이력에 기록한다
- 소스(`opal/core/references/`)를 수정하고, `install-mac.sh`로 배포본(`~/.opal/references/`)에 동기화한다

---

변경이력:

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 — 3레벨 정의 + Claude/Gemini/OpenAI 매핑 |
| v1.1 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — frontmatter 작성자 필드 삭제 + 변경이력 작성자 컬럼 제거 (139) |
