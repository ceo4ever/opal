# PM 검토 게이트

> 출처: opal/core/references/opal-pm.md §4
> 로드 시점: PM Gate 수행 시 / 워커 완료 수신 직후
> 역할: 워커 완료 선언 / 검토 11항목 / Pass·Fail 판정 / 문서 등록 확인 / 하네스와의 관계

---

각 단계 워커 완료 후, PM 관점에서 결과를 검토한다.

### 워커 완료 선언

워커 결과 수신 직후, Observability 선언을 수행한다 (하네스 §5 참조):

> `⚙️ 워커 완료:` {단계명} — {결과 한 줄 요약}

### 검토 절차

#### 문서 QA 검증 (PM 직접 검토)

PM Gate는 별도 QA Gate 단계를 두지 않고, 문서 QA(요구사항→설계 검토)를 PM이 직접 흡수하여 수행한다. 각 단계 산출물에 대해 아래 공통 검증 원칙 4종으로 검토한다. (검증 기준 라이브러리: `opal/skills/op-dev-qa/SKILL.md` / `opal/skills/op-task-qa/SKILL.md` — 단계별 검증 ID·QA-{단계}.md 형식 등 참조)

| 원칙 | 검토 내용 |
|------|----------|
| 완전성 | 요구사항이 빠짐없이 반영되었는가 |
| 정합성 | 이전 단계 산출물과 일치하는가 |
| 명확성 | 모호하지 않고 구체적인가 |
| 실행 가능성 | 이 산출물만으로 다음 단계를 진행할 수 있는가 |

추가로 **요구사항 누락·오해 검토**를 PM이 직접 수행한다 — 산출물이 원 요구사항(TASK.md)을 빠뜨리거나 잘못 해석한 곳이 없는지 확인한다.

> 동작 검증(TEST / TEST-SCENARIO / state-tool verify)은 본 문서 QA와 독립이며 그 실수행 주체는 별도 영역이다. PM Gate는 동작 검증 증거를 **확인**하되 그 절차를 대체하지 않는다 (검토 절차 8번 / 12번 참조).

#### self-check 질문 (PM 자문)

문서 QA 검증 시 PM은 산출물을 읽고 스스로 아래를 묻는다. 하나라도 "아니오"이면 미흡 항목으로 정리한다.

- 요구사항이 빠짐없이 반영됐나?
- 이전 단계와 일치하나?
- 모호한 곳은 없나?
- 이것만으로 다음 단계가 가능한가?

#### 표준 검토 항목

1. 관련 참조 문서가 워커에게 전달되었는가
2. 기술 스택에 맞는 MCP/스킬이 활용되었는가 (예: shadcn/ui → shadcn MCP 사용 여부)
3. `.opal/AGENT.md`의 PM 검토 기준 체크리스트 평가
4. TASK.md 요구사항과 산출물의 정합성
5. 참조 문서 내용이 산출물에 반영되었는가
6. `docs/PROJECT.md`의 프로젝트 원칙/기준에 부합하는가
7. 금지사항 위반 여부
8. EXECUTE 결과 changed_files 중 code-scan 대상 확장자 파일에 @header가 올바르게 작성되었는가
   - 확인 방법: `code-scan scan <file> --json` 실행
   - 결과 없음: @header 누락 → Fail
   - 결과 있음: module/layer/domain/description/exports 필드 존재 여부 확인 → 누락 시 Fail
   - **2소스 판정**: JSON 결과의 `_source` 필드로 유래를 구분한다 — `inline`(파일 내 인라인 @header) vs `file`/`package`/`rule`/`domain`(code-map 매니페스트 유래, 이하 통칭 "code-map 유래"). `readonly` 스코프에 속한 파일은 인라인 기록이 금지되므로 `_source`가 code-map 유래로 나오는 것이 정상이며, 이 경우를 인라인 누락으로 오판하지 않는다.
   - **합산 커버리지**: 커버리지 판정은 인라인 단독이 아니라 `code-scan validate --json` 결과의 `coverage.covered`(= `coverage.inline` + `coverage.manifest`) / `coverage.total`을 합산 기준으로 삼는다. `coverage.percent`가 목표치에 미달하면 Fail.
   - **CLOSE 진입 전 게이트**: CLOSE 단계 진입 전 `code-scan validate --changed <EXECUTE changed_files 목록> --json`을 실행해 `ok: true`(exit 0)를 확인한다. `ok: false`(exit 2, violations 존재) 시 CLOSE 진입을 보류하고 워커에게 위반 목록을 전달해 재지시한다.
     - **게이트 기준 = `newly_uncovered` 0건**: `counts.newly_uncovered`(git 기준 신규 파일 또는 HEAD 대비 헤더 회귀)가 1건이라도 있으면 `ok:false`(exit 2)로 차단한다.
     - **`pre_existing`은 비차단 보고 항목**: `counts.pre_existing`(HEAD 버전에도 애초에 헤더가 없던 기존 파일)은 `ok:true`(exit 0)에 포함되며 CLOSE 진입을 막지 않는다. 다만 `violations[]`에 `code:'uncovered', sub:'pre_existing'`으로 노출되므로 PM은 그 수·목록을 소유자 보고에 참고 정보로 남길 수 있다.
     - **근거**: 레거시 파일 소급 헤더 부여는 이 게이트의 책임 범위가 아니다 — `discover`/`scaffold`가 담당하는 별도 작업이다(본 게이트는 "이번 변경이 새 결손을 만들었는가"만 판정).
   - EXECUTE 결과에 새 domain/scope 추가 시 code-scan.json 갱신 여부도 함께 확인 (§9 참조)
9. 전문 에이전트 영역 침범 여부
   - FE 에이전트가 BE 파일을 수정하지 않았는가
   - BE 에이전트가 FE 파일을 수정하지 않았는가
   - 공통 영역(타입 정의 등) 변경 시 양쪽에 영향 분석이 되었는가
10. Batch 간 인터페이스 정합성 (BE API ↔ FE 호출 일치)
11. docs/ 무효화 체크
   - EXECUTE의 changed_files가 docs/ 문서의 내용을 무효화하지 않는가
   - 새 API 추가 → BACKEND.md 갱신 필요?
   - 새 컴포넌트 추가 → FRONTEND.md 갱신 필요?
   - 구조 변경 → ARCHITECTURE.md 갱신 필요?
   - 새 패턴 도입 → CONVENTIONS.md 갱신 필요?
   - 갱신 필요 시: PM이 직접 갱신하거나, opi 최신화를 제안
12. STATE.md 정합성 자동 검증 (state validate)
   - 실행: `~/.opal/tools/state-tool/run.sh validate tasks/{NNN}-.../`
   - 결과: violations[] 0건이면 Pass, ≥1건이면 PM Gate Fail (재작업)
   - 근거: TASK F-10 / PLAN §2.6
13. 컨벤션 자동 진단
   - **트리거 조건**: 단계 = EXECUTE이고 워커 반환 `changed_files` 중 docs/, .opal/, *.md, tasks/ 외 파일이 ≥1건 (R-6 스킵 조건의 역)
   - **영역 분할 절차**: `docs/PROJECT.md` "## 프로젝트 구성" 섹션 prefix 매칭으로 영역별 분할 — 의사코드는 `opal/core/references/pm/context-injection.md` §PROJECT.md 프로젝트 구성 기반 라우팅을 그대로 적용 (→ D-3). 매칭 실패 시 단일 호출(`scope=all`)로 폴백 (→ D-4 예시 B)
   - **호출**: 영역별로 opal-convention-checker 워커 디스패치 — 파라미터 매핑은 `opal/agents/opal-convention-checker/AGENT.md` §입력 명세 §PM Gate 호출 시나리오 표 참조 (→ D-2)
   - **호출 입력 명세**: `target_files = changed_files ∩ 영역 prefix`, `scope = 영역명` (단일 호출 시 `scope=all`), `task_folder = 현재 태스크 폴더`, `timestamp` = 영역별 분리 (병렬 호출별 고유 ts)
   - **판정 기준**:
     | 발견 이슈 심각도 | 결과 |
     |---------------|------|
     | Critical 또는 High ≥1건 | **Fail** → 워커 재지시 1회 → 미해결 시 소유자 에스컬레이션 |
     | Medium 이하만 | **Pass** + 소유자에 보고서 경로 요약 보고 |
   - **스킵 조건** (3종):
     1. `changed_files` = 0건
     2. `changed_files`가 docs/, .opal/, *.md, tasks/ 등 컨벤션 적용 외 파일만 포함
     3. `docs/CONVENTIONS.md` 부재 → 체커가 `check_enabled=false`로 자체 처리(`GC-CONVENTION-*.md` §5 "문서 작성 유도"만 작성) + PM Gate Pass
   - **하위 호환**: `.opal/AGENT.md` 미존재 시 PM Gate 자체 스킵(§판정 4번째 항목)이므로 본 §13도 동시 스킵 (→ D-1 §판정)
   - **근거**: TASK.md R-1~R-7 / `tasks/136-260508-opp-pm-gate-convention-auto-check/PLAN.md` §2 핵심 설계
14. 코드 변경 태스크의 디스패치 컨텍스트에 code-scan 결과 인용 검증
   - **트리거 조건**: `changed_files` 또는 `target`에 code-scan 지원 확장자(`.py .js .ts .vue .jsx .tsx .svelte .kt .kts .java .swift` 등) 포함 — §8/§13과 동형
   - **검증 내용**: 워커에게 전달된 디스패치 컨텍스트(PLAN.md Step 본문 또는 PM 메시지)에 code-scan 결과(`domain`/`layer`/`depends`/`exports`)가 인용되었는가
   - **신규 서브명령 인용도 대상**: `discover`/`scaffold`/`target`/`validate`/`feature` 서브명령의 결과(예: `target` 결과의 `write_to`/`reason`, `validate` 결과의 `coverage`/`counts`, `feature` 결과의 교차 스코프 목록)도 인용 대상에 포함한다 — `domain`/`layer`/`depends`/`exports` 인용과 동등하게 취급.
   - **적용 범위**: 코드 변경/탐색 태스크 한정. 순수 .md 문서·기획·정책만인 문서 작업은 **N/A(스킵)**.
   - **판정**: 인용 부재 시 **Fail** → 재디스패치 1회 (code-scan 결과 인용 추가 후 재시작)
   - **Pass 조건**: 디스패치 컨텍스트에 code-scan 결과 표(domain/layer/depends/exports 중 1개 이상, 또는 신규 서브명령 결과 필드 1개 이상) 또는 명시적 인용문 존재

### 자가 진단 (PM Gate 진입 전 체크)

1. 파이프라인 현황판 행 상태가 state-tool로만 갱신되었는가 (LLM 직접 편집 0건)
2. 각 Gate 직후 State Gate 행이 즉시 ✅ 처리되었는가
3. CLOSE 진입 게이트 통과 확인 — CLOSE 단계 첫 행 mark 시 prev_user_row(owner=user, status=done)가 존재하는가
   - 미통과 시 도구가 `close_gate_violation`으로 거부함 — 사용자 확인 행 먼저 처리 필요
   - 근거: PLAN §2.16 G-13
4. 최근 24시간 의사결정 로그에 `--force` 사용 0건 확인
   - 누적 발생 시 별도 태스크로 우회 제한 정책 재설계 필요
   - 근거: PLAN §2.17 트리거 #1/#3/#8 / R-11

### PM Gate 통과 후 단일 mark

PM Gate 통과 후 해당 행을 state-tool로 단일 mark한다. State Gate 행·QA Gate 행은 Phase4 완료로 제거되어 4행 패턴이 성립하지 않는다.

```
~/.opal/tools/state-tool/run.sh mark tasks/{NNN}-.../ --row <PM Gate 행 번호> --done
```

> [deprecated] gate-pass — 레거시 전용. State Gate/QA Gate 행이 제거되어 4행 패턴이 성립하지 않음. 신규 태스크는 위 단일 mark 사용. (Phase4 완료)
- 근거: PLAN §2.13 G-10 / R-10 (gate-pass deprecated, Phase4 완료)

### 판정

- **Pass**: 소유자에게 보고
- **Fail**: 워커에게 재지시 (최대 1회) → 재검토 → 보고
- **Fail (영역 침범/인터페이스 불일치)**: 해당 전문 에이전트에 재지시 (최대 1회)
- **`.opal/AGENT.md` 미존재 시**: PM 검토를 스킵하고 기존 흐름대로 진행 (하위 호환)

### 하네스와의 관계

하네스 interactive §3 PM Gate가 "PM 검토를 수행하라"고 지시하면, 이 §4의 절차를 따른다. 하네스는 게이트 구조(언제)를, 이 문서는 검토 내용(무엇을 어떻게)을 정의한다.

### 문서 등록 확인

작업 완료 후 새 문서가 `docs/` 하위에 생성된 경우:
1. 소유자에게 확인: "이 문서를 프로젝트 문서로 등록할까요?"
2. 소유자 승인 시 → 용도 인터뷰 → `docs/PROJECT.md` 문서 테이블에 등록

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 다운사이징 — opal-pm.md §4 분리 (128) |
| v1.1 | 2026-05-01 | 검토 절차 12번 `state validate` 추가 + 자가 진단 섹션(force 사용 0건 확인 R-11 / CLOSE 게이트 close_gate_violation §2.16 G-13) + gate-pass 일괄 처리 절차 추가 §2.13 G-10 (134) |
| v1.2 | 2026-05-08 | 검토 절차 13번 `컨벤션 자동 진단` 신설 — 트리거/영역 분할/호출/입력 명세/판정/스킵 3종/하위 호환 7개 소절 (136) |
| v1.3 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — "캡틴 에스컬레이션" / "캡틴에 보고" → "소유자 에스컬레이션" / "소유자에 보고" 치환 (139) |
| v1.4 | 2026-06-07 | gate-pass deprecated 정합 — "Gate 통과 일괄 처리(gate-pass)" 절을 "PM Gate 통과 후 단일 mark"로 교체. 4행 패턴 권장 제거, [deprecated] gate-pass 레거시 안내 추가. Phase4 완료 반영 (014 Phase 4) |
| v1.4 | 2026-06-07 | QA 문서검증을 PM Gate로 통합 — 공통 검증 원칙 4종 + 요구사항 누락·오해 검토 + self-check 흡수 (014) |
| v1.5 | 2026-06-11 22:38 | 표준 검토 항목 14번 신설 — 코드 변경 태스크 디스패치 컨텍스트 code-scan 결과 인용 검증 (문서 작업 N/A) (010) |
| v1.6 | 2026-07-28 15:10 | 표준 검토 항목 8번 — 2소스 판정(`_source` inline vs code-map 유래, readonly 스코프 예외) + 합산 커버리지(`coverage.covered`/`coverage.percent`) + CLOSE 진입 전 `validate --changed` 게이트 절차 추가. 14번 — `discover`/`scaffold`/`target`/`validate`/`feature` 신규 서브명령 결과도 인용 대상임을 반영 (077) |
| v1.7 | 2026-07-28 23:28 | 표준 검토 항목 8번 CLOSE 게이트 — `uncovered` 2분류(`newly_uncovered`/`pre_existing`) 반영: 게이트 기준을 "violations 0건"에서 "`counts.newly_uncovered` 0건"으로 명확화, `pre_existing`은 비차단 보고 항목(레거시 소급 부여는 discover/scaffold 몫)임을 명시 — Step 19 검증에서 자체 저장소 레거시 파일이 게이트를 막던 결함 재작업 (077) |
