# OPAL GC 공통 Capability 분리·고도화 제안서

> 상태: 제안
> 작성일: 2026-09-12
> 범위: `opal-pilot-gc` 검사 본체 분리, 검사 품질 고도화, 외부 기준 공급망
> 동반 제안: [PM 직접 수행 모델](./opal-pm-direct-execution.md)

---

## 1. 제안 요약

`opal-pilot-gc` 안에 결합된 보안 검사, 컨벤션 검사, 보고서 통합을 재사용 가능한 세 `op-*` skill로 분리한다.

```text
op-security-check ─┐
                   ├─> op-gc-report ─> 통합 판정·보고
op-convention-check┘
          ▲                    ▲
          │                    │
  opal-pilot-gc         opal-self-pm·다른 Pilot
```

- `op-security-check`: 보안 기준 선택, 정적·구조 검토, finding 생성
- `op-convention-check`: 프로젝트 규칙과 실행 설정 검토, finding 생성
- `op-gc-report`: 공통 schema 정규화, 중복 제거, 심각도·차단 판정, Markdown/JSON 출력
- `opal-pilot-gc`: SCAN → CHECK → REPORT → CLOSE 수명주기만 조율하는 thin wrapper

세 skill은 최신 공식 표준과 검토된 community reference를 활용할 수 있게 고도화한다. 단, 프로젝트 규칙과 승인된 공식 기준은 `enforce`, community 기준은 기본 `advisory`로 분리한다.

## 2. AS-IS와 한계

현행 `opal-pilot-gc`는 네 단계 Pilot로서 task 번호·폴더·상태·보고·CLOSE·brain ingest·개선 루프까지 소유한다(`opal/skills/opal-pilot-gc/SKILL.md`). 완결된 커밋 전 점검에는 적합하지만 다른 workflow 내부의 부분 검사로 호출하기에는 무겁다.

### 2.1 구조적 한계

1. `opal-self-pm`이나 다른 Pilot이 보안 검사만 필요해도 중첩 Pilot 전체를 시작해야 한다.
2. checker agent의 역할 문서와 Pilot 절차에 검사 기준이 나뉘어 재사용 계약이 불명확하다.
3. 보안·컨벤션 결과 형식이 독립적으로 진화하면 통합 보고가 문자열 결합에 머물 수 있다.
4. staged diff 중심 기본 범위는 untracked·비-staged·생성 산출물 등 실제 작업 범위를 놓칠 수 있다.
5. 외부 기준의 존재·버전·신뢰 수준을 보장하는 registry가 없어 환경마다 검사 품질이 달라질 수 있다.

### 2.2 유지할 강점

- 보안과 컨벤션을 독립 평가자가 병렬 점검하는 구조
- 검사는 원칙적으로 read-only이며 자동 수정하지 않는 경계
- 프로젝트 `SECURITY.md`·`CONVENTIONS.md`를 우선하는 방식
- finding 근거와 개선안을 남기는 보고서
- `opal-pilot-gc`의 독립 실행, 상태 추적, CLOSE 계약

## 3. 목표와 비목표

### 목표

- 검사 절차를 Pilot과 분리해 어느 workflow에서도 같은 계약으로 호출한다.
- 프로젝트 규칙, 공식 표준, community reference의 신뢰·집행 수준을 구분한다.
- 보안과 컨벤션 finding을 공통 schema로 통합한다.
- 실제 검사 파일 집합과 도구 실행 증거를 재현 가능하게 남긴다.
- reference가 없거나 오래돼도 안전하게 축소 실행하고 결측을 보고한다.

### 비목표

- 외부 skill이나 template을 자동 설치·실행하지 않는다.
- community 관행을 프로젝트 규칙보다 우선하지 않는다.
- 검사 skill이 발견한 문제를 자동 수정하지 않는다.
- `opal-pilot-gc`의 독립 실행 수명주기를 제거하지 않는다.
- 모든 언어와 framework의 규칙을 OPAL 본문에 복제하지 않는다.

## 4. 목표 아키텍처

### 4.1 계층

| 계층 | 컴포넌트 | 책임 |
|---|---|---|
| Orchestration | `opal-pilot-gc` | 범위 확정, 병렬 검사, report 호출, 상태·CLOSE |
| Adaptive consumer | `opal-self-pm` | 작업 영향에 따라 필요한 검사 선택, 결과 반영, 사용자 확인 |
| Other consumers | Dev·Write·SDD 등 Pilot | 단계 Gate나 완료 전 필요한 검사만 호출 |
| Check capability | `op-security-check`, `op-convention-check` | read-only finding 생성 |
| Normalize/report | `op-gc-report` | finding 통합·판정·출력 |
| Evaluator role | checker agent | 공통 skill을 독립 컨텍스트에서 실행하는 thin role |

checker agent는 기준과 출력 형식을 자체 복제하지 않는다. 호출받은 공통 skill을 읽고, 지정된 입력과 read-only 제한을 적용한 뒤 결과만 반환한다.

### 4.2 공통 입력

```yaml
project_root: /absolute/project
target_files:
  - relative/path
output_dir: /absolute/output
scope: changed|staged|commit|explicit
baseline: optional-reference
project_documents:
  - docs/CONVENTIONS.md
  - docs/SECURITY.md
reference_profile: default
```

- `project_root`, `target_files`, `output_dir`, `scope`를 공통 핵심 입력으로 사용한다.
- 기존 소비자를 위해 `task_folder`는 전환 기간에 `output_dir` alias로 허용한다.
- `target_files`는 호출자가 확정한 명시 목록이 기준이다. skill이 임의로 staged 범위로 축소하지 않는다.
- 입력 파일이 존재하지 않거나 project root 밖으로 벗어나면 검사 전 오류로 반환한다.

### 4.3 공통 출력

각 checker는 machine-readable result와 사람이 읽는 세부 보고를 함께 만든다.

```json
{
  "check": "security",
  "status": "pass|fail|partial|error",
  "checked_files": ["path/to/file"],
  "findings": [],
  "evidence": [],
  "references": [],
  "missing_capabilities": [],
  "report_path": "..."
}
```

`partial`은 검사 가능한 범위는 수행했지만 analyzer나 reference 결측이 있는 상태다. 결측을 `pass`로 해석하지 않는다.

## 5. Finding 공통 Schema

```json
{
  "id": "SEC-001",
  "fingerprint": "stable-hash",
  "category": "authorization",
  "severity": "critical|high|medium|low|info",
  "confidence": "high|medium|low",
  "disposition": "blocking|warning|advisory|suppressed",
  "rule_id": "CWE-862",
  "source_tier": "T1",
  "location": {"path": "src/api.ts", "line": 42},
  "evidence": "관측 사실",
  "impact": "실제 영향",
  "remediation": "수정 방향",
  "verification": "수정 후 확인 방법",
  "suppression": null
}
```

필수 원칙은 다음과 같다.

- severity와 confidence를 분리한다.
- 근거 없는 일반론은 finding으로 만들지 않는다.
- 재현 또는 확인 방법이 없는 항목은 confidence를 낮추거나 advisory로 둔다.
- suppress에는 사유, 승인 주체, 만료 조건을 기록한다.
- fingerprint로 baseline과 비교해 신규·잔존·해결 finding을 구분한다.

## 6. Reference 신뢰와 집행 정책

### 6.1 신뢰 계층

| Tier | 원천 | 기본 집행 | 예시 |
|---|---|---|---|
| T0 | 프로젝트 SSOT와 실행 설정 | `enforce` | `SECURITY.md`, `CONVENTIONS.md`, lint/compiler config |
| T1 | 검토·승인된 공식 표준 | `enforce` 또는 `advisory` | OWASP, MITRE CWE, NIST, 공식 언어·framework guide |
| T2 | 검토된 community reference | `advisory` | 공개 review checklist, skill template |
| T3 | 검색으로 발견했으나 미검토 | `disabled` | 신규 후보 |

T2 또는 T3 규칙은 사용자 승인 없이 `enforce`로 승격할 수 없다. T1도 프로젝트에 적용되는 control과 예외를 명시적으로 선택해야 차단 기준이 된다.

### 6.2 Reference Registry

외부 기준은 고정 URL 목록이 아니라 provenance를 가진 registry로 관리한다.

```json
{
  "id": "owasp-asvs",
  "source": "https://owasp.org/www-project-application-security-verification-standard/",
  "version": "5.0.0",
  "commit": null,
  "license": "CC BY-SA 4.0",
  "checksum": "optional-pinned-artifact-hash",
  "trust_tier": "T1",
  "default_disposition": "advisory",
  "stacks": ["web", "api"],
  "verified_at": "YYYY-MM-DD"
}
```

registry는 출처, version 또는 commit, license, checksum, trust tier, 적용 stack, 집행 수준, 검증일을 보존한다. 정확한 파일 경로와 검증 tool은 구현 PLAN에서 기존 skill registry와 역할 충돌을 확인해 확정한다.

### 6.3 발견·갱신 절차

1. 공식 원천을 우선 검색하고 version·게시 주체·license를 확인한다.
2. community 후보는 유지보수 상태, 내용 범위, 과도한 권한·명령, 공식 기준과의 충돌을 검토한다.
3. 외부 문서는 pin 또는 snapshot 가능한 형태로 등록한다.
4. 갱신 시 기존 version과의 rule diff, 새·삭제·변경 control, 예상 판정 변화를 보고한다.
5. 사용자가 갱신과 집행 수준을 승인한 뒤 registry를 바꾼다.
6. 다운로드한 skill·script는 검사 기준 자료로만 읽으며 자동 실행하지 않는다.

네트워크나 reference가 없으면 T0와 로컬에 pin된 T1/T2만 사용해 검사하고 `missing_capabilities`에 결측을 남긴다.

## 7. `op-security-check` 고도화

### 7.1 기준 선택 순서

1. 프로젝트 `docs/SECURITY.md`와 threat model
2. lockfile, dependency policy, secret rule, CI security config
3. 승인된 공식 표준과 stack별 공식 guide
4. 사용 가능한 정적 analyzer와 dependency scanner
5. 검토된 community reference

프로젝트 기준이 없으면 공식 baseline으로 advisory 검사를 수행하고 `SECURITY.md` 초안 생성을 제안한다. 문서 부재 자체를 모든 검사 생략의 이유로 삼지 않는다.

### 7.2 검사 영역

- 인증, 권한, 세션과 tenant 경계
- 입력 검증, injection, output encoding
- 비밀정보, 암호화, 개인정보와 로그 노출
- 파일·경로·command·network 경계
- SSRF, unsafe deserialization, template·code execution
- dependency와 software supply chain
- 오류 처리, auditability, rate limiting, abuse case
- 데이터 흐름과 trust boundary의 설계 위험
- 배포·runtime hardening과 보안 설정

대상 stack과 변경 파일에 해당하는 영역만 활성화하되, 비활성 영역과 이유를 결과에 남긴다.

### 7.3 도구와 판정

- analyzer 결과는 증거이지 최종 판정이 아니다.
- 도구명·version·실행 명령·exit code·대상 파일을 기록한다.
- secret 의심값 원문은 보고서에 복제하지 않고 위치와 식별 가능한 최소 정보만 남긴다.
- 차단은 적용 가능한 T0/T1 위반이면서 confidence가 충분할 때만 허용한다.
- 수정 제안에는 수정 뒤 확인할 test 또는 scan을 포함한다.

## 8. `op-convention-check` 고도화

### 8.1 기준 선택 순서

1. 프로젝트 `docs/CONVENTIONS.md`
2. formatter, linter, compiler, test, package 설정
3. 프로젝트 구조와 인접 코드의 현재 패턴
4. 공식 언어·framework style guide
5. 검토된 community code-review reference

문서와 실행 설정이 충돌하면 어느 쪽을 임의로 우선하지 않는다. 실제 tool 결과와 충돌 위치를 finding으로 반환하고 프로젝트 SSOT 정리가 필요하다고 보고한다.

### 8.2 검사 영역

- 이름, 파일 배치, import와 module boundary
- architecture layer와 dependency 방향
- public API, error, logging, configuration 계약
- type safety, nullability, resource lifecycle
- test 구조, fixture, determinism, coverage 의도
- 문서·주석·header와 현재 동작의 일치
- 복잡도, 중복, dead code, 불필요한 abstraction
- 접근성·국제화·framework 관례 등 stack별 규칙

포맷터가 자동 판정 가능한 항목과 사람이 판단할 설계 항목을 분리한다. formatter·linter 결과를 자연어로 재판정하지 않는다.

### 8.3 프로젝트 기준 부재

`CONVENTIONS.md`가 없으면 다음을 수행한다.

1. 실행 설정과 인접 코드에서 관측 가능한 규칙을 수집한다.
2. 공식 guide와 비교해 advisory report를 만든다.
3. 관측 사실과 권고를 분리한 `CONVENTIONS.md` 초안을 제안한다.
4. 사용자 채택 전에는 초안 규칙으로 변경을 차단하지 않는다.

## 9. `op-gc-report` 고도화

`op-gc-report`는 검사자가 아니라 결과 정규화와 release decision을 담당한다.

### 9.1 처리

1. 입력 schema와 실제 checked file 집합을 검증한다.
2. fingerprint와 위치·rule 근거로 중복 finding을 병합한다.
3. 신규·잔존·해결·suppressed 상태를 baseline과 비교한다.
4. source tier, severity, confidence, disposition으로 차단 여부를 계산한다.
5. 검사 결측과 partial 상태를 pass와 분리한다.
6. Markdown과 JSON 보고서를 같은 데이터에서 생성한다.

### 9.2 최종 판정

| 판정 | 조건 |
|---|---|
| `PASS` | blocking finding 0, 필수 검사 결측 0 |
| `PASS_WITH_ADVISORIES` | blocking 0, warning/advisory만 존재 |
| `FAIL` | blocking finding 1개 이상 |
| `INCOMPLETE` | 필수 checker 오류, 입력 불일치, 필수 analyzer 결측 |

높은 severity라는 이유만으로 community advisory를 자동 blocking으로 바꾸지 않는다. 반대로 필수 검사가 실행되지 않은 상태를 PASS로 만들지 않는다.

### 9.3 출력

- `GC-REPORT.md`: 사용자의 판단과 수정 우선순위
- `gc-report.json`: finding, provenance, evidence, baseline delta
- 선택적 SARIF: CI·code scanning 연동이 실제 필요할 때만 생성

보고서는 검사 파일 수를 추정하지 않고 `checked_files`의 실측값으로 표시한다.

## 10. 소비자별 계약

### 10.1 `opal-pilot-gc`

- SCAN에서 범위와 명시 파일 목록을 확정한다.
- CHECK에서 두 checker agent를 병렬 호출한다.
- checker agent는 각각 공통 skill 하나만 실행한다.
- REPORT에서 `op-gc-report`를 호출한다.
- 기존 상태·사용자 Gate·CLOSE·brain·개선 루프는 유지한다.

### 10.2 `opal-self-pm`

- 수정 직전 영향 분석으로 필요한 검사 종류를 선택한다.
- 작업 후 변경 파일 명시 목록으로 검사한다.
- finding 수정이 새 결정을 요구하면 질문 루프로 돌아간다.
- 결과와 knowledge impact를 사용자 최종 확인 입력에 포함한다.
- 전체 GC Pilot task를 중첩 생성하지 않는다.

### 10.3 다른 Pilot

- 보안·컨벤션 Gate가 필요한 단계에서 공통 skill을 직접 호출한다.
- Pilot이 가진 상태·Gate를 공통 skill이 다시 만들지 않는다.
- 통합 보고가 필요하지 않으면 개별 checker 결과만 소비할 수 있다.

## 11. 마이그레이션 순서

1. 현재 두 checker 보고를 공통 finding schema로 변환하는 adapter를 만든다.
2. `op-security-check`, `op-convention-check`, `op-gc-report`를 생성한다.
3. checker agent를 공통 skill thin role로 전환한다.
4. `opal-pilot-gc`를 thin wrapper로 바꾸고 기존 동작 회귀를 검증한다.
5. explicit target·untracked·staged·commit 범위 시나리오를 검증한다.
6. `opal-self-pm`과 한 개의 다른 Pilot에 공통 capability를 연결한다.
7. reference registry와 pin/update 승인 흐름을 추가한다.
8. README·PROJECT·ARCHITECTURE·help·install 자산을 동기화한다.

기존 report 소비자가 있으면 adapter 기간 동안 구형 Markdown 파일명을 유지한다. JSON schema가 안정된 뒤 중복 형식을 제거한다.

## 12. 수용 기준

- [ ] 세 `op-*` skill이 `opal-pilot-gc` 없이 독립 호출된다.
- [ ] `opal-pilot-gc`는 기존 SCAN→CHECK→REPORT→CLOSE 동작과 Gate를 유지한다.
- [ ] checker agent는 검사 규칙을 복제하지 않고 공통 skill을 실행하는 read-only role이 된다.
- [ ] 공통 입력이 explicit file list를 지원하고 staged 범위로 임의 축소하지 않는다.
- [ ] security와 convention 결과가 같은 finding schema를 사용한다.
- [ ] severity, confidence, disposition, source tier가 분리된다.
- [ ] project rules, official standards, community references의 신뢰와 집행 수준이 구분된다.
- [ ] community reference는 검토·사용자 승인 전 `enforce`가 될 수 없다.
- [ ] reference provenance와 version 또는 commit, license, 검증일을 추적한다.
- [ ] 외부 skill·script를 자동 실행하지 않는다.
- [ ] analyzer와 reference 결측은 `partial` 또는 `INCOMPLETE`로 보고된다.
- [ ] report가 신규·잔존·해결·suppressed finding을 구분한다.
- [ ] `opal-self-pm`이 중첩 Pilot 없이 필요한 검사만 호출한다.
- [ ] 기존 `opal-pilot-gc` 사용 시나리오와 신규 공통 호출 시나리오가 모두 검증된다.

## 13. 위험과 대응

| 위험 | 대응 |
|---|---|
| 기준이 많아져 오탐 증가 | 적용 stack 선별, confidence 분리, baseline·suppression 사용 |
| community 규칙이 프로젝트를 지배 | 기본 advisory, 사용자 승인 없는 enforce 금지 |
| 외부 자료의 공급망 위험 | provenance·pin·license·checksum, 자동 실행 금지 |
| 세 skill과 agent에 규칙 중복 | skill을 절차 SSOT로 두고 agent는 thin role로 제한 |
| 기존 GC 보고 소비자 파손 | adapter와 호환 파일명 후 점진 제거 |
| partial 검사를 성공으로 오인 | PASS와 INCOMPLETE를 구조적으로 분리 |

## 14. 우선 공식 Reference 후보

구현 시 최신 version과 license를 다시 확인하고 registry 승인 절차를 거친다.

- OWASP Application Security Verification Standard: <https://owasp.org/www-project-application-security-verification-standard/>
- OWASP Code Review Guide: <https://owasp.org/www-project-code-review-guide/>
- MITRE CWE Top 25: <https://cwe.mitre.org/top25/>
- NIST Secure Software Development Framework: <https://csrc.nist.gov/Projects/ssdf>
- OpenSSF Scorecard: <https://securityscorecards.dev/>

community capability 탐색 채널은 후보 발견에만 사용한다. 예를 들어 <https://skills.sh/>에서 찾은 자료는 T3로 시작하며, 내용·출처·license 검토 뒤에만 T2로 등록한다.
