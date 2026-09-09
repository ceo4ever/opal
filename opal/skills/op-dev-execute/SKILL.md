---
name: op-dev-execute
description: |
  **코드 실행 단계 스킬**. sdlc-v2 PLAN.md의 배정된 Work items를 구현하고 검증 증거를 반환한다.
  반드시 이 스킬을 사용해야 하는 상황: 개발 오케스트레이터가 EXECUTE Work item을 워커에게 디스패치할 때.
  필수 입력: task_folder, plan_source, scenario_source, work_items, 실행 capability. 보장 출력: 코드·문서 변경, changed_files, 검증 증거.
version: 3.2
---

# op-dev-execute — 코드 실행

## 실행 계약

- 워커는 디스패치된 W만 수행한다. 병렬 배치와 파일 소유권은 PM이 PLAN `Work items`로 확정한다.
- `references/execute-guide.md`를 Read하여 공통 실행 절차를 따른다.
- 전문 에이전트는 `references/execute-specialist-guide.md`, 범용·미지정 에이전트는 `references/execute-generalist-guide.md`를 추가로 Read한다.
- 워커는 내부 서브에이전트나 다른 스킬을 자체 호출하지 않는다.

## capability 소비

PM이 디스패치 프롬프트의 `## 실행 capability`에 주입한 스킬·MCP·외부 도구만 사용한다. 고정 도구 카탈로그나 과거 문서를 근거로 capability 존재를 추정하지 않는다. 필요한 capability가 없고 기본 제공 도구로 완료 기준을 충족할 수 없으면 블로커로 반환한다.

state-tool·test-tool 명령은 선택형 capability 목록이 아니라 EXECUTE 단계의 구조적 workflow다. 해당 명령을 실행할 수 없으면 통과 처리하지 않고 환경 블로커로 보고한다.

## 수행

1. `PLAN.md` 첫 frontmatter로 sdlc-v2/legacy 입력을 판정한다.
2. sdlc-v2에서는 배정된 Work items의 담당·변경 대상·구체적 변경·선행 작업·완료 기준 연결을 실행 입력으로 사용한다.
3. 공통 가이드의 진입 검사, 구현, 자가 점검, 상태 기록 순서대로 수행한다.
4. specialist/generalist 가이드의 차이만 추가 적용한다.
5. 공통 가이드의 결과 스키마로 changed_files, 수행 W, 실제 검증 명령과 결과, blocker를 반환한다.

진행 모드의 사용자 확인·자동 승인·CLOSE 경계는 워커가 변경하지 않는다.

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | - | 초기 작성 |
| v1.1 | 2026-04-12 | Step 3-H @header 작성 규칙 추가 — code-scan 대상 확장자 파일 생성/수정 시 워커 @header 작성 의무 (109) |
| v1.2 | 2026-04-13 13:48 | PLAN.md 기반 실행 전환 — 입력 우선순위를 "PLAN.md §4 > §3 > json 폴백"으로 변경, execution-plan.json 기반 실행 섹션을 PLAN.md §4·§3.N.2 기능 루프 기반으로 재작성, FE 역할 분담의 ui-designer 호출 방법을 "PLAN.md §3.N.2 FE 화면 설계 참조"로 변경, 가드레일·품질 체크리스트에서 json 참조를 PLAN.md로 통일, 과거 태스크 폴백 규칙 서술 (114) |
| v1.3 | 2026-04-15 | 실행 주체에 전문 에이전트 체계 안내 추가 — PM이 agents.md 매핑 기반 에이전트 선택 (117) |
| v2.0 | 2026-04-23 11:39 | 3구획 구조 전환 — references/ 에 execute-specialist-guide.md / execute-generalist-guide.md 신설, SKILL.md에 에이전트 이름 매핑 테이블 삽입, 페르소나/FE 역할 분담/FE·BE MCP 테이블 섹션을 범용 가이드로 이관, 실행 컨텍스트·Step 1·PLAN.md 기반 실행 섹션 재작성 (129) |
| v2.1 | 2026-05-15 16:40 | scenario_source 입력 파라미터 추가 + Step 3-S 자가 점검 절차(TDD red-green) 신설 + EXECUTE 품질 체크리스트에 L1/L2 시나리오 PASS 항목 + L3 TEST 위임 룰 추가 (004) |
| v2.2 | 2026-06-10 10:13 | 가드레일 #6 RED 테스트 파일 수정 금지 (reward hacking 방어) (016) |
| v2.3 | 2026-06-24 | Step 3-S에 test-tool unit 명시 호출 추가 — 구현 완료 즉시 단위 테스트 도구 기반 실행 (041) |
| v2.4 | 2026-08-02 16:09 | Step 4를 "체크리스트 갱신 및 증분 저장"으로 확장 — 갱신 시점을 산출물 완결 직후로 명시(말미 일괄 갱신 금지)하고, 증분 저장·입력 축소 규율의 SSOT를 `pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 참조로 연결(문언 복제 금지) (081) |
| v2.5 | 2026-08-21 15:19 | §절대 금지 표에 #7 행 추가(git commit·push·reset·rebase 실행 금지, 이유 칼럼에 `opal-harness.md` §1 커밋 규칙 포인터) + Step 4 원격 카운트 복제 제거(개수 표기 삭제 → 개수 없는 포인터, 항목 수는 `pm/dispatch-process.md`가 소유) (097) |
| v3.0 | 2026-09-09 14:18 KST | task 111 — 신규 EXECUTE 입력을 sdlc-v2 `Work items`로 전환하고 `plan-contract-check`·`code-scan-citation-check` 진입 검증을 명시. legacy §4.2/§3/execution-plan은 읽기 폴백으로 유지하고, PLAN 체크박스·QA 결과 중복 갱신 대신 state.json/test-scenario.json 소유 계약으로 정리 |
| v3.1 | 2026-09-09 14:18 KST | 문서 W를 코드 W와 같은 EXECUTE 범위에서 수행하되 구현으로 내용이 달라지는 문서만 수정하고 참조 전용 문서는 수정하지 않도록 docs 계약 추가 (task 111/W-4) |
