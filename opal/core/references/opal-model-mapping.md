# OPAL 모델 매핑 (opal-model-mapping)

> 작성일: 2026-03-29 | 버전: v1.4
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

| 레벨 | Claude | Gemini | OpenAI (참조전용) | Codex |
|------|--------|--------|--------|-------|
| `light` | haiku | gemini-3.1-flash-lite | gpt-5.4-mini | gpt-5.4-mini |
| `standard` | sonnet | gemini-flash-latest | gpt-5.4 | gpt-5.4 |
| `advanced` | opus | gemini-pro-latest | gpt-5.5 | gpt-5.5 |

> 플랫폼별 최신 모델이 출시되면 이 테이블을 갱신한다.

> **OpenAI 컬럼 = 참조 전용(install 어댑터 미연동)** — `install-mac.sh` mapping dict에 `openai` 키 없음(호출처 전체에 `platform="openai"` 없음). Codex 경로가 OpenAI 모델을 ChatGPT-auth로 사용한다.

### 공식 모델 목록

| 플랫폼 | URL |
|--------|-----|
| Claude | https://docs.anthropic.com/en/docs/about-claude/models |
| Gemini | https://ai.google.dev/gemini-api/docs/models |
| OpenAI | https://developers.openai.com/api/docs/models |
| Codex | https://developers.openai.com/codex/config-reference |

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
   - `AGENTS.md` (`~/.codex/AGENTS.md`) → Codex
2. **매핑 로드**: 이 문서의 플랫폼별 매핑 테이블에서 해당 컬럼을 세션 컨텍스트에 로드
3. **자동 치환**: 스킬의 레벨명(`light`/`standard`/`advanced`)을 현재 플랫폼의 실제 모델명으로 적용

> **Cursor 특이사항**: Cursor는 사용자가 설정한 모델 제공자(Claude/Gemini/OpenAI)에 따라 매핑이 달라진다. Cursor 감지 시 모델 제공자를 추가 확인하거나 사용자에게 질문한다.

## 5. 갱신 가이드라인

- 새 모델 출시 시 해당 플랫폼 컬럼만 갱신한다
- 레벨 정의(light/standard/advanced)는 변경하지 않는다
- 갱신 후 변경이력에 기록한다
- 소스(`opal/core/references/`)를 수정하고, `install-mac.sh`로 배포본(`~/.opal/references/`)에 동기화한다
- Codex는 모델 ID 변경 빈도가 높다 — 분기마다 [Codex Config Reference](https://developers.openai.com/codex/config-reference) 점검.

**최신 추종 운영 규칙 (2026-06-02 도입, 2026-06-17 점검)**:
- Claude(`haiku/sonnet/opus`)·Gemini standard/advanced(`gemini-flash-latest`/`gemini-pro-latest`)는 부동 별칭으로 자동 추종 → 갱신 불요.
- **별칭이 없는 Gemini light(`gemini-3.1-flash-lite`)·Codex·OpenAI는 분기마다 [Gemini API Models](https://ai.google.dev/gemini-api/docs/models) / [Codex Models](https://developers.openai.com/codex/models) / [OpenAI All Models](https://developers.openai.com/api/docs/models/all) 점검 후 핀 갱신.**
- `gemini-pro-latest`는 현 시점 preview 빌드를 가리킬 수 있다. preview 거동 변동 시 구체 ID 핀으로 임시 전환 가능. `gemini-*-latest` 별칭이 Gemini 3.x(3 Flash·3.5 Flash·3 Pro)를 추종하는지는 런타임에서 확인한다.
- **Codex 특화 핀 폐지 (2026-06-17)**: `gpt-5.3-codex`는 2026-06-30 일몰(신규 API 요청 중단)되며, 범용 대체 `gpt-5.5-codex`는 존재하지 않는다. Codex 특화 라인은 `gpt-5.3-codex-spark`(리서치 프리뷰·ChatGPT Pro·텍스트only)뿐이라 범용 advanced로 부적합 → Codex advanced는 프런티어 `gpt-5.5`로 통일한다.
- Claude advanced는 `opus`(부동) 유지. 최상위 `claude-fable-5`는 비용 2배·thinking 상시·30일 보존 필수 등 거동 차이로 기본 핀에서 보류(필요 시 별도 검토).

---

변경이력:

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-29 | 초기 작성 — 3레벨 정의 + Claude/Gemini/OpenAI 매핑 |
| v1.1 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — frontmatter 작성자 필드 삭제 + 변경이력 작성자 컬럼 제거 (139) |
| v1.2 | 2026-05-24 | Codex 컬럼 추가 + 플랫폼 감지/갱신 가이드 보강 (009) |
| v1.3 | 2026-06-02 20:16 KST | Gemini 부동 별칭 전환 + Codex 최신화 + OpenAI 참조전용 명시 + 최신 추종 운영 규칙 보강 (011) |
| v1.4 | 2026-06-17 10:21 KST | 최신 모델 재검토 — Codex/OpenAI standard `gpt-5.5`→`gpt-5.4`·advanced `gpt-5.3`/`gpt-5.3-codex`→`gpt-5.5`(gpt-5.3-codex 2026-06-30 일몰, gpt-5.5-codex 부재) + 운영 규칙에 Codex 특화 핀 폐지·Gemini 3.x 추종 확인·Fable 5 보류 명문화 + 헤더 버전 v1.0→v1.4 정합. Claude(haiku/sonnet/opus)·Gemini light(gemini-3.1-flash-lite GA) 현행 확인 |
