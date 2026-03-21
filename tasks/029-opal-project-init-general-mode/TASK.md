# TASK: opal-project-init 일반/개발 프로젝트 분기 + PM 공통 인터뷰

> 작성일: 2026-03-21 | 작업 유형: 기능 개선

## 작업 목표

opal-project-init에서 프로젝트를 "일반(비개발)"과 "개발"로 먼저 분기하여, 일반 프로젝트는 `.opal/AGENT.md` + `.opal/MEMORY.md`만 생성하고 끝내도록 한다. PM 프로필 인터뷰(페르소나, 의사결정 원칙, Phase)는 양쪽 모두 공통으로 수행한다.

## 배경

### 현재 문제

- opal-project-init은 개발 프로젝트만 상정 (기술 스택, 포트, DB 등 개발 전용 질문)
- OPAL 프레임워크 자체, 기획 문서 프로젝트, 비개발 프로젝트에는 사용 불가
- 개발 프로젝트도 PM 페르소나 인터뷰가 빠져 있어, `.opal/AGENT.md`가 기술 정보만 담김

### 캡틴과 합의한 구조

```
Step 0: 프로젝트 카테고리
        │
   ┌────┴────┐
   일반       개발
   ↓          ↓
   PM 공통    PM 공통 인터뷰
   인터뷰     + 기술 인터뷰
   ↓          + (신규/기존 분기)
   .opal/     ↓
   끝         docs + platform + .opal/
```

### 인터뷰 항목 정의

| 인터뷰 항목 | 일반 | 개발 |
|------------|------|------|
| 프로젝트명, 설명 | O | O |
| 도메인/분야 | O | O |
| 페르소나 (어떤 관점으로 사고?) | O | O |
| 의사결정 원칙 | O | O |
| 현재 Phase | O | O |
| 기술 스택, 포트, DB | - | O |
| 아키텍처, 특별 기능 | - | O |

## 요구사항

- [ ] Step 0에서 "일반/개발" 분기를 신규/기존 분기보다 먼저 수행
- [ ] 일반 프로젝트: PM 공통 인터뷰 → `.opal/AGENT.md` + `.opal/MEMORY.md` 생성 → 완료
- [ ] 개발 프로젝트: PM 공통 인터뷰 + 기존 기술 인터뷰 → 기존 프로세스 (docs + platform + .opal/)
- [ ] PM 공통 인터뷰 항목: 프로젝트명/설명, 도메인, 페르소나, 의사결정 원칙, 현재 Phase
- [ ] 자동 판별: 소스 코드 존재 시 "개발 프로젝트" 제안, 없으면 "일반 프로젝트" 제안
- [ ] apply.js에 `scope` 필드 추가 (`"full"` | `"opal-only"`)
- [ ] `scope: "opal-only"`이면 `[1/4]~[4/4]` 스킵, `[5/5]`만 실행
- [ ] PM 인터뷰 결과를 AGENT.md 플레이스홀더에 반영 (PERSONA, DECISION_PRINCIPLES, CURRENT_PHASE)

## 제약 조건

- 기존 개발 프로젝트 흐름(Step 0~8)의 동작을 변경하지 않음
- PM 공통 인터뷰는 개발 프로젝트에서 기존 인터뷰에 추가되는 형태

## 관련 문서

- `skills/opal-project-init/SKILL.md` — 메인 스킬 정의
- `skills/opal-project-init/scripts/apply.js` — 템플릿 적용 스크립트
- `skills/opal-project-init/templates/common/opal/AGENT.md` — PM 프로필 템플릿
- `tasks/028-opal-project-init-pm-profile/` — 이전 태스크 (PM 프로필 생성 파이프라인)
