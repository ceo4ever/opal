---
name: opal-action-status
description: |
  **루프 액션 에이전트 진행 현황 발동층 — 자동 탐지 + 해석 보고**.
  반드시 이 스킬을 사용해야 하는 상황: "opal-action-status", "opas", "액션 에이전트 현황", "루프 진행 상황".
alias: opas
triggers:
  - "^opas$"
  - "^opal-action-status$"
  - "(?i)(액션\\s*에이전트\\s*현황|루프\\s*진행\\s*상황|모니터\\s*현황)"
version: "1.0"
domain: dev
---

# opal-action-status (루프 액션 에이전트 진행 현황)

## 1. 실행 컨텍스트

- 오케스트레이터(PM)가 **직접 수행**한다. 워커 디스패치·파이프라인 없음(operator 스킬).
- **읽기 전용** — 도구 호출 + 해석 보고만 수행한다. 파일 쓰기·state 변경은 0이다.

## 2. 프로세스

인자 파싱 → 도구 호출 → backlog 결합 → 해석 보고 → 라이브 안내, 5단계 순차로 진행한다.

1. **인자 파싱**: `//opas [태스크폴더]` — 인자가 있으면 그 폴더를 대상으로 하고, 없으면 아래 "자동 탐지" 절차를 따른다.
2. **`opal-action-monitor --json` 호출**: `~/.opal/tools/opal-action-monitor/run.sh <task_folder> --json`을 절대경로로 호출한다. `ok:false`면 "5. 에러 경로"로 이동한다.
3. **backlog 결합(존재 시)**: 대상 태스크의 상위(loop 루트)에 `backlog.json`이 있으면 `~/.opal/tools/backlog-tool/run.sh show <loop-root>`를 호출해 루프 전체 뷰를 결합한다. `backlog.json`이 없으면(`backlog_not_initialized`) 실패로 취급하지 않고 자연히 건너뛴다.
4. **해석 보고**: 아래 "3. 해석 보고 형식"의 골격에 따라 PM이 1회 합성해 보고한다.
5. **라이브 안내**: 상주하지 않고 `--watch` 터미널 명령 1줄을 안내한다.

- [MUST] 도구는 `~/.opal/tools/.../run.sh` 절대경로로만 호출한다 — 스킬 본문에 플랫폼 조건문을 추가하지 않는다.

### 자동 탐지 (인자 없을 때)

1. **loop 루트 우선 탐지**: cwd에서 상향 탐색하여 `backlog.json`을 보유한 폴더(= oppl 루프 루트)를 찾는다.
   - 발견 시: 그 하위 `tasks/T*/.oppl-run/` 폴더들을 mtime 내림차순 정렬하여 **최신 채택**. 복수면 최신을 채택하되 후보 목록도 함께 제시한다.
2. **loop 루트 미발견 시 폴백**: cwd 하위 `tasks/**/.oppl-run/`을 glob(`tasks/*/.oppl-run`, `tasks/*/*/.oppl-run`, 최대 깊이 3)으로 스캔하여 mtime 최신 폴더를 채택한다.
3. **복수 후보**: 최신을 우선 채택하되, 상위 후보 목록(최대 10개)을 함께 제시하여 사용자가 다른 폴더를 재지정할 수 있게 안내한다.
4. **미탐지**: `.oppl-run/`을 보유한 폴더가 하나도 없으면 "진행 중인 액션 에이전트 태스크를 찾지 못했습니다. `//opas <태스크폴더>`로 직접 지정하세요."를 안내하고 종료한다.

- [MUST] glob 깊이 상한(loop 루트 기준 깊이 2, 전역 폴백 깊이 3)으로 무제한 재귀 스캔을 방지한다. 후보 나열 상한은 10개다.
- 탐지는 파일 mtime·존재 여부 기반의 읽기 전용 스캔이며 부수효과가 없다.

## 3. 해석 보고 형식 (골격)

1불릿 1문장으로 작성하며, 수치는 도구 출력값을 그대로 표시한다(재계산·재서술 금지).

- (a) **헤더**: 대상 태스크 폴더 + `generated_at`.
- (b) **전체 blocked 배너**: `--json`의 `blocked:true`이면 상단에 경고 배너 + journal blocked 사유를 표시한다.
- (c) **단계×축 표 요약**: `phases[]`를 `단계 | 축 | 상태 | 경과(s) | 최근 이벤트 | 비용($)`로 렌더한다(값은 도구 출력 그대로).
- (d) **journal 하이라이트**: `journal_tail[]`의 최근 이벤트를 요약한다.
- (e) **루프 백로그 결합(존재 시)**: `backlog-tool show` 결과에서 전체 태스크 진행(done/진행/대기)을 요약한다.
- (f) **다음 액션 제안**: 상태 기반으로 제안한다(예: `running` → watch 권고 / `failed`·`error` → err.log 확인 / `blocked` → 사람 게이트).
- (g) **`--watch` 안내**: `~/.opal/tools/opal-action-monitor/run.sh <task_folder> --watch [간격초]` 1줄을 안내한다.

- [MUST] **수치·스키마 비복제**: 상태 판정 규칙·폴링 주기·`--json` 스키마의 상세는 재서술하지 않고 `opal/tools/opal-action-monitor/README.md`(배포본: `~/.opal/tools/opal-action-monitor/README.md`) 포인터로 위임한다.

## 4. 커버리지 경계

opas의 커버리지는 현재 **oppl 한정**이다(관측 규약 `.oppl-run/`을 루프 액션 에이전트만 준수한다). 069·070(oppd·opsdd 전환) 완료 시에는 **스킬 무변경**으로 커버리지가 확장된다.

범용 설계 원칙: "폴더에 `.oppl-run/`이 있으면 렌더한다"(특정 파이프라인에 종속되지 않고 전방 호환).

## 5. 에러 경로

`opal-action-monitor`가 `{"ok":false}` + exit 1을 반환하면(대상 폴더 또는 `.oppl-run/` 부재), 성공으로 오해하지 않고 `error` 메시지를 사용자에게 안내한 뒤 종료한다. 자동 탐지에서 미탐지된 경우도 위 "자동 탐지 4." 절차에 따라 안내 후 종료한다.

## 6. 라이브 관측 안내

이 스킬은 1회 해석 보고만 수행하며 상주하지 않는다. 지속 관측이 필요하면 `~/.opal/tools/opal-action-monitor/run.sh <task_folder> --watch [간격초]`를 터미널에서 직접 실행하도록 안내한다.

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-17 (KST) | 신설 — 루프 액션 에이전트 진행 현황 발동층. 자동 탐지 + `opal-action-monitor`/`backlog-tool` 소비 + 해석 보고(읽기 전용) (068) |
| v1.1 | 2026-09-02 (KST) | 에이전트명·소유자 호칭 리터럴 제거 — 규범 산문은 역할어(`PM`/`사용자`/`소유자`)로, 산출물·보고 문면은 `{owner_name}` 플레이스홀더로 전환해 런타임에 소유자 호칭으로 대체된다. 프레임워크 재사용성 확보 (L2 직접 수정) |
