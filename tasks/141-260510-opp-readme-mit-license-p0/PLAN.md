# PLAN: README 오픈소스 공개 P0 정비 — MIT LICENSE + 표시·실측 정정

> 작성일: 2026-05-10
> 입력: `tasks/141-260510-opp-readme-mit-license-p0/TASK.md`
> 출력: `tasks/141-260510-opp-readme-mit-license-p0/PLAN.md`

## 1. 현황 조사

### 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | README.md | `README.md` | 본 태스크의 1차 변경 대상 (R-2~R-8) |
| D-2 | 소스 | ARCHITECTURE.md | `docs/ARCHITECTURE.md` | R-6 동기화 대상 (L186 배포 모델 다이어그램의 `opal/agents/* (10개)` + §컴포넌트 유형 §에이전트 분류 정합) |
| D-3 | 소스 | install.sh / install.ps1 | `scripts/install.sh` / `scripts/install.ps1` | R-4 (OPAL_VERSION 자동 latest 폴백 동작 검증) / R-8 (MCP 자동 등록 — 메뉴 없음 검증) |
| D-4 | 외부 | SPDX MIT License | [SPDX MIT License](https://spdx.org/licenses/MIT.html) | R-1 LICENSE 본문 SSOT |
| D-5 | 외부 | shields.io | [shields.io](https://shields.io) | R-2 배지 URL 형식 SSOT |
| D-6 | 소스 | ~/.opal/AGENT.md (Eager Step 6) | `opal/core/AGENT.md` | R-5 부트스트랩 첫 줄 출력 형식 SSOT (실측: `[부트스트랩] ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ⏳ references ⏳ model-mapping`) |
| D-7 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md` | 문서 컨벤션 (한국어 본문 + 영어 코드, 변경이력 의무 — docs는 면제) |
| D-8 | 설계 | PROJECT.md | `docs/PROJECT.md` | 영역(문서) 결정 + 전문 에이전트(`opal-task-agent` 폴백) 매핑 |
| D-9 | 외부 | GitHub Releases | [ceo4ever/opal Releases](https://github.com/ceo4ever/opal/releases) | R-4 안내 링크 대상 |
| D-10 | 외부 | shields.io License 배지 (예시) | https://img.shields.io/badge/License-MIT-yellow.svg | R-2 License 배지 URL 형태 |
| D-11 | 외부 | shields.io GitHub Release 배지 (예시) | https://img.shields.io/github/v/release/ceo4ever/opal | R-2 Latest Release 배지 URL 형태 (동적) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1 참조. 유형: `기획` / `설계` / `소스` / `외부`.

#### 컨벤션 인용 (CONVENTIONS.md §구현 규칙 발췌)

- [MUST] `docs/CONVENTIONS.md` §언어 규칙: "문서 본문 = 한국어 (기술 용어는 영어 병기)" — 본 태스크 모든 산출물 본문이 한국어임을 보장.
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 §Guards: "사용자가 명시적으로 '승인', '진행해', '구현해' 등의 실행 허가를 내리기 전까지 코드를 작성하거나 파일을 생성·수정하지 않는다." — PLAN.md 산출물 작성만 허용, EXECUTE 단계는 별도 승인 필요.
- [MUST] `docs/CONVENTIONS.md` §구현 규칙 §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다." — README.md / ARCHITECTURE.md / LICENSE는 docs 카테고리이므로 변경이력 의무 **면제** (TASK.md §제약 조건 "docs는 변경이력 의무 대상 아님" 확인 + L186 동일 케이스 v0.3.15 선례 확인). 본 태스크에서 변경이력 행 추가 안 함.
- [MUST] `docs/CONVENTIONS.md` §커밋 규칙: "커밋은 캡틴이 명시적으로 요청할 때만 수행" — EXECUTE 후 자동 커밋 금지.

### 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `LICENSE` (루트) | MIT 라이선스 본문 | **신규** (R-1) | 부재 (실측 `ls LICENSE` → No such file) |
| `README.md` | 프레임워크 공개 소개 문서 | **수정** (R-2~R-8 6건) | `README.md:1`, `:96`, `:103`, `:728`, `:729`, `:772` |
| `docs/ARCHITECTURE.md` | 시스템 아키텍처 (배포 모델 다이어그램 + §컴포넌트 유형 §에이전트) | **수정** (R-6 동기화) | `docs/ARCHITECTURE.md:186` (배포 모델 `opal/agents/* (10개)`) + `:129-152` (§에이전트 11개 명시) |

> 근거: `파일:N-M` 포맷. citation-rules.md §2.2.

### 현재 상태

- **LICENSE**: 저장소 루트에 LICENSE 파일 부재 → 오픈소스 공개 법적 1순위 누락 (D-1, 실측 `ls`).
- **README L1~5 (헤더)**: 타이틀 + 1줄 설명 + 구분선만 존재 → 배지 영역 부재 (D-1 `README.md:1-5`).
- **README L96 (OPAL_VERSION 예시)**: `OPAL_VERSION=v0.1` 하드코딩 — 실제 install.sh는 OPAL_VERSION 미설정 시 latest release tag 자동 조회 + `main` 폴백 동작 (D-3 `scripts/install.sh:50-67`). v0.1은 15 버전 outdated.
- **README L103 (부트스트랩 첫 줄)**: 6 칼럼 (`identity / harness / PM / registry / references / model-mapping`) — `~/.opal/AGENT.md` Eager Step 6 SSOT는 7 칼럼 (`identity / harness / PM / PM모드 / registry / references / model-mapping`)으로 `PM모드` 추가됨 (D-6 L53).
- **README L728 (agents 카운트)**: `서브에이전트 (전문 6종 + 범용 4종)` = 10종 표기 — 디렉토리 실측 `opal/agents/*` 12개 + `agents/*` 1개(wtm) = **13개** 차이.
- **README L729 (community-skills 카운트)**: `(31개)` — 실측 `find community-skills -maxdepth 3 -name SKILL.md` = **30개** / 6개 조직(anthropics, getsentry, google-labs-code, openai, trailofbits, vercel-labs).
- **README L772 (MCP 트러블슈팅)**: "설치 메뉴에서 [2] 또는 [3]을 선택했는지 확인" — 현 `install.sh` / `install.ps1`은 **자동 등록**(메뉴 없음). outdated.
- **README 하단 (License 섹션)**: 부재 (실측 `grep "## License"` → no match).
- **ARCHITECTURE.md L186 (배포 모델 다이어그램)**: `opal/agents/* (10개)` — 실측 12개 차이 (D-2).
- **ARCHITECTURE.md L129-152 (§컴포넌트 유형 §에이전트)**: 범용 5 + 전문 6 = **11개 명시** — 실측 13개와 2개 차이. 누락된 2개는 `opal-security-checker`, `opal-convention-checker` (PROJECT.md §주요 컴포넌트 GC 파이프라인에 별도 등재되어 있으나 ARCHITECTURE.md §에이전트 카테고리에는 미반영).

### 영향 범위

- **신규 파일 1건**: `LICENSE` (루트) — 다른 파일 영향 없음. install 스크립트는 이 파일을 패키징/배포하지 않음 (확인 — 별도 영향 없음).
- **README.md 6 위치 수정**: L1~5(배지 추가) / L96(예시 갱신) / L103(부트스트랩 첫 줄) / L728(agents 카운트) / L729(community-skills 카운트) / L772(MCP 트러블슈팅 라인 삭제) + 하단 `## License` 섹션 신설. 모두 표시·정정 위주, install/doctor/스킬 동작에 영향 없음.
- **ARCHITECTURE.md 1~2 위치 수정**: L186(배포 모델) + L129-152(§에이전트 분류) — README L728의 분류 표현과 동일하게 유지하기 위해 양쪽 동시 갱신.
- **install/doctor/스킬 동작**: 영향 없음 (텍스트 문서 변경만).
- **mac/Windows OS 분기**: 영향 없음 (모두 OS 무관 마크다운).
- **변경이력**: docs 카테고리는 변경이력 의무 면제 (L186 v0.3.15 선례) → 본 태스크에서 변경이력 행 추가 안 함.

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N-1 | `LICENSE` | SPDX MIT License 본문 + `Copyright (c) 2026 OPAL contributors` | TASK.md R-1 / [MUST] D-4 SPDX 표준 텍스트 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M-1 | `README.md` (L1~5 부근) | shields.io 배지 2종 (License: MIT + Latest Release) 헤더 직후 삽입 | TASK.md R-2 / D-5, D-10, D-11 |
| M-2 | `README.md` L96 | `OPAL_VERSION=v0.1` → `OPAL_VERSION=<원하는-태그>` placeholder + GitHub Releases 안내 1줄 | TASK.md R-4 / D-3 (install.sh latest 폴백) / D-9 |
| M-3 | `README.md` L103 | 부트스트랩 첫 줄을 7 칼럼 형식으로 정정 (`PM모드` 추가) | TASK.md R-5 / [MUST] D-6 L53 |
| M-4 | `README.md` L728 | `(전문 6종 + 범용 4종)` → 13개 기준 분류 (전문 6 + 범용 + GC 체커 2 + wtm) | TASK.md R-6 / 디렉토리 실측 |
| M-5 | `README.md` L729 | `(31개)` → `(30개 — 6개 조직 제공)` | TASK.md R-7 / 실측 |
| M-6 | `README.md` L772 | MCP 트러블슈팅 라인 삭제 (`claude mcp list` / `opal-cli doctor`로 안내 대체 — 단순 삭제 + 검증 명령 안내 1줄) | TASK.md R-8 / D-3 (자동 등록) |
| M-7 | `README.md` (트러블슈팅 다음) | `## License` 섹션 신설 — MIT 명시 + LICENSE 파일 상대 링크 한 단락 | TASK.md R-3 |
| M-8 | `docs/ARCHITECTURE.md` L186 | 배포 모델 다이어그램의 `opal/agents/* (10개)` → `opal/agents/* (12개)` (`agents/* (범용 1개)` 라인은 wtm-agent 그대로 유지 — 합계 13개) | TASK.md R-6 / 실측 |
| M-9 | `docs/ARCHITECTURE.md` §컴포넌트 유형 §에이전트 (L133-141) | 범용 에이전트 표에 `opal-security-checker`, `opal-convention-checker` 2행 추가 (모델/역할 PROJECT.md GC 파이프라인 표 인용) → 범용 5 → 7 → 합계 13 | TASK.md R-6 분류 정합 / D-2 / 리스크 R-T1 대응 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| (없음 — M-6은 라인 삭제이지만 README 파일 자체는 유지) | - | - |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | LICENSE 신규 작성 (SPDX 표준 텍스트) | `LICENSE` | 낮음 |
| 2 | ARCHITECTURE.md §에이전트 표 보강 (security/convention checker 2행 추가) | `docs/ARCHITECTURE.md:133-141` | 낮음 |
| 3 | ARCHITECTURE.md L186 배포 모델 카운트 정정 (10 → 12) | `docs/ARCHITECTURE.md:186` | 낮음 |
| 4 | README L728 agents 카운트 정정 (R-6 — ARCHITECTURE.md 정합 후) | `README.md:728` | 낮음 |
| 5 | README L1~5 배지 2종 삽입 (R-2 — LICENSE 신규 후) | `README.md:1-5` | 낮음 |
| 6 | README L96 OPAL_VERSION 예시 generic 화 (R-4) | `README.md:96` | 낮음 |
| 7 | README L103 부트스트랩 첫 줄 7 칼럼 정정 (R-5) | `README.md:103` | 낮음 |
| 8 | README L729 community-skills 카운트 정정 (R-7) | `README.md:729` | 낮음 |
| 9 | README L772 MCP 트러블슈팅 라인 삭제 + 검증 명령 안내 (R-8) | `README.md:772` | 낮음 |
| 10 | README 하단 `## License` 섹션 신설 (R-3 — LICENSE 신규 후) | `README.md` (트러블슈팅 다음) | 낮음 |

**의존성 원칙**: 의존 받는 쪽(LICENSE, ARCHITECTURE.md §에이전트 표) 먼저 → 그것을 참조하는 쪽(README 배지·License 섹션·agents 카운트) 나중.

### 핵심 설계

#### N-1. `LICENSE` (신규)

**구조**: SPDX MIT License 표준 텍스트 (1행 저작권 + 본문 22행 + 끝). 추가 텍스트 금지.

**필수 내용**:

```
MIT License

Copyright (c) 2026 OPAL contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

**근거**: [MUST] [SPDX MIT License](https://spdx.org/licenses/MIT.html): 저작권자 라인을 제외한 본문은 SPDX 표준 텍스트 그대로 — 직접 작성·번역·요약 금지 (→ D-4). TASK.md §제약 조건 "라이선스 본문은 SPDX 표준" + R-1 AC "추가 텍스트 없음".

**선택 결정**:
- 저작권자 표기 = `OPAL contributors` (단일 저작권자 대신 일반 관행 — TASK.md §확정된 설계 방향 §2).
- 연도 = `2026` (현재 일자 SSOT — 캡틴 환경 컨텍스트 `currentDate: 2026-05-10`).

#### M-1. `README.md` (배지 2종 — R-2)

**위치**: 헤더 블록 (L1~5) 직후, 첫 `---` 구분선 전에 한 줄 삽입.

**삽입할 라인 형태** (Markdown):

```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Latest Release](https://img.shields.io/github/v/release/ceo4ever/opal)](https://github.com/ceo4ever/opal/releases)
```

**근거**: TASK.md R-2 AC "두 배지가 올바른 SVG URL을 가리키며, License 배지 클릭 시 LICENSE 파일로 링크" / D-5 shields.io / D-10 / D-11. License 배지 = static `License-MIT-yellow.svg` (yellow는 shields.io MIT 표준 색상), Latest Release 배지 = dynamic `github/v/release/{owner}/{repo}` 엔드포인트 (매 릴리즈 자동 갱신 — TASK.md §배경 분석 "동적").

**디자인 결정**: 두 배지를 같은 줄에 공백 구분 배치 (전형적 shields.io 패턴). 추가 배지(CI/Tests/Build)는 P2로 후속 태스크에 분리 (TASK.md §확정된 설계 방향 §3).

#### M-2. `README.md` L96 (R-4 — OPAL_VERSION generic 화)

**기존 (L96)**:

```markdown
> 특정 버전 고정: `OPAL_VERSION=v0.1` 환경변수 사용 (mac/linux) 또는 `$env:OPAL_VERSION = 'v0.1'` (Windows).
```

**변경 후**:

```markdown
> 특정 버전 고정: `OPAL_VERSION=<원하는-태그>` 환경변수 사용 (mac/linux) 또는 `$env:OPAL_VERSION = '<원하는-태그>'` (Windows). 최신 태그는 [GitHub Releases](https://github.com/ceo4ever/opal/releases)에서 확인할 수 있다.
```

**근거**: TASK.md R-4 AC 3종 (placeholder / Releases 링크 / 향후 릴리즈에 README 갱신 불필요) 모두 충족 / D-3 `scripts/install.sh:50-67` (OPAL_VERSION 미설정 시 latest release 자동 폴백) / D-9 GitHub Releases.

#### M-3. `README.md` L103 (R-5 — 부트스트랩 첫 줄)

**기존 (L103)**:

```
[부트스트랩] ✅ identity ✅ harness ✅ PM ⏳ registry ⏳ references ⏳ model-mapping
```

**변경 후**:

```
[부트스트랩] ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ⏳ references ⏳ model-mapping
```

**근거**: [MUST] `~/.opal/AGENT.md:53` (Eager Step 6 SSOT): 정확히 7 칼럼 — `identity / harness / PM / PM모드 / registry / references / model-mapping` (→ D-6).

**검증**: `~/.opal/AGENT.md` Step 6.5 ~ Step 7 (line 19~23)에 `PM모드` 칼럼 의미 정의 — `.opal/AGENT.md` 존재 시 ✅ PM, 미존재 시 ⬜ 비서. README 예시는 PM 모드 진입 케이스(✅) 사용.

#### M-4. `README.md` L728 (R-6 — agents 카운트 13개)

**기존**:

```
│  agents/        서브에이전트 (전문 6종 + 범용 4종)       │
```

**변경 후 (디렉토리 실측 기반 13개)**:

```
│  agents/        서브에이전트 (전문 6 + 범용 5 + GC 2)    │
```

**분류 근거**:
- 전문 6 = `opal-plan / opal-fe / opal-be / opal-db / opal-planning / opal-test` (→ D-2 ARCHITECTURE.md L143-152)
- 범용 5 = `opal-task / opal-task-qa / opal-task-action / opal-sdd-action / wtm` (→ D-2 ARCHITECTURE.md L133-141)
- GC 2 = `opal-security-checker / opal-convention-checker` (→ D-8 PROJECT.md §주요 컴포넌트(GC 파이프라인))
- 합계 6+5+2 = 13개 ← 디렉토리 실측 (`opal/agents/*` 12 + `agents/*` 1) 일치

**박스 폭 정합**: 박스 라인은 60자 폭 박스 — 변경 후 라인이 폭을 초과하지 않도록 공백 패딩으로 맞춘다 (EXECUTE 시 알투가 박스 정렬 검증).

**근거**: TASK.md R-6 AC "카운트가 `opal/agents/*` + `agents/*` 합계와 일치, 분류는 ARCHITECTURE.md §컴포넌트 유형과 동일 표현" + 본 PLAN M-9에서 ARCHITECTURE.md를 13개 기준으로 사전 갱신하여 정합 보장.

#### M-5. `README.md` L729 (R-7 — community-skills 카운트)

**기존**:

```
│  community-skills/  외부 조직 제공 스킬 (31개)           │
```

**변경 후**:

```
│  community-skills/  외부 조직 제공 스킬 (30개 / 6개 조직) │
```

**근거**: TASK.md R-7 AC "카운트가 `find community-skills -maxdepth 3 -name SKILL.md` 결과와 일치, 6개 조직 명시" / 실측 30개 / 6개 조직(anthropics, getsentry, google-labs-code, openai, trailofbits, vercel-labs).

**미래 영향 메모 (TASK.md §확정된 설계 방향 §0)**: 별도 태스크 142가 community-skills를 fetch 방식으로 전환 시 본 라인 표현이 다시 변경될 예정 — 본 태스크는 정확한 사실로 정정만 수행.

#### M-6. `README.md` L772 (R-8 — MCP 트러블슈팅 라인 삭제)

**기존**:

```markdown
- MCP 서버가 설치되어 있는지 확인한다: 설치 메뉴에서 `[2]` 또는 `[3]`을 선택했는지 확인
```

**변경 후 — 단순 삭제 + 검증 명령 안내 1줄로 대체**:

```markdown
- MCP 서버 설치 상태를 검증한다: `claude mcp list` 또는 `opal-cli doctor` 실행 (현행 install은 자동 등록)
```

**근거**: TASK.md R-8 AC "해당 라인이 제거되고, 그 자리에 사용자가 검증할 수 있는 명령(`claude mcp list` / `opal-cli doctor`) 안내가 들어가거나 단순 삭제" + D-3 install 자동 등록 동작 확인.

#### M-7. `README.md` 하단 `## License` 섹션 신설 (R-3)

**위치**: 트러블슈팅 섹션 바로 다음 (현재 README 마지막 — L773 이후).

**삽입할 섹션 형태**:

```markdown
---

## License

OPAL은 MIT License 하에 배포된다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조한다.

Copyright (c) 2026 OPAL contributors
```

**근거**: TASK.md R-3 AC "라이선스 명, 저작권 표기, LICENSE 파일 상대 링크 포함" + TASK.md §확정된 설계 방향 §4 "한 단락 + LICENSE 파일 링크. 별도 페이지 분리 안 함".

#### M-8. `docs/ARCHITECTURE.md` L186 (R-6 동기화 — 배포 모델)

**기존**:

```
opal/agents/* (10개)──┤              ~/.opal/agents/  (source 캐시 — 어댑터 재생성용)
```

**변경 후**:

```
opal/agents/* (12개)──┤              ~/.opal/agents/  (source 캐시 — 어댑터 재생성용)
```

**참고**: L187 `agents/* (범용 1개)`는 wtm-agent로 그대로 유지 → 합계 13개. 다이어그램 폭은 변경 없음 (10 → 12 한 자릿수 차이만).

**근거**: TASK.md §확정된 설계 방향 §6 "ARCHITECTURE.md(L186) 표기 '10개'도 동시에 13개 기준으로 정합 갱신" + 디렉토리 실측 12개 (→ D-2).

#### M-9. `docs/ARCHITECTURE.md` §컴포넌트 유형 §에이전트 표 보강 (R-6 분류 정합)

**기존 (L133-141)**: 범용 에이전트 표 5행 (opal-task / opal-task-qa / opal-task-action / opal-sdd-action / wtm).

**변경 후**: GC 체커 2행을 범용 표 또는 신규 §GC 체커 서브섹션 중 하나로 추가.

**선택안 (PLAN 결정)**: 범용 에이전트 표 하단에 2행 추가 — PROJECT.md §주요 컴포넌트(GC 파이프라인) 표현을 그대로 옮긴다.

```markdown
| opal-security-checker | (PROJECT.md §GC 파이프라인 참조) | 보안 체크 — OWASP Top 10 / CWE Top 25 / SANS Top 25 Base + `docs/SECURITY.md` 누적 |
| opal-convention-checker | (PROJECT.md §GC 파이프라인 참조) | 컨벤션 체크 — 프로젝트 `docs/CONVENTIONS.md` 유일 기준 (부재 시 초안 유도) |
```

**모델 컬럼 결정**: PROJECT.md에 모델이 명시되지 않음. EXECUTE 단계에서 알투가 `opal/agents/opal-security-checker/AGENT.md` / `opal-convention-checker/AGENT.md`의 frontmatter `model:` 필드를 직접 Read해서 정확히 채워 넣는다 (PLAN 단계에서는 추측 금지 — citation-rules §0 근거 제시 원칙).

**근거**: TASK.md R-6 AC "분류는 `docs/ARCHITECTURE.md §컴포넌트 유형 §에이전트` 의 분류와 동일 표현" — 그러나 §에이전트 자체가 11개로 outdated이므로 README L728의 13개 분류와 정합되도록 ARCHITECTURE.md §에이전트도 함께 갱신 (리스크 R-T1 대응).

---

## 3. 실행 체크리스트

> 총 10개 Step | Phase 5개

| Phase | Step | 실행 | 비고 |
|-------|------|------|------|
| 1 | 1 | 단독 | LICENSE 신규 (의존 없음) |
| 2 | 2 | 단독 | ARCHITECTURE.md §에이전트 표 보강 (Step 4의 분류 정합 의존 대상) |
| 3 | 3 | 단독 | ARCHITECTURE.md L186 카운트 정정 (Step 2 완료 후 동일 파일 → 순차) |
| 4 | 4, 5, 6, 7, 8, 9 | 병렬 가능하나 **동일 파일** README.md 다중 위치 수정 → 순차 | EXECUTE 워커가 안전한 순서로 다중 Edit 적용 |
| 5 | 10 | 단독 | README 하단 `## License` 섹션 신설 (Step 1 LICENSE 의존) |

> **실제 적용**: README.md 다중 Edit은 단일 워커가 순차 Edit로 처리 (동일 파일이라 병렬 비추천). 따라서 모든 Step이 사실상 순차 실행이며, Phase 표는 의존 흐름을 표시.

---

### Step 1: LICENSE 신규 작성

- [x] 완료
- **파일**: `LICENSE` (저장소 루트)
- **작업 내용**: SPDX MIT License 표준 텍스트(D-4) 그대로 + `Copyright (c) 2026 OPAL contributors` 1행. 추가 텍스트·번역·요약 금지.
- **완료 기준**: 파일이 존재하고, 본문이 SPDX MIT 표준 텍스트와 정확히 일치, 저작권 라인이 `Copyright (c) 2026 OPAL contributors`.
- **테스트**:
  1. `ls /Volumes/Data/AiStudio/workspace/opal/LICENSE` → 존재 확인
  2. `head -3 LICENSE` → `MIT License` / 빈 줄 / `Copyright (c) 2026 OPAL contributors` 순
  3. `wc -l LICENSE` → 약 21~22줄 (SPDX 본문 기준)
  4. SPDX 텍스트 비교 — 본문에 `Permission is hereby granted` ~ `OTHER DEALINGS IN THE SOFTWARE.` 포함
- **의존**: 없음
- **agent**: `opal-task-agent` (범용 — PROJECT.md §프로젝트 구성 Framework 단일 영역, 문서 작성)
- **AC 매핑**: R-1
- **변경 파일**: `LICENSE` (신규)

### Step 2: ARCHITECTURE.md §에이전트 표 — GC 체커 2행 추가

- [x] 완료
- **파일**: `docs/ARCHITECTURE.md` (§컴포넌트 유형 §에이전트, L133-141 범용 에이전트 표)
- **작업 내용**:
  1. `opal/agents/opal-security-checker/AGENT.md` Read → frontmatter `model:` / `description:` 확인
  2. `opal/agents/opal-convention-checker/AGENT.md` Read → 동일
  3. 범용 에이전트 표 하단에 2행 추가 (모델 컬럼은 frontmatter 실측 값으로 채움)
- **완료 기준**: §에이전트 표가 범용 7행 + 전문 6행 = **13행**으로 구성되며, 추가 2행의 모델/역할이 AGENT.md frontmatter와 일치.
- **테스트**:
  1. `grep -c "^| opal-" docs/ARCHITECTURE.md` → 13 (기존 11 + 2)
  2. 추가 행에 `opal-security-checker` / `opal-convention-checker` 포함 확인
  3. 모델 컬럼이 실제 AGENT.md `model:` 값과 일치 (직접 Read 검증)
- **의존**: 없음
- **agent**: `opal-task-agent`
- **AC 매핑**: R-6 (분류 정합)
- **변경 파일**: `docs/ARCHITECTURE.md`

### Step 3: ARCHITECTURE.md L186 — 배포 모델 카운트 10 → 12

- [x] 완료
- **파일**: `docs/ARCHITECTURE.md:186`
- **작업 내용**: `opal/agents/* (10개)──┤` → `opal/agents/* (12개)──┤` Edit. L187 `agents/* (범용 1개)`은 그대로 유지.
- **완료 기준**: L186에 `opal/agents/* (12개)` 표기, 다른 라인은 변경 없음.
- **테스트**:
  1. `grep -n "opal/agents/\*" docs/ARCHITECTURE.md` → `(12개)` 확인
  2. `grep -n "agents/\* (범용" docs/ARCHITECTURE.md` → `(범용 1개)` 그대로 확인 (합계 13)
  3. 다이어그램 박스 폭 깨짐 없음 (10→12 한 자릿수)
- **의존**: 없음 (Step 2와 동일 파일이지만 다른 위치 → 순차 권장)
- **agent**: `opal-task-agent`
- **AC 매핑**: R-6 (실측 정합)
- **변경 파일**: `docs/ARCHITECTURE.md`

### Step 4: README L728 — agents 카운트 13개 분류 표기

- [x] 완료
- **파일**: `README.md:728`
- **작업 내용**: `agents/        서브에이전트 (전문 6종 + 범용 4종)` → `agents/        서브에이전트 (전문 6 + 범용 5 + GC 2)`. 박스 폭 60자 정합 검증.
- **완료 기준**: L728 표기가 디렉토리 실측 13개 분류와 일치하며, ASCII 박스(L725 `┌─...`와 L728의 `│ ... │`) 폭이 동일.
- **테스트**:
  1. `grep -n "agents/.*서브에이전트" README.md` → 1건 매칭, 새 표현 확인
  2. L725~732 박스 라인 폭 비교 — 모든 `│ ... │` 라인 길이 동일
  3. 분류 합계 6+5+2 = 13 확인 (`opal/agents/*` 실측 12 + `agents/*` 실측 1 = 13)
- **의존**: Step 2 (ARCHITECTURE.md §에이전트 분류 13개로 정합 후)
- **agent**: `opal-task-agent`
- **AC 매핑**: R-6
- **변경 파일**: `README.md`

### Step 5: README L1~5 — 배지 2종 삽입

- [x] 완료
- **파일**: `README.md` (L5 `---` 직전)
- **작업 내용**: 헤더 블록 직후, 첫 `---` 구분선 직전에 한 줄 삽입:
  ```markdown
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE) [![Latest Release](https://img.shields.io/github/v/release/ceo4ever/opal)](https://github.com/ceo4ever/opal/releases)
  ```
  + 위아래 빈 줄 1행씩.
- **완료 기준**:
  1. README 상단(타이틀 + 1줄 설명 다음)에 두 배지가 같은 줄에 나란히 표시
  2. License 배지 클릭 → `LICENSE` 파일 (상대 링크)
  3. Latest Release 배지 클릭 → `https://github.com/ceo4ever/opal/releases`
  4. 두 배지 SVG URL이 shields.io 형식
- **테스트**:
  1. `grep -n "shields.io" README.md` → 2건 매칭 (License-MIT-yellow.svg + github/v/release/ceo4ever/opal)
  2. 상대 링크 `(LICENSE)` 매칭 확인
  3. README 렌더 시 배지가 깨지지 않는지 시각 검증 (선택)
- **의존**: Step 1 (LICENSE 파일 존재 후 — 상대 링크 깨짐 방지)
- **agent**: `opal-task-agent`
- **AC 매핑**: R-2
- **변경 파일**: `README.md`

### Step 6: README L96 — OPAL_VERSION 예시 generic 화

- [x] 완료
- **파일**: `README.md:96`
- **작업 내용**: 기존 라인 전체 교체 →
  ```markdown
  > 특정 버전 고정: `OPAL_VERSION=<원하는-태그>` 환경변수 사용 (mac/linux) 또는 `$env:OPAL_VERSION = '<원하는-태그>'` (Windows). 최신 태그는 [GitHub Releases](https://github.com/ceo4ever/opal/releases)에서 확인할 수 있다.
  ```
- **완료 기준**: (1) `v0.1` 등 specific 버전 표기 없음, (2) `<원하는-태그>` placeholder, (3) GitHub Releases 링크 한 줄 안에 포함, (4) Windows 분기 동일 처리.
- **테스트**:
  1. `grep -n "OPAL_VERSION=v" README.md` → 0건 (specific 버전 제거 검증)
  2. `grep -n "<원하는-태그>" README.md` → 2건 (mac/linux + Windows)
  3. `grep -n "ceo4ever/opal/releases" README.md` → 1건 이상
- **의존**: 없음
- **agent**: `opal-task-agent`
- **AC 매핑**: R-4
- **변경 파일**: `README.md`

### Step 7: README L103 — 부트스트랩 첫 줄 7 칼럼 정정

- [x] 완료
- **파일**: `README.md:103`
- **작업 내용**: 기존 라인 →
  ```
  [부트스트랩] ✅ identity ✅ harness ✅ PM ✅ PM모드 ⏳ registry ⏳ references ⏳ model-mapping
  ```
- **완료 기준**: `~/.opal/AGENT.md:53` SSOT와 칼럼 수(7)·항목명·구분자 정확히 일치.
- **테스트**:
  1. `grep -n "PM모드" README.md` → 1건 매칭
  2. 칼럼 수 카운트 (✅ 4 + ⏳ 3 = 7 칼럼) 확인
  3. `~/.opal/AGENT.md` Step 6 출력 형식과 diff 0
- **의존**: 없음
- **agent**: `opal-task-agent`
- **AC 매핑**: R-5
- **변경 파일**: `README.md`

### Step 8: README L729 — community-skills 카운트 30개/6개 조직

- [x] 완료
- **파일**: `README.md:729`
- **작업 내용**: `community-skills/  외부 조직 제공 스킬 (31개)` → `community-skills/  외부 조직 제공 스킬 (30개 / 6개 조직)`. 박스 폭 정합 검증.
- **완료 기준**: 카운트 30 + 조직 수 6 명시. ASCII 박스 폭 정합.
- **테스트**:
  1. `grep -n "community-skills/" README.md` → 새 표현 확인
  2. `find community-skills -maxdepth 3 -name SKILL.md | wc -l` = 30 (실측 재확인)
  3. `ls -1d community-skills/*/ | wc -l` = 6 (조직 수 재확인)
  4. 박스 라인 폭 동일 검증
- **의존**: 없음
- **agent**: `opal-task-agent`
- **AC 매핑**: R-7
- **변경 파일**: `README.md`

### Step 9: README L772 — MCP 트러블슈팅 라인 정정

- [x] 완료
- **파일**: `README.md:772`
- **작업 내용**: 기존 라인 →
  ```markdown
  - MCP 서버 설치 상태를 검증한다: `claude mcp list` 또는 `opal-cli doctor` 실행 (현행 install은 자동 등록)
  ```
- **완료 기준**: "설치 메뉴에서 [2] 또는 [3]" 표현이 README에서 완전히 제거되고, 검증 명령 1줄로 대체.
- **테스트**:
  1. `grep -n "설치 메뉴" README.md` → 0건 (제거 검증)
  2. `grep -n "claude mcp list\|opal-cli doctor" README.md` → 1건 이상 (대체 명령 확인)
- **의존**: 없음
- **agent**: `opal-task-agent`
- **AC 매핑**: R-8
- **변경 파일**: `README.md`

### Step 10: README 하단 `## License` 섹션 신설

- [x] 완료
- **파일**: `README.md` (트러블슈팅 섹션 다음, 파일 마지막)
- **작업 내용**: 파일 끝(L773 이후)에 다음 블록 추가:
  ```markdown

  ---

  ## License

  OPAL은 MIT License 하에 배포된다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조한다.

  Copyright (c) 2026 OPAL contributors
  ```
- **완료 기준**: (1) `## License` 헤딩 존재, (2) MIT 명시, (3) `[LICENSE](LICENSE)` 상대 링크, (4) 저작권 표기 1행.
- **테스트**:
  1. `grep -n "^## License$" README.md` → 1건 매칭
  2. `grep -n "\[LICENSE\](LICENSE)" README.md` → 1건 매칭
  3. `grep -n "Copyright (c) 2026 OPAL contributors" README.md` → 1건 매칭 (LICENSE와 텍스트 정합)
- **의존**: Step 1 (LICENSE 파일 존재 후 — 상대 링크 깨짐 방지)
- **agent**: `opal-task-agent`
- **AC 매핑**: R-3
- **변경 파일**: `README.md`

---

## 4. QA 체크리스트

### 기능 테스트 (요구사항 R-1~R-8 직접 검증)

- [x] **R-1**: `LICENSE` 파일 존재. SPDX MIT 표준 텍스트 + `Copyright (c) 2026 OPAL contributors` 1행. 추가 텍스트 0.
- [x] **R-2**: README 상단에 License: MIT + Latest Release 배지 2종 표시. License 배지 클릭 → LICENSE 파일 이동, Release 배지 → GitHub Releases 페이지.
- [x] **R-3**: README 하단 `## License` 섹션이 트러블슈팅 직후에 존재. MIT 명시 + LICENSE 상대 링크 + 저작권 표기.
- [x] **R-4**: README L96 부근에 `OPAL_VERSION=<원하는-태그>` placeholder + GitHub Releases 링크 한 줄 안내. specific 버전(`v0.1` 등) 표기 없음.
- [x] **R-5**: README L103 부트스트랩 첫 줄이 `~/.opal/AGENT.md:53`과 칼럼 수(7)·항목명 정확 일치. `PM모드` 칼럼 포함.
- [x] **R-6**: README L728 카운트가 13개 분류(전문 6 + 범용 5 + GC 2). ARCHITECTURE.md L186 = 12개, L187 = 1개 (합계 13). ARCHITECTURE.md §컴포넌트 유형 §에이전트 표 = 13행 (범용 7 + 전문 6).
- [x] **R-7**: README L729 표기가 `30개 / 6개 조직`. 실측 검증 통과 (`find community-skills -maxdepth 3 -name SKILL.md | wc -l` = 30, 디렉토리 6개).
- [x] **R-8**: README L772의 "설치 메뉴에서 [2] 또는 [3]" 표현 제거. 대체 검증 명령(`claude mcp list` / `opal-cli doctor`) 1줄 안내.

### 일관성 테스트

- [x] README L728 분류와 ARCHITECTURE.md §컴포넌트 유형 §에이전트 표가 동일 분류 체계 사용 (전문 / 범용 / GC).
- [x] LICENSE 본문 저작권 라인과 README `## License` 섹션 저작권 표기가 정확히 동일 (`Copyright (c) 2026 OPAL contributors`).
- [x] README 배지의 License-MIT 표기와 LICENSE 파일·README §License 섹션 모두 MIT로 일치.
- [x] README L96 OPAL_VERSION 안내가 `scripts/install.sh:50-67` 동작(미설정 시 latest release 자동 폴백)과 정합 (specific 버전 강제 표기 없음).
- [x] README ASCII 박스(L725-732) 폭이 변경 후에도 정합 (모든 `│ ... │` 라인 길이 동일).

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙 (`docs/CONVENTIONS.md` §언어 규칙) 준수.
- [x] README 마크다운이 정상 렌더링 (배지 SVG 로드 가능, 링크 깨짐 없음).
- [x] 변경이력 행 추가 안 함 (TASK.md §제약 조건 "docs는 변경이력 의무 대상 아님" — L186 v0.3.15 선례 일치).
- [x] kebab-case 파일/폴더 네이밍 규칙 (해당 없음 — 본 태스크는 신규 파일이 `LICENSE` 1개로 OSS 표준 명명).

---

## 5. 리스크 및 대응

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-T1 | **분류 표현 영역 간 불일치** — README L728(13개 기준 신규 분류) ↔ ARCHITECTURE.md §컴포넌트 유형 §에이전트(11개 명시, security/convention checker 누락). citation-rules §7 영역 간 용어 일관성 검토 항목. | R-6 AC "분류는 ARCHITECTURE.md §컴포넌트 유형과 동일 표현" 충족 불가 위험. | **Step 2에서 ARCHITECTURE.md §에이전트 표에 GC 체커 2행 사전 추가**하여 양쪽 분류 정합 확보 (M-9). |
| R-T2 | **shields.io Latest Release 배지 동적 SVG** — repo가 비공개거나 release tag가 없을 때 배지가 깨짐. | 사용자 첫 시각 임팩트 손상. | 본 태스크 시점 기준 `ceo4ever/opal`은 public + v0.3.16 release 존재 (TASK.md §배경 확인). 향후 repo 비공개화 시 배지 정책 재검토 필요 — P2 후속. |
| R-T3 | **community-skills 카운트가 142 태스크에서 다시 변경** — 142가 fetch 방식으로 전환하면 R-7 표기가 또 outdated. | README 표기 재갱신 필요. | TASK.md §확정된 설계 방향 §0에 명시된 대로 142 태스크 범위에 README 갱신을 포함 — 본 태스크는 현 시점 정확한 사실(30개 / 6개 조직)로만 정정. |
| R-T4 | **README ASCII 박스 폭 깨짐** — L728 / L729 변경 후 박스 라인 폭이 60자에서 어긋날 가능성. | 시각적 정렬 문제 (기능 영향 없음). | EXECUTE 단계에서 변경 후 L725-732 박스 라인 폭을 직접 비교 검증 (Step 4 / Step 8 테스트 항목에 포함). |
| R-T5 | **ARCHITECTURE.md §에이전트에 추가하는 GC 체커의 모델 컬럼 정보 부재** — PROJECT.md GC 파이프라인 표에는 모델 명시 없음. | 추측 기재 시 citation-rules §0 위반. | EXECUTE 단계에서 `opal/agents/opal-security-checker/AGENT.md` / `opal-convention-checker/AGENT.md` frontmatter `model:` 직접 Read하여 정확한 값 기재 (Step 2 작업 내용에 포함). |

### §7.4 decision_required 보고

본 태스크에서는 다른 영역 간 용어 불일치(FE/BE 등)는 발견되지 않았다. R-T1은 ARCHITECTURE.md §에이전트 분류 자체를 본 태스크 범위 내(M-9, Step 2)에서 정정함으로써 자체 해결 — 추가 사용자 결정 사항 없음.

---

## 6. PM 검토 기준 (체크리스트)

> `.opal/AGENT.md` §PM 검토 기준 + 본 태스크 특성 매핑.

### 필수 검토

- [ ] TASK.md R-1~R-8 요구사항이 PLAN §3 실행 체크리스트 Step 1~10에 1:1로 커버 (AC 매핑 표 확인)
- [ ] `docs/CONVENTIONS.md` §언어 규칙 / §구현 규칙 §Guards / §변경이력 / §커밋 규칙 4종 [MUST] 인용 (PLAN §1 참조 문서 §컨벤션 인용 섹션)
- [ ] CONVENTIONS.md 금지사항(사용자 승인 없는 코드 생성·수정) 위반 없음 — PLAN까지만 작성, EXECUTE는 별도 승인
- [ ] PROJECT.md §프로젝트 문서 테이블에서 본 태스크 관련 문서(README.md, ARCHITECTURE.md, CONVENTIONS.md)가 워커에게 전달됨

### 도메인 검토

- [ ] **컴포넌트 표준화**: 본 태스크는 OSS 공개 표준(MIT LICENSE, shields.io 배지)에 정합. SPDX 표준 텍스트 사용으로 라이선스 호환성 확보.
- [ ] **재사용성 / 플랫폼 독립성**: 모든 변경이 OS 무관 마크다운 + 외부 표준 — 다른 OPAL 프로젝트에 영향 없음.
- [ ] **하네스 Guards/Gates 적용**: 사용자 승인 전 코드/파일 수정 금지. 본 PLAN은 산출물 문서만 작성. CLOSE 진입 별도 승인 필요.
- [ ] **변경이력 면제 검증**: docs(README/ARCHITECTURE) + LICENSE는 변경이력 의무 대상 아님 — TASK.md §제약 조건 + L186 v0.3.15 선례.
- [ ] **부트스트래퍼·MCP install 영향**: 없음 (텍스트 변경만 — install/doctor 동작에 영향 0).
- [ ] **추적 가능성 (citation-rules)**: §1 참조 문서 테이블 D-1~D-11 + §2 핵심 설계의 인라인 인용 / [MUST] 4종 / 영역 간 용어 일관성 R-T1 검출 모두 충족.

### 본 태스크 특성

- [ ] 본 태스크는 **문서 변경만**으로 회귀 테스트 시나리오 불필요 (TEST-SCENARIO.md 생략 — opp 표준).
- [ ] EXECUTE 단계 워커 = `opal-task-agent` 단일 (PROJECT.md §프로젝트 구성 Framework 단일 영역, 전문 에이전트 = `opal-task-agent` 폴백 정합).
- [ ] 모든 Step의 완료 기준이 검증 가능한 명령(`grep`, `find`, `wc -l`, 시각 검증)으로 표현됨.
