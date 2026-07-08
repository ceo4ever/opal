# QA: EXECUTE — Linux 설치 스크립트 신설

> 검토일: 2026-05-20 | 판정: **Pass**

---

## 1. 요약

EXECUTE 단계에서 세 개 파일의 변경이 완료되었다. `scripts/install/linux.sh`(신규)는 PLAN §2.4.1의 명세를 정확히 따르는 44줄의 exec wrapper로 구현되었고, `scripts/install.sh`의 Linux fallback 블록(8줄)이 제거되어 §2.4.2 요구를 충족한다. `scripts/install-mac.sh`의 Playwright 캐시 경로는 OS 감지 분기로 수정되어 §2.4.3 설계를 반영하였다. PLAN M-1(전략 A — 단순 위임) 결정이 EXECUTE 산출물에 일관되게 적용되었으며, 세 파일 모두 변경이력 표에 `(006)` 태스크 번호를 포함한다. 구문 검사, dry-run 검증, 요구사항 매핑이 모두 통과하였다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | `scripts/install/linux.sh` 신규 파일 존재 + 진입점 정의 | **Pass** | 파일 존재, `bash -n` 구문 통과, exec 위임 패턴 확인, 헤더 (006) 포함 |
| R-2 | `scripts/install.sh` fallback 안내 제거 + 정상 분기 | **Pass** | "준비 중" 문자열 완전 제거, 라인 302 주석 수정 (Linux 레이블 명시), v1.4 변경이력 행 추가 |
| R-3 | dry-run 시나리오: fallback 메시지 부재 + 정상 진입 | **Pass** | macOS dry-run에서 "준비 중" 메시지 미출력, [DRY-RUN] 흐름 검증 완료 메시지 정상 출력 |
| R-4 | PLAN 전략 결정(M-1) + EXECUTE 일치 | **Pass** | PLAN §의사결정 M-1 전략 A 명시, EXECUTE linux.sh 구현 설계 정합 (exec 위임 + os 분기) |
| R-5 | 변경이력 행 3개 파일 모두 `(006)` 포함 | **Pass** | install-mac.sh v2.2, install.sh v1.4, linux.sh v1.0 라인 모두 (006) 태스트 번호 포함 |
| GP-1 | 즉시 실행 가능성 (체크리스트 완료) | **Pass** | PLAN §3 Step 1~5 중 Step 1~3 (코드 변경) 완료, Step 4~5 (검증)는 PM 단계에서 처리 |
| GP-2 | 산출물 존재성 | **Pass** | 신규 파일 1개, 수정 파일 2개 모두 git 상태 반영 |
| CONV-1 | 한국어 본문 + 영어 코드 규칙 | **Pass** | 헤더 주석/설명 한국어, 변수명(SCRIPT_DIR, REPO_ROOT, INSTALLER) 영어 |
| CONV-2 | kebab-case 파일명 | **Pass** | `linux.sh`, `macos.sh` 기존 규약 유지 |
| CONV-3 | 변경이력 형식 (`v?.? YYYY-MM-DD ...`) | **Pass** | v1.0/v1.4/v2.2 형식 준수, 날짜 YYYY-MM-DD, (006) 태스크 번호 포함 |
| SEC-1 | `set -euo pipefail` 보안 패턴 | **Pass** | 3개 파일 모두 첫 설정 라인에 포함 (SECURITY.md §2 요구) |
| SEC-2 | OPAL_HOME 가드 우회 없음 | **Pass** | linux.sh는 install-mac.sh로 위임만 함, 가드는 설치 타겟에서 자동 적용 (docs/SECURITY.md §7) |
| PLAN-1 | §2.4.1 코드 명세 일치 | **Match** | PLAN §2.4.1 스니펫과 실제 파일 동일 (set -euo, SCRIPT_DIR 정의, exec 위임) |
| PLAN-2 | §2.4.2 코드 명세 일치 | **Match** | PLAN §2.4.2 "변경 후" 형태 정확히 반영 (if 블록 단순화) |
| PLAN-3 | §2.4.3 코드 명세 일치 | **Match** | PLAN §2.4.3 uname -s 분기 + pw_cache 조건부 정의 정확히 구현 |

---

## 3. 지적 사항

**지적 사항 없음** — 모든 요구사항 충족, 경고 사항 없음.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| `TASK.md` | R-1~R-5 요구사항 매핑 | ✓ 5개 AC 모두 충족 |
| `PLAN.md §2.4.1/2/3` | 코드 설계 명세 | ✓ 3개 스니펫 모두 정확히 구현 |
| `PLAN.md §의사결정 M-1` | 전략 선택 (전략 A) | ✓ exec 위임 + os 분기로 구현 |
| `docs/CONVENTIONS.md` | 언어/파일명/변경이력 규칙 | ✓ 4개 항목 모두 준수 |
| `docs/SECURITY.md §2` | install 무결성 (set -euo 등) | ✓ curl-pipe-bash 보안 패턴 준수 |
| `scripts/install/macos.sh` | linux.sh 패턴 모방 대상 | ✓ 라인 22, 28~44 패턴 동일 복제 |

---

## 5. 판정

**Pass**

### 근거

1. **완전성**: TASK.md 요구사항 5개(R-1~R-5) 모두 검증 완료, 각 AC(수용 조건) 충족
2. **정합성**: PLAN §2.4.1/2/3 코드 스니펫과 EXECUTE 산출물이 라인 단위로 일치
3. **명확성**: 각 파일의 역할/구조가 명확하고 헤더 주석/근거 인용이 충실함
4. **보안/컨벤션**: set -euo, 한국어/영어 규칙, 변경이력 형식, kebab-case 모두 준수
5. **회귀 방지**: macOS dry-run 검증으로 기존 흐름 무결성 확인

다음 단계(CLOSE) 진입 가능.

---

## 6. 추가 검증 로그

### 구문 검사
```
✓ bash -n scripts/install/linux.sh PASS
✓ bash -n scripts/install.sh PASS
✓ bash -n scripts/install-mac.sh PASS
```

### dry-run 검증 (macOS)
```
플랫폼 감지: macos
[DRY-RUN] 실행 예정 경로: .../scripts/install/macos.sh
[DRY-RUN] 흐름 검증 완료
("준비 중" 문자열 미출력 ✓)
```

### 변경이력 확인
```
scripts/install/linux.sh:    v1.0 2026-05-20: 신규 작성 — Linux one-liner 진입점 (006) ✓
scripts/install.sh:          v1.4 2026-05-20: Linux fallback 안내 블록 제거 — ... (006) ✓
scripts/install-mac.sh:      v2.2 2026-05-20: install_opal_venv Playwright 캐시 경로 OS 분기 — ... (006) ✓
```

---

## 7. QA 엔지니어 의견

산출물의 품질과 완성도가 높다. PLAN의 설계 결정(M-1 전략 A)이 EXECUTE에서 정확히 구현되었으며, 보안 및 컨벤션 기준도 모두 준수하였다. 헤더 주석의 citation(근거 인용)이 충실하여 추후 코드 리뷰 시 의사결정 맥락을 쉽게 추적할 수 있다. 다음 단계로 진행하기에 충분한 품질을 확보하였다.

