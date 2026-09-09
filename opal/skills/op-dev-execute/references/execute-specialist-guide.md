# EXECUTE 전문 에이전트 가이드

> 대상: opal-fe-agent / opal-be-agent / opal-db-agent
> 공통 절차: `references/execute-guide.md`

## 적용 차이

- AGENT.md의 도메인 경계와 PM이 배정한 W의 `담당`, `변경 대상`을 함께 지킨다.
- 담당 영역 밖 파일이나 다른 W의 파일이 필요하면 수정하지 않고 PM에 재배정을 요청한다.
- PM이 주입한 `## 실행 capability`만 사용한다. 다른 스킬·에이전트를 자체 호출하지 않는다.
- `changed_files`에는 담당 영역과 배정 W의 변경 대상에 포함된 파일만 반환한다.

나머지 진입 검사, 구현, 검증, 상태 기록, 블로커, 결과 형식은 공통 가이드만 따른다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-23 11:39 | 초기 작성 — 전문 에이전트 EXECUTE 지침 분리 (129) |
| v1.1 | 2026-09-09 KST | task 111 — sdlc-v2 Work items/AC-C-H-S/state.json/test-scenario.json 기준을 우선 적용하고 §4.2/§3.N.2/F-NNN은 legacy 폴백으로 한정 |
| v1.2 | 2026-09-09 KST | 고정 도메인 MCP/스킬 목록을 제거하고 PM dispatch가 주입한 런타임 capability만 사용하도록 전환 (111) |
| v1.3 | 2026-09-09 KST | 고정 UI 스킬 라우팅을 제거하고 PM 주입 capability 소비와 전문 영역 차이만 남김 (111) |
