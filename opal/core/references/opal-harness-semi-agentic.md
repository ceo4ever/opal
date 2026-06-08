# opal-harness-semi-agentic

> semi-agentic 모드(기본) 전용 하네스. 공통 하네스(opal-harness.md)와 함께 로드한다. `--semi-agentic` 플래그(또는 모드 플래그 미지정 — 기본 모드) 활성화 시 이 문서를 로드한다.

---

## 1. 모드 정의

| 모드 | 설명 |
|------|------|
| `interactive`   | 모든 단계 게이트마다 사용자 승인 (`--interactive` 명시) |
| `semi-agentic`  | **기본** — PLAN-equivalent 단계까지 사용자 검토, EXECUTE-equivalent 진입 후 PM 자율 통과. CLOSE 진입은 사용자 승인 필수 |
| `agentic`       | 모든 게이트 PM 자율 통과 (CLOSE 진입 제외) — `--agentic` 명시 |

## 2. 활성화 방법

- 기본: 모드 플래그 미지정 시 semi-agentic
- 명시: `--semi-agentic` 플래그
- 충돌: `--interactive` 또는 `--agentic`과 동시 사용 시 `mode_flag_conflict` 에러
- 활성화 시 STATE.md 모드 필드를 `semi-agentic`으로 기록 (`state init --mode semi-agentic`)

## 3. 모드 경계 (PLAN-equivalent → EXECUTE-equivalent 전환점)

| pilot | PLAN-equivalent 종료 시점 | EXECUTE-equivalent 시작 시점 |
|-------|--------------------------|----------------------------|
| opp   | PLAN 사용자 확인 행 (행 11) | EXECUTE 작업 행 (행 12) |
| opd   | TEST-SCENARIO 사용자 확인 행 | EXECUTE 작업 행 |
| opds  | PLAN 사용자 확인 행 | EXECUTE 작업 행 |
| opdw  | WIREFRAME 사용자 확인 행 | EXECUTE 작업 행 |
| opwt  | PLAN(간략/진단보고) 사용자 확정 행 | EXECUTE 작업 행 |
| oppd  | Phase 2 WBS 사용자 확정 행 (D-DEC-1) | Phase 3 액션 실행 첫 행 |
| opsdd | Phase 3 DESIGN 사용자 Gate (D-DEC-2) | Phase 4 EXECUTE-LOOP 첫 행 |

## 4. PLAN-equivalent까지의 동작 (interactive 준용)

- 단계 게이트마다 사용자 승인 필수
- PM Gate는 interactive 동일 (`opal-harness-interactive.md` §3 참조) — 문서 QA(요구사항→설계 검토)는 별도 QA Gate 단계 없이 PM Gate가 흡수
- AGENTIC-LOG.md 미생성 (이 시점까지)

> **참조**: semi-agentic 모드의 PLAN-equivalent 종료 시점까지의 동작은 `opal-harness-interactive.md`를 준용한다.

## 5. EXECUTE-equivalent 이후의 동작 (agentic 준용)

- PM 자율 통과 (`state-tool --auto-pass` 호출)
- AGENTIC-LOG.md 자동 생성 (EXECUTE 등가 첫 행 advance/mark 시점에 PM이 생성)
- Gate 루핑 규칙: `opal-harness-agentic.md §5` 적용
- PM 대행 의무(판단 기록/직접 검증/완수/품질 책임/투명성/에스컬레이션/폴백 승인): `opal-harness-agentic.md §3` 적용

**Pass 시 state-tool 호출 (EXECUTE-equivalent 이후 사용자 확인 행)**:

```
~/.opal/tools/state-tool/run.sh mark tasks/{NNN}-.../ \
  --row <N> --done \
  --auto-pass \
  --note "semi-agentic auto-pass: <PM 판단 근거>"
```

## 6. CLOSE 진입 게이트 (공통)

- agentic 모드와 동일하게 CLOSE 첫 행 `--auto-pass` 거부 (`agentic_close_gate_requires_user`)
- semi-agentic / agentic 양쪽 모두 동일 에러 코드로 거부

CLOSE 진입 절차:
1. PM이 소유자에게 CLOSE 진입 직전 상황을 보고한다
2. 소유자(사용자)의 승인 발화(`승인`/`확인`/`확인완료` 등)를 받는다
3. 직전 단계 사용자 확인 행(prev_user_row)을 `--owner user`로 mark한다:
   ```
   ~/.opal/tools/state-tool/run.sh mark tasks/{NNN}-.../ \
     --row <사용자 확인 행 N> --done \
     --owner user \
     --note "{owner_name} 확인: <발화 요약>"
   ```
4. 이후 CLOSE 첫 행 mark 시 도구가 prev_user_row 자동 검증을 통과시킨다

근거: `opal-harness-agentic.md §4` CLOSE 진입 게이트 / `PLAN.md §2.16 G-13` / D-DEC-5b

## 7. AGENTIC-LOG.md 생성 시점

- agentic 모드: TASK 시작 시점 (즉시 생성)
- semi-agentic 모드: EXECUTE-equivalent 첫 행 advance 또는 mark 시점 (PM이 EXECUTE 진입 시 생성)

**헤더 형식**:
```markdown
# AGENTIC-LOG: {태스크 제목}

> 모드: semi-agentic | 시작: YYYY-MM-DD HH:mm | 스킬: //{스킬명}
```

생성 이후 기록 방식은 `opal-harness-agentic.md §8` 동일.

## 8. interactive / agentic / semi-agentic 차이 표

| 단계 | interactive | semi-agentic | agentic | 비고 |
|------|-------------|-------------|---------|------|
| TASK 완료     | 사용자 승인 | 사용자 승인 | PM 자율 | |
| ANALYSIS 완료 | 사용자 승인 | 사용자 승인 | PM 자율 | |
| PLAN 완료     | 사용자 승인 | 사용자 승인 | PM 자율 | |
| TEST-SCENARIO 완료 | 사용자 승인 | 사용자 승인 (모드 경계) | PM 자율 | opd 전용 |
| EXECUTE 완료  | 사용자 승인 | PM 자율 | PM 자율 | |
| TEST 완료     | 사용자 승인 | PM 자율 | PM 자율 | |
| CLOSE 진입    | 사용자 승인 | 사용자 승인 (공통 게이트) | 사용자 승인 (공통 게이트) | |

## 9. 유지되는 규칙 (opal-harness.md §1 Guards 그대로 적용)

- 구현 금지 원칙 / 커밋 규칙 / 디스패치 의무 / 자동 루핑 제약 / CLOSE 진입 게이트
- 에스컬레이션 조건: `opal-harness-agentic.md §6` 동일 적용

---

## 10. 단계 전환 보고 양식 (캡틴 게이트 3종)

이 3 게이트 보고만 본 양식을 따른다 (§3 모드 경계 / §6 CLOSE 게이트 참조). 게이트 3종 외에는 `AGENT.md §보고 형식`의 형식 자율성이 유지된다.

---

### §10.1 PLAN 완료 보고

**5요소 표준**:

| 요소 | 내용 |
|------|------|
| 1. 의사결정 요약 | M-1~M-N 결정 결과 한 줄씩 |
| 2. 변경 범위 | 신규/수정/삭제 파일 N개 (간단 표) |
| 3. 체크포인트 | 캡틴이 다음 단계 진입 전 반드시 알아야 할 핵심 (이전 결정 번복·범위 변경·리스크) |
| 4. 실행 구성 | Step N개 / Phase 구성 (병렬·순차) |
| 5. 다음 액션 | 승인 시 무엇이 시작되는지 |

**양식 예시**:

🎯 결론·근거

1) PLAN 완료
   - 의사결정 요약: M-1 Eager 방식 채택 (Lazy 대비 정직성·가시성 우위) / M-2 알투 자율 판단

2) 변경 범위
   - 신규 1개, 수정 3개, 삭제 없음

3) 체크포인트
   - 기존 보고 형식 2종을 완전 대체. 되돌리기 필요 시 변경이력에서 복구 가능

4) 실행 구성
   - Phase 1 (Step 1 순차) → Phase 2 (Step 2~4 병렬)

---

▶️ 다음 진행 사항입니다.

1) 승인(확인)해주시면 EXECUTE를 시작하겠습니다

---

### §10.2 EXECUTE 후 사용자 확인 보고

**5요소 표준**:

| 요소 | 내용 |
|------|------|
| 1. 변경 결과 | changed_files 목록 + 각 파일 핵심 변경 1줄 |
| 2. 검증 결과 | QA 체크리스트 통과 여부 / 테스트 결과 |
| 3. 리스크 | 잔존 리스크 또는 미검증 항목 |
| 4. 잔여 작업 | 완료되지 않은 Step / 블로커 |
| 5. 다음 액션 | 확인 후 무엇이 시작되는지 |

**양식 예시**:

🎯 결론·근거

1) EXECUTE 완료
   - 변경 파일 4개, QA 전 항목 통과

2) 변경 결과
   - `AGENT.md` 수정 — §보고 형식 인라인 + Eager Step 6.6 제거
   - `opal-harness-semi-agentic.md` 수정 — §10 단계전환 양식 신설
   - `opal-harness.md` 수정 — §2 모듈 테이블 reporting-template 행 제거
   - `opal-pm.md` 수정 — §8 탐색 경로 재지정

3) 검증 결과
   - QA 체크리스트 전 항목 통과

4) 리스크
   - 없음

5) 잔여 작업
   - 없음

---

▶️ 다음 진행 사항입니다.

1) 확인(승인)해주시면 CLOSE로 진입하겠습니다

---

### §10.3 CLOSE 진입 보고

**5요소 표준**:

| 요소 | 내용 |
|------|------|
| 1. 완료 산출물 | 생성/수정된 파일 목록 |
| 2. QA 결과 | 기능·일관성·문서 품질 체크리스트 최종 결과 |
| 3. 잔여 미해결 | 미완료 항목 또는 Known Issue |
| 4. 후속 태스크 후보 | 파생 작업 또는 개선 아이디어 |
| 5. 확정 요청 | 캡틴에게 CLOSE 확정 요청 |

**양식 예시**:

🎯 결론·근거

1) 태스크 015 완료
   - CLOSE 확정을 요청합니다

2) 완료 산출물
   - `AGENT.md` 수정, `opal-harness-semi-agentic.md` 수정, `opal-harness.md` 수정, `opal-pm.md` 수정
   - `harness/reporting-template.md` 삭제

3) QA 결과
   - 기능·일관성·문서 품질 전 항목 통과

4) 잔여 미해결
   - 없음

5) 후속 태스크 후보
   - install 재실행으로 `~/.opal/references/` 배포 동기화

---

▶️ 다음 진행 사항입니다.

1) 확정(승인)해주시면 DONE.md를 생성하고 종료하겠습니다

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-05-09 11:22 | 초기 작성 — semi-agentic 신규 모드 SSOT (140) |
| v1.1 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — "캡틴" → "소유자" / note 예시 "{owner_name} 확인" placeholder 치환 (139) |
| v1.2 | 2026-05-15 16:40 | §3 opd 행 모드 경계 갱신 — PLAN 사용자 확인 행 → TEST-SCENARIO 사용자 확인 행. §8 차이 표에 TEST-SCENARIO 완료 행 추가(opd 전용) + 비고 컬럼 신설 (004) |
| v1.3 | 2026-06-07 | §4 QA→PM Gate 통합 정합화 — "QA Gate / PM Gate" → "PM Gate"(문서 QA 흡수, 별도 QA Gate 단계 없음, interactive §3 참조). 동작 검증(TEST/verify) 영역 불변 (014 Phase 4-2) |
| v1.4 | 2026-06-08 | §10 단계전환 보고 양식 3종 신설 — reporting-template.md §8 이전 + 🎯 결론·근거 통합 표기 + ▶️ 승인 대기 어미 통일 (015) |
