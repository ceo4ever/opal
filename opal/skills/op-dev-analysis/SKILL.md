---
name: op-dev-analysis
description: |
  **설계 전 코드·문서 사실 확인 단계 스킬**. TASK.md에서 PLAN을 바꿀 질문만 조사하고 변경·회귀 경계와 핵심 가정을 ANALYSIS.md로 반환한다.
  반드시 이 스킬을 사용해야 하는 상황: opal-pilot-dev가 ANALYSIS 단계를 워커에게 디스패치할 때.
  필수 입력: task_folder, TASK.md, PM이 선별한 프로젝트 문서와 실행 capability. 보장 출력: ANALYSIS.md.
---

# op-dev-analysis — 설계 전 사실 확인

## 입력 분기

1. TASK 첫 frontmatter가 `template: sdlc-v2`이면 `references/analysis-guide.md`를 Read하고 신규 ANALYSIS를 작성한다.
2. legacy TASK에 기존 ANALYSIS가 있으면 재작성하지 않고 기존 산출물을 반환한다.
3. legacy TASK에 ANALYSIS가 없을 때만 `references/analysis-legacy-guide.md`를 Read하여 기존 gate 호환 형식을 작성한다.

신규 경로에서는 legacy guide, persona, 기술 스택 카탈로그를 읽지 않는다.

## 실행 계약

- PM이 `docs/PROJECT.md` 레지스트리에서 선별해 주입한 프로젝트·기획·설계 문서와 필요한 구간만 확인한다. 주입되지 않은 문서군을 전체 탐색하지 않는다.
- PM이 `## 실행 capability`에 주입한 스킬·MCP·외부 도구만 사용한다. 미제공 capability의 존재를 추정하거나 추천 목록을 만들지 않는다.
- TASK의 확정된 Problem/outcome/scope/AC/C를 다시 도출하지 않는다. 사실 오류나 충돌만 근거와 함께 보고한다.
- 산출물에는 소스코드 원문을 복제하지 않고 `경로:줄번호`와 필요한 짧은 근거만 기록한다. 상세 근거 규칙은 `opal/core/references/harness/citation-rules.md`를 따른다.

## 완료

ANALYSIS.md를 저장한 뒤 다음만 확인한다.

- sdlc-v2 출력이 `Findings / Change boundary / Critical assumptions / Handoff` 네 절만 사용한다.
- 각 조사가 PLAN 결정이나 변경·회귀 경계를 실제로 바꾼다.
- 확인하지 못한 실제 연동·권한·데이터 가정은 한계 또는 착수 차단으로 남아 있다.
- 프로젝트 문서 전문, 기술 스택 목록, capability 카탈로그, QA 매트릭스를 만들지 않았다.

반환:

```text
ANALYSIS 완료: {task_folder}/ANALYSIS.md
착수 차단: {없음 | 항목}
```

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2025-XX-XX | 초판 |
| v1.2 | 2026-04-15 | 실행 주체에 전문 에이전트 체계 안내 추가 (117) |
| v1.3 | 2026-04-17 | §0 참조 문서 테이블 신설 + §1.1/§5 근거 컬럼 추가 (유형+외부URL 지원) + citation-rules 적용 (123) |
| v1.4 | 2026-04-24 | citation-rules 트리거 1줄 주입 — SSOT + Trigger 패턴 (130) |
| v1.5 | 2026-08-21 | 확정 입력 소비 규약(재도출 금지·3값 판정·사실오류 경로) 신설 + `## 확정 입력 판정` 표 템플릿 + 원문 블록 금지 포인터 추가 (098) |
| v1.6 | 2026-08-23 12:41 | 분석 품질 체크리스트 본문 삭제 → `analysis-core.md` §7 포인터로 교체(H-10) · 통일 형식에 §7 지정 분석 질문 Q표(권장)·§8 다음 단계 입력 핸드오프 표+「PLAN 결정 필요」 분리 표 실물 섹션 추가 · 확정 입력 판정값에 `승계` 추가(4값 판정) (100) |
| v1.7 | 2026-08-24 22:39 | §1.1 템플릿 헤더 4열→5열 개정(`영역` 선두 추가, `파일`→`경로`, `변경 필요`→`변경 유형`) + 앞 4열 승계 계약·값 도메인 주석 추가 + §8 표제 하단에 역할 한정 주석 추가(3열 헤더 불변) + 확정 입력 판정값을 구형 4값(`유효`/`승계`/`수정필요`/`사실오류`)에서 결정 계열(`해당없음(결정)`/`사실오류`)·사실 계열(`유효(대조 확인)`/`수정필요`/`사실오류`) 2계열로 교체, 구 `승계` 값은 `유효(대조 확인)`로 흡수 + `확정 입력 소비 규약`에 소급 미적용 규율 추가(신규 태스크부터 적용, `citation-rules.md` §5) + 템플릿 코드펜스 내 판정값 도메인 주석에서 중복 폐지 안내 제거(본문 안내로 일원화) (101) |
| v1.8 | 2026-09-09 14:17 | sdlc-v2 신규 ANALYSIS 산출 계약을 `Findings/Change boundary/Critical assumptions/Handoff` 4섹션으로 단순화하고, 구형 확정 입력 판정·파일표·기술 컨텍스트·QA 매트릭스는 legacy 입력 해석용으로 축소 (111) |
| v1.9 | 2026-09-09 14:17 | TASK frontmatter 기준 출력 분기 명확화: sdlc-v2는 4섹션 신규 출력, legacy는 기존 ANALYSIS 소비 우선 및 산출물 부재 시 legacy gate 호환 형식 생성 허용 (111) |
| v1.10 | 2026-09-09 14:30 | sdlc-v2에서도 `docs/PROJECT.md` 문서 레지스트리와 작업 도메인 문서·기획·설계 산출물 확인 계약을 유지하고, 기술 컨텍스트 포괄 수집 금지 및 문서 변경 후보를 `Change boundary`에 기록하도록 명시 (111) |
| v1.12 | 2026-09-09 KST | SKILL을 입력 분기·실행 계약·완료 조건으로 축소하고 신규 경로의 persona·기술 컨텍스트 중복 로드를 제거 (111) |
| v1.11 | 2026-09-09 16:08 | 고정 활용 MCP 표를 제거하고 PM dispatch가 주입한 런타임 capability만 사용하도록 전환 (111) |
