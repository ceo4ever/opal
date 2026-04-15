# DONE: 파이프라인 현황판 CLOSE 단계 분리 — DONE.md/State Gate/사용자 확인 귀속 재설계

> 태스크: 121 | 적용 스킬: opp | 모드: agentic
> 시작: 2026-04-15 15:18 | 완료: 2026-04-15 17:20 (KST)
> 소요: 약 2시간 2분 (PLAN 재지시 1회 포함)

---

## 1. 요약

OPAL 파이프라인 현황판의 **최종 단계(EXECUTE/TEST)에 혼재되어 있던 마감 블록(DONE.md 생성 + State Gate + 사용자 확인)을 별도의 `CLOSE` 단계로 분리**하는 구조 리팩토링을 완료. 모든 오케스트레이터가 공통 CLOSE 마감 패턴을 공유하게 되었고, "최종 단계 예외 규칙"이 소멸되어 템플릿 규칙이 단일화되었다.

부수적으로 캡틴 지시에 따라 **"CLOSE 진입 게이트" Guard**를 하네스 3개 문서(`opal-harness.md` §1 / `state-template.md` / `opal-harness-agentic.md` §7)에 명문화하여, 사용자의 명시적 승인(`승인`/`확인`/`확인완료` 등) 없이는 CLOSE 단계에 진입할 수 없도록 강제했다. 이 규칙은 agentic 모드에서도 유지된다.

## 2. 설계 결정 (C안)

| 항목 | 변경 전 | 변경 후 (C안) |
|------|---------|--------------|
| CLOSE 단계 구성 | 없음 (EXECUTE/TEST에 마감 블록 혼재) | **2행**: `DONE.md 생성` / `State Gate` |
| 사용자 확인 위치 | 최종 단계 끝 (마감 블록 내부) | 직전 단계(EXECUTE/TEST/QA/VERIFY) 끝 → CLOSE 진입 게이트 역할 |
| 최종 단계 패턴 | 예외 규칙 (일반 단계 패턴과 다름) | 일반 단계 패턴 100% 준수 (`... PM Gate → State Gate → 사용자 확인`) |
| CLOSE 진입 | 암묵적 (자동 전이) | 명시적 Guard (사용자 승인 필수, agentic에서도 예외 없음) |
| 추가작업 | 평면적 5단계 | CLOSE 재진입 7단계 |

## 3. 요구사항 달성 (R-1 ~ R-7)

| # | 요구사항 | 결과 | 변경 위치 |
|---|---------|------|---------|
| R-1 | state-template.md CLOSE 단계 공통 블록 규칙 (2행 + 진입 게이트) | ✅ Pass | `harness/state-template.md` L47, L52, L60, L62 |
| R-2 | opal-harness.md §3 이벤트 테이블 + 상태 전이 흐름 갱신 | ✅ Pass | `opal-harness.md` §3 이벤트 테이블, 상태 전이, 레거시 호환 |
| R-3 | 6개 SKILL.md 도메인 치환값 갱신 (C안) | ✅ Pass | opp/opd/opds/opdw/opwt/opsdd 전부 |
| R-4 | additional-work.md CLOSE 재진입 원칙 | ✅ Pass | `harness/additional-work.md` L28, L46 |
| R-5 | 레거시 호환 원칙 명시 | ✅ Pass | `state-template.md` L62 + `opal-harness.md` §3 |
| R-6 | 변경이력 갱신 (10개 파일) | ✅ Pass | 전 대상 파일 변경이력 테이블 (121) 참조 |
| R-7 | CLOSE 진입 게이트 Guard 명문화 | ✅ Pass | `opal-harness.md` §1 L45 + `state-template.md` L52 + `opal-harness-agentic.md` §7 L111 |

## 4. 변경 파일 (10개)

### 하네스 / 참조 (4개)

1. **`opal/core/references/harness/state-template.md`** (v1.1)
   - L47 "최종 단계(EXECUTE/TEST)" 예외 규칙 제거
   - "CLOSE 단계: 2행(`DONE.md 생성` / `State Gate`)" 규칙 추가
   - "CLOSE 진입 게이트" 원칙 blockquote 추가
   - DONE.md 행 규칙을 CLOSE 귀속으로 변경
   - 레거시 호환 원칙 단락 추가
   - 변경이력 섹션 신규 생성

2. **`opal/core/references/opal-harness.md`** (v4.2)
   - §1 Guards에 "CLOSE 진입 게이트" 서브섹션 신설 (R-7)
   - §3 이벤트 테이블에 CLOSE 귀속 명시
   - 상태 전이 흐름에 CLOSE 단계 언급
   - 레거시 호환 노트 추가

3. **`opal/core/references/opal-harness-agentic.md`** (v1.4)
   - §7 "유지되는 규칙" 테이블에 "CLOSE 진입 게이트" 행 추가 (R-7)
   - "agentic 모드에서도 CLOSE 진입은 사용자 승인 필수" 명시

4. **`opal/core/references/harness/additional-work.md`** (v1.1)
   - "CLOSE 재진입 원칙" blockquote 추가
   - 진입 절차 5단계 → 7단계로 확장 (State Gate + 사용자 확인 추가)
   - 변경이력 섹션 신규 생성

### 오케스트레이터 SKILL (6개)

5. **`opal/skills/opal-pilot-project/SKILL.md`** (v2.5) — opp
   - Harness 모드 + 단계 목록에 CLOSE 추가
   - STEP 4 CLOSE 섹션 신설
   - 진행 현황 행 예시: EXECUTE 마감 3행 제거 + State Gate/사용자 확인 2행 추가 + CLOSE 2행 추가 (19→20행)
   - Agentic Mode 흐름도에 CLOSE 추가 (CLOSE 진입 사용자 승인 필수 명시)

6. **`opal/skills/opal-pilot-dev/SKILL.md`** — opd
   - STEP 6 CLOSE 섹션 신설
   - TEST 마감 3행 제거 + 2행 추가 + CLOSE 2행 (24→25행)

7. **`opal/skills/opal-pilot-dev-short/SKILL.md`** — opds
   - STEP 5 CLOSE 섹션 신설
   - TEST 마감 3행 제거 + 2행 추가 + CLOSE 2행 (18→19행)

8. **`opal/skills/opal-pilot-dev-wireframe/SKILL.md`** — opdw
   - STEP 4 CLOSE 섹션 신설
   - EXECUTE 마감 3행 제거 + 2행 추가 + CLOSE 2행 (19→20행)

9. **`opal/skills/opal-pilot-write-tech/SKILL.md`** — opwt
   - QA 단계에서 DONE.md 생성 문구 분리
   - CLOSE 단계 섹션 신설 (QA 단계 뒤)
   - 단계 목록에 CLOSE 추가

10. **`opal/skills/opal-pilot-sdd/SKILL.md`** (v2.9.0) — opsdd
    - Phase 6 DONE → **CLOSE** 리네이밍
    - 진행 현황 4행 → 2행 통일 (VERIFY 사용자 확인이 CLOSE 진입 게이트)
    - 37→35행 축소
    - 6단계 파이프라인 요약 + Agentic Mode 흐름도 갱신

## 5. Gate 통과 이력

| 단계 | Gate | 결과 | 시점 |
|------|------|------|------|
| TASK | 사용자 확인 | ✅ Pass | 15:19 |
| PLAN | 작업 → PLAN.md 생성 | ✅ | 15:24 |
| PLAN | PM 산출물 검증 | ❌ Fail (이슈 2건 발견) | 15:25 |
| PLAN | 에스컬레이션 → C안 + R-7 확정 → FIX | ✅ 반영 | 15:27 |
| PLAN | 재검증 → QA Gate | ✅ Pass | 16:06 |
| PLAN | State Gate → PM Gate → State Gate | ✅ Pass | 16:06 |
| PLAN | 사용자 확인 | ✅ Pass ("승인") | 16:07 |
| EXECUTE | 작업 (10개 파일 / 11 Step) | ✅ | 16:16 |
| EXECUTE | QA Gate → State Gate → PM Gate | ✅ Pass | 16:22 |
| CLOSE | 진입 게이트 (R-7 사용자 승인) | ✅ Pass ("확인") | 17:20 |
| CLOSE | DONE.md 생성 → State Gate → 최종 사용자 확인 | ✅ | 17:20 |

## 6. AGENTIC-LOG 요약

- **게이트 판단**: 10회 (Pass 10 / Fail 1 → 재지시 후 Pass)
- **PM 의사결정**: 5건 (120번 처리, STATE.md 선제 적용, C안 채택, FIX 지시, 전환기 노트)
- **에스컬레이션**: 1건 (설계 의도 모호성 → C안 + R-7 확정)
- **수정 지시**: 1건 (PLAN v1 → v2 FIX, 완전 반영)
- **블로커**: 0건
- **3회 초과 Gate**: 0건

## 7. 전환기 노트 (Important)

본 태스크(121)는 **CLOSE 단계 도입 자체의 리팩토링 태스크**이므로, 시작 시점에는 아직 CLOSE 규칙이 프레임워크에 존재하지 않았다. STATE.md는 **초기 3행 CLOSE 구조**(17행 DONE.md 생성 / 18행 State Gate / 19행 사용자 확인)로 선제 작성되어 진행되었고, 중간에 C안으로 규칙이 확정되었으나 레거시 호환 원칙을 적용하여 **본 태스크 STATE.md의 구조는 소급 변경 없이 유지**되었다.

**적용 시점**:
- **122번부터 신규 태스크**: C안(2행 CLOSE + EXECUTE/TEST/QA/VERIFY 끝에 State Gate/사용자 확인) 적용
- **기존 태스크 (001~121)**: 레거시 구조 유지, 수정하지 않음

## 8. Info 2건 (EXECUTE 처리 완료)

| # | 항목 | 대응 |
|---|------|------|
| I-1 | state-template.md 변경이력 테이블 부재 | EXECUTE에서 신규 생성 (v1.0 + v1.1) |
| I-2 | additional-work.md v1.0 일시 특정 | EXECUTE에서 기존 도입 맥락(087)을 참조하여 신규 생성 |

## 9. 후속 권고

1. **다음 태스크(122번)부터 실질 검증**: 새 태스크를 C안 구조로 시작하여 규칙 동작 확인
2. **배포**: 본 태스크는 "개발" 범위에서 완료. 캡틴의 명시적 "배포" 지시가 있을 때 `install-mac.sh` 실행 (확정 기준 #2 준수)
3. **커뮤니티 영향**: 기존 OPAL 사용자가 있다면 CLOSE 단계 도입에 대한 안내 필요 — 단, 프로젝트 내부 변경이므로 외부 영향 미미

## 10. 산출물

- **TASK.md**: 요구사항 정의 (R-1~R-7, 체크박스 모두 `[x]` 갱신)
- **PLAN.md** (v2): 11 Step / 3 Phase 실행 체크리스트
- **QA-PLAN.md**: PLAN 검증 (Pass)
- **QA-EXECUTE.md**: EXECUTE 검증 (Pass)
- **AGENTIC-LOG.md**: 대행 일지 (22 엔트리)
- **STATE.md**: 파이프라인 현황판 (19행 — 레거시 3행 CLOSE 구조)
- **DONE.md**: 본 문서
- **변경 소스 파일**: 10개 (`opal/core/references/` 4개 + `opal/skills/` 6개)
