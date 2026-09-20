---
template: sdlc-v2
---
# PLAN: Ego Lite 브라우저 우선 통합

> 입력: [TASK.md](TASK.md) — ANALYSIS 없음(Short profile). `code-scan scan`은 현행 E2E 어댑터·resolver·CLI를 `domain=opal-tools`, `layer=util`로 식별했고, 신규 `ego-browser-tool/main.py`의 기록 위치는 `inline`으로 판정했다.

## References

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|---|---|---|---|
| D-1 | 소스 | 현행 E2E 어댑터 | `opal/tools/test-tool/lib/e2e_adapter.py:1` | cmux 단일 실행과 공통 verdict 소비 경계 |
| D-2 | 소스 | test-tool resolver | `opal/tools/test-tool/lib/resolver.py:91` | 추론 폴백의 E2E 후보 선언 |
| D-3 | 설계 | 테스트 도구 템플릿 | `opal/templates/test-tools.yaml` | 글로벌 E2E 후보 순서 SSOT |
| D-4 | 설계 | Web-to-Markdown | `skills/web-to-markdown/SKILL.md:90` | 현행 cmux→Playwright 실행 흐름 |
| D-5 | 설계 | 커뮤니티 스킬 관리자 | `opal/skills/opal-skill-manager/SKILL.md` §2 스킬 설치 | clone-copy·보안 스캔·user registry 계약 |
| D-6 | 설계 | OPAL 보안 모델 | `docs/SECURITY.md` §2, §4 | 다운로드 무결성과 외부 스킬 공급망 기준 |
| D-7 | 설계 | OPAL 컨벤션 | `docs/CONVENTIONS.md` §배포 경계, §플랫폼 분기 격리 | source→installed 및 어댑터 경계 |
| D-8 | 외부 | Ego Lite Quick Start | [공식 Quick Start](https://lite.ego.app/document/en/docs/quick-start) | macOS 설치·온보딩·로그인 상태 재사용 |
| D-9 | 외부 | Ego Lite E2E | [공식 자동화 테스트 안내](https://lite.ego.app/solutions/automated-test-automation) | 별도 Space·expected/actual·사람 인계 기준 |
| D-10 | 외부 | ego-browser skill | [citrolabs/ego-lite](https://github.com/citrolabs/ego-lite/tree/main/skills/ego-browser) | TaskSpace/Page API와 설치 스킬 원본 |
| D-11 | 외부 | Ego Lite Privacy | [공식 Privacy Policy](https://lite.ego.app/privacy) | 인증 세션·페이지 데이터·분석 데이터 경계 |
| D-12 | 외부 | Ego Lite Terms | [공식 Terms](https://lite.ego.app/terms) | 개인·비상업 계정 사용 범위 |

## Approach

Ego Lite 앱과 공식 스킬을 OPAL에 번들하지 않고 선택 설치 공급자로 둔다. 새 `ego-browser-tool`이 설치 상태, 검증된 앱 설치, 무해한 브라우저 assertion 실행을 단일 JSON 계약으로 감싸며, `test-tool`은 설정에 선언된 후보를 우선순위대로 순회한다. 공개 정보 검색은 이 체인에 넣지 않고 기존 웹 검색을 유지한다. 브라우저 콘텐츠 추출과 UI/E2E만 Ego Lite를 먼저 사용하고, 미설치이면 사용자 선택을 기다린다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| D-1. 작업 유형 분리 | 공개 정보 검색은 기존 웹 검색을 사용한다. 인증된 페이지, 동적 렌더링, UI 조작, 브라우저 E2E만 Ego Lite 후보 체인을 사용한다. | 공식 E2E 안내도 Ego Lite를 browser layer의 추가 신호로 두고 결정론적 CI suite를 병행하라고 명시한다 (→ D-9). TASK C-1·AC-2의 소유자 결정이다. |
| D-2. 공급자 순서 | `ego-lite(priority=1) → cmux(priority=2) → playwright(priority=3)`를 글로벌 템플릿과 resolver 추론값에 동일하게 선언하고, 어댑터는 이 목록을 priority로 정렬해 실제 실행한다. | 현행은 D-3에 두 후보를 선언하지만 D-1은 cmux만 인식한다. 선언과 실행을 같은 후보 목록으로 수렴해야 AC-1이 기계적으로 성립한다. |
| D-3. 대체 허용 상태 | 후보 결과가 내부 상태 `provider_unavailable`일 때만 다음 후보를 실행한다. `fail`, `infra_error`, `blocked`, `awaiting_human`은 즉시 최종 결과로 반환하며, 모든 후보가 없을 때만 `executor_unavailable`로 닫는다. | [MUST] `opal/tools/test-tool/lib/e2e_adapter.py:17`: "provider_unavailable일 때만 다음 Browser 후보 전환을 허용한다." |
| D-4. 미설치 핸드오프 | Ego CLI가 없으면 `awaiting_human` JSON에 `manual`, `r2`, `cancel` 세 선택과 원래 URL·assertion·resume 인자를 담는다. `manual`은 공식 설치 URL과 온보딩 안내, `r2`는 검증 설치 후 GUI 온보딩 안내, `cancel`은 Ego 후보만 `provider_unavailable`로 끝내 다음 후보를 허용한다. | 공식 설치는 앱 설치 후 사람이 GUI 온보딩을 완료해야 하고 CLI는 보통 `~/.local/bin`에 등록된다 (→ D-8, D-10). 원래 작업 재개는 TASK C-2·AC-3의 소유자 결정이다. |
| D-5. 안전 설치 | `ego-browser-tool install`은 macOS arm64/x86_64만 지원한다. 버전 `0.4.5.9`의 아키텍처별 CDN URL과 SHA-256을 소스 manifest에 고정하고, `hdiutil verify`→SHA-256→`codesign --verify --deep --strict`→`spctl --assess`를 모두 통과한 앱만 설치한다. quarantine 제거는 하지 않는다. arm64 hash는 `b83157810a11159ea118b310e9d62475b384d3a7548d5eaf990c426a0d7ab1b0`, x86_64 hash는 `78862c9a3cb71b0da361ca4e9e44bf5440d8b3bdd95c89eccaaf2a4ed16b4bc0`이다. | [MUST] `docs/SECURITY.md:34`: "SHA-256 검증 통과 → 설치 계속". 두 DMG는 2026-09-14 실측에서 image verify·코드서명·Gatekeeper 평가를 통과했다. 업스트림 설치 스크립트의 quarantine 제거는 이 기준보다 약해 재사용하지 않는다. |
| D-6. 앱 배포 경계 | OPAL release와 install은 Ego Lite 앱을 내려받거나 자동 설치하지 않는다. `ego-browser-tool`만 배포하고 사용자가 `r2`를 선택한 호출에서만 앱을 설치한다. Ego Lite 계정은 개인·비상업 단일 사용자 범위로 안내한다. | 공식 약관은 계정을 단일 사용자의 개인·비상업 용도로 규정한다 (→ D-12). 앱 번들은 TASK 범위에서도 제외됐다. |
| D-7. 브라우저 assertion | `test-tool integration`은 선택 입력 `--expect-text`를 받아 각 공급자가 관찰한 페이지 문자열과 비교한다. expected/actual 증거가 있으면 공통 E2E verdict를 만들고, assertion 없는 단순 open/navigate는 기존처럼 pass로 만들지 않는다. | 현행 테스트는 open→navigate→close만으로 pass가 될 수 없음을 고정한다 (`opal/tools/test-tool/tests/test_test_tool.py:791`). 공식 테스트 보고도 expected versus actual을 요구한다 (→ D-9). |
| D-8. Ego 실행 격리 | `ego-browser-tool smoke`는 goal당 TaskSpace 하나와 기본 Page `p1`을 사용하고, sentinel JSON만 OPAL 결과로 파싱한다. 성공 시 `finish({keep: []})`, 사람 인계나 오류 시 Space를 임의로 새로 만들거나 우회하지 않는다. | 공식 스킬은 goal당 TaskSpace 하나, 같은 Space 재개, 기본 종료 시 `finish({keep: []})`를 요구한다 (→ D-10). |
| D-9. 민감 정보·부작용 | wrapper는 비밀번호·cookie·token 추출 기능을 제공하지 않는다. 인증·MFA·결제·게시·삭제·설정 변경은 `blocked` 또는 `awaiting_human`으로 반환해 사람에게 넘긴다. | Privacy Policy는 인터페이스가 저장 비밀번호·인증 cookie·session token을 export하지 못하지만 인증된 페이지 내용에는 개인정보가 있을 수 있다고 밝힌다 (→ D-11). 공식 E2E 안내도 MFA·결제·파괴 행동을 사람 판단으로 둔다 (→ D-9). |
| D-10. 공식 커뮤니티 스킬 | 프레임워크 카탈로그에 `citrolabs/ego-browser`, `source_repo=citrolabs/ego-lite@skills/ego-browser`, MIT, commit `d01be93325c7ea59d41c2ca9f4c59b58b4be4046`을 등록한다. 실행 시 OPAL clone-copy와 Codex skill-installer를 각각 사용한다. | 2026-09-14 shallow clone 실측에서 version 2.0.0, commit 날짜 2026-09-10, MIT, `scan-risk` SAFE·active hit 0건을 확인했다. [MUST] `docs/SECURITY.md:110-112`는 registry v2.1의 검증 가능한 스킬에 commit SHA를 허용한다. |
| D-11. 플랫폼 격리 | 운영체제·아키텍처 감지는 `ego-browser-tool` 내부에만 둔다. test-tool·스킬·에이전트는 `provider_unavailable`/handoff JSON만 소비한다. | [MUST] `docs/CONVENTIONS.md:262-263`: 플랫폼별 차이는 어댑터 계층에서만 흡수하고 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다. |
| D-12. 배포 정합성 | 프로젝트 소스 변경 후 `scripts/install-mac.sh`로 `~/.opal`에 재배포하고 source/installed의 tool·template·registry·skill/agent 문안을 비교한다. 사용자 설치 스킬과 user registry는 install이 보존한다. | [MUST] `docs/CONVENTIONS.md:254-257`: 프로젝트 소스에서 변경하고 install로 배포하며 사용자 커뮤니티 스킬 영역은 불가침이다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. Ego 공급자·안전 설치 어댑터 | PM | `opal/tools/ego-browser-tool/main.py`, `opal/tools/ego-browser-tool/run.sh`, `opal/tools/ego-browser-tool/installer-manifest.json`, `opal/tools/ego-browser-tool/README.md`, `opal/tools/ego-browser-tool/tests/test_ego_browser_tool.py` | D-4~D-9의 `status`, `install`, `smoke` JSON 계약을 구현한다. manifest hash 검증, 서명·공증 실패 차단, app 미설치/CLI 미등록/GUI 온보딩을 구분하고, 테스트는 임시 DMG·명령 스텁으로 실제 외부 설치 없이 모든 분기를 검증한다. 신규 Python @header는 `module=ego_browser_tool`, `layer=util`, `domain=opal-tools`로 기록한다. | 없음 | P1 | AC-3, AC-4, AC-5, AC-9, C-2, C-4, C-5, C-6 |
| W-2. test-tool 다중 공급자 실행 | PM | `opal/tools/test-tool/lib/e2e_adapter.py`, `opal/tools/test-tool/lib/resolver.py`, `opal/tools/test-tool/test_tool.py`, `opal/tools/test-tool/tests/test_test_tool.py`, `opal/tools/test-tool/README.md`, `opal/templates/test-tools.yaml` | config 후보를 priority 순회하고 Ego→cmux→Playwright를 실제 호출한다. `--expect-text`와 `--ego-install-choice`를 CLI에 추가하고 expected/actual verdict, handoff 보존, provider_unavailable 전용 전환, 후보 소진을 검증한다. 기존 cmux 테스트 fixture와 resolver 추론값을 3순위 계약으로 갱신한다. | W-1 | P2 | AC-1, AC-3, AC-5, AC-6, AC-9, AC-10, C-2, C-3, C-4 |
| W-3. 브라우저 작업 지침 수렴 | PM | `skills/web-to-markdown/SKILL.md`, `opal/agents/opal-wtm-agent/AGENT.md`, `opal/core/references/agents.md` | 공개 검색은 기존 검색에 남기고, URL 추출·동적·인증·상호작용은 ego-browser-tool의 handoff 계약을 소비하도록 현행 2단 체인을 3단 체인으로 바꾼다. 미설치는 silent skip하지 않고 선택을 요청하며, cancel 뒤에만 cmux→Playwright를 사용한다. 민감정보와 사람 인계 규칙을 같은 문안으로 맞춘다. | W-1 | P2 | AC-2, AC-3, AC-6, AC-8, AC-10, C-1, C-2, C-3, C-6 |
| W-4. 커뮤니티 스킬 카탈로그·현재 환경 설치 | PM | `opal/core/references/community-skills-registry.json`, 런타임 `~/.opal/community-skills/citrolabs/ego-browser/`, `~/.opal/community-skills/user-registry.json`, `~/.codex/skills/ego-browser/` | D-10 항목을 소스 카탈로그에 추가한다. skill-manager의 migrate→clone→scan-risk→clone-copy→user registry 절차로 OPAL에 설치하고, 시스템 skill-installer helper로 Codex에도 같은 subdir을 설치한다. 설치 결과의 commit·license·trust를 조회해 증거화한다. | 없음 | P2 | AC-7, C-5, C-7 |
| W-5. 탐지·문서·배포 연결 | PM | `opal/tools/tool-scan/manifest.json`, `opal/core/references/tools.md`, `docs/PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/CONVENTIONS.md`, `docs/SECURITY.md`, `scripts/install-mac.sh` | ego-browser-tool을 도구 탐지·사용법·아키텍처·보안 기준에 등록하고 도구 수와 WTM 설명을 갱신한다. install-mac이 새 run.sh 실행 권한을 설정하도록 한 뒤 전체 install을 실행해 배포본 정합성을 확인한다. 수기 변경이력 행은 추가하지 않는다. | W-1, W-2, W-3, W-4 | P3 | AC-1, AC-4, AC-7, AC-8, AC-10, C-5, C-7 |
| W-6. 실제 앱 설치·브라우저 smoke | PM | 런타임 `/Applications/ego lite.app` 또는 `~/Applications/ego lite.app`, Ego Lite GUI, 태스크 증거 파일 | 캡틴이 이미 요청한 R2 설치 경로로 W-1의 검증 installer를 실행한다. GUI 온보딩은 `awaiting_human`으로 멈추고 완료 확인 후 CLI readiness를 검증한다. `https://example.com`에서 `Example Domain` assertion 1건을 별도 Space로 실행해 expected/actual 증거를 저장한다. | W-1, W-2, W-4, W-5 | P4 | AC-4, AC-7, AC-9, C-2, C-5, C-6 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 공식 CDN URL이 같은 경로에서 새 DMG로 바뀐다 | 고정 hash와 다운로드가 불일치 | 자동 설치가 중단된다 | hash 불일치는 `artifact_hash_mismatch`로 차단하고 기존 앱을 덮어쓰지 않는다. 새 버전 채택은 manifest와 실측 증거를 함께 갱신하는 별도 변경으로만 허용한다. |
| H-2. 앱 설치 후 GUI 온보딩 전까지 CLI가 없다 | 설치 완료를 실행 가능으로 오판 | 원래 E2E 재개 실패 | 앱 존재와 CLI readiness를 분리하고 install 결과를 `awaiting_human`으로 반환한다. 캡틴 확인 뒤 `status`와 최소 nodejs 출력을 재검증한다. |
| H-3. Ego CLI의 로그 형식이 바뀐다 | wrapper JSON 파싱 실패 | `infra_error` 또는 거짓 pass 위험 | JS가 고유 sentinel JSON을 마지막에 출력하고 wrapper는 sentinel만 파싱한다. sentinel 부재·중복·비정상 종료는 `infra_error`로 닫는다. |
| H-4. 공급자 목록만 바뀌고 실제 후보 전환이 다시 누락된다 | 선언/실행 불일치 재발 | Ego·Playwright가 이름만 등록된다 | W-2 테스트가 각 공급자 호출 로그와 priority 순서, Ego unavailable→cmux, Ego+cmux unavailable→Playwright를 공개 CLI에서 검증한다. |
| H-5. Ego 미설치에서 자동 fallback하면 사용자의 설치 선택이 사라진다 | TASK C-2 위반 | Ego가 계속 1급으로 채택되지 않는다 | 최초 미설치는 `awaiting_human`으로 멈추고 명시적 `cancel`만 provider_unavailable을 만든다. 테스트로 silent fallback 0건을 확인한다. |
| H-6. 인증된 브라우저 데이터가 테스트 증거에 과다 노출된다 | 개인정보·기밀 유출 | 사용자·조직 보안 위험 | wrapper는 assertion 일치 여부와 제한된 actual만 반환하고 전체 페이지·cookie·token은 저장하지 않는다. 실제 smoke는 공개 example.com만 사용한다. |
| H-7. 개인·비상업 약관과 조직 배포가 충돌한다 | 라이선스·운영 리스크 | OPAL 사용자에게 부적절한 기본 강제 | 앱은 optional user-managed provider로만 두고 OPAL 배포에서 앱을 설치하지 않는다. 문서에 조직/상업 사용 전 Citro Enterprise 조건 확인을 명시한다. |
| H-8. 현재 환경에서 앱 GUI 온보딩을 완료할 수 없다 | 실제 E2E 증거 미확보 | AC-9 차단 | 코드·mock 회귀 검증은 완료하되 실제 smoke는 `awaiting_human`으로 정확히 보고하고 캡틴 온보딩 뒤 같은 태스크에서 재개한다. 다른 공급자의 성공으로 대체하지 않는다. |

## Release and recovery

- 적용 순서: P1에서 안전 adapter를 만들고, P2에서 test-tool·브라우저 지침·두 커뮤니티 스킬 설치를 병행한 뒤, P3에서 탐지·문서·install을 수렴한다. P4는 검증된 앱 설치→GUI 온보딩→같은 요청의 실제 smoke 순서다.
- 검증 범위: 신규 tool 단위 테스트, test-tool 공개 CLI 회귀, skill-registry validate/match/list, 문서 라우팅 정적 검사, code-scan validate, 전체 관련 Python test, source→installed 비교를 수행한다. 실제 연동은 공개 `example.com` 한 건만 실행하고 expected/actual·Space id를 증거로 남긴다.
- 실측 경계: DMG 관측은 2026-09-14 macOS arm64/x86_64 공식 URL의 version 0.4.5.9에 한정한다. 앱 다운로드·검증 시간과 GUI에서 캡틴이 온보딩하는 대기 시간은 분리한다. actual 페이지 증거는 필요한 문자열 주변으로 제한한다.
- 실패 시: source 단계 실패는 변경 파일만 되돌려 installed 영역을 건드리지 않는다. install 전 실패는 기존 앱을 보존하고 임시 mount를 해제한다. 새 앱 복사 후 CLI readiness가 실패하면 앱은 삭제하지 않고 `awaiting_human`으로 남긴다. OPAL install 실패는 source를 보존하고 배포본 불일치를 보고한다. 커뮤니티 스킬 설치 실패는 기존 같은 vendor 경로를 덮어쓰지 않고 임시 clone을 보존하지 않는다.
