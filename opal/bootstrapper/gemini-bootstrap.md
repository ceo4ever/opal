# OPAL 부트스트래퍼 (Antigravity)

> **사용법**: 이 내용이 `~/.gemini/GEMINI.md`에 마커 기반으로 자동 삽입된다.
> `install-mac.sh`에서 OPAL 설치 시 자동 처리.
>
> **버전**: v1.1 (2026-03-14)

---

아래 내용이 `~/.gemini/GEMINI.md`에 삽입된다:

---

```markdown
## OPAL AI Agent — 필수 부트스트랩

> **[첫 줄 마커 게이트 — 최우선]** 사용자 메시지(디스패치 프롬프트)의 **첫 줄**이 정확히 `[WORKER]`이면 — 아래 스킵 게이트·`[MUST]` 파일 로드를 포함한 OPAL 부트스트랩 전체를 생략하고, 어떤 tier도 로드하지 않은 채 마커 다음 줄부터를 실제 요청으로 즉시 처리한다(아래 `[MUST]`보다 이 규칙이 우선한다). 첫 줄이 `[ASSISTANT]`이면 — 아래 절차는 정상 진행하되 `~/.opal/AGENT.md`의 `[ASSISTANT 규칙]`에 따라 PM(Phase B) 승격만 억제한다. 마커가 없으면 아래를 정상 수행한다.

> **[스킵 게이트 + 프로젝트 설정 머지]** 먼저 Read 도구로 `~/.opal/setting.json`(전역)을 읽고, 현재 작업 디렉토리의 `.opal/setting.local.json`(프로젝트)이 있으면 Read하여 전역 위에 키 단위로 덮어쓴다(로컬 우선, 로컬에 없는 키는 전역 유지). 병합된 effective setting의 `bootstrap` 값이 정확히 `off`이면 — 이하 OPAL 부트스트랩 절차 전체(정체성 포함)를 생략하고, OPAL 없이 순수 동작한다. 전역·로컬 모두 파일이 없거나·`bootstrap` 필드가 없거나·`off`가 아니거나·JSON 파싱에 실패하면 — 게이트를 무시하고 아래 절차를 정상 수행한다(fail-safe).

> 이 진입점은 알투 비서(비서 tier)를 활성화하며, OPAL 프로젝트(`.opal/AGENT.md` 존재) 진입 시 AGENT.md가 PM tier로 자동 승격한다.

**[MUST]** 사용자의 첫 번째 메시지에 응답하기 전에, 아래 파일들을 Read 도구로 순서대로 읽고 그 내용에 따라 행동해야 한다. 이 단계를 건너뛰면 안 된다.

1. `~/.opal/AGENT.md` — 에이전트 정의 및 부트스트랩 절차
2. `~/.opal/identity.md` — 에이전트 정체성 (없으면 AGENT.md의 온보딩 절차를 따른다)
```

---

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-03-09 | 최초 작성 — R2 스니핏을 OPAL 부트스트래퍼로 대체 |
| v1.1 | 2026-03-14 | Claude Code와 동일한 강제 부트스트랩으로 강화 — 정체성 혼합 문제 해결 |
| v1.1.1 | 2026-06-24 | OPAL_BOOTSTRAP=off skip 게이트 문구 추가 — Eager 부트스트랩 전체 스킵 옵션 (040) |
| v1.2 | 2026-06-28 | 스킵 게이트에 프로젝트 `.opal/setting.local.json` 머지 추가 — 전역 위에 로컬 키 덮어쓰기(로컬 우선), 병합된 effective setting의 `bootstrap`으로 판정. (046) |
| v1.1.2 | 2026-06-24 17:24 | OPAL_BOOTSTRAP 환경변수 게이트 → `~/.opal/setting.json` Read 게이트 전환 (043) |
| v1.2.1 | 2026-06-30 16:41 | 비서 tier 진입점 의미 1줄 정합 — PM 승격은 AGENT.md가 `.opal/AGENT.md` 존재 시 자동 수행 (049) |
| v1.3 | 2026-07-12 | 첫 줄 마커 게이트 신설 — `[WORKER]` 첫 줄이면 부트스트랩 전체 스킵(헤드리스 워커 배선), `[ASSISTANT]` PM 승격 억제 명문화. AGENT.md 마커 사다리를 진입점에 연결. (opal-agent) |
