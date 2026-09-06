# PLAN: 근거 등급층 신설 + 확정/미확정 판정 + 트랙 자동 강등

> 작성일: 2026-08-21 | 입력: TASK.md (ANALYSIS.md 없음 — opds 트랙, 코드 분석 직접 수행)
> 모드: Multi-Feature (F-001~F-005)

## 결론

- **U-1 = 신설**: `verify --evidence-check`를 별 플래그로 신설하고, 표 위치·헤더 탐색만 공통 하위함수로 추출해 재사용한다 — 기존 게이트는 차단형(`state_tool.py:2364` `err()`)이고 신규는 라우터형(항상 exit 0)이라 반환 계약이 양립하지 않는다.
- **U-2 = `의존 사실` 열 재정의 (열 추가 없음)**: 열 수가 불변이라 레거시 파싱이 무변경이고, 이미 있는 빈 슬롯에 집행을 붙이는 것이 새 열을 또 방치하는 것보다 실패모드가 적다.
- **U-3 = 4축 AND + 파일 수 상한 9(잠정치)·확정률 하한 90%**: 실측상 확정률·파일 수 어느 축도 단독으로 opd/opds를 가르지 못해(아래 §3 F-004) 전건 충족(AND)만 강등한다.
- **U-4 = `opal/core/references/harness/track-routing.md` 신설**: `opal-pm.md` §12는 PM 역할 전환 축(`opal-pm.md:140-200`)이지 트랙 축이 아니고, 강등 규칙을 두 오케스트레이터가 공유하므로 SSOT 파일이 필요하다.
- **U-5 = `citation-rules.md` §9 신설, §8.6 무접촉**: §8은 적용 대상이 기획 산출물·brain term 페이지로 한정되고(`citation-rules.md:330-341`) §8.6은 "병기 대상 선정" 축이라, 전 트랙 적용인 "충돌 서열" 축을 그 하위에 두면 적용 범위가 좁아진다.
- **리스크 최대치**: 에러 코드 1종 추가가 `TestErrorCodesCompleteness` 3개 테스트(카운트·목록·README 종수 대조)를 동시에 깬다 — 갱신 계획을 Step 6에 명시했다.
- **RED-first**: 하이브리드 — F-003(state-tool)만 RED-first 강제, F-001·002·004·005(문서)는 구현 후 검증.
- **에스컬레이션 후보**: 변경 파일 14개로 `opal-pilot-dev-short/SKILL.md:255` 승격 임계(10개)를 초과한다 — PM 판단 필요(§9 R-1).
- **분량 초과 사유**: 540줄 — 5기능·9Step·복잡 모드에서 `op-dev-plan/SKILL.md` §1~§9 골격(기능별 §2·§3 반복 + Step당 10필드 + §5 QA 매트릭스 + §8.3 참조 테이블)이 요구하는 최소 골격만으로 약 400줄이 소요되며, 중복 표(§3.N.1)·코드블록·산문은 이미 제거했다 — 골격 자체의 경량화는 R-7 대상이다.

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

산출물 근거에 등급·관할 체계를 신설하고, 확정/미확정 판정 4축을 state-tool이 집행하게 하며, 확정률 기반 `opd`→`opds` 하향 강등을 배선한다. 새 개념을 만들지 않고 이미 있는 빈 슬롯(`의존 사실` 열)에 집행을 붙인다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 근거 등급·관할 규정 신설 + 인용 의무 자기모순 해소 | R-1, R-2, R-7(a) | P0 | 없음 |
| F-002 | TASK.md 템플릿 확정/미확정 스키마 | R-3 | P0 | F-001 |
| F-003 | state-tool 근거 판정 집행(도구 4축) | R-4 | P0 | F-002 |
| F-004 | 트랙 판정·강등 배선 | R-5 | P1 | F-003 |
| F-005 | 확정 입력 소비 규약 + 산출물 형식 경량화 | R-6, R-7(b)(c) | P1 | F-001 |

### 1.3 기능 의존 그래프

```
F-001 ─┬─ F-002 ─ F-003 ─ F-004
       └─ F-005
```

---

## 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-003 신규 판정 | 레거시 태스크 001~097 TASK.md가 신 스키마 부재로 전건 미확정 판정 | P0 | L1 + L2(레거시 실파일) | S 후보: 레거시 TASK.md 입력 → `skipped` |
| H-2 | F-003 `cmd_verify` | `--clarification-check` 거부 동작(`clarification_gate_unmet`)·`--auto-pass` 우회 불가 불변 | P0 | L1 회귀 | S 후보: 기존 12건 전건 PASS 재확인 |
| H-3 | F-003 등급 매핑 | 경로 패턴→등급이 빌드 관습 의존 — 미매칭 처리 계약 | P1 | L1 | S 후보: 미매칭 경로 → `unknown` 반환 |
| H-4 | F-004 강등 라우터 | 강등(`opd`→`opds`)과 승격(`opds`→`opd`)의 상호 트리거 왕복 | P1 | L1(문서 정합 검사) | S 후보: 임계 상호배타 + 판정 시점 분리 검증 |
| H-5 | F-001 §5 개정 | "추론 기반 인용 생략 허용"에 의존하는 하류 규칙 | P2 | L1 | 실측: 의존자 **0건**(`grep -rn "인용 생략" opal/ docs/` → citation-rules.md 자기 외 무매칭) |
| H-6 | F-001 §9 배치 | `§8.6`·`opal-pm.md §7`·`harness/doc-code-mismatch.md`와 중복 서술 | P2 | L1(문서 검사) | S 후보: 중복 서술 0건 + 포인터 존재 |
| H-7 | F-005 경량화 | 검증 자산(시나리오 건수·목표-커버 게이트·evaluator) 축소 = 확정 방향 §13 위반 | P0 | L1(diff 검사) | S 후보: 축소 diff 0건 역검증 |
| H-8 | F-003 리팩터 | `_parse_clarification_table`(`state_tool.py:2225`) 공통 하위함수 추출이 dict 반환 계약을 변형 | P0 | L1 회귀 | S 후보: `TestClarificationGate` 12건 무수정 통과 |
| H-9 | F-003 인자 추가 | `TestClarificationGate._call_clarification_verify`가 고정 필드 `SimpleNamespace`를 넘겨(`test_state_tool.py:3936-3946`) 신 속성 부재 시 AttributeError | P0 | L1 | S 후보: `getattr(args,"evidence_check",False)` 기본값 경로 |
| H-10 | F-003 에러 코드 | `test_error_codes_count`(44 고정)·`test_all_28_codes_registered`·`test_s7...`(README 종수 대조, `:2528`) 동시 파괴 | P0 | L1 | S 후보: 45종 동기 + README 헤더 정정 |
| H-11 | F-003 등급 범위 | 도구 자동 부여가 E2/E4/E5로 한정되어 E1·E3이 상시 `unknown` → ③축 실효 저하 | P1 | L1 + PM 판정 | S 후보: E1·E3 인용의 `unknown` 반환 및 PM 위임 명시 |
| H-12 | F-004 문서 신설 | 승격 규칙(`opal-pilot-dev-short/SKILL.md:250-259`) 미이관으로 임계값이 2문서 분산 | P2 | L1(문서 검사) | S 후보: 신설 문서가 승격 규칙을 복제하지 않고 포인터만 보유 |
| H-13 | F-003 인용 파싱 | 정규 인용 4형식 중 미파싱 형식이 `citation_path_not_found`로 오강등 — 규정 준수 산출물이 미확정으로 강등되는 과잉 차단 | P0 | L1 + L2(실파일) | S 후보: 정규 형식 변형 통과 + 본 태스크 TASK.md 실파일 판정 |

---

## 2. 기능별 분석

### 2.1 관련 파일 맵 (전 기능 통합)

| F | 영역 | 경로 | 역할 | 변경 유형 |
|---|------|------|------|----------|
| F-001 | 가이드 | `opal/core/references/harness/citation-rules.md` | 인용 규칙 SSOT (426줄) | 수정 |
| F-002 | 스킬 | `opal/skills/op-task/SKILL.md` | TASK.md 템플릿·체크리스트 SSOT (280줄) | 수정 |
| F-003 | BE | `opal/tools/state-tool/state_tool.py` | 판정 구현 (2618줄) | 수정 |
| F-003 | 문서 | `opal/tools/state-tool/README.md` | 에러 코드 카탈로그 (363줄) | 수정 |
| F-003 | BE | `opal/tools/state-tool/tests/test_state_tool.py` | 회귀·RED (8353줄) | 수정 |
| F-004 | 가이드 | `opal/core/references/harness/track-routing.md` | 트랙 판정 규칙 SSOT | **신규** |
| F-004 | 가이드 | `opal/core/references/opal-harness.md` | §2 모듈 매핑 표 (`:101-111`) | 수정 |
| F-004 | 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | 진입 절차 — 강등 호출 지점 | 수정 (097 커밋 후) |
| F-004 | 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 승격 규칙 보유 — 포인터 상호 기재 | 수정 (097 커밋 후) |
| F-005 | 스킬 | `opal/skills/op-dev-analysis/SKILL.md` | ANALYSIS 입력 처리 절 (178줄) | 수정 |
| F-005 | 스킬 | `opal/skills/op-dev-plan/SKILL.md` | PLAN 입력 분기·출력 형식 (450줄) | 수정 |
| F-005 | 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | PLAN 골격 SSOT (463줄) | 수정 |
| 문서 | 문서 | `docs/PROJECT.md` | 문서 레지스트리·주요 컴포넌트 | 수정 |
| 문서 | 문서 | `docs/CONVENTIONS.md` | §Citation Rules 포인터 | 수정 |

### 2.2 현재 구현 (F별)

**F-001 — `citation-rules.md`**
- §0(`:11`) "상상·추정·기억 기반 기재 금지"와 §5 첫 항목(`:238`) "추론/경험 기반 결정은 인용 생략 허용"이 정면 충돌한다.
- §4 표 TASK 행(`:225`)의 인라인 인용 의무가 "선택"이며 사실 주장과 결정을 구분하지 않는다.
- 등급·서열 규정은 0건이고 §1.5(`:38-49`)는 유형별 필수/선택 매트릭스일 뿐 권위 서열이 아니다.
- §8.6(`:370-380`)은 brain term `sources` 다층 병기 규칙이며 적용 대상이 §8.1(`:330-335`) 기획 산출물로 한정된다.

**F-002 — `op-task/SKILL.md`**
- `## 명확화 결과` 표는 `요소 | 확정값 | 미확정(있으면) | 의존 사실` 4열이다(`:138`).
- `## 확정된 설계 방향` 절(`:129`, `:85-87`)은 항목 태그 규약 없이 자유 서술이다.
- 작성 체크리스트 마지막 항목(`:256`)이 4요소 잠금만 검사한다.

**F-003 — `state_tool.py`**
- `_parse_clarification_table`(`:2225`)은 `확정값` 열 인덱스만 식별하고 `의존 사실` 열은 파싱하지 않는다.
- `_check_clarification_gate`(`:2299`)는 확정값 셀의 공란/TBD/`-`만 검사하고 섹션·표 부재 시 `None`으로 graceful skip을 신호한다.
- `cmd_verify`(`:2322`)는 플래그별 조기 반환 4분기(`clarification_check` → `fix_mode` → 시나리오 → `red_check`) 구조다.
- `ERROR_CODES`는 44종이고 README 헤더가 "(44종 실측 SSOT"로 동기되어 있다(`README.md:281`).

**F-004 — 트랙 라우팅**
- 승격 규칙은 조기(요구사항 ≥8개)·PLAN 결과(파일 ≥10개) 2시점으로 이미 존재한다(`opal-pilot-dev-short/SKILL.md:239-259`).
- `opal-pilot-dev/SKILL.md` 420줄에 강등 규칙은 0건이며 진입부는 하네스 Read·모드 판별로 시작한다(`:10-21`).
- `install_opal_references()`가 `opal/core/references/`를 `cp -Rf`로 통째 배포하므로 신설 파일은 install 변경 없이 배포된다(`scripts/install-mac.sh:1567-1580`).

**F-005 — ANALYSIS·PLAN 스킬**
- `op-dev-plan/SKILL.md:39-49` "입력 분기" 절은 분석 깊이만 조절하고 TASK.md 확정 항목을 입력으로 다루지 않는다.
- `plan-guide.md` 3단계는 "클래스/함수 시그니처와 핵심 로직"까지만 규정하고 원문 붙여넣기를 금지하지 않는다.
- PLAN.md 출력 형식(`op-dev-plan/SKILL.md:155-347`)에 상단 결론 집약 블록이 없다.

### 2.3 영향 범위

- **F-001**: 10개 pilot SKILL·`plan-guide.md`가 §2·§3.1·§3.2를 참조하나 §5 인용 생략 조항에 의존하는 규칙은 **0건**(H-5 실측: `grep -rn "인용 생략" opal/ docs/` → citation-rules.md 자기 외 무매칭). `docs/CONVENTIONS.md:218-222`가 이 문서를 근거로 가리킨다.
- **F-002**: `tasks/` 19개 TASK.md 중 18개가 `## 확정된 설계 방향`을 보유하나 `## 미확정 사항`은 4개뿐이다 — 확정률 분모가 대부분 확정 항목만으로 구성된다. `_parse_clarification_table`이 이 표의 유일 소비자다.
- **F-003**: `TestClarificationGate`(`test_state_tool.py:3910`) 12건이 `cmd_verify`를 직접 호출하고, `TestErrorCodesCompleteness`(`:2421`) 3건이 종수·목록·README 헤더를 고정한다. `_maybe_check_clarification_gate`(`state_tool.py:2140-2157`)가 `advance`/`mark` 자동 훅에서 같은 파서를 호출한다.
- **F-004**: 확정률 실측 — opds 081·085·095·097 = 100%, 082 = 71%, 083 = 61%; opd 091·093·094 = 100%. 파일 수 실측 — opds PLAN 변경 계획 행 7~37 vs opd 15~105로 분포가 겹친다. **두 축 모두 단독으로 트랙을 가르지 못하므로 4축 AND가 유일하게 방어 가능한 결합이다.**
- **F-005**: 검증 자산 소유 문서(`harness/scenario-gate.md`·`harness/red-first.md`·`op-dev-test-scenario/`)는 무접촉이어야 한다(H-7).

## 3. 기능별 설계

### F-001: 근거 등급·관할 규정 신설

#### 3.1.1 파일 변경 계획
§2.1 파일 맵의 F-001 행과 동일하다 (중복 표 제거 — R-7 자기적용).

#### 3.1.2 설계 결정
- **§9 신설(§8.9 다음, 변경이력 앞)** — E1~E5 정의 표 + AS-IS/TO-BE 관할 2축 표 + 충돌 해소 규칙 + 등급 외 목록 4종. (→ TASK.md §확정 방향 §1·§2·§3)
- **[MUST] §9 등급 외 목록**: 빌드 산출물·고아 화석·기억·추정은 근거로 인정하지 않는다. (→ 확정 방향 §1)
- **관할 2축**: AS-IS 서열은 E1>E2>E3>E4>E5, TO-BE 서열은 정책·요구사항 문서 > 설계 문서 > 소스코드(최하위). (→ 확정 방향 §2)
- **E5 단독 금지**: brain·code-map은 원천 포인터이므로 E1~E4 동반 인용을 강제한다 — 근거는 `opal-pm.md` §13이 brain을 "stale 가능 스냅샷"으로 규정한 점. (→ D-9)
- **§8.6 경계 1줄(§9 안에 기재, §8.6 무접촉)**: "§8.6은 병기 *대상 선정*, §9는 병기된 원천 간 *충돌 해소* — §8.6으로 병기한 각 원천에 §9 등급을 부여한다." (H-6 대응)
- **§0 개정**: `[MUST]` 문장에 "사실 주장"과 "결정(권한 행사)"의 구분 1줄 추가 — 결정은 등급 판정 대상이 아니다. (→ 확정 방향 §5)
- **§4 표 TASK 행 개정**: 인라인 인용 열을 "선택"에서 "**사실 주장 필수 / 결정 선택**"으로 상향. (→ R-2 AC(b))
- **§5 개정**: "추론/경험 기반 결정" 항목을 "결정(권한 행사)은 인용 생략 허용 / 사실 주장은 생략 불허"로 분리 — 의존자 0건이므로 파급 없음. (H-5)
- **§2.2 개정(R-7(a))**: 코드 근거 절에 "산출물에 소스코드 원문 블록 기재 금지, `경로:줄번호` + 필요 시 1~3줄 약식 발췌" 규칙 추가.

#### 3.1.3~4 환경/배치: 해당 없음 (install 재배포는 CLOSE 공통 절차).

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC(a)(b)(c)(d) | 산출물 검사 | §9에 E1~E5 각 1행 이상 + 2축 표("소스코드는 TO-BE 최하위" 문장 포함) + 충돌 규칙 + §8.6 경계 1줄 존재 |
| TS-002 | R-2 AC(a)(b)(c) | 산출물 검사 | §5에 사실/결정 분리 존재, §4 TASK 행이 사실 주장 "필수", §0·§4·§5 상호 모순 0건 |
| TS-003 | R-7 AC(a) | 산출물 검사 | §2.2에 원문 블록 금지 + `경로:줄번호` 대체 규정 존재 |

### F-002: TASK.md 템플릿 확정/미확정 스키마

#### 3.2.1 파일 변경 계획
§2.1 파일 맵의 F-002 행과 동일하다 (중복 표 제거 — R-7 자기적용).

#### 3.2.2 설계 결정
- **`## 확정된 설계 방향` 항목 접두 태그 `[결정]`/`[사실]` 의무화** — 표 열이 아니라 항목 접두로 두는 이유는 항목이 리스트 형태이고 열 추가 없이 파싱 가능하기 때문이다. (→ 확정 방향 §5)
- **[MUST] `## 명확화 결과` 표는 열을 추가하지 않는다 (U-2 판정)** — `의존 사실` 열의 규약을 "해당 행 확정값 안의 *사실 주장*에 대한 근거 인용(`경로:줄번호` 또는 `경로 §N`)"으로 재정의한다.
- **`-` 허용 조건 명시**: 해당 행 확정값이 순수 `[결정]`(사실 주장 0건)일 때만 `-` 허용, 사실 주장이 있으면 `-` 금지.
- **레거시 비소급 1줄**: 001~097 TASK.md는 소급 변경하지 않는다. (→ R-3 AC(d), `citation-rules.md` §5 레거시 호환 상속)
- **체크리스트 2항 추가**: `[결정]`/`[사실]` 태그 부여 여부, `의존 사실` 열 규약 충족 여부.

#### 3.2.3~4 환경/배치: 해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R-3 AC(a)(b)(c)(d) | 산출물 검사 | 템플릿에 태그 요구·`의존 사실` 재정의·`-` 허용 조건·레거시 비소급이 각 1줄 이상 존재하고 체크리스트 2항 추가됨 |
| TS-005 | R-3 AC(b) 역검증 | 회귀 테스트 | 템플릿 `## 명확화 결과` 표의 열 수가 4로 불변 |

### F-003: state-tool 근거 판정 집행

#### 3.3.1 파일 변경 계획
§2.1 파일 맵의 F-003 행과 동일하다 (중복 표 제거 — R-7 자기적용).

#### 3.3.2 설계 결정 (공개 계약만)
- **U-1 판정 = 신설**: `verify <task-path> --evidence-check [--task-md PATH]`. 근거 — `--clarification-check`는 미충족 시 `err(command,"clarification_gate_unmet",...)`로 exit 1 하는 차단기이고(`state_tool.py:2364`), 신규는 미충족을 반환값에 담아 항상 exit 0 하는 라우터다. 같은 플래그에 얹으면 `TestClarificationGate` 12건의 반환 계약이 변한다.
- **코드 재사용 경계 (U-1 후속)**: 신규 `_locate_clarification_table(lines) -> (section_lines, header_cells, header_idx) | None`을 **추출**하고, `_parse_clarification_table`은 이를 호출하는 얇은 래퍼로 만들어 dict 반환 계약을 그대로 유지한다. 셀 해석·등급 부여·판정은 신규 함수로 분리한다 — 표 탐색만 공유, 판정은 비공유. (H-8)
- **[MUST] `_check_clarification_gate`의 반환 계약(`missing[]` / `None` graceful skip)과 `_maybe_check_clarification_gate` 자동 훅 경로는 무접촉이다.** (→ TASK.md §제약 "기존 게이트 불변")
- **신규 함수 3종 시그니처**: `_extract_citations(cell) -> list[str]` / `_grade_citation(raw) -> ("E2"|"E4"|"E5"|"unknown", exists: bool | None)` / `_check_evidence_gate(task_md_path) -> dict | None`(`None` = 섹션/표/열 부재 graceful skip).
- **[MUST] 추출 단위는 인라인 코드 스팬(백틱)과 마크다운 링크로 한정한다** — 백틱 밖 산문·괄호 주석은 경로 후보가 아니다. 따라서 `` `state_tool.py:2225`(`_parse_clarification_table`) `` 는 앞 스팬만, `` `.opal/MEMORY.json` history 096 항목 `` 는 백틱 안 경로만 취한다.
- **인용 형식별 파싱 계약** (`citation-rules.md` 정규 4형식 기준):

| # | 형식 | 근거 | 파싱 | 경로 추출 | `exists` 판정 | 등급 |
|---|------|------|------|----------|--------------|------|
| ① | `` `경로:N` `` / `` `경로:N-M` `` | `citation-rules.md:76-95` (§2.2) | 대상 | 콜론 앞 | 파일 존재 **AND** N ≤ 파일 총 줄수 | 경로 패턴 매핑 |
| ② | `` `경로` §N {섹션명} `` | `:57-66` (§2.1) | 대상 | 백틱 스팬 전체 | **파일 존재만** — §N 유효성은 미검사(PM ⑥ 소관) | 경로 패턴 매핑 |
| ③ | `[사이트명](URL)` | `:97-110` (§2.3) | 대상 | URL(경로 아님) | `None` — **네트워크 접근 금지** | `unknown` |
| ④ | `(→ D-N §N)` | `:200-218` (§3.2) | **비대상** | 없음 | `None` | `unknown` |

- **[MUST] ④ 단축 참조는 도구가 해석하지 않는다** — 참조 문서 테이블 역참조 인프라를 신설하지 않는다(PRINCIPLES §2). 단축 참조만 있는 셀은 `citation_missing`이 아니라 `grade_unknown`으로 판정한다 — 차단하지 않으므로(exit 0) 규정 준수 산출물이 파이프라인을 멈추지 않는다.
- **[MUST] 디렉토리 없는 파일명 단독 토큰(`` `citation-rules.md` §2 ``)은 `unknown`으로 반환하고 저장소 탐색을 수행하지 않는다** — 실측상 `opal/` 하위에 `SKILL.md` 42건·`README.md` 23건·`pipeline.json` 10건이 존재해 파일명 단독은 구조적으로 모호하다. 판별 규칙은 "토큰에 `/`가 없으면 경로 미해석" 한 줄이다.
- **경로 해석 기준**: 프로젝트 루트 기준 상대경로로 해석하며 루트 탐색은 기존 `find_project_root`(`state_tool.py:634`)를 재사용한다 — 신규 탐색 함수를 만들지 않는다.
- **`e5_sole_citation` 오탐 방지**: ③④ 및 `unknown` 토큰은 "E5 아닌 근거"로 계수한다 — E5 토큰만 단독으로 있을 때에만 ④축 위반으로 판정한다.
- **`citation_missing` 판정 조건**: 셀에 백틱 스팬·마크다운 링크가 **0건**일 때만 부여한다(산문 단독).
- **반환 JSON 스키마**: `{ok:true, command:"verify", evidence_check:"pass"|"routed"|"skipped", items:[{element, verdict:"확정"|"미확정", reasons:[...], citations:[{raw, grade, exists}]}], confirmed_ratio: float, unconfirmed:[element]}` — exit code 항상 0.
- **미확정 사유 코드 4종(도구 4축 대응)**: `citation_missing`(①) / `citation_path_not_found`(②) / `grade_unknown`(③) / `e5_sole_citation`(④). (→ 확정 방향 §6)
- **기본 등급 패턴 세트(1차)**: `.opal/brain/**`·`.opal/code-scan.json`·`*code-map*` → E5 / `docs/**`·`*.md` → E4 / `**/tests/**`·`test_*.py` 및 코드 확장자(`.py .ts .tsx .js .sh .json`) → E2 / 그 외 → `unknown`. (→ 확정 방향 §11)
- **[MUST] E1(실행 관측)·E3(생성 코드)은 도구 자동 부여 대상이 아니다** — 경로 패턴으로 판별 불가하므로 `unknown`으로 반환한다. 프로젝트별 매핑 설정 파일을 신설하지 않는다. (H-11, [MUST] `~/.opal/PRINCIPLES.md` §2: "현재 요구사항만 해결한다. 사변적 추상화·요청되지 않은 유연성 금지.")
- **[MUST] `unknown` 등급 계상 계약 (PM 확정)**: `unknown`은 `confirmed_ratio` 계산에서 **미확정으로 계상한다**. 단 도구는 차단하지 않는다(exit 0 유지). PM이 ⑤⑥축 판단으로 해당 항목을 확정으로 승격할 수 있으며, 승격 시 근거를 산출물에 기재한다.
- **계약 근거 (1) 증거 없음 = 미완료**: 도구 축 ①~④의 목적은 PM 자기 추정을 걸러내는 것이므로 `unknown`("도구가 검증하지 못했다")을 확정으로 계수할 수 없다 — [MUST] `~/.opal/PRINCIPLES.md` §4: "Completion requires evidence: real run output or real response. No evidence → not done."
- **계약 근거 (2) 오작동 방향 고정**: `unknown`이 미확정 측이면 확정률이 내려가 A1이 미충족되고 결과가 **강등 불발**(보수적)로 수렴한다 — §9 R-5가 이미 택한 fail-safe 방향과 일관된다.
- **계약 근거 (3) 진행 차단 없음**: H-11(E1·E3 상시 `unknown` → ③축 실효 저하)은 이 계약 하에서 "강등이 덜 일어난다"로 귀결되며, PM 승격 경로가 있으므로 태스크 진행을 막지 않는다.
- **신규 에러 코드 1종**: `evidence_check_flag_conflict` — `--evidence-check`와 `--clarification-check` 동시 지정 시 거부(무성 무시 방지). ERROR_CODES 44→45.
- **[MUST] 인자 접근은 `getattr(args, "evidence_check", False)`로 한다** — 기존 테스트가 고정 필드 `SimpleNamespace`를 넘기므로 속성 부재 시 AttributeError가 난다(`test_state_tool.py:3936-3946`). (H-9)
- **분기 배치**: `cmd_verify` 안에서 `clarification_check` 분기 **뒤·`fix_mode` 앞**에 삽입한다 — 기존 조기 반환 순서를 바꾸지 않는다.

#### 3.3.3~4 환경/배치: 해당 없음 / 해당 없음 (표준 라이브러리만 사용).

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-4 AC(a) | 기능 테스트 | 신 스키마 TASK.md 입력 시 항목별 `확정`/`미확정(사유)` + `confirmed_ratio` 반환, exit 0 |
| TS-007 | R-4 AC(b) | 기능 테스트 | 존재하지 않는 경로 인용 → `citation_path_not_found`로 미확정 강등 |
| TS-008 | R-4 AC(c) | 기능 테스트 | `.opal/brain/**` 단독 인용 → `e5_sole_citation`으로 미확정 강등 |
| TS-009 | R-4 AC(d) | 기능 테스트 | 미매칭 경로 → `grade:"unknown"` 반환 (차단 아님) |
| TS-010 | R-4 AC(e) | 회귀 테스트 | `TestClarificationGate` 12건 무수정 전건 PASS + `--auto-pass` 우회 불가 유지 |
| TS-011 | R-4 AC(e) / H-1 | 회귀 테스트 | 레거시 TASK.md(`의존 사실` 열 전건 `-`) → `evidence_check:"skipped"` 또는 미확정 반환이되 exit 0 |
| TS-012 | R-4 AC(f) / H-10 | 산출물 검사 | `len(ERROR_CODES)`==45 AND README 헤더 종수==45 |
| TS-013 | R-4 신규 에러 | 기능 테스트 | 두 플래그 동시 지정 → `evidence_check_flag_conflict` exit 1 |

### F-004: 트랙 판정·강등 배선

#### 3.4.1 파일 변경 계획
§2.1 파일 맵의 F-004 행과 동일하다 (중복 표 제거 — R-7 자기적용).

#### 3.4.2 설계 결정
- **U-3 판정 = 4축 AND, 전건 충족만 강등**: 축 A1 확정률 ≥ 90% / A2 예상 변경 파일 ≤ 9 / A3 신규 개념(새 모듈·스키마·외부 의존) 0건 / A4 최고 검증 계층 ≤ L2(실환경·E2E 불요).
- **[MUST] A1 확정률 계산에서 `unknown` 등급 항목은 미확정 측(분자 제외·분모 포함)이다** — `§3.3.2` `unknown` 계상 계약을 그대로 소비하며, PM이 ⑤⑥축으로 확정 승격한 항목만 분자에 든다.
- **임계값 근거**: A1 90%는 실측 분포(opds 100%·100%·100%·100% vs 82·83의 71%·61%) 사이의 잠정 절단선이다 — opd 태스크도 100%가 다수여서 단독 판정축이 될 수 없다.
- **임계값 근거**: A2 9는 승격 임계 10과 **상호배타**가 되는 최대값이다(`opal-pilot-dev-short/SKILL.md:255`) — 두 규칙이 동시 발동할 수 없다. (H-4)
- **[MUST] A1·A2 임계값은 관측 기반 잠정치로 명시한다** — `pm/dispatch-process.md` §Step 6가 임계값 3을 잠정치로 표기한 선례를 따르고, 새 관측이 쌓이면 갱신한다.
- **재귀 차단(H-4)**: 강등 판정 시점은 **TASK 완료 직후 1회**, 승격 판정 시점은 **PLAN 결과**로 분리한다 — 시점이 다르고 임계가 상호배타이므로 왕복 구조가 성립하지 않는다.
- **fail-safe**: `## 확정된 설계 방향` 섹션 부재 또는 확정 항목 0건이면 A1 미충족으로 처리해 강등하지 않는다 — 실측상 레거시 태스크 다수가 이 상태다. (H-1)
- **강등 절차**: 캡틴 승인 왕복 없이 `opds`로 진입하고 4축 판정 결과를 사후 통보한다. (→ 확정 방향 §9, R-5 AC(c))
- **[MUST] 신설 문서는 승격 규칙을 복제하지 않는다** — 승격 임계값 SSOT는 `opal-pilot-dev-short/SKILL.md` §에스컬레이션 규칙으로 유지하고 포인터만 상호 기재한다. (H-12, R-5 AC(d))

#### 3.4.3~4 환경/배치: `install_opal_references()`가 디렉토리 전체를 복사하므로 install 스크립트 변경 없음(`scripts/install-mac.sh:1576`) / 해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-014 | R-5 AC(a) | 산출물 검사 | 신설 문서에 4축 + 임계값 표 + 잠정치 표기 존재 |
| TS-015 | R-5 AC(b) | 산출물 검사 | `opal-pilot-dev/SKILL.md` STEP 1 직후에 강등 판정 호출 지점 1건 존재 |
| TS-016 | R-5 AC(c) | 산출물 검사 | 승인 왕복 없음 + 사후 통보 문장 존재 |
| TS-017 | R-5 AC(d) / H-4·H-12 | 산출물 검사 | 강등 임계 A2(≤9)와 승격 임계(≥10)가 상호배타이고, 신설 문서에 승격 임계값 수치 복제 0건 |

### F-005: 확정 입력 소비 규약 + 형식 경량화

#### 3.5.1 파일 변경 계획
§2.1 파일 맵의 F-005 행과 동일하다 (중복 표 제거 — R-7 자기적용).

#### 3.5.2 설계 결정
- **[MUST] 재도출 금지**: TASK.md에 `[결정]` 태그 항목이 있으면 ANALYSIS·PLAN은 그 항목을 재도출하지 않고 3값 판정만 수행한다. (→ 확정 방향 §10, R-6 AC(a))
- **3값 판정 포맷**: 두 산출물 상단에 `## 확정 입력 판정` 표 — `항목 | 판정(유효/수정필요/사실오류) | 근거`. `수정필요`·`사실오류`는 근거 인용 필수. (R-6 AC(b))
- **`사실오류` 경로**: 확정 지위를 박탈하고 정상 설계 경로로 복귀 + 캡틴 보고를 산출물과 완료 보고에 동시 기재한다. (R-6 AC(c))
- **명문화 1줄**: "확정은 검증 면제가 아니라 재설계 면제다." (R-6 AC(d))
- **[MUST] 소스코드 원문 블록 금지 / 구현 코드 전사 금지**: 설계 절은 "결정 + 근거 + 변경되는 공개 계약"으로 한정한다 — 함수 시그니처·반환 스키마·에러 코드명은 허용, 함수 본문은 금지. (R-7 AC(b))
- **결론 블록 골격**: 산출물 최상단 `## 결론` — 결정·리스크 각 1~2줄, 불릿 1개 1문장, 분량 목표 초과 시 사유 1줄. (R-7 AC(c))
- **[MUST] 검증 자산 무접촉**: `harness/scenario-gate.md`·`harness/red-first.md`·`op-dev-test-scenario/` 및 시나리오 건수·목표-커버 게이트·evaluator 규정을 축소·수정하지 않는다. (→ 확정 방향 §13, R-7 AC(d))

#### 3.5.3~4 환경/배치: 해당 없음.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-018 | R-6 AC(a)(b)(c)(d) | 산출물 검사 | 두 스킬에 재도출 금지·3값 표 포맷·사실오류 경로·"재설계 면제" 문장 각 존재 |
| TS-019 | R-7 AC(b)(c) | 산출물 검사 | plan-guide 3단계에 설계 절 한정 + 결론 블록 골격 존재 |
| TS-020 | R-7 AC(d) / H-7 | 회귀 테스트 | 검증 자산 3경로의 diff 0건 (git diff --stat 실측) |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001 | 1 | opal-task-agent | 순차 | §9가 하류 참조 대상 — 선행 필수 |
| 2 | F-002, F-005 | 2, 3 | opal-task-agent | 병렬 가능 | 독립 파일 집합 (Step 3은 3파일 = 상한 준수) |
| 3 | F-003 RED | 4 | opal-test-agent | 순차 | RED-first 강제 트랙 |
| 4 | F-003 GREEN | 5, 6 | opal-be-agent | 순차 | 동일 모듈 — 같은 디스패치에 묶음(2파일) |
| 5 | F-004 | 7, 8 | opal-task-agent | 순차 | Step 7/8 분할로 산출 상한 3 준수 |
| 6 | 문서 | 9 | PM 직접 | 순차 | docs/ 갱신 |

> 산출량 상한: `pm/dispatch-process.md` §Step 6 — 단일 디스패치 산출 3파일 초과 금지. Step 3(3파일)·Step 8(2파일)로 분할 반영.

### 4.2 실행 체크리스트

> 총 9개 Step | Phase 6개 | 실행 모드: **복잡**

#### Step 1: citation-rules.md §9 신설 + §0·§2.2·§4·§5 개정
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/citation-rules.md`
- **작업 내용**: §3.1.2 설계 결정 9건 반영 + 변경이력 1행(v2.5, KST, 098)
- **완료 기준**: TS-001·TS-002·TS-003 전건 PASS
- **테스트**: TS-001, TS-002, TS-003
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: op-task/SKILL.md 템플릿·체크리스트 확장
- [x] 완료
- **소속 기능**: F-002
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-task/SKILL.md`
- **작업 내용**: §3.2.2 설계 결정 5건 반영 + 변경이력 1행
- **완료 기준**: TS-004·TS-005 PASS (표 열 수 4 불변)
- **테스트**: TS-004, TS-005
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: ANALYSIS·PLAN 확정 입력 소비 규약 + 형식 경량화
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/op-dev-analysis/SKILL.md`, `opal/skills/op-dev-plan/SKILL.md`, `opal/skills/op-dev-plan/references/plan-guide.md`
- **작업 내용**: §3.5.2 설계 결정 7건 반영 + 각 파일 변경이력 1행
- **완료 기준**: TS-018·TS-019·TS-020 PASS (검증 자산 diff 0건)
- **테스트**: TS-018, TS-019, TS-020
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 4: state-tool RED 테스트 작성 (mode: red)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-test-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py`
- **작업 내용**: TS-006~TS-013 RED 케이스 신설 + `TestErrorCodesCompleteness` 3건(카운트 45·EXPECTED_CODES·README 종수) 갱신. mock 금지, 실 파일 픽스처 + 공개 CLI 경로만.
- **완료 기준**: 신규 케이스 전건 FAIL(RED 증거 기록) + 기존 회귀 케이스 무수정
- **테스트**: RED-EVIDENCE 기록
- **실행 방법**: sub-agent
- **의존**: Step 2

#### Step 5: state_tool.py 판정 구현 (GREEN)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-be-agent
- **파일**: `opal/tools/state-tool/state_tool.py`, `opal/tools/state-tool/README.md`
- **작업 내용**: §3.3.2 공개 계약대로 하위함수 추출·신규 함수 3종·`--evidence-check` 분기·등급 패턴·에러 코드 1종 구현 + README 카탈로그 45종 정정·`verify` 절 보강·변경이력
- **완료 기준**: TS-006~TS-013 전건 PASS + 기존 회귀 전건 PASS(기준선 341 passed / 3 skipped / 84 subtests passed — **스코프: `opal/tools/state-tool/tests/` 디렉토리 전체(2파일)**, `test_state_tool.py` 단독은 324 (2026-08-21 PM 직접 실행 관측))
- **테스트**: TS-006~TS-013 + 전체 pytest
- **실행 방법**: sub-agent
- **의존**: Step 4

#### Step 6: 회귀 확인 — 기존 게이트 불변 검증
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE
- **agent**: opal-test-agent
- **파일**: `opal/tools/state-tool/tests/test_state_tool.py` (실행만, 수정 금지)
- **작업 내용**: `TestClarificationGate` 12건·`TestVerify`·`TestErrorCodesCompleteness` 실행하여 H-2·H-8·H-9·H-10 반증
- **완료 기준**: TS-010·TS-011·TS-012 PASS + 테스트 파일 수정 0건
- **테스트**: TS-010, TS-011, TS-012
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: track-routing.md 신설 + opal-harness.md 모듈 표 등재
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 가이드
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/track-routing.md`(신규), `opal/core/references/opal-harness.md`
- **작업 내용**: 4축·임계값(잠정치 표기)·강등 절차·재귀 차단·승격 포인터 작성 + 모듈 매핑 표 1행 + 변경이력
- **완료 기준**: TS-014·TS-017 PASS
- **테스트**: TS-014, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 6

#### Step 8: 오케스트레이터 2종 배선 (**097 커밋 후 편집**)
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-dev-short/SKILL.md`
- **작업 내용**: opd STEP 1 직후 강등 판정 호출 지점 배선 + opds §에스컬레이션 규칙에 포인터 1줄 + 각 변경이력 1행. **편집 전 097 커밋 완료를 `git status`로 확인한다.**
- **완료 기준**: TS-015·TS-016 PASS + 097 변경분 유실 0건
- **테스트**: TS-015, TS-016
- **실행 방법**: sub-agent
- **의존**: Step 7

#### Step 9: docs/ 갱신
- [ ] 완료
- **소속 기능**: F-001~F-005
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`, `docs/CONVENTIONS.md`
- **작업 내용**: PROJECT.md 문서 레지스트리에 `track-routing.md` 등재 + 주요 컴포넌트 절 1건 추가, CONVENTIONS.md §Citation Rules에 등급 규정 포인터 1줄 + 각 변경이력
- **완료 기준**: 신설 문서가 레지스트리에서 조회 가능하고, CONVENTIONS 포인터가 §9를 가리킴
- **테스트**: 산출물 검사
- **실행 방법**: direct
- **의존**: Step 8

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 → Step 2, 3 | §9가 두 Step의 참조 대상 — 선행 확정 필요 |
| Step 2 ∥ Step 3 | 독립 파일 집합, 상호 참조 없음 |
| Step 4 → Step 5 | RED-first 순서 (`harness/red-first.md` §1) |
| Step 5 → Step 6 | 테스트 불변성 — 구현자와 검증자 분리 (동 §2·§3) |
| Step 7 → Step 8 | 신설 문서 확정 후 포인터 배선 (역순이면 dangling 참조) |
| Step 8 → Step 9 | 최종 파일 집합 확정 후 레지스트리 등재 |

---

## 5. QA 체크리스트

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | §9 등급·2축·충돌 규칙 + §0·§4·§5 모순 해소 | TS-001, TS-002, TS-003 | 4개 AC 전건 + 모순 0건 |
| F-002 | 템플릿 스키마 확장 + 열 수 불변 | TS-004, TS-005 | 4개 AC 전건 + 열 4개 유지 |
| F-003 | 4축 판정 반환 + 기존 게이트 불변 + 카탈로그 정합 | TS-006~TS-013 | 8건 전건 PASS |
| F-004 | 4축·임계값·재귀 차단·승격 비복제 | TS-014~TS-017 | 4개 AC 전건 |
| F-005 | 재도출 금지·3값 판정·형식 경량화·자산 무접촉 | TS-018~TS-020 | 4개 AC 전건 |

### 5.2 회귀 테스트
- [ ] `TestClarificationGate` 12건 무수정 전건 PASS (H-2, H-8, H-9)
- [ ] state-tool 전체 pytest 기준선 341 passed / 3 skipped / 84 subtests passed — **스코프: `opal/tools/state-tool/tests/` 디렉토리 전체(2파일)**, `test_state_tool.py` 단독은 324 (2026-08-21 PM 직접 실행 관측) 이상 — 근거는 `python3 -m pytest opal/tools/state-tool/tests/ -q` 실행 관측이며 메모리 요약 인용이 아니다
- [ ] 레거시 TASK.md 19건 중 `의존 사실` 전건 `-` 케이스가 exit 0으로 처리됨 (H-1)
- [ ] `--auto-pass` 우회 불가 규칙 불변 (`test_case9_auto_pass_cannot_bypass`)
- [ ] 검증 자산 3경로 diff 0건 (H-7)
- [ ] 097 변경 3파일의 미커밋 변경분 유실 0건

### 5.3 코드/문서 품질
- [ ] 변경 문서 전건에 변경이력 표 1행 추가 (일시 KST + 태스크 번호 098) — [MUST] `.opal/AGENT.md` §금지사항
- [ ] `~/.opal/` 경로 직접 편집 0건 — 프로젝트 `opal/` 수정 후 install 재배포
- [ ] SSOT 중복 서술 0건 (H-6, H-12) — 포인터로 연결
- [ ] 신규 추상화·프로젝트별 설정 파일 0건 — [MUST] `~/.opal/PRINCIPLES.md` §2
- [ ] `git commit`/`push`/`reset`/`rebase` 실행 0건 (워킹트리에 남기고 보고)

### 5.4 보안
- [ ] `_grade_citation` 경로 실존 검사가 태스크 폴더 밖 절대경로·`..` 토큰을 이탈 경로로 취급하지 않는지 확인 (`_is_safe_artifact_token` 선례 참조)
- [ ] 판정 결과 JSON에 홈 디렉토리 절대경로 노출 0건 (`_redact_path_like` 선례 참조)
- [ ] 하드코딩 시크릿·토큰 0건

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 9개 | 복잡 |
| 변경 파일 수 | 14개 (신규 1 + 수정 13) | 복잡 |
| 모듈 범위 | 다중 (references / skills / tools / docs) | 복잡 |
| 작업 유형 | 대규모 개선 (규칙 신설 + 도구 확장) | 복잡 |
| 외부 의존성 | 없음 (표준 라이브러리·기존 도구) | 단순 |
| **실행 모드** | **복잡** | |

### RED-first 트랙 판정

- **F-003 = RED-first 강제**: state-tool CLI 반환 계약·판정 로직 변경은 `harness/red-first.md` §1.5 "비즈니스 로직" + "API 계약"에 해당하고 self-confirming 위험이 높다.
- **F-001·002·004·005 = 구현 후 검증 허용**: 동 §1.5 "설정·문서" 분류에 해당하며 산출물 검사(TS-001~005, 014~020)로 판정 가능하다.
- **§1.6 목표계열 선작성 = 적용됨**: PM+캡틴 페어가 PLAN 디스패치와 병렬로 Block A(TASK 유래 — 목표·R·채택/잔존) 선작성을 완료했다(TEST-SCENARIO.md 20건 — 목표달성 3 / 요구커버 7 / 채택·잔존 3 / 경계·부정 7).
- **적격 판정 근거**: `harness/red-first.md` §1.6 (f) 착수 판단표 1행(PLAN 워커 예상 소요 > 선작성 소요) + 3행(교체형 목표) 충족 — R-2가 `citation-rules.md` §5 "추론/경험 기반 결정은 인용 생략 허용" 조항을 대체하고 AC(a)가 구형 잔존 0건을 요구하므로 [MUST] `opal/skills/op-task/SKILL.md` §요구사항 작성 기준: "**교체형 목표**(구형→신형 전환·대체·마이그레이션)를 감지하면 AC에 (a)구형 잔존0 (b)신형 채택 검증 기준을 의무로 포함한다."에 해당한다.
- **Block B 보강**: PLAN 확정 후 PM이 PLAN 유래 계열(F-001~005 · H-1~H-12)을 도출 입력에 추가해 루브릭 ③기능커버·④리스크커버를 보강한다 — 동 §1.6 (b) [MUST]. 본 PLAN §3·§4·§5의 TS-001~020 목록은 PLAN 유래 검증 계약이며 Block B 보강 대상과 별개다.
- **작성자 분리 불변**: 선작성·보강 주체는 PM+캡틴 페어이고 PLAN 작성 주체(`opal-plan-agent`)와 분리 유지된다 — 동 §1.6 (c) [MUST].
- **§2 작성자≠구현자 준수**: Step 4(opal-test-agent) ≠ Step 5(opal-be-agent), Step 6 검증도 test-agent가 수행한다.

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
`B1`[S1] → `B2`[S2 ∥ S3] → `B3`[S4 test-agent] → `B4`[S5 be-agent] → `B5`[S6 test-agent] → `B6`[S7 → S8] → `B7`[S9 PM]
- 파일 충돌 방지: `test_state_tool.py`는 Step 4만 수정하고 Step 6은 실행만 한다.
- 동일 파일 다중 Step 0건 — 분할 규칙(`dispatch-process.md` §Step 6)상 묶음 강제 대상 없음.

### C-2. 스킬 요구사항
- 기존 스킬로 충족: `op-dev-execute`(문서·코드 편집), `op-dev-test`(회귀). 신규 스킬 갭 0건.

### C-3. 도구 요구사항
- `pytest`(기존), `node ~/.opal/tools/date/date.js`(변경이력 KST 일시), `git status`(097 커밋 확인). 신규 패키지·MCP 0건.

### C-4. 테스트 전략
- 기능: `python3 -m pytest opal/tools/state-tool/tests/test_state_tool.py -v`
- 회귀: 동 스위트 전체 + 기준선 341 passed / 3 skipped / 84 subtests passed — **스코프: `opal/tools/state-tool/tests/` 디렉토리 전체(2파일)**, `test_state_tool.py` 단독은 324 (2026-08-21 PM 직접 실행 관측) 대조
- 산출물 검사: TS-001~005·014~020은 grep 기반 존재·부재 판정
- 자산 무접촉: `git diff --stat -- opal/core/references/harness/scenario-gate.md opal/core/references/harness/red-first.md opal/skills/op-dev-test-scenario/`

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 규칙 문서 | Markdown SSOT (`opal/core/references/`, `opal/skills/`) | 없음 (프레임워크 자체) |
| 도구 | Python 3 표준 라이브러리 CLI + unittest/pytest | `trailofbits/modern-python` 미적용 — 표준 라이브러리 전용·기존 파일 부분 수정이므로 uv/ruff 도입 대상 아님 |
| 배포 | Bash (`scripts/install-mac.sh`) | 없음 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| 없음 | 외부 라이브러리 신규 도입 0건 — context7·shadcn 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | 인용 규칙 SSOT | `opal/core/references/harness/citation-rules.md` | R-1·R-2·R-7 주 편집 대상 (§0 `:11` / §4 `:225` / §5 `:238` / §8.6 `:370`) |
| D-2 | 소스 | state-tool 본체 | `opal/tools/state-tool/state_tool.py` | R-4 구현 대상 (`:2225` 파서 / `:2299` 게이트 / `:2322` cmd_verify / `:158` ERROR_CODES) |
| D-3 | 설계 | TASK 스킬 템플릿 | `opal/skills/op-task/SKILL.md` | R-3 편집 대상 (`:138` 표 스키마 / `:256` 체크리스트) |
| D-4 | 설계 | 판정 주체 분리 선례 | `opal/core/references/harness/scenario-gate.md` §2 | 확정 방향 §6·§7 근거 — 본 태스크는 이 패턴을 재사용하고 문서는 무접촉 |
| D-5 | 설계 | Full Task 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | R-5 배선 대상 — 강등 규칙 0건 확인 |
| D-6 | 설계 | Short Task 오케스트레이터 | `opal/skills/opal-pilot-dev-short/SKILL.md` | 승격 임계값 SSOT (`:239-259`) — 상호배타 근거 |
| D-7 | 설계 | PLAN 작성 가이드 | `opal/skills/op-dev-plan/references/plan-guide.md` | R-7 편집 대상 — PLAN 골격 SSOT |
| D-8 | 설계 | ANALYSIS·PLAN 스킬 | `opal/skills/op-dev-analysis/SKILL.md`, `opal/skills/op-dev-plan/SKILL.md` | R-6 편집 대상 — 입력 처리 절 |
| D-9 | 설계 | PM 행동 프로세스 | `opal/core/references/opal-pm.md` §12·§13 | U-4 배치 판정 근거(`:140-200`), brain stale 규정 |
| D-10 | 설계 | 헌법 | `~/.opal/PRINCIPLES.md` §2·§3 | 사변적 추상화 금지, 계획 명시 범위 한정 |
| D-11 | 설계 | 프로젝트 PM 프로필 | `.opal/AGENT.md` | 배포 경계·변경이력·하네스 우회 금지 |
| D-12 | 설계 | 도구 에러 카탈로그 | `opal/tools/state-tool/README.md` | R-4 AC(f) 등재 대상 (`:281` 헤더 종수) |
| D-13 | 설계 | RED-first 규칙 SSOT | `opal/core/references/harness/red-first.md` §1.5·§1.6·§2 | RED-first 트랙 판정 근거 |
| D-14 | 설계 | 디스패치 산출량 상한 | `opal/core/references/pm/dispatch-process.md` §Step 6 | Phase 그룹핑 3파일 상한 + 잠정치 표기 선례 |
| D-15 | 설계 | 하네스 모듈 매핑 | `opal/core/references/opal-harness.md` §2 (`:101-111`) | 신설 harness 문서 등재 의무 |
| D-16 | 소스 | 회귀 테스트 | `opal/tools/state-tool/tests/test_state_tool.py` | H-8·H-9·H-10 근거 (`:2421`, `:2528`, `:3910`, `:3936-3946`) |
| D-17 | 소스 | 배포 스크립트 | `scripts/install-mac.sh:1567-1580` | 신설 파일 자동 배포 확인 (install 변경 불요) |
| D-18 | 설계 | 프로젝트 컨벤션 | `docs/CONVENTIONS.md` §Citation Rules·§State 관리 | [MUST] 인용·state-tool 전용 규율 |

> [MUST] `docs/CONVENTIONS.md` §Citation Rules: "`[MUST]` 토큰이 붙은 항목은 인용 누락 시 산출물 부적합 처리."
> [MUST] `docs/CONVENTIONS.md` §State 관리: "파이프라인 행 상태(⬜/🔄/✅) 변경은 `~/.opal/tools/state-tool/run.sh`로만 수행한다. `state.json` 직접 편집 금지."
> [MUST] `docs/CONVENTIONS.md` §배포 경계: 프레임워크 배포 파일(`~/.opal/`) 직접 편집 금지 — 프로젝트 소스 수정 후 install 재배포.

---

## 9. 리스크 및 대응

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 변경 파일 14개가 opds 승격 임계(≥10, `opal-pilot-dev-short/SKILL.md:255`)를 초과 | 전체 | 중 | **PM 에스컬레이션 판단 필요** — 파일당 변경량이 대부분 수 줄 규모이고 모듈이 5개로 명확히 분리되므로 Phase 6분할 유지로 opds 완주 가능하다고 판단하나, 결정권은 캡틴에게 있다 |
| R-2 | 097 미커밋 3파일과 Step 8 편집 충돌 | F-004 | 중 | Step 8 진입 시 `git status`로 097 커밋 완료 확인 후 편집 (Step 8 작업 내용에 명시) |
| R-3 | 에러 코드 추가로 테스트 3건 동시 파괴 (H-10) | F-003 | 높음 | Step 4에서 45종 계약으로 선(先) 갱신 + README 헤더 동시 정정 |
| R-4 | 도구 자동 등급이 E2/E4/E5로 한정되어 ③축 실효 저하 (H-11) | F-003 | 중 | §9에 "도구 자동 부여 범위 = E2/E4/E5, E1·E3은 PM 판단" 경계를 명문화하고 관측 후 2차에서 확장 판단 |
| R-5 | 임계값 A1(90%)·A2(9)가 잠정치이며 실측이 트랙을 가르지 못함 | F-004 | 중 | 문서에 잠정치 표기 + 4축 AND(보수적)로 오작동 방향을 "강등 불발"로 고정 |
| R-6 | 형식 경량화가 검증 자산 축소로 번질 위험 (H-7) | F-005 | 높음 | 자산 3경로 diff 0건을 TS-020 회귀로 고정 + Step 3 완료 기준에 포함 |
