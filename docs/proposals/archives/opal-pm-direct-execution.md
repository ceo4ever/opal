# OPAL PM 직접 수행 모델 설계 제안서

> 상태: 적용완료
> 작성일: 2026-09-10
> 범위: Pilot의 PM 실행 주체와 대화형 PM 직접 수행 계약
> 동반 제안: [GC 공통 Capability 분리·고도화](./archives/opal-gc-capability-refactor.md)

---

## 1. 제안 요약

PM 직접 수행을 하나의 느슨한 경량 예외로 두지 않고, 사용 목적이 다른 두 진입점으로 제공한다.

| 사용자 진입 | 실행 방식 | 선택 기준 |
|---|---|---|
| `//opd <작업>` | 기존 Pilot + 워커 실행 | 표준 역할 분리로 수행할 때 |
| `//opd --pm <작업>` | 기존 Pilot + PM 실행 | 단계·상태·Gate는 유지하되 PM이 직접 구현할 때 |
| `//oppm <작업>` | 대화형 PM 직접 수행 | 질문과 검토를 반복하며 범위와 해법을 함께 확정할 때 |

`--pm`은 새로운 workflow가 아니라 **선택한 Pilot의 실행 주체(actor)를 PM으로 바꾸는 공통 옵션**이다. `//oppm`은 `opal-self-pm`을 발동하는 별도 명령이며 Pilot이 아니다.

두 경로 모두 PM이 실제 분석·작성·구현을 수행한다. 서브에이전트는 독립 검토·평가·테스트에만 사용할 수 있다. 구현을 워커에게 위임했다면 그 실행 단위는 PM 직접 수행으로 분류하지 않는다.

## 2. 배경과 문제

현행 `L2 경량 트랙`은 “직접 수행”을 파일 1~2개, 단순 수정, 동작 검증 불요 조건에 묶는다(`opal/core/references/opal-pm.md` §12). 이 구조에는 다음 문제가 있다.

1. 실행 주체와 작업 규모가 결합돼 있다. PM이 실행할지와 작업이 작은지는 별개 결정이다.
2. Pilot의 상태·Gate를 유지하면서 PM이 직접 구현하는 공식 경로가 없다.
3. 대화 도중 요구를 발견하고 다시 조사하는 적응형 작업을 고정 단계나 무상태 L2 중 하나로만 선택해야 한다.
4. 직접 수행 종료 시 기획·설계·문서·brain·memory 영향 확인이 하나의 완료 계약으로 묶여 있지 않다.

이 제안은 L2의 파일 수 제한을 제거하되, 검증과 승인 경계를 약화하지 않는다.

## 3. 용어와 불변 조건

### 3.1 PM 직접 수행

PM 직접 수행은 PM이 다음 작업을 실제로 행하는 실행 방식이다.

- 현재 상태와 관련 근거를 조회한다.
- 요구와 설계를 사용자와 확정한다.
- 대상 파일·데이터·문서를 직접 작성하거나 수정한다.
- 실제 검증을 실행하고 결과를 판정한다.
- 변경된 지식과 산출물을 동기화한다.

PM이 최종 책임만 보유하고 구현을 워커에게 맡기는 것은 PM 조율이지 PM 직접 수행이 아니다.

### 3.2 독립 검증 예외

생성자와 평가자를 분리해야 하는 검증에는 서브에이전트를 사용할 수 있다.

- 보안·컨벤션 검사
- 테스트 실행과 결과 판정
- 설계·명세 독립 평가
- 읽기 전용 교차 검토

이때도 PM은 검증 입력, 범위, 채택 기준과 후속 수정을 소유한다. 서브에이전트가 파일을 구현·수정하면 직접 수행 경계를 벗어난다.

### 3.3 권한 경계

직접 수행 선택은 작업 방식의 승인이지 모든 부수 동작의 포괄 승인이나 자동 커밋 지시가 아니다. 다음은 기존 별도 승인 계약을 유지한다.

- 외부 skill·package 설치와 계정·MCP 연결
- 프로젝트 밖 또는 외부 시스템 쓰기
- 파괴적 변경과 비가역 데이터 마이그레이션
- commit, push, 배포
- Pilot과 harness가 정한 사용자 Gate

## 4. 명령과 라우팅

### 4.1 Pilot의 `--pm` 옵션

PM 직접 실행을 지원하는 Pilot은 공통 옵션 `--pm`을 받는다.

```text
//opd --pm 사용자 인증 흐름 개선
//opwt --pm 결제 정책서 개정
//opsdd --pm 알림 기능 명세와 구현
```

파서는 Pilot alias 다음의 `--pm`을 actor 옵션으로 해석한다. Pilot·profile·mode 옵션과 섞여도 각 축을 독립적으로 보존한다.

| 축 | 예시 | 의미 |
|---|---|---|
| workflow | `opd`, `opwt`, `opsdd` | 단계와 산출물 |
| actor | 기본 `worker`, `--pm` | 구현 주체 |
| interaction mode | 기본, `--interactive`, `--agentic` | 사용자 Gate 수준 |
| profile | `opd`, `opds` | 해당 Pilot 내부 프로파일 |

예를 들어 `//opd --pm --interactive`는 Dev Pilot의 단계와 interactive Gate를 유지하면서 PM이 실행한다.

### 4.2 `//oppm`

`//oppm`은 canonical skill `opal-self-pm`의 alias다.

```text
//oppm 워커 디스패치 정책을 함께 정리하고 반영해줘
```

자연어 “대화하면서 직접 해줘”, “하나씩 질문하며 PM이 처리해줘”도 `opal-self-pm`을 제안할 수 있다. 단순한 “직접 수행”만으로 Pilot과 `//oppm` 중 하나를 임의 선택하지 않고, 현재 명령·대화 맥락이 없으면 한 번 확인한다.

## 5. Pilot `--pm` 실행 계약

`--pm`은 선택한 Pilot을 복제하거나 우회하지 않는다. 기존 Pilot의 다음 계약을 그대로 유지한다.

- 단계 순서와 단계별 skill
- task 폴더와 산출물
- `state.json`, event receipt, observability
- PLAN·TEST-SCENARIO·RED-first·PM Gate
- mode별 사용자 확인과 CLOSE 승인
- 실제 테스트와 완료 증거
- CLOSE의 brain·memory·개선 루프

달라지는 것은 실행 주체뿐이다.

| 항목 | 기본 Pilot | `--pm` Pilot |
|---|---|---|
| 분석·계획·구현 산출 | 단계별 워커 | PM |
| `worker.dispatch` | 각 워커 호출 전에 필수 | 실제 검증 워커를 호출할 때만 적용 |
| Work item 담당 | 전문 워커 역할 | `PM` |
| 단계 상태와 Gate | 유지 | 동일하게 유지 |
| 독립 검증 | Pilot 계약에 따름 | 동일하게 유지 |

Pilot이 단계 실행을 워커 전용으로 규정한 부분은 actor-aware 계약으로 바꾼다. `actor=pm`이면 PM이 해당 단계 skill을 직접 읽고 입력·출력·검증 계약을 적용한다. 독립 검증자를 호출하는 행만 `worker.dispatch`를 load·verify한다.

실행 도중 PM이 구현을 워커에게 넘겨야 한다면 사용자에게 actor 변경을 알리고 기본 Pilot 실행으로 재분류한다. 이미 만든 상태와 산출물은 재사용하되 주체 기록을 사실대로 갱신한다.

## 6. `opal-self-pm` 대화형 루프

`opal-self-pm`은 고정 Pilot이 아니라 종료 조건을 가진 대화형 PM 작업 루프다.

```text
질문
  → 조회·검토·정리
  → 질문
  → 조회·검토·정리
  → 작업 계약 확정
  → 사용자 실행 승인
  → PM 작업·검증
  → 지식·산출물 동기화
  → 사용자 최종 확인
  → 종료
```

새로운 결정이나 범위 변경이 생기면 작업 중에도 질문 단계로 돌아간다. 질문 수를 미리 정하거나 고정 단계로 가장하지 않는다.

### 6.1 한 번에 한 질문

사용자에게는 결정할 질문을 한 개씩 제시한다. 각 질문에는 다음을 포함한다.

- 현재 결정해야 하는 한 가지
- 선택지 또는 답변 범위
- PM 권고 답안
- 권고 이유와 주요 trade-off
- 답에 따라 달라지는 다음 조회 또는 작업

사용자 답변 뒤 PM은 관련 원천을 조회하고, 확인된 사실·결정·남은 쟁점을 짧게 정리한 다음 다음 질문을 한다. 이미 답한 질문을 반복하지 않는다.

### 6.2 시점별 문서·지식 조회

모든 문서를 처음부터 전량 읽지 않는다. 결정 시점에 필요한 원천을 선별하되 다음 영역의 영향 여부는 빠짐없이 판정한다.

| 시점 | 우선 조회 | 목적 |
|---|---|---|
| 시작 | `docs/PROJECT.md`, memory brief, 관련 brain, 코드 구조 | 프로젝트 좌표와 과거 결정 확인 |
| 요구 발견 | 기획서, 정책서, 사용자 흐름, 현행 산출물 | 목표·제약·용어 확정 |
| 설계 결정 | 아키텍처, 인터페이스, 데이터 모델, 관련 코드 | 소비자와 변경 영향 확정 |
| 수정 직전 | `docs/CONVENTIONS.md`, `docs/SECURITY.md`, 운영·배포 제약 | 구현 규칙과 위험 확인 |
| 범위 변경 | 새 범위에 맞춰 원천 재선별 | 누락된 영향 재평가 |
| 완료 직전 | 변경 파일과 관련 docs·brain·memory·코드맵 | 낡은 원천 동기화 |

각 영역은 `update` 또는 `no-op + 근거`로 판정한다. “관련 없어 보임” 같은 무근거 생략은 허용하지 않는다.

### 6.3 작업 전 계약과 승인

파일·설정·데이터를 쓰기 전에 PM은 다음 계약을 한 번에 제시하고 사용자 승인을 받는다.

1. 목표와 완료 조건
2. 포함 범위와 제외 범위
3. 변경 대상
4. 확정된 결정과 남은 가정
5. 검증 방법
6. 예상되는 docs·기획·설계·brain·memory 영향

승인 이후 계약 안의 가역적 작업은 연속 수행한다. 계약 밖 변경, 별도 권한 경계, 사용자 선택이 필요한 새 결정이 발생하면 작업을 멈추고 질문 루프로 돌아간다.

### 6.4 실행과 검증

PM은 확정 계약에 따라 직접 수정한다. 검증은 변경 성격에 비례하되 실제 명령·응답·파일 확인 증거가 있어야 한다. 독립성 요구가 있으면 공통 `op-*` 검사 skill이나 read-only evaluator를 호출한다.

대화형 실행은 Pilot Gate를 흉내 내지 않는다. 대신 다음 최소 완료 조건을 갖는다.

- 합의한 결과가 실제 산출물에 반영됨
- 필요한 정적·동적 검증 통과
- 실패와 수정의 재검증 완료
- 변경 범위 밖 사용자 작업 보존
- 지식·산출물 영향 판정 완료

### 6.5 지식 동기화와 최종 확인

작업 후 다음 영역을 모두 판정하고 결과를 사용자에게 보여준다.

| 정보 유형 | owner |
|---|---|
| 현재 요구·정책·사용 흐름 | 기획·정책 문서 |
| 구조·인터페이스·데이터 모델 | 설계·아키텍처 문서 |
| 사용법·운영 절차 | 관련 프로젝트 문서 |
| 결정 이유·채택/폐기 근거 | Project Brain |
| 다음 세션 주의사항·후속 | project memory |
| 코드 구조·exports·depends | code-scan 원천 |

중복 기록하지 않고 각 owner에 현재 사실만 반영한다. 모든 영향이 `update` 또는 `no-op + 근거`로 닫힌 뒤 사용자에게 최종 확인을 요청한다.

- 사용자가 확인하면 종료한다.
- 수정 의견이 있으면 질문·조회·정리 루프로 돌아간다.
- 최종 확인 전에는 완료로 선언하지 않는다.

## 7. 경량 실행 기록

`opal-self-pm`은 Pilot state를 만들지 않지만, 대화 압축·세션 전환에도 결정을 잃지 않도록 machine-readable 경량 기록을 남길 수 있어야 한다.

최소 필드는 다음과 같다.

```json
{
  "objective": "...",
  "status": "discovering|awaiting_approval|executing|awaiting_confirmation|done",
  "decisions": [],
  "open_questions": [],
  "approved_scope": [],
  "changed_files": [],
  "validation": [],
  "knowledge_impact": []
}
```

이는 `state.json`이나 task pipeline의 대체물이 아니다. 정확한 저장 위치, 생성 도구, 보존 기간은 구현 PLAN에서 기존 runtime 기록과 충돌 여부를 확인해 확정한다.

## 8. 공통 검사 Capability 연동

PM 직접 수행에서 보안·컨벤션 검사를 재사용하기 위해 `opal-pilot-gc`의 검사 본체를 다음 독립 skill로 분리한다.

- `op-security-check`
- `op-convention-check`
- `op-gc-report`

`opal-pilot-gc`는 이 skill들을 조합하는 경량 wrapper로 남고, `opal-self-pm`과 다른 Pilot도 필요한 시점에 직접 호출한다. 세부 입력·출력·reference 정책은 동반 제안서가 소유한다.

프로젝트 규칙과 사용자가 승인한 공식 표준만 차단 가능한 `enforce` 기준이 된다. 외부 community template은 기본 `advisory`이며, 검토와 사용자 승인 없이 차단 규칙으로 승격하지 않는다.

## 9. Capability 선택과 보강

PM은 실행 시점의 실제 capability만 사용한다.

1. 현재 workflow 또는 문제에 맞는 기존 OPAL skill·tool을 먼저 확인한다.
2. 기본 도구로 충분하면 새 skill을 만들지 않는다.
3. 공식 문서나 외부 자료가 필요하면 최신성과 출처를 확인한다.
4. 외부 skill 설치가 필요하면 출처·권한·license·실행 위험을 제시하고 별도 승인을 받는다.
5. 반복 가능한 공백이고 기존 skill과 중복되지 않을 때만 skill 생성을 제안한다.

설치·생성은 원래 작업 승인에 포함되지 않는다. 승인 후 생성하더라도 registry 검증과 실제 호출 검증을 통과해야 사용 가능 상태로 본다.

## 10. 하네스 변경 범위

| owner | 변경 방향 |
|---|---|
| `opal/core/references/opal-pm.md` | L2를 `--pm` actor와 `opal-self-pm`으로 대체 |
| `opal/core/references/harness/guards.md` | Pilot actor 분기, 직접 수행 승인·독립 검증 경계 정의 |
| `opal/core/references/pm/dispatch-process.md` | Steps 1~3을 PM 직접 작업 preflight로 재사용 가능하게 분리 |
| `opal/core/references/harness/capability.md` | PM의 capability 선택·보강 계약 추가 |
| Pilot parser·registry·help | 공통 `--pm` 옵션과 `oppm` alias 등록 |
| Pilot·단계 skill | `actor=worker|pm` 입력과 실행 주체별 dispatch 분기 추가 |
| 신규 `opal-self-pm` | 질문 루프, 승인, 기록, 실행, 동기화, 최종 확인 구현 |
| GC 관련 skill·agent | 동반 제안서의 공통 검사 capability로 전환 |
| README·PROJECT·ARCHITECTURE | 사용자 진입점과 컴포넌트 관계 갱신 |
| install·adapter | 모든 지원 플랫폼에서 같은 명령과 옵션 노출 |

## 11. 수용 기준

- [ ] `//opd`, `//opd --pm`, `//oppm`의 차이가 사용자 관점에서 명확하다.
- [ ] `--pm`이 workflow나 mode가 아니라 actor 옵션으로 파싱된다.
- [ ] 지원 Pilot에서 `--pm`이 기존 단계·산출물·상태·Gate를 그대로 유지한다.
- [ ] PM이 분석·작성·구현을 직접 수행하며 구현 위임은 직접 수행으로 기록되지 않는다.
- [ ] 독립 검토·평가·테스트에 한해 서브에이전트를 사용할 수 있다.
- [ ] `opal-self-pm`이 질문 한 개와 권고 답안을 반복하는 adaptive loop로 동작한다.
- [ ] 쓰기 전 목표·범위·대상·결정·검증·지식 영향을 제시하고 사용자 승인을 받는다.
- [ ] 범위나 결정이 바뀌면 실행 중에도 질문 루프로 복귀한다.
- [ ] 완료 전 프로젝트·기획·설계·컨벤션·보안·brain·memory·코드맵 영향을 모두 판정한다.
- [ ] 영향 대상은 갱신하고 비대상은 `no-op + 근거`로 기록한다.
- [ ] `opal-self-pm`은 사용자 최종 확인 전 종료하지 않는다.
- [ ] 외부 설치·권한·비가역 변경·commit·배포는 별도 승인 경계를 유지한다.
- [ ] 세 공통 GC skill이 Pilot과 `opal-self-pm`에서 같은 입력·결과 계약으로 호출된다.
- [ ] 기존 L2 전용 제한과 모호한 `direct-workflow`·`direct-adaptive` 사용자 용어가 owner 문서에서 제거된다.

## 12. 구현 순서

1. 공통 actor 모델과 명령 파싱 계약을 정하고 한 Pilot에서 `--pm`을 수직 검증한다.
2. `opal-self-pm`의 대화 루프·승인·최종 확인·경량 기록을 구현한다.
3. GC 공통 capability를 분리하고 두 직접 수행 경로에 연결한다.
4. 나머지 Pilot으로 `--pm` 지원을 확산한다.
5. L2 참조를 제거하고 README·PROJECT·ARCHITECTURE·help·adapter를 동기화한다.
6. 일반 Pilot, `--pm` Pilot, `//oppm`의 회귀·통합 시나리오를 검증한다.

첫 구현은 모든 Pilot을 동시에 바꾸지 않고, actor 경계와 상태·Gate 보존을 한 Pilot에서 입증한 뒤 확산하는 방식을 권고한다.
