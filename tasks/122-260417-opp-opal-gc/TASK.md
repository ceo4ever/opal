# TASK: opal-pilot-gc 경량 Pilot + 보안/컨벤션 에이전트 개발

> 작성일: 2026-04-17 | 작업 유형: 신규 | 적용 스킬: opp | 모드: interactive
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

커밋 전 코드 컨벤션 및 보안 체크를 수행하는 **경량 Pilot(`opal-pilot-gc`)**과 2개의 전문 에이전트(`opal-convention-checker`, `opal-security-checker`)를 프레임워크 기본 컴포넌트로 개발한다. 초기에는 수동 실행(`//opgc`) 전용이며, 훅 통합 등 자동화는 후속 태스크로 분리한다.

## 배경

캡틴이 "커밋 시점에 코드 컨벤션과 보안 등을 자동 체크하는 garbage-collector"를 원한다. 다음 합의에 도달:

1. **옵션 검토** — 스킬 / 에이전트 / 훅 / git pre-commit 비교 완료
2. **선택 1** — "스킬+에이전트 수동 실행 → 이후 자동화" 점진적 접근
3. **선택 2** — 단순 스킬이 아니라 **경량 Pilot** 구조로 — 하네스(Guards/Gates/State) 적용, STATE.md 관리, 단계별 게이트
4. **이번 태스크 범위** — 경량 Pilot 오케스트레이터 + 단계 + 에이전트 2개 (자동화는 후속)

메모리 `project_security_task.md`에 030 태스크에서 "보안 전용 스킬+에이전트 생성 예정" 보류가 있으며, 이번 태스크가 해당 보류 건의 **코드 보안(TEST 단계) 부분**을 흡수한다.

## 배경 분석 (대화에서 도출)

### 1. 현재 OPAL 프레임워크 보안 자산

- `opal/skills/` — 보안 전용 스킬 0개 (검색 확인)
- `opal/agents/` — 보안 전용 에이전트 0개 (검색 확인)
- 030 산출물 — `execute-guide.md`에 기본 가드레일(하드코딩 시크릿, SQL injection 패턴)만 내장

### 2. 기준 문서 상태 및 설계 함의

- 프로젝트 `docs/`에 `SECURITY.md` **없음** → 보안은 프레임워크 Base 원칙이 반드시 존재해야 하므로, 문서 부재와 무관하게 강제 적용되는 구조 필요
- `docs/CONVENTIONS.md` **존재** → 컨벤션은 프로젝트 전용 기준을 유일 출처로 사용 가능
- **설계 함의**: 보안과 컨벤션은 기준의 성격이 다르므로 적용 방식을 **분리**한다 (§6, §7 참조)

### 3. 옵션별 비교 (대화에서 정리)

| 유형 | 트리거 | 강제성 | 추론력 | 이번 태스크 채택 |
|------|--------|--------|--------|--------|
| Claude Code 훅 | Claude의 `git commit` 직전 | 강 | 약 | ❌ (후속) |
| 스킬 단독 | 캡틴 수동 호출 | 약 | 강 | ❌ (Pilot으로 상향) |
| **경량 Pilot** | 캡틴 수동 호출 (`//opgc`) | 중 | 강 | ✅ |
| 전문 에이전트 | Pilot이 디스패치 | - | 강 (도메인) | ✅ (2개) |
| git pre-commit hook | 누가 커밋하든 | 최강 | 중 | ❌ (후속) |

### 4. 030 보안 보류 태스크와의 관계

메모리 `project_security_task.md`는 보안을 **2단계(PLAN 설계 보안 + TEST 코드 보안)**로 분리하자는 방향이었다. 이번 `opal-pilot-gc`는 **TEST(코드 보안)** 부분을 담당. PLAN(설계 보안)은 별도 후속으로 분리 유지.

### 5. Pilot 전환 근거

`opal-gc`는 본질적으로 **SCAN → CHECK → REPORT → APPLY → CLOSE** 다단계 구조이며, STATE 관리/게이트/agentic 모드가 유용하다. 다만 `//opgc` 빠른 실행이 주 용도이므로 기존 `opal-pilot-project` 스타일(TASK→PLAN→EXECUTE→CLOSE)은 오버헤드. **경량 Pilot 패턴**(산출물 최소화 + 체크리스트 내장 보고서)을 도입한다.

## 확정된 설계 방향 (대화에서 합의)

### §1. 구성 — 경량 Pilot + 에이전트 2개

| 컴포넌트 | 이름 | 약어/별칭 | 역할 |
|----------|------|---------|------|
| Pilot | `opal-pilot-gc` | `opgc` (별칭 `gc`) | 오케스트레이션, 단계 진행, STATE 관리, APPLY 결과 통합 |
| 에이전트 | `opal-convention-checker` | - | 코드 컨벤션·네이밍·구조·죽은 코드·미사용 import |
| 에이전트 | `opal-security-checker` | - | 시크릿 / OWASP Top 10 / CWE / SANS / 의존성 / 권한 |

**경량 Pilot 설계 원칙**: 표준 하네스(Guards/Gates/State) 적용하되, **산출물 최소화** (PLAN.md/EXECUTE.md 생성 생략, **통합 보고서·별도 APPLY 로그 생성 없음** — 체크리스트 갱신 + DONE.md로 대체).

### §2. 파이프라인 — 5단계 (SCAN → CHECK → REPORT → APPLY → CLOSE)

```
SCAN → CHECK → REPORT → APPLY → CLOSE
  │       │        │        │       │
  선별    병렬     에이전트별  체크박스  DONE.md
  staged  디스패치 보고서(체크  순회 +   생성
  /all    2개      리스트 내장) 적용·체크
```

| # | 단계 | 역할 | 산출물 | 게이트 |
|---|------|------|--------|--------|
| 1 | SCAN | 대상 파일 선별(`--scope`), 기술 스택 감지, 기준 문서(CONVENTIONS.md/SECURITY.md) 로드 | STATE.md 갱신 | - |
| 2 | CHECK | `opal-security-checker` + `opal-convention-checker` **병렬 디스패치** | 각 에이전트 임시 결과 (STATE 로그) | 워커 완료 확인 |
| 3 | REPORT | 각 에이전트 결과를 **자기완결 보고서(체크리스트 내장)**로 생성. 빈도 분석(§9), 문서 업데이트 제안 감지(§9·§10). STATE.md에 **요약 테이블** 갱신 | `GC-SECURITY-{ts}.md`, `GC-CONVENTION-{ts}.md` | 사용자 확인 |
| 4 | APPLY (선택) | 보고서 체크리스트를 순회하며 자동 판정(§3) — `[x] done` / `[!] failed` / `[?] review` / `[~] pending`. 문서 업데이트 제안 승인 시 CONVENTIONS.md/SECURITY.md 갱신 연계(§10) | 보고서 체크박스·주석 갱신 (별도 LOG 파일 없음) | 사용자 승인 (기본) |
| 5 | CLOSE | 실행 요약 집계, DONE.md 생성 | `DONE.md` | 사용자 확인 (CLOSE 진입 게이트 준수) |

**태스크 폴더 구조** (매 실행마다 생성 — D+ 안):

```
tasks/{NNN}-{YYMMDD}-opgc-{짧은요약}/
  ├── STATE.md                        # 파이프라인 상태 + 실행 요약 테이블 (허브)
  ├── GC-SECURITY-{타임스탬프}.md     # 보안 보고서 (체크리스트 내장, 자기완결)
  ├── GC-CONVENTION-{타임스탬프}.md   # 컨벤션 보고서 (체크리스트 내장, 자기완결)
  └── DONE.md                          # CLOSE 단계 완료 문서
```

> **트래커(이력 저장소) 도입하지 않음** (§9 참조 — 각 실행은 독립).
> **별도 APPLY 로그 파일 없음** — 적용 결과는 각 보고서 체크박스·주석 갱신으로 기록 + Git diff/log가 코드 변경 이력 담당.

### §3. APPLY 실행 방식 — 체크리스트 기반 + 자동 상태 판정

#### 실행 모드

| 방안 | 동작 | 채택 |
|------|------|------|
| A) **기본: 리포트 확인 후 적용** | REPORT 완료 → 사용자 승인 → APPLY | ✅ 기본값 |
| B) **`--apply` 플래그: 자동 적용** | REPORT 직후 APPLY 자동 실행, 결과 일괄 확인 | ✅ 선택 가능 |

안전이 기본, 속도는 명시적 선택. 구체 흐름(승인 UX, 롤백 방안 등)은 PLAN에서 확정.

#### 체크박스 5단계 상태 모델

| 기호 | 상태 | 설명 |
|------|------|------|
| `[ ]` | open | 미처리 (신규) |
| `[x]` | done | 적용 완료 |
| `[~]` | pending | 보류 — 이번 실행에서 처리 안 함 |
| `[?]` | review | 소유자 확인 필요 — 에이전트 판단 불가 |
| `[!]` | failed | 시도했으나 실패 — 재시도/수동 필요 |

#### 자동 상태 결정 규칙 (APPLY 단계가 수행)

```
각 이슈 순회 시:
  1. 자동 수정 가능 + 수정 성공       → [x] done
  2. 자동 수정 가능 + 수정 실패       → [!] failed  (실패 사유 주석)
  3. 자동 수정 불가 (수동 지침 존재) → [?] review  (해결 방안 주석)
  4. 자동 수정 불가 (판단 모호)      → [?] review  (판단 근거 주석)
  5. 캡틴이 직전 지시로 보류         → [~] pending (사유 주석)
```

> `[x]` 외 모든 상태는 **인라인 주석**에 사유·조치를 명시한다. `[x]`는 적용 시각을 주석으로 기록.

#### 실패/보류/확인필요 항목의 후속

- **다음 `//opgc` 실행 시 동일 fingerprint로 재발견** → 새 보고서에 `[ ]` open으로 초기화
- 과거 사유는 이전 태스크 폴더의 보고서(Git 커밋 이력)에서 확인 가능
- 트래커 없이도 **재가시화**가 자연스럽게 이루어짐

### §4. Arguments 설계

```
//opgc                          # 전체 체크 (기본: staged 범위, APPLY 승인 대기)
//opgc --only security          # 보안만
//opgc --only convention        # 컨벤션만
//opgc --scope staged           # 스테이징된 변경분 (기본)
//opgc --scope all              # 프로젝트 전체
//opgc --apply                  # REPORT 후 바로 APPLY (승인 생략)
//opgc --agentic                # agentic 모드 (자율 실행)
```

### §5. 배포 범위 — 프레임워크 기본

- `opal/skills/opal-pilot-gc/`
- `opal/agents/opal-convention-checker/`, `opal/agents/opal-security-checker/`
- `install-mac.sh` 배포 대상에 추가

### §6. 컨벤션 체크 기준 — 프로젝트 전용 단일 기준 + 부재 시 작성 유도

**원칙**: 컨벤션은 프로젝트마다 다르므로 **프로젝트 `docs/CONVENTIONS.md`를 유일한 기준**으로 사용한다. 프레임워크는 내장 기본값을 강요하지 않는다.

#### 동작 분기

| 상황 | 동작 |
|------|------|
| `docs/CONVENTIONS.md` 존재 | 해당 문서를 유일한 기준으로 체크 |
| 부재 | **체크 실패 아님** + "CONVENTIONS.md가 없습니다. 코드베이스 분석 기반 초안을 생성할까요?" 안내 → 캡틴 승인 시 초안 생성 → 재실행 시 기준 적용 |

#### 작성 유도 방식

- `opal-convention-checker`가 부재를 감지하면 초안 생성 모드로 전환
- 초안 생성 경로 (PLAN에서 확정):
  - 1안: 기존 `opi` 계열 스킬 재사용
  - 2안: 전용 초안 생성 서브 프로세스 (코드베이스 샘플 → 네이밍/들여쓰기/파일 구조/import 순서 추출)

#### 설계 근거

- 프로젝트마다 언어·팀 규칙·도메인이 달라 내장 공통값은 오히려 노이즈
- 컨벤션이 명문화되지 않은 프로젝트에는 "체크 실패"보다 **"명문화 촉진"이 더 가치 있음**

### §7. 보안 체크 기준 — Base 원칙 + SECURITY.md (2축 구조)

**원칙**: 체크 시점에는 두 출처만 사용한다.

- **계층 1 — Base 원칙** (프레임워크 내장, 항상 강제 적용)
- **계층 2 — 프로젝트 `docs/SECURITY.md`** (있으면 추가, 없으면 작성 유도)

기술 스택별 보안 가이드(context7 MCP)는 **체크 시점에 동적 조회하지 않고, `SECURITY.md` 작성 시점에 정적으로 반영**한다. 이유: 결과 일관성 보장, 외부 의존 최소화, 적용 규칙의 명시성 및 리뷰 가능성.

#### 계층 1 — Base 원칙 (강제 적용)

`opal-security-checker` 에이전트에 내장하여 **모든 실행에서 강제 적용**:

| 기준 | 출처 | 역할 |
|------|------|------|
| OWASP Top 10 (2021) | owasp.org | 웹 애플리케이션 10대 위험 |
| CWE Top 25 | cwe.mitre.org | 소프트웨어 취약점 카테고리 |
| SANS Top 25 | sans.org | 공격 유형별 대응 |
| 커뮤니티 스킬 (선정 시) | PLAN 실사 후 | `openai/security-best-practices`, `getsentry/code-review` 등 — 래핑 호출 |

#### 계층 2 — 프로젝트 `docs/SECURITY.md` (동작 분기)

| 상황 | 동작 |
|------|------|
| 존재 | Base 원칙 + SECURITY.md 통합 기준으로 체크 |
| 부재 | **Base만으로 체크 정상 수행** + 보고서 말미에 **SECURITY.md 작성 유도 안내** |

#### SECURITY.md 작성 유도 프로세스 (부재 시)

"SECURITY.md가 없습니다. 기술 스택별 보안 가이드와 프로젝트 커스텀 항목을 기반으로 초안 생성할까요?"

초안 생성 단계:

1. **기술 스택 감지** — `package.json`, `requirements.txt`, `go.mod`, `pom.xml` 등 확인
2. **스택별 가이드 조회** — `context7` MCP로 공식 보안 가이드 수집 (예: Express helmet, Django DEBUG 금지, Spring Security 등)
3. **코드베이스 샘플 분석** — 인증/인가 구조, 시크릿 관리 방식, 외부 API 연동 패턴, 민감 데이터 흐름 파악
4. **초안 구성**:

   ```markdown
   # SECURITY
   
   ## 1. 기술 스택별 보안 원칙 (자동 생성 — context7 인용)
   - {스택}별 권장 패키지 / 설정 / 금지 패턴
   
   ## 2. 프로젝트별 추가 보안 원칙 (캡틴 편집 필요)
   - {코드베이스 분석 기반 제안 항목}
   
   ## 3. 체크 범위 및 제외 (캡틴 편집)
   - 검토 대상 디렉토리
   - 제외 파일 / 패턴
   ```

5. **캡틴 승인 후 저장** (자동 생성 금지 — 하네스 Guards 준수)

#### 갱신 주기

`SECURITY.md`가 오래되어 최신 취약점 반영 못할 수 있으므로, 장기 사용 시 **주기적 갱신 유도 메커니즘 필요**. PLAN에서 확정 — 예: N개월 경과 감지, `//opgc refresh-security` 명령 등.

#### 적용 흐름 (체크 시점)

```
opal-security-checker 실행 시:
  1. [강제] Base 원칙 로드 (내장 체크리스트)
  2. [조건] docs/SECURITY.md 존재 확인
     - 존재: Read → Base에 병합
     - 부재: Base만 적용 + 보고서 말미에 작성 유도 안내
  3. 통합 체크리스트로 체크 수행
  4. 결과를 §8 보고서 포맷으로 반환
```

### §8. 보고서 구조 — 각 에이전트 자기완결 + 체크리스트 내장 (D+안)

**D+안 핵심**: 통합 요약 파일 없음. 각 에이전트가 **자기완결 보고서** 생성. STATE.md가 요약 테이블 허브 역할. 체크리스트 내장 + 5단계 상태 모델.

#### 보고서 공통 구조 (보안/컨벤션 동일 골격)

```markdown
# GC {SECURITY|CONVENTION} REPORT — {타임스탬프}

## 1. 헤더
- 실행 일시 (시작 / 완료 / 소요)
- 범위 (`staged` / `all`), 대상 파일 수
- 에이전트: opal-{security|convention}-checker
- APPLY 수행 여부

## 2. 요약 지표
| 지표 | 값 |
|------|-----|
| 총 이슈 수 | N |
| 심각도 분포 | Critical N / High N / Medium N / Low N / Info N |
| 자동 수정 가능 | N |
| 수동 조치 필요 | N |
| 파일별 상위 Top 5 | ... |
| 카테고리별 빈도 | 동일 fingerprint 파일 수 기준 순위 (§9 빈도 트리거) |
| Critical/High 수 | 심각도 트리거 대상 (§9) |
| 문서 업데이트 제안 수 | §9·§10 트리거 수 |

## 3. 수정 대상 (체크리스트)

### Critical (N건)
- [ ] GC-001 [파일:라인] {요약}
  - 카테고리: {OWASP A07 / CWE-798 등}
  - 위반 기준: Base | 프로젝트({SECURITY.md|CONVENTIONS.md} §N)
  - 설명: {무엇이 문제}
  - 해결 방안: {구체적 수정 안내}
  - 자동 수정: Y / N
  - 참조: {URL}

### High (N건)
### Medium (N건)
### Low (N건)
### Info (N건)

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)
- [ ] 빈번 이슈 "{카테고리}" (N개 파일) → {SECURITY.md|CONVENTIONS.md} §N 규칙 추가 제안
- [ ] Critical/High 이슈 "{카테고리}" → SECURITY.md 체크리스트 카테고리 추가 제안
- [ ] 새 카테고리 "{카테고리}" 등장 → 문서 §N 신설 제안

## 5. 문서 작성 유도 (해당 시)
- SECURITY.md 부재 → 초안 생성 안내 (보안 보고서만 해당)
- CONVENTIONS.md 부재 → 초안 생성 안내 (컨벤션 보고서만 해당)
```

#### 체크박스 상태 표기

| 기호 | 상태 | 주석 내용 |
|------|------|----------|
| `[ ]` | open | (비어 있음) |
| `[x]` | done | **적용 시각**: YYYY-MM-DD HH:mm + (자동 수정 내용 요약) |
| `[~]` | pending | **보류 사유**: {이유} |
| `[?]` | review | **확인 요청**: {판단 근거 / 해결 방안} |
| `[!]` | failed | **실패 사유**: {원인} / **권장**: {대안} |

#### 이슈 엔트리 필드

- **ID**: `GC-NNN` (자동 채번, 단일 실행 내 범위)
- **파일:라인**: `src/auth/login.js:42`
- **카테고리**: OWASP/CWE/컨벤션 카테고리
- **위반 기준**: `Base` / `프로젝트(SECURITY.md §N)` / `프로젝트(CONVENTIONS.md §N)`
- **설명**: 무엇이 문제인지
- **해결 방안**: 구체적 수정 안내
- **자동 수정 가능**: Y / N
- **참조**: OWASP / CWE / MDN 등 공식 문서 URL

> 내부 집계용 fingerprint(§9)는 보고서에 기본 미노출. 단일 실행 내 빈도 트리거 판정에만 사용.

#### 심각도 기준

| 등급 | 정의 | 예시 |
|------|------|------|
| Critical | 즉시 차단 필요 | 하드코딩된 API 키, 확정된 SQL Injection, RCE 가능성 |
| High | 주요 취약점 | 인증 누락 엔드포인트, 권한 우회, 민감정보 로그 출력 |
| Medium | 잠재 위험 / 설계 결함 | 약한 암호화, CORS 과다 허용, 검증 누락 |
| Low | 스타일 / 경미한 이슈 | 미사용 import, 네이밍 위반 |
| Info | 권장 개선 | 주석 스타일, 선택적 최적화 |

#### 카테고리 체계

| 에이전트 | 카테고리 | 예시 |
|---------|---------|------|
| security | OWASP 매핑 | A01 Broken Access Control, A03 Injection, A07 Auth Failures 등 |
| security | CWE ID | CWE-79 XSS, CWE-89 SQLi, CWE-798 Hard-coded Credentials |
| security | 도메인 | 시크릿 / 인증 / 인가 / 입력검증 / 의존성 / 로깅 / 암호화 / 설정 |
| convention | 컨벤션 카테고리 | 네이밍 / 들여쓰기 / 파일 구조 / 죽은 코드 / 미사용 import / 문서화 |

#### STATE.md 실행 요약 테이블 (허브 역할)

STATE.md는 통합 요약 파일을 대체하여 아래 테이블을 포함:

```markdown
## 이번 실행 요약

| 에이전트 | 총 이슈 | Critical | High | 적용 완료 | 실패 | 확인 필요 | 보류 | 문서 제안 | 보고서 |
|----------|--------|----------|------|----------|------|----------|------|----------|--------|
| security | 12 | 1 | 3 | 7 | 1 | 2 | 2 | 2건 | [→](./GC-SECURITY-{ts}.md) |
| convention | 27 | 0 | 0 | 25 | 0 | 1 | 1 | 1건 | [→](./GC-CONVENTION-{ts}.md) |
| **합계** | 39 | 1 | 3 | 32 | 1 | 3 | 3 | 3건 | - |
```

> **순서**: 보안 → 컨벤션 (고정).

#### DONE.md 템플릿

```markdown
# DONE: opal-pilot-gc 실행 — {타임스탬프}

## 실행 범위
- scope: {staged|all}
- 대상 파일 수: N
- 실행 시간: HH:mm:ss
- APPLY 모드: {기본|--apply}

## 처리 요약
| 에이전트 | 총 | [x] | [!] | [?] | [~] | [ ] | 문서제안 |
|----------|----|-----|-----|-----|-----|-----|----------|
| security | 12 | 7 | 1 | 2 | 2 | 0 | 2건 |
| convention | 27 | 25 | 0 | 1 | 1 | 0 | 1건 |

## 산출물
- [GC-SECURITY](./GC-SECURITY-{ts}.md)
- [GC-CONVENTION](./GC-CONVENTION-{ts}.md)

## 후속 권장
- 수동 조치 필요: {목록}
- 문서 업데이트 미처리: {건수} (다음 실행 시 재검토)
- 보류/확인 필요 항목: {목록}
```

#### 최종 포맷 확정은 PLAN에서

- 실제 샘플 보고서 1부 포함
- 체크리스트(OWASP 전 항목, CWE Top 25, 컨벤션 카테고리) 전량 열거
- 심각도 판정 기준의 경계 케이스 정의
- Markdown 템플릿 파일 구조 확정

### §9. 문서 업데이트 트리거 — 빈도 + 심각도 (단일 실행 내)

**배경**: 매 실행 결과를 이력 저장소(tracker)에 누적하는 대신, **단일 `//opgc` 실행 내에서 빈도/심각도를 분석**하여 문서 업데이트 제안을 생성한다. 캡틴의 합의 사항: *"gc를 했는데, 동일한 실수를 다른 파일에서 빈번하게 나오거나, 심각한 실수라고 판단하는 경우"*에만 문서 갱신을 유도한다.

#### 트리거 조건 (임계값은 PLAN에서 확정)

| 트리거 | 감지 방식 | 제안 |
|--------|----------|------|
| **빈번** | 단일 실행 내 **동일 fingerprint가 N개 이상의 파일에서 발견** | "이 규칙을 CONVENTIONS.md / SECURITY.md에 추가할까요?" |
| **심각** | **Critical 또는 High** 심각도 이슈 발견 (1건만이라도) | "이 취약점 유형을 SECURITY.md 체크리스트에 추가할까요?" |
| **새 카테고리** | 기존 CONVENTIONS.md / SECURITY.md에 없는 카테고리 등장 | "문서에 새 섹션 추가를 검토할까요?" |

#### 설계 원칙

- **이력 저장소(tracker) 없음** — 각 실행은 독립. 과거 실행과 비교하지 않음
- **fingerprint는 내부 집계용**으로만 사용 — 단일 실행 내에서 동일 이슈가 몇 개 파일에 퍼져 있는지 계산
- **상태(open/fixed/ignored/suppressed) 개념 없음** — 체크 결과를 매번 새로 산출. 예외 처리가 필요하면 **소스 코드의 주석 annotation** 또는 **CONVENTIONS.md/SECURITY.md 명시 제외 규칙**으로 처리
- **파이프라인 단순화** — SCAN에 tracker 로드 없음, APPLY에 상태 전이 없음 (체크박스 5단계만)

#### 파이프라인 영향

| 단계 | 동작 |
|------|------|
| SCAN | 대상 파일 선별, 기준 문서(CONVENTIONS.md / SECURITY.md) 로드 |
| CHECK | 에이전트 병렬 디스패치 |
| REPORT | 결과 수합 + 심각도/카테고리 분류 + **빈도 분석(파일별 fingerprint 집계)** + **문서 업데이트 제안 감지(§10 연계)** |
| APPLY | 체크리스트 순회, 자동 판정(§3), 문서 업데이트 제안 승인 시 CONVENTIONS.md / SECURITY.md 갱신 연계 |
| CLOSE | DONE.md 생성, 상태 요약 집계 |

#### Fingerprint (내부 집계용)

동일 이슈 식별용 해시 — 세부 알고리즘은 PLAN에서 확정:

- 기본 구성: `{카테고리} + {코드 패턴 해시}` (파일 경로는 집계를 위해 fingerprint에서 **제외**)
- 라인 번호는 fingerprint에서 제외 (동일 패턴이면 줄이 달라도 같은 이슈)
- 단일 실행 내 동일 fingerprint가 나온 파일 수 → 빈도 트리거 판정

#### 세부 사항 (PLAN에서 확정)

- **빈도 임계값 N** (예: 3 파일 / 5 파일 — 선택 근거 기록)
- **심각도 트리거 범위** — Critical/High 둘 다 / Critical만
- Fingerprint 알고리즘 세부 (코드 패턴 해시 대상)
- 새 카테고리 감지 알고리즘 (기존 문서 섹션 매핑 방식)

### §10. 문서 진화 피드백 루프 — 갱신 실행 흐름

**역할**: §9에서 감지된 트리거를 실제 문서 갱신으로 이어가는 흐름을 정의한다.

#### 업데이트 흐름

```
REPORT 말미: "문서 업데이트 제안" 섹션에 §9 트리거 목록 표시
   ↓
캡틴 승인 절차 (PLAN에서 UX 확정: 일괄 vs 항목별)
   ↓
APPLY 단계: 승인된 제안 실행
   - 방식: opi 재사용 또는 전용 서브 프로세스 (PLAN에서 확정)
   - 대상: docs/CONVENTIONS.md 또는 docs/SECURITY.md
   - 내용: 새 규칙 추가 / 새 섹션 신설
   ↓
다음 `//opgc` 실행 시 갱신된 기준 자동 반영
```

#### 자율 금지 원칙

- **문서 자동 갱신 금지** — 하네스 Guards 준수
- 제안만 수행, 실제 갱신은 캡틴 명시 승인 후에만

#### 세부 사항 (PLAN에서 확정)

- 문서 갱신 방식 (opi 재사용 vs 전용 서브 프로세스)
- 캡틴 승인 UX (일괄 승인 / 항목별 승인 / 참고만 표시)
- 갱신 이력 기록 방식 (Git 커밋 메시지 포맷 + 갱신 로그)

### §11. 030 보안 보류 태스크 흡수

이번 태스크 완료 시 `project_security_task.md` 상태를 `완료(TEST 부분)`로 전환. 설계 보안(PLAN 단계) 범위는 별도 후속 태스크로 분리 유지.

## 요구사항

- [x] **opal-pilot-gc 경량 Pilot 작성** — `opal/skills/opal-pilot-gc/SKILL.md` 생성
  - 무엇을: **5단계 파이프라인**(SCAN→CHECK→REPORT→APPLY→CLOSE), arguments 파싱, STATE.md 도메인 치환값(실행 요약 테이블 포함), Agentic Mode 섹션, DONE.md 템플릿 참조
  - 어디에: `opal/skills/opal-pilot-gc/SKILL.md`
  - 왜: §1, §2, §4
  - AC: (1) frontmatter(name/description, 별칭 `opgc`/`gc`), (2) **5단계 정의**(각 단계 게이트/산출물/워커 디스패치 명시 — CLOSE 포함), (3) STATE.md 도메인 치환값 섹션(모드/단계 목록/파이프라인 현황판 행 예시 + **이번 실행 요약 테이블 템플릿** 포함), (4) arguments 파싱 규칙(`--only`, `--scope`, `--apply`, `--agentic`), (5) 에이전트 병렬 디스패치 프롬프트 템플릿, (6) Agentic Mode 섹션, (7) 태스크 폴더 자동 생성 규칙, (8) **DONE.md 템플릿** 포함, (9) **CLOSE 진입 게이트**(사용자 확인 필수) 준수

- [x] **opal-convention-checker 에이전트 작성** — `opal/agents/opal-convention-checker/AGENT.md` 생성
  - 무엇을: 컨벤션·네이밍·파일 구조·죽은 코드·미사용 import 체크 전담. **프로젝트 `docs/CONVENTIONS.md` 유일 기준**, 부재 시 초안 생성 유도. 출력은 **자기완결 보고서(체크리스트 내장)**
  - 어디에: `opal/agents/opal-convention-checker/AGENT.md`
  - 왜: §1, §6, §8
  - AC: (1) frontmatter(name/description/model), (2) `docs/CONVENTIONS.md` 존재 여부 감지 로직, (3) **존재 시**: 해당 문서 기반 체크, (4) **부재 시**: 체크 생략 + 초안 생성 유도 동작 명시, (5) **출력 포맷 §8 준수**(자기완결 보고서 골격 + 체크리스트 + 5단계 상태 주석 포맷), (6) **프레임워크 내장 공통 컨벤션 기본값 포함 금지**

- [x] **컨벤션 초안 생성 동작 설계** — `opal-convention-checker` 내부 서브 프로세스
  - 무엇을: `docs/CONVENTIONS.md` 부재 시 코드베이스 분석 기반 초안 생성 유도
  - 어디에: `opal-convention-checker/AGENT.md` 또는 별도 헬퍼 스킬
  - 왜: §6
  - AC: (1) PLAN에서 초안 생성 방식 확정(opi 재사용 vs 전용 서브), (2) 코드베이스 샘플 분석 항목 정의(네이밍/들여쓰기/파일 구조/import 순서), (3) 캡틴 승인 절차 포함(자동 저장 금지)

- [x] **opal-security-checker 에이전트 작성** — `opal/agents/opal-security-checker/AGENT.md` 생성
  - 무엇을: 시크릿/OWASP/CWE/SANS/의존성/권한 체크 전담. **2축 구조** (Base + SECURITY.md). 출력은 **자기완결 보고서(체크리스트 내장)**
  - 어디에: `opal/agents/opal-security-checker/AGENT.md`
  - 왜: §1, §7, §8
  - AC: (1) frontmatter, (2) **Base 내장**: OWASP Top 10 + CWE Top 25 + SANS Top 25 체크리스트, (3) `docs/SECURITY.md` 존재 분기 로직(존재 시 병합/부재 시 Base만 + 작성 유도), (4) **커뮤니티 스킬 래핑 호출 방식**(선정 시 정의), (5) **출력 포맷 §8 준수**(자기완결 보고서 골격 + 체크리스트 + 5단계 상태 주석 포맷, CVE/CWE 참조 포함, Base vs 프로젝트 출처 표시)

- [x] **SECURITY.md 초안 생성 동작 설계** — `opal-security-checker` 내부 서브 프로세스
  - 무엇을: `docs/SECURITY.md` 부재 시 기술 스택별 보안(context7) + 코드베이스 분석 기반 프로젝트 커스텀 항목 통합 초안 생성 유도
  - 어디에: `opal-security-checker/AGENT.md` 또는 별도 헬퍼 스킬
  - 왜: §7
  - AC: (1) PLAN에서 초안 생성 방식 확정, (2) context7 MCP 호출 방식과 인용 형식 명시, (3) 코드베이스 분석 항목(인증/인가/시크릿/외부 API) 도출 로직, (4) 캡틴 승인 절차 포함(자동 저장 금지)

- [x] **보고서 구조 확정 (자기완결 + 체크리스트 내장)** — REPORT 단계 산출물 포맷
  - 무엇을: §8 초안(각 에이전트 자기완결 보고서 + 체크리스트 + 5단계 상태 모델 + 심각도/카테고리/지표)을 PLAN에서 최종 확정, EXECUTE에서 템플릿 구현
  - 어디에: `opal/skills/opal-pilot-gc/` 하위 보고서 템플릿 또는 SKILL.md 내부
  - 왜: 캡틴 요청 — 보안 유형/심각성 분류 + 지표 + 체크리스트 기반 적용 관리
  - AC: (1) PLAN.md에 보고서 포맷 명세(섹션/필드/지표/심각도 기준) 포함, (2) 샘플 보고서 1부 포함(보안·컨벤션 각 1), (3) 심각도 경계 케이스 정의, (4) Base/프로젝트 출처 구분 방식 확정, (5) 체크리스트(OWASP 전 항목, CWE Top 25, 컨벤션 카테고리) 전량 열거, (6) 5단계 상태(`[ ] [x] [~] [?] [!]`) 주석 포맷 확정

- [x] **APPLY 실행 방식 확정** — PLAN에서 검토 및 확정
  - 무엇을: §3 실행 모드(A 기본 / B `--apply`) + **자동 상태 결정 규칙**(5가지) + 체크박스·주석 갱신 흐름 + 실패/보류/확인 필요 항목 처리
  - 어디에: PLAN.md 및 `opal-pilot-gc/SKILL.md` APPLY 단계 정의
  - 왜: 캡틴 검토 요청 + 5단계 상태 모델 확정
  - AC: PLAN.md에 (1) APPLY 실행 흐름(기본/플래그 모드), (2) 자동 상태 결정 규칙 5가지 구체화(자동 수정 성공/실패/불가/판단모호/캡틴 보류 판정 알고리즘), (3) 주석 포맷(상태별 필수 기록 항목), (4) 실패/보류/확인 필요 항목의 다음 실행 재가시화 방식, (5) 롤백 방안(부분 실패 시) 명시

- [x] **문서 업데이트 트리거 + 갱신 루프 구현** — §9, §10
  - 무엇을: 단일 실행 내 **빈도(N개 파일 이상)** + **심각도(Critical/High)** + **새 카테고리** 감지 → 제안 생성 → 캡틴 승인 후 CONVENTIONS.md / SECURITY.md 갱신 연계
  - 어디에: `opal-pilot-gc/SKILL.md` REPORT 단계 말미 + APPLY 연계 흐름
  - 왜: §9, §10 — 반복·중요 이슈를 문서 규칙으로 승격시켜 재발 방지 (캡틴 합의 — tracker 도입 없이 단일 실행 내 판단)
  - AC: (1) PLAN.md에 **빈도 임계값 N(파일 수) + 심각도 트리거 범위(Critical/High vs Critical) 확정**, (2) 새 카테고리 감지 알고리즘 정의(기존 문서 섹션 매핑), (3) Fingerprint 알고리즘 세부(단일 실행 내 집계용) 정의, (4) 갱신 방식(opi 재사용 vs 전용 서브 프로세스) 선택 근거 기록, (5) 캡틴 승인 UX(일괄 vs 항목별) 확정, (6) **자동 갱신 금지 + 캡틴 승인 절차** 준수, (7) **이력 저장소(tracker) 도입하지 않음** 명시

- [x] **커뮤니티 보안 스킬 실사 및 등록** — PLAN 단계
  - 무엇을: `openai/security-best-practices`, `getsentry/code-review` 등의 라이선스/품질/접근성/래핑 가능성 실사 → 계층 1 Base 편입 여부 결정
  - 어디에: PLAN.md에 결정 근거. 채택 시 `community-skills/` 또는 `opal/core/references/skills.md` 등록
  - 왜: §7 Base 원칙의 질적 강화
  - AC: PLAN.md에 후보별 실사 결과(라이선스/품질/적용 방식/채택 근거) 기록. 채택 시 EXECUTE에서 실제 통합, 기각 시 OWASP/CWE/SANS만으로 Base 구성됨을 명시

- [x] **레퍼런스 문서 갱신** — 스킬/에이전트 레지스트리 등록
  - 무엇을: 신규 컴포넌트 등록
  - 어디에: `opal/core/references/skills.md` (`opal-pilot-gc`, `opgc` 약어, `gc` 별칭), `opal/core/references/agents.md` (에이전트 2개)
  - 왜: `//opgc` / `//gc` 매칭 및 에이전트 디스패치 전제
  - AC: skill-registry에서 `//opgc` 및 `//gc` 매칭 가능, agents.md에 에이전트 2개 등록

- [x] **install-mac.sh 배포 경로 동기화**
  - 무엇을: 신규 Pilot/에이전트 배포 대상 추가
  - 어디에: `scripts/install-mac.sh`
  - 왜: 확정 기준 §2 — `~/.opal/` 배포 구조와 소스 구조 일치 필수
  - AC: 실행 시 `~/.opal/skills/opal-pilot-gc/`, `~/.opal/agents/opal-convention-checker/`, `~/.opal/agents/opal-security-checker/`가 배포된다 (dry-run 확인 가능)

- [x] **030 보안 보류 메모리 정리** — CLOSE 단계
  - 무엇을: `project_security_task.md` 상태를 `완료(TEST)`로 전환, 설계 보안(PLAN)은 별도 후속으로 분리 유지 명시
  - 어디에: `.opal/memory/project_security_task.md` + `.opal/MEMORY.md` 인덱스
  - 왜: §11
  - AC: 메모리 파일/인덱스가 현재 상태를 정확히 반영, 설계 보안 후속이 별도 항목으로 기록됨

## 제약 조건

- **구현 금지 원칙**: TASK/PLAN 단계에서 실제 Pilot/에이전트 파일 생성 금지. EXECUTE 승인 후만 작성
- **하네스 준수**: 경량 Pilot이어도 Guards/State/게이트는 필수 (산출물만 최소화)
- **플랫폼 독립**: Claude Code, Cursor, Gemini 어디서든 동작 (플랫폼 특정 로직 금지)
- **커뮤니티 스킬 원본 수정 금지**: 래핑만 허용
- **`~/.opal/` 직접 수정 금지**: 소스 경로(`opal/`)에서만 수정 (확정 기준 §2)
- **자동화 범위 제외**: 훅 통합, git pre-commit 통합은 별도 후속
- **커밋 자동화 금지**: 캡틴의 명시 지시 전까지 자동 커밋 금지
- **docs/backup/ git 포함**: 백업 파일은 git에 포함 (확정 기준 §3)
- **트래커 금지**: 이슈 이력 저장소(`.opal/gc/tracker.*`) 도입하지 않음. 단일 실행 내 판단만 사용
- **CLOSE 진입 게이트**: APPLY 단계 사용자 확인 없이는 CLOSE 진입 금지 (하네스 Guards)

## 기술 스택

- OPAL 프레임워크 (Markdown 기반 Pilot/에이전트 정의)
- Bash (`install-mac.sh` 배포 스크립트)
- MCP: `context7` (SECURITY.md 초안 생성 시 스택별 보안 가이드 조회)
- 외부 기준: OWASP Top 10 (2021), CWE Top 25, SANS Top 25

## 관련 문서

- `docs/PROJECT.md` — 프로젝트 정의, 원칙, 문서 허브
- `docs/ARCHITECTURE.md` — 프레임워크 아키텍처
- `docs/CONVENTIONS.md` — 코드/문서 컨벤션 (컨벤션 에이전트 유일 기준)
- `.opal/AGENT.md` — PM 검토 기준
- `.opal/memory/project_security_task.md` — 030 보안 보류 메모리
- `~/.opal/references/opal-harness.md` — 하네스 공통 규칙
- `~/.opal/references/opal-pm.md` — PM 행동 프로세스
- `opal/core/references/skills.md` — 스킬 레지스트리
- `opal/core/references/agents.md` — 에이전트 레지스트리
- `scripts/install-mac.sh` — 배포 스크립트
- `opal/skills/opal-pilot-project/SKILL.md` — 표준 Pilot 참조 (경량 Pilot 설계 시 구조 비교)
- `opal/skills/opal-skill-creator/SKILL.md` — 스킬 생성 표준
- `opal/skills/opal-agent-creator/SKILL.md` — 에이전트 생성 표준
