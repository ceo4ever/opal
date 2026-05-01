# DONE: 멀티 플랫폼 에이전트 배포 메커니즘 구축

> 완료일: 2026-04-30 | 적용 스킬: opp | 모드: agentic

---

## 1. 태스크 결과 요약

OPAL 에이전트(`~/.opal/agents/`, 13개)가 Claude Code / Cursor / Gemini CLI에서 sub-agent로 정식 인식되도록 `scripts/install-mac.sh`에 자동 어댑터 생성 메커니즘을 구축했다. Antigravity는 공식적으로 sub-agent 미지원으로 확인되어 적용 제외 + 사유 인용 문서화. mams 프로젝트에서 보고된 "OPAL 에이전트가 silent fallback to general-purpose"되던 문제의 정확한 원인이 입증되고 해소되었다.

## 2. 변경 파일 (총 2개)

| 파일 | 변경 내용 |
|------|----------|
| `scripts/install-mac.sh` | 헬퍼 `_flatten_description()` + 변환 함수 `emit_platform_agent_adapter()` + 플랫폼별 함수 3개(`install_claude_agents`/`install_cursor_agents`/`install_gemini_agents`) + `install_opal()` 본문 호출 블록 추가. 헤더 변경이력 v1.1 → v1.3 |
| `opal/core/references/agents.md` | §"플랫폼 sub-agent 어댑터 변환 규칙" 신규 섹션 추가 — 4개 플랫폼 메커니즘 표 + frontmatter 변환 매핑 + 본문 처리 + Antigravity 미지원 처리 + Cursor inherit 정책 / Antigravity 사용자 안내. 변경이력 v1.1 → v1.3 |

## 3. 검증 결과

### 3.1 정적 검증 (PM + QA 워커)

- ✅ `bash -n scripts/install-mac.sh` exit_code 0
- ✅ 4개 플랫폼 공식 문서 spot check (Claude/Cursor/Gemini/Antigravity) 모두 인용 정확성 입증
- ✅ Citation Rules §0 §1.5 §2.4 §3.1 §3.2 §4 모두 준수
- ✅ 하네스 Guards 100% 준수 — 배포 행위 캡틴 명시 지시 시에만 실행 / `~/.opal/` 직접 수정 없음 / OPAL 에이전트 본문 13개 무변경

### 3.2 실배포 검증 (캡틴 명시 지시)

캡틴이 `bash scripts/install-mac.sh` 명시 실행 + 새 Claude Code 세션 검증:

- ✅ `~/.claude/agents/` 13개 / `~/.cursor/agents/` 13개 / `~/.gemini/agents/` 13개 어댑터 정상 배포
- ✅ frontmatter 변환 매핑 정확 — Claude(haiku/sonnet/opus 분포 2:6:5), Cursor(inherit 13), Gemini(flash-lite/flash/pro 2:6:5)
- ✅ AUTO-GENERATED 헤더 보존 (39/39)
- ✅ Claude Code 세션의 "Available agent types" 목록에 OPAL 13개 정상 노출 — **silent fallback 가설 실증적으로 해소**

## 4. 작업 중 발견·해소한 결함 2건

본 태스크는 PLAN → EXECUTE → 1차 배포 → 캡틴 검증 → 결함 발견 → EXECUTE 보강(v1.2) → 2차 배포 → 결함 발견 → EXECUTE 보강(v1.3) → 3차 배포 → 검증 통과 사이클을 거쳤다. 발견된 결함은 모두 본 태스크 안에서 해소되었다.

| # | 결함 | 발견 시점 | 원인 | 해소 |
|---|------|---------|------|------|
| F-1 | Claude Code 파서가 multiline description 어댑터 미인식 | 2차 배포 후 새 세션 검증 | PyYAML 출력의 기본 width=80 + 자체 yaml_escape() 직렬화로 한국어 description이 multiline 출력 → Claude Code 파서는 single-line 가정 | v1.2 — `_flatten_description()` 헬퍼 도입(`re.sub(r'\s+', ' ', s).strip()`) + 적용 3곳 (PyYAML 추출 + stdlib 블록 처리 + stdlib 단일 라인) |
| F-2 | install-mac.sh 재실행 시 기존 어댑터 39개 모두 user-managed로 오탐지하여 skip | 3차 배포 직후 | W-2 사용자 파일 가드의 `head = ''.join([next(f, '') for _ in range(3)])` 검사가 frontmatter 첫 3줄만 보고 line 9의 AUTO-GENERATED 헤더를 못 찾음 | v1.3 — `head = f.read()`로 전체 파일 검사 |

## 5. 학습 사항 (메모리 후보)

### 5.1 Claude Code sub-agent frontmatter 제약

- YAML 표준은 큰따옴표 내 줄바꿈을 valid로 받아들이지만, **Claude Code 파서는 single-line description을 가정**한다. multiline description은 sub-agent 등록 실패의 silent 원인이 된다.
- 신규 OPAL 에이전트 추가 시 `description: |` 블록 스타일을 사용해도 어댑터 변환 시점에 자동 평탄화되므로 OPAL 에이전트 작성자는 컨벤션 변경 불필요.

### 5.2 silent fallback 가설 입증

- Claude Code Agent 도구는 미등록 `subagent_type`을 silent하게 `general-purpose`로 폴백한다 (에러 미발생).
- 본 태스크 이전의 모든 OPAL 디스패치는 사실상 `general-purpose`로 실행되었으며, OPAL 페르소나·자체 로드 문서·금지 규칙 차별화는 발화하지 않았다. 결과물은 PM의 풍부한 컨텍스트 주입 덕에 그럴듯하게 나왔으나, 본 태스크 이전엔 OPAL의 "전문 에이전트 시스템" 효과가 실질적으로 미실현 상태였음.

### 5.3 Antigravity 미지원

- 2026-04 기준 Antigravity는 커스텀 sub-agent를 지원하지 않으며 (Google AI Forum 공식 응답: "feature request escalated to internal teams for review"), 현재 OPAL 부트스트래퍼는 `~/.gemini/GEMINI.md`(Gemini CLI 호환 경로)를 통해 동작한다. Antigravity가 sub-agent를 지원하기 시작하면 `install_antigravity_agents()`를 추가하여 어댑터 자동 생성 가능.

## 6. agentic 모드 운영 통계

- 게이트 판단: 8회 (Pass: 8 / Fail: 0)
- 3회 초과 Gate: 0건
- 오류 발견: 7건 (Warning 5건 + Critical 2건 — F-1/F-2 모두 본 태스크 EXECUTE 안에서 해소)
- 수정 지시: 0건 (Warning은 EXECUTE 워커 프롬프트 사전 주입으로 해소, Critical은 v1.2/v1.3 보강으로 해소)
- PM 의사결정: 11건
- 개선 사항: 7건
- 에스컬레이션: 0건

## 7. R-6 검증 절차 실행 결과

PLAN.md §4 Step 8(silent fallback 가설 입증 5단계)은 캡틴이 직접 수행했다:

1. ✅ `bash scripts/install-mac.sh` 실행 (캡틴 명시 지시)
2. ✅ `ls ~/.claude/agents/` → 13개 파일 존재
3. ✅ `head -10 ~/.claude/agents/opal-task-agent.md` → frontmatter `name`, `model: sonnet` 정확
4. ✅ 새 Claude Code 세션의 "Available agent types"에 OPAL 13개 노출 — **silent fallback 끊김 입증**
5. ✅ 다음 디스패치부터 `subagent_type: opal-be-agent` 등으로 정확한 라우팅 가능

## 8. 후속 작업 (선택)

| 항목 | 우선순위 | 비고 |
|------|---------|------|
| Cursor / Gemini CLI 동등 검증 | 중 | 캡틴이 Cursor/Gemini를 일상 사용 시 자연 검증. 별도 태스크 아님 |
| `install-mac.sh` 종료부에 "Claude Code/Cursor/Gemini CLI 재시작 시 sub-agent 노출" 안내 메시지 | 하 | UX enhancement — 별도 태스크 후보 |
| Antigravity sub-agent 출시 모니터링 | 하 | 정기 점검 메모리 등록 검토 |

## 9. 본 태스크가 미친 영향

- **127번 태스크**(oppd FE/BE 전문 에이전트 라우팅) — 본 태스크 완료 후 비로소 의미 있게 작동. 127이 정의한 라우팅(`opal-task-action-agent` → `opal-fe-agent`/`opal-be-agent`)이 실제로 페르소나 분기를 발화시킬 수 있게 됨.
- **122번 태스크**(opal-pilot-gc) — `opal-security-checker`, `opal-convention-checker` 두 sub-agent가 정상 등록되어 GC 파이프라인 실효성 향상.
- **117번 태스크**(전문 에이전트 시스템) — 설계가 사실상 본 태스크에 의해 비로소 실행 가능 상태로 전환됨.

본 태스크는 OPAL "전문 에이전트 시스템"의 누락된 마지막 다리(bridge)였다.

## 10. 산출물 인덱스

| 파일 | 역할 |
|------|------|
| TASK.md | 요구사항 R-1~R-7 + 미확정 사항 + 배경 분석 |
| PLAN.md (531줄) | 4개 플랫폼 조사 + frontmatter 변환 규칙 + install-mac.sh 함수 설계 + 검증 절차 |
| QA-PLAN.md | PLAN 검증 — Conditional Pass + Warning 5건 |
| QA-EXECUTE.md | EXECUTE 검증 — Pass |
| STATE.md | 파이프라인 현황판 + 의사결정 로그 |
| AGENTIC-LOG.md | PM 대행 일지 — 게이트 8회 Pass, 의사결정 11건 |
| DONE.md | 본 문서 — 완료 보고 + 학습 사항 + 후속 |
