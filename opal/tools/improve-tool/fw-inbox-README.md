<!--
@header {
  "module": "fw-inbox-readme",
  "layer": "reference",
  "domain": "opal-pipeline",
  "description": "~/.opal/fw-inbox/ 런타임 수집 디렉토리 안내 — install이 create-if-absent로 이 파일을 시드한다(058 F-002/F-005).",
  "exports": ["fw-inbox 용도", "항목 스키마"]
}
-->

# fw-inbox — 프레임워크 개선 제안 수집소

이 디렉토리는 `improve-tool record --scope fw`가 결정론적으로 write하는 **전역 수집소**다.
로컬(프로젝트 한정) 개선과 달리, 여기 쌓이는 항목은 프레임워크 소스(SSOT — 스킬/도구/참조문서/하네스)에
반영될 후보다. 수집만 하며, 소스 반영은 소유자/PM이 검토 후 별도로 수행한다.

## 이 디렉토리에 직접 쓰지 않는다

항목 write는 반드시 `improve-tool record --scope fw`를 경유한다. 사람이 직접 파일을 추가/편집하지 않는다.

## 항목 파일명 규칙

```
{YYYYMMDD-HHmmss}-{host}-{slug}.md
```

정렬 가능(시간순) + 충돌 회피(호스트+슬러그).

## 항목 스키마 (자기완결 — 이 파일만으로 출처·맥락·제안이 재구성 가능)

```markdown
---
type: fw-improvement
title: <제안 제목>
created: <YYYY-MM-DD HH:mm KST>
host: <hostname>                    # 출처 메타 — 어느 PC
project: <프로젝트명>                # 출처 메타 — 어느 프로젝트
project_root: <절대경로>
source_task: <NNN | task-path | "">
situation: <retrospective | feedback | conversation>   # 발생 맥락 유형
status: inbox
---

## 제안 요약
<1-2문장>

## 상황 (Context)
<어떤 상황에서 이 개선이 필요하다고 판단했는지>

## 제안 내용
<구체적 개선 — 어느 프레임워크 소스 SSOT를 어떻게 바꿔야 하는지>
```

필수 출처 메타 4종(자기완결성 — H-8): `host` · `project` · `situation` · `created`.

## 근거

`tasks/058-260713-opd-학습루프-도구화-개선수집/PLAN.md` §3.2.2 (F-002 fw-inbox 항목 스키마).
