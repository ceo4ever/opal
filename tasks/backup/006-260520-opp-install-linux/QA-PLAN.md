# QA: PLAN — Linux 설치 스크립트 신설 (scripts/install/linux.sh)

> 검토일: 2026-05-20 | 판정: **Pass**

---

## 1. 요약

PLAN.md는 Linux 사용자를 위한 one-liner 설치 진입점(`scripts/install/linux.sh`)을 신설하고, 기존 `scripts/install.sh`의 fallback 안내를 제거하는 계획을 명시한다. 전략 결정(M-1~M-4)은 install-mac.sh의 함수별 호환성 정밀 분석(27개 함수 분류)을 근거로 하며, 변경 범위는 최소(3개 파일, macOS 의존성 1줄)로 제한된다. 6개 실행 Step과 QA 체크리스트가 명확하게 정의되어 있어 EXECUTE 단계로 즉시 진행 가능하다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | **Pass** | 4개 의사결정(M-1~M-4) 완료, 6개 Step 정의, 각 Step 별 완료 기준·테스트 명시, 코드 예시 제공 |
| GP-2 | 의존성 순서 | **Pass** | Step 1-2 병렬(독립), Step 3 → 4 → 5 → 6 순차 의존 정상 구성. 실행 순서 명확. |
| GP-3 | TASK 반영 | **Pass** | R-1(linux.sh 신설) ← Step 2, R-2(fallback 제거) ← Step 3, R-3(one-liner 동작) ← Step 4-5, R-4(전략 결정) ← M-1, R-5(변경이력) ← 설계 2.4.1/2/3. 5개 요구사항 모두 반영. |
| GP-4 | 파일 목록 완전성 | **Pass** | 신규(N-1): scripts/install/linux.sh, 수정(U-1, U-2): install.sh/install-mac.sh, 삭제 없음. 명확히 분류. |
| GP-5 | 설계 구체성 | **Pass** | §2.4.1/2/3에서 Before/After 코드 제시, 라인 번호 명시(install.sh 325~335, install-mac.sh 945), 주석 및 근거 포함. |
| GP-6 | 체크리스트 커버리지 | **Pass** | §3의 6개 Step + §4의 4개 카테고리 QA (기능/일관성/문서/보안). 모든 R-1~R-5가 Step과 QA 항목으로 분해됨. |

---

## 3. 지적 사항

**지적 사항 없음.**

모든 검증 항목이 통과했으며, 문서 구조, 근거 제시, 설계 결정의 정합성에서 높은 수준의 품질을 유지하고 있다.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | R-1~R-5 요구사항이 PLAN.md §1(현황), §2(결정), §3(Step), §4(QA)에 모두 반영됨 | **Pass** |
| docs/CONVENTIONS.md | 언어 규칙(한글+영문 코드), 파일명(kebab-case), 변경이력 형식(KST + 버전 + 태스크번호), @header 규칙, 플랫폼 분기 격리 모두 준수 | **Pass** |
| docs/SECURITY.md | `set -euo pipefail` 포함(§2.4.1), OPAL_HOME 가드(자동 적용 — linux.sh → install-mac.sh 위임), Playwright 캐시 경로 분기(§2.4.3, D-9 근거) | **Pass** |
| docs/ARCHITECTURE.md | 어댑터 계층 원칙 준수 — OS 차이를 install_opal_venv() 내부에 격리, install.sh 본체에 조건문 추가 없음 | **Pass** |
| .opal/AGENT.md | agentic 모드 자율 결정 근거(M-1) 명시, CLOSE 진입 캡틴 승인 게이트 이해 (§6 "추가 검토 메모"), 배포 경계 준수(프로젝트 소스 수정만) | **Pass** |
| citation-rules.md | §4 PLAN 단계 의무: 참조 테이블(D-1~D-9) + 인라인 인용(M-1~M-4 문장 내 근거) + [MUST] 포맷 사용 정상 | **Pass** |

---

## 5. 심화 검토 항목

### 5.1 M-1 (전략 결정) 근거 강도 평가

**분석 수준**: 우수
- §1의 §1.3 "install-mac.sh 함수별 Linux 호환성 정밀 분석"에서 27개 함수를 분류 (F-1~F-27)
  - Linux 호환: 17개 (F-2/3/4/7/10/11/12/15/16/17/18/21/22/23/26/27)
  - 부분 호환(경로/라벨): 9개 (F-1/5/6/8/9/13/14/19/25)
  - macOS 전용: **1개** (F-20 `install_opal_venv` Playwright 캐시)
- 결론: 재사용 가능성 매우 높다 (1345줄 중 1줄만 수정)
- 전략 A(단순 위임) 선택의 정당성: §2.1 M-1에서 B/C 대안과 비교하며 명시
  - B(별도 신설): 1345줄 중복 유지보수 위험
  - C(install-core.sh 일반화): 리팩토링 범위 과도 + v0.5.0 베타 차단 긴급도에 부합 않음
  - A 선택 트레이드오프: 파일명 인상 문제는 헤더 주석 + 후속 리네이밍 태스크로 인수인계

**평가**: ✅ **매우 타당한 결정**

### 5.2 M-2 (Linux 배포판 범위) 합리성

**결정 내용**:
- 명시 지원: Ubuntu 22.04+ / Debian 12+ (apt 기반)
- Best effort: RHEL/Fedora/CentOS/Arch
- 비지원: Alpine (musl libc — Playwright 미지원)

**근거**:
- §1.2의 `check_deps()` 및 install-mac.sh 내 graceful skip 패턴 (python3/node) 활용
- curl-pipe-bash 보안 모델 준수: 자동 설치 금지(sudo 권한 증대 차단)
- Ubuntu/Debian이 OSS 사용자 분포 1위

**평가**: ✅ **합리적 범위 한정. 문서화됨.**

### 5.3 설계 코드 정확성

**linux.sh** (§2.4.1):
- `set -euo pipefail` 포함 ✓
- 에러 처리 (install-mac.sh 부재 시 exit 1) ✓
- exec 위임 패턴 (macos.sh 모방) ✓
- 주석 상세 (근거 TASK.md/PLAN.md 참조 포함) ✓

**install.sh** (§2.4.2):
- 단순화: Linux fallback 블록 제거, macOS와 동일 에러 처리 경로 통합 ✓
- 안전: 기존 정상 경로(install_path 검증) 유지 ✓

**install-mac.sh** (§2.4.3):
- OS 감지: `uname -s` 표준 명령 사용 ✓
- 경로: `~/.cache/ms-playwright` (Playwright Docs 준수, D-9) ✓
- 폴백: macOS는 `~/Library/Caches/ms-playwright` 유지 ✓

**평가**: ✅ **코드 정확도 높음. 보안/호환성 준수.**

### 5.4 Step 구성과 QA 체크리스트 정합성

**Step 1~3**: 코드 수정 작업
- QA 4.1 "함수별 Linux 호환성" 테스트 ✓
- QA 4.3 "변경이력 행 추가" 검증 ✓

**Step 4**: macOS dry-run (회귀 방지)
- QA 4.1 "fallback 경고 없음" ✓
- QA 4.2 "어댑터 격리 원칙" ✓

**Step 5**: Linux 검증
- QA 4.1 "Playwright 캐시 경로" ✓
- QA 4.4 "set -euo pipefail" ✓

**Step 6**: AC 매핑 (R-1~R-5 최종 확인)
- QA 4.1~4.4 모두 포함 ✓

**평가**: ✅ **Step과 QA 항목 1:1 매핑. 누락 없음.**

### 5.5 위험 식별의 충실도 (§5)

5개 리스크 분류 (R-T1~R-T5):

| # | 리스크 | 대응 |
|---|--------|------|
| R-T1 | python3 절대 경로 부재 (Alpine) | M-2 비지원 명시, 후속 커맨드 우선 리팩토링 |
| R-T2 | Playwright 브라우저 설치 실패 | 기존 graceful skip 패턴 유지 |
| R-T3 | Linux 실제 환경 검증 불가 | Step 5 옵션 A(docker) 1차, B(mock) 폴백, CLOSE에서 캡틴 추가 검증 |
| R-T4 | linux.sh/macos.sh 중복 DRY 위반 | 트레이드오프 명시, v0.6 로드맵 별도 태스크 |
| R-T5 | 변경이력 누락 | Step 완료 기준에 grep 명시 |

**평가**: ✅ **리스크 파악 정확. 현실적 대응.**

### 5.6 agentic 모드 자율 결정 문서화 (§6)

PLAN.md §6에서 명시:
- M-1 전략 선택의 자율 결정 인정 (캡틴 검토 시 이의 제기 가능)
- AGENTIC-LOG.md 기록 필요성 언급 (하네스 §3 폴백 승인 의무)

**평가**: ✅ **agentic 모드 규칙 준수. 투명성 우수.**

### 5.7 docs/ 영향 분석 (§7)

PLAN.md 자체에서 docs/ 갱신이 필요 없음을 명시:
- PROJECT.md: 폴더 구조맵 이미 존재
- ARCHITECTURE.md: 배포 모델 변경 없음
- CONVENTIONS.md: 컨벤션 신설 없음
- SECURITY.md: 정책 변경 없음

→ PM의 CLOSE 단계 DONE.md에서 "docs/ 갱신 없음" 확인 항목으로 추가 권장

**평가**: ✅ **메타인식 높음.**

---

## 6. citation-rules.md 준수 검증

### 6.1 참조 문서 테이블 (D-1~D-9)

| # | 근거 위치 | 인용 형식 | 검증 |
|---|----------|----------|------|
| D-1 | PLAN §1 "관련 파일" | `scripts/install.sh` + 라인 범위(325-335) | ✅ 정확 |
| D-2 | PLAN §2.4.1 "패턴 직접 모방" | `scripts/install/macos.sh:1-44` | ✅ 정확 |
| D-3 | PLAN §1 "함수별 분석 테이블 F-1~F-27" | `scripts/install-mac.sh:1-1345` | ✅ 정확 |
| D-4~D-8 | PLAN §1 참조 문서 표 | 경로 + 참조 이유 | ✅ 명확 |
| D-9 | PLAN §1 "외부 컨텍스트" + §2.4.3 | Playwright Docs URL | ✅ 링크 포함 |

### 6.2 인라인 인용 (M-1~M-4)

**M-1**: "§1 정밀 분석 결과... Table F-20" (→ D-1 참조)
- [MUST] CONVENTIONS.md §"플랫폼 분기 격리" 직인용 포함 ✅

**M-2**: "§1 check_deps()... scripts/install-mac.sh:832-844, 1075-1078"
- 라인 번호 명시 ✅

**M-3/M-4**: 이전 결정 참조 + 함수명/경로 명시 ✅

### 6.3 [MUST] 포맷 (citation-rules.md §2.4)

M-1에서:
```
[MUST] `docs/CONVENTIONS.md` §"플랫폼 분기 격리": "... 스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다 ..."
```

**평가**: ✅ **[MUST] 포맷 정확. 원문 인용 포함.**

---

## 7. 판정

### 최종 판정

**Pass** ✅

### 판정 근거

1. **6개 PLAN 검증 항목(GP-1~GP-6) 모두 통과**
   - 설계 결정 완료 및 정당화됨
   - 파일 목록 완전하고 명확함
   - 실행 체크리스트 상세하고 의존성 정상

2. **citation-rules.md 준수**
   - 참조 문서 테이블 D-1~D-9 완비
   - 인라인 인용 정확
   - [MUST] 포맷 올바르게 사용

3. **CONVENTIONS.md 준수**
   - 언어, 파일명, 변경이력 형식 모두 정확
   - 플랫폼 분기 격리 원칙 준수
   - @header 규칙 (코드 예시에서 확인 가능)

4. **SECURITY.md 준수**
   - set -euo pipefail 포함
   - OPAL_HOME 가드 자동 적용
   - sha256/curl-pipe-bash 보안 모델 유지

5. **agentic 모드 투명성**
   - 자율 결정(M-1) 이유 명확
   - AGENTIC-LOG.md 기록 계획 명시

6. **품질 수준**
   - 함수별 호환성 정밀 분석(27개 함수 분류)
   - 리스크 파악 및 현실적 대응
   - 메타인식(docs/ 영향 분석 포함)

### 실행 준비도

**즉시 EXECUTE 단계 진행 가능**

- 6개 Step이 명확히 정의됨
- 각 Step별 완료 기준과 테스트 방법 제시
- agent 배정(opal-task-agent) 타당
- QA 체크리스트 완비

---

## 8. 추가 조언

### 8.1 EXECUTE 단계 체크포인트

EXECUTE 워커는 다음 항목을 Step 완료 시 STATE.md에 기록하길 권장:

```
Step 1: install-mac.sh Playwright 캐시 OS 분기 추가 ✅
Step 2: scripts/install/linux.sh 신규 생성 ✅
Step 3: scripts/install.sh Linux fallback 제거 ✅
Step 4: macOS dry-run 회귀 검증 ✅ (log: /tmp/...)
Step 5: Linux 검증 (옵션: docker/mock/실제) ✅ (option: B-mock)
Step 6: R-1~R-5 AC 매핑 최종 확인 ✅
```

### 8.2 CLOSE 단계 PM 체크포인트

PM은 DONE.md 작성 시 다음을 확인:

- [ ] EXECUTE 모든 Step 완료 (STATE.md 확인)
- [ ] 변경이력 행 3개 파일 모두 추가됨 (grep 확인)
- [ ] docs/ 영향 없음 (§7 확인)
- [ ] R-1~R-5 AC 모두 검증됨 (로그 수집)
- [ ] 커밋 준비 (캡틴 승인 대기)

### 8.3 향후 관심사

PLAN.md §6 "추가 검토 메모"에서 언급한 향후 개선:

- v0.6 로드맵: `install-core.sh` 리네이밍 (M-1 트레이드오프)
- python3 경로 자동 감지 (R-T1 대응)

이들은 별도 태스크로 분리되어야 함. 현 태스크는 긴급도(v0.5.0 베타 진입로 차단) 우선.

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-20 | 초기 QA 검증 완료 — PLAN 단계 6개 항목 모두 Pass |
