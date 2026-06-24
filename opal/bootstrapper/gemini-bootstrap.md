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

> **[스킵 게이트]** 먼저 Read 도구로 `~/.opal/setting.json`을 읽는다. JSON의 `bootstrap` 필드 값이 정확히 `off`이면 — 이하 OPAL 부트스트랩 절차 전체(정체성 포함)를 생략하고, OPAL 없이 순수 동작한다. 파일이 없거나·`bootstrap` 필드가 없거나·`off`가 아니거나·JSON 파싱에 실패하면 — 게이트를 무시하고 아래 절차를 정상 수행한다(fail-safe).

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
| v1.1.2 | 2026-06-24 17:24 | OPAL_BOOTSTRAP 환경변수 게이트 → `~/.opal/setting.json` Read 게이트 전환 (043) |
