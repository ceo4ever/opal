# TASK: 브레인 미실체 지식 등록 차단 게이트

> 작성일: 2026-07-22 | 작업 유형: 개선 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청 (대화)
> 출력: TASK.md

## 작업 목표

브레인(지식 위키)에 **미실체 지식**(개선사항·오류·향후 계획·미확정 설계 등 아직 실재하지 않는 것)이 등록되는 것을 방지하는 장치를 추가한다. 확정·실재하는 지식(사용자가 판단해 지식화하는 query/ask 산출물 포함)은 그대로 허용한다.

## 배경

현재 브레인 ingest에는 "미실체 지식"을 걸러내는 장치가 없다. op-brain-ingest §STEP3 제외 기준은 "오타·trivial·되돌려진·임시 변경"만 다루며, "미래·개선·오류·미확정" 부류는 제외 목록에 없다 (`opal/skills/op-brain-ingest/SKILL.md`). brain-tool에도 미실체 콘텐츠를 거르는 도구 게이트가 없다. 그 결과 아직 구현·확정되지 않은 설계가 `concept`/`status: active`로 등록되어 "확정 안 된 것이 마치 지식처럼 작동"한다.

## 배경 분석 (대화에서 도출)

실제 사례로 pointail 프로젝트의 `/.opal/brain/pages/concept/direct-delivery-mission-design.md`를 검토했다. 이 파일이 문제를 그대로 증명한다:

- 본문이 스스로 미완료임을 명시하는데도 `status: active`다 — "구현 영향 범위 (HOW) — 아직 미착수, 설계 기록 단계"(§해당 파일), "미확정 이슈", "이 결정 기록만으로 착수되지 않는다 — 별도 opd 승인이 필요하다".
- 유입 경로가 CLOSE 자동 ingest가 아니라 `opbr 질의` 세션이다 — `sources: task:직접배송 설계 검토 (opbr 질의, 2026-07-21)`. query 모드는 원래 read-only이고 등록 허용은 `draft term`뿐인데(`opal/skills/opal-brain/SKILL.md` STEP query 진입점③), concept/active가 만들어졌다.
- 근본 원인 두 가지: (1) "미실체 → 등록 금지"를 강제하는 판별 기준 자체가 SSOT에 없음, (2) brain-tool `search` 의 draft 필터는 `term` 타입에만 적용되어(`opal/tools/brain-tool/brain_tool.py:620`) 설령 draft로 넣어도 concept/entity/flow는 답변에 노출됨.
- 즉 LLM이 미완료임을 알면서도 등록한 전례가 있으므로, 규칙(prose)만으로는 새며 도구 게이트가 필요하다 (헌법 "enforce, don't advise" — `~/.opal/PRINCIPLES.md` Core Stance).

> pointail 파일 자체의 정리는 **다른 프로젝트 소관**으로 이 태스크 범위가 아니다(별건). 이 태스크는 ai-framework 프레임워크에 재발 방지 장치를 추가한다.

## 확정된 설계 방향 (대화에서 합의)

캡틴과 합의한 경계와 2층 장치:

1. **경계 = 내용의 실체 유무** (모드가 아님). query/ask에서 사용자가 판단해 기존 지식·소스 코드를 지식화하는 흐름(synthesis 포함)은 정당 → **그대로 유지**. 막을 대상은 "아직 실재하지 않는 것"(개선·오류·향후 계획·미확정 설계)뿐이다.
2. **1층 — 판별 기준 명문화 (WHAT 규칙)**: op-brain-ingest §STEP3 + opal-brain ingest 절에 "미실체 제외" 기준을 SSOT로 추가한다. 미실체 지식은 brain 아니라 memory로 보낸다(활용은 memory에서).
3. **2층 — 도구 게이트 (결정론적 backstop)**: brain-tool이 미실체 마커를 감지해 `add-page`를 **거부**(overridable — `--force` + note)하고, `lint`에 신규 kind를 추가해 이미 등록된 미실체 페이지를 소급 검출한다. op-brain-ingest는 add-page 실패를 skip-and-continue로 처리하므로 CLOSE 차단 위험 없음.

## 명확화 결과

> TASK 4요소를 잠근다. 각 요소는 확정값 또는 명시적 "N/A: <사유>"로 채운다 (공란·TBD 금지).

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | 브레인에 미실체 지식(개선·오류·향후·미확정 설계)이 등록되는 것을 방지하는 2층 장치(판별 기준 명문화 + 도구 게이트) 추가. 실재 지식은 그대로 허용 | - | `opal/skills/op-brain-ingest/SKILL.md`, `opal/tools/brain-tool/brain_tool.py` |
| 범위 | **포함**: op-brain-ingest §STEP3 미실체 제외 기준 추가 / opal-brain ingest 절 SSOT 정합 / brain-tool add-page 미실체 거부 게이트(overridable) / lint 신규 kind 소급 검출 / 테스트 / install 재배포. **제외**: query·ask의 synthesis 지식화 흐름 변경 / 기존 draft-term 메커니즘 변경 / 미실체→memory 자동 이관 / 타 프로젝트(pointail) 파일 정리 | 마커 감지 방식·add-page 세부 정책 → PLAN | `opal/skills/opal-brain/SKILL.md` |
| 제약 | 배포 경계(`~/.opal/` 직접수정 금지, 소스 수정 후 install) / 하위호환(기존 페이지·add-page 호출 무손상, 기존 active concept 자동 거부·삭제 금지 — lint 검출까지만) / enforce-don't-advise(규칙+도구 backstop) / 마커 오검출 최소화 / 변경이력·@header 규칙 준수 | - | `.opal/AGENT.md` 금지사항, `PRINCIPLES.md` |
| 완료기준 | ①op-brain-ingest·opal-brain에 미실체 제외 기준 SSOT 명문화(헤딩+기준 행 존재) ②add-page가 미실체 마커 감지 시 거부(--force 우회 가능) ③lint 신규 kind로 미실체 페이지 검출 ④pointail 유형 콘텐츠 거부·검출 + 정상 지식 통과 회귀 테스트 All Pass ⑤install 재배포 완료 | - | - |

## 요구사항

- [ ] **R-1 미실체 제외 기준 명문화 (SSOT)** — 무엇을: op-brain-ingest §STEP3 제외 기준 표에 "미실체(미래·개선·오류·미확정 설계)" 행 추가 / 어디에: `opal/skills/op-brain-ingest/SKILL.md` §STEP3 제외 기준 / 왜: 판별 기준 부재가 근본 원인(배경 분석) / AC: 제외 기준 표에 미실체 행이 존재하고, 예시(개선사항·오류·향후 계획·미확정 설계)가 명시된다
- [ ] **R-2 opal-brain ingest 절 정합** — 무엇을: ingest 관련 절에 R-1 기준을 SSOT 재사용으로 반영(별도 정의 금지, op-brain-ingest §STEP3 참조) / 어디에: `opal/skills/opal-brain/SKILL.md` STEP ingest / 왜: 두 진입점(CLOSE·//opbr)이 동일 기준을 쓰게 / AC: opal-brain ingest 절이 op-brain-ingest §STEP3를 SSOT로 참조하고 미실체 제외를 언급한다
- [ ] **R-3 add-page 미실체 거부 게이트** — 무엇을: `add-page`가 본문 미실체 마커 감지 시 신규 에러코드로 거부, `--force`+note로만 우회 / 어디에: `opal/tools/brain-tool/brain_tool.py` (add-page 경로) / 왜: 규칙만으론 샘 → 도구 강제 / AC: 미실체 마커 포함 페이지 add-page 시 `ok:false`+신규 에러코드 반환, `--force` 시 통과+경고 기재
- [ ] **R-4 lint 미실체 소급 검출** — 무엇을: `lint`에 신규 kind(예: `speculative`) 추가 / 어디에: `opal/tools/brain-tool/brain_tool.py` (lint 경로) / 왜: 이미 등록된 미실체 페이지 검출 / AC: 미실체 마커 포함 기존 페이지가 `lint` issues에 신규 kind로 나타난다
- [ ] **R-5 테스트** — 무엇을: pointail 유형(미착수·미확정 설계) 콘텐츠가 add-page 거부+lint 검출됨 / 정상 concept(실체 있는 지식)은 통과함을 증명 / 어디에: `opal/tools/brain-tool/tests/` / 왜: 완료 = 검증된 동작(헌법 §4) / AC: 신규 테스트 통과 + 기존 테스트 회귀 0
- [ ] **R-6 install 재배포** — 무엇을: 소스 수정 후 install로 `~/.opal/` 재배포 / 어디에: install 스크립트 / 왜: 배포 경계 준수 / AC: 배포된 brain-tool·SKILL이 소스와 일치

## 제약 조건

- **배포 경계**: `~/.opal/` 직접 편집 금지. `opal/` 소스 수정 후 install 재배포 (`.opal/AGENT.md` 금지사항).
- **하위호환**: 기존 brain 페이지·`add-page` 정상 호출을 깨지 않는다. 기존 `active` concept를 자동 거부·삭제하지 않는다(lint 검출까지만).
- **enforce, don't advise**: 규칙(LLM 적용)에만 의존하지 않고 도구 게이트로 backstop한다 (`PRINCIPLES.md` Core Stance).
- **마커 오검출 최소화**: 정상 지식이 미래 표현을 단순 언급하는 경우 하드거부하지 않는다(구조적 신호 우선 — 구체안 PLAN).
- **추적성**: 변경이력 표 행 추가(KST+태스크번호), 코드 @header 규칙 준수.

## 기술 스택

- Python 3 (brain-tool — `opal/tools/brain-tool/brain_tool.py`, PyYAML)
- Markdown SKILL 문서 (op-brain-ingest, opal-brain)
- pytest (brain-tool 테스트)
- bash install 스크립트 (배포)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | op-brain-ingest SKILL | `opal/skills/op-brain-ingest/SKILL.md` | §STEP3 제외 기준 SSOT — R-1 대상 |
| D-2 | 소스 | opal-brain SKILL | `opal/skills/opal-brain/SKILL.md` | STEP ingest / query 진입점③ — R-2 대상 |
| D-3 | 소스 | brain_tool.py | `opal/tools/brain-tool/brain_tool.py` | add-page/lint/search(draft 필터 620행) — R-3·R-4 대상 |
| D-4 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | enforce-don't-advise 원칙 근거 |
| D-5 | 소스 | brain-tool tests | `opal/tools/brain-tool/tests/` | R-5 테스트 추가 위치 |

## 미확정 사항 (PLAN에서 결정)

- **M-1 미실체 마커 감지 방식** — 섹션 헤딩 토큰 스캔("미착수/미확정/향후/TODO" 등) vs 전문 밀도 vs frontmatter 플래그. 오검출 최소화 관점에서 방식·마커 사전 확정.
- **M-2 add-page 거부 정책 세부** — 신규 에러코드명, `--force` 우회 시 경고 기재 위치·형식, 거부 대상 판정 임계.
- **M-3 draft-term 기존 경로** — 이번 범위 유지(변경 없음) 확인. (opal-brain query 진입점③ 그대로.)
- **M-4 미실체→memory 이관** — 이번 범위 제외(향후) 확인. 이번엔 차단/검출까지만.
