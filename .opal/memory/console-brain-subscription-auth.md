---
name: console-brain-subscription-auth
description: OPAL Console 브레인 질의(및 향후 LLM 기능)는 종량제 API가 아니라 각 사용자의 Claude 구독으로 작동해야 함 — 로컬 Claude Code CLI(claude -p) 경유
metadata:
  type: project
---

OPAL Console의 프로젝트 브레인 질의 기능(태스크 036, Phase 1 MVP)은 **각 사용자의 Claude 멤버십 구독으로 작동해야 한다** (캡틴 지시, 2026-06-22).

**금지**: Anthropic 종량제 API 경로 — API 키, `ANTHROPIC_API_KEY`, `ant auth login` OAuth 프로필. 모두 토큰 종량 과금이라 부적합.

**채택 방식 (캡틴 정정 2026-06-22, 아키텍처 B)**: backend(FastAPI)가 **로컬 `claude` CLI로 실제 opbr 스킬을 구동**한다 — `claude -p "//opbr ask <질문>" --output-format json`(+세션 플래그) → **OPAL 프레임워크·opbr 스킬이 로드되어** 실제 brain query를 수행, 사용자 Claude Code 구독으로 실행. backend는 opbr를 재구현하지 않는 얇은 프록시(DRY/SSOT). 자격증명은 Claude Code가 Keychain에서 자체 관리(우리가 토큰 미취급). **`--safe-mode`(=opbr 미로드) 사용 금지** — opbr가 작동해야 하므로.

**관리형 지속 세션**: 데몬이 BrainSession 관리 — 지연 프라임(서버 재실행 시 핸들 폐기→다음 질의가 1회 부팅) + 5트리거 리셋(재실행·컨텍스트 임계·유휴·크래시·수동 "새 대화"). 매 질의 재부팅 회피. 방식 B1(`--resume`) vs B2(상주 `stream-json` 프로세스)는 스파이크 지연 실측으로 확정. headless opbr는 brain 쓰기 금지(질의 전용).

**단계화**: Phase 1 스파이크(인증+질의+OPAL/opbr 세션→답변 최소 E2E) 먼저 빠르게 검증 → 캡틴 OK → Phase 2+ 나머지(FE·세션 리셋·격리·테스트·docs).

**진행 상태 (2026-06-22 일시중단, 다음 세션 재개)**: 태스크 `tasks/036-260622-opd-브레인질의-콘솔연동/` (opd, agentic). Phase 1 스파이크·Phase 2 구현 + 라이브 fix 다수 완료(권한 allowedTools·프로젝트별 cwd 격리·**대화별 세션**(conversation_id↔claude핸들 분리, 콜드마다 새 uuid)·프로젝트 필수·프로젝트별 연동배지·새대화 즉시 재프라임·낙관적 업데이트(제출 즉시 이력+답변대기·오라우팅 방지)). 코드 단위검증 완료(BE 211·FE 89·실claude 0). **재개 지점**: 캡틴 콘솔 재배포 → 낙관적업데이트 라이브 재테스트 → 통과 시 CLOSE(JP주석 정리·DONE.md·brain ingest). 상세 이력: 해당 태스크 `AGENTIC-LOG.md`(엔트리 1~56). 핵심 설계: claude `--safe-mode` 금지(opbr 로드 필요)·`--allowedTools "Bash,Read,Grep,Glob"`(콤마형, 라이브검증)·세션=대화별·이력=브라우저 localStorage. [[feedback_commit_direct_main]]

**Why**: OPAL은 Claude Code 위에서 동작하는 프레임워크이며, 사용자는 이미 구독 로그인 상태다. 종량 과금 없이 구독 자원을 그대로 활용하는 것이 캡틴 요구이자 OPAL 철학(Claude Code 기반)과 정합.

**How to apply**: Console에 LLM 합성이 필요한 기능을 추가할 때 Anthropic API SDK를 끌어들이지 말고, 로컬 `claude -p` 서브프로세스(어댑터 계층 격리)로 구현한다. "로그인 체크" = `claude` CLI 가용·인증 여부 확인. 읽기전용 위반(LLM 호출)은 해당 라우터에만 격리한다. 관련: [[feedback_deploy_boundary]]
