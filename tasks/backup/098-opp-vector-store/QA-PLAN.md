# QA: PLAN — OPAL Vector Store

> 검토일: 2026-04-08 | 판정: **Pass (조건부 주의)**

---

## 1. 요약

PLAN.md는 TASK.md의 6개 요구사항(R1~R6)을 전반적으로 충실하게 반영하고 있으며, DB 스키마·API·CLI 인터페이스가 구체적으로 설계되어 있다. 11개 Step의 순서와 의존성도 명확하다. 다만 아래 3가지 주의 사항이 존재하며, 이를 EXECUTE 전에 인지하고 진행하면 된다.

---

## 2. 검증 결과 (GP-1~GP-6 항목별)

### GP-1. 즉시 실행 가능성 — **Pass**

- 11개 Step이 의존성 순서에 따라 번호로 정렬되어 있고, 각 Step에 **완료 기준(테스트 명령)**이 명시되어 있다.
- Step 1(의존성 파일 정의)부터 시작하여 Step 11(install-mac.sh 수정)까지 막힘 없이 순차 실행 가능하다.
- 단, Step 8(Node.js 폴백)의 완료 기준 "Python 인덱싱 → Node.js 검색 상호 호환"은 Python 구현(Step 2~7) 완료 후에만 검증 가능하므로 실질적 의존성은 Step 1 이상이지만 기술적으로는 Step 7 이후를 전제한다. 명시되어 있지 않아 **경미한 누락**.

### GP-2. 의존성 순서 — **Pass**

- Step 의존성이 명시되어 있으며 논리적으로 정확하다.
  - Step 2(db.py) → Step 1 의존
  - Step 3(embedder.py) → Step 1 의존
  - Step 4(chunker.py) → 의존 없음 (독립)
  - Step 5(commands.py) → Step 2, 3, 4 의존
  - Step 6(vector-store.py) → Step 5 의존
  - Step 7(run.sh) → Step 6 의존
  - Step 8(Node.js) → Step 1 의존 (※ 상호 호환 테스트는 Step 7 이후)
  - Step 9(훅) → Step 7 의존
  - Step 10(문서 수정) → Step 7 의존
  - Step 11(install-mac.sh + ARCHITECTURE.md) → Step 7, 8, 9, 10 의존
- Step 8의 의존을 "Step 1"로만 표기한 것은 부정확하다. 상호 호환 완료 기준 관점에서는 Step 7 이후가 맞으나, 파일 생성 자체는 Step 1 의존으로 가능하므로 **구현/테스트 분리가 필요하나 치명적이지 않음**.

### GP-3. TASK 반영 — **Pass**

| 요구사항 | PLAN 반영 여부 | 비고 |
|---------|-------------|------|
| R1: vector-store 도구 구현 (Python + Node.js + run.sh) | Pass | Step 1~8, §3.1 파일 목록 13개 |
| R2: CLI 명령 6개 + --json 출력 | Pass | §2.4 JSON 형식, Step 5 commands.py 6개 명령 |
| R3: 네임스페이스 설계 (opal / {project}, tasks TASK.md+STATE.md) | Pass | §2.5 네임스페이스 설계, DONE.md 제외 명시 |
| R4: install-mac.sh 통합 (의존성 + 초기 인덱싱 + 모델 프리로드 + 훅 머지) | Pass | §3.7 install_vector_store 함수 전체 구현 |
| R5: opal-pm.md §3 Step 2 통합 | Pass | §3.5, Step 10 |
| R6: skill-registry 시맨틱 폴백 | Pass | §3.6, Step 10 |

- TASK.md의 모든 6개 요구사항이 PLAN에 반영됨.
- R3 세부: TASK.md §배경 분석에서 `tasks/*/TASK.md + STATE.md`를 명시하고 DONE.md는 제외한다고 했는데, §2.5 네임스페이스 설계에 `tasks/*/TASK.md`, `tasks/*/STATE.md`가 명시되고 `DONE.md 제외`가 §1.2 비교표에도 반영됨.

### GP-4. 파일 목록 완전성 — **Pass (경미한 누락 1건)**

- **신규 생성 13개** 파일이 §3.1 테이블에 열거됨.
- **수정 5개** 파일(`claude-hooks.json`, `opal-pm.md`, `AGENT.md`, `install-mac.sh`, `ARCHITECTURE.md`)이 명시됨.
- **삭제 없음** 명시됨.
- **경미한 누락**: `opal/tools/vector-store/.gitignore` (전용 venv `.venv/` 폴더 git 제외 처리) 파일이 목록에 없다. 전용 venv를 `opal/tools/vector-store/.venv`에 생성하므로, 해당 경로를 git에서 제외하는 `.gitignore`가 없으면 대규모 바이너리가 git에 추가될 위험이 있다.

### GP-5. 설계 구체성 — **Pass**

- **DB 스키마**: §2.2에 `chunks` 테이블 + `vec_chunks` 가상 테이블 DDL이 완전히 명시됨. 컬럼 타입, 인덱스, UNIQUE 제약 포함.
- **API 인터페이스**: §2.3 `run.sh` 진입점 코드, §2.4 JSON 출력 형식, §3.4 훅 설정 JSON이 구체적으로 제시됨.
- **CLI 명령 인터페이스**: `index`, `search`, `add`, `update`, `delete`, `status` 6개 명령. `--namespace`, `--dir`, `--query`, `--top-k`, `--file`, `--json`, `--pattern` 플래그가 §3.5/3.6의 예시 명령에서 확인됨.
- **주의**: `--pattern` 플래그가 §3.7 install-mac.sh 코드에서 사용되지만(`--pattern "skills/*/SKILL.md"`), R2 CLI 명령 인터페이스 설명이나 Step 5~6에서 이 플래그가 명시적으로 정의되지 않음. EXECUTE 시 CLI 파서에 반드시 포함해야 함.

### GP-6. 체크리스트 커버리지 — **Pass (경미한 누락 1건)**

- §5 실행 체크리스트: 11개 Step에 각 파일 생성 및 테스트 항목이 빠짐없이 포함됨.
- §6 QA 체크리스트: 기능 테스트(12항목), 런타임 호환성(5항목), 통합 테스트(4항목), 코드 품질(4항목)으로 요구사항 전반을 커버함.
- **경미한 누락**: QA 체크리스트에 `.gitignore` 존재 확인 항목이 없음.
- **경미한 누락**: `run.sh status --json` 플래그 동작 여부를 검증하는 QA 항목이 없음 (status 명령은 `--help`만 언급됨).

---

## 3. 지적 사항

### 3-A. `.gitignore` 누락 (중요도: 보통)

`opal/tools/vector-store/.venv`는 Python 전용 venv로 수 GB에 달한다. §3.1 파일 목록에 `opal/tools/vector-store/.gitignore`가 없어, EXECUTE 시 git에 대용량 바이너리가 포함될 수 있다. Step 1 또는 Step 7에서 `.gitignore` 생성을 추가해야 한다.

```
# 추가 권고 파일: opal/tools/vector-store/.gitignore
.venv/
node_modules/
__pycache__/
*.pyc
```

### 3-B. `--pattern` 플래그 미정의 (중요도: 보통)

§3.7 install-mac.sh 코드에서 `run.sh index --pattern "skills/*/SKILL.md"` 형식을 사용하지만, `index` 명령의 CLI 파서(Step 5~6)에서 `--pattern` 플래그가 명시되지 않았다. EXECUTE 시 `argparse` 정의에 `--pattern` (복수 허용)을 반드시 추가해야 한다.

### 3-C. `merge_hooks_config` 동일 이벤트 덮어쓰기 리스크 (중요도: 낮음)

§7 리스크 테이블에서 "PostToolUse는 신규 이벤트이므로 충돌 없음"이라고 기술하고 있으나, 실제 `merge_hooks_config` 구현은 `data['hooks'][event] = rules`로 **이벤트 키 단위 완전 교체**를 수행한다. 현재는 PostToolUse가 신규이므로 안전하지만, 향후 다른 PostToolUse 훅이 추가된 경우 덮어쓰기가 발생한다. PLAN의 리스크 기술은 사실과 부합하나, 장기적으로 머지 로직의 배열 병합(append) 개선을 별도 태스크로 고려할 것을 권고한다.

### 3-D. Step 8 의존성 표기 부정확 (중요도: 낮음)

Step 8의 의존을 "Step 1"로만 표기하였으나, "Python 인덱싱 → Node.js 검색 상호 호환" 완료 기준은 Step 7 이후에만 검증 가능하다. 혼동 방지를 위해 "의존: Step 1 (파일 생성) / 상호 호환 테스트는 Step 7 이후"로 명시하는 것이 바람직하다.

---

## 4. 교차 참조 검증

| 참조 대상 | 실제 존재 여부 | 비고 |
|----------|-------------|------|
| `opal/tools/skill-registry/skill-registry.js` | 존재 확인 | 패턴 참조용 |
| `opal/tools/xlsx-tool/run.sh` | 존재 확인 | run.sh 패턴 참조용 |
| `opal/core/hooks/claude-hooks.json` | 존재 확인 | SubagentStop/Stop 훅 포함, PostToolUse 없음 (예상대로) |
| `opal/core/references/opal-pm.md` | 존재 확인, §3 Step 2 확인 | vector-store 절차 아직 미추가 (예상대로) |
| `opal/core/AGENT.md` | 존재 확인, skill-registry 섹션 확인 | 시맨틱 폴백 아직 미추가 (예상대로) |
| `scripts/install-mac.sh` | 존재 확인, `merge_hooks_config` 함수 확인 | vector-store 항목 아직 미추가 (예상대로) |
| `docs/ARCHITECTURE.md` | 존재 확인 | tools/ 테이블에 vector-store 미반영 (예상대로) |
| `tasks/backup/059-opal-vector-store/` | 존재 확인 | PLAN/QA-PLAN 선행 설계 참조용 |
| `opal/tools/requirements.txt` | 존재 확인 | §1.1에서 "확인 필요"로 명시됨 (전용 venv 결정으로 수정 불필요 확정) |

- `docs/ARCHITECTURE.md` tools/ 테이블(`tools/` 행)이 실제로는 `| tools/ | CLI 도구 (skill-registry/, xlsx-tool/, check-env.js, requirements.txt) |` 형태로 존재하여 §3.1 수정 대상(#18)과 일치한다.
- `merge_hooks_config`는 이벤트 키 단위로 덮어쓰므로 PostToolUse(신규 키)는 기존 SubagentStop/Stop(다른 키)에 영향을 주지 않는다. PLAN의 리스크 분석이 올바르다.

---

## 5. 판정

**Pass (조건부 주의)**

PLAN.md는 TASK.md의 R1~R6 전체를 반영하고, 설계 구체성·파일 목록·실행 순서·QA 체크리스트 모두 충분한 수준이다. EXECUTE를 진행할 수 있다.

EXECUTE 전 반드시 인지해야 할 항목:

1. **[필수]** Step 1에서 `opal/tools/vector-store/.gitignore`를 생성하여 `.venv/`, `node_modules/`, `__pycache__/`를 git에서 제외한다.
2. **[필수]** Step 5~6 구현 시 `index` 명령에 `--pattern` 플래그(복수 허용)를 argparse에 포함한다.
3. **[참고]** `merge_hooks_config`는 이벤트 키 단위 완전 교체 방식이므로 현재는 안전하나, 향후 PostToolUse 훅이 추가될 경우 배열 병합 방식으로 개선이 필요하다.
