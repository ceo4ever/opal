# DONE: Ego Lite 브라우저 우선 통합

## 결과

브라우저 상호작용과 E2E의 공급자 순서를 Ego Lite → cmux → Playwright로 통일하고, 다음 공급자로의 전환은 `provider_unavailable`일 때만 허용하도록 실행 계약을 고정했다. 공개 정보 검색은 기존 웹 검색 경로에 유지했다.

Ego Lite 미설치 시 직접 설치·R2 설치·취소 선택과 원래 요청의 재개 정보를 반환한다. R2 설치는 macOS 아키텍처별 고정 DMG에 대해 이미지·SHA-256·코드서명·Gatekeeper 검증을 통과한 경우에만 진행하며, 앱 복사는 번들 심볼릭 링크를 보존하는 `ditto`를 사용한다.

공식 `ego-browser` 스킬을 MIT 라이선스와 고정 커밋으로 OPAL 커뮤니티 카탈로그 및 현재 Codex 환경에 설치했다. 실제 Ego CLI가 캡처 환경에서 실행 결과를 stderr로 전달하는 동작도 어댑터가 처리하도록 회귀 검증을 추가했다.

현재 환경의 `/Applications/ego lite.app`과 `~/.local/bin/ego-browser` 온보딩을 완료했고, 설치된 `test-tool`이 Ego Lite를 1순위로 선택하여 `https://example.com`의 `Example Domain`을 실제 브라우저에서 검증했다.

## 변경 파일

- `opal/tools/ego-browser-tool/`
- `opal/tools/test-tool/README.md`
- `opal/tools/test-tool/lib/e2e_adapter.py`
- `opal/tools/test-tool/lib/resolver.py`
- `opal/tools/test-tool/test_tool.py`
- `opal/tools/test-tool/tests/test_test_tool.py`
- `opal/templates/test-tools.yaml`
- `opal/tools/tool-scan/manifest.json`
- `opal/core/references/community-skills-registry.json`
- `opal/core/references/tools.md`
- `opal/core/references/agents.md`
- `opal/agents/opal-wtm-agent/AGENT.md`
- `skills/web-to-markdown/SKILL.md`
- `scripts/install-mac.sh`
- `docs/PROJECT.md`
- `docs/ARCHITECTURE.md`
- `docs/CONVENTIONS.md`
- `docs/SECURITY.md`
- `tasks/129-260914-opds-ego-lite-브라우저-우선통합/`

## 검증

- `ego-browser-tool` 단위·계약 테스트: 4/4 PASS.
- `test-tool` 단위·통합·회귀 테스트: 88/88 PASS.
- `test-tool integration`: Ego Lite 단독 선택, `Example Domain` assertion PASS, Space 11.
- 테스트 시나리오: 12/12 PASS, FAIL·BLOCKED·awaiting_human 0건.
- 충실도 게이트: 12/12 충족. 실제 브라우저 시나리오 S-10은 `real-usage`로 기록.
- 컨벤션 검사: Critical 0 / High 0 / 전체 finding 0.
- `code-scan validate`: 변경 Python 파일 coverage 100%, violation 0.
- source→`~/.opal` 핵심 도구 비교, JSON 파싱, shell 구문, `git diff --check`: 전부 PASS.

## 회고적 학습 후보

없음

## 참고

- Ego Lite는 개인·비상업 단일 사용자 선택 공급자이며 조직·상업 사용 전 Citro Enterprise 조건 확인이 필요하다.
- 공개 무해 페이지의 실제 E2E는 완료했다. 인증·동적 UI가 포함된 제품 시나리오는 캡틴이 말한 대로 이후 실제 태스크에서 계속 검증한다.
- 커밋은 사용자 권한이므로 수행하지 않았다.
