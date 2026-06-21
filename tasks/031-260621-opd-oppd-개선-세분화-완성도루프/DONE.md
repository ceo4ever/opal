# DONE: oppd 개선 — 프로세스(문서 승격) + WBS 세분화(BE/FE) + 액션 완성도 루프(B7)

> 완료일: 2026-06-21 16:14 | 스킬: //opd (opds→opd 전환) | 모드: agentic | 태스크: 031

## 요약

oppd(`opal-pilot-project-dev`) 파이프라인을 3개 축으로 개선했다. 변경 대상은 전부 프레임워크 소스 `.md` 7개(배포본 `~/.opal/` 미편집). TEST 문서 정합성 검증 All Pass 23/23, FAIL 0.

## 변경 파일 (7, 전부 소스 `opal/...`)

| 파일 | 변경 요약 | F-ID |
|------|----------|------|
| `opal/core/references/opal-harness.md` | §1 자동 루핑 제약 표에 "PLAN 재진입(재설계 루프)" 행 신설 (2회, SSOT) | F-026 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | PRD/TRD 태스크폴더 작성+docs 승격 · WBS 태스크폴더 전용 · sizing 교체 · PM검수 4종 · Phase3 scope 분기+WBS 2단기준+TRD/PRD 게이트 · STATE 재설계 루프 로그 | F-001/002/003/010/015/023/024 |
| `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | sizing 단일책임 · 너무 큼/작음 · 수용시나리오 용어계층 · 통합 액션 타입 · 병렬=파생 · PM검수 4종 · BE 원자5종 · FE 3계층 · BE/FE 매트릭스 | F-010~F-018 |
| `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | §1 목적 재서술 (병렬=세분화 파생) | F-014 |
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | triage 3분류 · §3-5 QA 0회→설계수준 scope별 분기 · §7 PLAN 재진입 포인터 | F-021/027 |
| `opal/agents/opal-task-action-agent/AGENT.md` | B7 경계 재설계 루프 · triage · 1차분류+자동승격 · 3계층 라우팅 · scope 반환 · 명명 구분 · WBS/TRD 직접수정 금지 가드 | F-020~F-025 |
| `opal/agents/opal-fe-agent/AGENT.md` | FE 3계층(T0/T1/T2) 구현 역할 + 컴포넌트 API 계약 | F-017 |

## 단계별 결과

| 단계 | 결과 |
|------|------|
| TASK | 27 요구사항(F-001~F-027) + 4요소 잠금. opds→opd 전환(범위 초과) |
| ANALYSIS | 줄번호 매핑·교차참조맵·F-027 충돌·드리프트·리스크 R-1~R-7. decision_required 4건 → 캡틴 확정 |
| PLAN | 12 Step/9 Phase·H-1~H-11 가설·22 TS·33 [MUST]. F-026 N=2 채택 |
| TEST-SCENARIO | S-001~S-027 문서 정합성 시나리오 (전부 M1 grep) |
| EXECUTE | 배치1(5파일 병렬)+배치2(2파일)+fix(1). 회귀 1건 검출·교정 |
| TEST | All Pass 23/23 (opal-test-agent + PM 직접 SSOT 최종확인) |

## 캡틴 확정 결정 (AskUserQuestion)

1. 문서 승격 = PM 자동 판단(greenfield 복사/반복 델타)
2. 세분화 집행 = 문서 규칙화(이번) + WBS 검증기 도구(후속)
3. B7 루프백 = 경계 재설계 루프
4. 분류 주체 = 액션 에이전트 1차분류 + fix 한도초과 자동승격
5. WBS 변경 = 2단 기준 / TRD·PRD = 항상 사용자 게이트
6. 공통 컴포넌트 추출 = 기존 UI킷 우선 + 2+ 화면
7. 용어 계층(수용시나리오=상위) / 재진입 명명 구분 / STATE 재설계 루프 로그 / F-026 N=2

## 특이사항

- **회귀 1건 검출·교정**: W6가 action-agent의 model 레벨명(advanced/light/standard)을 Claude 전용 `opus`로 하드코딩(플랫폼 독립성 위반) → PM 강화검토(직접 Read)로 검출 → fix 워커로 복원.
- **ANALYSIS R-1 환각**: "배포본에 model:opus 블록 존재" 분석이 사실과 반대(배포본=레벨명)였고 PLAN이 이를 신뢰 → W6 실행으로 이어짐. PM Gate가 차단. (학습: 드리프트 분석은 PM이 실측 교차검증)
- 모든 루프 상한 수치는 harness SSOT 단독 기재, 타 문서는 포인터만(R-3 준수).

## 후속 (별도 지시 대기)

- **install 재배포** — 소스 변경이 실제 프레임워크(`~/.opal/`)에 발효되려면 재배포 필요. (이번 미수행)
- **커밋** — 커밋 규칙상 캡틴 명시 지시 시에만. (이번 미수행)
- **roadmap-guide.md 정리** — 소스 참조 0건 고아 파일(ROADMAP→WBS v4.0 전환 잔존). "1~3일"/"병렬 식별" 구서술 잔존 → 삭제 별도 태스크 후보.
- **WBS 검증기 도구 게이트** — #2 세분화의 도구 집행(coarse/generic 액션 거부). 확정 방향대로 후속 태스크.
