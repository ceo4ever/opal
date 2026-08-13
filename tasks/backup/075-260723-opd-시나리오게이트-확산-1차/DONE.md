# DONE: op-scenario-gate 목표-커버 게이트 확산 1차 (opds·opsdd)

> 완료일: 2026-07-23 | 스킬: opd (agentic) | 소유자: 캡틴
> 상태: 완료·커밋 대기·미배포(캡틴 배포)

## 1. 목표와 결과

073에서 구축한 목표-커버 게이트 공유 컴포넌트를 **opds·opsdd에 확산 적용**했다. 신규 tool/agent/pilot 0 — op-scenario-gate Step 2에 pilot별 정규화 변환기를 추가하고 각 오케스트레이터에 게이트를 배선하는 것만으로 완결(정규화 계약의 확장성 실증). oppl은 제외 확정(자체 표면-게이트+독립평가 보유), oppd는 2차 유예.

## 2. 요구사항 이행 (R-1~R-6)

| R-ID | 내용 | 결과 |
|------|------|------|
| R-1 | op-scenario-gate Step 2 pilot 변환기 확장 | ✅ pilot=opds(opd 동형)·pilot=opsdd(SPEC.md FR/AC/EC 소스, covers_requirements=FR 역참조) additive 추가. opd 행 diff 0. 규율 #4·enum·산문 3종 지원 정합 |
| R-2 | opds producer 확립 + 게이트 배선 | ✅ opal-pilot-dev-short STEP 2를 PM+캡틴 직접 작성으로 확립(op-dev-plan 미접촉→opd 무영향) + pipeline.json `plan.scenario_gate` 행(11행, spec-validate 0). EXECUTE 구조적 차단 실증 |
| R-3 | opsdd Phase 2 REVIEW 게이트 배선 | ✅ STATE 24→25행 재정렬(행10 커버리지 게이트/행11 목표-커버 게이트) + `--row N` 전수 수정 + REVIEW 4단계 배선. 독립 evaluator로 self-confirming 해소, DESIGN 진입 차단 실증 |
| R-4 | opsdd verify-guide §4 대체 | ✅ 수동 FR/AC/EC 커버리지 → scenario-coverage-check 게이트 대체. §2 S-1~S-6 정의 테이블 diff 0(존치) |
| R-5 | 회귀 | ✅ opd·op-dev-plan·scenario-gate.md·test-tool·evaluator diff 0. test_scenario 31 passed(회귀 0). opds spec-validate 0, opsdd rows_count 25 |
| R-6 | 자기적용 실증 | ✅ opds/opsdd 변환기 정규화 페이로드: 완전→exit 0, 누락→exit 16. 075 자신도 073 게이트 통과(avg 2.0, 파이프라인 dogfooding) |

## 3. 발견①(에스컬레이션) 해소

- **발견①**: opds가 TEST-SCENARIO.md를 신뢰성 있게 생성하는지 SSOT 문서 상충(opal-pilot-dev-short:54 "통합작성" vs op-dev-plan:6/35/146 "출력 제외").
- **캡틴 결정(옵션1)**: opds STEP 2 서술 보강으로 producer 확립(PM+캡틴이 op-dev-test-scenario 형식으로 직접 작성), **op-dev-plan 미접촉**(opd 공용 스킬 회귀 방지).
- 실증: op-dev-plan diff 0 확인.

## 4. 변경 파일 (changed_files)

**수정 (소스 5 + 문서 1)**
- `opal/skills/op-scenario-gate/SKILL.md` (Step 2 pilot=opds/opsdd 변환기 + 규율/enum 정합 + v1.1)
- `opal/skills/opal-pilot-dev-short/SKILL.md` (STEP 2 producer 확립 + 게이트 배선 + 미러 표/행번호 + v4.4)
- `opal/skills/opal-pilot-dev-short/references/pipeline.json` (plan.scenario_gate 행, 11행)
- `opal/skills/opal-pilot-sdd/SKILL.md` (STATE 24→25행 재정렬 + REVIEW 게이트 배선 + `--row N` 전수 + v3.6.0)
- `opal/skills/opal-pilot-sdd/references/verify-guide.md` (§4 게이트 대체, S-1~S-6 존치, v1.1)
- `docs/PROJECT.md` (확산 반영 + 변경이력)

**태스크 산출물**: TASK.md·ANALYSIS.md·PLAN.md·TEST-SCENARIO.md·AGENTIC-LOG.md·SCENARIO-GATE-1.md·DONE.md

**커밋 제외**: `.claude/settings.json`(075 무관 세션 설정 변경)

## 5. 후속·미해결

- **opsdd pipeline.json 미전환(070 후속)**: opsdd는 아직 SKILL.md 마크다운 표 파싱(레거시 `--row N`) — 게이트 행 삽입 시 `--row N` 전수 수정이라는 회귀 위험(H-3)을 감수해야 했다. state-tool init이 deprecation 경고를 출력한다. 070 그룹A pipeline.json 전환을 opsdd에도 적용하는 별도 후속 태스크 권고(회고 기록).
- **oppd 2차 확산**: 자율·무인이라 가치 최고이나 action-agent 내부 접합이라 복잡 — 별도 태스크.

## 6. agentic 대행 요약

- 게이트 판단 6회 전부 Pass. 에스컬레이션 1건(발견①, 캡틴 옵션1로 해소). PM 의사결정 3건. 상세: `AGENTIC-LOG.md`.
- 핵심 검증(opds/opsdd 게이트 차단·rows_count 25·opd diff 0·회귀 31 passed·자기적용 exit16/0)을 PM이 직접 재실행 확인(헌법 §4 "verified behavior").
- 파이프라인 dogfooding: 075 자신이 073 게이트를 통과(avg 2.0) — 게이트가 확산 태스크 자신에 실제 적용됨.
