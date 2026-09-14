<!--
@header {
  "module": "opal-self-pm-question-loop",
  "layer": "reference",
  "domain": "opal-pipeline",
  "description": "opal-self-pm 루프가 매 턴 사용자에게 제시하는 질문 1개의 5요소 구성과, 시작·요구 발견·설계 결정·수정 직전·범위 변경·완료 직전 각 시점에서 조회할 원천을 규정한다.",
  "exports": ["질문 1개의 5요소", "시점별 문서·지식 조회", "이 프로젝트에서의 구체화"]
}
-->

# question-loop — 질문 1개와 시점별 조회

> 소유: `opal-self-pm/SKILL.md` §3.

## 1. 질문 1개의 5요소

사용자에게는 결정할 질문을 **한 개씩** 제시한다. 매 질문은 아래 5요소를 모두 포함한다.

| # | 요소 | 내용 |
|---|---|---|
| 1 | 현재 결정해야 하는 한 가지 | 이번 턴에 답을 받아야 할 단일 결정 사항 |
| 2 | 선택지 또는 답변 범위 | 사용자가 고를 수 있는 구체적 선택지 (또는 자유 응답 범위) |
| 3 | PM 권고 답안 | PM이 조회·근거로 판단한 권고 값 |
| 4 | 권고 이유와 주요 trade-off | 왜 그 답을 권고하는지, 다른 선택지 대비 trade-off |
| 5 | 다음 조회 또는 작업 | 이 답변에 따라 달라지는 다음 조회 대상 또는 착수할 작업 |

사용자 답변 뒤 PM은 관련 원천을 조회하고, 확인된 사실·결정·남은 쟁점을 짧게 정리한 다음 다음 질문을 한다. **이미 답한 질문을 반복하지 않는다.**

## 2. 시점별 문서·지식 조회

모든 문서를 처음부터 전량 읽지 않는다. 결정 시점에 필요한 원천을 선별하되, 아래 각 시점에서 다음 영역의 영향 여부는 빠짐없이 판정한다.

| 시점 | 우선 조회 | 목적 |
|---|---|---|
| 시작 | `docs/PROJECT.md`, project memory brief(`memory-tool show --boot-brief` 결과), 관련 brain(`.opal/brain/` 존재 시 `brain-tool search "<키워드>"`), 코드 구조(`code-scan scan`/`domain`/`search`) | 프로젝트 좌표와 과거 결정 확인 |
| 요구 발견 | 기획서, 정책서, 사용자 흐름, 현행 산출물 | 목표·제약·용어 확정 |
| 설계 결정 | 아키텍처, 인터페이스, 데이터 모델, 관련 코드 | 소비자와 변경 영향 확정 |
| 수정 직전 | `docs/CONVENTIONS.md`, `docs/SECURITY.md`, 운영·배포 제약 | 구현 규칙과 위험 확인 |
| 범위 변경 | 새 범위에 맞춰 원천 재선별 | 누락된 영향 재평가 |
| 완료 직전 | 변경 파일과 관련 docs·brain·memory·코드맵(`code-scan`) | 낡은 원천 동기화 |

각 영역은 `update` 또는 `no-op + 근거`로 판정한다(완료 직전 판정의 8영역 세부는 `references/knowledge-sync.md` 참조). "관련 없어 보임" 같은 무근거 생략은 허용하지 않는다.

## 3. 이 프로젝트에서의 구체화

- "관련 brain" 조회는 `.opal/brain/` 디렉토리가 존재할 때만 수행한다. 부재 시 이 조회 항목은 건너뛰되, §완료 직전 knowledge_impact 판정에서 brain 영역을 `no-op + 근거: brain 미초기화`로 기록한다.
- "project memory brief" 조회는 `~/.opal/tools/memory-tool/run.sh show --boot-brief`로 수행한다.
- "코드 구조" 조회는 `~/.opal/tools/code-scan/run.sh scan`/`domain`/`search` 중 필요한 서브커맨드를 선택한다(`header-rules.md` §code-scan 활용 가이드의 시점·폴백 규칙을 그대로 따른다).
