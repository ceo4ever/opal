# DONE: 세션 브리핑 출력 집행

## 결과

`session.project` 부트에서 상태·메모리 JSON을 읽고도 사용자 응답에서 요약 블록이
누락되던 경로를 제거했다. `event-loader project-brief`가 최대 1건의 이어보기와 최대
2건의 우선 검토 항목을 완성된 Markdown으로 조립하고, 네 플랫폼 부트스트래퍼가 그
stdout을 첫 응답 맨 앞에 byte-for-byte 출력하도록 계약을 강화했다.

## 주요 변경

- `event-loader project-brief` raw Markdown 및 `--json` 진단 출력을 추가했다.
- 상태·메모리 조회 중 하나가 실패하면 해당 블록만 생략하고 짧은 접두부는 유지한다.
- 출력 전체를 UTF-8 1,024바이트 이하로 제한한다.
- Claude Code·Codex·Cursor·Gemini의 공통 부트 본문을 단일 명령 계약으로 통일했다.
- 통합 감사가 문서 조각뿐 아니라 실제 렌더링 stdout과 빈 결과를 검증하도록 보강했다.
- 공식 macOS 설치기 메뉴 1로 `~/.opal/` 및 플랫폼 부트스트래퍼에 배포했다.

## 변경 파일

- `opal/tools/event-loader/event_loader.py`
- `opal/tools/event-loader/tests/test_event_loader_extended.py`
- `opal/tools/event-loader/README.md`
- `opal/bootstrapper/claude-bootstrap.md`
- `opal/bootstrapper/codex-bootstrap.md`
- `opal/bootstrapper/cursor-bootstrap.mdc`
- `opal/bootstrapper/gemini-bootstrap.md`
- `opal/core/AGENT.md`
- `opal/core/references/opal-pm.md`
- `scripts/tests/task113_bootstrap_audit.py`
- `scripts/tests/test_task113_bootstrap_contract.py`
- `docs/ARCHITECTURE.md`
- `docs/PROJECT.md`
- `tasks/117-260912-opd-세션-브리핑-출력-집행/`

## 검증

- event-loader 전체 단위·통합 테스트: 12건 통과
- bootstrap 계약 테스트: 2건 통과
- source bootstrap audit: 통과
- installed parity audit: 통과
- 실제 설치본 `project-brief`: 이어보기·우선 검토 동시 출력 확인
- 소스·설치본 event-loader SHA-256: 일치
- TEST 시나리오: 6/6 PASS, RED 대상 2/2 확인, fidelity 6/6 충족
- `py_compile`, `git diff --check`, code-scan: 통과

## 참고

- 캡틴의 직접 수행 지시에 따라 알투가 구현·검증했으며, 독립 evaluator는 생략하고
  결정론적 커버리지 검사와 실제 RED/GREEN 증거로 대체했다.
- 기존 115 태스크와 동시에 생성된 118 태스크의 파일은 수정하거나 복원하지 않았다.
- 이번 태스크는 `docs/proposals/`를 소비하지 않아 제안서 아카이브 판정은 no-op이다.
- 커밋은 생성하지 않았다.
