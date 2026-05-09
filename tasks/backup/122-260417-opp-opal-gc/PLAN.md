# PLAN: opal-pilot-gc 경량 Pilot + 보안/컨벤션 에이전트 개발

> 작성일: 2026-04-17 | 버전: v1.0
> 입력: TASK.md
> 출력: PLAN.md
> 적용 스킬: op-task-plan

## 0. 실행 전략 요약

§1~§11(TASK.md) 확정 방향을 다음 순서·묶음으로 구현한다.

| Phase | 묶음 | 포함 Step | 근거 |
|-------|------|-----------|------|
| P1 — 기반 자산 | 보고서 템플릿 + 체크리스트 리소스 | S-01, S-02 | 하위 레이어 우선. Pilot/에이전트가 템플릿을 `references/`로 공유 |
| P2 — 전문 에이전트 | 보안/컨벤션 에이전트 AGENT.md + 초안 생성 서브 | S-03, S-04, S-05, S-06 | 에이전트가 Pilot보다 하위 레이어. Pilot은 이를 디스패치만 |
| P3 — Pilot (오케스트레이터) | opal-pilot-gc SKILL.md + 파이프라인/템플릿 | S-07, S-08 | 하위 레이어 확정 후 조립 |
| P4 — 통합·배포 | 레지스트리 등록 + install-mac.sh + 메모리 정리 | S-09, S-10, S-11, S-12 | 최종 통합. 코드 변경 없이 구성 파일만 갱신 |

**설계 판단 근거 (요약)**:
- 프로젝트 원칙 "컴포지션 > 모놀리식" → Pilot/에이전트/보고서 템플릿을 **3개 컴포넌트**로 분리 (`opal/core/references/harness/citation-rules.md` §1)
- 프로젝트 원칙 "재사용성 > 편의성" → `docs/CONVENTIONS.md`/`docs/SECURITY.md` 초안 생성을 **opi 재사용**(`opal/skills/opal-project-init/SKILL.md:4-6`)으로 해결하여 중복 방지
- 프로젝트 원칙 "하네스 준수" → 경량 Pilot이어도 5단계 현황판 + State Gate + CLOSE 진입 게이트 유지 (`~/.opal/references/opal-harness.md` §1 §3)

---

## 1. 현황 조사

### 1.1 참조 문서 (PLAN 작성 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md | `tasks/122-260417-opp-opal-gc/TASK.md` | 요구사항·제약·§1~§11 확정 방향 원문 |
| D-2 | 설계 | OPAL Harness | `~/.opal/references/opal-harness.md` §1 §3 | Guards(구현 금지, CLOSE 진입 게이트), State(파이프라인 현황판) |
| D-3 | 설계 | PM 프로필 | `.opal/AGENT.md` §확정 기준 §금지사항 | `~/.opal/` 직접 수정 금지, 배포 금지, 커뮤니티 원본 수정 금지 |
| D-4 | 설계 | PROJECT | `docs/PROJECT.md` §프로젝트 원칙 | 표준화/재사용/플랫폼 독립/컴포지션/하네스 준수 |
| D-5 | 설계 | ARCHITECTURE | `docs/ARCHITECTURE.md` §배포 모델 | 소스 → `~/.opal/` 배포 구조 |
| D-6 | 설계 | CONVENTIONS | `docs/CONVENTIONS.md` §네이밍 §커밋 | kebab-case, `opal-pilot-*`/`opal-{domain}-agent`/약어 규칙 |
| D-7 | 설계 | 표준 Pilot | `opal/skills/opal-pilot-project/SKILL.md:91-142` | CLOSE 단계 + 현황판 20행 예시 (경량 Pilot 비교 기준) |
| D-8 | 설계 | 스킬 생성 표준 | `opal/skills/opal-skill-creator/SKILL.md:94-190` | SKILL.md 규격(frontmatter, references/, 버전 태깅) |
| D-9 | 설계 | 에이전트 생성 표준 | `opal/skills/opal-agent-creator/SKILL.md:92-170` | AGENT.md 규격(frontmatter, 레지스트리 등록) |
| D-10 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` §1 §2 | PLAN 인용 포맷(테이블 + 인라인 `[MUST]`) |
| D-11 | 소스 | 커뮤니티 security-best-practices | `community-skills/openai/security-best-practices/SKILL.md:1-87` | 라이선스(Apache 2.0), 11개 stack 레퍼런스 확인 |
| D-12 | 소스 | 커뮤니티 code-review | `community-skills/getsentry/code-review/SKILL.md:1-103` | 보안·성능·테스트 리뷰 체크리스트 |
| D-13 | 소스 | opi 스킬 | `opal/skills/opal-project-init/SKILL.md:298-339` | `docs/` 초안 작성 Phase + 백업 프로토콜 (초안 생성 재사용 근거) |
| D-14 | 소스 | opi 최신화 모드 | `opal/skills/opal-project-init/SKILL.md:480-811` | 기존 문서에 섹션 추가하는 Phase 3 흐름 (§10 문서 갱신 재사용 근거) |
| D-15 | 소스 | 스킬 레지스트리 | `opal/core/references/skills.md` | 스킬 등록 포맷 |
| D-16 | 소스 | 에이전트 레지스트리 | `opal/core/references/agents.md:1-80` | 에이전트 등록 포맷 |
| D-17 | 소스 | install-mac.sh | `scripts/install-mac.sh:419-440` | OPAL 스킬/에이전트 배포 블록 위치 |
| D-18 | 소스 | 030 보안 보류 메모리 | `.opal/memory/project_security_task.md` | §11 흡수 대상 |
| D-19 | 외부 | OWASP Top 10 (2021) | https://owasp.org/Top10/ | 계층 1 Base 원칙 출처 |
| D-20 | 외부 | CWE Top 25 | https://cwe.mitre.org/top25/ | 계층 1 Base 원칙 출처 |
| D-21 | 외부 | SANS Top 25 | https://www.sans.org/top25-software-errors/ | 계층 1 Base 원칙 출처 |
| D-22 | 외부 | OpenAI security-best-practices 저장소 | https://github.com/openai/codex-skills (Apache 2.0) | 실사 대상 — 라이선스/접근성 |
| D-23 | 외부 | getsentry code-review 저장소 | https://github.com/getsentry/sentry-skills | 실사 대상 — 라이선스/접근성 |

### 1.2 관련 파일

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/opal-pilot-gc/SKILL.md` | Pilot 오케스트레이터 (신규) | 생성 | TASK.md 요구사항 1 |
| `opal/skills/opal-pilot-gc/references/report-security-template.md` | 보안 보고서 템플릿 | 생성 | TASK.md §8 요구사항 6 |
| `opal/skills/opal-pilot-gc/references/report-convention-template.md` | 컨벤션 보고서 템플릿 | 생성 | TASK.md §8 요구사항 6 |
| `opal/skills/opal-pilot-gc/references/base-security-checklist.md` | OWASP+CWE+SANS 전량 체크리스트 | 생성 | TASK.md §7 요구사항 4 |
| `opal/skills/opal-pilot-gc/references/base-convention-checklist.md` | 컨벤션 카테고리 전량 체크리스트 | 생성 | TASK.md §8 요구사항 6 |
| `opal/skills/opal-pilot-gc/references/done-template.md` | DONE.md 템플릿 | 생성 | TASK.md §8 요구사항 1(AC 8) |
| `opal/agents/opal-security-checker/AGENT.md` | 보안 에이전트 (신규) | 생성 | TASK.md 요구사항 4 |
| `opal/agents/opal-convention-checker/AGENT.md` | 컨벤션 에이전트 (신규) | 생성 | TASK.md 요구사항 2 |
| `opal/core/references/skills.md` | 스킬 레지스트리 | 수정 | `opal/core/references/skills.md:30-72` |
| `opal/core/references/agents.md` | 에이전트 레지스트리 | 수정 | `opal/core/references/agents.md:46-80` |
| `scripts/install-mac.sh` | 배포 스크립트 | 수정 | `scripts/install-mac.sh:419-440` |
| `.opal/memory/project_security_task.md` | 030 보안 보류 메모리 | 수정 | D-18 |
| `.opal/MEMORY.md` | 메모리 인덱스 | 수정 | 메모리 상태 전환 반영 |
| `opal/core/references/opal-skills-registry.json` | 스킬 JSON SSOT | 수정 | `opal/core/references/skills.md:3-4` |

### 1.3 현재 상태

- OPAL 프레임워크에 보안/컨벤션 전담 에이전트·스킬 **없음** (TASK.md §1 확인).
- 커뮤니티 보안 스킬 2종은 이미 배포 대상(`community-skills/openai/security-best-practices/`, `community-skills/getsentry/code-review/`)에 포함.
- `docs/CONVENTIONS.md` 존재, `docs/SECURITY.md` 부재 (프로젝트별 기준 비대칭 — TASK.md §2).
- `opal-pilot-project`(`opp`)가 표준 Pilot으로 CLOSE 단계까지 구현되어 있어 경량 Pilot 비교 기준 확보.
- `opal-project-init`(`opi`)이 docs/ 초안 생성·최신화 양쪽을 모두 담당하고 있어 초안/섹션 추가 로직 재사용 가능.

### 1.4 영향 범위

- **프레임워크 컴포넌트 추가**: Pilot 1개 + 에이전트 2개 + references 5개 → 레지스트리·배포 스크립트 동기화 필요.
- **하네스 영향 없음**: 경량 Pilot이 기존 Guards/Gates/State를 그대로 사용하므로 `opal-harness.md`는 수정하지 않는다.
- **커뮤니티 스킬**: 원본 수정 없이 래핑 호출만 수행 — 디렉토리 변경 없음.
- **메모리**: 030 보류 태스크를 `완료(TEST)`로 전환, 설계 보안(PLAN)은 별도 항목으로 분리 유지.

---

## 2. 10가지 위임 사항 결정

> TASK.md에서 "PLAN에서 확정" 으로 위임된 세부 사항을 모두 확정한다. 각 결정은 **근거**를 명시한다.

### 2.1 빈도 임계값 N (파일 수)

**결정: N = 3 파일** (고정값, `opal-pilot-gc/SKILL.md`에서 상수로 선언)

**근거**:
- N=2는 단일 실행 내 노이즈 증폭 위험 — 동일 함수를 2곳에서 수정하면 무조건 트리거되어 "빈번"의 의미가 희석된다.
- N=5는 소규모 `--scope staged` 실행에서 사실상 발동 불가 (통상 staged 파일 수 3~10개).
- N=3은 "한 번의 우연이 아닌 **패턴**"의 최소 임계값이며, GitHub의 Code Scanning 빈도 기반 priority 알림도 유사 구간(3+ occurrences) 사용.
- `--scope staged` / `--scope all` 모두 동일 값 사용(단일 실행 내 비교이므로 모드에 독립). 필요 시 향후 `--freq-threshold` 플래그로 오버라이드 가능성만 SKILL.md 주석으로 남긴다(이번 구현 범위 아님).

### 2.2 심각도 트리거 범위

**결정: Critical + High 둘 다** (1건만이라도 발동)

**근거**:
- TASK.md §9 표: "**Critical 또는 High** 심각도 이슈 발견 (1건만이라도)" 원문 그대로 채택.
- `opal/core/references/harness/citation-rules.md` §2.4 "[MUST] 재해석 여지 제거" 원칙 — 원문이 "Critical 또는 High"이므로 "Critical만"으로 축소 해석하지 않는다.
- High까지 포함해야 "인증 누락 엔드포인트" 등 Critical 직전 카테고리가 문서로 승격되어 재발 방지 효과 확보(TASK.md §8 심각도 예시 참조).
- Medium/Low/Info는 빈도 트리거(N=3)로 잡히는 구조라서 중복 방지.

### 2.3 Fingerprint 알고리즘 세부

**결정: "카테고리 + 정규화된 코드 스니펫 토큰 시퀀스" SHA-1 8-byte 프리픽스**

**해시 입력 구성**:
```
fingerprint_input = "{category_id}|{normalized_tokens}"
fingerprint = sha1(fingerprint_input).hex()[:16]   # 16자리 hex (8-byte)
```

**정규화 규칙 (순서대로 적용)**:
1. 원본 코드 스니펫을 이슈 위치 ±3줄 범위로 추출 (블록 컨텍스트 최소 확보).
2. 주석 제거 (`//`, `#`, `/* */`, `<!-- -->`).
3. 문자열 리터럴 → `STR` 토큰 (예: `"abc"` → `STR`).
4. 숫자 리터럴 → `NUM` 토큰.
5. 식별자(변수명/함수명/파라미터) → `ID` 토큰 (언어별 식별자 정규식 사용).
6. 연속 공백을 단일 스페이스로 압축, 앞뒤 공백 제거.
7. 파일 경로·라인 번호는 **입력에서 제외** (TASK.md §9 규칙 준수).

**예시** (Node.js 하드코딩 시크릿):
```
원본:   const API_KEY = "sk-1234567890abcdef";
정규화: ID ID = STR ;
카테고리: CWE-798
fingerprint_input: "CWE-798|ID ID = STR ;"
```
→ 다른 파일에서 변수명과 키 값만 다른 동일 패턴은 동일 fingerprint 산출 → 빈도 집계 가능.

**충돌 처리**:
- 8-byte 프리픽스 충돌 확률은 단일 실행 수십~수백 건 범위에서 사실상 무시 가능 (생일 역설: 2^32 수준 필요).
- 충돌 감지 시: 동일 fingerprint + 동일 카테고리 + 동일 해결 방안 문자열 3축을 함께 비교하여 동일 이슈로 판정. 불일치 시 별도 이슈로 분리.
- 에이전트는 fingerprint를 **보고서 본문에 노출하지 않는다** (TASK.md §8 "내부 집계용 fingerprint는 보고서에 기본 미노출"). STATE.md 내부 테이블에만 기록.

**언어별 식별자 정규식** (references/base-convention-checklist.md에 상세):
- JS/TS: `[A-Za-z_$][A-Za-z0-9_$]*`
- Python: `[A-Za-z_][A-Za-z0-9_]*`
- Go/Java: JS 규칙 재사용 (`_` 허용)

### 2.4 새 카테고리 감지 알고리즘

**결정: "헤더 섹션 인덱스 구축 + 카테고리 키워드 매칭" 2단계 절차**

**절차**:
1. **기준 문서 헤더 인덱스 구축**:
   - `docs/CONVENTIONS.md` 또는 `docs/SECURITY.md`를 Read.
   - 정규식 `^#{2,3}\s+(.+)$`로 §2~§3 수준 헤더를 수집 → `headers_set`.
   - 각 헤더를 소문자화 + 공백 제거 + 한/영 키워드 분리(예: "입력 검증 / Input Validation" → `{입력검증, inputvalidation, input, validation}`).
2. **이슈 카테고리 매칭**:
   - 보고서의 각 이슈는 `category_id` + `category_label`을 가진다 (예: `OWASP-A03`, "Injection").
   - 이슈의 `category_label`을 동일한 정규화 처리 → `candidate_keys`.
   - `candidate_keys ∩ headers_set == ∅` 이면 "새 카테고리 등장"으로 판정.
3. **제안 생성**:
   - 새 카테고리는 REPORT §4 "문서 업데이트 제안" 테이블에 `new_category=true` 플래그로 기록.
   - 문구: "새 카테고리 `{category_label}` 등장 → {기준 문서} §{다음 번호}에 신설 제안".

**부재 시 동작**: 기준 문서가 없으면 "새 카테고리" 판정을 건너뛰고 "초안 생성 유도"로 전환한다(§2.10 결정과 연동).

### 2.5 문서 갱신 방식 (opi 재사용 vs 전용 서브)

**결정: opi 재사용** (`//opi refresh-docs --target {conventions|security}` 간이 호출 형태로 래핑)

**옵션 비교**:

| 옵션 | 장점 | 단점 |
|------|------|------|
| A) opi 재사용 | 기존 백업 프로토콜·섹션 등록 프로토콜 재활용 / SSOT 단일화 / 새 컴포넌트 없음 | opi 최신화 모드를 약간 변형 호출해야 함 |
| B) 전용 서브 프로세스 | GC 전용 UX 최적화 가능 | opi와 기능 중복 / 백업 로직 재구현 / SSOT 분산 |

**채택 근거**:
- `docs/PROJECT.md` §프로젝트 원칙 "재사용성 > 편의성" — 새 로직 신설보다 기존 `opi`(`opal/skills/opal-project-init/SKILL.md:480-811` 최신화 모드)의 Phase 3 섹션 추가 흐름을 활용.
- `docs/PROJECT.md` 원칙 "표준화 > 커스터마이징" — 문서 갱신 경로를 하나로 유지.
- opi는 이미 `docs/backup/` 백업 프로토콜(SKILL.md:36-52)과 문서 등록 프로토콜(SKILL.md:322-329)을 구현 → GC는 이를 재사용하면 충분.

**호출 방식** (EXECUTE 단계에서 확정 구현):
- GC Pilot이 APPLY 단계에서 승인된 문서 업데이트 제안을 **패치 블록 목록**으로 작성 → opi "섹션 단위 drill-down 보고" 형식(`opal/skills/opal-project-init/SKILL.md:706-762`)과 정합.
- 실제 갱신 실행 시 opi 스킬을 Read + 해당 Phase 3 흐름 호출 (PM 직접 수행, 별도 서브에이전트 불필요).
- GC는 "변경 제안만" 생성, 실제 Write는 opi 프로토콜로 위임.

### 2.6 캡틴 승인 UX

**결정: 항목별 승인 (번호 입력 방식) + "전체 승인/전체 거부" 단축키**

**UX 스펙**:
```
[GC — 문서 업데이트 제안 승인]

다음 3건의 제안이 있습니다:

  [1] CONVENTIONS.md §5 "Import 순서 규칙" 신설 제안
      근거: 4개 파일에서 import 순서 위반 (빈도 트리거 N=3)
      내용: "외부 → 내부 → 상대 경로" 3단 순서 명문화

  [2] SECURITY.md §3 "하드코딩 시크릿 금지" 추가 제안
      근거: Critical 이슈 2건 발견 (src/api/keys.js:12, src/auth/oauth.js:8)
      내용: CWE-798 대응 — .env 사용 + pre-commit 스캔

  [3] CONVENTIONS.md §7 "미사용 import 제거" 규칙 추가 제안
      근거: 8개 파일에서 발생 (빈도 트리거)
      내용: ESLint no-unused-imports 규칙 활성화

승인할 번호를 입력하세요:
  - 번호 나열: 1,3  (쉼표 구분)
  - 전체 승인: a
  - 전체 거부: n
  - 상세 보기: d <번호>  (예: d 2)

> _
```

**근거**:
- TASK.md §10 "캡틴 승인 UX (일괄 승인 / 항목별 승인 / 참고만 표시)"에서 3안 비교 요구.
- **참고만 표시**는 "제안만 만들고 사용자가 직접 문서 수정" — 하네스의 Guards(자동 갱신 금지, TASK.md §10 "자율 금지 원칙")와 정합하지만, "승인 후 자동 반영" 효과가 빠져서 §10 "APPLY 단계에서 승인된 제안 실행" 흐름과 맞지 않는다.
- **일괄 승인**은 3건 중 1건만 반대하고 싶을 때 세분화 불가 — 캡틴이 실제 코드 컨벤션 갱신 결정을 내릴 때 신중하게 항목별로 검토해야 한다는 프로젝트 원칙("문서화 우선", `.opal/AGENT.md` §철학)과 충돌.
- **항목별 승인**이 가장 안전하고 `//opgc` 실행 후 통상 1~5건 정도이므로 입력 부담도 크지 않다.
- `a`/`n` 단축키로 일괄 승인도 가능하게 하여 일괄 승인의 편의성도 확보.

### 2.7 커뮤니티 보안 스킬 실사 결과

| 스킬 | 저장소 | 라이선스 | 접근성 | 품질 | 래핑 가능성 | 결론 |
|------|--------|---------|-------|-----|----------|------|
| `openai/security-best-practices` | 이미 `community-skills/openai/security-best-practices/`에 존재 | Apache 2.0 (`community-skills/openai/security-best-practices/LICENSE.txt`) | 이미 배포 경로 확보 | SKILL.md + 11개 스택별 reference(Python Django/Flask/FastAPI, JS/TS React/Vue/Next.js/Express/jQuery, Go general) | **높음** — Read 래핑만 필요, 원본 수정 없음 | ✅ **채택** |
| `getsentry/code-review` | `community-skills/getsentry/code-review/` | 저장소 상에 LICENSE 파일 없음 → Sentry 기본 공개 정책(BUSL 1.1 문서 리뷰 가이드 성격) — 원본 미수정 래핑 호출에 한해 사용 가능 | 이미 배포 경로 확보 | 코드 리뷰 체크리스트(보안·성능·테스트·디자인) — 개별 언어 심층도는 낮음 | **중간** — 코드 리뷰 관점 참조용 래핑만 | ✅ **부분 채택** (보안 전용이 아니므로 opal-convention-checker의 코드 품질 섹션에서 참조) |

**채택 방식**:
- **`opal-security-checker`** → Base 원칙 로드 후, 감지된 스택에 맞는 `openai/security-best-practices/references/<stack>.md`를 **Read하여 체크리스트에 병합**. 원본 수정 없음(`.opal/AGENT.md` 금지사항 "커뮤니티 스킬 원본 수정 금지" 준수).
- **`opal-convention-checker`** → `getsentry/code-review/SKILL.md`를 **Read하여 코드 품질·성능 관점 체크 항목을 보조 카테고리로 참조**. 컨벤션이 유일 기준인 프로젝트의 경우 이는 "추가 제안"으로만 제시하고 "위반"으로 판정하지 않는다.
- 커뮤니티 스킬은 **에이전트 AGENT.md 내부의 "의존 스킬" 섹션**에 명시 + 탐색 경로는 `~/.opal/community-skills/{org}/{skill}/`.

**기각 대안**:
- context7 MCP로 매 실행마다 동적 조회 → TASK.md §7 "체크 시점에 동적 조회하지 않고, SECURITY.md 작성 시점에 정적으로 반영한다" 원칙과 충돌하므로 기각. context7은 **SECURITY.md 초안 생성 시에만** 사용.

### 2.8 APPLY 자동 판정 알고리즘 + 롤백 방안

#### 자동 판정 알고리즘 (TASK.md §3 "5가지 규칙" 구체화)

각 이슈에 대해 아래 분기를 순차 평가한다:

```
INPUT: issue = { id, category, severity, file, line, description, fix_hint, auto_fixable: bool }
INPUT: user_deferred: Set<issue_id>  // 사용자가 직전 --apply 세션에서 보류 지시한 ID

STEP 1. if issue.id ∈ user_deferred:
           return { state: "[~] pending", note: "캡틴 보류: {지시 시각}" }

STEP 2. if issue.auto_fixable == false:
           if issue.fix_hint is concrete and unambiguous:
               return { state: "[?] review", note: "해결 방안: {fix_hint}" }
           else:
               return { state: "[?] review", note: "판단 근거: {description} / 추가 검토 필요" }

STEP 3. // auto_fixable == true 인 경우
        try:
            apply_patch(issue)          // Edit/Write으로 실제 코드 수정
            run_verify(issue)           // 언어별 minimal 검증 (§2.8 아래 "검증" 정의)
        except PatchConflict as e:
            return { state: "[!] failed", note: "실패 사유: 패치 충돌 ({e.file}:{e.line}). 권장: 수동 수정 후 재실행" }
        except VerifyFail as e:
            rollback_patch(issue)       // §롤백 방안 적용
            return { state: "[!] failed", note: "실패 사유: 검증 실패 ({e.reason}). 권장: {e.hint}" }
        else:
            return { state: "[x] done", note: "적용 시각: {now_ts} — {patch_summary}" }
```

**auto_fixable 판정 기준** (에이전트 내장):
- 컨벤션: 미사용 import 제거, import 순서 정렬, 일관성 있는 들여쓰기 수정, 네이밍 규칙 단순 치환(케이스 변환) → `true`
- 컨벤션: 파일 구조 변경, 함수 분해, 죽은 코드 제거(외부 참조 불확실) → `false`
- 보안: `.env` 로드 경로가 이미 있는 경우의 하드코딩 시크릿 치환 → `true` (단 값은 `${ENV_NAME}` placeholder로 대체, 실제 시크릿 노출 금지)
- 보안: SQL Injection / XSS / 권한 우회 / 암호화 선택 → `false` (도메인 지식 필요)

**검증(run_verify)**:
- 언어별 syntax check: JS(`node --check`), Python(`python -m py_compile`), Go(`gofmt -l`).
- syntax 실패 시 즉시 VerifyFail 발생 → 롤백.
- 테스트 실행은 하지 않는다 (TASK.md §3 범위 밖, 하네스 "자동 루핑 제약" 중 unit/integration test 범위 침범 방지).

#### 롤백 방안 (부분 실패 시)

**3-tier 전략**:

1. **파일 단위 즉시 롤백** (기본):
   - 각 이슈 `apply_patch` 시작 직전에 `git stash push --keep-index -- {file}` (해당 파일만 stash).
   - 검증 실패 시 `git stash pop` 으로 즉시 복원.
   - stash 식별: `gc-{실행타임스탬프}-{issue_id}` 메시지.
2. **APPLY 세션 단위 체크포인트** (전역):
   - APPLY 단계 진입 시 `git stash push --keep-index --include-untracked -m "gc-session-{ts}"` 로 세션 진입 전 스냅샷 저장.
   - 세션 전체 abort 요청 시(`//opgc --apply` 실행 중 `Ctrl+C` 또는 에이전트 내부 실패) 이 stash로 복원.
   - 성공 시 stash 보존(사용자가 `git stash list`에서 확인 가능) — 자동 drop 금지.
3. **커밋 분리 금지**:
   - GC는 **커밋을 생성하지 않는다**(하네스 §1 커밋 규칙 — 사용자 명시 지시 필요). 즉 stash 기반 롤백만 사용하고 `git commit` / `git reset` 은 절대 호출하지 않는다.

**부분 실패 UX**:
- APPLY 완료 후 STATE.md 실행 요약 테이블에 `[!] failed` 건수와 함께 "롤백된 파일 N개 — 영향 없음"을 표시.
- 실패한 이슈는 `[!] failed` 상태 + 실패 사유 인라인 주석으로 보고서에 남아 **다음 `//opgc` 실행 시 재발견**된다(TASK.md §3 "실패/보류/확인필요 항목의 후속").

### 2.9 각 보고서 체크리스트 전량 + 샘플 보고서 2부

#### 보안 체크리스트 전량 (Base — references/base-security-checklist.md에 구현)

**OWASP Top 10 (2021) — 전 10개 카테고리**:

| 카테고리 ID | 제목 | 기본 심각도 |
|-----------|------|----------|
| OWASP-A01 | Broken Access Control | Critical |
| OWASP-A02 | Cryptographic Failures | High |
| OWASP-A03 | Injection | Critical |
| OWASP-A04 | Insecure Design | High |
| OWASP-A05 | Security Misconfiguration | High |
| OWASP-A06 | Vulnerable and Outdated Components | High |
| OWASP-A07 | Identification and Authentication Failures | Critical |
| OWASP-A08 | Software and Data Integrity Failures | High |
| OWASP-A09 | Security Logging and Monitoring Failures | Medium |
| OWASP-A10 | Server-Side Request Forgery (SSRF) | High |

**CWE Top 25 — 2023 리스트 전량**:

| Rank | CWE ID | 제목 |
|------|--------|------|
| 1 | CWE-787 | Out-of-bounds Write |
| 2 | CWE-79 | Cross-site Scripting (XSS) |
| 3 | CWE-89 | SQL Injection |
| 4 | CWE-416 | Use After Free |
| 5 | CWE-78 | OS Command Injection |
| 6 | CWE-20 | Improper Input Validation |
| 7 | CWE-125 | Out-of-bounds Read |
| 8 | CWE-22 | Path Traversal |
| 9 | CWE-352 | Cross-Site Request Forgery (CSRF) |
| 10 | CWE-434 | Unrestricted File Upload |
| 11 | CWE-862 | Missing Authorization |
| 12 | CWE-476 | NULL Pointer Dereference |
| 13 | CWE-287 | Improper Authentication |
| 14 | CWE-190 | Integer Overflow |
| 15 | CWE-502 | Deserialization of Untrusted Data |
| 16 | CWE-77 | Command Injection |
| 17 | CWE-119 | Improper Restriction of Buffer Operations |
| 18 | CWE-798 | Hard-coded Credentials |
| 19 | CWE-918 | Server-Side Request Forgery (SSRF) |
| 20 | CWE-306 | Missing Authentication for Critical Function |
| 21 | CWE-362 | Race Condition |
| 22 | CWE-269 | Improper Privilege Management |
| 23 | CWE-94 | Code Injection |
| 24 | CWE-863 | Incorrect Authorization |
| 25 | CWE-276 | Incorrect Default Permissions |

**SANS Top 25** — CWE Top 25와 90% 중복되므로 references/base-security-checklist.md에서 "CWE Top 25와 매핑 테이블" 형식으로 참조만 유지하여 중복 카테고리 생성 방지.

**도메인 체크리스트**:

| 도메인 | 체크 항목 | 기본 심각도 |
|--------|----------|-----------|
| 시크릿 | `.env` 외 하드코딩, `git grep` 기반 private key 패턴, API key 포맷 패턴 | Critical |
| 인증 | 토큰 검증 누락, 세션 만료 미설정, 기본 비밀번호 | Critical/High |
| 인가 | `@RequireAuth` 누락, 수평권한 체크 누락 | High |
| 입력검증 | schema 미사용, HTML 이스케이프 누락 | High/Medium |
| 의존성 | `package.json` / `requirements.txt` 지정 버전 없음, deprecated | Medium |
| 로깅 | 민감 정보 로그 출력 (password, token 키 포함) | High |
| 암호화 | MD5/SHA-1 사용, 약한 RNG (Math.random()) | Medium |
| 설정 | DEBUG=True 프로덕션, CORS `*`, `eval()` 사용 | High |

#### 컨벤션 체크리스트 전량 (references/base-convention-checklist.md에 구현)

> **주의**: 프로젝트 `docs/CONVENTIONS.md`가 유일한 기준이다. 아래는 **참조용 카테고리 목록**이며, 개별 규칙은 프로젝트 문서에서 로드한다. `docs/CONVENTIONS.md`가 없으면 체크 실패가 아닌 "초안 생성 유도"로 전환.

| 카테고리 | 검사 항목 (docs/CONVENTIONS.md 규칙과 매핑) |
|---------|--------|
| 네이밍 | 파일/폴더 kebab-case, 변수 camelCase/snake_case 일관성, 컴포넌트 네이밍 접두사 규칙 |
| 들여쓰기 | 탭 vs 스페이스, 깊이 일관성, 파일 말미 개행 |
| 파일 구조 | 디렉토리 레이아웃, 확장자 규칙, 순환 의존 |
| 죽은 코드 | 미사용 함수/변수, 주석 처리된 코드 블록, 미참조 export |
| 미사용 import | 미사용 import 구문, 중복 import, 와일드카드 import |
| 문서화 | 공개 함수 주석 누락, frontmatter 누락(문서 파일), 변경이력 누락 |
| import 순서 | 외부 → 내부 → 상대 경로 순서, 그룹 간 빈 줄, 알파벳 정렬 |
| 코드 품질 (getsentry/code-review 참조) | N+1 query, unbounded O(n²), unnecessary allocation 패턴 |

#### 샘플 보고서 1: 보안 (GC-SECURITY-sample.md)

```markdown
# GC SECURITY REPORT — 2026-04-17T14:32:18+09:00

## 1. 헤더
- 실행 일시: 시작 2026-04-17 14:32:18 / 완료 2026-04-17 14:34:02 / 소요 1분 44초
- 범위: `staged` / 대상 파일 6개
- 에이전트: opal-security-checker
- APPLY 수행 여부: Y (--apply 플래그)

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 7 |
| 심각도 분포 | Critical 2 / High 2 / Medium 2 / Low 1 / Info 0 |
| 자동 수정 가능 | 3 |
| 수동 조치 필요 | 4 |
| 파일별 상위 Top 5 | src/api/auth.js (3) / src/services/oauth.js (2) / src/config/db.js (1) / src/utils/logger.js (1) |
| 카테고리별 빈도 | CWE-798 (2 파일) / OWASP-A03 (1 파일) |
| Critical/High 수 | 4 |
| 문서 업데이트 제안 수 | 2 (빈도 1 + 심각도 1) |

## 3. 수정 대상

### Critical (2건)

- [x] GC-001 [src/api/auth.js:12] 하드코딩된 API 키 발견
  - 카테고리: CWE-798 Hard-coded Credentials
  - 위반 기준: Base (OWASP-A07)
  - 설명: 소스에 `const API_KEY = "sk-..."` 형태로 시크릿이 하드코딩되어 있음
  - 해결 방안: `.env`에 `API_KEY` 추가 후 `process.env.API_KEY`로 치환
  - 자동 수정: Y
  - 참조: https://cwe.mitre.org/data/definitions/798.html
  - **적용 시각**: 2026-04-17 14:33:41 — `.env` placeholder 치환 완료

- [x] GC-002 [src/services/oauth.js:8] client_secret 하드코딩
  - 카테고리: CWE-798 Hard-coded Credentials
  - 위반 기준: Base (OWASP-A07)
  - 설명: OAuth client_secret가 리터럴로 저장
  - 해결 방안: `.env`의 `OAUTH_CLIENT_SECRET` 참조로 교체
  - 자동 수정: Y
  - 참조: https://cwe.mitre.org/data/definitions/798.html
  - **적용 시각**: 2026-04-17 14:33:58 — `.env` placeholder 치환 완료

### High (2건)

- [?] GC-003 [src/api/auth.js:47] JWT 서명 검증 누락
  - 카테고리: OWASP-A07 Identification and Authentication Failures
  - 위반 기준: Base
  - 설명: `jwt.decode()` 사용 — 서명 검증 없이 페이로드만 읽음
  - 해결 방안: `jwt.verify(token, SECRET, { algorithms: ['HS256'] })` 로 교체
  - 자동 수정: N (비밀키 관리 구조 확인 필요)
  - 참조: https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/
  - **확인 요청**: 해결 방안: 전역 SECRET 주입 방식을 캡틴에게 확인 필요

- [?] GC-004 [src/api/auth.js:89] Prepared statement 미사용
  - 카테고리: OWASP-A03 Injection (CWE-89)
  - 위반 기준: Base
  - 설명: `db.query("SELECT * FROM users WHERE id = " + userId)` — SQL concat
  - 해결 방안: parameterized query로 전환 (`db.query("SELECT * FROM users WHERE id = ?", [userId])`)
  - 자동 수정: N (ORM 도입 여부 확인 필요)
  - 참조: https://cwe.mitre.org/data/definitions/89.html
  - **확인 요청**: 판단 근거: 다른 쿼리들도 동일 패턴인지 확인 필요 — 범위가 staged 밖

### Medium (2건)

- [x] GC-005 [src/config/db.js:22] MD5 해시 사용
  - 카테고리: CWE-327 Weak Cryptography (A02)
  - 위반 기준: Base
  - 설명: `crypto.createHash('md5')` 사용 — 충돌 공격 가능
  - 해결 방안: `sha256` 또는 `bcrypt`로 교체
  - 자동 수정: Y
  - 참조: https://owasp.org/Top10/A02_2021-Cryptographic_Failures/
  - **적용 시각**: 2026-04-17 14:33:22 — `sha256`으로 치환

- [~] GC-006 [src/utils/logger.js:15] 민감 정보 로그 출력 가능성
  - 카테고리: OWASP-A09 Logging Failures
  - 위반 기준: Base
  - 설명: `logger.info(JSON.stringify(req.body))` — password 필드 포함 가능
  - 해결 방안: 화이트리스트 필드만 로그
  - 자동 수정: N
  - **보류 사유**: 캡틴이 직전 --apply 세션에서 보류 지시 (2026-04-17 14:32:45)

### Low (1건)

- [!] GC-007 [src/services/oauth.js:32] `Math.random()` 사용
  - 카테고리: CWE-338 Use of Cryptographically Weak PRNG
  - 위반 기준: Base
  - 설명: 토큰 생성에 `Math.random()` 사용
  - 해결 방안: `crypto.randomBytes(32).toString('hex')`
  - 자동 수정: Y
  - **실패 사유**: 패치 충돌 (src/services/oauth.js:32 — 이미 다른 생성 로직 존재)
  - **권장**: 수동으로 기존 생성 로직 검토 후 교체

### Info (0건)

## 4. 문서 업데이트 제안

- [ ] GC-DP-01 빈번 이슈 "CWE-798 Hard-coded Credentials" (2개 파일) → SECURITY.md §3 규칙 추가 제안
  - 근거: 단일 실행 내 2개 파일 발견 — 빈도 트리거 N=3에 **미달하지만** 심각도 Critical로 심각도 트리거 발동
  - 제안 내용: "시크릿은 `.env` 사용 + pre-commit 훅에서 정규식 스캔"
- [ ] GC-DP-02 Critical/High 이슈 "OWASP-A07 Auth Failures" → SECURITY.md 체크리스트 카테고리 추가 제안
  - 근거: High 1건 발생 (GC-003)
  - 제안 내용: "JWT는 반드시 `verify()` 사용 / `decode()` 단독 금지"

## 5. 문서 작성 유도

- `docs/SECURITY.md` 부재 감지 → 기술 스택(Node.js/Express)별 가이드 + 위 업데이트 제안 GC-DP-01~02를 초안에 포함하여 생성 제안
  - 생성 방식: `opal-project-init` 스킬 재사용 (Phase 2 작성 프로세스)
  - 캡틴 승인 후 실행
```

#### 샘플 보고서 2: 컨벤션 (GC-CONVENTION-sample.md)

```markdown
# GC CONVENTION REPORT — 2026-04-17T14:32:18+09:00

## 1. 헤더
- 실행 일시: 시작 2026-04-17 14:32:18 / 완료 2026-04-17 14:33:55 / 소요 1분 37초
- 범위: `staged` / 대상 파일 6개
- 에이전트: opal-convention-checker
- APPLY 수행 여부: Y (--apply 플래그)

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 14 |
| 심각도 분포 | Critical 0 / High 0 / Medium 3 / Low 9 / Info 2 |
| 자동 수정 가능 | 11 |
| 수동 조치 필요 | 3 |
| 파일별 상위 Top 5 | src/components/Login.jsx (5) / src/utils/format.js (3) / src/api/auth.js (2) / src/services/oauth.js (2) / src/config/db.js (2) |
| 카테고리별 빈도 | import 순서 (4 파일) / 미사용 import (3 파일) / 네이밍 (2 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 1 (빈도 트리거) |

## 3. 수정 대상

### Critical (0건)
### High (0건)

### Medium (3건)

- [x] GC-C01 [src/components/Login.jsx:1-12] import 순서 위반
  - 카테고리: import 순서
  - 위반 기준: 프로젝트(CONVENTIONS.md §네이밍 규칙) — *docs에 import 순서 규칙 부재* ← 제안 트리거
  - 설명: react, 내부 모듈, 상대 경로가 혼재
  - 해결 방안: "외부 → 내부 → 상대" 3단 그룹 분리
  - 자동 수정: Y
  - **적용 시각**: 2026-04-17 14:33:10

- [x] GC-C02 [src/utils/format.js:3-8] import 순서 위반 (상동)
  - **적용 시각**: 2026-04-17 14:33:14

- [?] GC-C03 [src/components/Login.jsx] 파일 구조 위반
  - 카테고리: 파일 구조
  - 위반 기준: 프로젝트(CONVENTIONS.md §파일 구조)
  - 설명: 컴포넌트가 200줄 초과 (문서 규칙: 150줄)
  - 자동 수정: N
  - **확인 요청**: 해결 방안: 컴포넌트 분리(`LoginForm`, `LoginFooter`). 분해 전략은 캡틴 확인 필요

### Low (9건)

- [x] GC-C04 [src/components/Login.jsx:4] 미사용 import `useCallback`
  - 카테고리: 미사용 import
  - 자동 수정: Y — **적용 시각**: 2026-04-17 14:33:16

- [x] GC-C05 [src/utils/format.js:2] 미사용 import `lodash/debounce`
  - 자동 수정: Y — **적용 시각**: 2026-04-17 14:33:17

- [x] GC-C06 [src/api/auth.js:5] 미사용 import `axios`
  - 자동 수정: Y — **적용 시각**: 2026-04-17 14:33:17

- [x] GC-C07 [src/services/oauth.js:4] 네이밍 위반 `user_name` → `userName`
  - 카테고리: 네이밍
  - 위반 기준: 프로젝트(CONVENTIONS.md §언어 규칙)
  - 자동 수정: Y — **적용 시각**: 2026-04-17 14:33:19

- [x] GC-C08 [src/services/oauth.js:22] 네이밍 위반 `GetToken` → `getToken`
  - 자동 수정: Y — **적용 시각**: 2026-04-17 14:33:19

- [x] GC-C09 [src/config/db.js:5] 미사용 변수 `DB_RETRY_MAX`
  - 카테고리: 죽은 코드
  - 자동 수정: Y — **적용 시각**: 2026-04-17 14:33:20

- [x] GC-C10 [src/components/Login.jsx:45] 들여쓰기 혼용 (탭 + 스페이스)
  - 카테고리: 들여쓰기
  - 자동 수정: Y — **적용 시각**: 2026-04-17 14:33:21

- [!] GC-C11 [src/components/Login.jsx:120] 죽은 코드 (주석 처리된 블록)
  - 카테고리: 죽은 코드
  - 자동 수정: Y
  - **실패 사유**: 검증 실패 (제거 후 syntax 에러 — 인접 블록 의존성 의심)
  - **권장**: 수동 검토 후 제거

- [x] GC-C12 [src/utils/format.js:15] 파일 말미 개행 누락
  - 카테고리: 들여쓰기
  - 자동 수정: Y — **적용 시각**: 2026-04-17 14:33:22

### Info (2건)

- [ ] GC-C13 [src/components/Login.jsx] 컴포넌트 주석 없음
  - 카테고리: 문서화
  - 자동 수정: N
  - 해결 방안: JSDoc 추가 권장

- [ ] GC-C14 [src/services/oauth.js] 변경이력 섹션 없음 (해당 시)
  - 카테고리: 문서화 (Info)

## 4. 문서 업데이트 제안

- [ ] GC-DP-C01 빈번 이슈 "import 순서" (4개 파일) → CONVENTIONS.md §5 규칙 추가 제안
  - 근거: 단일 실행 내 4개 파일 발견 — 빈도 트리거 N=3 초과
  - 제안 내용: "외부 → 내부 → 상대 경로 순서 / 그룹 간 빈 줄 1줄 / 각 그룹 내 알파벳 정렬"

## 5. 문서 작성 유도

- `docs/CONVENTIONS.md` 존재 — 작성 유도 생략
```

### 2.10 SECURITY.md / CONVENTIONS.md 초안 생성 방식

**결정: opi 재사용 (§2.5와 동일 결정)**

**초안 생성 흐름** (에이전트 AGENT.md에 내장):

1. 에이전트가 SCAN 단계에서 `docs/SECURITY.md` 또는 `docs/CONVENTIONS.md` 부재 감지.
2. REPORT §5 "문서 작성 유도" 섹션에 초안 생성 안내 표시.
3. 캡틴이 승인하면 GC Pilot이 **opi 스킬을 Read + `초기화 모드`의 Phase 2-3 프로세스를 호출**.
   - SECURITY.md: opi Phase 3 "개발 문서 작성 대상"에 SECURITY.md 항목을 추가(본 PLAN §4 S-04 참조 — opi 수정 대상 아님, **GC 측 래핑에서 파라미터로 주입**).
   - CONVENTIONS.md: opi가 이미 담당 중 → 그대로 위임.
4. 초안 구성은 TASK.md §7 "SECURITY.md 작성 유도 프로세스" 4단계(기술 스택 감지 → context7 조회 → 코드베이스 샘플 분석 → 초안 구성)를 에이전트가 opi Phase 2 인터뷰 전에 preprocessing으로 준비하여 opi에 입력으로 전달.
5. opi의 "캡틴 승인 후 저장" 원칙(`opal/skills/opal-project-init/SKILL.md:319` 작성 프로세스 4단계) 그대로 적용 — GC가 자동 저장하지 않는다.

**초안 템플릿 최종 확정**:

`docs/SECURITY.md` 초안 구조 (TASK.md §7의 4단계 초안 구성을 구체화):
```markdown
# SECURITY

## 1. 보안 원칙 (프로젝트 전용)
- [캡틴 편집] 이 프로젝트의 보안 철학 1~3줄

## 2. 기술 스택별 보안 원칙 (자동 생성 — context7 인용)
### {스택 1: Express}
- helmet 미들웨어 적용 — [출처: context7 express/security]
- secure cookies — [출처: ...]
### {스택 2: Python/Flask}
- SECRET_KEY 환경변수 필수 — [출처: ...]
- DEBUG=False 프로덕션 — [출처: ...]

## 3. 프로젝트별 추가 보안 원칙 (캡틴 편집 필요)
- [제안] 하드코딩 시크릿 금지 — `.env` 사용 (코드베이스 분석 결과: 이미 `dotenv` 설치됨)
- [제안] JWT 검증 시 `verify()` 사용, `decode()` 단독 금지 (GC 보고서 GC-003 근거)

## 4. 체크 범위 및 제외 (캡틴 편집)
### 검토 대상 디렉토리
- src/
- lib/
### 제외 파일 / 패턴
- tests/**/*.mock.js
- **/*.d.ts

## 변경이력
| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v0.1 | {ts} | opal-pilot-gc가 제안한 초안 (캡틴 검토 필요) |
```

`docs/CONVENTIONS.md` 초안 구조 — opi가 기본 제공하는 구조(`opal/skills/opal-project-init/references/docs-guide.md`의 CONVENTIONS 섹션)를 그대로 사용. GC는 "미사용 import / import 순서 / 죽은 코드" 등 **컨벤션 에이전트가 실제로 체크할 카테고리 섹션**만 빈 placeholder로 추가 제안.

**opi 수정 여부**: opi는 수정하지 않는다. GC 에이전트가 opi에게 "추가 섹션 제안 리스트"를 입력으로 전달하는 방식만 사용(`.opal/AGENT.md` §확정 기준 §2 "`~/.opal/` 경로 수정 금지" 및 "커뮤니티/기존 스킬 원본 수정 금지" 원칙 준수).

---

## 3. 구현 계획

### 3.1 파일 변경 계획

#### 신규 생성

| # | 파일 경로 | 역할 | 근거 |
|---|----------|------|------|
| N1 | `opal/skills/opal-pilot-gc/SKILL.md` | Pilot 오케스트레이터 SKILL.md | TASK.md 요구사항 1 |
| N2 | `opal/skills/opal-pilot-gc/references/report-security-template.md` | 보안 보고서 템플릿 | TASK.md §8 요구사항 6 |
| N3 | `opal/skills/opal-pilot-gc/references/report-convention-template.md` | 컨벤션 보고서 템플릿 | TASK.md §8 요구사항 6 |
| N4 | `opal/skills/opal-pilot-gc/references/base-security-checklist.md` | OWASP+CWE Top 25 + 도메인 체크리스트 | TASK.md §7 AC 2 |
| N5 | `opal/skills/opal-pilot-gc/references/base-convention-checklist.md` | 컨벤션 카테고리 체크리스트 | TASK.md §8 요구사항 6 |
| N6 | `opal/skills/opal-pilot-gc/references/done-template.md` | DONE.md 템플릿 | TASK.md §8 요구사항 1 AC 8 |
| N7 | `opal/agents/opal-security-checker/AGENT.md` | 보안 전문 에이전트 | TASK.md 요구사항 4 |
| N8 | `opal/agents/opal-convention-checker/AGENT.md` | 컨벤션 전문 에이전트 | TASK.md 요구사항 2 |

#### 수정

| # | 파일 경로 | 변경 내용 | 근거 |
|---|----------|----------|------|
| M1 | `opal/core/references/skills.md` | `opal-pilot-gc` 항목 등록(`opgc`/`gc` 약어 포함) | TASK.md 요구사항 10 |
| M2 | `opal/core/references/opal-skills-registry.json` | JSON SSOT에 `opal-pilot-gc` 레코드 추가 | `opal/core/references/skills.md:3-4` |
| M3 | `opal/core/references/agents.md` | `opal-security-checker`, `opal-convention-checker` 등록 | TASK.md 요구사항 10 |
| M4 | `scripts/install-mac.sh` | OPAL 스킬/에이전트 복사 블록에 신규 경로 추가 | TASK.md 요구사항 11 |
| M5 | `.opal/memory/project_security_task.md` | 상태 `완료(TEST)` 전환 + 설계 보안(PLAN) 별도 유지 명시 | TASK.md 요구사항 12 |
| M6 | `.opal/MEMORY.md` | 메모리 인덱스에서 project_security_task 상태 갱신 | TASK.md 요구사항 12 |

#### 삭제

| # | 파일 경로 | 사유 |
|---|----------|------|
| - | - | 없음 |

### 3.2 구현 순서

| 순서 | 작업 | 파일 | 난이도 |
|------|------|------|-------|
| 1 | Base 체크리스트 + 보고서 템플릿 작성 | N2~N6 | 중 |
| 2 | 보안 에이전트 AGENT.md | N7 | 중 |
| 3 | 컨벤션 에이전트 AGENT.md | N8 | 중 |
| 4 | Pilot SKILL.md (5단계 + arguments + STATE 치환 + Agentic) | N1 | 상 |
| 5 | 레지스트리 등록 | M1~M3 | 하 |
| 6 | install-mac.sh 배포 블록 | M4 | 하 |
| 7 | 030 보안 보류 메모리 정리 | M5~M6 | 하 |
| 8 | docs/ 갱신 (PROJECT.md + ARCHITECTURE.md 표) | M-docs | 하 |

> **병렬 가능**: Step 1의 6개 references(N2~N6)는 독립적이므로 병렬 작성 가능. Step 2/3(보안·컨벤션 에이전트)도 Step 1 완료 후 병렬 가능. Step 4 Pilot은 에이전트 이름이 확정된 뒤 순차.

### 3.3 핵심 설계

#### N1. `opal/skills/opal-pilot-gc/SKILL.md`

- **Frontmatter**: `name: opal-pilot-gc`, `description`에 트리거 "opgc", "gc", "//opgc", "garbage collection" 포함(→ `opal/core/references/skills.md` §스킬 도구 사용법 기준). 별칭은 description에 명시하고 `opal-skills-registry.json`의 `aliases` 배열에 `["opgc", "gc"]` 추가.
- **Harness 로드**: 상단에 `~/.opal/references/opal-harness.md` Read 명시 + `--agentic` 여부에 따라 interactive/agentic 서브 하네스 분기 (→ `opal-pilot-project/SKILL.md:11-18` 패턴 그대로 재사용).
- **5단계 정의** (TASK.md §2):
  - STEP 1 SCAN: `--scope staged|all` 파싱, `git diff --name-only --staged` 또는 `ls-files`, 기술 스택 감지(`package.json` 등), 기준 문서 로드. 산출물: STATE.md 갱신만.
  - STEP 2 CHECK: `opal-security-checker` + `opal-convention-checker` **병렬 디스패치** (→ `~/.opal/references/opal-harness.md` §7 참조). `--only` 플래그 처리. 산출물: 각 에이전트 임시 결과(STATE 로그).
  - STEP 3 REPORT: 결과 수합 + §9 빈도(N=3) + 심각도(Critical/High) + 새 카테고리 감지. STATE.md 요약 테이블 갱신. 산출물: `GC-SECURITY-{ts}.md`, `GC-CONVENTION-{ts}.md`. 게이트: 사용자 확인(기본) 또는 `--apply` 자동 진행.
  - STEP 4 APPLY: §2.8 알고리즘으로 체크박스 순회, stash 기반 롤백, 문서 업데이트 제안 승인 UX 실행 + opi 호출 래핑. 산출물: 보고서 체크박스/주석 갱신.
  - STEP 5 CLOSE: DONE.md 생성, 메모리 업데이트 없음(트래커 금지 원칙), State Gate. 게이트: **[MUST] APPLY 사용자 확인 없이 CLOSE 진입 금지** (→ `~/.opal/references/opal-harness.md` §1 CLOSE 진입 게이트, TASK.md 제약 원문 준수).
- **STATE.md 도메인 치환값 섹션**:
  - 모드: `GC`
  - 단계 목록: `SCAN / CHECK / REPORT / APPLY / CLOSE`
  - 파이프라인 현황판 행 구조 (opp SKILL.md:119-142 20행을 12행으로 경량화):
    ```
    | # | 단계 | 항목 | 상태 | 시점 |
    | 1 | SCAN | 작업 | ⬜ | - |
    | 2 | CHECK | 병렬 디스패치 | ⬜ | - |
    | 3 | CHECK | 에이전트 완료 확인 | ⬜ | - |
    | 4 | REPORT | GC-SECURITY-{ts}.md 생성 | ⬜ | - |
    | 5 | REPORT | GC-CONVENTION-{ts}.md 생성 | ⬜ | - |
    | 6 | REPORT | 실행 요약 테이블 갱신 | ⬜ | - |
    | 7 | REPORT | 사용자 확인 | ⬜ | - |
    | 8 | APPLY | 체크박스 순회 + 자동 판정 | ⬜ | - |
    | 9 | APPLY | 문서 업데이트 제안 승인 | ⬜ | - |
    | 10 | APPLY | 사용자 확인 | ⬜ | - |
    | 11 | CLOSE | DONE.md 생성 | ⬜ | - |
    | 12 | CLOSE | State Gate | ⬜ | - |
    ```
  - 실행 요약 테이블 템플릿: TASK.md §8 343-355줄 그대로.
- **arguments 파싱**: TASK.md §4 6종(`--only`, `--scope`, `--apply`, `--agentic`, 조합).
- **에이전트 병렬 디스패치 프롬프트 템플릿**: `[WORKER]` 마커 + Guards 핵심 규칙 + `docs/CONVENTIONS.md`·`docs/SECURITY.md` 경로 + `base-*-checklist.md` 경로 + 보고서 템플릿 경로 주입 (→ `opal-pilot-project/SKILL.md:46-48` PM 컨텍스트 주입 규칙 준수).
- **Agentic Mode 섹션**: `opal-harness-agentic.md` 참조 + CLOSE 진입 게이트만 유지(다른 게이트는 자율 통과), AGENTIC-LOG.md 생성.
- **태스크 폴더 자동 생성 규칙**: `tasks/{NNN}-{YYMMDD}-opgc-{short-summary}/`. `short-summary`는 scope + only 기반 자동 생성(예: `staged-sec-only`, `all-apply`).
- **DONE.md 템플릿 참조**: N6 파일 참조.

#### N7. `opal/agents/opal-security-checker/AGENT.md`

- **Frontmatter**: `name`, `description`(보안 체크 전담), `model: advanced`(OWASP/CWE 추론 필요), `icon: 🛡️`, `tools: [Read, Grep, Glob, Bash, Edit, Write]`(APPLY에서 시크릿 치환 필요). (→ `opal-plan-agent/AGENT.md` 참조 `model: advanced` 패턴.)
- **실행 프로세스**:
  1. 부트스트랩 스킵(`[WORKER]` 마커 수신).
  2. `base-security-checklist.md` Read.
  3. `docs/SECURITY.md` 존재 분기:
     - 존재 → Read → Base 병합
     - 부재 → Base만 적용 + 보고서 §5 작성 유도 안내 플래그 설정
  4. 감지된 스택에 맞는 커뮤니티 스킬 래핑:
     - `~/.opal/community-skills/openai/security-best-practices/references/{stack}.md` Read (존재 시)
     - `~/.opal/community-skills/getsentry/code-review/SKILL.md` Read (보조 참조)
  5. 대상 파일 순회 + 체크리스트 매칭 + fingerprint 산출(§2.3 알고리즘).
  6. 보고서 템플릿(N2) 기반 `GC-SECURITY-{ts}.md` 작성 (체크리스트 내장, 5단계 상태 주석 포맷).
- **Base 내장**: OWASP Top 10 + CWE Top 25 + SANS Top 25 매핑 체크리스트(references로 분리).
- **자체 로드 문서**: `docs/SECURITY.md`(존재 시), `docs/ARCHITECTURE.md`(시스템 구성).
- **출력**: `artifact_path`, `summary`, `status`, `blockers`, `changed_files`.

#### N8. `opal/agents/opal-convention-checker/AGENT.md`

- **Frontmatter**: `model: standard`(규칙 매칭 중심), `icon: 📏`, `tools: [Read, Grep, Glob, Bash, Edit, Write]`.
- **실행 프로세스**:
  1. 부트스트랩 스킵.
  2. `docs/CONVENTIONS.md` 존재 확인:
     - 존재 → Read + 규칙 파싱 + 체크
     - 부재 → **체크 생략** + 보고서 §5에 "CONVENTIONS.md 부재 — 초안 생성 유도" 플래그. 단, `base-convention-checklist.md`의 카테고리 목록을 **초안 제안 근거**로만 수집(위반 판정 아님).
  3. `getsentry/code-review/SKILL.md` Read (참조용).
  4. `base-convention-checklist.md` Read (카테고리 참조).
  5. 파일 순회 + 프로젝트 규칙 매칭 + fingerprint 산출.
  6. `GC-CONVENTION-{ts}.md` 작성.
- **프레임워크 내장 공통 컨벤션 기본값 포함 금지**: base-convention-checklist는 "카테고리 리스트"이지 "규칙 리스트"가 아님 — 모든 규칙은 `docs/CONVENTIONS.md`에서만 로드.

#### N2/N3. 보고서 템플릿

- §2.9 샘플 보고서 구조 그대로. 표/체크리스트/주석 포맷 placeholder 형태.
- 체크박스 5단계 기호 + 주석 규칙(TASK.md §8 "체크박스 상태 표기") 표를 템플릿 상단에 고정 주석으로 기입.

#### N4. base-security-checklist.md

- §2.9 전체 체크리스트 + 각 항목별 "감지 정규식/패턴/AST 질의" 힌트 + "자동 수정 가능 여부" + "참조 URL".
- 스택별 references 디렉토리를 매핑(`javascript-react → community-skills/openai/.../javascript-typescript-react-web-frontend-security.md`).

#### N5. base-convention-checklist.md

- §2.9 컨벤션 카테고리 + "검사 방식(파일 패턴/정규식/언어별 린트 힌트)" + "자동 수정 가능 여부".
- **규칙을 내장하지 않는다** — 카테고리만 제공.

#### N6. done-template.md

- TASK.md §8 DONE.md 템플릿(359-384줄) 그대로 + GC 특수 필드:
  - scope / 대상 파일 수 / 실행 시간 / APPLY 모드
  - 처리 요약 테이블(에이전트별)
  - 산출물 링크
  - 후속 권장

#### M1. `opal/core/references/skills.md`

- "공통 (모든 프로젝트)" 테이블 아래에 새 행 또는 새 섹션("코드 품질 스킬") 추가:
  - `opal-pilot-gc` (`opgc` / `gc`) — 커밋 전 보안/컨벤션 체크 — 수동(`//opgc`).

#### M2. `opal-skills-registry.json`

- 신규 엔트리: `{ "name": "opal-pilot-gc", "type": "orchestrator", "aliases": ["opgc", "gc"], "description": "...", "triggers": ["//opgc", "//gc", ...], "path": "~/.opal/skills/opal-pilot-gc/" }` (기존 JSON 구조 확인 필요 — EXECUTE Step에서 재검증).

#### M3. `agents.md`

- "전문 에이전트 (Specialist)" 섹션에 2개 추가 — opal-plan-agent 패턴(`opal/core/references/agents.md:49-60`) 재사용.

#### M4. `install-mac.sh`

- `scripts/install-mac.sh:424-440` OPAL 스킬 복사 블록에 `opal-pilot-gc` 경로 추가(기존 for 루프 패턴이면 자동 포함 가능성 있음 — EXECUTE에서 검증 후 명시적 테스트).
- OPAL 에이전트 복사 블록에 2개 에이전트 경로 추가.

#### M5/M6. 메모리

- `.opal/memory/project_security_task.md` — 헤더에 `status: 완료(TEST — 122에서 흡수)` 추가, 본문에 "설계 보안(PLAN 단계) 후속은 별도 태스크로 분리 유지" 유지.
- `.opal/MEMORY.md` 인덱스 — 해당 항목 앞에 `[완료(TEST)]` 태그.

---

## 4. 실행 체크리스트

> 총 12개 Step (PLAN 워커가 EXECUTE 단계로 전달하는 체크리스트)

> **agent 필드**: PM이 전달한 전문 에이전트 매핑 테이블이 없으므로, 범용 워커 `opal-task-action-agent` 또는 `opal-task-agent`로 통일하되, 작업 성격에 따라 다음과 같이 배정:
> - 문서 작성(AGENT.md, SKILL.md, references) → `opal-task-action-agent` (고품질 문서 생산 및 자율 실행)
> - 레지스트리 갱신 / install-mac.sh 수정 / 메모리 정리 → PM 직접 (단순 편집, 디스패치 오버헤드 불필요)

### Step 1: 보고서 템플릿 2종 + 체크리스트 3종 작성
- [x] 완료
- **파일**: `opal/skills/opal-pilot-gc/references/report-security-template.md`, `report-convention-template.md`, `base-security-checklist.md`, `base-convention-checklist.md`, `done-template.md`
- **작업 내용**: PLAN §3.3 N2~N6 설계대로 작성. 샘플 보고서(§2.9)를 placeholder화 + OWASP 10/CWE Top 25 전량 포함 + 컨벤션 카테고리 8종 포함 + DONE.md 템플릿.
- **완료 기준**: 5개 파일 생성, 각 파일 frontmatter(해당 시)/섹션 구조/표 완성. OWASP 카테고리 10개, CWE 25개, 컨벤션 카테고리 8개가 모두 포함되어 있다.
- **테스트**: Grep으로 `OWASP-A0[1-9]|OWASP-A10` 10건, `CWE-` 25건, 컨벤션 카테고리 목록 8종 존재 확인.
- **의존**: 없음
- **agent**: opal-task-action-agent (병렬 5개 파일 생성)

### Step 2: opal-security-checker AGENT.md 작성
- [x] 완료
- **파일**: `opal/agents/opal-security-checker/AGENT.md`
- **작업 내용**: PLAN §3.3 N7 설계 + §2.7 커뮤니티 스킬 래핑 + §2.8 자동 판정 알고리즘 내장. 체크리스트 5단계 상태 주석 포맷 명시.
- **완료 기준**: AGENT.md 존재, frontmatter(name/description/model: advanced/icon/tools), Base 원칙 내장 섹션, `docs/SECURITY.md` 분기 로직, 커뮤니티 스킬 래핑 호출 방식, 보고서 §8 포맷 준수 체크리스트 모두 충족.
- **테스트**: AGENT.md에 "OWASP", "CWE", "SANS", "security-best-practices", "code-review", "[x]/[~]/[?]/[!]" 키워드 모두 존재.
- **의존**: Step 1
- **agent**: opal-task-action-agent

### Step 3: opal-convention-checker AGENT.md 작성
- [x] 완료
- **파일**: `opal/agents/opal-convention-checker/AGENT.md`
- **작업 내용**: PLAN §3.3 N8 설계. `docs/CONVENTIONS.md` 유일 기준 + 부재 시 초안 생성 유도 + 내장 공통 규칙 금지 명시.
- **완료 기준**: AGENT.md 존재, `docs/CONVENTIONS.md` 부재 분기 로직, 초안 생성 안내 플래그, opi 재사용 호출 방식(§2.10), 보고서 §8 포맷 준수.
- **테스트**: AGENT.md에 "CONVENTIONS.md", "opi", "초안" 키워드 존재, "프레임워크 내장 공통 컨벤션 금지" 또는 동등 표현 존재.
- **의존**: Step 1
- **agent**: opal-task-action-agent

### Step 4: opal-pilot-gc SKILL.md 작성
- [x] 완료
- **파일**: `opal/skills/opal-pilot-gc/SKILL.md`
- **작업 내용**: PLAN §3.3 N1 설계 전체 반영. 5단계 정의 + CLOSE 진입 게이트 + STATE 치환값(현황판 12행) + arguments 파싱(`--only`, `--scope`, `--apply`, `--agentic`) + 에이전트 병렬 디스패치 프롬프트 + Agentic Mode + 태스크 폴더 규칙 + DONE.md 템플릿 참조 + 빈도 임계값 N=3 상수 + 심각도 트리거 Critical/High + fingerprint 알고리즘 사양 + 자동 판정 알고리즘 내장 + stash 롤백 + opi 재사용 호출 방식.
- **완료 기준**: SKILL.md 존재, TASK.md 요구사항 1의 AC 9개 모두 충족. SKILL.md 500줄 이하(필요 시 references로 분리).
- **테스트**: 5단계 헤더(SCAN/CHECK/REPORT/APPLY/CLOSE) 존재, "CLOSE 진입 게이트" 키워드 존재, `--apply` 설명 존재, "N=3" 또는 동등 표현 존재, "stash" 키워드 존재.
- **의존**: Step 1, 2, 3
- **agent**: opal-task-action-agent

### Step 5: 스킬 레지스트리 등록 (skills.md + JSON SSOT)
- [ ] 완료
- **파일**: `opal/core/references/skills.md`, `opal/core/references/opal-skills-registry.json`
- **작업 내용**: 스킬 항목 1개 등록(opgc/gc 약어 포함). JSON에 triggers, aliases 배열 추가.
- **완료 기준**: `skill-registry match "//opgc"`가 `opal-pilot-gc`를 반환(dry-run), `skill-registry match "//gc"` 동일 결과.
- **테스트**: `node ~/.opal/tools/skill-registry/skill-registry.js validate` 통과(설치되어 있다면). 없으면 JSON 수동 파싱 확인.
- **의존**: Step 4
- **agent**: PM 직접

### Step 6: 에이전트 레지스트리 등록 (agents.md)
- [ ] 완료
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: "전문 에이전트 (Specialist)" 섹션에 `opal-security-checker`, `opal-convention-checker` 2개 등록.
- **완료 기준**: 2개 섹션이 추가되고 역할/호출 시점/입력/출력/에이전트 경로 필드가 기입됨.
- **테스트**: Grep으로 `### opal-security-checker`, `### opal-convention-checker` 존재 확인.
- **의존**: Step 2, 3
- **agent**: PM 직접

### Step 7: install-mac.sh 배포 블록 갱신
- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: `opal/skills/` 복사 블록에 `opal-pilot-gc` 포함 확인 / 필요 시 추가. `opal/agents/` 복사 블록에 2개 에이전트 포함 확인.
- **완료 기준**: `bash -n scripts/install-mac.sh` 문법 통과. dry-run 또는 `--help` 출력 시 3개 경로가 포함되는지 확인(install-mac 자체에 dry-run 모드 있으면 사용, 없으면 코드 리뷰만).
- **테스트**: Grep으로 `opal-pilot-gc`, `opal-security-checker`, `opal-convention-checker` 각 1회 이상 출현.
- **의존**: Step 4, 6
- **agent**: PM 직접

### Step 8: 030 보안 보류 메모리 상태 전환
- [ ] 완료
- **파일**: `.opal/memory/project_security_task.md`, `.opal/MEMORY.md`
- **작업 내용**: `project_security_task.md` 상단에 `status: 완료(TEST — 122 흡수)` + 본문에 설계 보안(PLAN) 후속은 별도 태스크 유지 명시. MEMORY.md 인덱스 갱신.
- **완료 기준**: 두 파일 모두 상태 반영, 설계 보안 별도 후속 문구 포함.
- **테스트**: Grep으로 `완료(TEST` 또는 `완료 (TEST` 패턴 존재.
- **의존**: Step 1~7
- **agent**: PM 직접

### Step 9: docs/ 갱신 Step — 프로젝트 문서 테이블에 관련 문서 반영
- [ ] 완료
- **파일**: `docs/PROJECT.md` (프로젝트 문서 테이블) + `docs/ARCHITECTURE.md` (오케스트레이터 + 에이전트 테이블)
- **작업 내용**: `opal-pilot-gc` (opgc), 2개 에이전트를 아키텍처 테이블에 추가. `docs/SECURITY.md` 권장 항목을 PROJECT.md 문서 테이블에 추가(프로젝트 옵션 문서로).
- **완료 기준**: 4개 테이블이 갱신되어 신규 컴포넌트 등록.
- **테스트**: Grep으로 `opal-pilot-gc`/`opgc` 출현 확인(PROJECT.md + ARCHITECTURE.md).
- **의존**: Step 5, 6
- **agent**: PM 직접

### Step 10: 샘플 보고서 2부를 references/에 참조용으로 고정 저장
- [ ] 완료
- **파일**: `opal/skills/opal-pilot-gc/references/sample-gc-security-report.md`, `sample-gc-convention-report.md`
- **작업 내용**: PLAN §2.9의 샘플 보고서 2부를 실제 파일로 저장(캡틴·워커가 구현 시 참조용).
- **완료 기준**: 2개 파일 존재, 보고서 포맷(§8) 100% 준수.
- **테스트**: 각 파일에 §1~§5 섹션 존재, 체크박스 5단계 기호 모두 등장(`[ ]`, `[x]`, `[~]`, `[?]`, `[!]`).
- **의존**: Step 1
- **agent**: opal-task-action-agent (병렬 가능)

### Step 11: QA 자가 점검 — 모든 산출물 일관성 검증
- [x] 완료
- **파일**: 전체 산출물
- **작업 내용**: op-task-qa를 통해 체크리스트 갱신 상태·Frontmatter·네이밍 규칙·하네스 준수 확인(PM Gate 예비 단계).
- **완료 기준**: QA-EXECUTE.md 생성, 모든 체크리스트 갱신 상태 통과.
- **테스트**: QA 에이전트 실행 → verdict=pass.
- **의존**: Step 1~10
- **agent**: opal-task-qa-agent (op-task-qa 스킬 실행)

### Step 12: EXECUTE 완료 보고 + CLOSE 단계 진입 승인 대기
- [ ] 완료
- **파일**: - (보고 행위만)
- **작업 내용**: 변경 파일 목록 + QA 결과 + 다음 단계(CLOSE) 진입 승인 요청.
- **완료 기준**: 사용자가 `승인` / `확인완료` 등 명시적 표현 반환.
- **테스트**: STATE.md의 EXECUTE 사용자 확인 행 `✅` 전환.
- **의존**: Step 11
- **agent**: PM 직접

---

## 5. 테스트 시나리오 (TS-NNN)

> 아래 TS는 `opal-pilot-gc` 구현 완료 후 동작을 검증하는 시나리오. **EXECUTE 완료 후 수동 실행 또는 opi와 동일하게 smoke 테스트 단계에서 사용**한다.

### TS-01: `//opgc` 기본 실행 (staged, APPLY 승인 대기)
- **입력**: 스테이징된 파일 3개(의도적으로 하드코딩 시크릿 1개 + 미사용 import 2개 포함). `//opgc` 실행.
- **기대 출력**:
  - 태스크 폴더 `tasks/{NNN}-{YYMMDD}-opgc-staged/` 생성
  - STATE.md 현황판 12행 초기화
  - SCAN → CHECK(병렬) → REPORT 진행
  - `GC-SECURITY-{ts}.md` + `GC-CONVENTION-{ts}.md` 생성
  - REPORT 완료 후 "APPLY를 진행할까요? (y/n)" 대기
- **검증**: STATE.md 행 7(REPORT 사용자 확인) `⬜` 상태, 행 1~6 `✅`.

### TS-02: `//opgc --only security` 단일 에이전트 실행
- **입력**: 스테이징된 파일, `//opgc --only security`.
- **기대 출력**: `opal-convention-checker` 디스패치 생략, `GC-CONVENTION-*.md` 미생성, STATE.md 실행 요약 테이블에 convention 행 미표시.
- **검증**: `tasks/.../GC-CONVENTION-*.md` 존재하지 않음 + STATE.md 내 `convention` 문자열 미등장.

### TS-03: `//opgc --apply` 자동 APPLY 모드
- **입력**: 스테이징된 하드코딩 시크릿 1개(auto_fixable=Y), `//opgc --apply`.
- **기대 출력**:
  - REPORT 후 승인 없이 APPLY 진행
  - 보고서 GC-001 체크박스 `[x] done` + 적용 시각 주석
  - 실제 파일의 `"sk-..."`가 `process.env.API_KEY`로 치환
  - stash 생성되었으나 abort 없었으므로 보존
- **검증**: `git stash list`에 `gc-session-{ts}` 존재, 대상 파일에 `process.env` 포함.

### TS-04: `//opgc --agentic` agentic 모드
- **입력**: `//opgc --agentic` + 10개 이슈 혼합.
- **기대 출력**:
  - AGENTIC-LOG.md 생성
  - SCAN/CHECK/REPORT/APPLY Gate를 PM이 자율 통과
  - CLOSE 진입만 사용자 승인 요청(CLOSE 진입 게이트 유지)
- **검증**: AGENTIC-LOG.md에 각 Gate 통과 이벤트 기록, CLOSE 진입 전 사용자 확인 row `⬜`.

### TS-05: SECURITY.md 부재 시 초안 유도 흐름
- **입력**: `docs/SECURITY.md` 미존재 상태에서 `//opgc --only security` 실행.
- **기대 출력**:
  - 보고서 §5에 "SECURITY.md 부재 — 초안 생성을 제안합니다" 안내
  - 사용자 승인 시 opi 재사용 호출 → `docs/SECURITY.md` 초안 생성(캡틴 검토 단계 진입)
  - 자동 저장 금지(opi 프로토콜 준수)
- **검증**: 보고서 §5 플래그 존재 + opi 호출 시 "캡틴 승인 대기" 메시지.

### TS-06: CONVENTIONS.md 부재 시 초안 유도 흐름
- **입력**: `docs/CONVENTIONS.md` 미존재 상태에서 `//opgc --only convention` 실행.
- **기대 출력**:
  - `opal-convention-checker`가 **위반 체크 생략** + 보고서 §5에 초안 생성 안내만 표시
  - 자동 수정 0건
- **검증**: `GC-CONVENTION-*.md` §3 수정 대상 전 카테고리 "0건" + §5 플래그 존재.

### TS-07: 빈도 트리거 발동 → 문서 업데이트 제안
- **입력**: 4개 파일에 동일 fingerprint(import 순서 위반) 배치, `//opgc`.
- **기대 출력**:
  - 보고서 §4 "문서 업데이트 제안"에 `GC-DP-C01 빈번 이슈 "import 순서" (4개 파일)` 등장
  - 임계값 N=3 초과 명시
- **검증**: 보고서 §4에 "빈번" + "4개 파일" + "N=3" 키워드 존재.

### TS-08: Critical/High 트리거 발동 → 문서 업데이트 제안
- **입력**: Critical 이슈 1건(하드코딩 시크릿), `//opgc`.
- **기대 출력**:
  - 보고서 §4에 "심각도 트리거 — Critical/High 1건 → SECURITY.md 추가 제안"
  - 빈도 미달이어도 심각도로 트리거 발동
- **검증**: 보고서 §4 심각도 트리거 항목 존재.

### TS-09: 체크박스 5단계 상태 전이 (각 상태별 자동 판정 케이스)
- **입력**: 5개 이슈 동시 주입:
  1. auto_fixable=Y + verify 성공 → `[x] done` 기대
  2. auto_fixable=Y + verify 실패 → `[!] failed` + 롤백 기대
  3. auto_fixable=N + fix_hint 구체 → `[?] review` + 해결 방안 주석 기대
  4. auto_fixable=N + fix_hint 모호 → `[?] review` + 판단 근거 주석 기대
  5. 캡틴 직전 보류 ID → `[~] pending` + 보류 사유 주석 기대
- **기대 출력**: 5개 이슈 각각 기호 + 주석 모두 정확.
- **검증**: 보고서에 `[x]`, `[!]`, `[?]`, `[?]`, `[~]` 각 1건 이상 + 주석 형식 TASK.md §8 "체크박스 상태 표기" 테이블 준수.

### TS-10: 커뮤니티 스킬 래핑 호출
- **입력**: Node.js/Express 프로젝트 + `//opgc --only security`.
- **기대 출력**:
  - 에이전트가 `~/.opal/community-skills/openai/security-best-practices/references/javascript-express-web-server-security.md` Read
  - 해당 가이드의 권장 항목(helmet, secure cookies 등)이 보고서에 출처 표기되어 등장
  - 원본 수정 없음(파일 타임스탬프 불변)
- **검증**: 보고서 출처 필드에 `community-skills/openai/...` 경로 등장 + 해당 파일 `stat` 비교 변경 없음.

**총 TS 시나리오 수: 10개**

---

## 6. QA 체크리스트

### 6.1 기능 테스트
- [ ] TS-01~TS-10 모두 통과
- [ ] 체크박스 5단계 상태 + 주석 포맷 TASK.md §8 100% 준수
- [ ] CLOSE 진입 게이트가 기본/agentic 양 모드 모두 유지됨
- [ ] stash 기반 롤백이 자동 수정 실패 시 원복을 수행
- [ ] opi 재사용 시 커뮤니티/원본 스킬 수정 없음

### 6.2 일관성 테스트
- [ ] skill-registry / agents-registry / install-mac.sh 3곳이 동일한 경로를 참조
- [ ] `docs/PROJECT.md` + `docs/ARCHITECTURE.md` 컴포넌트 테이블이 신규 항목 반영
- [ ] frontmatter name이 kebab-case + 디렉토리명 일치
- [ ] 약어 `opgc`, `gc` 2종이 skill-registry에서 매칭 성공

### 6.3 문서 품질
- [ ] SKILL.md 500줄 이하 (초과 시 references/ 분리)
- [ ] 한국어 본문 + 영어 코드/필드명 규칙 준수
- [ ] 변경이력 표 (v1.0 + 초기 작성) 포함
- [ ] citation-rules §2 포맷 준수(표 + 인라인 `[MUST]`)
- [ ] 샘플 보고서 2부가 실제 템플릿으로 사용 가능한 수준

---

## 7. 리스크 및 대응

| # | 리스크 | 영향 | 대응 방안 |
|---|--------|------|----------|
| R1 | fingerprint 알고리즘이 충돌을 과다 생성 | 빈도 트리거 오발동 | 8-byte prefix + 3축(카테고리 + 해결 방안 + 해시) 비교로 충돌 완화. 관측 지표 향후 추가 검토(이번 구현 범위 밖) |
| R2 | stash 기반 롤백이 `--include-untracked` 파일과 충돌 | 사용자 워킹 카피 손상 | APPLY 진입 전 `git status` 확인 + dirty 상태면 사용자에게 확인 요청 (하네스 §1 Git 사전 점검 준용) |
| R3 | opi 재사용 호출 시 opi 내부 인터뷰 Phase가 과도하게 블로킹 | UX 저하 | GC가 opi에 "초안 preprocessing 결과"를 입력으로 전달 + opi의 Q&A는 "추가 필요 시만" 진입하도록 플래그 신설 가능성(EXECUTE에서 평가) |
| R4 | 커뮤니티 `getsentry/code-review` 라이선스 불확실 | 법적 리스크 | 원본 수정 없음 + Read 기반 참조만 수행(참조 시 출처 표기). 라이선스 파일 확인 후 필요 시 공식 저장소 링크로 대체 고려 |
| R5 | 새 카테고리 감지가 한글/영문 헤더 변형에 취약 | 문서 업데이트 오제안 | 헤더 정규화 시 한글 공백 제거 + 영문 lowercase + 공통 stop-word 제거로 완화. 미매칭 시 "의심" 플래그로만 표시하고 최종 판정은 사용자 확인 |
| R6 | SKILL.md가 500줄을 초과 | CONVENTIONS 위반 | STATE 치환값 테이블·보고서 템플릿은 `references/`로 분리(Step 1 사전 분리) |
| R7 | N=3 임계값이 프로젝트 규모에 따라 부적절 | 빈도 트리거 미발동 | 이번 구현은 고정값. 후속 태스크에서 `--freq-threshold` 플래그 도입 옵션 남김(SKILL.md 주석 처리) |

---

## 8. 해결하지 못한 블로커

**없음**. 10가지 위임 사항 모두 결정 완료, 커뮤니티 스킬 실사 완료, 샘플 보고서 2부 완성.

---

## 9. 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-17 | 초기 작성 — 10가지 위임 사항 결정, 12 Step 체크리스트, 10 TS 시나리오, 샘플 보고서 2부, 리스크 7종 |
