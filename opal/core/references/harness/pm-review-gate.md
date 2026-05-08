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
     | Critical 또는 High ≥1건 | **Fail** → 워커 재지시 1회 → 미해결 시 캡틴 에스컬레이션 |
     | Medium 이하만 | **Pass** + 캡틴에 보고서 경로 요약 보고 |
   - **스킵 조건** (3종):
     1. `changed_files` = 0건
     2. `changed_files`가 docs/, .opal/, *.md, tasks/ 등 컨벤션 적용 외 파일만 포함
     3. `docs/CONVENTIONS.md` 부재 → 체커가 `check_enabled=false`로 자체 처리(`GC-CONVENTION-*.md` §5 "문서 작성 유도"만 작성) + PM Gate Pass
   - **하위 호환**: `.opal/AGENT.md` 미존재 시 PM Gate 자체 스킵(§판정 4번째 항목)이므로 본 §13도 동시 스킵 (→ D-1 §판정)
   - **근거**: TASK.md R-1~R-7 / `tasks/136-260508-opp-pm-gate-convention-auto-check/PLAN.md` §2 핵심 설계

### 자가 진단 (PM Gate 진입 전 체크)

1. 파이프라인 현황판 행 상태가 state-tool로만 갱신되었는가 (LLM 직접 편집 0건)
2. 각 Gate 직후 State Gate 행이 즉시 ✅ 처리되었는가
3. CLOSE 진입 게이트 통과 확인 — CLOSE 단계 첫 행 mark 시 prev_user_row(owner=user, status=done)가 존재하는가
   - 미통과 시 도구가 `close_gate_violation`으로 거부함 — 사용자 확인 행 먼저 처리 필요
   - 근거: PLAN §2.16 G-13
4. 최근 24시간 의사결정 로그에 `--force` 사용 0건 확인
   - 누적 발생 시 별도 태스크로 우회 제한 정책 재설계 필요
   - 근거: PLAN §2.17 트리거 #1/#3/#8 / R-11

### Gate 통과 일괄 처리 (gate-pass)

표준 단계 행 구성(QA Gate → State Gate → PM Gate → State Gate 4행 연속)에서 PM이 `gate-pass` 1회 호출로 4행 일괄 ✅ 처리한다.

```
~/.opal/tools/state-tool/run.sh gate-pass tasks/{NNN}-.../ --start <QA Gate 행 번호>
```

- 적용 조건: 4행이 정확히 `["QA Gate", "State Gate", "PM Gate", "State Gate"]` 패턴이고 동일 stage인 경우
- 비표준 행 구성(opsdd/oppd 등): `gate_pattern_mismatch` / `gate_stage_mixed` 거부 → `mark` 4회 개별 호출 사용
- 근거: PLAN §2.13 G-10 / R-10

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
