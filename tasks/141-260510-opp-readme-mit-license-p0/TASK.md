# TASK: README 오픈소스 공개 P0 정비 — MIT LICENSE + 표시·실측 정정

> 작성일: 2026-05-10 | 작업 유형: 개선 | 적용 스킬: opp | 모드: semi-agentic
> 입력: 사용자 요청 (오픈소스 공개에 따른 README 최신화 + 신규 사용자 친화성 개선 — 본 태스크는 그중 P0 범위)
> 출력: TASK.md / PLAN.md / DONE.md + 실제 변경(LICENSE 신규, README 정정)

## 작업 목표

오픈소스 공개에 부합하도록 (a) MIT LICENSE 파일을 신규로 추가하고 README에 라이선스 표기·배지·섹션을 삽입하며, (b) README의 outdated/부정확 표기 6건(버전 예시·부트스트랩 형식·에이전트 카운트·community-skills 카운트·MCP 설치 메뉴 안내)을 실측 기반으로 정정한다.

## 배경

OPAL은 v0.3.16까지 진화하며 GitHub 공개 저장소(`ceo4ever/opal`)에 push됐고 캡틴이 이번 시리즈에서 install·doctor·MCP·Cursor 부트스트랩까지 안정화한 상태다. 다음 사용자가 진입하는 1차 표지 문서가 README이며, 동시에 라이선스 표기 부재는 오픈소스 공개의 법적 1순위 누락이다. 본 태스크는 알투의 README 검토 보고에서 도출된 P0 범위(7건)를 처리한다. P1(Quick Start, 3-way 모드 설명, opal-cli 표, mini-glossary, 트러블슈팅 강화)은 별도 후속 태스크로 분리한다.

## 배경 분석 (대화에서 도출)

알투가 `README.md` (773 줄), `docs/ARCHITECTURE.md`, `scripts/install.ps1`, `scripts/install/windows.ps1`, `community-skills/`, `agents/`, `opal/agents/`를 읽고 다음 사실관계를 확인했다.

| 항목 | 현 README 표기 | 실측 | 결론 |
|---|---|---|---|
| L96 OPAL_VERSION 예시 | `v0.1` | 현 latest = `v0.3.16` (15 버전 차) | **generic placeholder `<원하는-태그>` + GitHub Releases 링크 안내**(영구 정확·유지보수 0) |
| L103 부트스트랩 첫 줄 | `[부트스트랩] ✅ identity ✅ harness ✅ PM ⏳ registry ⏳ references ⏳ model-mapping` | `~/.opal/AGENT.md` Eager Step 6 보고 형식은 `… ✅ PM ✅ PM모드 ⏳ registry …` (PM모드 칼럼 추가) | 실제 출력 형식과 정합하도록 갱신 |
| L728 agents 카운트 | `서브에이전트 (전문 6종 + 범용 4종)` = 10종 | `opal/agents/*` 12개 + `agents/*` 1개(wtm) = **13개** | 13개 기준으로 분류 표기 재정리 (전문/범용 + 외부 1) |
| L729 community-skills 카운트 | `(31개)` | 조직 6개(`anthropics`, `getsentry`, `google-labs-code`, `openai`, `trailofbits`, `vercel-labs`) / SKILL.md = **30개** | "30개 (6개 조직 제공)" 형식으로 정정 |
| L772 MCP 트러블슈팅 | "설치 메뉴에서 [2] 또는 [3]을 선택했는지 확인" | 현 install(.sh / .ps1) 은 자동 등록 + 메뉴 없음 | 라인 삭제 (현행 자동 등록 안내로 대체) |
| 라이선스 | 미표기 | LICENSE 파일·README 라이선스 섹션·배지 모두 부재 | 이번 태스크에서 일괄 신규 |
| 배지 | 없음 | shields.io 표준 사용 가능 | License / Latest Release 2종 우선 |

**라이선스 결정**: MIT (캡틴 결정). AI 에이전트 프레임워크 카테고리(LangChain / LlamaIndex / AutoGen / CrewAI / AutoGPT 등)와 Anthropic 의존 생태계(Anthropic SDK / MCP / Claude Agent SDK)와 정합.

## 확정된 설계 방향 (대화에서 합의)

0. **community-skills 라이센스 / fetch 전환은 별도 태스크 142로 분리** — 캡틴 결정(2026-05-10): community-skills를 OPAL repo 번들에서 제거하고 vercel-labs/skills 표준(`skills.sh` / `npx skills`)을 통한 fetch 방식으로 전환한다. 이 결정에 따라 본 141 태스크는 임시 라이센스 정합(THIRD_PARTY_LICENSES.md)을 작성하지 않는다 — 142에서 번들 자체가 사라지면 라이센스 문제도 함께 해결되기 때문. R-7의 "30개 / 6개 조직" 카운트는 142 완료 시 다시 갱신될 예정이며, 142 태스크에 README 표기 갱신 작업이 포함된다.
1. **범위는 P0만** — 7건 정정 + LICENSE/README 라이선스 표기. P1·P2는 별도 후속 태스크로 분리한다.
2. **LICENSE 본문**: SPDX 표준 MIT License 본문, `Copyright (c) 2026 OPAL contributors`. 명시적 단일 저작권자 대신 "OPAL contributors" 사용 — 향후 컨트리뷰터 누적에 대비한 일반 관행.
3. **배지 2종 우선**: `License: MIT` (shields.io) + `Latest Release` (GitHub release/tag). 그 이상은 P2.
4. **README 라이선스 섹션은 하단**(`## License`)에 신설 — 한 단락 + LICENSE 파일 링크. 별도 페이지 분리 안 함.
5. **부트스트랩 첫 줄 갱신**: 현 `~/.opal/AGENT.md`의 Eager Step 6 출력 사양을 SSOT로 따른다 — `PM모드` 칼럼 포함 6 칼럼 형식.
6. **에이전트 카운트 표기**: ARCHITECTURE.md(L186) 표기 "10개"도 동시에 13개 기준으로 정합 갱신한다(부수 영향 — 같은 PR에 포함). 분류는 `docs/ARCHITECTURE.md §컴포넌트 유형 §에이전트` 의 분류와 동일하게 유지.
7. **MCP 트러블슈팅 라인 삭제**: 단순 삭제. 자동 등록은 [3/4] doctor 진단 + `claude mcp list` / `claude mcp get`으로 검증 가능하므로 별도 안내 문구 불필요.
8. **mac/Windows 정합 확인**: 라이선스/배지/표시 정정은 OS 무관. install 동작과 무관해 회귀 위험 없음.

## 요구사항

- [x] **R-1 LICENSE 신규**: 저장소 루트에 `LICENSE` 파일 생성. 무엇을: SPDX 표준 MIT License 본문 / 어디에: `LICENSE` (루트) / 왜: 오픈소스 공개의 법적 1순위 / AC: SPDX MIT 표준 텍스트 그대로 + `Copyright (c) 2026 OPAL contributors` 1행 / 추가 텍스트 없음
- [x] **R-2 README 배지 추가**: README 상단(타이틀 + 1줄 설명 사이 또는 직후)에 shields.io 배지 2종 추가. 무엇을: License (MIT) + Latest Release 배지 / 어디에: README 상단 / 왜: 오픈소스 공개 1차 표지 / AC: 두 배지가 올바른 SVG URL을 가리키며, License 배지 클릭 시 LICENSE 파일로 링크
- [x] **R-3 README License 섹션 신설**: README 하단에 `## License` 섹션 신설. 무엇을: MIT 명시 + LICENSE 링크 한 단락 / 어디에: README 트러블슈팅 다음 / 왜: 라이선스 명시 의무 / AC: 라이선스 명, 저작권 표기, LICENSE 파일 상대 링크 포함
- [x] **R-4 OPAL_VERSION 예시 generic 화 + Releases 링크 안내** (캡틴 통찰: 매 릴리즈 갱신 부담 회피 — 영구 정확): 무엇을: L96 `v0.1` → `<원하는-태그>` placeholder + 직후 1줄 안내(`최신 태그는 [GitHub Releases](https://github.com/ceo4ever/opal/releases)에서 확인할 수 있다`) / 어디에: README L96 부근 / 왜: 정적 latest 표기는 매 릴리즈마다 outdated → 유지보수 부담 / AC: (1) `OPAL_VERSION` 예시가 specific 버전이 아닌 placeholder 형식, (2) GitHub Releases 페이지 링크가 한 줄 안에 포함, (3) 향후 릴리즈에도 README 갱신 불필요한 형태
- [x] **R-5 부트스트랩 첫 줄 형식 정정**: L103 형식을 현 출력 사양과 일치시킴. 무엇을: `PM모드` 칼럼 포함 6 칼럼 형식으로 갱신 / 어디에: README L103 / 왜: 사용자가 보는 실제 출력과 다른 예시는 혼동 유발 / AC: Eager Step 6 출력 형식 SSOT(`~/.opal/AGENT.md`)와 칼럼 수·항목명·구분자 일치
- [x] **R-6 agents 카운트 정정**: L728 표기 갱신 + ARCHITECTURE.md(L186) 동기화. 무엇을: "전문 6 + 범용 4 = 10개" → 실제 13개 기준 분류로 / 어디에: README L728 + ARCHITECTURE.md L186 / 왜: 실측과 8개 차이 / AC: 카운트가 `opal/agents/*` + `agents/*` 합계와 일치, 분류는 ARCHITECTURE.md §컴포넌트 유형과 동일 표현
- [x] **R-7 community-skills 카운트 정정**: L729 "31개" → 실측. 무엇을: "30개 (6개 조직 제공)" 또는 동등 표기 / 어디에: README L729 / 왜: 실측과 1개 차이, 조직 단위 정보 추가 / AC: 카운트가 `find community-skills -maxdepth 3 -name SKILL.md` 결과와 일치, 6개 조직 명시
- [x] **R-8 MCP 트러블슈팅 outdated 삭제**: L772 안내 라인 삭제. 무엇을: "MCP 서버가 설치되어 있는지 확인한다: 설치 메뉴에서 `[2]` 또는 `[3]`을 선택했는지 확인" 라인 제거 / 어디에: README L772 / 왜: 현 install은 자동 등록, 메뉴 없음 (outdated) / AC: 해당 라인이 제거되고, 그 자리에 사용자가 검증할 수 있는 명령(`claude mcp list` / `opal-cli doctor`) 안내가 들어가거나 단순 삭제

## 제약 조건

- **변경이력 의무**: ARCHITECTURE.md 동기화 시 변경이력 형식 부재 — docs는 변경이력 의무 대상 아님(이전 v0.3.15에서 동일 케이스 진행). README도 변경이력 표 없음 — 본 태스크에서 추가 안 함.
- **부수 영향 최소화**: 본 태스크는 표시·정정 위주로 install/doctor/스킬 동작에 영향을 주지 않는다. 코드 파일은 변경하지 않는다.
- **mac/Windows OS 무관**: 모든 변경이 텍스트 문서. install 동작 영향 없음.
- **커밋은 사용자 승인 후**: 하네스 Guards — 명시적 지시 없이는 commit/push 안 함.
- **라이선스 본문은 SPDX 표준** — 직접 작성 금지, https://spdx.org/licenses/MIT.html 표준 텍스트 사용. 저작권자 1행만 채움.

## 기술 스택

- **문서**: Markdown (CommonMark)
- **라이선스**: SPDX-Identifier `MIT`
- **배지 서비스**: shields.io (외부, 변경 불요)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | README.md | `README.md` | 본 태스크의 1차 변경 대상 |
| D-2 | 소스 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | R-6 동기화 대상 (에이전트 카운트) |
| D-3 | 소스 | install.ps1 / windows.ps1 | `scripts/install.ps1` / `scripts/install/windows.ps1` | R-4 (현 latest 버전 검증) / R-8 (MCP 자동 등록 동작 확인) |
| D-4 | 외부 | SPDX MIT License | https://spdx.org/licenses/MIT.html | R-1 본문 SSOT |
| D-5 | 외부 | shields.io | https://shields.io | R-2 배지 URL 형식 SSOT |
| D-6 | 소스 | ~/.opal/AGENT.md | `opal/core/AGENT.md` Eager Step 6 | R-5 부트스트랩 출력 형식 SSOT |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §2 참조.
