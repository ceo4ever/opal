# PLAN: opm 범용 모니터 스킬 신설 — 액션 에이전트 진행 현황 발동층

> 작성일: 2026-07-17 | 입력: TASK.md (ANALYSIS.md 없음 — 코드 직접 분석)
> 모드: Multi-Feature | 실행 모드: 단순 (근거: §6)
> 작성자: opal-plan-agent (Framework 영역 → 실행 Step agent = opal-task-agent)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

067에서 완성된 관측 도구(`opal-action-monitor`)·데이터 규약(`.oppl-run/`)에 **발동층**을 얹는다. `//opm [태스크폴더]` 경량 operator 스킬을 신설하여, 인자 없이 호출하면 진행 중인 oppl 태스크를 자동 탐지하고 `opal-action-monitor --json`(+ 존재 시 `backlog-tool show`)을 소비해 **루프 전체(백로그) + 태스크 내부(단계×축) 결합 현황을 알투가 1회 해석 보고**한다. 라이브 관측은 `--watch` 터미널 명령 안내로 위임한다. 스킬은 읽기 전용(도구 호출 + 해석만, 쓰기 0)이며 도구·규약은 무변경한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | opal-monitor 스킬 본체 (SKILL.md: 실행 컨텍스트·프로세스·해석 보고 형식·에러 경로·커버리지 경계) | R-1 | P0 | 없음 |
| F-002 | 자동 탐지 규칙 (인자 없을 때 oppl 태스크 폴더 탐지 + 복수 후보 + 미탐지 3경로) | R-2 | P0 | F-001 (SKILL 본문에 명문화) |
| F-003 | 레지스트리 등록 + 약어 충돌 확인 (opal-skills-registry.json, alias opm) | R-3 | P0 | F-001 |
| F-004 | 정합·배포·변경이력 (oppl SKILL 안내 1줄 · PROJECT.md 컴포넌트/변경이력 · install 배포 확인) | R-4 | P1 | F-001, F-003 |
| F-005 | 동작 실증 (067 실증 폴더·fixture 실측 — 인자 지정/자동 탐지/부재/backlog 스킵/레지스트리/배포) | R-5 | P0 | F-001~F-004 |

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 ─┬─ F-002 ─┐
       ├─ F-003 ─┼─ F-004 ─ F-005
       └─────────┘
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | 자동 탐지 알고리즘 (F-002) | cwd 하위 복수 `.oppl-run/` 중 오탐 선택 → 엉뚱한 태스크 렌더 | P2 | L2 (다중 fixture mtime) | S-7 |
| H-2 | 도구 에러 계약 소비 (F-001) | `{"ok":false}` + exit 1을 성공으로 오해 → 허위 보고 | P1 | L2 (부재 폴더) | S-8 |
| H-3 | backlog 결합 (F-001) | backlog.json 부재 시 `backlog_not_initialized`를 전체 실패로 처리 | P1 | L2 (단독 `.oppl-run/`) | S-9 |
| H-4 | 수치·스키마 비복제 (F-001) | SKILL이 6상태·2초 폴링·JSON 스키마를 재서술 → README와 drift | P2 | L1 (grep) | S-3 |
| H-5 | 약어 등록 (F-003) | opm 등록 오류/충돌 → `//opm` 발동 불가 | P1 | L1 (skill-registry match/validate) | S-4 |
| H-6 | 읽기 전용 계약 (F-001) | 스킬이 파일 쓰기·state 변경 지시 → 부수효과 | P1 | L1 (문구 검사) | S-3 |
| H-7 | install 배포 (F-004) | `opal/skills/` 신규 폴더가 배포 루프에 누락 → 탐색 경로 부재 | P2 | L3 (배포 후 Read) | S-10 |
| H-8 | 커버리지 경계 (F-001) | oppl 한정·069/070 확장 경계 문구 부재 → 커버리지 오해 | P2 | L1 (grep) | S-1 |
| H-9 | oppl SKILL 무접촉 (F-004) | 안내 1줄 초과 변경 → oppl 회귀 | P1 | L1 (diff 검사) | S-5 |

---

## 2. 기능별 분석

### F-001: opal-monitor 스킬 본체

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-monitor/SKILL.md` | 신설 스킬 정의 (frontmatter·프로세스·보고 형식) | 신규 |
| 소스(계약) | `opal/tools/opal-action-monitor/README.md` | 소비할 CLI·`--json` 스키마·에러계약 SSOT (`README.md:92-120`) | 참조 |
| 소스(계약) | `opal/tools/backlog-tool/README.md` | `show <task-path> [--format md\|json]` 계약 (`README.md:170-181`) | 참조 |
| 설계 준거 | `opal/skills/opal-brain/SKILL.md` | operator형(파이프라인 없음·도구 직접 호출 라우터) 구조 준거 (`SKILL.md:1-24`) | 참조 |

#### 2.1.2 현재 구현 (직접 분석)

**소비 계약 (067 완성, 무변경):**
- `~/.opal/tools/opal-action-monitor/run.sh <task_folder> [--json|--watch]` — `--json`은 1회성 스키마 `{ok, task_folder, generated_at, blocked, phases[], journal_tail[]}` 출력 (`opal-action-monitor/README.md:92-108`). 실측 확인: T01 샘플에서 `ok:true` + phases 6종(t1/t2/g/t3/t4a/t4b) 정상 렌더.
- 에러 계약: 폴더/`.oppl-run/` 부재 시 stdout에 `{"ok":false,"error":"<메시지>"}` + exit 1 (`README.md:114-120`). 실측 확인: `tasks/068-.../`(`.oppl-run/` 없음) 대상 → `{"ok": false, "error": ".oppl-run/ 디렉토리가 없습니다: ..."}`.
- `--watch [간격초] [--watch-timeout <초>]` — 라이브 재렌더, 종료조건 3종 (`README.md:69-77`). 스킬은 1회 해석만 하고 라이브는 이 명령을 **안내**한다.
- `~/.opal/tools/backlog-tool/run.sh show <loop-root> [--format md|json]` — 루프 전체 백로그 뷰. backlog.json 부재 시 `backlog_not_initialized` 에러 (`backlog-tool/README.md:194`).

**operator 선례 (opbr):** `opal-brain`은 단계 파이프라인·워커 디스패치 없이 첫 인자로 모드를 라우팅하고 `brain-tool`을 직접 호출하는 operator 라우터다 (`opal-brain/SKILL.md:20-44`). opm은 이보다 단순한 **단일 모드 라우터**(모드 분기 없음, 인자 파싱 → 탐지 → 도구 호출 → 해석).

**oppl 폴더 구조 (탐지 근거):** oppl 루프 프로젝트 루트는 `tasks/{NNN}-oppl-{프로젝트명}/`이며 그 안에 `backlog.json`(SSOT) + `tasks/T{NN}-{태스크명}/`(개별 태스크) 구조를 가진다 (`opal-pilot-project-loop/SKILL.md:70-83`). 루프 액션 에이전트는 개별 태스크 폴더 하위에 `.oppl-run/`을 남긴다 (`opal-action-monitor/README.md:20-35`).

#### 2.1.3 영향 범위
- 상위 의존(발동): `//opm` 입력 → skill-registry match → 이 SKILL.md 로드. F-003(레지스트리) 필수.
- 하위 의존(소비): `opal-action-monitor`·`backlog-tool` CLI(무변경 소비). 스킬은 두 도구의 산출물/JSON만 읽는다 — import·직접 결합 없음.
- 무영향: `opal-action-monitor`·`.oppl-run/` 규약·oppl 본문(안내 1줄 제외)은 변경하지 않는다.

---

### F-002: 자동 탐지 규칙

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-monitor/SKILL.md` | 자동 탐지 절 (F-001 본문 내 서브섹션) | 신규 |
| 설계 근거 | `opal/skills/opal-pilot-project-loop/SKILL.md` | oppl 폴더 구조 (loop 루트·backlog.json·tasks/T{NN}/) | 참조 |

#### 2.2.2 현재 구현 (직접 분석)
- 현재 발동층 부재 — 캡틴이 터미널에서 직접 `opal-action-monitor` 실행하거나 알투에게 자연어 요청해야 함 (TASK §배경).
- 탐지 SSOT: 파일 시스템 자체 — `backlog.json`(loop 루트 마커) + `.oppl-run/`(태스크 관측 마커). 실측: `tasks/067-.../samples/T01-정상슬라이스/.oppl-run/` 존재, `tasks/056-.../dryrun/backlog.json` 존재.

#### 2.2.3 영향 범위
- 자동 탐지는 파일 mtime·glob 기반 읽기 전용 스캔 — 부수효과 없음. 오탐 시 후보 목록 제시로 사용자 확정에 위임.

---

### F-003: 레지스트리 등록 + 약어 충돌 확인

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 레지스트리 | `opal/core/references/opal-skills-registry.json` | 프레임워크 스킬 메타데이터 SSOT (entry 추가) | 수정 |
| 도구 | `~/.opal/tools/skill-registry/skill-registry.js` | `match`/`validate` 검증 (무변경) | 참조 |
| 참조 | `opal/core/references/skills.md` | 레지스트리 사용법 문서 — SSOT는 JSON임을 명시 (`skills.md:1-6`) | 참조 (무변경) |

#### 2.3.2 현재 구현 (직접 분석)
- **레지스트리 SSOT 위치 확정**: `skills.md`는 "스킬 메타데이터는 JSON 레지스트리가 SSOT"라 명시하며 실제 등록은 `opal/core/references/opal-skills-registry.json`이다 (`skills.md:3-5`). TASK D-3의 `skills.md 등록`은 이 JSON 등록으로 해석 확정. `skills.md`는 tech-stack 추천 문서일 뿐 개별 pilot/operator 스킬 목록을 담지 않으므로 **무변경**.
- **엔트리 형식 (opbr 선례)**: `{name, alias, description, triggers[], paths[], domain, [pipeline]}` (`opal-skills-registry.json:689-703`). operator 스킬(opbr·opws)은 `opal` 그룹에 속한다 (registry group `"opal"` @ line 595).
- **약어 충돌 실측**: `node skill-registry.js match "opm"` → `{"found": false}`, `match "//opm"` → `{"found": false}`. 충돌 0 확인 (PM 확인 + 재실측).

#### 2.3.3 영향 범위
- registry JSON에 1 엔트리 추가 → `match "opm"`/`match "//opm"`가 opal-monitor로 해석되도록 발동 경로 활성화. validate 통과 필수.

---

### F-004: 정합·배포·변경이력

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 모니터링 안내에 `//opm` 언급 1줄 추가 (`SKILL.md:379`) | 수정 (1줄) |
| 문서 | `docs/PROJECT.md` | Project Loop 컴포넌트 표 opal-monitor 행 + 변경이력 | 수정 |
| 환경 | `scripts/install-mac.sh` | 스킬 배포 루프 (무변경 — glob 자동 포함 확인) | 참조 |

#### 2.4.2 현재 구현 (직접 분석)
- **oppl 모니터링 안내 현황**: oppl SKILL.md:379 "진행 현황 모니터링: `~/.opal/tools/opal-action-monitor/run.sh <task_folder> [--watch]` ..." 한 문단 존재. 여기에 `//opm` 발동 안내 1줄만 추가 (본문 무접촉 — H-9).
- **install 배포 방식 (실측)**: `install-mac.sh:1062-1069`가 `for skill_dir in "$opal_dir/skills"/*/; do install_dir ...` 로 `opal/skills/` 하위 **모든** 디렉토리를 `~/.opal/skills/{name}/`로 일괄 복사한다. 즉 `opal/skills/opal-monitor/` 신설 시 **install 스크립트 수정 없이 자동 배포**된다. 배포명 = 디렉토리명 = `opal-monitor`. `strip_deploy_md_recursive`가 배포본에서 변경이력 섹션 strip (`install-mac.sh:1069`).
- **변경이력 의무**: `docs/CONVENTIONS.md §변경이력 작성 의무` — 스킬·참조 문서 변경 시 변경이력 행 추가(태스크번호 괄호).

#### 2.4.3 영향 범위
- oppl SKILL 1줄 추가 외 회귀 없음. PROJECT.md 컴포넌트 표 갱신은 발견 가능성(문서 조망) 확보.

---

### F-005: 동작 실증

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 실증 fixture | `tasks/067-.../samples/T01-정상슬라이스/` | 정상 6단계 완주 `.oppl-run/` — 인자 지정/자동 탐지 실측 | 참조 (읽기) |
| 실증 fixture | `tasks/067-.../samples/monitor-fixtures/{running,done,blocked,error}/` | 상태별 단일 phase fixture — 자동 탐지 다중 후보·상태 렌더 실측 | 참조 (읽기) |
| 실증 대상 | `tasks/068-260717-opds-opm-모니터-스킬/` | `.oppl-run/` 부재 폴더 — 미탐지/에러 안내 실측 | 참조 (읽기) |

#### 2.5.2 현재 구현 (직접 분석)
- 실측 완료: monitor `--json`이 T01에서 `ok:true` 렌더, 068 폴더에서 `{"ok":false,...}` 에러 계약 반환. 시나리오는 mock 없이 실 폴더·실 도구로만 구성 (PRINCIPLES §4).

#### 2.5.3 영향 범위
- 실증은 읽기 전용 관찰 — 산출물 변경 없음. TEST-SCENARIO.md가 시나리오 SSOT.

---

## 3. 기능별 설계

### F-001: opal-monitor 스킬 본체

#### 3.1.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-monitor/SKILL.md` | 스킬 | operator 단일 모드 라우터 정의 | (→ D-2 §모드라우팅), (→ D-1 §CLI) |

#### 3.1.2 API·데이터 모델·화면 설계

**스킬명·디렉토리 결정**: 정식명 `opal-monitor`, 디렉토리 `opal/skills/opal-monitor/`, 약어 `opm`.
- [MUST] `docs/CONVENTIONS.md §네이밍 규칙`: "스킬 폴더: `{그룹}-{역할}` — `opal-pilot-dev`, `op-dev-analysis`" — opal 그룹 operator이므로 `opal-{역할}` 채택 (opbr=opal-brain 동형, `CONVENTIONS.md:19`).
- 도구명 `opal-action-monitor`와 구분: 도구는 렌더러, 스킬은 발동층 → 스킬명은 간결한 `opal-monitor`. (→ D-2 operator 선례)

**frontmatter 골격** (opbr 준거, `opal-brain/SKILL.md:1-15`):
```yaml
---
name: opal-monitor
description: |
  **루프 액션 에이전트 진행 현황 발동층 — 자동 탐지 + 해석 보고**.
  반드시 이 스킬을 사용해야 하는 상황: "opal-monitor", "opm", "액션 에이전트 현황", "루프 진행 상황".
alias: opm
triggers:
  - "^opm$"
  - "^opal-monitor$"
  - "(?i)(액션\\s*에이전트\\s*현황|루프\\s*진행\\s*상황|모니터\\s*현황)"
version: "1.0"
domain: dev
---
```

**본문 필수 절 (R-1 AC — 아래 6절 전부 존재):**
1. **실행 컨텍스트** — 오케스트레이터(알투/PM)가 **직접 수행**. 워커 디스패치·파이프라인 없음(operator). 읽기 전용(도구 호출 + 해석만, 파일 쓰기·state 변경 0). (→ D-2 §Harness)
2. **프로세스** — 5단계 순차:
   - ① 인자 파싱: `//opm [태스크폴더]` — 인자 있으면 그 폴더, 없으면 자동 탐지(§3.2.2 F-002).
   - ② `opal-action-monitor --json` 호출: `~/.opal/tools/opal-action-monitor/run.sh <task_folder> --json`. `ok:false`면 에러 경로(아래 5절).
   - ③ backlog 결합(존재 시): loop 루트에 `backlog.json`이 있으면 `~/.opal/tools/backlog-tool/run.sh show <loop-root>` 호출 — 루프 전체 뷰 결합. 부재 시 자연 스킵(§3.1.2 backlog 조건).
   - ④ 해석 보고: 아래 "해석 보고 형식" 골격으로 알투가 1회 합성.
   - ⑤ 라이브 안내: `--watch` 터미널 명령 1줄 안내(스킬은 상주하지 않음).
   - [MUST] 도구명은 `~/.opal/tools/.../run.sh` 절대경로로만 호출 — `docs/CONVENTIONS.md §플랫폼 분기 격리`: "스킬 본문에 플랫폼 조건문 추가 금지" (`CONVENTIONS.md:208-211`).
3. **해석 보고 형식 (골격)** — 1불릿 1문장, 수치는 도구 출력값 그대로 표시(재계산·재서술 금지):
   - (a) 헤더: 대상 태스크 폴더 + `generated_at`.
   - (b) **전체 blocked 배너**: `--json`의 `blocked:true`이면 상단에 경고 배너 + journal blocked 사유.
   - (c) **단계×축 표 요약**: `phases[]`를 `단계 | 축 | 상태 | 경과(s) | 최근 이벤트 | 비용($)`로 렌더 (값은 도구 출력 그대로).
   - (d) **journal 하이라이트**: `journal_tail[]` 최근 이벤트 요약.
   - (e) **루프 백로그 결합(존재 시)**: backlog-tool show 결과에서 전체 태스크 진행(done/진행/대기) 요약.
   - (f) **다음 액션 제안**: 상태 기반(예: `running` → watch 권고 / `failed`·`error` → err.log 확인 / `blocked` → 사람 게이트).
   - (g) **--watch 안내**: `~/.opal/tools/opal-action-monitor/run.sh <task_folder> --watch [간격초]` 1줄.
   - [MUST] **수치·스키마 비복제**: 6상태 판정 규칙·2초 폴링·JSON 스키마 상세는 재서술하지 않고 `opal-action-monitor/README.md` 포인터로 위임 (TASK §제약, `README.md:42-52`). (→ D-1 §상태 판정)
4. **커버리지 경계** — [MUST] "opm 커버리지는 현재 **oppl 한정**(관측 규약 `.oppl-run/`을 루프 액션 에이전트만 준수). 069·070(oppd·opsdd 전환) 완료 시 **스킬 무변경**으로 3/3 확장." 명문 (TASK §커버리지 현실, → D-6). 범용 설계 원칙: "폴더에 `.oppl-run/`이 있으면 렌더"(파이프라인 무관·전방 호환).
5. **에러 경로** — [MUST] `opal-action-monitor`가 `{"ok":false}` + exit 1 반환 시(폴더/`.oppl-run/` 부재) 성공으로 오해하지 않고 `error` 메시지를 사용자에게 안내 후 종료 (H-2, `README.md:114-120`). 자동 탐지 미탐지 시 안내 후 종료(§3.2.2).

#### 3.1.3 환경 변경
해당 없음 (기존 CLI 소비, 신규 패키지·의존성 없음).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (6절 완비) | 산출물 검사 | 실행컨텍스트·프로세스·보고형식·커버리지경계·에러경로 5절 전부 존재, 수치는 README 포인터로만 참조 |
| TS-002 | R-1 AC (에러 경로) | 기능 테스트 | 부재 폴더에서 `{"ok":false}` 안내 후 종료 (허위 보고 없음) |

---

### F-002: 자동 탐지 규칙

#### 3.2.1 파일 변경 계획

**수정** — F-001 SKILL.md 본문 내 "자동 탐지" 절로 통합 작성 (별도 파일 없음).

#### 3.2.2 API·데이터 모델·화면 설계

**자동 탐지 알고리즘 (인자 없을 때):**
1. **loop 루트 우선 탐지**: cwd에서 상향 탐색하여 `backlog.json` 보유 폴더(= oppl 루프 루트)를 찾는다 (`opal-pilot-project-loop/SKILL.md:77-78`).
   - 발견 시: 그 하위 `tasks/T*/.oppl-run/` 폴더들을 mtime 내림차순 정렬 → **최신 채택**. 복수면 최신 우선 + 후보 목록 제시.
2. **loop 루트 미발견 시 폴백**: cwd 하위 `tasks/**/.oppl-run/`를 glob(깊이 상한 — `tasks/*/.oppl-run` 및 `tasks/*/*/.oppl-run`, 최대 깊이 3)으로 스캔 → mtime 최신 폴더 채택.
3. **복수 후보**: 최신 우선 채택하되 상위 N개(권장 최대 10) 후보 목록을 함께 제시하여 사용자가 다른 폴더 재지정 가능하게 안내.
4. **미탐지**: `.oppl-run/` 보유 폴더가 하나도 없으면 "진행 중인 액션 에이전트 태스크를 찾지 못했습니다. `//opm <태스크폴더>`로 직접 지정하세요." 안내 후 종료.

**스캔 비용 상한 (H-1 완화):**
- [MUST] glob 깊이 상한(loop 루트 기준 깊이 2, 전역 폴백 깊이 3)으로 무제한 재귀 스캔 방지. 후보 나열 상한 10.
- 탐지는 파일 mtime·존재 기반 읽기 전용 — 부수효과 0.

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-003 | R-2 AC (3경로 명문) | 산출물 검사 | 탐지 규칙·복수 후보·미탐지 3경로 + 깊이 상한 명문 |
| TS-004 | R-2 AC (자동 탐지 실측) | 기능 테스트 | 다중 fixture에서 최신 채택 + 후보 목록 제시 |

---

### F-003: 레지스트리 등록 + 약어 충돌 확인

#### 3.3.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-skills-registry.json` | 레지스트리 | `opal` 그룹에 opal-monitor 엔트리 추가 (alias opm) | (→ D-3 §엔트리형식), `opal-skills-registry.json:689-703` |

#### 3.3.2 API·데이터 모델·화면 설계

**추가 엔트리 (opbr 선례 형식):**
```json
{
  "name": "opal-monitor",
  "alias": "opm",
  "description": "루프 액션 에이전트 진행 현황 발동층 — 자동 탐지 + opal-action-monitor/backlog-tool 소비 + 해석 보고 (읽기 전용)",
  "triggers": ["^opm$", "^opal-monitor$", "(?i)(액션\\s*에이전트\\s*현황|루프\\s*진행\\s*상황)"],
  "paths": ["{project}/.opal/skills/opal-monitor/SKILL.md", "~/.opal/skills/opal-monitor/SKILL.md"],
  "domain": "dev"
}
```
- 배치 그룹: `opal` (operator 스킬 opbr·opws와 동일 그룹, `opal-skills-registry.json:595`).
- [MUST] `docs/CONVENTIONS.md §약어(Alias)`: 약어 체계 준수 — opm은 미사용 확인(실측 `match "opm"` → found:false). (`CONVENTIONS.md:39-50`)
- 등록 후 `validate` 통과 필수 (JSON 유효성·중복 alias 검증).

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음.

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R-3 AC (매칭 + 충돌 0) | 기능 테스트 | `match "opm"`/`match "//opm"` → opal-monitor found:true, `validate` pass, 충돌 0 |

---

### F-004: 정합·배포·변경이력

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 오케스트레이터 | 모니터링 안내에 `//opm` 발동 1줄 추가 (본문 무접촉) | `SKILL.md:379` |
| 2 | `docs/PROJECT.md` | 문서 | Project Loop 컴포넌트 표 opal-monitor(opm) 행 + 변경이력 | `PROJECT.md:103-112` |

#### 3.4.2 API·데이터 모델·화면 설계

**oppl 안내 1줄 (H-9 무접촉):**
- SKILL.md:379 기존 안내 문단 말미에 "스킬 발동: `//opm [태스크폴더]`로 자동 탐지 + 해석 보고(읽기 전용)를 실행할 수 있다." 1줄만 추가. 다른 절 무변경.

**PROJECT.md 컴포넌트 행:**
- Project Loop 표(`PROJECT.md:103-111`)에 `opal-monitor | opm | operator | 액션 에이전트 진행 현황 발동층 — 자동 탐지 + opal-action-monitor/backlog-tool 소비 + 해석 보고(읽기 전용). oppl 한정 커버리지(069/070 확장 시 무변경)` 행 추가 + 변경이력 행(068).

**install 배포 (무변경 확인):**
- [MUST] `docs/CONVENTIONS.md §배포 경계`: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행" (`CONVENTIONS.md:203-204`) — 스킬은 `opal/skills/opal-monitor/`에 작성 후 install로 배포.
- `install-mac.sh:1062-1069` glob이 `opal/skills/*/`를 자동 복사하므로 install 스크립트 **수정 불요** — 신설 폴더 자동 포함. 배포 검증(S-10)만 수행.

#### 3.4.3 환경 변경
해당 없음 (install 스크립트 무변경).

#### 3.4.4 배치/마이그레이션
install 재실행(배포) — 사람 게이트(캡틴 승인 후).

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-006 | R-4 AC (안내·이력) | 산출물 검사 | oppl SKILL `//opm` 1줄 존재(본문 무변경 diff), PROJECT.md 행 + 변경이력 3종(PROJECT/opal-monitor/registry) |
| TS-007 | R-4 AC (배포) | 통합 테스트 | 배포 후 `~/.opal/skills/opal-monitor/SKILL.md` Read 가능 |

---

### F-005: 동작 실증

#### 3.5.1 파일 변경 계획
신규/수정 없음 — 읽기 전용 실증. TEST-SCENARIO.md가 시나리오 SSOT.

#### 3.5.2 API·데이터 모델·화면 설계
- 실증 fixture 3종 활용: T01(정상 6단계), monitor-fixtures/{running,done,blocked,error}(상태별), 068 폴더(부재).
- 6경로 실측: 인자 지정 / 자동 탐지 / 부재 폴더 / backlog 결합 스킵 / 레지스트리 매칭 / 배포 Read. 전부 mock 금지·실 도구·실 폴더 (TASK R-5 AC).

#### 3.5.3 환경 변경
해당 없음.

#### 3.5.4 배치/마이그레이션
해당 없음.

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-008 | R-5 AC (인자 지정) | 기능 테스트 | T01 지정 → 단계×축 해석 보고 산출 |
| TS-009 | R-5 AC (backlog 스킵) | 기능 테스트 | 단독 `.oppl-run/`(loop 루트·backlog.json 없음) → backlog 자연 스킵 + 태스크 단독 뷰 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)
| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002 | 1 | opal-task-agent | 순차 | SKILL 본체 + 자동 탐지 통합 작성 |
| 2 | F-003 | 2 | opal-task-agent | 순차 | registry 등록 (Step 1 후 paths 확정) |
| 3 | F-004 | 3, 4 | opal-task-agent / PM 직접 | 순차 | oppl 1줄 + docs 갱신 |
| 4 | F-004(배포) | 5 | PM 직접(사람 게이트) | 순차 | install 배포 + 검증 |
| 5 | F-005 | (TEST 단계) | 오케스트레이터 | — | TEST-SCENARIO 실증 (EXECUTE Step 아님) |

### 4.2 실행 체크리스트
> 총 5개 Step | Phase 4개(+TEST) | 실행 모드: 단순

#### Step 1: opal-monitor SKILL.md 신설 (본체 + 자동 탐지)
- [x] 완료 (명명 오버라이드 — 캡틴 확정 opal-action-status/opas로 구현: `opal/skills/opal-action-status/SKILL.md`)
- **소속 기능**: F-001, F-002
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-monitor/SKILL.md` (신규)
- **작업 내용**: frontmatter(name/alias:opm/triggers/domain) + 본문 6절(실행 컨텍스트·프로세스 5단계·해석 보고 형식 골격 a~g·커버리지 경계·에러 경로) + 자동 탐지 절(loop 루트 우선→glob 폴백→복수 후보→미탐지 4경로 + 깊이 상한). 수치·스키마는 opal-action-monitor/README.md 포인터로만 참조. 변경이력 표(v1.0, 068).
- **완료 기준**: 6절 + 자동 탐지 4경로 전부 존재, 6상태·2초·JSON 스키마 리터럴 재서술 부재(README 포인터만), 읽기 전용·쓰기 0 명문
- **테스트**: TS-001, TS-002, TS-003, TS-004
- **실행 방법**: direct
- **의존**: 없음

#### Step 2: 레지스트리 등록 (alias opm)
- [x] 완료 (명명 오버라이드 — alias opas로 등록. `match "opas"`/`match "//opas"` → found:true(opal-action-status). `validate`는 배포 전이라 dangling 1건(paths 미배포)만 검출 — Step 5 배포 후 해소 예정)
- **소속 기능**: F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: `opal` 그룹에 opal-monitor 엔트리(name/alias:opm/description/triggers/paths/domain:dev) 추가. paths는 `{project}/.opal/skills/opal-monitor/SKILL.md`·`~/.opal/skills/opal-monitor/SKILL.md`.
- **완료 기준**: `node skill-registry.js match "opm"` → found:true(opal-monitor), `match "//opm"` → found:true, `validate` pass, 약어 충돌 0
- **테스트**: TS-005
- **실행 방법**: direct
- **의존**: Step 1

#### Step 3: oppl SKILL 모니터링 안내 1줄 정합
- [x] 완료 (`//opas [태스크폴더]` 안내 1줄 + 변경이력 v1.6(068) 추가, 본문 무접촉)
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-loop/SKILL.md`
- **작업 내용**: `SKILL.md:379` 모니터링 안내 문단에 `//opm [태스크폴더]` 발동 1줄 추가 + 변경이력 행(068). 본문 다른 절 무접촉(H-9).
- **완료 기준**: `//opm` 1줄 존재, diff가 안내 1줄 + 변경이력 1행으로 한정, 회귀 0
- **테스트**: TS-006
- **실행 방법**: direct
- **의존**: Step 1, Step 2

#### Step 4: docs/PROJECT.md 컴포넌트 표 + 변경이력 갱신
- [x] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: Project Loop 컴포넌트 표에 opal-monitor(opm) operator 행 추가(커버리지 경계 명시) + 변경이력 행(068). (새 패턴/컴포넌트 도입 → PROJECT.md 갱신 대상)
- **완료 기준**: opal-monitor 행 + 변경이력 행 존재, oppl 한정·069/070 확장 경계 서술
- **테스트**: TS-006
- **실행 방법**: direct
- **의존**: Step 1
- **비고**: docs/ 갱신 Step (자동 생성 규칙 — 새 컴포넌트 도입)

#### Step 5: install 배포 + 배포 검증 [사람 게이트]
- [x] 완료
- **소속 기능**: F-004
- **영역**: 배치
- **agent**: PM 직접 (캡틴 승인 후 실행 — 배포는 사람 게이트)
- **파일**: `scripts/install-mac.sh` 실행 (스크립트 무변경 — glob 자동 포함)
- **작업 내용**: 캡틴 승인 후 `./scripts/install-mac.sh` 실행 → `~/.opal/skills/opal-monitor/SKILL.md` 배포 확인 + `~/.opal/references/opal-skills-registry.json` opm 엔트리 반영 확인.
- **완료 기준**: 배포 후 `~/.opal/skills/opal-monitor/SKILL.md` Read 가능, `//opm` 매칭 활성
- **테스트**: TS-007
- **실행 방법**: direct
- **의존**: Step 1, Step 2, Step 3
- **비고**: [SUPERVISOR] 캡틴 배포 승인 필요 (CONVENTIONS §배포 경계)

> **F-005 동작 실증(R-5)은 EXECUTE Step이 아니라 TEST 단계**에서 TEST-SCENARIO.md(S-6~S-10)로 수행한다 — 오케스트레이터 책임.

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | registry paths가 스킬 디렉토리명에 의존 (Step 1 확정 선행) |
| Step 1 → Step 3 | oppl 안내가 `//opm` 발동 전제 (스킬 존재 선행) |
| Step 1 ∥ Step 4 | PROJECT.md는 스킬 내용과 독립 문서 갱신 (병렬 가능하나 순차 진행 무해) |
| Step 5 (최종) | 배포는 소스 3종(Step 1~3) 완료 후 + 캡틴 승인 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | SKILL 6절 완비 + 수치 비복제 | TS-001 | 6절 존재, 6상태/2초/JSON 스키마 리터럴 부재(README 포인터만) |
| F-001 | 에러 경로 안내 | TS-002 | 부재 폴더 `{"ok":false}` 안내 후 종료 |
| F-002 | 자동 탐지 3경로 명문 + 실측 | TS-003, TS-004 | 탐지/복수후보/미탐지 + 깊이상한 명문, 다중 fixture 최신 채택 |
| F-003 | 약어 등록·충돌 0 | TS-005 | match found:true, validate pass, 충돌 0 |
| F-004 | 정합·이력·배포 | TS-006, TS-007 | oppl 1줄(무접촉), 변경이력 3종, 배포 후 Read 가능 |
| F-005 | 6경로 실증 | TS-008, TS-009 | 인자/자동/부재/backlog스킵/레지스트리/배포 전건 PASS |

### 5.2 회귀 테스트
- [ ] oppl SKILL diff가 안내 1줄 + 변경이력 1행으로 한정 (본문 무접촉 — H-9)
- [ ] `opal-action-monitor`·`.oppl-run/` 규약·backlog-tool 무변경 (도구 로직 0 변경)
- [ ] 기존 스킬 약어 매칭 회귀 없음 (opm 추가가 다른 alias 매칭 변경 안 함)

### 5.3 코드/문서 품질
- [ ] `docs/CONVENTIONS.md §변경이력 작성 의무` 준수 — SKILL v1.0·registry·oppl·PROJECT.md 이력 행(068, KST 일시)
- [ ] 네이밍 `{그룹}-{역할}` = opal-monitor, 파일/디렉토리 kebab-case
- [ ] SKILL 본문에 플랫폼 조건문 부재 (도구는 `~/.opal/tools/.../run.sh` 절대경로)

### 5.4 보안
- [ ] SKILL·registry·문서에 하드코딩 토큰/시크릿 없음
- [ ] 스킬 읽기 전용 계약 준수 — 파일 쓰기·state 변경 지시 부재 (부수효과 0)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 (≤5) |
| 변경 파일 수 | 4개 (SKILL 신규 + registry·oppl·PROJECT.md 정합) | 경계 (실질 신규 1개, 3개는 엔트리/1줄/행 수준) |
| 모듈 범위 | 단일 (Framework 스킬) | 단순 |
| 작업 유형 | 신규 스킬 문서 | 경계 (문서 저술 — 코드/토폴로지 없음) |
| 외부 의존성 | 없음 (기존 CLI 소비, 신규 패키지 0) | 단순 |
| **실행 모드** | **단순** | 순차 실행·워커 토폴로지 불요·Short Task |

> 변경 파일 4개·신규 유형은 형식상 복잡 경계이나, 실질 신규는 SKILL.md 1개이고 나머지는 정합(엔트리 1·1줄·행 1) 수준이며 단일 모듈·순차·외부 의존 0이므로 **단순 모드** 채택. §7(실행 아키텍처) 생략.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 스킬·레지스트리 | Markdown, JSON (frontmatter YAML) | (해당 없음 — 프레임워크 문서 저술) |
| 소비 CLI | Bash/Python (`opal-action-monitor`, `backlog-tool`) | 무변경 소비 |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 프레임워크 내부 스킬 저술 — 외부 라이브러리 문서 불요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 소스 | opal-action-monitor | `opal/tools/opal-action-monitor/README.md` | 소비할 CLI·`--json` 스키마·에러계약 SSOT |
| D-2 | 설계 | opbr 선례 | `opal/skills/opal-brain/SKILL.md` | operator형(파이프라인 없음) 구조 준거 |
| D-3 | 설계 | 스킬 레지스트리 | `opal/core/references/opal-skills-registry.json`, `opal/core/references/skills.md` | 등록 형식(SSOT=JSON)·약어 충돌 확인 |
| D-4 | 설계 | oppl 오케스트레이터 | `opal/skills/opal-pilot-project-loop/SKILL.md` | 모니터링 안내 1줄 정합 + 폴더 구조(탐지 근거) |
| D-5 | 기록 | 067 DONE | `tasks/067-260717-opd-루프액션-스트림-모니터링/` | 도구·규약 완성 상태·실증 fixture |
| D-6 | 기록 | 후속 메모 | `memory/후속_069_070_액션에이전트_관측_확장.md` | 커버리지 확장 경계 근거 |
| D-7 | 소스 | backlog-tool | `opal/tools/backlog-tool/README.md` | `show` 서브명령 계약 (loop 백로그 결합) |
| D-8 | 소스 | install-mac.sh | `scripts/install-mac.sh:1062-1069` | 스킬 배포 glob(자동 포함) 확인 |
| D-9 | 설계 | RED-first 트랙 | `opal/core/references/harness/red-first.md` §1.5 | 구현-후-검증 트랙 판정 근거 |

> [MUST] `docs/CONVENTIONS.md §배포 경계`: "`~/.opal/` 직접 편집 금지 — 항상 프로젝트 소스 수정 후 install로 배포" (`CONVENTIONS.md:203-204`).
> [MUST] `docs/CONVENTIONS.md §네이밍 규칙`: "스킬 폴더: `{그룹}-{역할}`" (`CONVENTIONS.md:19`).
> [MUST] `docs/CONVENTIONS.md §플랫폼 분기 격리`: "스킬·에이전트 본문에 플랫폼 조건문 추가 금지" (`CONVENTIONS.md:208-211`).
> [MUST] `docs/CONVENTIONS.md §변경이력 작성 의무`: 변경 시 이력 행 추가(태스크번호·KST 일시) (`CONVENTIONS.md:196-199`).

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | 자동 탐지 오탐 | F-002 | P2 | glob 깊이 상한 + 복수 후보 목록 제시(사용자 확정 위임) |
| H-2 | 에러 계약 오해 | F-001 | P1 | `{"ok":false}` exit 1 → 명시적 에러 안내 경로 (S-8 실증) |
| H-3 | backlog 결합 크래시 | F-001 | P1 | backlog.json 존재 시만 호출 + `backlog_not_initialized` 자연 스킵 (S-9) |
| H-4 | 수치·스키마 복제 | F-001 | P2 | README 포인터로만 참조, 리터럴 grep 검사 (S-3) |
| H-5 | 약어 충돌·매칭 실패 | F-003 | P1 | match/validate 실측 게이트 (S-4) |
| H-6 | 읽기 전용 위반 | F-001 | P1 | 쓰기 도구 호출 부재 grep + 계약 명문 (S-3) |
| H-7 | install 미배포 | F-004 | P2 | glob 자동 포함 확인 + 배포 후 Read 검증 (S-10) |
| H-8 | 커버리지 경계 누락 | F-001 | P2 | oppl 한정·069/070 확장 문구 명문 (S-1) |
| H-9 | oppl 무접촉 위반 | F-004 | P1 | 안내 1줄 한정 diff 검사 (S-5) |
