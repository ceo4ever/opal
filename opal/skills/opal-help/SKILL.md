---
name: opal-help
description: |
  **스킬 카탈로그 & 사용법 안내 스킬** — 사용자가 호출 가능한 스킬 목록을 보여주고(Mode 1), 특정 스킬의 기능·사용법·예시를 안내한다(Mode 2). //help, //opal-help 등으로 호출된다.
  반드시 이 스킬을 사용해야 하는 상황: 사용자가 //help 또는 //opal-help 입력 시 / "어떤 스킬 쓸 수 있어", "스킬 목록", "명령어 도움말" 류 질문 시 / "//opd 어떻게 써", "이 스킬 사용법" 류 특정 스킬 사용법 문의 시.
  read-only operator 스킬 — 파일 수정·워커 디스패치 없이 skill-registry 도구의 list/get을 조회하여 안내만 한다.
triggers:
  - "//help"
  - "//opal-help"
  - "스킬 목록"
  - "사용 가능한 스킬"
  - "어떤 스킬"
  - "명령어 도움말"
version: 1.0.0
---

# opal-help — OPAL 스킬 카탈로그 & 사용법 안내

## 목적

사용자가 (1) 호출 가능한 스킬을 한눈에 파악하고, (2) 특정 스킬의 기능·사용법·예시를 확인하도록 안내한다.
**read-only operator 스킬**이다 — 파일을 수정하거나 워커를 디스패치하지 않는다. 데이터는 `skill-registry` 도구에서만 조회한다.

## 전제 — 데이터 소스

스킬 메타데이터의 SSOT는 JSON 레지스트리이며, `skill-registry` 도구로 조회한다.

```bash
node ~/.opal/tools/skill-registry/skill-registry.js list --group={그룹}
node ~/.opal/tools/skill-registry/skill-registry.js get {스킬명 또는 alias}
node ~/.opal/tools/skill-registry/skill-registry.js match "{사용자 입력}"
```

Node.js 미설치 등으로 도구 호출이 실패하면 `~/.opal/references/skills.md`를 Read하여 폴백 안내한다.

## 진입 분기 (Mode 판별)

`//help` 뒤에 이어지는 인자(arguments)로 모드를 결정한다.

| 입력 | 모드 |
|------|------|
| `//help` (인자 없음) | Mode 1 — 카탈로그 (사용자 호출 가능 스킬만) |
| `//help --all` | Mode 1 — 카탈로그 (내부 단계 스킬까지 전부) |
| `//help {스킬명 또는 alias}` (예: `//help opd`) | Mode 2 — 특정 스킬 상세 |

> 하네스 모드 플래그(`--interactive`/`--semi-agentic`/`--agentic`)는 read-only 카탈로그에 영향이 없으므로 무시한다. (`--all`은 opal-help 전용 플래그다.)

---

## Mode 1 — 카탈로그

### Step 1: 사용자 호출 가능 그룹 조회

사용자가 `//`로 직접 호출할 수 있는 3개 그룹만 조회한다.

```bash
node ~/.opal/tools/skill-registry/skill-registry.js list --group=opal-pilot
node ~/.opal/tools/skill-registry/skill-registry.js list --group=standalone
node ~/.opal/tools/skill-registry/skill-registry.js list --group=opal
```

> 내부 단계 스킬(`op-dev-*`/`op-sdd-*`/`op-data-*`/`op-task-*`/`op-brain-*`)은 파일럿이 디스패치하는 워커이므로 **기본 숨김**이다. `dispatched_by` 필드가 있는 스킬은 직접 호출 대상이 아니다.

### Step 2: 그룹별 표 렌더

조회 결과를 아래 형식으로 표시한다. `alias`가 있으면 `//{alias}`, 없으면 `//{name}`을 호출 표기로 쓴다.

```
[OPAL 스킬 카탈로그]

🚀 파일럿 (오케스트레이터 — 단계 파이프라인으로 작업 수행)
| 호출 | 스킬 | 설명 |
|------|------|------|
| //opd | opal-pilot-dev | Full Task 오케스트레이터 |
| ... | ... | ... |

🧩 독립 스킬 (단일 목적 스킬)
| 호출 | 스킬 | 설명 |
|------|------|------|
| //wfb | wireframe-builder | UI 분석·설계 |
| ... | ... | ... |

⚙️ 오퍼레이터 (프레임워크 운영 — 초기화/생성/안내)
| 호출 | 스킬 | 설명 |
|------|------|------|
| //opi | opal-project-init | 프로젝트 초기화 + 최신화 |
| ... | ... | ... |
```

### Step 3: 하단 안내

표 아래에 다음 안내를 덧붙인다.

```
특정 스킬 상세: //help {호출명}  (예: //help opd)
내부 단계 스킬까지 보기: //help --all
모드 플래그: 파일럿은 //{alias} [--interactive|--semi-agentic|--agentic] <작업설명> 형식 (기본 semi-agentic)
```

### Step 4: `--all` 처리

`//help --all` 입력 시 위 3그룹에 더해 내부 단계 스킬 그룹도 조회하여 별도 섹션으로 추가한다.

```bash
node ~/.opal/tools/skill-registry/skill-registry.js list --group=op-dev
node ~/.opal/tools/skill-registry/skill-registry.js list --group=op-sdd
node ~/.opal/tools/skill-registry/skill-registry.js list --group=op-data
node ~/.opal/tools/skill-registry/skill-registry.js list --group=op-task
node ~/.opal/tools/skill-registry/skill-registry.js list --group=op-brain
```

```
🔧 내부 단계 스킬 (파일럿이 디스패치 — 직접 호출 불가)
| 스킬 | 단계 | 디스패치 주체 |
|------|------|--------------|
| op-dev-analysis | ANALYSIS | opal-pilot-dev |
| ... | ... | ... |
```

---

## Mode 2 — 특정 스킬 상세

### Step 1: 스킬 조회

인자를 스킬명 또는 alias로 조회한다.

```bash
node ~/.opal/tools/skill-registry/skill-registry.js get {arg}
```

### Step 2: 상세 렌더

`get`이 스킬을 반환하면(error 없음) 아래 형식으로 표시한다.

```
[스킬 상세] {name} ({//alias 또는 //name})

기능
- {description}
- 도메인: {domain}  (없으면 생략)
- 분류: {group}

사용법
- {pipeline 있을 때}  //{alias} [--interactive|--semi-agentic|--agentic] <작업 설명>
- {pipeline 없을 때}  //{alias} <작업 설명>   (또는 인자 없이 //{alias})
- 파이프라인: {pipeline}   (있을 때만)

예시
- {triggers의 자연어 패턴 1~2개를 자연스러운 호출 예시로 변환}
- //{alias} {도메인에 맞는 구체 작업 설명 예시}

경로
- {paths}
```

- `description`/`domain`/`group`/`pipeline`/`triggers`/`paths`는 `get` 출력 필드에서 가져온다.
- `triggers`의 정규식(`^...$`, `(?i)...`)은 사람이 읽을 수 있는 자연어 예시로 풀어 제시한다. 정규식 메타문자를 그대로 노출하지 않는다.
- `pipeline` 필드 유무로 파일럿(모드 플래그 적용)과 단순 스킬(모드 플래그 무관)을 구분한다.

### Step 3: 심층 안내 (선택 — lazy)

사용자가 "더 자세히", "프로세스 보여줘" 등 깊은 설명을 요청할 때만 대상 스킬의 SKILL.md(`paths`)를 Read하여 프로세스를 요약한다. 기본적으로는 SKILL.md를 로드하지 않는다(토큰 절약).

### Step 4: 미발견 처리

`get`이 `error`(스킬 없음)를 반환하면:

1. `match "//{arg}"`로 트리거 기반 근접 탐색을 시도한다.
2. 매칭되면 "혹시 `//{찾은 alias}`를 찾으셨나요?"로 추천한다.
3. 매칭 실패 시 "`{arg}` 스킬을 찾을 수 없습니다. `//help`로 전체 목록을 확인하세요."로 안내한다.

---

## 비범위 (Non-goals)

opal-help는 안내만 한다. 다음은 각 전용 스킬로 위임한다.

| 요청 | 위임 대상 |
|------|----------|
| 스킬 생성/수정 | `//osc` (opal-skill-creator) |
| 커뮤니티 스킬 검색/설치/삭제 | `//osm` (opal-skill-manager) |
| 현재 상태 진단 + 다음 액션 권유 | `//next` (opal-next) |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0.0 | 2026-06-21 | 초기 작성 — Mode 1(카탈로그, 사용자 호출 가능 스킬만 + --all) / Mode 2(특정 스킬 상세). skill-registry list/get 조회 기반 read-only operator 스킬 |
