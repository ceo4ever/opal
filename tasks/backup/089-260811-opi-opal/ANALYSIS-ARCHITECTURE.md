# ANALYSIS: docs/ARCHITECTURE.md 실측 1:1 대조

> 실측 일시: 2026-08-11 13:08 KST | opi 최신화 Phase 2 Step C·D
> 대상: `docs/ARCHITECTURE.md` (424줄)
> 기준(SSOT): 실제 디렉토리·파일·frontmatter 실측. `docs/` 상호인용 미사용.
> 산출 경로: 워커가 하네스 제약으로 파일을 쓰지 못해 **PM이 워커 반환 본문을 그대로 저장**했다.

## 0. 대조 단위

표 1행 = 1건, 트리 1항목 = 1건, 명제 1개 = 1건. §3·§4는 §2와 중복 계상하지 않는다.

## 1. 대조 요약

| 분류 | 건수 |
|------|------|
| 일치 | 84 |
| 불일치 | 16 |
| 문서에 없음 | 12 |
| 실제에 없음 | 4 |

총 116건 중 **32건(27.6%)이 현행과 어긋난다.**

실측 기준값:

```
ls opal/agents | wc -l              → 15
ls skills/ | wc -l                  →  8
ls opal/skills | wc -l              → 42
ls opal/tools                       → 20 (도구 19 + requirements.txt)
ls opal/core/mcps/*.json            →  4
ls dashboard/frontend/src/pages/    →  7
ls dashboard/backend/routers/*.py   →  7
```

## 2. 불일치 (문서 ≠ 실제)

### 2-A. 수량 — PM 확정분 승계, 재실측으로 유효 확인

| # | 문서 위치 | 문서 표기 | 실측값 | 근거 | 갱신 제안 |
|---|---|---|---|---|---|
| D-1 | `:39` `:79` `:204` `:376` | 서브에이전트 **12개** (4곳) | **15** | `ls opal/agents \| wc -l` → 15 | 4곳 `15개`. PM 지시서의 `:373`은 현재 `:376`(트리) |
| D-2 | `:78` `:201` `:340` | 독립 스킬 **5개**(`:78`) / **6개**(`:201`·`:340`) | **8** | `ls skills/` → api-analyzer, erd-modeler, **html-mockup**, interview, **system-architecture-html**, ui-designer, web-to-markdown, wireframe-builder | 3곳 `8개` — 문서 내부 5 vs 6 불일치도 동시 해소 |
| D-3 | `:78` `:360` / `:202` | OPAL 스킬 **25개** / **24개** | **42** | `ls opal/skills \| wc -l` → 42 | 3곳 `42개` |
| D-4 | `:79` `:376` | 내역 "전문 7 + 범용 4 + 도구성 1" | **전문 8 + 범용 7** | 문서 자체 표(`:150-157` 범용 7행 / `:162-170` 전문 8행)와도 어긋남 | `전문 8 + 범용 7` |

에이전트 표(`:150-170`)는 **이미 15개 전부를 나열 중**이다. 틀린 것은 요약 수치와 트리뿐이다.

### 2-B. model 레벨 — frontmatter 전수 실측

`for d in opal/agents/*/; do grep -m1 '^model:' "$d/AGENT.md"; done`

| # | 위치 | 에이전트 | 문서 | 소스 frontmatter |
|---|---|---|---|---|
| D-5 | `:151` | `opal-task-agent` | standard | **advanced** |
| D-6 | `:165` | `opal-be-agent` | standard | **advanced** |

나머지 13개는 전건 일치: task-qa `light` · task-action `advanced` · sdd-action `advanced` · wtm `light` · security-checker `advanced` · convention-checker `standard` · plan `advanced` · fe `standard` · db `standard` · planning `advanced` · test `standard` · evaluator `advanced` · loop-action `advanced`.

### 2-C. 서술 내용

| # | 위치 | 문서 표기 | 실측값 | 근거 | 갱신 제안 |
|---|---|---|---|---|---|
| D-7 | `:155` `:388` | wtm 폴백 "Phase 1 **WebFetch** → Phase 2 cmux → Phase 3 playwright" (3단) | **2단** cmux → playwright, WebFetch 제거 | `opal/agents/opal-wtm-agent/AGENT.md:5-6` | 2곳 모두 2단으로 |
| D-8 | `:391` | frontend "**6개 화면** — 브레인 질의 포함, 태스크 036" | **7** | `ls dashboard/frontend/src/pages/` → brain, dashboard, doctor, memory, projects, **settings**, tasks | `7개 화면 — 설정 포함, 태스크 061`. 본문 `:239`는 이미 정확 — **트리만 stale** |
| D-9 | `:296-299` | 적용 플랫폼: context7·playwright "Claude/Cursor/Gemini", shadcn·sequential-thinking "Claude/Cursor" | **4종 모두 5플랫폼** | `cat opal/core/mcps/*.json` → 전부 `"platforms":["claude","cursor","gemini","antigravity","codex"]` | 4행 모두 5플랫폼으로 통일 |
| D-10 | `:296-299` | 설치 방식 "CLI 또는 config_merge" | json 4개 전부 `"install_type":"config_merge"` | 동상 | CLI 등록은 install 스크립트 플랫폼 분기의 결과임을 구분 서술 |
| D-11 | `:283` `:329` | `console {start\|stop\|status\|open\|scan}` | **`log` 포함 6종** | `opal/tools/opal-cli/run.sh:70` | `{start\|stop\|status\|open\|scan\|log}` |
| D-12 | `:212-219` `:222-224` `:230` | 배포 대상 플랫폼 **3종** (`~/.claude/` `~/.cursor/` `~/.gemini/`) | **4종** — `~/.codex/` 누락 | `scripts/install-mac.sh:700 install_codex_agents()`, `:817 install_codex_config()`, `:563` codex 모델맵, `opal/bootstrapper/codex-bootstrap.md` 실재 | Codex 행 신설 |
| D-13 | `:303` | MCP 등록 "claude / gemini / Cursor·Antigravity" | **5플랫폼** | `scripts/install-mac.sh:149`, `:1915` `codex mcp add` | Codex 추가 |
| D-14 | `:81` | `references/` = 6종 열거 | **19 엔트리** + `harness/` 17파일 + `pm/` 6파일 | `ls opal/core/references` | 열거 대신 범주 서술로 전환 (§5 T-084 참조) |
| D-15 | `:82` `:354-359` | `tools/` = 6종(표) / 4종(트리) | **도구 19종** | `ls opal/tools` | §3 M-8 참조 |
| D-16 | `:394` | `scripts/` = "설치 스크립트 (**install-mac.sh**)" | **6 엔트리** | `ls scripts/` → `install-mac.sh` `install.sh` `install.ps1` `merge-hooks.py` `install/`(linux·macos·windows) `tests/` | 진입점·플랫폼 어댑터·tests 반영 |

## 3. 문서에 없음 (실제에만 존재)

| # | 항목 | 실측 근거 | 추가할 섹션 |
|---|---|---|---|
| M-1 | 독립 스킬 2종: `html-mockup`, `system-architecture-html` | `ls skills/` | §컴포넌트 유형 스킬 표 "독립" 그룹(`:131-136`) + 트리(`:340-346`) |
| M-2 | Pilot 2종: `opal-pilot-data-design`, `opal-pilot-gc` | `ls opal/skills` | §오케스트레이터 표(`:108-115`) + 트리(`:361-367`) |
| M-3 | 데이터 설계 단계 스킬 3종: `op-data-ddl`, `op-data-dictionary`, `op-data-model` | 동상 | 스킬 표에 **"데이터 단계" 그룹 신설** |
| M-4 | 보조 단계 스킬 3종: `op-brain-ingest`, `op-scenario-gate`, `op-spec-validator` | 동상 | 스킬 표 신규 그룹 또는 "범용 단계" 확장 |
| M-5 | OPAL 스킬 6종: `opal-action-status`, `opal-brain`, `opal-help`, `opal-improve`, `opal-next`, `opal-workspace-sync` | 동상 | 스킬 표 "OPAL" 그룹(`:137-141`) + 트리(`:371-375`) |
| M-6 | `op-sdd-action-plan` | `ls opal/skills` | §SDD 단계 표 — `op-sdd-tasks` 자리 대체(§4 A-1) |
| M-7 | 에이전트 트리 3종 누락: `opal-security-checker`, `opal-convention-checker`, `opal-loop-action-agent` | **표(`:156-157`·`:170`)에는 있으나 트리(`:376-388`)에만 없음** | 트리 |
| M-8 | 도구 13종: `backlog-tool` `brain-tool` `date` `doctor` `git-sync-tool` `improve-tool` `opal-action-monitor` `opal-agent` `opal-cli` `playwright-tool` `state-tool` `test-tool` (+ `cmux-tool`은 트리에만 존재, `:82` 표에는 없음) | `ls opal/tools` | §Global Layer `tools/` 행(`:82`) + 트리(`:354-359`) |
| M-9 | **Codex 플랫폼 전반** — 부트스트래퍼(`~/.codex/AGENTS.md`)·에이전트 어댑터·config.toml·MCP 등록 | `opal/bootstrapper/codex-bootstrap.md`, `install-mac.sh:700·817·1915` | §배포 모델 다이어그램·본문 (D-12·D-13과 동일 근원) |
| M-10 | `opal/core/` 직속 4파일: `AGENT.md` `PRINCIPLES.md` `identity-template.md` `setting.default.json` | `ls opal/core/` | 트리 `:350-353` |
| M-11 | `docs/architecture-diagram/opal_framework_architecture.html` (태스크 086 산출) | `ls docs/architecture-diagram/` | §시스템 구성 상단 시각 자산 포인터 + 변경이력 |
| M-12 | 저장소 루트 6항목: `README.md` `LICENSE` `VERSION` `CLAUDE.md` `GEMINI.md` `memory/` | `ls -1` (루트) | 트리 `:339-397` |

## 4. 실제에 없음 (문서에만 존재)

| # | 문서 위치 | 문서 표기 | 왜 실제에 없는지 |
|---|---|---|---|
| A-1 | `:130` | SDD 단계 스킬 `op-sdd-tasks` | `ls -d opal/skills/op-sdd-tasks` → **No such file**. 실제는 `op-sdd-action-plan`(M-6). `:114` opsdd 파이프라인의 `TASKS` 단계명도 재확인 필요 |
| A-2 | `:204` | 배포 모델 `agents/* (범용 1개)` | `ls -d agents` → **No such file**. 저장소 루트에 `agents/` 디렉토리 자체가 없다 |
| A-3 | `:347` | 트리 `agents/ 범용 에이전트 슬롯 (현재 비어있음)` | 동상 — "비어있음"이 아니라 **부재**. 행 삭제 권고 |
| A-4 | `:300` | MCP 표 `Notion` 행 | `ls opal/core/mcps/` → notion.json 없음. `grep -n "Notion\|notion" scripts/install-mac.sh` → **0건** |

## 5. 최근 태스크 반영 필요성 판정

| 태스크 | 반영 필요 | 대상 섹션 | 사유 |
|---|---|---|---|
| 083 (08-04) | **불요 — 이미 반영** | `:82` tools/ + 변경이력 `:408` | `shardPolicy` 3단 우선순위·`split`/`init` 서술 존재. `code-scan.js` USAGE 실측 15종이 "13→15" 기술과 일치 |
| 084 (08-06) | **필요** | §Global Layer `references/` 행(`:81`) | `opal/core/references/pm/asis-analysis.md` 신설(219줄). ARCHITECTURE.md는 `pm/` 하위 디렉토리를 **언급조차 안 함** → D-14와 함께 해소 |
| 085 (08-07) | **불요 — 이미 반영** | 배포 채널 `:328` + 변경이력 `:407` | DL-CONTRACT 규약 서술 존재 |
| 086 (08-10) | **필요** | §시스템 구성 도입부 + 트리 `docs/` + 변경이력 | 다이어그램 HTML 신설. ASCII 다이어그램(`:9-52`)과 정본 10계층 HTML이 **병존하는데 상호 포인터가 없다**. 086이 "정본 10계층 1종으로 통일"했으므로 ASCII가 2차 진실이 되는 리스크 — 링크 삽입 + ASCII 축소 권고 |
| 087 (08-10) | **불요 — 이미 반영** | `:312-314` Python 절 + 변경이력 `:406` | 재실측 전건 일치: `install-mac.sh:70-71` `OPAL_PYTHON_MIN="3.11"`/`OPAL_PYTHON_TARGET="3.14"`, `:1408` 옵트아웃, `:1429` brew 자동설치, `:1480·1500` 미달 시 중단, `:1505` 기존 venv 재검증·폐기 |
| 088 (08-11) | **불요 — 이미 반영** | `:82` memory-tool 행 + 변경이력 `:405` | CLOSE 시 state-tool→memory-tool subprocess 호출·`history_link.warning` 비차단 서술 존재 |

## 6. 섹션별 갱신 제안 요약

| 섹션 | 판정 |
|---|---|
| §시스템 구성 다이어그램 (`:9-52`) | **갱신 필요** — 서브에이전트 12→15(D-1), 나열 10종→15종 또는 요약 표기. 086 HTML 포인터 추가 |
| §부트스트랩 진입 모델 (`:54-66`) | **변경 없음** — `opal/core/AGENT.md` 대조 전건 일치 |
| §Global Layer (`:70-84`) | **갱신 필요** — skills/agents 수량(D-1·D-2·D-3), `references/` 범주 서술 전환(D-14), `tools/` 19종(D-15·M-8) |
| §Project Layer (`:86-98`) | **변경 없음** — 7행 전건 실재 확인 |
| §컴포넌트 유형 — 스킬 (`:102-141`) | **갱신 필요** — Pilot 2·데이터 3·보조 3·OPAL 6·독립 2 = **16종 추가**, `op-sdd-tasks`→`op-sdd-action-plan` 교체 |
| §컴포넌트 유형 — 에이전트 (`:143-170`) | **갱신 필요(경미)** — model 2건(D-5·D-6), wtm 폴백 2단(D-7). **행 구성 자체는 15개 완비** |
| §커뮤니티 스킬 (`:172-182`) | **미검증** — 런타임 설치 대상이라 저장소 실측 불가 |
| §하네스 (`:184-194`) | **미검증** — `opal-harness.md` 소관, 본 보고서 범위 밖 |
| §배포 모델 (`:196-232`) | **갱신 필요(대)** — Codex 전 경로 누락(D-12·M-9), `agents/*` 부재 소스(A-2), 수량 3건 |
| §OPAL Console (`:234-286`) | **갱신 필요(경미)** — `console log`(D-11). 화면 7·포트 7823·라우터 7종·어댑터 4종은 **전건 일치** |
| §외부 의존 (`:288-334`) | **갱신 필요** — MCP 플랫폼 4행(D-9), Notion 행 삭제(A-4), Codex 등록(D-13). Python·Node·배포 채널은 **변경 없음** |
| §디렉토리 구조 (`:336-397`) | **갱신 필요(대)** — 트리가 가장 크게 stale. `agents/` 삭제(A-3), 스킬·에이전트·도구 누락 다수, `opal/core/` 직속(M-10), 루트 6항목(M-12), `scripts/`(D-16), frontend 화면 수(D-8) |
| §변경이력 (`:401-424`) | **갱신 필요** — 084·086 행 없음. **날짜 역순 정렬이 깨져 있다**(`:411` 2026-07-17 뒤 `:412` 2026-06-18 → `:413` 2026-06-30) |

## 7. PM 지시서 대비 정정 1건

지시서의 참고사항 중 **`state-tool` 서브명령 "10종"은 실측 11종**이다.

```
grep -c "sub.add_parser(" opal/tools/state-tool/state_tool.py → 11
init, show, advance, mark, block, validate, add-row, status, gate-pass, spec-validate, verify
```

`verify`(`state_tool.py:2471-2473`)가 다중행 호출이라 단순 grep에서 누락되기 쉽다. `brain-tool`은 **10종**으로 확인. 두 수치 모두 `docs/ARCHITECTURE.md`에는 서술이 없어 이 문서의 갱신 대상은 아니나, `docs/CONVENTIONS.md`·`tools.md` 대조 시 11종을 기준으로 삼아야 한다.

## 8. 가장 중요한 3건

1. **Codex 플랫폼이 배포 모델에서 통째로 빠져 있다** (D-12·D-13·M-9) — `install_codex_agents()`·`install_codex_config()`·`codex mcp add`·`codex-bootstrap.md`가 모두 실재하는데 문서는 3플랫폼만 서술한다. 수치 오차가 아니라 **지원 플랫폼 하나가 문서에서 비가시 상태**다.
2. **스킬 인벤토리가 42 중 27만 문서화됐다** (D-3·M-1~M-6) — 데이터 설계 3종·Pilot 2종·OPAL 6종 등 16종이 표에 없고, 반대로 `op-sdd-tasks`는 실물이 없다. 스킬 표가 레지스트리 역할을 못 하고 있다.
3. **디렉토리 트리가 표보다 더 낡았다** (D-8·M-7·M-10·M-12·A-3) — 에이전트 표는 15개를 정확히 나열하는데 트리는 12개, Console 본문은 7화면인데 트리는 6화면, 트리의 `agents/` 항목은 **디렉토리 자체가 존재하지 않는다**. 트리를 본문 표에서 파생시키는 재작성을 권고한다.
