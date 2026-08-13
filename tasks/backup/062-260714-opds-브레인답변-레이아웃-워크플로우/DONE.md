# DONE: 브레인 답변 생성 내부 워크플로우 — content-driven 레이아웃 선택

> 완료일: 2026-07-14 | 스킬: opds (agentic) | 상태: 완료

## 작업 요약

`opal-brain` query 답변 생성을 **6단계 내부 워크플로우**(질의 분해 → 지식 수집 → 구조 분석 → 레이아웃 설계 → 내용 합성 → 자기검증)로 구조화하고, 레이아웃을 질의 유형이 아니라 **주입된 하위 문서의 실제 관계 구조에서 도출**(content-driven)하도록 `opal/skills/opal-brain/SKILL.md §답변 구조`를 재작성했다. 캡틴 정성 피드백을 반영해 표현·가독성 규율(항목 내부 다문장 분해·1라인 1내용)도 추가했다.

## 최종 산출물

| 산출물 | 경로 |
|--------|------|
| TASK.md | `tasks/062-260714-opds-브레인답변-레이아웃-워크플로우/TASK.md` |
| PLAN.md | `동 폴더/PLAN.md` |
| TEST-SCENARIO.md | `동 폴더/TEST-SCENARIO.md` (All Pass) |
| AGENTIC-LOG.md | `동 폴더/AGENTIC-LOG.md` |
| DONE.md | `동 폴더/DONE.md` |

## 변경 파일

| 파일 | 변경 |
|------|------|
| `opal/skills/opal-brain/SKILL.md` | 수정 — §답변 구조 재작성(6단계·6축·5후보·판정·가드3종·2예시·가독성 규율) + §변경이력 v1.8 + frontmatter `version:"1.5"→"1.8"` (53+/6-) |
| `dashboard/backend/adapters/opbr_adapter.py` | 무변경 (SSOT=SKILL.md 확인만) |
| 배포본 `~/.opal/skills/opal-brain/SKILL.md` | `install-mac.sh` 재배포로 반영 |

## 핵심 결정

1. **레이아웃은 content-driven** — 질의 유형(고정 택소노미)이 아니라 주입된 하위 문서의 실제 관계 구조(여정/병렬/계층/조건)에서 도출한다. "방문형 캠페인 정책"을 표면상 표로 단정한 오류가 계기.
2. **6단계 워크플로우, 단일 세션 호출 1회** — 단계 증가가 claude subprocess 호출 증가로 이어지지 않는다(콜드 ~56s latency 방어, 가드 G2).
3. **관측 축 6종 → 후보 5종 매핑 판정** — 여정/순서성→Flow, 값 보유→표, 병렬성→그룹핑, 주제 수→복합, 분량→Flat. 동점 시에만 tie-break(더 단순한 쪽). 전면 가중합 스코어링 미채택(self-scoring 편향).
4. **불변 가드 3종** — G1 비출력 내부 사고(1~4단계 미노출), G2 호출 1회, G3 read-only JSON 이스케이프 계약 유지.
5. **표현·가독성 규율** — 항목 내부 다문장은 하위 불릿으로 분해, 1라인 1내용(전 후보 공통). 캡틴 정성 피드백 반영.
6. **SSOT 한 곳** — `SKILL.md §답변 구조`가 대화형 `ask`·비대화형 `--read-only` 공통 SSOT. adapter는 얇은 프록시라 무변경.

## 검증 결과

- **L1 문서 구조(S-1~S-5)**: All PASS — 6단계·6축·5후보·판정·가드3종·2예시·공통적용·앵커무결성·v1.8/version·adapter 무변경.
- **L2 read-only 스모크(S-6)**: PASS — brain 146p 대상 실행. JSON 펜스 1개·펜스 밖 raw 마크다운 0·citations 3개 유실 0·claude 호출 1회·G1 내부단계 누출 0. 계약 비파손 확인.
- **L3 정성(S-7)**: 실 커머스 brain 답변이 여정 Flow(5단계)로 도출됨을 캡틴이 관측 — 워크플로우 작동 확인(근사). 도메인 brain 정량 검증은 제한.

## 후속

- **커밋 대기** — 커밋은 미수행(캡틴 지시 대기). 대상: `opal/skills/opal-brain/SKILL.md`.
- **S-7 정량 관찰(선택)** — 커머스 도메인 프로젝트에서 성격이 다른 질의로 레이아웃 일관성 추가 확인 가능.
