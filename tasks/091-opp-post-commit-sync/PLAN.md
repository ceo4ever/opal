# PLAN: post-commit 문서 동기화 — A안 설계 검토

> 태스크: 091 | 작성일: 2026-04-06 | 유형: 분석/검토

---

## 1. 현황 조사

### 1-1. opi 최신화 모드 구조 (Phase별)

opi v3.0.0의 최신화 모드는 6개 Phase로 구성되어 있다.

| Phase | 이름 | 인터랙티브 요소 | post-commit 재사용 가능성 |
|-------|------|----------------|------------------------|
| 0 | 태스크 폴더 생성 | 없음 | **불필요** — post-commit은 별도 태스크 불필요 |
| 1 | 현재 상태 분석 | 없음 | **재사용 가능** — MEMORY.md 읽기, docs/ 스캔, 변경 맥락 수집 |
| 2 | 프로젝트 유형별 분석 | 없음 | **부분 재사용** — Step A~D(레이아웃/스택/코드/비교) 중 Step D(1:1 비교)만 필요 |
| 2.5 | 분석 결과 보고 + 사용자 인터뷰 | **있음** — 대규모 변화 시 사용자 방향 선택 필수 | **불가** — 사용자 확인 대기가 자동화를 차단 |
| 3 | 변경 사항 정리 + 사용자 검토 | **있음** — 섹션(section) 단위 승인/거부, 미등록 문서 용도 인터뷰 | **불가** — 섹션별 개별 승인이 자동화를 차단 |
| 4 | 플랫폼 파일 갱신 + 완료 | 없음 (MEMORY.md 갱신, DONE.md 작성) | **불필요** — post-commit 스코프 밖 |

**핵심 발견**: opi는 Phase 2.5와 3에서 **사용자 인터뷰/승인이 필수**인 interactive 스킬이다. post-commit 자동화에서 이 인터랙션을 제거하면 opi의 핵심 안전장치(사용자 검토)가 무력화된다. 분석 로직(Phase 1~2)은 개념적으로 재사용 가능하나, 실제로는 opi SKILL.md 내부에 절차적으로 엮여 있어 모듈 단위 추출이 불가하다.

### 1-2. Claude Code PostToolUse 훅 동작 방식

**훅 이벤트 종류**: `PreToolUse`, `PostToolUse`, `Stop`, `SubagentStop`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `PreCompact`, `Notification`

**PostToolUse 훅 구조** (settings.json 기준):

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "스크립트 경로 또는 인라인 명령",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**matcher 문법**:
- 도구 이름 기준 매칭: `"Bash"`, `"Write"`, `"Edit"`, `"Write|Edit"` 등
- 정규식 사용 가능: `".*"` (모든 도구)
- 빈 문자열 `""`: 모든 이벤트에 매칭 (현재 claude-hooks.json에서 사용 중)
- **중요**: matcher는 **도구 이름**(Bash, Write 등)에 매칭한다. `Bash(git commit*)` 같은 세부 명령 필터링은 matcher 레벨이 아니라 **훅 스크립트 내부에서 `tool_input`을 파싱**하여 수행해야 한다.

**훅 스크립트에서 tool_input 접근**:
- 훅 커맨드에 stdin으로 JSON 컨텍스트가 전달된다
- `jq -r '.tool_input.command'`로 실행된 Bash 명령을 추출 가능
- `tool_output`으로 명령의 출력 결과도 접근 가능

**훅 실행 컨텍스트**:
- 현재 작업 디렉토리는 프로젝트 루트
- 환경변수: `CLAUDE_ENV_FILE` (세션 환경 변수 영속화용)
- 훅 타임아웃: 기본값 존재, `timeout` 필드로 조정 가능

**훅 output → 세션 주입**:
- `type: "command"` 훅은 stdout을 세션에 반환한다
- `type: "prompt"` 훅은 프롬프트 텍스트를 Claude에게 주입한다
- PostToolUse의 경우, 훅 출력이 Claude의 다음 응답 컨텍스트에 포함된다

### 1-3. 훅 → claude CLI 호출 가능성 및 방법

**방법 A: PostToolUse `type: "prompt"` 훅 사용 (권장)**

PostToolUse 훅에서 `type: "prompt"`를 사용하면, git commit 감지 시 Claude 세션 내에서 프롬프트를 주입할 수 있다. 이 방식은 **현재 세션 컨텍스트를 그대로 활용**한다.

```json
{
  "PostToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "bash ~/.opal/hooks/post-commit-check.sh",
          "timeout": 10
        }
      ]
    }
  ]
}
```

`post-commit-check.sh`가 git commit을 감지하면 → 스킬 프롬프트를 출력 → Claude가 해당 프롬프트를 읽고 docs 업데이트를 자율 수행.

**방법 B: 훅에서 `claude -p` 별도 프로세스 실행**

```bash
claude -p "커밋 후 docs/ 업데이트를 수행해줘" --allowedTools "Read,Write,Edit,Bash(git:*)"
```

이 방식은 **별도 세션**이 생성되어 현재 대화 컨텍스트를 잃는다. 비용 증가 + 세션 분리 문제.

**방법 C: 훅에서 `type: "prompt"` + 스킬 SKILL.md 참조 지시**

가장 자연스러운 패턴. PostToolUse 훅의 prompt 타입에서 "SKILL.md를 읽고 실행하라"고 지시.

**권장: 방법 A + C 혼합** — command 훅으로 git commit 여부를 필터링하고, 조건 충족 시 prompt를 통해 현재 세션 Claude에게 스킬 실행을 지시.

### 1-4. 현재 배포 구조 (install-mac.sh)

**훅 배포 흐름**:
1. 소스: `opal/core/hooks/claude-hooks.json`
2. `merge_hooks_config()` 함수가 `~/.claude/settings.json`의 `hooks` 키에 이벤트별로 병합
3. 병합 방식: 이벤트별(`SubagentStop`, `Stop` 등) **덮어쓰기** (`data['hooks'][event] = rules`)

**새 훅 추가 시**: `claude-hooks.json`에 `PostToolUse` 이벤트를 추가하면, `install-mac.sh` 실행 시 자동으로 `~/.claude/settings.json`에 병합된다. 별도 배포 스크립트 수정 불필요 (merge_hooks_config가 이미 범용적).

**주의**: 현재 merge 방식이 이벤트 키 단위 덮어쓰기(`data['hooks'][event] = rules`)이므로, 같은 이벤트에 사용자 커스텀 훅이 있으면 덮어쓸 위험이 있다. 하지만 현재는 사용자가 PostToolUse 훅을 사용하지 않으므로 문제 없음.

---

## 2. 핵심 설계 결정

### 2-1. opi 확장 vs 신규 스킬 비교

| 기준 | opi 확장 (`--post-commit` 플래그) | 신규 스킬 (`opal-post-commit-sync`) |
|------|----------------------------------|-------------------------------------|
| **재사용성** | Phase 1~2 분석 로직 재사용 가능 (이론적) | 필요한 분석만 경량으로 자체 구현 |
| **복잡도** | 높음 — 기존 6-Phase 흐름에 분기 추가, 인터랙티브/비인터랙티브 모드 공존 | 낮음 — 단일 목적, 단순한 파이프라인 |
| **유지보수** | 리스크 높음 — opi 변경 시 post-commit 경로도 영향. 두 모드의 동작 차이를 항상 고려해야 함 | 독립적 — opi 변경과 무관. 각 스킬이 자체 생애주기 |
| **단일 책임** | 위반 — opi의 책임: "사용자와 대화하며 프로젝트 환경 구축". post-commit 자동화는 다른 책임 | 준수 — "커밋 후 변경 파일 기반 docs 자동 업데이트"라는 단일 책임 |
| **테스트 용이성** | 낮음 — opi 전체를 실행해야 post-commit 경로 테스트 가능 | 높음 — 독립 실행/테스트 가능 |
| **훅 연동** | 어색함 — opi는 세션 시작 시 호출하는 스킬. 훅에서 플래그 부여하여 호출하는 패턴이 부자연스러움 | 자연스러움 — 훅 전용 경량 스킬로 설계 |

### 2-2. 권장 방향: **신규 스킬 (`opal-post-commit-sync`)** 생성

**근거**:
1. **단일 책임 원칙**: opi는 "사용자와 대화하며 프로젝트 문서를 관리"하는 interactive 스킬. post-commit 자동 동기화는 "커밋 변경 기반 docs 자동 업데이트"라는 별도 책임이다.
2. **인터랙티브 제거 불가**: opi의 핵심 가치(Phase 2.5 사용자 방향 선택, Phase 3 섹션별 승인)를 건너뛰면 안전장치가 무력화된다. `--post-commit` 플래그로 이를 우회하는 것은 opi 설계를 훼손한다.
3. **분석 로직의 실질 재사용 불가**: opi의 분석은 SKILL.md 절차에 인라인되어 있어 함수 호출처럼 추출할 수 없다. 어차피 새로 작성해야 한다.
4. **스코프 차이**: opi는 프로젝트 전체를 분석하지만, post-commit은 **변경된 파일만** 분석하면 된다. 훨씬 좁은 스코프.

### 2-3. 스킬 동작 흐름

```
[커밋 감지]
PostToolUse(Bash) 훅
  → post-commit-check.sh가 stdin에서 tool_input.command 파싱
  → git commit 패턴 매칭 확인
  → 매칭 실패: exit 0 (무시)
  → 매칭 성공: docs 업데이트 필요 여부 판단용 메시지 출력

[변경 파일 분석]
  → git diff --name-only HEAD~1 HEAD로 변경 파일 목록 추출
  → 변경 파일 중 docs/ 관련 영향이 있는 코드 파일 필터링
    (docs/ 자체 변경은 제외 — 이미 직접 수정했으므로)
  → 영향 있는 파일이 없으면: "docs 업데이트 불필요" → 종료

[docs 업데이트 대상 선별]
  → PROJECT.md의 문서 테이블에서 등록된 docs 목록 확인
  → 변경된 코드 영역과 각 docs의 커버 범위를 매칭
    (예: routes/ 변경 → BACKEND.md, components/ 변경 → FRONTEND.md)
  → 업데이트 대상 docs 목록 생성

[agentic 실행]
  → 각 대상 doc에 대해: 현재 내용 Read → 변경 코드 분석 → 차이 반영하여 Edit
  → 변경 내역 요약 출력 (사용자에게 결과 보고)
  → 사용자가 확인 후 별도 커밋 (자동 커밋은 하지 않음)
```

---

## 3. 구현 범위 (파일 목록)

### 3-1. 생성할 파일

| # | 파일 경로 (소스) | 배포 경로 | 역할 |
|---|-----------------|----------|------|
| 1 | `opal/skills/opal-post-commit-sync/SKILL.md` | `~/.opal/skills/opal-post-commit-sync/SKILL.md` | 스킬 정의 — 동작 흐름, 분석 규칙, docs 매핑 규칙 |
| 2 | `opal/core/hooks/scripts/post-commit-check.sh` | `~/.opal/hooks/post-commit-check.sh` | 훅 스크립트 — stdin에서 tool_input 파싱, git commit 패턴 매칭, 조건 충족 시 프롬프트 출력 |

### 3-2. 수정할 파일

| # | 파일 경로 | 수정 내용 |
|---|----------|----------|
| 1 | `opal/core/hooks/claude-hooks.json` | `PostToolUse` 이벤트 추가 — matcher: `"Bash"`, command: `post-commit-check.sh` 실행 |
| 2 | `scripts/install-mac.sh` | 훅 스크립트 파일 배포 로직 추가 (`post-commit-check.sh` → `~/.opal/hooks/`) |
| 3 | `opal/core/references/skills.md` | 신규 스킬 레지스트리 등록 (있는 경우) |

### 3-3. 각 파일 역할 상세

**SKILL.md** (핵심):
- 트리거: PostToolUse 훅에서 호출됨 (직접 `//` 호출도 가능하게 설계)
- 입력: 변경 파일 목록 (git diff)
- 처리: 변경 파일 → docs 매핑 → 해당 docs 읽기 → 차이 분석 → 업데이트 제안
- 출력: 업데이트된 docs 내용 + 변경 요약
- agentic 모드: 사용자 확인 없이 분석/제안까지 자율 수행, 실제 Write는 사용자 확인 후

**post-commit-check.sh**:
```bash
#!/bin/bash
# stdin으로 PostToolUse 컨텍스트(JSON)가 들어옴
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

# git commit 패턴 매칭
if echo "$COMMAND" | grep -qE '^git commit'; then
  # docs 업데이트 스킬 실행을 Claude에게 지시
  echo "커밋이 감지되었습니다. opal-post-commit-sync 스킬에 따라 docs/ 업데이트 필요 여부를 확인하세요."
fi
exit 0
```

**claude-hooks.json 수정 후 예상**:
```json
{
  "PostToolUse": [
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "bash ~/.opal/hooks/post-commit-check.sh",
          "timeout": 10
        }
      ]
    }
  ],
  "SubagentStop": [ ... ],
  "Stop": [ ... ]
}
```

---

## 4. 미결 사항 / 캡틴 확인 필요

### 4-1. 훅 출력 → Claude 행동 연결 방식

PostToolUse `type: "command"` 훅의 stdout이 Claude 세션에 어떻게 반영되는지 실전 검증이 필요하다.

- **낙관적 시나리오**: stdout 메시지가 Claude의 다음 turn 컨텍스트에 삽입되어, Claude가 SKILL.md를 읽고 자율 실행
- **비관적 시나리오**: stdout이 단순 로그로만 처리되어 Claude 행동을 트리거하지 못함
- **대안**: `type: "prompt"` 훅을 사용하면 확실히 Claude에게 프롬프트로 전달됨. 다만 모든 Bash 실행마다 prompt가 평가되는 성능 이슈 가능

**캡틴 확인 필요**: 실제 PostToolUse 훅의 stdout/prompt 동작을 간단한 테스트로 먼저 검증할 것인지, 아니면 `type: "prompt"` 방식으로 바로 구현할 것인지.

### 4-2. 자동 업데이트 범위 제한

- post-commit-sync가 자동으로 **Write/Edit까지** 수행할 것인지, 아니면 **분석 + 제안만** 하고 사용자 승인을 기다릴 것인지.
- 전자: 완전 자동화 (리스크: 잘못된 업데이트)
- 후자: 반자동 (리스크: 사용자가 무시할 수 있음)
- **권장**: 분석 + 제안까지 자동, Write는 사용자 확인 후. 단, 캡틴이 "완전 자동"을 선호하면 옵션으로 제공.

### 4-3. 워커 세션에서의 동작

- 워커(`[WORKER]`)가 커밋할 때도 훅이 발동한다. 워커 세션에서 post-commit-sync가 실행되면 워커의 작업 흐름을 방해할 수 있다.
- **권장**: 훅 스크립트에서 환경변수 또는 플래그로 워커 세션을 감지하여 스킵하는 로직 추가.

### 4-4. install-mac.sh의 hooks 디렉토리 배포

- 현재 install-mac.sh는 hooks 스크립트 **파일**을 별도로 배포하는 로직이 없다 (JSON만 merge).
- `~/.opal/hooks/` 디렉토리 생성 + 스크립트 복사 로직을 추가해야 한다.
- 기존 `install_dir` 함수를 재사용 가능.

### 4-5. merge_hooks_config 덮어쓰기 문제

- 현재 `merge_hooks_config`는 이벤트 키 단위로 덮어쓴다 (`data['hooks'][event] = rules`).
- 향후 사용자가 자신만의 PostToolUse 훅을 추가하면 OPAL 배포 시 삭제될 위험.
- **장기 과제**: merge 방식을 배열 병합(append)으로 개선하는 것이 바람직. 이번 태스크에서는 현재 방식 유지.

---

## 5. 실행 체크리스트 (향후 구현 태스크용)

### Step 1: 훅 동작 검증 (선행 검증)
- [ ] 간단한 PostToolUse `type: "command"` 훅을 settings.json에 수동 추가
- [ ] git commit 실행 후 훅 stdout이 Claude 세션에 어떻게 반영되는지 확인
- [ ] `type: "prompt"` 방식도 테스트하여 비교
- [ ] 결과에 따라 최종 훅 타입 결정

### Step 2: 훅 스크립트 작성
- [ ] `opal/core/hooks/scripts/post-commit-check.sh` 작성
- [ ] stdin JSON 파싱 (jq 사용)
- [ ] git commit 패턴 매칭 로직 구현
- [ ] 워커 세션 감지 로직 추가 (환경변수 체크)
- [ ] 실행 권한 설정 (`chmod +x`)

### Step 3: claude-hooks.json 수정
- [ ] `PostToolUse` 이벤트 항목 추가
- [ ] matcher: `"Bash"`, command: 훅 스크립트 경로
- [ ] timeout 설정

### Step 4: SKILL.md 작성
- [ ] 스킬 YAML frontmatter (name, description, triggers, version)
- [ ] 동작 흐름 정의 (변경 파일 분석 → docs 매핑 → 업데이트 제안)
- [ ] docs 매핑 규칙 정의 (어떤 코드 변경이 어떤 docs에 영향을 주는지)
- [ ] 출력 형식 정의 (변경 요약 + 업데이트 내용)

### Step 5: install-mac.sh 수정
- [ ] `~/.opal/hooks/` 디렉토리 생성 로직 추가
- [ ] 훅 스크립트 파일 복사 로직 추가
- [ ] 실행 권한 자동 설정

### Step 6: 스킬 레지스트리 등록
- [ ] `opal/core/references/skills.md`에 opal-post-commit-sync 추가
- [ ] 트리거, 약식명 등록

### Step 7: 통합 테스트
- [ ] install-mac.sh 실행 후 배포 확인
- [ ] 실제 커밋 → 훅 발동 → 스킬 실행 → docs 업데이트 제안 확인
- [ ] 워커 세션에서 커밋 시 스킵 확인
- [ ] docs/ 변경만 있는 커밋에서 불필요한 트리거 방지 확인

---

## 6. QA 체크리스트

- [x] PLAN.md가 TASK.md의 4개 요구사항(opi 분석, 훅 연결 방식, 설계 방향, 구현 범위)을 모두 충족하는가
  - §1-1 opi Phase별 분석, §1-2~1-3 훅 연결 방식, §2 설계 방향, §3 구현 범위 — 4개 모두 커버됨
- [x] opi 확장 vs 신규 스킬 비교가 구체적 근거와 함께 제시되어 있는가
  - §2-1 비교표에 재사용성/복잡도/유지보수/단일책임/테스트용이성/훅연동 6개 기준별 구체 근거 명시
- [x] Claude Code PostToolUse 훅의 matcher/실행 방식 설명이 구체적인가
  - §1-2에서 matcher 문법(도구명 기준, 정규식), stdin JSON 파싱, tool_input 접근, command/prompt 타입 차이 모두 설명됨
  - 실전 검증 미완 여부는 §4-1 미결 사항으로 명시 처리됨 (허용)
- [x] 구현 파일 목록이 소스 경로 + 배포 경로 모두 포함하는가
  - §3-1 생성 파일 2개(SKILL.md, post-commit-check.sh), §3-2 수정 파일 3개 — 소스/배포 경로 쌍 완전
- [x] install-mac.sh 배포 경로가 기존 패턴과 일관성이 있는가
  - `~/.opal/hooks/`는 기존 `~/.opal/skills/`, `~/.opal/agents/`, `~/.opal/tools/` 패턴과 일관성 있음
  - §4-4에서 기존 `install_dir` 함수 재사용 언급. 단, §3-2 수정 내용란에 구체 구현 방식 미기재 (경미한 결함, 허용)
- [x] 미결 사항이 캡틴이 판단할 수 있도록 명확히 정리되어 있는가
  - §4에서 4-1~4-5 총 5개 미결 사항, 각각 시나리오/권장 방향/캡틴 확인 필요 포인트 명시
- [x] 실행 체크리스트가 의존관계를 고려한 순서로 작성되어 있는가
  - Step 1(훅 선행 검증) → Step 2(스크립트) → Step 3(hooks.json) → Step 4(SKILL.md) → Step 5(install) → Step 6(레지스트리) → Step 7(통합테스트)
  - 훅 동작 미검증 시 구현 방향이 바뀔 수 있으므로 Step 1 선행 분리는 적절

**QA 결과: PASS** (7/7 통과, 경미한 결함 1건 허용)
