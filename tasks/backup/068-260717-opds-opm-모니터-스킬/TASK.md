# TASK: opm 범용 모니터 스킬 신설 — 액션 에이전트 진행 현황 발동층

> 작성일: 2026-07-17 | 작업 유형: 신규 | 적용 스킬: opds | 모드: agentic
> 입력: 사용자 요청 (067 후속 — 캡틴 확정 "CLOSE 후 068 진행", B안 별도 스킬 선택)
> 출력: TASK.md

## 작업 목표

`//opm [태스크폴더]` 경량 operator 스킬을 신설한다 — 인자 없이 호출하면 진행 중인 oppl 태스크를 자동 탐지하고, `opal-action-monitor --json`(+`backlog-tool show`)을 소비해 **루프 전체(백로그)와 태스크 내부(축별 상태)를 결합한 현황을 알투가 해석해 보고**한다. 라이브 관측은 `--watch` 터미널 명령 안내로 위임한다.

## 배경

067에서 관측 데이터(events.jsonl·journal)와 뷰어 도구(opal-action-monitor)가 완성됐으나 발동층이 없다 — 현재는 캡틴이 터미널에서 직접 실행하거나 알투에게 자연어로 요청해야 한다. 캡틴 요구: 스킬 한 줄로 발동. A안(oppl 모드 플래그) 대비 B안(별도 스킬)을 캡틴이 선택 — 근거: 컴포지션·재사용성 원칙 부합, oppl 본문 무접촉(회귀 0), oppd·opsdd 확장 시 스킬 무변경. 자동 탐지는 파일 SSOT(backlog.json·태스크 폴더) 기반이라 양안 동등함을 확인함.

## 배경 분석 (대화에서 도출)

- **선례 구조**: `opal-brain`(opbr)이 멀티모드 operator(단계 파이프라인·워커 디스패치 없음, 도구 직접 호출 라우터)의 기존 선례 — opm은 이보다 단순한 단일 모드 라우터.
- **소비할 도구 계약(067 완성)**: `~/.opal/tools/opal-action-monitor/run.sh <task_folder> [--json|--watch]` — `--json` 스키마(ok/task_folder/blocked/phases[]/journal_tail), 에러계약 `{"ok":false}`+exit 1. `backlog-tool show`(oppl 백로그 SSOT).
- **커버리지 현실**: 관측 규약(.oppl-run/)은 현재 루프 액션 에이전트만 준수 — opm 커버리지는 당장 oppl 한정이며, 069·070(oppd·opsdd 전환, `memory/후속_069_070_액션에이전트_관측_확장.md`) 완료 시 스킬 무변경으로 3/3 확장. 스킬 문서에 이 경계를 명시해야 한다.
- **스킬 신설 체크(PM 프로필 지침)**: 약어 `opm` 충돌 여부 확인 필요(skills.md 레지스트리), 부트스트래퍼 영향(전역 마커 방식이라 프로젝트 마커 불요 — 049 2-tier), install 배포 경로(`opal/skills/` 또는 `skills/` — 도구 의존 스킬이므로 OPAL 전용 `opal/skills/` 적합).

## 확정된 설계 방향 (대화에서 합의)

1. **별도 경량 스킬**(B안) — oppl SKILL 무접촉(기존 안내 1줄에 `//opm` 언급 추가 정도만 허용).
2. **범용 설계**: "폴더에 `.oppl-run/`이 있으면 렌더" — 파이프라인 무관(전방 호환). 당장 커버리지는 oppl 한정임을 문서에 명시.
3. **자동 탐지**: 인자 없으면 backlog.json/최근 oppl 태스크 폴더 탐지. 라이브는 `--watch` 터미널 명령 안내(스킬은 1회 해석 보고).
4. **읽기 전용**: 스킬은 도구 호출+해석만 — 파일 쓰기·상태 변경 없음.

## 명확화 결과

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | `//opm [태스크폴더]` operator 스킬 — 자동 탐지 + opal-action-monitor/backlog-tool 소비 + 해석 보고 + watch 안내 | - | 067 도구·계약 완성 |
| 범위 | 포함: SKILL.md 신설(`opal/skills/` 하위)·skills.md 레지스트리 등록(약어 opm)·oppl SKILL 안내 1줄 정합·install 배포 확인·동작 실증. 제외: 도구(opal-action-monitor) 로직 변경, oppd/opsdd 전환(069·070), Console 연계 | 자동 탐지 상세 규칙(스캔 범위·복수 후보 처리)은 PLAN에서 설계 | `opal/tools/opal-action-monitor/README.md` |
| 제약 | 워커 디스패치·파이프라인 없는 operator형(opbr 선례) / 읽기 전용(쓰기 0) / 약어 충돌 시 대안 제시 후 에스컬레이션 / `~/.opal/` 직접 편집 금지 / 변경이력 의무 / 규칙·수치 비복제(도구 README 포인터) | - | `.opal/AGENT.md` 지침 |
| 완료기준 | ① `//opm` 호출 시(레지스트리 매칭) 스킬이 로드되어 자동 탐지→렌더 해석 보고가 완주된다(067 실증 폴더로 실측) ② 인자 지정·부재 폴더·미탐지 각 경로가 정의대로 동작(에러 안내 포함) ③ skills.md 등록 + 약어 충돌 없음 확인 ④ oppl 한정 커버리지·069/070 확장 경계 명시 ⑤ install 배포 후 스킬 탐색 경로에서 Read 가능 | - | PLAN TEST-SCENARIO에서 시나리오 확정 |

## 요구사항

- [ ] R-1 **SKILL.md 신설**: `opal/skills/opm/SKILL.md`(경로·명명은 PLAN에서 레지스트리 관례 확인 후 확정) — 실행 컨텍스트(오케스트레이터 직접 수행·워커 없음), 프로세스(인자 파싱→자동 탐지→`opal-action-monitor --json` 호출→`backlog-tool show` 결합(존재 시)→해석 보고 형식→watch 안내), 커버리지 경계(oppl 한정·069/070 확장), 에러 경로(부재/미탐지). 왜: 확정 방향 §1~4. AC: 위 절이 전부 존재하고 도구 수치·스키마는 README 포인터로만 참조.
- [ ] R-2 **자동 탐지 규칙**: 인자 없을 때 — cwd 프로젝트의 oppl 태스크 폴더(backlog.json 보유 폴더 또는 `.oppl-run/` 보유 최신 태스크) 탐지 규칙과 복수 후보 시 처리(최신 우선 + 후보 목록 제시)를 SKILL에 명문화. 왜: 캡틴 요구("oppl이 아는 걸 활용"의 B안 흡수). AC: 탐지 규칙·복수 후보·미탐지 3경로가 명문.
- [ ] R-3 **레지스트리 등록**: skills.md(약어 `opm`)에 등록 + 약어 충돌 확인. 왜: `//` 발동 전제. AC: `skill-registry match "opm"` 매칭 확인 + 충돌 0.
- [ ] R-4 **정합·배포**: oppl SKILL 모니터링 안내에 `//opm` 언급 1줄, install 배포 확인(스킬 일괄 복사 여부), 변경 문서 변경이력(068). 왜: 발견 가능성·배포 경계. AC: 안내 존재 + 배포 후 `~/.opal/skills/.../SKILL.md` Read 가능 + 이력 전부.
- [ ] R-5 **동작 실증**: 067 실증 폴더(`tasks/067-…/samples/T01-정상슬라이스`)와 fixture로 — 인자 지정/자동 탐지/부재 폴더 3경로 실측 + 해석 보고 산출. 왜: PRINCIPLES §4. AC: TEST-SCENARIO 전 시나리오 PASS.

## 제약 조건

- [MUST] `.opal/AGENT.md` §금지사항: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스를 수정한 후 install로 배포한다."
- [MUST] `.opal/AGENT.md` §업무 수행 지침: "새 스킬·에이전트 추가 시: 기존 컴포넌트와의 의존 관계, 약어(alias) 충돌, 부트스트래퍼 영향을 확인한다." / 변경이력 의무.
- 스킬은 읽기 전용 — 도구 호출과 해석 보고만, 파일 쓰기·state 변경 없음.
- 도구 로직·규약(067 산출) 무변경. oppl SKILL은 안내 1줄 외 무접촉.

## 기술 스택

- Markdown (SKILL.md·레지스트리)
- 기존 CLI 소비: `~/.opal/tools/opal-action-monitor/run.sh`, `~/.opal/tools/backlog-tool/run.sh`

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-action-monitor | `opal/tools/opal-action-monitor/README.md` | 소비할 CLI·JSON 스키마·에러계약 SSOT |
| D-2 | 설계 | opbr 선례 | `opal/skills/opal-brain/SKILL.md` | operator형(파이프라인 없음) 스킬 구조 준거 |
| D-3 | 설계 | 스킬 레지스트리 | `~/.opal/references/skills.md` (소스 위치는 PLAN에서 확인) | 등록 형식·약어 충돌 확인 |
| D-4 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 모니터링 안내 1줄 정합 |
| D-5 | 기록 | 067 DONE | `tasks/067-260717-opd-루프액션-스트림-모니터링/DONE.md` | 도구·규약 완성 상태, 커버리지 경계 |
| D-6 | 기록 | 후속 메모 | `memory/후속_069_070_액션에이전트_관측_확장.md` | 확장 경계 서술 근거 |
| D-7 | 소스 | backlog-tool | `opal/core/references/tools.md` §backlog-tool | show 서브명령 소비 |
