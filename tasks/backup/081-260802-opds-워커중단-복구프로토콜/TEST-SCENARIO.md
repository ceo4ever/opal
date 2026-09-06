# TEST SCENARIO: 워커 중단 복구 프로토콜 + 디스패치 산출량 상한 + 증분 저장 규율 SSOT화

> 작성일: 2026-08-02 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반 (작성자 분리 — PLAN 워커는 opal-plan-agent)

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `opal-harness.md` §1 표 행 추가 | 표를 참조 관계로 인용하는 하위 문서가 기존 8행 전제로 동작 | P2 | L1 | S-1 |
| H-2 | `pm-review-gate.md` 신규 절 삽입 | `opal-pm.md:66` 열거형 포인터("검토 11항목")가 신규 절 미반영 (선행 결함) | P2 | L1 | S-14 |
| H-3 | `pm-review-gate.md` 파일 변경 | `test-regression.js:930`이 본문의 `validate --changed`·커버리지 문구 존치를 검사 — 절 삽입으로 유실 시 실패 | P1 | L2 | S-12 |
| H-4 | `dispatch-process.md` 2개소 동시 수정 | 병렬 편집 시 후행 저장이 선행 편집을 덮어써 한쪽만 반영 | P1 | L1 | S-3, S-5 |
| H-5 | 수치 중복 기재 | 동일 수치가 2파일에 존재하면 향후 한쪽만 갱신되어 규칙 불일치 | P1 | L1 | S-8 |
| H-6 | install 재배포 | `install-mac.sh:208-212`가 배포본에서 `## 변경이력` 이후를 strip — 단순 diff는 항상 불일치(오탐) | P2 | L2 | S-10 |
| H-7 | REQ-6 메모리 졸업 | `promote`는 `memory/<file>.md` 실파일 전제 — 대상 2건 파일 부재로 `memory_file_not_found` 거부 | P1 | L2 | S-11 |
| H-8 | `parallel-execution.md` 변경이력 | 이 파일에 `## 변경이력` 절 자체가 없음(89줄) — REQ-5 AC 충족에 절 신설 선행 필요 | P2 | L1 | S-7 |
| H-9 | 주입 템플릿 고정 항목 | `## 핵심 제약`은 원래 "문서에서 추출한 [MUST]" 슬롯 — 문서 무관 고정 규율 혼입 시 근거 역추적 혼선 | P2 | L1 | S-5 |
| H-10 | 두 문서 문언 상충 | SSOT(`dispatch-process.md`)와 `op-dev-execute` Step 4 문언이 다르면 워커가 따를 기준 모호 | P1 | L1 | S-6 |
| H-11 | 규칙 재현성 (목표 자체) | 규칙이 등재돼도 **사전 지식 없는** 다음 PM이 문서만으로 동일 대응을 재현하지 못하면 목표 미달 | P1 | L2, L3 | S-13, S-15 |
| H-12 | 새 SSOT의 로드 조건 | `dispatch-process.md`가 단일 디스패치 경로에서 실제로 로드되지 않으면, 앵커 이동이 무효가 되고 080형 재발("규칙은 있는데 그 시점에 안 읽힘")이 그대로 남는다 | P1 | L1 | S-16 |
| H-13 | 규율의 프롬프트 도달 | 주입 템플릿 2줄이 실제 워커 디스패치 프롬프트에 포함되지 않으면, "프롬프트 의존 → SSOT 이관"이라는 교체 자체가 미성립 | P1 | L2 | S-17 |
| H-14 | 자기적용 미준수 | 본 태스크가 신설한 산출량 상한을 본 태스크 EXECUTE가 지키지 않으면, 규칙이 실사용에서 채택되지 않음을 스스로 입증 | P2 | L2 | S-18 |

> **가설 추가 이력**
> - **H-11** (1회차, PM 추가): PLAN의 H-1~H-10은 전부 개별 변경의 무결성 가설이며 **태스크 목표(재현성) 자체를 검증하는 가설이 없었다**.
> - **H-12~H-14** (2회차, 평가자 gaps 반영): 1회차 시나리오 집합은 전부 "문서에 등재됐는가"까지만 검증하고 **"규칙이 실제 적용 경로에 도달하는가"를 아무도 검증하지 않았다**(SCENARIO-GATE-1.md G-2·G-3·G-4). 080형 재발이 정확히 그 지점에서 일어난다.

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 본 태스크는 DB·런타임 데이터가 없는 문서 규칙 트랙이다. "테이블" 자리에는 검증 대상 파일을, "식별자" 자리에는 앵커(절·행)를 기재한다.

| 테이블(파일) | 식별자(앵커) | 상태 | 출처 |
|--------------|-------------|------|------|
| `opal/core/references/opal-harness.md` | §1 자동 루핑 제약 표 (8행), 변경이력 최신 v6.7 | 변경 전 (git clean) | 저장소 HEAD |
| `opal/core/references/harness/pm-review-gate.md` | `### 워커 완료 선언` 블록, 표준 검토 항목 1~14, 변경이력 최신 v1.8 | **변경 전이나 080 미커밋분 존재** | 워킹트리 (git `M`) |
| `opal/core/references/pm/dispatch-process.md` | Step 6 항목 1~4, 워커 컨텍스트 주입 템플릿 `## 핵심 제약`, 변경이력 최신 v1.5 | 변경 전 (git clean) | 저장소 HEAD |
| `opal/core/references/harness/parallel-execution.md` | §7.4 판단 주체 bullet, 파일 말미 89줄, 변경이력 절 **부재** | 변경 전 (git clean) | 저장소 HEAD |
| `opal/skills/op-dev-execute/SKILL.md` | Step 4 (`:92-95`), 변경이력 최신 v2.3 | 변경 전 (git clean) | 저장소 HEAD |
| `.opal/MEMORY.json` | `memories[]` 중 `status: candidate` 2건 | 변경 전 (미커밋분 존재) | 워킹트리 (git `M`) |
| `~/.opal/` 배포본 | 위 5파일의 배포 사본 | install 이전 (구 버전) | 직전 install 산출 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | `opal-harness.md` §1 표 8행 | Step 1 워커가 행 1개 + note + 변경이력 삽입 | 표 9행, 신규 행 3컬럼 완비, 셀에 `3개` 부재 |
| S-2 | `pm-review-gate.md` 절 목록 (신규 절 부재) | Step 2 워커가 신규 절 + 역할 라인 + 변경이력 삽입 | `### 워커 중단 시 산출물 실측 판정` 절 존재, 1·2·3 단계 순서, `[MUST]` 덮어쓰기 금지 |
| S-3 | `dispatch-process.md` Step 6 항목 1~4 | Step 3 워커가 항목 5 삽입 | 항목 1~5 연속, "3개를 초과"·"관측 기반 잠정치"·"4~9 구간은 미검증" 존재 |
| S-4 | `parallel-execution.md` §7.4 4 bullet | Step 4 워커가 참조 bullet 1줄 삽입 | §7.4 bullet 5개, 신규 줄에 숫자 임계값 부재, Step 6 참조 존재 |
| S-5 | 주입 템플릿 `## 핵심 제약` 펜스 | Step 3 워커가 고정 2줄 + 하단 note 삽입 | 펜스 **내부** 2줄 + `← 전 워커 공통 고정` 라벨, 펜스 하단 note 존재 |
| S-6 | `op-dev-execute` Step 4 원문 (`:92-95`) | Step 5 워커가 Step 4 치환 | 제목 "체크리스트 갱신 및 증분 저장", SSOT 경로 참조 존재, 규율 원문 복제 0건 |
| S-7 | 5파일 변경이력 (parallel-execution은 절 부재) | Step 1~5 워커가 각 파일에 변경이력 행 추가 | 5파일 전부 `(081)` 행 ≥1, `parallel-execution.md`는 신설 절에 2행 |
| S-8 | 변경 후 5파일 전체 | (검증만 — 편집 없음) | `1회`=harness 1파일, `3개` 상한=dispatch 1파일, 3단계 본문=pm-review-gate 1파일 |
| S-9 | 변경 후 신규 상호 참조 5건 | (검증만) | 5건의 참조 대상 파일·앵커가 모두 실재 |
| S-10 | 소스 5파일(변경 후) + 배포본(구) | `./scripts/install-mac.sh` 실행 | strip 기준 diff 5건 전부 0줄 |
| S-11 | `MEMORY.json` candidate 2건 | `memory-tool update --status promoted` ×2 + `append --kind history` ×1 | candidate 0건, promoted 2건, history에 081 행 |
| S-12 | 변경 후 `pm-review-gate.md` | `node --test test-regression.js` | 전량 Pass (특히 `077 S-21`) |
| S-13 | 배포된 규칙 문서만 로드한 **신규 컨텍스트 워커** (정답 미고지) | "워커가 600초 스톨했다" 상황만 제시하고 대응안 산출을 요구 | 산출된 대응이 R-1(재시도 1회)·R-2(실측 판정 3단계)·R-3(3개 초과 분할) 3요소를 자력으로 포함 |
| S-14 | `opal-pm.md:66` | (관측만 — 변경 없음) | "검토 11항목" stale 여부 기록, 후속 F-4 입력 |
| S-15 | S-13 워커 산출물 | 캡틴이 산출 대응의 실무 타당성을 판정 | 자동 대조로는 잡히지 않는 해석 오류·의미 왜곡 부재 |
| S-16 | `opal-pm.md` §3 · `AGENT.md` Lazy 테이블 | (검증만) | `dispatch-process.md` 로드 조건이 **무조건("워커 디스패치 직전, 매번")**이고 `parallel-execution.md`의 조건부("병렬 디스패치 시")와 다름이 문서로 확인됨 |
| S-17 | 본 태스크 EXECUTE 디스패치 프롬프트 원문 | Step 1~5 워커 디스패치 실행 | 각 프롬프트에 주입 템플릿 고정 2항목(증분 저장·입력 축소)이 실제 포함 |
| S-18 | 본 태스크 §4.2 배치 구성 | Step 1~5 디스패치 실행 | 배치별 산출 파일 수가 전부 3개 이하 (Phase1=2 / Phase2=1 / Phase3=2) |
| S-19 | `dispatch-process.md` Step 6 항목 5 문언 | (검증만) | "3개를 초과" 문언이 3개=분할 불요 / 4개=분할 의무로 단일 해석되며 off-by-one 모호성 부재 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 파일 검사)

#### S-1: 자동 루핑 제약 표 신규 행 + 수치 유일성 준수

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `opal/core/references/opal-harness.md` §1 자동 루핑 제약 표 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 정적 검사)** |
| 조건 | Step 1 완료 후. 기존 8행이 보존된 상태 |
| 기대 결과 | ①"워커 프로세스 비정상 종료" 행 1개 존재 ②3컬럼(실패 유형 / `1회 (동일 컨텍스트 재개)` / 새 컨텍스트로 분할 재배치) 완비 ③신규 행·보충 note에 `3개` 부재 ④`pm/dispatch-process.md` Step 6 참조 존재 ⑤기존 8행 무변경 |
| 도구 | grep / git diff |
| 실행 명령 | `grep -n "워커 프로세스 비정상 종료\|자동 루핑 제약\|3개" opal/core/references/opal-harness.md`; `git diff opal/core/references/opal-harness.md` |
| 결과 | Pass |
| 상세 | ①58행에 "워커 프로세스 비정상 종료 (스톨 · 응답 중 연결 종료)" 행 확인 ②3컬럼 완비: `1회 (동일 컨텍스트 재개)` / `새 컨텍스트로 분할 재배치 (분할 기준: pm/dispatch-process.md Step 6)` ③신규 행 + 64행 보충 note("동일 컨텍스트 재개가 같은 지점에서 재실패하면...") 전체에 `3개` 리터럴 0건(grep 확인, 다만 note에 "재개 **3회**"는 존재 — `3개`와는 다른 문자열이라 무관) ④분할 기준에 `pm/dispatch-process.md` Step 6 참조 존재 ⑤`git diff` 결과 기존 8행(53~57행)은 컨텍스트 라인(공백 diff)으로만 나타나고 `-` 삭제 라인 0건, 신규 3행(표 행+공백+note)만 `+` 추가 — 무변경 확인 |

#### S-2: 산출물 실측 판정 절 신설 + 덮어쓰기 금지 [MUST]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3(부분), REQ-2 AC |
| 대상 | `opal/core/references/harness/pm-review-gate.md` 신규 절 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 정적 검사)** |
| 조건 | Step 2 완료 후 |
| 기대 결과 | ①`### 워커 중단 시 산출물 실측 판정` 절 존재 ②번호 1·2·3 단계가 순서대로 존재 ③"완료분 파일을 재작업 대상에 포함하거나 덮어쓰지 않는다"가 `[MUST]` 접두 표현 ④절 본문에 `1회`·`3개` 수치 부재, 두 SSOT 경로 참조만 존재 ⑤역할 라인(`:5`)에 신규 절 반영 |
| 도구 | grep |
| 실행 명령 | `grep -n "^### 워커 중단 시 산출물 실측 판정" -A 15 opal/core/references/harness/pm-review-gate.md`; `grep -n "1회\|3개" opal/core/references/harness/pm-review-gate.md`; `grep -n "^> 역할:" opal/core/references/harness/pm-review-gate.md` |
| 결과 | Pass |
| 상세 | ①17행 `### 워커 중단 시 산출물 실측 판정` 절 존재 확인 ②21~23행에 "1. 산출물 확정" → "2. 완료/잔여 판정" → "3. 잔여만 재배치" 순서 확인 ③23행 "**[MUST] 완료분 파일을 재작업 대상에 포함하거나 덮어쓰지 않는다**" — `[MUST]` 접두 확인 ④전역 grep으로 "1회"·"3개" 매치 라인은 74/102/115/143/144행뿐이며 전부 신규 절(17~25행) 밖의 기존 문구(headerSource 설정·재지시 횟수 등) — 신규 절 본문에는 두 수치 부재, 25행에 `opal-harness.md` §1 표 / `pm/dispatch-process.md` Step 6 두 SSOT 경로 참조만 존재 ⑤5행 역할 라인이 "워커 완료 선언 / 워커 중단 시 산출물 실측 판정 / 검토 절차(문서 QA · 표준 검토 항목) / Pass·Fail 판정 / 문서 등록 확인 / 하네스와의 관계"로 갱신되어 신규 절 반영 확인 |

#### S-3: 디스패치 산출량 상한 + 잠정치 단서

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `opal/core/references/pm/dispatch-process.md` Step 6 항목 5 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 정적 검사)** |
| 조건 | Step 3 완료 후 |
| 기대 결과 | ①Step 6 항목 번호가 1~5로 연속 ②"산출 파일이 3개를 초과" 존재 ③"관측 기반 잠정치"·"4~9 구간은 미검증" 존재 ④동일 파일 다중 Step은 같은 디스패치 순차 편집 규정 존재 |
| 도구 | grep |
| 실행 명령 | `sed -n '149,162p' opal/core/references/pm/dispatch-process.md`; `grep -n "3개를 초과\|관측 기반 잠정치\|4~9 구간은 미검증\|같은 경로는 1개로 계수" opal/core/references/pm/dispatch-process.md` |
| 결과 | Pass |
| 상세 | ①Step 6 항목이 153~157행에 1,2,3,4,5로 연속 번호 확인(5번이 신규 "산출량 상한") ②157행 "단일 디스패치가 생성·수정하는 **산출 파일이 3개를 초과하면**" 존재 ③158행 "임계값 3은 **관측 기반 잠정치**다... **4~9 구간은 미검증**이다" 존재 ④157행 "동일 파일을 2개 이상 Step이 변경하면 분할하지 않고 같은 디스패치에 묶어 순차 편집한다(동시 편집 시 후행 저장이 선행 편집을 덮어쓰는 충돌 방지)" 규정 존재 |

#### S-4: §7.4 참조 1줄 — 본문 복제 금지 + 앵커 타당성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5(부분), REQ-3 AC |
| 대상 | `opal/core/references/harness/parallel-execution.md` §7.4 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep + diff 정적 검사)** |
| 조건 | Step 3 → Step 4 순서 준수 후 |
| 기대 결과 | ①§7.4에 추가된 줄이 **정확히 1줄** ②그 줄에 임계값 숫자 부재 ③`pm/dispatch-process.md` Step 6 참조 존재 ④기존 수치(50KB/200KB/Max 2) 무변경 ⑤`opal-harness.md` §2 하네스 모듈 표의 `harness/parallel-execution.md` 행 로드 시점이 "병렬 디스패치 시"로 유지 (행번호 미지정 — 같은 파일 §1 편집으로 드리프트하므로 값으로 조회) |
| 도구 | grep / git diff |
| 실행 명령 | `git diff opal/core/references/harness/parallel-execution.md`; `sed -n '58,65p' opal/core/references/harness/parallel-execution.md`; `sed -n '96,112p' opal/core/references/opal-harness.md` |
| 결과 | Pass (단, ⑤ 앵커 라인번호는 오기 — 상세 참조) |
| 상세 | ①git diff §7.4 구간(58~65행)에 `+` 라인은 "**산출량 상한(참조)**" 1줄뿐, 정확히 1줄 추가 확인 ②그 줄 본문에 숫자 임계값 없음("규칙 본문과 임계값은 `pm/dispatch-process.md` Step 6 실행 라우팅에 있다"만 서술) ③같은 줄에 `pm/dispatch-process.md` Step 6 참조 존재 ④위쪽 기존 3개 bullet(50KB/200KB 고부하 기준, Max 2개, 판단 주체)은 diff상 컨텍스트(무변경) 확인 ⑤`opal-harness.md`의 하네스 모듈 로드 시점 표에서 "병렬 처리 \| harness/parallel-execution.md \| 병렬 디스패치 시 \| §7" 행은 **현재 105행**이며 값("병렬 디스패치 시")은 유지되어 있음 — 그러나 시나리오가 지정한 "`opal-harness.md:102`" 앵커는 102행(현재 "추가작업" 행)과 불일치. 이는 S-1이 §1 표에 3행(행+공백+note)을 선행 삽입하며 그 아래 §2 모듈 표 전체가 3행씩 밀린 결과다(원래 102행이었던 것이 편집 후 105행이 됨). 값 자체는 기대대로 유지되므로 본 시나리오 실질 판정은 Pass로 하되, 앵커 라인번호 표기가 파일 자기수정으로 stale해졌다는 점을 S-16과 연계해 기록한다. |

#### S-5: 주입 템플릿 고정 2항목 — 펜스 내부 배치

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-9 |
| 대상 | `opal/core/references/pm/dispatch-process.md` 워커 컨텍스트 주입 템플릿 `## 핵심 제약` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 정적 검사)** |
| 조건 | Step 3 완료 후 (S-3와 동일 파일 — 두 편집이 모두 살아 있어야 함) |
| 기대 결과 | ①"증분 저장"·"입력 축소" 2줄이 코드 펜스 **내부**에 존재 ②각 줄에 `← 전 워커 공통 고정` 라벨 ③펜스 하단에 고정 항목 note 존재 ④**S-3의 Step 6 항목 5가 동시에 존재**(H-4 덮어쓰기 부재 확인) |
| 도구 | grep / awk (펜스 범위 판정) |
| 실행 명령 | `grep -n '\`\`\`' opal/core/references/pm/dispatch-process.md`; `sed -n '80,110p' opal/core/references/pm/dispatch-process.md`; `grep -n "3개를 초과" opal/core/references/pm/dispatch-process.md` |
| 결과 | Pass |
| 상세 | ①코드 펜스는 85행(여는 펜스)~103행(닫는 펜스) 범위. "증분 저장"(93행)·"입력 축소"(94행) 2줄이 85~103 범위 내부에 위치 확인 ②두 줄 모두 줄 끝에 `← 전 워커 공통 고정` 라벨 확인 ③펜스 종료(103행) 직후 105행에 "> **전 워커 공통 고정 2항목**(증분 저장 · 입력 축소)은 Step 2 문서 선별 결과와 무관하게 **모든 워커 디스패치에 항상 포함**한다..." note 존재 확인 ④같은 파일 157행에 S-3에서 확인한 Step 6 항목 5(산출량 상한)가 동시에 살아있음 확인 — 두 편집(S-3/S-5)이 서로 덮어쓰지 않았음(H-4 무결성) |

#### S-6: 두 문서 문언 무충돌 — 규율 원문 복제 0건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-10 |
| 대상 | `opal/skills/op-dev-execute/SKILL.md` Step 4 ↔ `dispatch-process.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 정적 검사)** |
| 조건 | Step 3 → Step 5 순서 준수 후 |
| 기대 결과 | ①Step 4 제목이 "체크리스트 갱신 및 증분 저장" ②`pm/dispatch-process.md` 참조 존재 ③규율 원문("말미 일괄 저장 금지"·"전체 통독 금지")이 스킬 파일에 복제 0건 ④두 문서를 나란히 읽었을 때 상충 지시 없음 |
| 도구 | grep |
| 실행 명령 | `sed -n '91,97p' opal/skills/op-dev-execute/SKILL.md`; `grep -n "말미 일괄 저장 금지\|전체 통독 금지\|말미 일괄\|통독 금지" opal/skills/op-dev-execute/SKILL.md` |
| 결과 | Pass |
| 상세 | ①91행 제목이 "### Step 4. 체크리스트 갱신 및 증분 저장"로 확인 ②96행에 "SSOT는 `opal/core/references/pm/dispatch-process.md` §워커 컨텍스트 주입 템플릿 §핵심 제약(전 워커 공통 고정 2항목)이며, 본 스킬은 이를 복제하지 않는다" 참조 존재 ③grep 결과 "말미 일괄 저장 금지"·"전체 통독 금지" 정확한 원문은 스킬 본문(Step 4, 91~96행) 어디에도 없음 — 유일한 매치는 210행 변경이력 행("말미 일괄 갱신 금지"로 유사 서술, 변경 사실을 기술하는 changelog 문구일 뿐 규율 본문 재서술이 아님) ④본문 문구("갱신 시점은 산출물 1개를 완결 저장한 직후다 — 모든 Step을 끝낸 뒤 일괄 갱신하지 않는다")와 dispatch-process.md 원문("산출물 1개를 완결 저장한 뒤 다음 산출물로 이동한다. 말미 일괄 저장 금지")이 같은 시점 규율을 가리켜 상충 없음 |

#### S-7: 5파일 변경이력 행 + 형식 준수

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-8 |
| 대상 | 대상 5파일 `## 변경이력` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 정적 검사)** |
| 조건 | Step 1~5 완료 후 |
| 기대 결과 | ①5파일 전부 `(081)` 포함 행 ≥1 ②일시가 `YYYY-MM-DD HH:mm` 형식 ③`parallel-execution.md`는 신설 절에 v1.0·v1.1 2행 ④버전 번호가 각 파일 직전 버전의 다음 값(v6.8 / v1.9 / v1.6 / v1.1 / v2.4) |
| 도구 | grep |
| 실행 명령 | `git diff opal/core/references/opal-harness.md opal/core/references/harness/pm-review-gate.md opal/core/references/pm/dispatch-process.md opal/core/references/harness/parallel-execution.md opal/skills/op-dev-execute/SKILL.md` (변경이력 섹션 확인) |
| 결과 | Pass |
| 상세 | ①5파일 전부 `(081)` 포함 변경이력 행 ≥1 확인 — opal-harness.md v6.8("2026-08-02 16:03"), pm-review-gate.md v1.9("2026-08-02 16:03"), dispatch-process.md v1.6("2026-08-02 16:06"), parallel-execution.md v1.1("2026-08-02 16:09"), op-dev-execute/SKILL.md v2.4("2026-08-02 16:09") ②5건 모두 `YYYY-MM-DD HH:mm` 형식 확인 ③parallel-execution.md는 기존에 변경이력 절 자체가 없었으므로(H-8) 절 신설과 함께 v1.0("초기 작성 — opal-harness.md §7 분리", 일시 "-")·v1.1(081) 2행이 함께 기재됨 확인 ④직전 최신 버전 대비: opal-harness.md v6.7→v6.8, pm-review-gate.md v1.8→v1.9, dispatch-process.md v1.5→v1.6, op-dev-execute v2.3→v2.4 모두 다음 값 확인. parallel-execution.md는 직전 버전이 없었으므로(신규 절) v1.0(초기)+v1.1(081)로 시작 — "직전 버전의 다음 값" 규칙이 v1.0 기준 v1.1로 일관 적용됨 |

#### S-8: 수치 리터럴 유일성 (Governance)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | 변경 후 5파일 전체 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — 저장소 전역 grep)** |
| 조건 | Step 1~5 완료 후 |
| 기대 결과 | ①재시도 상한 `1회` 규정은 `opal-harness.md` 1파일에만 ②산출 `3개` 상한 규정은 `dispatch-process.md` 1파일에만 ③실측 판정 3단계 본문은 `pm-review-gate.md` 1파일에만 ④나머지 문서는 경로 참조만 보유 |
| 도구 | grep -rn |
| 실행 명령 | 5파일 대상 `grep -l "동일 컨텍스트 재개"` / `grep -l "3개를 초과"` / `grep -l "산출물 확정\|완료/잔여 판정\|잔여만 재배치"` / 파일별 `grep -n "1회"`, `grep -n "3개"` |
| 결과 | Pass |
| 상세 | ①"1회 (동일 컨텍스트 재개)" 리터럴은 `opal-harness.md`(58행) 1파일에만 존재. "동일 컨텍스트 재개"라는 용어 자체는 pm-review-gate.md(25행)·dispatch-process.md(160행)에도 등장하지만 두 곳 다 "동일 컨텍스트 재개 횟수 상한은 `opal-harness.md` ...를 따른다"는 포인터 문장이며 `1회` 수치를 재기재하지 않음(grep으로 두 줄에 "1회" 부재 확인) ②"3개"는 5파일 전체 grep 결과 `dispatch-process.md`(157·158·183행)에만 존재, 나머지 4파일 0건 확인 ③"산출물 확정"·"완료/잔여 판정"·"잔여만 재배치" 3단계 본문(번호 1·2·3 목록)은 `pm-review-gate.md`(21~23행) 1파일에만 존재. `opal-harness.md`(64행)에 "실제 산출물을 확정하고 잔여만 재배치하는 절차는 ... 따른다"는 1줄 포인터가 있으나 3단계 번호 목록을 재서술하지 않음(단계 구분 없는 요약 지시문) ④나머지 문서(parallel-execution.md, op-dev-execute/SKILL.md)는 세 수치·본문 어느 것도 갖지 않고 경로 참조만 보유 확인 |

#### S-9: 참조 무결성 — 신규 상호 참조 5건

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-10 |
| 대상 | 신규 도입된 문서 간 참조 5건 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 앵커 실재 확인)** |
| 조건 | Step 1~5 완료 후 |
| 기대 결과 | (a) harness → pm-review-gate §워커 중단 시 산출물 실측 판정 (b) harness → dispatch Step 6 (c) pm-review-gate → harness §1 표 (d) pm-review-gate·parallel-execution·op-dev-execute → dispatch 해당 절 (e) dispatch → pm-review-gate 신규 절 — **5건 전부 대상 앵커가 실재**하며 dangling 0건 |
| 도구 | grep |
| 실행 명령 | `grep -n "^## " opal/core/references/opal-harness.md`; `grep -n "^## \|^### 워커 중단\|^### 검토 절차" opal/core/references/harness/pm-review-gate.md`; 각 참조 문구 grep |
| 결과 | Pass |
| 상세 | (a) opal-harness.md:64 → `harness/pm-review-gate.md` §워커 중단 시 산출물 실측 판정 — 대상 헤딩 실재(pm-review-gate.md:17) (b) opal-harness.md:58 → `pm/dispatch-process.md` Step 6 — 대상 실재(dispatch-process.md:149 "## Step 6. 실행 라우팅") (c) pm-review-gate.md:25 → `opal-harness.md` §1 자동 루핑 제약 표 — opal-harness.md의 "## 1. Guards (제약)"(8행) 하위 "### 자동 루핑 제약"(44행) 실재 확인 (d) pm-review-gate.md:25 / parallel-execution.md:65 / op-dev-execute/SKILL.md:96 모두 `pm/dispatch-process.md` Step 6(실행 라우팅) 또는 §워커 컨텍스트 주입 템플릿을 가리키며 둘 다 실재 (e) dispatch-process.md:160 → `harness/pm-review-gate.md` §워커 중단 시 산출물 실측 판정 — 실재. 5건 전부 대상 앵커 실존 확인, dangling 0건 |

#### S-14: `opal-pm.md` 열거형 포인터 stale 관측 (비변경)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `opal/core/references/opal-pm.md:66` |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 관측)** |
| 조건 | Step 1~5 완료 후. **본 태스크는 이 파일을 변경하지 않는다** |
| 기대 결과 | "검토 11항목" 표기가 실제 항목 수·신규 절과 불일치함을 기록한다. **Fail 판정 대상이 아니며**, 후속 F-4(문서 포인터 현행화) 입력으로 남긴다 |
| 도구 | grep |
| 실행 명령 | `grep -n "검토 11항목" opal/core/references/opal-pm.md`; `grep -n "^[0-9]\+\. " opal/core/references/harness/pm-review-gate.md` |
| 결과 | 관측 완료 (Fail 비대상) |
| 상세 | opal-pm.md:66 "상세(워커 완료 선언, 검토 11항목, Pass/Fail 판정, 문서 등록 확인, 하네스와의 관계): `harness/pm-review-gate.md` 참조." — "11항목" 표기 확인. 그러나 실제 pm-review-gate.md의 "표준 검토 항목" 번호 목록은 1~14(14개, 077 이전 v1.5부터 이미 14개)이며, 본 태스크(081)가 그 위에 번호 없는 신규 절 "### 워커 중단 시 산출물 실측 판정"까지 추가해 실제 항목 수·구조가 더 벌어졌다. "11항목"은 081 이전부터 이미 stale했고(14개인데 11로 표기) 081로 격차가 그대로 유지·확인됨. Fail 판정 대상 아님 — 후속 F-4(opal-pm.md:66 포인터 문구 현행화, "11항목" → "14항목 + 산출물 실측 판정 절"로 정정) 입력으로 기록 |

#### S-16: 새 SSOT의 로드 조건 무조건성 (앵커 이동의 실효성)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-12 |
| 대상 | `opal/core/references/opal-pm.md` §3 · `opal/core/references/opal-harness.md` §2 하네스 모듈 표(로드 시점 컬럼) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep 정적 검사)** |
| 조건 | Step 1~5 완료 후. **본 시나리오는 081이 변경하지 않는 문서를 검사한다** — 앵커 이동 전제의 사실 확인이 목적 |
| 기대 결과 | ①`opal-pm.md` §3에서 `dispatch-process.md`의 로드 시점이 "워커 디스패치 직전"이며 **매번·무조건**임이 확인된다(조건부 수식어 부재) ②`opal-harness.md` §2 하네스 모듈 표에서 `parallel-execution.md`의 로드 시점이 "병렬 디스패치 시" **조건부**임이 확인된다(행번호가 아니라 행 값으로 조회한다) ③두 로드 조건이 실제로 다르다 — 같다면 앵커 이동의 근거가 무너지므로 **Fail 처리하고 PLAN M-1을 재검토한다** |
| 도구 | grep |
| 실행 명령 | `sed -n '53,62p' opal/core/references/opal-pm.md`; `grep -n "" opal/core/references/opal-harness.md \| sed -n '99,106p'` |
| 결과 | Pass (단, 앵커 라인번호 오기 발견 — 상세 참조, 내용 판정에는 영향 없음) |
| 상세 | ①opal-pm.md §3(53행) "워커에게 작업을 디스패치하기 전에 **매번** 다음 절차를 수행한다: ... → 실행 라우팅(Step 6) ..."(56행 상세 경로가 `pm/dispatch-process.md`) + "Lazy 트리거: 워커 디스패치 직전"(57행) — 조건부 수식어 없이 매번·무조건 확인 ②opal-harness.md 하네스 모듈 표에서 "병렬 처리 \| harness/parallel-execution.md \| 병렬 디스패치 시 \| §7" 행이 조건부("병렬 디스패치 시") 확인. **단, 이 행의 실제 현재 라인은 105행이며, 시나리오가 지정한 102행은 081 자신의 S-1 편집(§1 표에 3행 선삽입)으로 밀려 현재 "추가작업" 행이 되어 있다.** §7 PM Gate 체크(TEST-SCENARIO.md 하단)는 "N-1(S-16 앵커 오기) 정정 완료"라 기재했으나, 그 정정 이후 S-1 편집이 다시 앵커를 밀어낸 것으로 보인다 — **자기참조적 앵커 드리프트**(본 태스크가 검증하려는 문제의 축소판) ③값(무조건 vs 조건부) 자체는 실제로 다름을 확인 — 앵커 이동(dispatch-process.md를 opal-pm.md §3의 무조건 로드 경로로) 근거는 유효, H-12 핵심 판정은 Pass. 단, 라인번호 표기 재정정이 필요함을 F-4에 추가 입력으로 남긴다(정정 완료로 종결 처리한 §7 체크 항목이 재발했음을 캡틴에 보고) |

#### S-19: 임계값 문언의 단일 해석성 (off-by-one 경계)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `dispatch-process.md` Step 6 항목 5 문언 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구 — grep + 문언 판정)** |
| 조건 | Step 3 완료 후 |
| 기대 결과 | ①"3개를 초과"가 사용되어 **산출 3개 = 분할 불요 / 4개 = 분할 의무**로 단일 해석된다 ②"3개 이상"·"약 3개" 등 모호 표현 부재 ③계수 규칙("같은 경로는 1개로 계수")이 명시되어 동일 파일 중복 계수 모호성이 없다 |
| 도구 | grep |
| 실행 명령 | `grep -n "3개를 초과" opal/core/references/pm/dispatch-process.md`; `grep -n "3개 이상\|약 3개\|3개 정도\|3개가량" opal/core/references/pm/dispatch-process.md`; `grep -n "같은 경로는 1개로 계수" opal/core/references/pm/dispatch-process.md` |
| 결과 | Pass |
| 상세 | ①157행 "산출 파일이 3개를 초과하면"만 사용 — "초과"는 수학적으로 `>3`이므로 3개는 불요/4개부터 의무로 단일 해석 ②"3개 이상"·"약 3개"·"3개 정도"·"3개가량" 등 모호 표현 grep 결과 0건(exit 1) ③159행 "산출 파일 수는 PLAN.md §4.2 각 Step의 `**파일**` 항목을 합집합으로 세되, **같은 경로는 1개로 계수한다**" — 계수 규칙 명시로 동일 파일 중복 계수 모호성 제거 확인 |

### L2. 프로세스 통합 (자동, 실 도구 실주행)

#### S-10: install 재배포 후 소스↔배포본 일치

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `scripts/install-mac.sh` 실행 결과 (`~/.opal/` 배포본) |
| 계층 | L2 |
| **실행 방식** | **M1 (도구 실주행)** |
| 조건 | Step 1~5 완료 후. 배포본에서 `## 변경이력` 이후가 strip됨을 전제로 정규화 비교 |
| 기대 결과 | ①install 정상 종료(exit 0) ②5파일 전부 strip 기준 diff 0줄 ③`~/.opal/community-skills/` 사용자 데이터 무변경 |
| 도구 | bash / awk / diff |
| 실행 명령 | (PM 원 실행: `./scripts/install-mac.sh`, AGENTIC-LOG §Step 6 기록) + 본 워커 재검증: `awk '/^## 변경이력/{exit}{print}' <src>` vs 동일 스크립트로 `~/.opal/` 배포본 5파일 각각 `diff` (독립 재실행) |
| 결과 | Partial (①미충족, ②③충족) |
| 상세 | ①AGENTIC-LOG.md §Step 6 기록에 따르면 실제 실행은 **exit 0이 아니라 exit 143(SIGTERM, 10분 타임아웃)**으로 중단됨 — MCP 등록 단계(npx/playwright 캐시 등)에서 장시간 소요된 것으로 추정, 본 태스크 대상 5파일 배포와 무관한 후행 단계. 기대결과 ①은 문자 그대로는 불충족 ②본 워커가 독립적으로 strip-diff 재실행: opal-harness.md/pm-review-gate.md/dispatch-process.md/parallel-execution.md/op-dev-execute·SKILL.md 5파일 전부 `diff` 결과 0줄(변경이력 절 이전 본문 완전 일치) 확인 — 소스↔배포본 실질 목표(REQ-5 AC)는 충족 ③`~/.opal/community-skills/`는 레포 외부 사용자 데이터라 baseline diff 불가(직접 재현 불가능) — 변경 정황·리포트 없음, 미검증으로 기록. **종합**: install 스크립트 자체의 비정상 종료(exit 143)는 이 태스크가 신설한 "워커 중단 시 산출물 실측 판정" 3단계를 PM이 자기적용해 실측 확인 후 재실행 불요로 판단했고(AGENTIC-LOG §Step 6), 본 워커의 독립 재검증도 5파일 diff 0줄로 이를 뒷받침한다. 다만 ① 리터럴 미충족은 은폐하지 않고 Partial로 명기한다. |

#### S-11: 개선 후보 메모리 졸업 (도구 실주행)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `.opal/MEMORY.json` — candidate 2건 |
| 계층 | L2 |
| **실행 방식** | **M1 (도구 실주행 — memory-tool)** |
| 조건 | Step 6(배포) 완료 후. `promote` 서브명령은 파일 부재로 거부되므로 `update --kind memory --status promoted` 경로 사용 |
| 기대 결과 | ①`update` 호출 2건 전부 `ok: true` ②`append --kind history` 1건 `ok: true` ③재조회 시 대상 2건 `status: promoted`, `candidate` 0건 ④`history`에 081 행 존재 ⑤기존 active 메모리 4건 무변경 |
| 도구 | memory-tool |
| 실행 명령 | (PM 원 실행: `memory-tool update --kind memory --status promoted` ×2 + `append --kind history` ×1, AGENTIC-LOG §Step 7 기록) + 본 워커 재검증: `python3 -c "import json; d=json.load(open('.opal/MEMORY.json')); ..."`(candidate/promoted 집계, history[0] 확인) |
| 결과 | Pass |
| 상세 | ①②AGENTIC-LOG §Step 7 기록상 `ok: true` — 도구 호출 자체의 raw 응답은 재현 불가하나 그 결과 상태는 아래 ③④⑤로 직접 재검증됨 ③`.opal/MEMORY.json` 직접 파싱 결과: candidate 0건, promoted 2건("워커 보고는 실측 대조 없이 신뢰 불가", "078 워커 실패 완화책이 079에서 인프라 실패 0건으로 재현됨") — 기대와 일치 ④`history[0]` = "081 워커중단 복구 프로토콜 SSOT화"(가장 최근 항목) 존재 확인. FIFO 상한(5)으로 최고령 075 항목이 밀려남(AGENTIC-LOG §Step 7, `history_count: 5` 유지로 정상 동작) ⑤`git diff .opal/MEMORY.json`에서 status 필드가 변경된 행은 정확히 2건(promoted 전환)뿐이고, 나머지 4건(Console 브레인 구독 인증 / 브레인 질의 콜드 경량화 / 후속 069·070 액션에이전트 관측 확장 / 080 이관 결정)은 `active` 상태로 무변경 확인 |

#### S-12: 기존 회귀 스위트 무손상

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `opal/tools/code-scan/tests/test-regression.js` |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구 실행)** |
| 조건 | Step 2(pm-review-gate 편집) 완료 후 |
| 기대 결과 | ①전량 Pass ②특히 `077 S-21: pm-review-gate.md에 validate --changed 게이트 절차 + 커버리지 언급 유지` Pass ③`opal-harness.md` §9 code-scan 행 검사 Pass |
| 도구 | node --test |
| 실행 명령 | `node --test opal/tools/code-scan/tests/test-regression.js` (본 워커 직접 실행) |
| 결과 | Pass |
| 상세 | 직접 실행 결과: `tests 36 / pass 36 / fail 0 / cancelled 0 / skipped 0`(duration 8627.9ms) ①전량 Pass 확인 ②"✔ 077 S-21: pm-review-gate.md에 validate --changed 게이트 절차 + 커버리지 언급 유지 (0.179041ms)" 개별 Pass 확인(0.18ms) ③"✔ 077 TS-051 (S-21): brain-tool README 2소스 문언 + opal-harness.md §9 code-scan 서브명령 정합" Pass 확인 — 회귀 무손상 |

#### S-13: 목표달성 — 블라인드 재현 테스트 (사전 지식 없는 워커)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | 배포된 규칙 문서 3종 (`~/.opal/references/opal-harness.md` §1 / `harness/pm-review-gate.md` 신규 절 / `pm/dispatch-process.md` Step 6·주입 템플릿) |
| 계층 | L2 |
| **실행 방식** | **M2 (자동화 — 신규 컨텍스트 워커 디스패치)** |
| 조건 | Step 6(install 배포) 완료 후. **정답을 고지하지 않는다** — 워커에게 본 태스크의 TASK·PLAN·TEST-SCENARIO를 주지 않고, 배포된 규칙 문서 경로와 상황만 준다. 프롬프트에 "1회"·"3단계"·"3개" 수치를 포함하지 않는다 |
| 기대 결과 | 워커가 산출한 대응안이 3요소를 **자력으로** 포함한다 — ①재시도 상한 = 1회(동일 컨텍스트 재개) ②중단 후 산출물 실측 판정 3단계(git 실측 → 완료/잔여 판정 → 잔여만 재배치, 완료분 덮어쓰기 금지) ③재배치 시 산출 파일 3개 초과 분할. **3요소 중 1개라도 누락되거나 다른 값을 도출하면 Fail** — 그 경우 어느 문서에서 경로가 끊겼는지 워커 응답으로 역추적한다 |
| 도구 | Agent (신규 컨텍스트 워커, 규칙 문서만 접근) |
| 실행 명령 | PM 실행(디스패치 조건 — 본 TEST-SCENARIO 상단 "S-13 실행 결과" 절에 원문 보존됨): 신규 컨텍스트 워커에게 TASK/PLAN/TEST-SCENARIO 미제공, `tasks/` 접근 금지, 프롬프트에 "1회"·"3단계"·"3개" 수치 미포함, 배포본 3문서(`~/.opal/references/opal-harness.md`, `harness/pm-review-gate.md`, `pm/dispatch-process.md`)만 열람 허용 조건으로 "재시도 정책/산출물 판정/재배치 분할" 질의 |
| 결과 | Pass |
| 상세 | 워커 응답(PM이 원문 보존)을 3요소 대조: ①"스톨(600초대)·연결종료는 '워커 프로세스 비정상 종료' 유형으로, 최대 1회까지만 '동일 컨텍스트 재개'로 재시도... 재실패하면... 새 컨텍스트로 분할 재배치"(근거 opal-harness.md §1 58행+64행 인용) — R-1(1회, 동일 컨텍스트 재개) 정확 일치 ②"① git status --short + git diff --stat으로 실제 파일 확정 ② PLAN.md §4.2 체크리스트와 대조해 Step 단위 완료/잔여 판정... ③ 잔여만 재배치, 완료분은 대상 제외 + Write 대신 Edit 지시"(근거 pm-review-gate.md §워커 중단 시 산출물 실측 판정 17~25행) — R-2(3단계: git 실측→완료/잔여 판정→잔여만 재배치, 완료분 덮어쓰기 금지) 정확 일치, 심지어 Write→Edit 치환 지시까지 세부 반영 ③"산출 파일이 3개를 초과하면 비중첩 파일 집합으로 분할... 이번 10파일 일괄 사례는 3파일 이하로 쪼개 재배치해야 한다"(근거 dispatch-process.md §Step 6 149~160행 항목 5) — R-3(3개 초과 분할) 정확 일치. 3요소 전부 자력 포함, 수치·절차 왜곡 0건. 워커는 막힌 지점(O1 §7.6 교차참조가 지정 3문서 범위 밖)을 정직하게 자백했고, 그 지점을 제외한 단일 워커 재시도·판정·분할 3질문은 3문서만으로 완전히 재현했다고 스스로 명시 — 이는 H-11(재현성) 목표에 부합하는 바람직한 경계 인식이다. **판정: Pass — H-11 목표달성(블라인드 재현) 확인.** S-15(캡틴 실무 타당성 판정)로 넘긴다 |

> **1회차 대비 변경 (SCENARIO-GATE-1.md G-1 반영)**: 1회차 S-13은 정답 3개와 탐색 경로를 기대결과·요청 양식에 미리 명시한 채 **TEST-SCENARIO 저자 본인**이 수행하는 구조였다 — 정답을 아는 사람이 안내된 경로를 따라가므로 "무지 상태의 다음 PM이 도달 실패하는" 실패를 원리적으로 검출할 수 없었다. 2회차는 정답 미고지 + 저자 아닌 신규 컨텍스트 워커로 바꿔 **탐색 가능성이 아닌 재현성**을 검증한다.

#### S-17: 규율의 프롬프트 도달 (교체 성립 여부)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-13 |
| 대상 | 본 태스크 EXECUTE Step 1~5의 실제 디스패치 프롬프트 |
| 계층 | L2 |
| **실행 방식** | **M2 (자동화 — 프롬프트 원문 대조)** |
| 조건 | Step 1~5 디스패치 실행 시. 프롬프트 원문을 `AGENTIC-LOG.md`에 보존한 뒤 대조한다 |
| 기대 결과 | ①Step 1~5 각 디스패치 프롬프트에 "증분 저장"·"입력 축소" 2항목이 **모두** 포함 ②문구 출처가 PM 즉흥 작문이 아님이 확인 — **Phase 3(Step 4·5)** 프롬프트는 이미 신설된 `dispatch-process.md` 주입 템플릿 인용, **Phase 1·2(Step 1~3)** 프롬프트는 템플릿 신설 이전이므로 `PLAN.md` §3.3.2 (A) 확정 문언과 동일 문구여야 한다 ③1건이라도 누락되면 Fail — 템플릿이 실제 주입 경로로 작동하지 않는다는 뜻이므로 REQ-4 설계를 재검토한다 |
| 도구 | grep / AGENTIC-LOG.md |
| 실행 명령 | `sed -n '19,37p' AGENTIC-LOG.md`(EXECUTE 디스패치 기록 표); `grep -n "3.3.2\|증분 저장\|입력 축소" PLAN.md`; `sed -n '511,527p' PLAN.md`(확정 삽입 문언과 자구 대조) |
| 결과 | Pass (단, 증거 성격 한계는 상세 참조) |
| 상세 | ①AGENTIC-LOG.md §EXECUTE 디스패치 기록 표(24~30행)에 Step 1~5 전 행이 "✅ 증분 저장 + 입력 축소"로 기재됨 — 5건 전부 포함 ②문구 출처: Phase1·2(Step1~3)는 "PLAN §3.3.2 (A) 확정 문언" 출처로 표기되었고, 실제 PLAN.md 511~527행(§3.3.2 설계 — 확정 삽입 문언)의 520~521행 텍스트("- [MUST] 증분 저장: 산출물 1개를 완결 저장한 뒤 다음 산출물로 이동한다. 말미 일괄 저장 금지. ← 전 워커 공통 고정" / "- [MUST] 입력 축소: ...")가 AGENTIC-LOG 34~36행에 기재된 "주입 문구 원문"과 자구 동일 확인. Phase3(Step4·5)는 "`dispatch-process.md` 주입 템플릿 인용(Step 3에서 신설 완료)" 출처로 표기되었고, 실제 dispatch-process.md 93~94행(S-5에서 확인한 펜스 내부 2줄)이 그 인용 대상과 동일 문구임을 이미 S-5에서 확인함 ③누락 0건 — Fail 조건 미해당. **증거 한계**: 본 판정은 EXECUTE 당시 실제 Agent 호출의 원문 프롬프트 전체 텍스트가 아니라 PM이 사후 작성한 AGENTIC-LOG 요약표에 근거한다(라이브 디스패치 텍스트는 재현 불가). 요약표와 SSOT 원문(PLAN §3.3.2, dispatch-process.md)의 자구 일치는 직접 확인했으나, "표에 기재된 그대로 실제 프롬프트에 주입되었는가"는 PM 자기보고 신뢰 구간이 일부 남는다는 점을 기록한다 |

#### S-18: 자기적용 — 신설 상한의 실사용 준수

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-14 |
| 대상 | 본 태스크 EXECUTE 배치 구성 (PLAN §4.1) |
| 계층 | L2 |
| **실행 방식** | **M2 (자동화 — 실행 기록 대조)** |
| 조건 | Step 1~5 완료 후 |
| 기대 결과 | ①실제 디스패치된 배치별 산출 파일 수가 전부 **3개 이하**(Phase1=2 / Phase2=1 / Phase3=2) ②`dispatch-process.md`를 건드리는 REQ-3·REQ-4가 **단일 디스패치에서 순차 편집**됨 ③계획(PLAN §4.1)과 실제 실행이 일치 — 불일치 시 Fail |
| 도구 | AGENTIC-LOG.md / git diff |
| 실행 명령 | `sed -n '39,45p' AGENTIC-LOG.md`(배치 구성 실측); `sed -n '658,666p' PLAN.md`(§4.1 Phase 그룹핑 계획); `git diff --stat` 6파일 |
| 결과 | Pass |
| 상세 | ①AGENTIC-LOG.md §배치 구성 실측(41~45행): Phase1=2(`opal-harness.md`,`pm-review-gate.md`)/Phase2=1(`dispatch-process.md`)/Phase3=2(`parallel-execution.md`,`op-dev-execute/SKILL.md`) — 전부 3개 이하, 계획과 완전 일치 확인 ②PLAN.md §4.1(662행) 표에 "Phase 2 \| F-002 + F-003 \| Step 3 \| 1 \| 순차 \| `dispatch-process.md` 단일 파일 2개소 순차 편집 — 분할 금지" 명시 — REQ-3(산출량 상한)·REQ-4(주입 템플릿)를 건드리는 두 요구사항이 Step 3 단일 디스패치에서 순차 편집됨을 계획·실행 양쪽에서 확인(S-3·S-5가 같은 파일에서 함께 살아있음을 이미 확인한 것과 정합) ③`git diff --stat` 결과 dispatch-process.md는 1개 파일로만 잡히고(단일 커밋 단위 diff), 계획된 배치 수(Phase 4개)·파일 수 배분이 실제 diff 구성과 일치 — 불일치 0건 |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-15: 블라인드 재현 결과의 실무 타당성 확정 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | S-13이 산출한 신규 컨텍스트 워커의 대응안 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 자동 대조는 3요소 포함 여부만 보므로, 의미 왜곡 판정은 사람이 한다 |
| 조건 | S-13 실행 완료 후. 캡틴은 워커 응답 원문을 본다 |
| 기대 결과 | 워커 대응안이 형식적으로 3요소를 담았더라도 **실무적으로 틀리지 않았는지** 캡틴이 판정한다 — 예: "1회"를 재개 총 횟수가 아닌 다른 의미로 해석했거나, 실측 판정을 워커 자기보고 신뢰로 대체했거나, 분할 기준을 입력 파일 수로 오해한 경우 Fail |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | **Pass** — 캡틴 확인 완료 (2026-08-02) |
| 상세 | opal-test-agent는 L3 [SUPERVISOR] 시나리오를 실행하지 않고 PM에 위임했다. PM이 S-13 워커 응답 원문 3요소([1] 재시도 1회·[2] git 실측 3단계·[3] 3개 초과 분할)를 캡틴에게 제시했고, **캡틴이 "S-15 통과"로 판정**했다(2026-08-02). 의미 왜곡·수치 오해·판정 근거 대체 지적 0건 — H-11(재현성) 목표달성 확정 |

> **[SUPERVISOR] PM 요청 양식**
> 캡틴, S-15 확인을 요청드립니다.
> 1. S-13에서 신규 컨텍스트 워커가 산출한 대응안 원문을 보여드리겠습니다.
> 2. 그 대응안이 **캡틴이 080에서 실제로 했던 대응**과 실질적으로 같은지 판정해주십시오.
> 3. 형식은 맞지만 의미가 어긋난 지점(수치 해석·판정 근거·분할 기준 오해)이 있으면 지목해주십시오.
> 4. 실질 동등하면 Pass, 어긋난 지점이 있으면 해당 규칙 문언을 어떻게 고칠지 지시해주십시오.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| REQ-1 AC (표 행 3컬럼) | H-1 | L1 | S-1 | `opal-harness.md`:§1 표 [T081/L1-REQ1] | TS-001 |
| REQ-1 AC (수치 유일성) | H-1, H-5 | L1 | S-1, S-8 | `opal-harness.md`:§1 [T081/L1-REQ1b] | TS-002 |
| REQ-2 AC (3단계 순서) | H-3 | L1 | S-2 | `pm-review-gate.md`:신규 절 [T081/L1-REQ2] | TS-003 |
| REQ-2 AC (덮어쓰기 금지 [MUST]) | H-3 | L1 | S-2 | `pm-review-gate.md`:신규 절 [T081/L1-REQ2b] | TS-003 |
| REQ-2 AC (수치 재서술 부재) | H-5 | L1 | S-2, S-8 | `pm-review-gate.md`:신규 절 [T081/L1-REQ2c] | TS-004 |
| REQ-3 AC (3개 초과 분할 + 잠정치) | H-4 | L1 | S-3 | `dispatch-process.md`:Step 6 [T081/L1-REQ3] | TS-005 |
| REQ-3 AC (§7.4 참조 1줄) | H-5 | L1 | S-4 | `parallel-execution.md`:§7.4 [T081/L1-REQ3b] | TS-006 |
| REQ-3 AC (앵커 타당성) | H-5 | L1 | S-4 | `opal-harness.md`:§2 모듈 표 [T081/L1-REQ3c] | TS-016 |
| REQ-4 AC (고정 2항목 주입) | H-4, H-9 | L1 | S-5 | `dispatch-process.md`:주입 템플릿 [T081/L1-REQ4] | TS-007 |
| REQ-4 AC (문언 무충돌) | H-10 | L1 | S-6 | `op-dev-execute/SKILL.md`:Step 4 [T081/L1-REQ4b] | TS-008, TS-017 |
| REQ-5 AC (변경이력 5파일) | H-8 | L1 | S-7 | 5파일:`## 변경이력` [T081/L1-REQ5] | TS-009 |
| REQ-5 AC (배포본 일치) | H-6 | L2 | S-10 | `install-mac.sh`:실행 [T081/L2-REQ5b] | TS-010 |
| REQ-6 AC (candidate 0건 / promoted 2건) | H-7 | L2 | S-11 | `.opal/MEMORY.json`:memories [T081/L2-REQ6] | TS-011 |
| 완료기준 (참조 무결성) | H-1, H-10 | L1 | S-9 | 5파일:상호 참조 [T081/L1-INTEG] | TS-013 |
| 완료기준 (Governance 유일성) | H-5 | L1 | S-8 | 저장소 전역 grep [T081/L1-GOV] | TS-014 |
| 완료기준 (회귀 무손상) | H-3 | L2 | S-12 | `test-regression.js`:077 S-21 [T081/L2-REG] | TS-012 |
| **목표 (재현성 — 블라인드)** | **H-11** | **L2** | **S-13** | 신규 컨텍스트 워커 [T081/L2-GOAL] | **목표달성 축 (2회차 재설계)** |
| **목표 (재현성 — 실무 타당성)** | **H-11** | **L3** | **S-15** | 캡틴 판정 [T081/L3-GOAL] | **2회차 신설 — 의미 왜곡 판정** |
| 앵커 이동 실효성 (SSOT 로드 조건) | H-12 | L1 | S-16 | `opal-pm.md`:§3 [T081/L1-LOAD] | **2회차 신설 — G-2 대응** |
| 교체 성립 (규율의 프롬프트 도달) | H-13 | L2 | S-17 | EXECUTE 프롬프트 원문 [T081/L2-INJECT] | **2회차 신설 — G-3 대응** |
| 실사용 채택 (자기적용 준수) | H-14 | L2 | S-18 | AGENTIC-LOG 배치 기록 [T081/L2-SELF] | **2회차 신설 — G-4 대응** |
| REQ-3 AC (임계값 단일 해석성) | H-4 | L1 | S-19 | `dispatch-process.md`:Step 6 [T081/L1-EDGE] | **2회차 신설 — G-5 대응** |
| (관측 전용) | H-2 | L1 | S-14 | `opal-pm.md`:66 [T081/L1-OBS] | TS-015, Fail 비대상 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | N/A | N/A | changed_files 6건(`opal-harness.md`/`pm-review-gate.md`/`dispatch-process.md`/`parallel-execution.md`/`op-dev-execute/SKILL.md`/`.opal/MEMORY.json`) 전부 `.md`·`.json` 문서 파일 — 코드 파일 0건, 린트 대상 없음 |
| 2 | 타입 체크 | N/A | N/A | 동일 사유 — 코드 변경 0건 |
| 3 | 포맷터 | N/A | N/A | 동일 사유 — 코드 변경 0건. 실질 대체 검증은 S-12 회귀 스위트(36 pass/0 fail, 직접 실행 확인)로 갈음 |

> 본 태스크는 코드 변경 0건(문서 트랙)이다. 1~3은 N/A 처리하되, 회귀 스위트(S-12)가 실질 대체 검증이다.

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | Pass | `git diff` 6개 changed_files의 추가(`+`)라인 전체에 `grep -iE "api[_-]?key\|secret\|password\|token\s*=\|Bearer [A-Za-z0-9]\|AKIA[0-9A-Z]{16}"` 실행 — 매치 0건 |
| 2 | .gitignore 확인 | 참고(무관) | `git status --short .gitignore`에 ` M` 표시가 있으나 diff 확인 결과 `!.opal/code-scan.json` 1줄 추가 — 본 태스크(081) changed_files에 `.gitignore`는 없으며 내용도 077/080계열 code-scan 추적 설정으로 081과 무관. 081 자체의 시크릿 제외 규칙 변경 0건 |
| 3 | 사용자 홈 실경로 노출 부재 (`~/.opal/` 표기 사용) | Pass | 동일 6파일 추가 라인에 `grep -E "/Users/[a-zA-Z0-9_]+"` 실행 — 매치 0건. 배포 경로는 전부 `~/.opal/...` 표기 사용 확인(예: `harness/pm-review-gate.md`, `pm/dispatch-process.md` 등 상대 경로 참조) |

## 7. 판정

**All Pass (캡틴 판정 반영 최종) -- S-1~S-9, S-11~S-19(18건) Pass, S-14 관측(Fail 비대상), Fail 0건.**

> **최종 판정 경위 (PM 기록)**: 아래 test-agent 원 판정은 `Partial Fail`이었다. 미충족 2건을 캡틴이 각각 처리하여 최종 `All Pass`로 확정한다.
> - **S-15**: 캡틴 수동 판정 완료 → **Pass** (블라인드 워커 대응의 실무 타당성 인정, 의미 왜곡 지적 0건).
> - **S-10**: 캡틴 결정 (a) — **AC 충족으로 Pass 처리**. 근거: REQ-5 AC는 "install 후 배포본과 소스의 규칙 문언 일치"이며 strip 기준 5/5 일치를 PM·test-agent가 각각 독립 확인했다. 시나리오 기대결과 ①"exit 0"은 PM이 작성 시 AC보다 넓게 잡은 조건으로, install 전체 성공(MCP 등록 등)은 본 태스크 완료기준 범위 밖이다. **install 전체 재실행은 캡틴이 직접 수행하기로 함** — PM은 완료분 재배포를 하지 않는다(`pm-review-gate.md` §워커 중단 시 산출물 실측 판정 ③ 준용).
> - **잔여 관측 2건**(비차단, 후속 분리): F-4 `opal-pm.md:66` "검토 11항목" stale / F-6 O1(§7.6) 교차 참조가 조건부 로드 문서를 가리켜 추적 단절(블라인드 워커 발견).

**[test-agent 원 판정 — 기록 보존]** Partial Fail -- S-1~S-9, S-11~S-13, S-16~S-19(16건) 전부 Pass(실행 출력 증거 첨부, 필요한 시나리오는 EXECUTE/PM 원 실행과 별도로 본 워커가 grep/diff/node --test/python3 파싱으로 독립 재검증), 코드 품질(§5) N/A(0 code changes, 회귀 스위트 36/36 Pass로 대체 검증), 보안(§6) Pass(시크릿·실경로 노출 0건). 다만 S-10(install 재배포)이 기대결과 ①"exit 0"을 리터럴 충족하지 못함(실측 exit 143, SIGTERM 타임아웃 — AGENTIC-LOG §Step 6에 정직히 기록됨, MCP 등록 등 본 태스크 무관 후행 단계 추정)해 Partial로 판정했고, ②③(strip diff 0줄, 본 워커 독립 재실행으로 재확인)은 충족한다. S-14는 시나리오 설계상 Fail 비대상 관측 항목(검토 11항목 stale 재확인, F-4 입력)이며, S-15는 [SUPERVISOR] 마커로 캡틴 수동 판정 대기 중(Pending)이라 자동 판정 범위 밖이다. 부가 관측: S-4/S-16에서 `opal-harness.md:102` 앵커가 S-1 자신의 §1 표 3행 삽입으로 105행으로 밀렸음을 발견(내용 판정에는 영향 없으나 §7 PM Gate 체크의 "N-1 정정 완료" 항목이 재발한 것이므로 캡틴 보고 필요). 핵심 기능(H-1~H-14 SSOT 등재·재현성·자기적용)은 전부 Pass이므로 Critical Fail은 아니나, S-10의 리터럴 미충족과 S-15 미확정으로 All Pass를 선언하지 않는다.**

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부 (S-15)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 1:N 매핑 완전 (H-1~H-14)
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 없음 — M2 의무 트리거 N/A (FE 화면·인증/인가·외부 API 연동 0건). 단 S-13·S-17·S-18은 자발적 M2 채택
- [x] **목표 커버** — TASK.md REQ-1~REQ-6 전체가 §4에 매핑되고, 목표달성 시나리오 S-13(L2 블라인드 재현)·S-15(L3 실무 타당성)가 §3에 존재
- [x] **2회차 정정 반영** — SCENARIO-GATE-2.md 잔여 결함 N-1(S-16 앵커 오기)·N-2(S-17 Phase별 출처 분기)·N-3(S-13 프롬프트 원문 보존 의무)·N-4(본 체크 stale) 정정 완료
