---
template: sdlc-v2
---
# TEST-SCENARIO: Ego Lite 브라우저 우선 통합

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: macOS arm64 개발 머신, 프로젝트 소스와 `~/.opal` 배포본, Python unittest, Node 기반 skill-registry, 실제 Ego Lite 앱과 `ego-browser` CLI
- 공통 데이터: 공개·무해한 `https://example.com`과 assertion 문자열 `Example Domain`; DMG version 0.4.5.9의 고정 manifest; 공식 스킬 commit `d01be93325c7ea59d41c2ca9f4c59b58b4be4046`
- 대역 사용과 한계: 공급자 순회·오류·설치 실패는 임시 실행 파일과 가짜 명령 결과로 검증한다. 대역 결과는 실제 앱 설치, 코드서명·공증 확인, GUI 온보딩, 실제 Ego Space E2E를 대신하지 않는다.
- 실행 조건: 결정론 검사는 자동 실행한다. 앱 최초 온보딩은 캡틴이 GUI에서 완료하고 같은 run의 resume 정보로 재개한다. 인증·결제·게시·삭제 등 외부 부작용은 실행하지 않는다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, AC-5, C-3, H-4 | 세 공급자 stub과 priority가 뒤섞인 E2E 설정 | test-tool 공개 CLI로 integration을 실행하고 공급자 호출 로그를 확인 | priority 정렬 결과가 Ego→cmux→Playwright이고 최종 JSON이 E2E contract 상태·driver·expected/actual을 보존한다 | Python unittest, CLI integration | 구현 전 RED |
| S-2 | AC-3, C-2, H-2, H-5 | Ego 앱/CLI가 없고 설치 선택이 전달되지 않음 | Ego smoke와 test-tool integration을 실행 | silent fallback 없이 `awaiting_human`이고 manual·r2·cancel 선택, URL·assertion·resume 인자가 모두 반환된다 | Python unittest, CLI JSON | 구현 전 RED |
| S-3 | AC-6, C-3, H-4, H-5 | 각 후보가 순서대로 `provider_unavailable`, `fail`, `infra_error`, `blocked`, `awaiting_human`을 반환 | 상태 조합별 integration 실행과 호출 로그 비교 | `provider_unavailable`에서만 다음 후보가 호출되고 나머지는 즉시 종료되며 후보 소진만 `executor_unavailable`이다 | Python unittest matrix | 구현 전 RED |
| S-4 | AC-4, C-4, C-5, H-1 | 비지원 OS/arch, hash 불일치, hdiutil 실패, codesign 실패, spctl 실패, 정상 검증 fixture | `ego-browser-tool status/install`을 각 fixture로 실행 | 비지원 환경은 provider unavailable, 검증 실패는 기존 앱을 덮어쓰지 않는 blocked/infra error, 모든 검증 통과만 앱 복사와 `awaiting_human`을 반환한다 | Python unittest + 명령 stub, 임시 설치 경로 | 구현 전 RED |
| S-5 | AC-5, AC-9, C-6, H-3, H-6 | Ego CLI sentinel 정상·부재·중복·비정상 종료 fixture와 expect text 일치/불일치 | `ego-browser-tool smoke` 실행 | 일치는 pass, 불일치는 fail, malformed/비정상 CLI는 infra_error이며 결과에는 제한된 expected/actual과 Space id만 있고 cookie·token·전체 페이지가 없다 | Python unittest + Ego CLI stub | 구현 전 RED |
| S-6 | AC-1, AC-6, AC-10, C-3, C-4 | Ego unavailable, cmux unavailable, Playwright 성공/실패 fixture와 기존 cmux fixture | test-tool 전체 회귀 테스트 실행 | 순차 fallback과 Playwright assertion이 동작하고 기존 cmux fail/infra/격리 시퀀스 및 assertion 없는 pass 금지가 유지된다 | `python -m unittest discover -s opal/tools/test-tool/tests` | 구현 전 RED |
| S-7 | AC-7, C-5, C-7 | 공식 repo shallow clone과 소스 카탈로그, 비어 있는 또는 기존 user registry | migrate dry-run/실행, scan-risk, clone-copy, registry validate/match/list, Codex skill-installer 실행 | OPAL과 Codex 양쪽에 `SKILL.md`가 있고 OPAL registry가 citrolabs/ego-browser·MIT·고정 commit·SAFE를 반환하며 기존 user registry 항목은 보존된다 | skill-registry CLI + filesystem 실측 | 구현 후 |
| S-8 | AC-2, AC-3, AC-8, C-1, C-2, C-6, H-7 | 변경된 WTM skill·agent·tools/security/project 문서 | 라우팅·용어 정적 검사를 실행 | 공개 검색은 기존 web search, browser extract/UI/E2E는 Ego 우선, 미설치는 세 선택, cancel 후 cmux→Playwright, 민감·부작용은 사람 인계로 모든 소비자 문안이 일치한다 | `rg` 기반 정적 회귀 + 문서 직접 검토 | 구현 후 |
| S-9 | AC-4, AC-8, AC-10, C-7 | 소스 테스트가 모두 통과한 상태 | `scripts/install-mac.sh`로 배포 후 source/installed tool·template·catalog·skill/agent를 비교하고 code-scan validate를 실행 | 설치 성공, ego-browser-tool 실행 권한, tool-scan 검색 가능, source/installed 계약 동일, newly_uncovered 0건, 사용자 community skill/user registry 보존이다 | 실제 OPAL install + checksum/diff + code-scan | 배포 후 |
| S-10 | AC-4, AC-7, AC-9, C-2, C-5, C-6, H-1, H-2, H-3, H-6, H-8 | 실제 macOS 지원 아키텍처, Ego 미설치, 공개 example.com만 허용 | 검증 installer를 실행하고 캡틴이 GUI 온보딩한 뒤 같은 handoff를 resume하여 `--expect-text 'Example Domain'` smoke 실행 | DMG version/hash·서명·공증 증거가 남고 CLI readiness가 통과하며 실제 별도 Space에서 expected/actual assertion pass와 Space id가 기록된다 | collaborative browser E2E, human onboarding + Ego CLI | 설치 후 |
| S-11 | AC-10, C-1, C-3 | Ego 선택과 무관한 공개 웹 검색 및 기존 Playwright 추출 입력 | 일반 web search 1건과 playwright-tool 공개 URL 추출 회귀 실행 | 검색은 Ego 설치 prompt 없이 기존 검색 결과를 반환하고 Playwright 추출은 기존 JSON/content 계약을 유지한다 | 실제 web search + Playwright CLI 또는 기존 회귀 | 구현 후 |
| S-12 | AC-4, AC-7, AC-8, C-5, C-6, H-7 | 최종 문서와 카탈로그 | 문서·registry에서 앱 번들/상업 기본 사용/quarantine 제거/무고지 인증 행동 문구를 검사 | 앱은 optional user-managed, 개인·비상업·Enterprise 확인, 민감정보·사람 승인, hash·서명·공증 검증이 명시되고 금지 문구는 0건이다 | 정적 검사 + 공식 문서 대조 | 구현 후 |
