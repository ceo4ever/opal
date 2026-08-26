---
type: concept
title: 커뮤니티 스킬 basename alias 매칭 — 벤더 무관 호출
tags: [architecture, community-skills, ux, routing]
sources: [task:064]
related: [community-skill-installation-architecture]
created: 2026-07-17
updated: 2026-07-17
status: active
---

## 개요

`//` 호출 시 커뮤니티 스킬을 basename으로 매칭하도록 확장했다. `//pdf` 같은 단축 호출이 vendor 무관하게 `anthropics/pdf`를 자동으로 찾는다. basename 충돌 시(드문 경우) 후보 목록을 제시한다.

## 결정 배경 (WHY)

1. **매칭 비대칭** (근거: task:064 D2) — `//pdf`는 triggers 정규식 폴백으로 우연히 매칭되나 `//pdf 문서 만들어줘`는 found:false로 실패. 명시적 basename alias 경로 부재.

2. **불편한 호출** — `//anthropics/pdf`처럼 vendor를 항상 지정해야 하는 번거로움.

3. **향후 호환성** — basename 충돌은 현재 0개지만 향후 커뮤니티 확대 시 안전장치 필요.

## 결정 내용

### 매칭 우선순위 (3단계)

```
1. 정식명 (skills.name) — 예: "anthropics/pdf"
2. alias (skills.alias 필드) — 사용자 정의 별칭
3. basename (source_repo 마지막 경로) — 예: "pdf" → anthropics/pdf
```

### basename 충돌 정책

**현황**: registry 32개 basename 전수 유일 (충돌 0)

**충돌 발생 시**: 단일 자동 선택 대신 **후보 목록 제시**

```json
{
  "found": false,
  "ambiguous": true,
  "candidates": [
    { "name": "vendor1/skill", "install_method": "clone-copy" },
    { "name": "vendor2/skill", "install_method": "clone-copy" }
  ]
}
```

**호출자 처리**: ambiguous 감지 시 명시 호출 권고 (`//vendor1/skill`)

### 실제 구현

**함수**: `matchByAlias(skills, alias)` (근거: `opal/tools/skill-registry/skill-registry.js:129-135`)

**처리 분기**:
1. 정식명 정확 매칭 → 반환
2. alias 포함 검사 → 반환
3. basename 매칭 → 단일 or ambiguous
4. 무매칭 → null

**matchCommand**: ambiguous 지원으로 다형 반환 처리 (근거: `skill-registry.js:199`)

## 영향 범위

- skill-commands.md 호출 경로 (`//` 커맨드) — basename으로도 발견 가능 (근거: task:064 F-3)
- skill-manager 검색 절차 — ambiguous 후보 제시 (근거: task:064 §2)
- registry basename 유일성 정책 — 설계 단계에서 충돌 확인

## 관련 페이지

- [[community-skill-installation-architecture]] — vendor 중첩 레이아웃
