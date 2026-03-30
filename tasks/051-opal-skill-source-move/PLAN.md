# PLAN: OPAL 전용 스킬 소스 디렉토리 이동

> 작성일: 2026-03-30
> 입력: TASK.md
> 출력: PLAN.md

## 1. 현황 조사

### 관련 파일

| 파일 | 역할 | 변경 필요 |
|------|------|----------|
| `skills/` (20개 디렉토리) | 이동 대상 스킬 소스 | 이동 (삭제) |
| `opal/skills/` (4개 기존) | 이동 목적지 (기존 스킬 유지) | 이동 대상 수신 |
| `scripts/install-mac.sh` | 배포 스크립트 | **수정 필요** |
| `opal/core/references/opal-skills-registry.json` | 스킬 레지스트리 JSON | 변경 불필요 |
| `opal/core/references/opal-harness.md` | 하네스 (스킬 탐색 경로) | 변경 불필요 |
| `opal/core/references/skills.md` | 스킬 목록 (Markdown) | 변경 불필요 |
| `opal/core/references/agents.md` | 에이전트 레지스트리 | 변경 불필요 |
| `opal/tools/skill-registry/skill-registry.js` | 스킬 레지스트리 CLI | 변경 불필요 |
| `CLAUDE.md` | 소스 구조 설명 | **수정 필요** |
| `README.md` | 소스 구조 설명 | **수정 필요** |
| `docs/ARCHITECTURE.md` | 아키텍처 문서 | **수정 필요** |
| `docs/CONVENTIONS.md` | 컨벤션 문서 | 변경 불필요 |

### 현재 상태

**skills/ 디렉토리 (25개)**:
- 잔류 대상 5개: api-analyzer, interview, ui-designer, web-to-markdown, wireframe-builder
- 이동 대상 20개:
  - 오케스트레이터 6개: opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe, opal-pilot-write, opal-pilot-write-tech, opal-project-pilot
  - dev 단계 7개: op-dev-analysis, op-dev-plan, op-dev-todo, op-dev-execute, op-dev-test-scenario, op-dev-qa, op-dev-wireframe
  - 범용 단계 4개: op-task, op-task-plan, op-task-execute, op-task-qa
  - OPAL 전용 3개: opal-project-init, opal-agent-creator, opal-skill-creator

**opal/skills/ 디렉토리 (4개, 유지)**:
- opal-onboarding, opal-orchestrator, opal-project-dev-pilot, opal-skill-manager

**install-mac.sh 배포 로직** (핵심):
- 280-283행: `$FRAMEWORK_ROOT/skills` 전체를 `~/.opal/skills/`로 복사
- 286-295행: `$opal_dir/skills/*/`를 개별적으로 `~/.opal/skills/{name}`으로 복사
- 이동 후: skills/에 5개만 남으므로, opal/skills/에서 24개(기존 4 + 신규 20)가 복사되어야 함
- 50행: `detect_framework_root()`에서 `skills` 디렉토리 존재를 검증 — 잔류 5개가 있으므로 문제 없음

**opal-skills-registry.json**: 모든 `paths` 필드가 배포 경로(`{project}/.opal/skills/`, `~/.opal/skills/`)만 사용. 소스 경로를 참조하지 않으므로 변경 불필요.

**opal-harness.md**: 스킬 탐색 경로가 배포 경로만 사용 (`{프로젝트}/.opal/skills/op-dev-{stage}/SKILL.md`, `~/.opal/skills/op-dev-{stage}/SKILL.md`). 변경 불필요.

**skills.md, agents.md**: 배포 경로 기반. 변경 불필요.

**skill-registry.js**: `getReferencesDir()`가 `~/.opal/references/` 또는 `opal/core/references/`에서 레지스트리를 로드. 스킬 소스 경로를 직접 참조하지 않음. 변경 불필요.

**docs/CONVENTIONS.md**: `skills/{skill-name}/` 패턴을 스킬 구조 예시로 사용. 이는 범용 구조 설명이므로 변경 불필요 (standalone 스킬도 동일 구조).

### 영향 범위

| 영향 영역 | 설명 |
|-----------|------|
| **install-mac.sh** | skills/ 복사 시 5개만 복사됨. opal/skills/에서 24개 복사. 배포 결과는 동일해야 함 |
| **CLAUDE.md 소스 구조** | `skills/` 하위 목록이 크게 줄고, `opal/skills/` 하위가 늘어남 |
| **README.md 소스 구조** | 동일 |
| **docs/ARCHITECTURE.md** | 디렉토리 구조 + 배포 모델 도표 + Global Layer 스킬 수 갱신 |
| **런타임** | 배포 대상(~/.opal/skills/)이 동일하므로 런타임 영향 없음 |

---

## 2. 구현 계획

### 파일 변경 계획

#### 신규 생성

해당 없음.

#### 수정

| # | 파일 경로 | 변경 내용 |
|---|----------|----------|
| 1 | `scripts/install-mac.sh` | 배포 로직 갱신: skills/에서 standalone 5개만 복사, opal/skills/에서 24개 복사 |
| 2 | `CLAUDE.md` | 소스 구조 트리에서 skills/ → 5개로 축소, opal/skills/ → 24개로 확대 |
| 3 | `README.md` | 소스 구조 트리 갱신 (skills/ 5개, opal/skills/ 24개) |
| 4 | `docs/ARCHITECTURE.md` | 디렉토리 구조, Global Layer 스킬 수, 배포 모델 도표 갱신 |

#### 삭제 (이동)

| # | 파일 경로 | 사유 |
|---|----------|------|
| 1-20 | `skills/{20개 스킬 디렉토리}` | `opal/skills/`로 이동 |

### 구현 순서

| 순서 | 작업 | 파일 | 예상 난이도 |
|------|------|------|-----------|
| 1 | 스킬 디렉토리 이동 | skills/ → opal/skills/ (20개) | 낮음 (git mv) |
| 2 | install-mac.sh 갱신 | scripts/install-mac.sh | 중간 |
| 3 | CLAUDE.md 갱신 | CLAUDE.md | 낮음 |
| 4 | README.md 갱신 | README.md | 낮음 |
| 5 | docs/ARCHITECTURE.md 갱신 | docs/ARCHITECTURE.md | 낮음 |
| 6 | 배포 검증 | install-mac.sh 드라이런 | 낮음 |

### 핵심 설계

#### 1. 스킬 디렉토리 이동 (git mv)

`git mv`로 20개 디렉토리를 이동한다. 이동 후 소스 구조:

```
skills/                    ← standalone 5개만 잔류
├── api-analyzer/
├── interview/
├── ui-designer/
├── web-to-markdown/
└── wireframe-builder/

opal/skills/               ← 기존 4개 + 이동 20개 = 24개
├── opal-onboarding/        (기존)
├── opal-orchestrator/      (기존)
├── opal-project-dev-pilot/ (기존)
├── opal-skill-manager/     (기존)
├── opal-pilot-dev/         (이동)
├── opal-pilot-dev-short/   (이동)
├── opal-pilot-dev-wireframe/ (이동)
├── opal-pilot-write/       (이동)
├── opal-pilot-write-tech/  (이동)
├── opal-project-pilot/     (이동)
├── op-dev-analysis/        (이동)
├── op-dev-plan/            (이동)
├── op-dev-todo/            (이동)
├── op-dev-execute/         (이동)
├── op-dev-test-scenario/   (이동)
├── op-dev-qa/              (이동)
├── op-dev-wireframe/       (이동)
├── op-task/                (이동)
├── op-task-plan/           (이동)
├── op-task-execute/        (이동)
├── op-task-qa/             (이동)
├── opal-project-init/      (이동)
├── opal-agent-creator/     (이동)
└── opal-skill-creator/     (이동)
```

#### 2. install-mac.sh 갱신

현재 로직:
```bash
# 280-283: skills/ 전체 → ~/.opal/skills/ (install_dir로 전체 복사)
install_dir "$FRAMEWORK_ROOT/skills" "$opal_home/skills" "프레임워크 스킬 (${fw_skill_count}개)"

# 286-295: opal/skills/*/ → ~/.opal/skills/{name} (개별 복사)
for skill_dir in "$opal_dir/skills"/*/; do ...
```

변경 후 로직:
- skills/ 복사는 동일 (standalone 5개만 포함)
- opal/skills/ 복사도 동일 (24개 포함)
- 카운트 표시 메시지만 업데이트 (내용은 자동으로 맞음)
- `detect_framework_root()`의 `skills` 디렉토리 검증: 잔류 5개가 있으므로 통과

**결론: install-mac.sh는 로직 변경이 불필요하다.** 현재 코드가 이미 `skills/*`와 `opal/skills/*/`를 각각 복사하는 구조이므로, 스킬이 어느 쪽에 있든 배포 결과는 동일하다. 카운트 메시지의 숫자만 자동으로 달라진다 (find 명령으로 동적 계산).

단, 주석의 스킬 수 표시를 정확하게 갱신한다:
- 280행 주석: `프레임워크 스킬 (skills/ → ~/.opal/skills/)` → `독립 스킬 (skills/ → ~/.opal/skills/)`
- 285행 주석: `OPAL 전용 스킬 (opal/skills/ → ~/.opal/skills/)` → `OPAL 스킬 (opal/skills/ → ~/.opal/skills/)`

#### 3. CLAUDE.md 갱신

소스 구조 섹션의 `skills/` 트리를 축소하고, `opal/skills/` 트리를 확대한다.

변경 사항:
- `skills/` 하위: standalone 5개만 나열
- `opal/skills/` 하위: 기존 4개 + 오케스트레이터 6개 + dev 단계 7개 + 범용 단계 4개 + OPAL 전용 3개 = 24개

#### 4. README.md 갱신

소스 구조 섹션 (179-228행)에서:
- `skills/` 하위: standalone 5개만 나열
- `opal/skills/` 하위: 24개로 확대, 카테고리별 정리

#### 5. docs/ARCHITECTURE.md 갱신

- 58행 Global Layer 표: `프레임워크 스킬 21개 + OPAL 전용 스킬 4개` → `독립 스킬 5개 + OPAL 스킬 24개`
- 152-167행 배포 모델: `skills/*` 라인 주석을 `standalone 5개`로, `opal/skills/*`를 `OPAL 24개`로
- 171-216행 디렉토리 구조: `skills/` 하위를 standalone 5개로, `opal/skills/` 하위를 24개로

---

## 3. 실행 체크리스트

> 총 6개 Step

### Step 1: 스킬 디렉토리 이동 (20개)
- [ ] 완료
- **파일**: `skills/` → `opal/skills/` (20개 디렉토리)
- **작업 내용**: `git mv`로 20개 스킬 디렉토리를 `skills/`에서 `opal/skills/`로 이동한다. 이동 대상: opal-pilot-dev, opal-pilot-dev-short, opal-pilot-dev-wireframe, opal-pilot-write, opal-pilot-write-tech, opal-project-pilot, op-dev-analysis, op-dev-plan, op-dev-todo, op-dev-execute, op-dev-test-scenario, op-dev-qa, op-dev-wireframe, op-task, op-task-plan, op-task-execute, op-task-qa, opal-project-init, opal-agent-creator, opal-skill-creator
- **완료 기준**: `skills/`에 5개만 잔류, `opal/skills/`에 24개 존재, git status에서 renamed 확인
- **테스트**: `ls skills/ | wc -l` → 5, `ls opal/skills/ | wc -l` → 24
- **의존**: 없음

### Step 2: install-mac.sh 주석 갱신
- [ ] 완료
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: 280행 주석을 `독립 스킬`로, 285행 주석을 `OPAL 스킬`로 변경. 283행 메시지 라벨도 `독립 스킬`로 변경. 295행 메시지도 갱신.
- **완료 기준**: 주석과 메시지가 실제 내용과 일치
- **테스트**: 스크립트 문법 검증 `bash -n scripts/install-mac.sh`
- **의존**: Step 1

### Step 3: CLAUDE.md 소스 구조 갱신
- [ ] 완료
- **파일**: `CLAUDE.md`
- **작업 내용**: `### 소스 구조 (이 저장소)` 섹션의 `skills/` 트리를 standalone 5개로 축소, `opal/skills/` 트리를 24개로 확대. 컴포넌트 유형 표의 스킬 수도 갱신.
- **완료 기준**: 소스 구조 트리가 실제 디렉토리와 일치
- **테스트**: 문서의 스킬 목록과 실제 디렉토리 비교
- **의존**: Step 1

### Step 4: README.md 소스 구조 갱신
- [ ] 완료
- **파일**: `README.md`
- **작업 내용**: 소스 구조 섹션 (179-228행)의 `skills/` 트리를 standalone 5개로 축소, `opal/skills/` 트리를 24개로 확대.
- **완료 기준**: 소스 구조 트리가 실제 디렉토리와 일치
- **테스트**: 문서의 스킬 목록과 실제 디렉토리 비교
- **의존**: Step 1

### Step 5: docs/ARCHITECTURE.md 갱신
- [ ] 완료
- **파일**: `docs/ARCHITECTURE.md`
- **작업 내용**: (1) Global Layer 표 스킬 수 갱신, (2) 배포 모델 도표 주석 갱신, (3) 디렉토리 구조 트리 갱신 — skills/ 5개, opal/skills/ 24개
- **완료 기준**: 문서 내 모든 스킬 수/목록이 실제와 일치
- **테스트**: 문서의 스킬 목록과 실제 디렉토리 비교
- **의존**: Step 1

### Step 6: 배포 검증
- [ ] 완료
- **파일**: `scripts/install-mac.sh` (실행)
- **작업 내용**: `bash -n scripts/install-mac.sh`로 문법 검증. 가능하면 실제 install 실행하여 `~/.opal/skills/`에 29개(standalone 5 + OPAL 24) 스킬이 정상 배포되는지 확인.
- **완료 기준**: (1) 문법 에러 없음, (2) 배포 후 `~/.opal/skills/`에 29개 디렉토리 존재 (기존과 동일)
- **테스트**: `ls ~/.opal/skills/ | wc -l` → 29 (이동 전후 동일)
- **의존**: Step 1, Step 2

---

## 4. QA 체크리스트

### 기능 테스트
- [ ] `skills/`에 standalone 5개만 잔류하는가
- [ ] `opal/skills/`에 24개 (기존 4 + 이동 20) 존재하는가
- [ ] `git mv`로 이동하여 히스토리가 보존되는가
- [ ] `bash -n scripts/install-mac.sh` 문법 검증 통과하는가
- [ ] install-mac.sh 실행 후 `~/.opal/skills/`에 29개 배포되는가

### 일관성 테스트
- [ ] opal-skills-registry.json의 배포 경로가 여전히 유효한가 (변경 불필요 확인)
- [ ] opal-harness.md의 스킬 탐색 경로가 여전히 유효한가 (변경 불필요 확인)
- [ ] skills.md, agents.md가 변경 불필요한가 확인
- [ ] skill-registry.js가 변경 불필요한가 확인
- [ ] CLAUDE.md, README.md, ARCHITECTURE.md의 스킬 수/목록이 실제와 일치하는가

### 문서 품질
- [ ] 한국어 본문 + 영어 코드/필드명 규칙을 따르는가
- [ ] kebab-case 파일/폴더 네이밍을 따르는가

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 방안 |
|--------|------|----------|
| git mv 시 히스토리 추적 실패 | 낮음 — git은 rename detection으로 처리 | `git mv` 사용, 한 커밋에서 이동만 수행 (내용 변경 분리) |
| install-mac.sh 배포 결과 변경 | 높음 — 런타임에 스킬을 찾지 못함 | Step 6에서 배포 검증 필수 |
| 문서에서 소스 구조 누락 갱신 | 낮음 — 개발 편의 저하 | CLAUDE.md, README.md, ARCHITECTURE.md 모두 갱신 |
| opal/skills/에 기존 스킬과 이름 충돌 | 없음 — 이름 겹침 없음 확인됨 | 사전 확인 완료 |
