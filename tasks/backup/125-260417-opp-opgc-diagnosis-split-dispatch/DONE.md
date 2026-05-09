# DONE: opgc 진단 전담화 + 프로젝트 구성 표준 정립 (125)

> 완료일: 2026-04-18 | 작업 유형: 개선 | 적용 스킬: opp | 모드: interactive
> 시작: 2026-04-17 23:52 | 종료: 2026-04-18 14:20 | 소요: 약 14h 28m (대기 시간 포함)
> 참조: [TASK.md](./TASK.md) · [PLAN.md](./PLAN.md) · [QA-PLAN.md](./QA-PLAN.md) · [QA-EXECUTE.md](./QA-EXECUTE.md) · [STATE.md](./STATE.md) · [EFFECT-ANALYSIS.md](./EFFECT-ANALYSIS.md)

---

## 1. 작업 목표

opal-pilot-gc(opgc)를 **"진단 전담 Pilot"** 으로 재정의하고(APPLY 단계 완전 제거, 수정은 opds로 수동 체인), PROJECT.md **"프로젝트 구성"** 섹션을 표준으로 정립하여 CHECK 단계가 프로젝트 구성에 따라 체커를 동적으로 병렬 디스패치하도록 한다.

## 2. 변경 사항 요약

### 2.1 변경 파일 (9개 수정 + 1개 신설 = 10개)

| # | 파일 | 주요 변경 | 버전 |
|---|------|---------|------|
| 1 | `docs/PROJECT.md` | `## 프로젝트 구성` H2 섹션 신설(Framework 단일 행), "프로젝트 문서" 테이블 `적용 범위` 컬럼 추가(5컬럼), opgc 설명 "GC 4단계 Pilot"로 교체 | - |
| 2 | `docs/CONVENTIONS.md` | 말미에 "참고 — 허브+링크 모델" 박스 추가 (OPAL은 단일 문서 유지) | - |
| 3 | `opal/core/references/conventions-hub-model.md` **(신설)** | 허브+링크 구조 가이드 §1~§5 + 변경이력, 링크 규약, 체이닝 4단계, 예시 2종(풀스택/단일 문서) | v1.0 |
| 4 | `opal/agents/opal-convention-checker/AGENT.md` | Phase 6(APPLY) 삭제, `tools`에서 Edit/Write 제거, `apply_mode` 입력 제거, `scope` 입력 추가, 허브+링크 체이닝 의사코드, Phase 번호 재배정 | v1.1 |
| 5 | `opal/agents/opal-security-checker/AGENT.md` | 동일 변경(4번과 같은 구조) | v1.1 |
| 6 | `opal/skills/opal-pilot-gc/SKILL.md` | **대대적 개편** — 4단계 파이프라인, CLI 토글 전환(`--security`/`--convention`, `--apply`/`--only` 제거), STEP 1.5 프로젝트 구성 파싱, STEP 2.2 병렬 매트릭스 4케이스, STEP 4 CLOSE에 `//opds` 체인 + TASK.md 골격, STATE.md 현황판 8행, 마이그레이션 안내 | v1.1 |
| 7 | `opal/skills/opal-project-init/SKILL.md` | 인터뷰에 Q8~Q10(프로젝트 구성) 추가, Phase 2 표준 섹션 생성, 최신화 Step E에 누락 감지·추가 제안 분기 신설 | v3.4 |
| 8 | `opal/core/references/pm/context-injection.md` | 트리거 테이블에 프로젝트 구성 라우팅 행 추가, 신규 섹션 "PROJECT.md 프로젝트 구성 기반 라우팅"(파싱 의사코드 + 예시 3건 + opgc 연계) | - |
| 9 | `opal/core/references/opal-pm.md` | §6 문단에 프로젝트 구성 기반 라우팅 한 줄 + context-injection.md 참조 | - |
| 10 | `opal/core/references/agents.md` | 체커 두 항목 입력에 `scope` 추가, 매핑 테이블에 `conventions-hub-model.md 참조` 추가, 출력 파일명 포맷 `[-{element}]` 반영 | - |

### 2.2 주요 변경 축

| 축 | 전환 내용 |
|----|---------|
| **파이프라인** | opgc 5단계(SCAN/CHECK/REPORT/**APPLY**/CLOSE) → 4단계(SCAN/CHECK/REPORT/CLOSE) |
| **CLI** | `--only security/convention` → `--security/--convention` 토글, `--apply` 제거(역할 `--agentic`에 흡수) |
| **책임 분리** | 진단(opgc) + 수정(opds 수동 체인) 역할 분리 — 체커 Edit/Write 권한 제거 |
| **디스패치** | 고정 1+1 → PROJECT.md "프로젝트 구성" 기반 N×2 병렬 (Fallback: 1+1) |
| **참조 구조** | 단일 CONVENTIONS.md/SECURITY.md → 허브+링크 모델 선택 가능 |
| **표준화** | PROJECT.md "프로젝트 구성" 섹션 + "프로젝트 문서" `적용 범위` 컬럼 정립 |

### 2.3 요구사항 이행 현황 (F-1 ~ F-11)

F-1 opgc CLI 축약·조합 전환 ✅ · F-2 APPLY 단계 제거 ✅ · F-3 opgc→opds 수동 체인 가이드 ✅ · F-4 PROJECT.md 기반 SCAN 동적 분할 병렬 ✅ · F-5 체커 2종 APPLY 제거 ✅ · F-6 체커 허브+링크 체이닝 ✅ · F-7 PROJECT.md "프로젝트 구성" + 적용 범위 컬럼 ✅ · F-8 opi 반영 ✅ · F-9 opal-pm.md/context-injection.md 라우팅 ✅ · F-10 주변 문서 정합화 ✅ · F-11 허브+링크 가이드 신설 ✅

전수 QA 검증 Pass (QA-PLAN.md, QA-EXECUTE.md 참조).

## 3. 적용 효과 분석

> 본 분석은 PLAN 단계 PM Gate 직후 캡틴 요청("뭐가 달라지고, 좋아지고, 나빠지고, 추후 검토할 것")에 따라 정리되어 DONE.md에 병합되었다.

### 3.1 달라지는 것 (Before → After)

| 영역 | Before | After |
|------|--------|-------|
| **opgc 파이프라인** | 5단계 SCAN/CHECK/REPORT/**APPLY**/CLOSE, 12행 현황판 | 4단계 SCAN/CHECK/REPORT/CLOSE, 8행 현황판 |
| **opgc 책임** | 진단 + 수정 (Edit/Write) | 진단 전담 (보고서까지만) |
| **opgc CLI** | `--only security`, `--only convention`, `--apply`, `--agentic` | `--security`, `--convention`, `--agentic` |
| **수정 경로** | `//opgc --apply` 자동 | `//opgc` → 보고서 확인 → `//opds "{폴더} GC 결과 반영"` 수동 체인 |
| **CHECK 디스패치** | 고정 1+1 (convention 1 + security 1) | PROJECT.md 구성 기반 N×2 병렬 (Fallback: 1+1) |
| **체커 권한** | `[Read, Grep, Glob, Bash, Edit, Write]`, `apply_mode` 파라미터 | `[Read, Grep, Glob, Bash]`, `scope` 파라미터 |
| **체커 참조 구조** | 단일 CONVENTIONS.md/SECURITY.md | 허브+링크 (허브 → FE/BE/Batch 상세) |
| **PROJECT.md** | "프로젝트 구성" 섹션 없음, "프로젝트 문서" 3컬럼 | "프로젝트 구성" 표준 신설 + "프로젝트 문서" `적용 범위` 컬럼 추가 |
| **opi (신규)** | "프로젝트 구성" 템플릿 없음 | 신규 프로젝트 자동 생성, 기존 프로젝트 누락 감지 |
| **PM 라우팅** | 파일 경로 → 에이전트 자동 매핑 규약 부재 | PROJECT.md 구성 기반 자동 라우팅 |

### 3.2 좋아지는 것 (Pros)

| # | 이점 | 영향 |
|---|------|------|
| 1 | **단일 책임 원칙** — opgc는 진단, opds는 수정 | SKILL.md 복잡도 ↓, 유지보수 ↑ |
| 2 | **안전성 강화** — 체커에서 Edit/Write 권한 제거 | 파일 손상 리스크 제로, hook 연동 안전 |
| 3 | **수정 품질 보증** — opds의 PLAN→TEST 루핑(3회) 자동 적용 | 회귀 방지, 체계적 검증 |
| 4 | **병렬 처리** — FE/BE/Batch 분리 디스패치 | 모노레포 진단 속도 N배 + 영역별 전문성 |
| 5 | **PROJECT.md가 SSOT로 격상** — opp/oppd 등 타 오케스트레이터도 혜택 | 에이전트 자동 라우팅 기반 마련 |
| 6 | **허브+링크 문서 모델** — 대형 프로젝트에서 컨벤션/보안 문서 분산 가능 | 단일 파일 비대화 방지 |
| 7 | **하위호환 유지** — 기존 프로젝트는 현행 1+1 그대로 | 점진적 도입 가능 |
| 8 | **hook 연동 준비 완료** — 진단 전담이라 자동 트리거 안전 | 126 태스크 진입장벽 ↓ |
| 9 | **opi 자동화** — 신규 프로젝트가 처음부터 표준 구조 | 표준 정립 가속 |
| 10 | **플랫폼 독립성 재확인** — hook은 선택적 통합 레이어로 분리 | OPAL 코어는 중립 유지 |

### 3.3 나빠지는 것 (Cons / Tradeoffs)

| # | 단점 | 완화 방안 |
|---|------|---------|
| 1 | **UX 단계 증가** — 1회 호출 → 2회 호출 (opgc + opds) | README/가이드에 워크플로우 명시 |
| 2 | **단순 수정의 오버헤드** — import 순서 1건도 TASK→PLAN→EXECUTE→TEST 경유 | opds 조기 에스컬레이션 기준이 Short로 잡아주므로 실질 영향 작음 |
| 3 | **수동 변환 부담** — opgc 보고서 → opds TASK.md를 사람이 연결 | TASK.md 골격 예시를 opgc SKILL.md에 수록 (F-3) |
| 4 | **학습 비용** — 어느 스킬을 언제 쓰는지 재인지 필요 | 대화 톤의 워크플로우 문서 필요 |
| 5 | **변경 규모** — 9개 파일 수정 + 1개 신설 (단일 태스크) | 5 Phase 순차 실행 + Step 11 교차 검증으로 누락 방지 |
| 6 | **PROJECT.md 의존성 증가** — 구성 섹션 품질이 동적 분할 정확도 결정 | Fallback 항상 동작, opi가 누락 감지 |
| 7 | **문서 분산 가능성** — 허브+링크로 쪼개면 작은 프로젝트는 오히려 복잡 | 선택적 모델 (강제 아님) |
| 8 | **`--agentic` 의미 축소** — 과거엔 "자동 수정까지"였으나 이제 "자율 진단" | 변경이력 v1.1 + README 안내로 해소 |
| 9 | **사용자 혼동 가능성** — "opgc는 수정 안 하는데 왜 있어?" | "진단·보고서 전담 Pilot" 정체성 재포지셔닝 필요 |
| 10 | **opgc CLI 기억 재정립** — `--only X` → `--X` 변경에 따른 근육 기억 재학습 | 변경이력 + 예시 5종 수록 |

### 3.4 추후 검토사항 (126+ 태스크 후보)

| 우선순위 | 주제 | 설명 |
|---------|------|------|
| **High** | **Claude Code hook 통합** | opgc가 진단 전담이 되어 hook 연동 안전. PreToolUse(git commit), Stop 이벤트별 경량 스크립트 설계. 125 완료 필수 선행 |
| High | **`//` 스킬 공통 `--help` 표준화** | EXECUTE 대화 중 제기 — 모든 opal-pilot-* 스킬에 `--help` 플래그 + 표준 출력 포맷. 하네스 공통 규칙 + SKILL.md 표준 섹션 헤딩 |
| High | **경량 Bash 린터 병행** | AI 진단 외에 기본 시크릿 스캔·eslint/ruff/golangci-lint 등 bash 병행 → 기본 품질은 항상 보장 + AI 토큰 비용 절감 |
| Medium | **opgc → opds 자동 체인 옵션** | 사용자 피드백 누적 후 `--fix` 플래그 도입 검토 (현재는 수동 체인 MVP) |
| Medium | **보고서 → TASK.md 자동 변환기** | 수동 체인의 번거로움을 줄이는 보조 도구 |
| Medium | **opgc 경량 모드** | `--ephemeral`(태스크 폴더 없이 stdout JSON), `--quiet`(로그 최소화) — hook 친화 |
| Medium | **병렬도 제한 규칙** | 거대 모노레포(FE/BE/Batch/Mobile/Infra 5+)에서 동시 디스패치 수 제한 |
| Medium | **docs/ 무효화 자동 감지** | Info 1 같은 정합성 깨짐을 체계적으로 추적하는 메모리/리포트 체계 |
| Low | **전문 에이전트 확장** | opal-mobile-agent, opal-infra-agent 추가 (현재 FE/BE/DB/기획만) |
| Low | **CONVENTIONS.md 허브 검증** | 허브의 링크가 실제 존재하는지 확인하는 체커 옵션 |
| Low | **PROJECT.md 자동 갱신 제안** | 새 패턴 감지 시 "프로젝트 구성" 섹션 갱신 제안 자동화 |
| Low | **fingerprint 중복 제거 강화** | 동적 분할 병렬 시 공통 파일 이슈 중복 보고 방지 로직 검증 |
| Low | **opgc 보고서 포맷 정합성** | 수동 체인 편의를 위한 opgc 보고서 YAML frontmatter 도입 검토 |

### 3.5 요약 판단

> **정비 가치 ≫ 비용**. opgc가 "진단 전담 Pilot + PROJECT.md 라우팅 기반"으로 재포지셔닝되면 **hook 통합, 모노레포 확장, 전문 에이전트 체계 전체가 풀리는 열쇠**가 됩니다. 단점은 주로 UX 단계 증가인데, 이는 문서·워크플로우 가이드로 해소 가능합니다.

## 4. 검증 결과

| 게이트 | 결과 | 산출물 |
|--------|------|--------|
| PLAN QA Gate | **Pass** (Info 2건: PROJECT.md:70 설명 정합성, opi 변경이력 버전 — EXECUTE에서 모두 반영) | [QA-PLAN.md](./QA-PLAN.md) |
| PLAN PM Gate | **Pass** (Info 1을 EXECUTE 명시 지시로 흡수) | STATE.md 의사결정 로그 #7 |
| EXECUTE QA Gate | **Pass** (지적 사항 0건, F-1~F-11 + CR-EX-1~8 전원 Pass) | [QA-EXECUTE.md](./QA-EXECUTE.md) |
| EXECUTE PM Gate | **Pass** (@header 해당 없음, docs/ 무효화 반영) | STATE.md |

## 5. 하네스 Guards 준수

- `~/.opal/` 직접 수정 **0건** (모든 변경은 프로젝트 소스 경로에서 수행)
- 커뮤니티 스킬 원본 수정 **0건**
- `git commit` 호출 **0건** (캡틴 요청 시 별도 수행)
- QA 에이전트 호출 금지(EXECUTE 워커 기준) ✅
- STATE.md 갱신 금지(워커 기준) ✅ — 오케스트레이터 PM만 수행
- 단일 태스크 완료 원칙 — 125 하나에서 종결(126/127 분리 없음) ✅

## 6. 의사결정 로그 요약

| # | 시점 | 결정 |
|---|------|------|
| 1 | 2026-04-17 23:20 | CLI 축약 A안(토글 조합) 채택 — `--only X` → `--X` |
| 2 | 2026-04-17 23:25 | `--apply` 제거, 자동화는 `--agentic`에 단일화 |
| 3 | 2026-04-17 23:35 | APPLY 단계 완전 제거, 수정은 opds 수동 체인(A안) |
| 4 | 2026-04-17 23:40 | PROJECT.md "프로젝트 구성" 섹션 표준화, "프로젝트 문서"에 `적용 범위` 컬럼 |
| 5 | 2026-04-17 23:50 | 125 단일 태스크로 완료(126/127 분리 없음) |
| 6 | 2026-04-18 13:30 | PROJECT.md 컬럼 처리 옵션 2 채택 — 기존 `용도` 유지 + `적용 범위` 추가(5컬럼) |
| 7 | 2026-04-18 13:30 | Info 1 반영 — EXECUTE Step 1에 `docs/PROJECT.md:70` opgc 설명 4단계 갱신 지시 |
| 8 | 2026-04-18 13:32 | CLOSE 단계 DONE.md에 "적용 효과 분석" 포함 (본 §3) |

## 7. 배포 및 후속 작업

### 배포

현재 변경사항은 프로젝트 소스(`opal/...`, `docs/...`)에 있고 **배포본(`~/.opal/`)에는 반영되지 않았습니다**. 캡틴이 `scripts/install-mac.sh` 실행 시점부터 신 CLI·체커 구조가 유효해집니다.

### 다음 태스크 권장

1. **126: Claude Code hook 통합** — 진단 전담 opgc를 hook에 안전 연동 (High)
2. **127: `--help` 표준화** — 전 opal-pilot-* 스킬에 공통 도움말 체계 (High)
3. **128: 경량 Bash 린터 병행** — AI 진단 + bash 기본 품질 보증 2단 구조 (High)

세부 리스트는 §3.4 참조.

## 8. 태스크 산출물

- [TASK.md](./TASK.md) — 요구사항 F-1~F-11, 확정 설계 D-1~D-11, 관련 문서 D-1~D-13
- [PLAN.md](./PLAN.md) — 11 Steps / 5 Phases, 인용 포맷 citation-rules §2/§3.1 준수
- [QA-PLAN.md](./QA-PLAN.md) — PLAN 단계 QA 리포트 (Pass)
- [QA-EXECUTE.md](./QA-EXECUTE.md) — EXECUTE 단계 QA 리포트 (Pass)
- [STATE.md](./STATE.md) — 파이프라인 현황판 20행 + 의사결정 로그 8건
- [EFFECT-ANALYSIS.md](./EFFECT-ANALYSIS.md) — 적용 효과 분석 원본 (본 DONE.md §3에 병합)
- **DONE.md** (이 파일)
