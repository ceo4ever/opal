# opal-start 진단·라우팅 흐름 가이드

> 로드 시점: opal-start/SKILL.md Step 1·2 실행 시
> 역할: 환경 진단 순서·판단 기준·분기 라우팅 상세 설명

---

## 1. 진단 흐름 개요

`//start`가 호출되면 아래 순서로 환경 상태를 점검하고 라우팅 결정을 내린다.

```
[START]
  │
  ▼
[A] ~/.opal/AGENT.md 존재?
  ├─ NO  → [분기 0] OPAL 미설치 안내 → END
  └─ YES ↓
  │
  ▼
[B] ~/.opal/identity.md 존재?
  ├─ NO  → [분기 1] onboarding 위임 → END
  └─ YES ↓
  │
  ▼
[C] cwd 프로젝트 신호 감지?
  ├─ NO  → [분기 2] 비서 모드 안내 → END
  └─ YES ↓
  │
  ▼
[D] cwd에 .opal/AGENT.md 존재?
  ├─ NO  → [분기 3] //opi 권유 → END
  └─ YES ↓
  │
  ▼
[E] cwd에 docs/PROJECT.md 존재?
  ├─ NO  → [분기 4] PROJECT.md 없음 안내 → END
  └─ YES → [분기 5] PM 모드 정상 → 슬래시 커맨드 메뉴 안내 → END
```

이상 징후 감지 시(어느 분기에서든 예상 파일 구조 불일치 등) → [분기 6] doctor 권유를 추가 안내.

---

## 2. 진단 항목 상세

### A. OPAL 설치 확인

**점검 방법**: `~/.opal/AGENT.md` 파일 존재 여부 (Read 시도 또는 Bash `test -f ~/.opal/AGENT.md`)

**판정 기준**:
- 존재: OPAL 설치됨
- 부재: OPAL 미설치 → 즉시 분기 0으로 라우팅

### B. 에이전트 정체성 확인

**점검 방법**: `~/.opal/identity.md` 파일 존재 여부

**판정 기준**:
- 존재: 정체성 설정 완료
- 부재: `//onboarding` 스킬로 위임 필요 → 분기 1

**근거**: `opal/skills/opal-onboarding/SKILL.md` — identity.md 없을 때 자동 실행 조건

### C. cwd 프로젝트 신호 감지

**점검 방법**: Bash로 아래 신호 파일 중 1개 이상 존재 확인

| 신호 파일/디렉토리 | 의미 |
|-----------------|------|
| `.git/` | Git 저장소 (가장 강한 신호) |
| `package.json` | Node.js 프로젝트 |
| `pyproject.toml` | Python 프로젝트 |
| `Cargo.toml` | Rust 프로젝트 |
| `go.mod` | Go 프로젝트 |
| `CLAUDE.md` | Claude Code 프로젝트 |
| `GEMINI.md` | Gemini 프로젝트 |
| `.cursor/` | Cursor 프로젝트 |

신호 파일이 1개도 없으면 비프로젝트로 판정 → 분기 2

### D. OPAL 프로젝트 초기화 확인

**점검 방법**: cwd 기준 `.opal/AGENT.md` 존재 여부

**판정 기준**:
- 존재: OPAL 프로젝트 초기화 완료
- 부재: `//opi`로 초기화 필요 → 분기 3

**근거**: `opal/core/AGENT.md` §역할 전환 — `.opal/AGENT.md` 존재 여부로 비서/PM 자동 전환

### E. 프로젝트 문서 확인

**점검 방법**: cwd 기준 `docs/PROJECT.md` 존재 여부

**판정 기준**:
- 존재: PM 모드 완전 동작 가능 → 분기 5 (정상)
- 부재: 프로젝트 문서 미생성 → 분기 4

---

## 3. 분기별 안내 메시지 상세

### 분기 0: OPAL 미설치

```
OPAL이 설치되지 않았습니다.

설치 명령:
  macOS / Linux:
    curl -fsSL https://raw.githubusercontent.com/ceo4ever/opal/main/install.sh | bash

  Windows (PowerShell):
    iex (irm https://raw.githubusercontent.com/ceo4ever/opal/main/install.ps1)

설치 후 AI 도구를 재시작하면 OPAL 에이전트가 자동 로드됩니다.
```

### 분기 1: 정체성 미설정

```
에이전트 정체성이 설정되지 않았습니다.

  - //onboarding 을 입력하면 설정을 시작합니다.
  - 또는 다음 메시지를 보내면 자동으로 시작됩니다: "정체성 설정해줘"
```

### 분기 2: 비프로젝트 (비서 모드)

```
현재 비프로젝트 위치입니다. 비서 모드로 동작합니다.

가능한 작업:
  - 자연어로 일반 작업 요청 (문서 작성, 코드 질문 등)
  - //opi  : 현재 위치에 OPAL 프로젝트 초기화
  - 프로젝트 폴더로 이동 후 //start 재실행하면 PM 모드로 진입 가능
```

### 분기 3: 프로젝트 미초기화

```
프로젝트 폴더이지만 OPAL 환경이 초기화되지 않았습니다.

  - //opi 를 실행하면 이 프로젝트에 OPAL 환경을 설정합니다.
  - 초기화 후 //start 재실행으로 정상 PM 모드를 확인하세요.
```

### 분기 4: PROJECT.md 없음

```
OPAL 프로젝트 환경은 있지만 docs/PROJECT.md가 없습니다.

  - //opi 로 프로젝트를 재초기화하거나 docs/PROJECT.md를 직접 생성하세요.
  - PROJECT.md 없이도 //opp, //opds 등의 슬래시 커맨드는 동작하지만
    프로젝트 컨텍스트 자동 로딩이 제한됩니다.
```

### 분기 5: PM 모드 정상

```
[OPAL] PM 모드 정상입니다.

다음 중 선택하세요:
  - //opp <요청>   범용 작업 (문서/설정/분석)
  - //opds <요청>  개발 Short Task (빠른 구현)
  - //opd <요청>   개발 Full Task (전체 파이프라인)
  - //opi          프로젝트 정의 갱신
  - opal-cli doctor  환경 진단
```

### 분기 6: 시스템 이상 징후 (doctor 권유)

분기 0~5에서 예상과 다른 상태가 감지될 때 추가로 안내한다.

```
환경에 이상 징후가 있습니다.

  opal-cli doctor 로 의존성·경로·MCP·부트스트래퍼 정합성을 진단하세요.
  (opal-cli 미설치 시: ~/.opal/tools/doctor/run.sh 직접 실행)
```

---

## 4. 진단 결과 표 출력 형식

SKILL.md Step 1 완료 후 사용자에게 출력하는 표 형식:

```
[OPAL Start] 환경 진단 결과

| 항목 | 결과 |
|------|------|
| ~/.opal/identity.md | ✓ 있음 |
| ~/.opal/AGENT.md (OPAL 설치) | ✓ 있음 |
| cwd 프로젝트 여부 | ✓ 프로젝트 (신호: .git, CLAUDE.md) |
| .opal/AGENT.md (프로젝트 초기화) | ✓ 있음 |
| docs/PROJECT.md | ✓ 있음 |

→ 분기 5: PM 모드 정상
```

결과 항목의 값:
- `✓ 있음` / `✗ 없음` — 존재 여부 명확한 경우
- `✓ 프로젝트 (신호: {감지된 신호 목록})` — cwd 신호 감지 시 감지된 파일 나열
- `- 비프로젝트` — 신호 미감지
- `- 해당없음` — 이전 분기에서 이미 라우팅된 경우 (진단 불필요)

---

## 5. opal-onboarding 위임 방식

분기 1(identity 부재) 발생 시, 이 스킬은 직접 온보딩을 수행하지 않는다. 다음 방식으로 위임한다:

1. `//onboarding` 호출 안내 메시지를 출력한다.
2. 사용자가 `//onboarding`을 입력하면 `opal-onboarding` 스킬이 자동 매칭된다.
3. AGENT.md 부트스트랩 자동 발화(identity.md 부재 시 자동 실행)도 동일하게 작동한다.

**근거**: `opal/skills/opal-onboarding/SKILL.md` §실행 조건 + `opal/core/AGENT.md` 부트스트랩 Eager 단계

---

## 6. 관련 컴포넌트 참조

| 컴포넌트 | 경로 | 관계 |
|---------|------|------|
| opal-onboarding | `opal/skills/opal-onboarding/SKILL.md` | identity 미설정 시 위임 대상 |
| opal-project-init | `opal/skills/opal-project-init/SKILL.md` | 프로젝트 초기화 (`//opi`) |
| OPAL 부트스트랩 | `opal/core/AGENT.md` | 자동 로드 + 역할 전환 기준 |
| doctor 도구 | `opal/tools/doctor/run.sh` | 시스템 진단 |
| opal-cli | `opal/tools/opal-cli/run.sh` | CLI 진입점 (`opal-cli doctor` 등) |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0.0 | 2026-05-09 00:00 | 초기 작성 (139) — 진단·라우팅 흐름 상세 가이드 신규 |
