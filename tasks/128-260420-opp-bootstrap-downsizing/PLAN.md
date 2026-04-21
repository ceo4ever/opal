# PLAN: 부트스트랩 다운사이징 — Eager 로드 최적화 (v3 — 독립 모듈 분리)

> 작성일: 2026-04-20  
> 개정일: 2026-04-21 (v3: *-detail.md 방식 포기 → 섹션별 독립 harness 모듈 / v3.1: PM 직접 작업 docs 프리로드 규칙 추가)  
> 입력: TASK.md, MAMS 072 ANALYSIS.md, 재검토 결과  
> 출력: PLAN.md  

---

## 1. 현황 조사

### 참조 문서

| # | 유형 | 문서 | 경로 | 참조 이유 |
|---|------|------|------|----------|
| D-1 | 기획 | TASK.md | `tasks/128-260420-opp-bootstrap-downsizing/TASK.md` | 요구사항·트랙 A/B/C/D |
| D-2 | 소스 | AGENT.md | `opal/core/AGENT.md` | Eager/Lazy 절차·섹션별 분류 |
| D-3 | 소스 | opal-harness.md | `opal/core/references/opal-harness.md` | §1 Guards·§3/§4 분리 대상 |
| D-4 | 소스 | opal-pm.md | `opal/core/references/opal-pm.md` | §1+§2(Eager)·§4/§5/§7(분리) |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | strip 훅 삽입 지점 |
| D-6 | 소스 | harness/observability.md | `opal/core/references/harness/observability.md` | 기존 모듈 헤더 포맷 |
| D-7 | 소스 | 오케스트레이터 AGENT.md | `.opal/AGENT.md` | 확정 기준 #2(배포 경계) |
| D-8 | 분석 | MAMS 072 ANALYSIS.md | `mams/tasks/072-.../ANALYSIS.md` | 바이트 실측·분류 기준선 |

### 섹션별 분류 최종 확정

#### AGENT.md (~5,042 tok)

| 섹션 | 분류 | 처리 | 근거 |
|------|------|------|------|
| 부트스트랩 개요·Eager 1~7·Lazy 트리거 | 🔴 | **Eager 유지** | 세션 시작 필수 |
| 정체성 적용·핵심 역할·역할 전환 | 🔴 | **Eager 유지** | 세션 시작 필수 |
| §부트스트랩 완료 보고 | 🔴 | **Eager 유지** | 첫 응답에 출력 |
| §보고 형식 (역할 접두사 포함) | 🔴 | **Eager 유지** | 첫 응답부터 사용 |
| §프로젝트 메모리 브리핑 | 🔴 | **Eager 유지** | 첫 응답에 브리핑 |
| §주도성 | 🔴 | **Eager 유지** | 모든 상호작용에 영향 |
| §프로젝트 부트스트래퍼 자동 관리 (전체) | 🔴 | **Eager 유지** | Eager 6단계에서 실행 |
| §스킬 레지스트리 + §쌍슬래시 커맨드 | 🟡 | → **harness/skill-commands.md** | `//` 입력 시에만 필요 |
| §code-scan 활용 규칙 | 🔴 | **Eager 유지** | PM 기본 도구 — 문서·코드 검토 시 항시 적용 원칙 |
| §기억과 학습 | 🟡 | → **harness/memory-learning.md** | 메모리 쓰기 시점에만 필요 |
| §프로젝트 컨텍스트 | 🟡 | → stub (파일 목록 1줄 요약만 유지) | 133 tok, 파일 분리 실익 낮음 |
| §PM 행동 프로세스 요약 | ⚪ | **삭제** | opal-pm.md Eager로 중복 (D-6) |
| §모델 매핑 자동 적용 절차 | ⚪ | **삭제** (1줄 참조만 잔존) | opal-model-mapping.md에 있음 (D-7) |
| 변경이력 | ⚪ | **배포 시 strip** | install-mac.sh로 처리 |

#### opal-harness.md (~5,469 tok)

| 섹션 | 분류 | 처리 | 근거 |
|------|------|------|------|
| §1 Guards | 🔴 | **Eager 유지** | 세션 시작 필수 |
| §2 모듈 구조 | 🔴 | **Eager 유지** | opal-pilot-* 워커가 직접 Read·서브 하네스 로딩 규칙 |
| §0 용어 정의 | ⚪ | **삭제** | 런타임 미참조, 개발자 문서용 (TASK D-3) |
| §3 State 관리 | 🟡 | → **harness/state.md** | TASK/Gate 시점에만 필요 |
| §4 TASK 공통 프로세스 | 🟡 | → **harness/task-process.md** | TASK 진입 시에만 필요 |
| §5~§8 | 🟡 | **이미 stub** — 현행 유지 | stub이므로 이동 실익 없음 |
| §9 OPAL Tools | 🟡 | **Eager 유지** (Lazy 트리거 이미 있음) | §9 이미 자체 Lazy 트리거 명시 |
| §3 레거시 호환 노트 3개 | ⚪ | **삭제** | 이미 완료된 호환 조치 (TASK D-8) |
| 변경이력 | ⚪ | **소스 v4.4 추가 후 배포 시 strip** | install-mac.sh로 처리 |

#### opal-pm.md (~2,588 tok)

| 섹션 | 분류 | 처리 | 근거 |
|------|------|------|------|
| §1 PM 역할 개요 + §2 PM 컨텍스트 로드 | 🔴 | **Eager 유지** (§2에 PM 직접 작업 docs 프리로드 규칙 1줄 추가) | Eager step 4 Read 대상 |
| §3 디스패치 전 (stub) | 🟡 | **현행 stub 유지** | 이미 stub, 이동 실익 없음 |
| §4 PM 검토 게이트 | 🟡 | → **harness/pm-review-gate.md** | PM Gate 수행 시에만 필요 |
| §5 학습 루프 + 자기 개선 | 🟡 | → **harness/pm-learning-loop.md** | 학습 루프 진입 시에만 필요 |
| §6 컨텍스트 주입 (stub) | 🟡 | **현행 stub 유지** | 이미 stub |
| §7 문서/코드 불일치 | 🟡 | → **harness/doc-code-mismatch.md** | 불일치 감지 시에만 필요 |
| §9~§11 (stub) | 🟡 | **현행 stub 유지** | 이미 stub |
| 변경이력 | — | **신규 작성** (소스만, 배포 미strip) | Lazy 파일이므로 strip 불필요 |

### 예상 절감량

| 파일 | 현재 Eager | 개선 후 Eager | 절감 |
|------|-----------|-------------|------|
| AGENT.md | ~5,042 tok | ~3,068 tok | ~1,974 tok |
| opal-harness.md | ~5,469 tok | ~1,600 tok | ~3,869 tok |
| opal-pm.md | ~2,588 tok | ~530 tok | ~2,058 tok |
| **합계 (3파일)** | **~13,099 tok** | **~5,198 tok** | **~7,901 tok** |
| identity + MEMORY + 프로젝트 AGENT.md 포함 | ~18,500 tok | **~10,598 tok** | **~7,902 tok (−43%)** |

---

## 2. 구현 계획

### 신규 파일 (독립 harness 모듈)

| # | 파일 | 출처 | 토큰 | Lazy 트리거 |
|---|------|------|------|------------|
| N-1 | `harness/skill-commands.md` | AGENT.md §스킬레지스트리 + §쌍슬래시커맨드 | ~305 | `//` 커맨드 입력 시 |
| N-2 | `harness/memory-learning.md` | AGENT.md §기억과 학습 | ~538 | 메모리 쓰기/기억 요청 시 |
| N-3 | `harness/state.md` | opal-harness.md §3 (레거시 노트 제외) | ~1,300 | TASK 시작 / Gate 직후 State Gate |
| N-4 | `harness/task-process.md` | opal-harness.md §4 | ~593 | TASK 단계 진입 시 |
| N-5 | `harness/pm-review-gate.md` | opal-pm.md §4 | ~694 | PM Gate 수행 시 |
| N-6 | `harness/pm-learning-loop.md` | opal-pm.md §5 | ~453 | 학습 루프 진입 / 판단 불확실 시 |
| N-7 | `harness/doc-code-mismatch.md` | opal-pm.md §7 | ~239 | 문서·코드 불일치 감지 시 |

> 모든 신규 파일: 공통 헤더 포맷 (`출처` / `로드 시점` / `역할`) + 변경이력 테이블 (v1.0 / 2026-04-21 / 128)

### 수정 파일

| # | 파일 | 변경 내용 |
|---|------|---------|
| M-1 | `opal/core/AGENT.md` | §스킬레지스트리·§쌍슬래시 → stub / §code-scan **Eager 유지(무수정)** / §기억과학습 → stub / §프로젝트컨텍스트 → 1줄 요약 stub / §PM행동프로세스 → 삭제 / §모델매핑절차 → 삭제(1줄 참조 잔존) / 변경이력 섹션 삭제 (배포 strip으로 커버) / Lazy 트리거 테이블에 N-1~N-2 트리거 행 추가 / 설계 원칙 문구 갱신 |
| M-2 | `opal/core/references/opal-harness.md` | §0 삭제 / §3 본문 → stub(→harness/state.md) / §3 레거시 호환 노트 3개 삭제 / §4 본문 → stub(→harness/task-process.md) / §2 모듈 테이블에 N-4·N-5 행 추가 / 변경이력 v4.4 행 추가 |
| M-3 | `opal/core/references/opal-pm.md` | §4 본문 → stub(→harness/pm-review-gate.md) / §5 본문 → stub(→harness/pm-learning-loop.md) / §7 본문 → stub(→harness/doc-code-mismatch.md) / 변경이력 섹션 신규 작성 |
| M-4 | `scripts/install-mac.sh` | `strip_deploy_md()` 함수 추가 / AGENT.md 복사 → strip 호출 교체 / opal-harness.md strip 후처리 추가 |

> [MUST] 배포 경계: `~/.opal/` 직접 수정 금지. 모든 변경은 `opal/core/**` 소스에서 수행.
>
> [MUST] AGENT.md Eager 1~7 번호·순서·Read 경로 변경 없음.

---

### 핵심 설계

#### N-1. `harness/skill-commands.md`

```
> 출처: opal/core/AGENT.md §스킬 레지스트리 + §쌍슬래시 커맨드
> 로드 시점: 사용자가 // 로 시작하는 입력을 보낼 때
> 역할: skill-registry 호출 절차 / 스킬명 추출·매칭 / 폴백(skills.md) / 커맨드 형식
```
- 본문: AGENT.md `:38-44`(§스킬 레지스트리) + `:91-107`(§쌍슬래시 커맨드) 전체 이동

#### N-2. `harness/code-scan-rules.md`

```
> 출처: opal/core/AGENT.md §code-scan 활용 규칙
> 로드 시점: .opal/code-scan.json 존재 프로젝트에서 구조 파악·탐색 요청 시
> 역할: 상황별 code-scan 명령 테이블 / 도구 우선 원칙 / 폴백(Glob/Grep)
```
- 본문: AGENT.md `:160-173` 전체 이동

#### N-3. `harness/memory-learning.md`

```
> 출처: opal/core/AGENT.md §기억과 학습
> 로드 시점: 메모리 쓰기 요청 시 / "이거 기억해줘" 발화 시 / 태스크 완료 후 기록 시
> 역할: 저장소 구조 / 저장 대상·비대상 / 갱신 트리거 / 인덱스·히스토리 형식 / 타임스탬프 규칙 / FIFO
```
- 본문: AGENT.md `:187-203` 전체 이동

#### N-4. `harness/state.md`

```
> 출처: opal/core/references/opal-harness.md §3
> 로드 시점: TASK 단계 시작 시 / EXECUTE Step 진행 시 / Gate 직후 State Gate 수행 시
> 역할: STATE.md 이벤트 테이블 / 상태 전이 흐름 / State Gate 자가 점검 / 세션 복원
```
- 본문: opal-harness.md `:122-218` 이동. **레거시 호환 노트 3개 제외.**
- STATE.md 공통 템플릿 서브섹션 → `harness/state-template.md` 참조 stub 유지 (기존 파일 중복 금지)
- 추가작업 프로세스 서브섹션 → `harness/additional-work.md` 참조 stub 유지

#### N-5. `harness/task-process.md`

```
> 출처: opal/core/references/opal-harness.md §4
> 로드 시점: TASK 단계 진입 시 / 태스크 채번 시 / 저장 경로 판단 시
> 역할: 스킬 영역 프로세스 / 태스크 채번 규칙 / 공통 영역 후처리 / 저장 경로 규칙
```
- 본문: opal-harness.md `:221-265` 전체 이동

#### N-6. `harness/pm-review-gate.md`

```
> 출처: opal/core/references/opal-pm.md §4
> 로드 시점: PM Gate 수행 시 / 워커 완료 수신 직후
> 역할: 워커 완료 선언 / 검토 11항목 / Pass·Fail 판정 / 문서 등록 확인 / 하네스와의 관계
```
- 본문: opal-pm.md `:57-111` 전체 이동

#### N-7. `harness/pm-learning-loop.md`

```
> 출처: opal/core/references/opal-pm.md §5
> 로드 시점: 판단이 불확실할 때 / 학습 루프 진입 시 / 반복 패턴 감지 시
> 역할: 질문 → 분류 → 기록 루프 / 자기 개선 절차 / 판단 기준 축적
```
- 본문: opal-pm.md `:113-141` 전체 이동

#### N-8. `harness/doc-code-mismatch.md`

```
> 출처: opal/core/references/opal-pm.md §7
> 로드 시점: EXECUTE 검토 중 문서·코드 불일치 감지 시
> 역할: 코드=SSOT 원칙 / PM 측 절차 4단계 / 판정 기준 / 워커 책임
```
- 본문: opal-pm.md `:153-174` 전체 이동

---

#### M-1. AGENT.md 수정 상세

**stub 교체 (내용 → 해당 모듈 파일로 이동 완료 표시):**

| 원섹션 | stub 내용 |
|--------|---------|
| §스킬 레지스트리 | `> 상세: harness/skill-commands.md` / `> Lazy 트리거: // 커맨드 입력 시` |
| §쌍슬래시 커맨드 | `> skill-commands.md에 통합` |
| §code-scan 활용 규칙 | **무수정 — Eager 유지** (PM 기본 도구, 항시 적용) |
| §기억과 학습 | `> 상세: harness/memory-learning.md` / `> Lazy 트리거: 메모리 쓰기 요청 시` |
| §프로젝트 컨텍스트 | 섹션 헤더 유지 + 파일 목록 7행만 유지 (절차 설명 제거, ~50 tok으로 압축) |

**삭제:**
- `## PM 행동 프로세스` 섹션 전체 (TASK D-6)
- `## 모델 매핑 자동 적용` 절차 3단계 + Cursor 특이사항 → `> 상세: ~/.opal/references/opal-model-mapping.md — Lazy 트리거: 워커 디스패치 직전` 1줄만 잔존 (TASK D-7)
- `## 변경이력` 섹션 전체 (install-mac.sh strip으로 배포 시 제거)

**Lazy 트리거 테이블 신규 행 2개 추가:**

```markdown
| // 커맨드 입력 시 | `harness/skill-commands.md` | - | **금지** | 로드 중단, 트리거 발생 시 재로드 |
| 메모리 쓰기 요청 / "이거 기억해줘" 발화 시 | `harness/memory-learning.md` | PM 컨텍스트 로드 완료 | **금지** | 로드 중단, 트리거 발생 시 재로드 |
```

> [MUST] 기존 `// 커맨드 입력 → skill-registry` 행이 존재하므로 skill-commands.md 행과 중복 정리 필요 — `skill-registry` 행을 `skill-commands.md`를 가리키도록 갱신하거나 병합.

**설계 원칙 문구 갱신 (`:7`):**
> `"identity.md + opal-harness.md + opal-pm.md + 프로젝트 PM 컨텍스트"` → 동일하게 유지 (파일 구조 변경 없음, 파일 내 내용만 슬림화)

#### M-2. opal-harness.md 수정 상세

- **§0 용어 정의 삭제** (`:8-20`): 섹션 헤더·본문 전체 제거
- **§2 모듈 테이블에 2행 추가** (`:99-107`):
  - `| State 관리 | harness/state.md | TASK 시작 / State Gate | §3 |`
  - `| TASK 공통 프로세스 | harness/task-process.md | TASK 단계 진입 시 | §4 |`
- **§3 본문 stub 교체** (`:122-218`):
  - `> [필수 로드] TASK 단계 시작 / Gate 직후 State Gate 수행 시` / `> 탐색: harness/state.md`
  - STATE.md 공통 템플릿·추가작업 프로세스 서브섹션은 기존 stub 형태 유지
  - 레거시 호환 노트 3개 삭제
- **§4 본문 stub 교체** (`:221-265`):
  - `> [필수 로드] TASK 단계 진입 시` / `> 탐색: harness/task-process.md`
- **변경이력 v4.4 행 추가** (`:349-377` 맨 아래):
  - `| v4.4 | 2026-04-21 | 다운사이징 — §0 삭제, §3 레거시 노트 삭제, §3/§4 → harness/state.md·task-process.md 분리. §2 모듈 테이블 갱신 (128) |`

#### M-3. opal-pm.md 수정 상세

- **§4 본문 stub 교체** (`:57-111`): `> 탐색: harness/pm-review-gate.md` / `> Lazy 트리거: PM Gate 수행 시`
- **§5 본문 stub 교체** (`:113-141`): `> 탐색: harness/pm-learning-loop.md` / `> Lazy 트리거: 판단 불확실 / 학습 루프 진입 시`
- **§7 본문 stub 교체** (`:153-174`): `> 탐색: harness/doc-code-mismatch.md` / `> Lazy 트리거: 문서·코드 불일치 감지 시`
- **§2 PM 직접 작업 docs 프리로드 규칙 추가** (`:1-46` 내 §2 말미):
  - 추가 규칙: "작업 시작 전 `pm/dispatch-process.md` Steps 1~3 실행 — 관련 docs/ 문서 선별·Read·핵심 제약 추출 (워커 디스패치 여부 무관)"
  - §1 내용 무수정
- **변경이력 섹션 신규 작성** (파일 맨 아래):
  - `| v1.0 | 2026-04-21 | 다운사이징 — §4→pm-review-gate.md, §5→pm-learning-loop.md, §7→doc-code-mismatch.md 분리. §3/§6/§9~§11 stub 유지 (128) |`

#### M-4. install-mac.sh 수정

```bash
strip_deploy_md() {
    local src="$1"
    local dst="$2"
    /usr/bin/awk 'BEGIN{keep=1} /^## 변경이력$/{keep=0} keep==1{print}' "$src" > "$dst"
}
```

- AGENT.md 복사 라인 (`:416`) → `strip_deploy_md "$opal_dir/core/AGENT.md" "$opal_home/AGENT.md"`
- opal-harness.md strip 후처리 (`:625-637` 이후) → `strip_deploy_md "$ref_src/opal-harness.md" "$ref_dst/opal-harness.md"`

---

## 3. 구현 순서

| Phase | Step | 작업 | 파일 | 비고 |
|-------|------|------|------|------|
| 1 | 1 | 신규 모듈 8개 생성 (병렬) | N-1~N-8 | 모두 독립 — 동시 생성 가능 |
| 2 | 2A | opal-harness.md 수정 | M-2 | §0 삭제·§3/§4 stub·§2 테이블 갱신 |
| 2 | 2B | opal-pm.md 수정 | M-3 | §4/§5/§7 stub |
| 3 | 3 | AGENT.md 수정 | M-1 | stub 교체·삭제·Lazy 트리거 추가 |
| 3 | 4 | install-mac.sh 수정 | M-4 | Step 3과 병렬 가능 |
| 4 | 5 | 자체 검증 | 전체 | 참조 경로·Grep 테스트 |

---

## 4. QA 체크리스트

### 기능 테스트

**신규 파일:**
- [ ] N-1: `harness/skill-commands.md` 존재 + §스킬레지스트리·§쌍슬래시 전체 포함
- [ ] N-2: `harness/memory-learning.md` 존재 + 저장소·트리거·인덱스 형식·FIFO 포함
- [ ] N-3: `harness/state.md` 존재 + 이벤트 테이블·상태 전이·State Gate 포함 / 레거시 노트 0건
- [ ] N-4: `harness/task-process.md` 존재 + 채번 규칙·저장 경로 포함
- [ ] N-5: `harness/pm-review-gate.md` 존재 + 11항목·Pass/Fail·문서 등록 확인 포함
- [ ] N-6: `harness/pm-learning-loop.md` 존재 + 루프 절차·분류·기록 포함
- [ ] N-7: `harness/doc-code-mismatch.md` 존재 + 원칙·4단계 절차·판정 기준 포함

**AGENT.md (M-1):**
- [ ] §스킬레지스트리·§쌍슬래시 본문 제거 + stub 존재
- [ ] §code-scan 내용 무수정 (Eager 유지)
- [ ] §기억과학습 본문 제거 + stub 존재
- [ ] §PM행동프로세스 섹션 없음
- [ ] §모델매핑 절차 없음 (1줄 참조만)
- [ ] 변경이력 섹션 없음
- [ ] Lazy 트리거 테이블에 skill-commands·code-scan-rules·memory-learning 행 존재
- [ ] Eager 1~7 번호·경로 불변

**opal-harness.md (M-2):**
- [ ] §0 헤더 없음
- [ ] §3 본문 제거 + stub(→state.md) 존재 / 레거시 호환 노트 0건
- [ ] §4 본문 제거 + stub(→task-process.md) 존재
- [ ] §2 모듈 테이블에 state.md·task-process.md 행 존재
- [ ] §1 Guards 내용 무수정

**opal-pm.md (M-3):**
- [ ] §2 말미에 PM 직접 작업 docs 프리로드 규칙 1줄 존재
- [ ] §1 내용 무수정
- [ ] §4 본문 제거 + stub(→pm-review-gate.md) 존재
- [ ] §5 본문 제거 + stub(→pm-learning-loop.md) 존재
- [ ] §7 본문 제거 + stub(→doc-code-mismatch.md) 존재
- [ ] 변경이력 섹션 존재

**install-mac.sh (M-4):**
- [ ] `strip_deploy_md` 함수 정의 1건
- [ ] AGENT.md strip 호출 1건
- [ ] opal-harness.md strip 호출 1건
- [ ] `bash -n scripts/install-mac.sh` 종료 코드 0

### 일관성 테스트

- [ ] 8개 신규 파일 헤더 포맷이 기존 harness/observability.md와 일관
- [ ] §2 모듈 테이블의 탐색 경로 각주 형식 (`{프로젝트}/.opal/references/harness/{file}` → `~/.opal/references/harness/{file}`) 준수
- [ ] N-4 내 state-template.md·additional-work.md 서브섹션이 기존 파일을 가리키는 stub만 존재 (중복 생성 없음)
- [ ] Lazy 트리거 테이블의 기존 `// 커맨드 입력 → skill-registry` 행이 N-1과 중복 없이 정리됨
- [ ] AGENT.md 보고 형식·부트스트랩 완료 보고·주도성·부트스트래퍼 섹션 무수정

### 문서 품질

- [ ] 한국어 본문 + 영어 코드/필드명 규칙 준수
- [ ] kebab-case 파일명 (`skill-commands.md` / `code-scan-rules.md` / `memory-learning.md` 등)
- [ ] 각 신규 파일에 변경이력 테이블 (v1.0 / 2026-04-21 / 128)
- [ ] 각 stub에 탐색 경로 + Lazy 트리거 조건 명시

---

## 5. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| §스킬레지스트리와 기존 Lazy 트리거 `// → skill-registry` 행 중복 | 낮음 | M-1에서 기존 행을 `skill-commands.md`로 갱신하여 통합 |
| N-3 memory-learning.md 미로드 시 메모리 기록 형식 오류 | 중 | Lazy 트리거 "이거 기억해줘" 발화 시 반드시 로드 명시. AGENT.md stub에 트리거 명확히 기재 |
| opal-pm.md §5 학습 루프가 pm-learning-loop.md로 분리된 후 Lazy 트리거 미발동 | 낮음 | AGENT.md Lazy 트리거 테이블 또는 opal-pm.md §5 stub에 트리거 조건 명시 |
| strip_deploy_md awk 조용히 실패 시 빈 파일 배포 | 낮음 | `[[ -s "$opal_home/AGENT.md" ]]` 검사 권장 (후속 개선) |
| opal-pilot-*/SKILL.md가 §3/§4 참조 중일 경우 stub 역방향 추적 불일치 | 낮음 | Step 5 Grep 검증. stub에 `출처: opal-harness.md §3/§4` 메타 포함 |
