# TASK: 에이전트 아이콘 Observability + 메모리 브리핑 간소화

> 작성일: 2026-04-08 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

Observability 선언에 에이전트별 아이콘 체계를 도입하고, 부트스트랩 메모리 브리핑 절차를 간소화한다.

## 배경

현재 Observability(하네스 §5)의 행위 주체 표시가 "워커" 중심으로 설계되어 있어, QA 에이전트 등 비워커 에이전트 디스패치 시 선언이 누락된다. 또한 부트스트랩 메모리 브리핑 시 MEMORY.md 인덱스 외에 하위 파일까지 선택적으로 Read하도록 되어 있어 토큰이 낭비된다.

## 배경 분석 (대화에서 도출)

### Observability 누락 현황
- 하네스 §5 행위 주체 표시 테이블이 `⚙️ 워커 디스패치:` / `⚙️ 워커 완료:`로 정의됨
- "워커"는 하네스 §0에서 "단계 스킬을 실행하는 서브에이전트"로 정의되어, QA 에이전트 등은 용어상 해당 안 됨
- 결과적으로 Agent 도구로 디스패치되는 비워커 에이전트(QA 등)는 선언 대상에서 빠짐

### 메모리 브리핑 현황
- AGENT.md 브리핑 절차 4단계: "관련성이 높은 메모리 파일을 선택적으로 Read한다 (전부 읽지 않음)"
- MEMORY.md 인덱스만으로 브리핑에 충분하며, 하위 파일 Read는 토큰 낭비

### 에이전트 frontmatter 현황
- 현재 필드: `name`, `description`, `model`
- `icon` 필드 없음 (5개 에이전트: opal-task-agent, opal-task-qa-agent, opal-task-action-agent, op-dev-test-agent, wtm-agent)

## 확정된 설계 방향 (대화에서 합의)

1. **에이전트 아이콘 체계**: 각 에이전트 AGENT.md frontmatter에 `icon` 필드 추가. 미정의 시 디폴트 아이콘 `✨` 사용
2. **PM 표시 현행 유지**: `📋 알투[PM] 직접:`은 변경 없음. 아이콘 체계는 Agent 도구 디스패치에만 적용
3. **선언 형식**: `{icon} 디스패치: {단계명} — {설명}` / `{icon} 완료: {단계명} — {결과 요약}`
4. **메모리 브리핑 간소화**: MEMORY.md 인덱스만 읽고, 하위 파일은 읽지 않음
5. **메모리 정리는 수동**: 캡틴 요청 시에만 수행

## 요구사항

- [ ] R1: 하네스 §5 행위 주체 표시 테이블 확장 — `⚙️ 워커 디스패치/완료` 형식을 `{icon} 디스패치/완료` 형식으로 변경. 모든 Agent 도구 디스패치(워커 + QA + 기타 에이전트)에 적용되도록 확장
  - 어디에: `opal/core/references/opal-harness.md` → §5 Observability → 행위 주체 표시
  - 왜: 비워커 에이전트 디스패치가 선언에서 누락됨
  - AC: 행위 주체 표시 테이블에 (1) 에이전트 아이콘 룩업 규칙(frontmatter → 디폴트 ✨)이 명시, (2) PM 직접 행위(`📋`)는 현행 유지, (3) 모든 Agent 디스패치가 선언 대상에 포함

- [ ] R2: 에이전트 AGENT.md frontmatter에 `icon` 필드 추가 — 5개 에이전트에 `icon` 필드 추가
  - 어디에: `agents/*/AGENT.md` (5개 파일)
  - 왜: 아이콘 체계 지원을 위한 frontmatter 확장
  - AC: 5개 에이전트 AGENT.md에 `icon` 필드가 존재하고 유효한 이모지 값이 설정됨

- [ ] R3: AGENT.md 브리핑 절차 간소화 — 4단계("관련성이 높은 메모리 파일을 선택적으로 Read") 삭제, 5단계 번호를 4로 조정
  - 어디에: `opal/core/AGENT.md` → 프로젝트 메모리 브리핑 → 절차
  - 왜: MEMORY.md 인덱스만으로 브리핑에 충분, 하위 파일 Read는 토큰 낭비
  - AC: 브리핑 절차에 하위 파일 Read 단계가 없고, MEMORY.md 인덱스만 읽도록 되어 있음

## 제약 조건

- 소스 파일만 수정 (`opal/core/`, `agents/`). `~/.opal/` 배포본 직접 수정 금지 (확정 기준 #2)
- PM 직접 행위 표시(`📋 알투[PM] 직접:`)는 변경하지 않음
- 기존 오케스트레이터 SKILL.md의 Observability 참조(`하네스 §5 참조`)는 변경 불필요 (하네스 공통에서 해결)

## 기술 스택

- Markdown 문서
- YAML frontmatter

## 관련 문서

- `opal/core/references/opal-harness.md` — 하네스 공통 (§5 Observability)
- `opal/core/AGENT.md` — 에이전트 정의 + 부트스트랩 절차
- `agents/*/AGENT.md` — 에이전트 frontmatter 정의
