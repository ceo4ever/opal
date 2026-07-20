---
type: entity
title: improve-tool
tags: [tool, improvement, cli, decision-making]
sources: [task:058]
related: [[opal-improve], [fw-inbox-collection], [memory-tool]]
created: 2026-07-20
updated: 2026-07-20
status: active
---

## 개요

PM 개선 루프의 기록 집행 도구다. 개선 후보를 결정론적으로 로컬(프로젝트 메모리) 또는 FW(프레임워크 인박스)로 분기하여 기록한다. scope에 따라 memory-tool에 위임하거나 `~/.opal/fw-inbox/`에 항목을 자기완결 형식으로 쓴다.

## 책임 (WHAT)

- **record**: 개선 후보 기록
  - `--scope <local|fw>` 필수
  - `--title` 제안 제목
  - `--body` 제안 본문
  - `--situation` 발생 맥락(retrospective/feedback/conversation)
  - `--source-task` 태스크 번호/경로
  - `--project-root` 로컬 목적지/메타 해석
  - **로컬 분기**: MEMORY.md 존재 시 memory-tool append 위임, 부재 시 graceful skip
  - **FW 분기**: `~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md` 결정론적 write — 출처메타(host·project·situation·created) 포함 자기완결
  - **반환**: `{"ok":true,"scope":...,"path":...}` 성공 / `{"ok":false,"error":"..."}` 실패 / `{"ok":true,"skipped":true}` no-op
- **list**: 항목 조회 (read-only)
  - `--scope <local|fw>` 필수
  - `--project-root` local 시 지정
  - **반환**: 메타 요약 배열
- **show**: 단일 항목 조회 (read-only)
  - `--id` 또는 `--path` 지정
  - **반환**: 항목 전문

## 설계 배경 (WHY)

PRINCIPLES "Enforce, don't just advise: if a rule must always hold, a tool gates it" — PM 개선 루프를 단순 prose 문서에서 벗어나 도구 집행으로 전환하기 위해 설계했다 (근거: TASK.md 배경). 기존 state-tool·brain-tool·memory-tool의 표준 골격(venv 래퍼 + argparse 서브명령 + JSON `"ok"` 계약)을 답습하여 복잡도를 최소화했다 (근거: PLAN.md §F-001 3.1). scope 분기는 개선이 반영될 **대상 영역**을 명확히 하기 위해 로컬/FW 2원화했으며, 로컬 scope에서 memory-tool을 재사용하여 "파일 처리·데이터 변환 작업이 필요할 때 직접 코드를 작성하기 전에 OPAL 도구를 우선 검토한다" (CONVENTIONS §도구 우선 원칙)를 준수한다 (근거: PLAN.md §F-001 3.1.2 [MUST]).

## 관계 (HOW)

- **call-by**: [[opal-improve]] — 5단계 기록 스텝에서 호출
- **call-by**: [[close-retrospective-hardstep]] — CLOSE 회고 스텝에서 호출
- **delegate-to**: [[memory-tool]] — local scope에서 MEMORY.md append 위임
- **creates**: [[fw-inbox-collection]] — FW scope에서 항목 write

## 소스 커버리지

| 항목 | 경로:줄번호 | 설명 |
|------|-----------|------|
| run.sh 래퍼 | `opal/tools/improve-tool/run.sh` | venv 진입점, OPAL .venv 호출 |
| Python 본체 | `opal/tools/improve-tool/improve_tool.py` | argparse 서브명령 디스패치, scope 분기 로직 |
| record 서브명령 | `opal/tools/improve-tool/improve_tool.py` | local/fw 분기, memory-tool 위임, fw-inbox write |
| list 서브명령 | `opal/tools/improve-tool/improve_tool.py` | 항목 메타 조회 |
| show 서브명령 | `opal/tools/improve-tool/improve_tool.py` | 항목 전문 조회 |
| fw-inbox README | `opal/tools/improve-tool/fw-inbox-README.md` | install seed, 수집소 용도·항목 스키마 안내 |
| 도구 레지스트리 | `opal/core/references/tools.md` | improve-tool 등록 (record/list/show 서브명령·용도 요약) |
