# PLAN_C: dev-task-pilot 컴포지션 전환 (하이브리드 실행)

> 작성일: 2026-03-26 | 참조: TASK.md, ANALYSIS.md, **PLAN.md**, **PLAN_B.md**  
> 입력: TASK.md, ANALYSIS.md, PLAN.md(설계 정본), PLAN_B.md(절차·워커 프롬프트)  
> 출력: PLAN_C.md

## 1. 목적

**PLAN.md**는 구현 범위·디렉터리 구조·페르소나·단계별 입출력·오케스트레이터·에이전트까지 담은 **설계 정본(design authority)**이다.  
**PLAN_B.md**는 `opal-skill-creator`와 워커를 쓰는 **실행 절차(Phase A~F)**와 디스패치 프롬프트를 담는다.

**PLAN_C**는 둘을 합친 **단일 실행 계획**이다: *설계는 PLAN에 따르고, 생성·검증은 PLAN_B 흐름을 따른다.*

---

## 2. 역할 분담 규칙

| 구분 | 정본 문서 | PLAN_C에서의 취급 |
|------|-----------|------------------|
| 스킬별 디렉터리·파일 목록 | PLAN.md §1 | 반드시 준수. 워커 산출물이 다르면 설계 오류로 간주하고 수정 |
| 구현 순서·의존 | PLAN.md §2 | Phase B/C 순서와 정합. 단계 스킬 8개는 PLAN과 동일하게 상호 독립 → 병렬 가능 |
| frontmatter·산출물 헤더·페르소나·단계 스킬 본문 | PLAN.md §3.1~§3.4 | Spec·생성 스킬의 **내용 기준**. `dtp-skill-specs.md`는 §3를 축약·구조화한 Phase 1 답변으로 본다 |
| 오케스트레이터·에이전트·탐색 경로·스킬/MCP 매핑 | PLAN.md §3.5~§3.8 | 오케스트레이터 3개·에이전트 3개·경로 규칙의 근거 |
| 의존성·리스크(설계 관점) | PLAN.md §4, §8 | 실행 리스크와 함께 참고 |
| Skill Spec 템플릿·워커 프롬프트·Phase F·레지스트리 스킵 타이밍 | PLAN_B.md §2~§7 | 그대로 적용 |

**충돌 시**: 기능·구조·입출력은 **PLAN.md 우선**. 절차 문구만 다르면 **PLAN_B.md 우선**.

---

## 3. 실행 파이프라인 (요약)

PLAN_B §1과 동일하되, 각 Phase 시작 전 **해당 구간의 PLAN.md §절을 Read**한다.

```
Phase A: dtp-skill-specs.md 작성 (알투) — 내용은 PLAN.md §3에서 추출
    ↓
Phase B: 단계 스킬 8개 (워커 × opal-skill-creator) — PLAN_B 워커 프롬프트
    ↓
Phase C: 오케스트레이터 3개 (워커 × opal-skill-creator) — §3.5·실제 경로 반영
    ↓
Phase D: 에이전트 3개 (알투 직접) — PLAN.md §3.6
    ↓
Phase E: 레지스트리 + CLAUDE.md + .opal/MEMORY.md — PLAN.md §1 수정 표 + PLAN_B §6
    ↓
Phase F: 통합 테스트 + Description 최적화 — PLAN.md §6 동적 검증 + PLAN_B §7
```

---

## 4. Phase A 보강 (PLAN_C 전용)

`tasks/032-dtp-to-otp-restructure/dtp-skill-specs.md`를 작성할 때:

1. **스킬별로** PLAN_B §2의 Spec 템플릿을 채운다.
2. **Persona·Principles·행동 규칙**은 PLAN.md §3.3 해당 항목에서 **복사·축약하지 말고 의미가 빠지지 않게** 옮긴다.
3. **디렉터리 트리·references/personas 파일명**은 PLAN.md §3.4 해당 스킬 절과 **글자 단위로 맞출 필요는 없으나**, 파일 역할(어떤 가이드가 어디로 가는지)은 동일해야 한다.
4. **오케스트레이터 3개(dtp-dev / dtp-dev-short / dtp-dev-wf)** Spec에는 PLAN.md §3.5의 파이프라인 블록·게이트·에스컬레이션을 요약해 넣는다.

Spec 작성이 끝나면 캡틴 검토·승인 후 Phase B로 진행한다 (PLAN_B A-2).

---

## 5. Phase B·C 워커 지시 (PLAN_C 전용)

워커 프롬프트는 **PLAN_B §3·§4** 본문을 사용한다. 다음만 **추가**한다.

```
**설계 정본**: tasks/032-dtp-to-otp-restructure/PLAN.md — §3 해당 스킬/오케스트레이터와 불일치하면 PLAN.md에 맞게 수정할 것.
**산출물 검증**: 생성 후 PLAN.md §1의 해당 행(파일 목록)과 대조할 것.
```

Phase C 워커에는 **Phase B 완료 후 실제 `skills/dtp-*/SKILL.md` 경로**를 PLAN_B §4처럼 나열해 넣는다.

---

## 6. 예외·탈출 해치 (Escalation)

- **워커가 Spec을 무시하고 본문을 임의로 줄이거나 단계를 누락**하면: 해당 스킬만 재디스패치하거나, 알투가 PLAN.md §3를 보고 **직접 패치**한다 (PLAN_B 리스크 표와 동일).
- **병렬 불가**(플랫폼·세션 제약) 시: PLAN.md §2 순서(페르소나 선행 → 단계 스킬)에 가깝게 **순차**로 진행해도 된다. 순서는 단계 스킬 간 **무관**이므로 임의 순서 가능.
- **opal-skill-creator로 오케스트레이터 품질이 반복적으로 불만족**이면: Phase C 해당 스킬만 알투 **직접 작성**으로 전환한다 (산출물 기준은 여전히 PLAN.md §3.5).
- **에이전트 3개**는 PLAN_B와 같이 **항상 알투 직접** (도구 특성상 변경 없음).

---

## 7. 검증 체크리스트 (PLAN_C = PLAN + B 합집합)

완료 판정은 아래를 **모두** 만족해야 한다.

**PLAN.md 기준 (설계)**

- [ ] PLAN.md §5 실행 체크리스트 항목이 산출물 수준에서 충족되는가 (스킬·에이전트·문서)
- [ ] PLAN.md §6 QA — 기능·정합성·동적 검증 항목 통과
- [ ] PLAN.md §6의 테스트 프롬프트(또는 이에 상응하는 시나리오)로 파이프라인 확인

**PLAN_B.md 기준 (프로세스·품질)**

- [ ] PLAN_B §8 Phase A~F 체크리스트 완료
- [ ] PLAN_B §9 QA 체크리스트 완료
- [ ] 오케스트레이터 3개에 대해 PLAN_B §7 Description 최적화 루프 수행(또는 캡틴 승인 하에 한 회 스킵 명시)

---

## 8. 산출물 목록 (참조만)

최종 파일·레지스트리 변경 목록은 **PLAN.md §1**을 따른다. 추가 산출물은 **PLAN_B**와 동일: `dtp-skill-specs.md`, Phase F 테스트·최적화 기록(선택: `tasks/032-dtp-to-otp-restructure/` 하위 메모).

---

## 9. PLAN / PLAN_B / PLAN_C 관계 한 줄 요약

| 문서 | 역할 |
|------|------|
| PLAN.md | 무엇을 만들고, 구조·내용이 어떻게 생겼는지 |
| PLAN_B.md | skill-creator·워커·Phase·프롬프트·리스크(실행 세부) |
| **PLAN_C.md** | PLAN을 정본으로 B를 실행하는 **합의된 단일 런북** |

---

## 10. 변경이력

| 버전 | 일자 | 비고 |
|------|------|------|
| v1.0 | 2026-03-26 | 최초 작성 — PLAN + PLAN_B 하이브리드 실행 정의 |
