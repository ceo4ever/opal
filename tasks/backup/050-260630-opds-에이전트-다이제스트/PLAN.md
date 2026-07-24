# PLAN: AGENT.md 다이제스트 — 비서 tier 코어 경량화 (PM 이관 + 메타 정리)

> 작성일: 2026-06-30 | 입력: TASK.md (ANALYSIS.md 없음 — 직접 분석)
> 모드: Multi-Feature
> 작업 본질: **다이제스트(이동·dedup·trim)이지 기능 개정이 아니다.** 행동 규칙의 의미 불변(회귀 0).

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

049로 부트스트랩이 2-tier가 되면서 `opal/core/AGENT.md`가 비서 tier에서 매 세션 로드된다. 본 태스크는 AGENT.md를 **비서 코어만 남긴 lean core**로 다이제스트한다. PM/프로젝트 전용 섹션(역할전환 상세·code-scan 활용·opal-brain 활용·메모리 브리핑·모델매핑 적용·프로젝트 컨텍스트)을 이미 Phase B로 로드되는 `opal-pm.md`로 **이동하되 기존 내용과 중복 제거 병합(dedup)**하고, 부트스트래퍼 자동관리(설치시점·비런타임)는 신규 reference로 이관하며, 변경이력은 trim한다. **동작(부트스트랩 절차·2-tier 게이트·보고형식·`//` 진입)은 불변.**

> **[측정 정정 — 직접 분석으로 확인]** 배포 파이프라인(`scripts/install-mac.sh:227` `strip_deploy_md`)이 `## 변경이력` 섹션을 **배포 시점에 제거**한다. 따라서 런타임 로드되는 `~/.opal/AGENT.md`는 **455줄(소스 493줄 - 변경이력 38줄)**이다(`wc -l ~/.opal/AGENT.md` = 455 검증). 즉 변경이력 trim(R-4)은 **런타임 토큰 영향 0**(소스 가독성·유지보수 위생 항목). 실제 비서 세션 토큰 경감은 **PM 섹션 이동(R-2·R-3)**에서 발생한다. lean core 목표(~205줄)는 소스 493줄이 아니라 **런타임 body 455줄** 기준으로 재해석한다 — 이관 대상 합계 ≈ 250줄을 옮기면 잔존 body ≈ 205줄.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | AGENT.md 비서 코어 잔류 확정 (이관 대상 제거) | R-1, R-6 | P0 | 없음 |
| F-002 | PM 섹션 → opal-pm.md 이관 + dedup 병합 | R-2 | P0 | 없음 |
| F-003 | 부트스트래퍼 자동관리 → 신규 reference 이관 | R-3 | P0 | 없음 |
| F-004 | 변경이력 trim (최근 5 + git 링크) | R-4 | P1 | 없음 |
| F-005 | 교차참조 갱신 (dangling 0) | R-5 | P0 | F-001, F-002, F-003 |

> R-6(동작 불변·회귀 0)은 독립 기능이 아니라 **F-001~F-005 전체에 걸친 가로 제약**이다. F-001(코어 잔류 완결성)·§5.2 회귀·TEST-SCENARIO 회귀 트랙(049 TS-001~004 재실행)에서 집행한다.

### 1.3 기능 의존 그래프 (ASCII)

```
F-001 (코어 잔류) ─┐
F-002 (PM 이관)  ─┼─ F-005 (교차참조 갱신·dangling 0)
F-003 (부스 이관) ─┘
F-004 (변경이력 trim) ── 독립 (병렬)
```

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨. 본 태스크는 문서 이동이라 동작계약 가설이 적고, **정보 손실·dangling·동작 회귀**가 핵심 리스크다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-002 PM 섹션 이동 | 도구 인지 맵(잔류) 내부 포인터 `§code-scan 활용 규칙`·`§opal-brain 활용 규칙`이 AGENT.md에서 제거된 절을 가리킴 → dangling | P1 | L1(정적 grep — 포인터가 opal-pm.md 새 위치 지시) | S-후보 (TS-비서코어포인터) |
| H-2 | F-002 dedup | 하네스 모드 3-way가 `opal-harness.md §2`에 **이미 존재** → 단순 복사 시 중복 | P1 | L1(정적 grep — opal-pm.md에 3-way 표 중복 신설 부재) | S-후보 (TS-dedup) |
| H-3 | F-001 코어 절삭 | 비서가 알투로 행동하는 데 필요한 정보(정체성·보고형식·도구판단·`//` 진입·주도성·핵심역할) 손실 | P0 | L1(정적 grep — 필수 6섹션 잔존) | S-후보 (TS-코어완결) |
| H-4 | F-001·F-005 부트스트랩 절 | step 6 공통 절의 `(아래 "프로젝트 부트스트래퍼 자동 관리" 참조)` 포인터가 이관 후 dangling | P0 | L1(정적 grep — 포인터가 신규 reference 지시) | S-후보 (TS-부스포인터) |
| H-5 | F-001 동작 불변 | 부트스트랩 Eager 2-phase·2-tier 게이트·step0 스킵게이트·`//` 불변식·완료보고 변형 | P0 | L1(정적 grep) + L3(049 TS-001~004 재실행) | S-후보 (TS-회귀001~004) |
| H-6 | F-004 변경이력 trim | 049·050 변경이력 행 누락 / 전체 이력 추적 불능 | P2 | L1(정적 grep — 050 행 + git 링크 존재) | S-후보 (TS-변경이력) |
| H-7 | F-002 이동 후 opal-pm.md 비대화 | PM tier 토큰 중립(이동) 가정이 깨지고 PM 세션 토큰 급증 | P2 | L1(줄수 측정 — 이동분 ≈ 수신분, 중복 없음) | S-후보 (TS-토큰중립) |

**가설 도출 노트(3종 예시 대응)**:
- H-예1(반환 계약) ↔ **H-1**: 잔류 섹션(도구 인지 맵)의 내부 포인터가 이동 섹션을 가리키는 "포인터 계약"이 깨질 수 있음 → 정적 grep 의무.
- H-예2(동시성) ↔ **해당 없음**: 문서 이동이라 동시성·레이스 없음.
- H-예3(DB 제약) ↔ **H-5**: mock(정적 grep) 통과 후 실세션(부트스트랩 LLM 거동)에서만 드러나는 동작 회귀 → L3(049 TS-001~004 재실행, 캡틴 수동) 의무.

---

## 2. 기능별 분석

### F-001: AGENT.md 비서 코어 잔류 확정 (이관 대상 제거)

#### 2.1.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/AGENT.md` | 부트스트랩 SSOT — 비서 코어만 잔류 | 수정 |

#### 2.1.2 현재 구현 (line 단위 섹션 진단)

> `grep -nE "^#{2,4} "` + Read로 실측. 분류축: **유지(비서 코어) / 이관(→목적지) / trim**.

| 줄범위 | 섹션 | 분류 | 비고 |
|--------|------|------|------|
| 5~81 | `## 부트스트랩` (Eager 2-phase·Lazy 테이블·레지스트리·완료보고) | **유지** | 049 핵심 — 절대 불변. TS-001~004 대상 |
| 83~91 | `## 정체성 적용` | **유지** | 비서 코어 (정체성) |
| 93~112 | `## 핵심 역할` (1.AI 비서 / 2.프로젝트 PM) | **유지** | 비서 코어 (역할 인식). PM 진입 신호 서술 포함 — 유지 |
| 114~118 | `## 행동 규칙` 헤더 + `### 역할 전환` 도입 | **유지(축약)** | 헤더 잔류, 하위 분기 일부 이관 |
| 120~125 | `#### 상태 정의` (비서/PM 소형 표) | **유지** | 비서 코어 (TASK 진단표 "비서/PM 상태정의(소형 표) 유지") |
| 127~132 | `#### PM 내 하네스 적용 기준` (대화/태스크) | **이관 → opal-pm.md** | PM 전용. 비서 세션 불필요 |
| 134~140 | `#### 하네스 모드 체계 (3-way)` | **dedup 제거** | `opal-harness.md §2` 모듈 구조 표에 **이미 존재**(semi/interactive/agentic) → opal-pm.md에 **포인터만** |
| 142~148 | `#### 자동 전환 트리거` | **이관 → opal-pm.md** | PM 전용 전환 상세 |
| 150~158 | `#### 소유자 오버라이드` | **이관 → opal-pm.md** | PM 전용 (`//`·"그냥 해"·"비서로" 모드 지정) |
| 160~192 | `#### "그냥 해/직접 수행" = L2 경량 트랙` | **이관 → opal-pm.md** | PM 전용 (L2 진입기준·하네스 적용범위) |
| 194~221 | `### code-scan 활용 규칙` (+ brain↔code-scan 표) | **이관 → opal-pm.md** | TASK 진단표 "code-scan 활용 이관" |
| 222~252 | `### opal-brain 활용 규칙` (search·ingest) | **이관 → opal-pm.md** | TASK 진단표 "opal-brain 활용 이관" |
| 253~283 | `### 도구·MCP 적극 활용 규칙` (도구 인지 맵) | **유지** | 비서 코어 (도구 판단 — TASK 진단표 "도구·MCP 활용 유지"). 단 내부 포인터 2건 갱신(H-1) |
| 285~296 | `### 주도성` | **유지** | 비서 코어 (TASK 진단표 "주도성 유지") |
| 298~301 | `### 기억과 학습` (stub) | **유지** | 이미 stub(memory-learning.md 참조). 비서 코어 잔류 무해 |
| 303~348 | `### 보고 형식` | **유지** | 비서 코어 (TASK 진단표 "보고 형식 유지"). **opal-pm.md §8이 이 섹션을 가리킴 — 잔류 확정, 참조 불변** |
| 350~382 | `## 프로젝트 메모리 브리핑` | **이관 → opal-pm.md** | TASK 진단표 "메모리 브리핑 이관" |
| 385~395 | `## 모델 매핑 자동 적용` | **이관 → opal-pm.md** | TASK 진단표 "모델매핑 적용 이관". 단 부트스트랩 step0 본문의 models 로드 1줄 서술은 **부트스트랩 절에 잔류**(이동 대상은 "## 모델 매핑 자동 적용" 독립 절) |
| 397~445 | `## 프로젝트 부트스트래퍼 자동 관리` | **이관 → 신규 reference (F-003)** | 설치시점·비런타임 |
| 446~454 | `## 프로젝트 컨텍스트` | **이관 → opal-pm.md** | TASK 진단표 "프로젝트 컨텍스트 이관" |
| 456~493 | `## 변경이력` | **trim (F-004)** | 최근 5 + git 링크. **배포 시 strip되어 런타임 영향 0** |

#### 2.1.3 영향 범위

- **잔류 후 dangling 위험(H-1·H-4)**: `253~283 도구 인지 맵`이 잔류하면서 그 안의 포인터 `§code-scan 활용 규칙`(L265)·`§opal-brain 활용 규칙`(L266)이 이관되는 절을 가리킴. step6 공통(L37)의 `(아래 "프로젝트 부트스트래퍼 자동 관리" 참조)`도 이관 대상을 가리킴. → F-005에서 갱신.
- **부트스트랩 절(5~81) 내 자기참조**: 없음(독립). 2-phase 게이트 로직은 플랫폼 독립으로 잔류(049 TS-020 정합).
- **opal-pm.md §8 → AGENT.md §보고 형식**: 보고 형식 잔류로 **불변**(건드리지 않음).

---

### F-002: PM 섹션 → opal-pm.md 이관 + dedup 병합

#### 2.2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/AGENT.md` | 이관 대상 섹션 제거 | 수정 |
| 문서 | `opal/core/references/opal-pm.md` | PM 섹션 수신(병합) | 수정 |
| 문서 | `opal/core/references/opal-harness.md` | dedup 기준(하네스 3-way 기존 보유) | 참조(불변) |

#### 2.2.2 현재 구현 — dedup 커버리지 분석 (직접 Read 확인)

> **[MUST] 이동이 아니라 dedup**: 이관 대상이 목적지 문서에 **이미 존재**하면 "AGENT.md에서 제거 + 기존 문서로 단일화(포인터)"한다. 중복 신설 금지(`opal/core/PRINCIPLES.md` §2).

| 이관 대상 (AGENT.md) | opal-pm.md 기존 커버리지 | opal-harness.md 기존 커버리지 | dedup 판정 |
|---------------------|------------------------|----------------------------|-----------|
| `#### 하네스 모드 체계 (3-way)` (134~140) | 없음 | **있음** — `opal-harness.md §2 모듈 구조` 표가 semi/interactive/agentic 3-way를 정의(`opal-harness.md:74~88`) | **중복 — opal-pm.md에 표 신설 금지. `opal-harness.md §2` 포인터만** |
| `#### PM 내 하네스 적용 기준` (127~132) | 없음(§1 역할 개요는 활성화 조건만) | 없음 | **신규 수신** — opal-pm.md에 신설 |
| `#### 자동 전환 트리거` (142~148) | 없음 | 없음 | **신규 수신** |
| `#### 소유자 오버라이드` (150~158) | 없음 | 없음 | **신규 수신** |
| `#### "그냥 해" = L2 경량 트랙` (160~192) | 없음 | 없음 | **신규 수신** |
| `### code-scan 활용 규칙` (194~221) | **부분** — `opal-pm.md §9 code-scan.json PM 관리 의무`가 생성/갱신 의무를 다룸(활용 규칙 표는 없음) | 없음 | **병합 수신** — §9에 "활용 규칙"(상황→활용 방법 표 + brain↔code-scan 표)을 흡수, §9 기존 관리 의무와 중복 없이 통합 |
| `### opal-brain 활용 규칙` (222~252) | 없음(brain은 §9 인접이나 활용 규칙 부재) | 없음 | **신규 수신** |
| `## 프로젝트 메모리 브리핑` (350~382) | 없음 | 없음 | **신규 수신** |
| `## 모델 매핑 자동 적용` (385~395) | 없음(opal-pm.md) | **있음** — `opal-harness.md §6 Model Mapping`이 레벨·오버라이드 우선순위 정의(`opal-harness.md:178~189`) | **중복 — opal-pm.md에 신설하되 본문은 `opal-harness.md §6` + `opal-model-mapping.md §5` 포인터로 단일화**(우선순위 표 재서술 금지) |
| `## 프로젝트 컨텍스트` (446~454) | 없음 | 없음 | **신규 수신** (단 AGENT.md `## 핵심 역할`·부트스트랩과 의미 중복 — 포인터 수준 권장) |

> **dedup 핵심 결론 2건**:
> 1. **하네스 모드 3-way** → opal-pm.md에 표를 복사하지 않는다. opal-pm.md 신규 절에서 `> 하네스 모드 3-way(semi-agentic/interactive/agentic): opal-harness.md §2 모듈 구조 참조` 1줄 포인터로 단일화. (`→ opal-harness.md §2`)
> 2. **모델 매핑 우선순위** → opal-pm.md에 우선순위 표를 복사하지 않는다. `> 오버라이드 우선순위·레벨 정의: opal-harness.md §6 + opal-model-mapping.md §5 참조`로 단일화. 단 "PM 진입 시 models 로드 적용" 같은 **PM 행동 측면**만 새로 서술.

#### 2.2.3 영향 범위

- **opal-pm.md 수신 후 구조**: 기존 §1~§11 + 변경이력. 신규 섹션을 §11 뒤(또는 의미상 §3 디스패치 인접)에 추가. PM 행동 프로세스 문서이므로 "역할 전환/L2/code-scan·brain 활용/메모리 브리핑/모델매핑 적용/프로젝트 컨텍스트"가 의미적으로 정합.
- **opal-pm.md는 Phase B Eager 로드(부트스트랩 step 4)** → PM 세션은 이미 이 문서를 읽으므로 **토큰 중립(이동)**, 비서 세션은 미로드로 경감(H-7).
- **opal-harness.md는 불변**(dedup 기준 제공처). 건드리지 않음.

---

### F-003: 부트스트래퍼 자동관리 → 신규 reference 이관

#### 2.3.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/AGENT.md` | "프로젝트 부트스트래퍼 자동 관리" 절 제거 + 1줄 포인터 | 수정 |
| 문서 | `opal/core/references/bootstrapper-management.md` | 부트스트래퍼 자동관리 상세 수신 | 신규 |

#### 2.3.2 현재 구현

- AGENT.md 397~445 `## 프로젝트 부트스트래퍼 자동 관리`: 4 플랫폼(Claude/Cursor/Codex/Gemini) 자동 삽입 정책 + 수동 삽입 마커 블록(414~421 — 코드블록 내 `# === OPAL START ===`). **이 내용은 설치/프로젝트 진입 시점 가이드이며 매 세션 런타임 행동이 아니다**(TASK 진단표 "설치시점·비런타임").
- 단 step6(공통 절, L37)이 이 섹션을 런타임에 1회 참조한다(Gemini 자동삽입 분기). → **포인터로 연결 유지 필요**.

> **[MUST] 마커 블록 보존**: 397~445 내 `414~421`의 수동 삽입 마커 코드블록(`# === OPAL START === ... # === OPAL END ===`)은 의미 변경 없이 신규 reference로 **그대로 이동**한다. install-mac.sh `extract_bootstrap_content`(L241)는 **bootstrapper/ 디렉토리 파일**에서 추출하므로 AGENT.md 이 블록 이동은 install 동작에 무영향(직접 분석 — `scripts/install-mac.sh:1042` strip_deploy_md만 AGENT.md 사용).

#### 2.3.3 영향 범위

- **신규 reference 명명**: `bootstrapper-management.md` (TASK가 예시한 이름 그대로). 위치 `opal/core/references/` (harness/ 하위 아님 — 부트스트랩 인프라 성격이나 기존 `references/` 평면 문서들과 동급. `opal-harness.md`·`opal-pm.md`와 같은 레벨이 적절). **[MUST] PRINCIPLES.md §2: 신규 reference는 이 1개만. 추가 파일 생성 금지.**
- **Lazy 트리거 등록 불요**: 이 reference는 런타임 Lazy 로드 대상이 아니다(설치/init 시점 가이드). AGENT.md step6이 가리키되, Gemini 자동삽입은 step6 본문 1줄로 충분하고 상세는 install/opi가 수행. → Lazy 테이블(44~61) 신규 행 추가는 **하지 않는다**(과설계 회피). 단 AGENT.md에 `> 상세: references/bootstrapper-management.md` 포인터만 남긴다.

---

### F-004: 변경이력 trim (최근 5 + git 링크)

#### 2.4.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/AGENT.md` | 변경이력 표 trim | 수정 |

#### 2.4.2 현재 구현

- AGENT.md 456~493 `## 변경이력`: v1.0~v4.0 총 33행. **배포 시 `strip_deploy_md`가 전체 제거**(`scripts/install-mac.sh:227`) → 런타임 토큰 0.
- 049 행 = v4.0(L492). 050 행은 본 태스크에서 추가 예정.

#### 2.4.3 영향 범위

- trim 후: 최근 5행(v3.8·v3.9·v3.10·v3.11·v4.0) + 본 태스크 050 행 = 6행. + "전체 이력: `git log opal/core/AGENT.md`" 안내 1줄. (049·050 행 보존 — 049=v4.0 잔존, 050=신규 추가).
- **[MUST] 049 행 보존 필수**(H-6). trim은 v1.0~v3.7 구간만 제거하고 git 링크로 대체.

> **F-004 위생 항목 주의**: 런타임 영향 0이나, 소스 가독성·이력 추적 위생으로 수행. 다른 OPAL 문서(opal-harness.md·opal-pm.md)는 전체 이력을 유지하나, AGENT.md만 33행으로 비대 → trim 적격. **변경이력 trim을 다른 reference로 확산하지 않는다**(F-004는 AGENT.md 한정).

---

### F-005: 교차참조 갱신 (dangling 0)

#### 2.5.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/AGENT.md` | 잔류 도구 인지 맵 포인터 + step6 포인터 갱신 | 수정 |
| 문서 | (전수 grep 결과) 프로젝트 전체 | dangling 참조 검출 | 검증 |

#### 2.5.2 현재 구현 — 교차참조 전수 맵 (`grep -rn "AGENT.md §" opal/ docs/` + AGENT.md 내부 grep)

| # | 참조 위치 | 참조 대상 | 이동 여부 | 조치 |
|---|----------|----------|----------|------|
| X-1 | `opal/core/AGENT.md:37` (step6 공통) | `(아래 "프로젝트 부트스트래퍼 자동 관리" 참조)` | **이동(F-003)** | **갱신** → `(상세: references/bootstrapper-management.md)` |
| X-2 | `opal/core/AGENT.md:265` (도구 인지 맵) | `§code-scan 활용 규칙` | **이동(F-002)** | **갱신** → `opal-pm.md §code-scan 활용 규칙` |
| X-3 | `opal/core/AGENT.md:266` (도구 인지 맵) | `§opal-brain 활용 규칙` | **이동(F-002)** | **갱신** → `opal-pm.md §opal-brain 활용 규칙` |
| X-4 | `opal/core/references/opal-pm.md:104` | `AGENT.md §보고 형식` | **잔류(F-001)** | **불변** — 보고 형식 잔류 |
| X-5 | `opal/core/references/opal-pm.md:146` (변경이력) | `AGENT.md §보고 형식` | 잔류 | 불변 (변경이력 기술) |
| X-6 | `opal/core/references/opal-harness-semi-agentic.md:112` | `AGENT.md §보고 형식` | 잔류 | 불변 |
| X-7 | `opal/core/references/harness/skill-commands.md:3` | `AGENT.md §스킬 레지스트리 + §쌍슬래시 커맨드` (출처 주석) | 잔류(63~66) | 불변 (분리 출처 표기) |
| X-8 | `opal/core/references/harness/memory-learning.md:3` | `AGENT.md §기억과 학습` (출처 주석) | 잔류 stub(298~301) | 불변 |
| X-9 | `opal/skills/op-dev-execute/references/execute-specialist-guide.md:10,15,36,43` | `AGENT.md §페르소나/§금지 규칙/§결과 반환` | **프로젝트/에이전트 레벨 AGENT.md** (≠ `opal/core/AGENT.md`) | **불변** — core AGENT.md 무관 |
| X-10 | `opal/tools/state-tool/tests/test_state_tool.py:19,128,1761,2601` | `AGENT.md §확정 기준 #2` | **프로젝트/에이전트 레벨 AGENT.md** | **불변** — core AGENT.md 무관 |

> **dangling 갱신 대상은 X-1·X-2·X-3 (3건, 모두 AGENT.md 내부)**. X-4~X-10은 잔류 섹션 또는 비-core AGENT.md 참조로 **불변**. `grep -rn "AGENT.md §역할 전환|§code-scan|§opal-brain|§프로젝트 메모리|§모델 매핑|§부트스트래퍼|§프로젝트 컨텍스트"` 결과 = **0건**(이동 섹션을 외부에서 가리키는 참조 없음 — 직접 grep 검증 완료).

#### 2.5.3 영향 범위

- 갱신은 AGENT.md 내부 3건으로 국소적. 외부 문서(opal-pm.md §8 등) 참조는 잔류 섹션을 가리켜 불변.
- F-005는 F-001·F-002·F-003 완료 후 수행(이동 확정 후 포인터 갱신).

---

## 3. 기능별 설계

### F-001: AGENT.md 비서 코어 잔류 확정

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 문서 | 이관 대상 섹션(2.1.2 표 "이관"·"dedup 제거"·"trim" 행) 제거. 유지 섹션은 **문구 불변**. `### 역할 전환` 헤더 + `#### 상태 정의` 잔류, 하위 PM 전용 분기는 이관 | (→ §2.1.2 표) |

#### 3.1.2 설계 — 잔류 후 AGENT.md 골격 (비서 코어 완결성)

> **[MUST] `opal/core/PRINCIPLES.md` §3 Surgical**: 유지 섹션은 **문구·의미 불변**. 이관·제거·포인터화 외 인접 개선·재작성 금지.

잔류 후 AGENT.md 섹션 순서(비서 코어):
```
## 부트스트랩 (5~81, 불변)            ← Eager 2-phase + Lazy + 레지스트리 + 완료보고
## 정체성 적용 (불변)
## 핵심 역할 (불변)                   ← AI 비서 + 프로젝트 PM(진입 신호)
## 행동 규칙
  ### 역할 전환                       ← 도입 + #### 상태 정의(소형 표)만 잔류
                                      ← (PM 하네스기준·3-way·자동전환·오버라이드·L2 → opal-pm.md)
  ### 도구·MCP 적극 활용 규칙          ← 도구 인지 맵 잔류 (포인터 2건 갱신: §X-2·X-3)
  ### 주도성 (불변)
  ### 기억과 학습 (stub 불변)
  ### 보고 형식 (불변)                ← opal-pm.md §8이 가리킴 — 불변
## 변경이력 (trim — F-004)
```

**비서 코어 완결성 점검 항목** (H-3 — "비서가 알투로 행동"):
- [ ] 정체성 적용 (§정체성 적용) — 잔류
- [ ] 보고 형식 (§보고 형식 골격·원칙·역할별 표기) — 잔류
- [ ] 도구 판단 (§도구·MCP 적극 활용 규칙 인지 맵) — 잔류
- [ ] `//` 진입 (§부트스트랩 Phase A `//` 불변식 + Lazy 트리거) — 잔류
- [ ] 주도성 (§주도성) — 잔류
- [ ] 핵심 역할 (§핵심 역할 — 비서/PM 인식) — 잔류
- [ ] 비서/PM 상태 정의 소형 표 (§역할 전환 #### 상태 정의) — 잔류

> **잔류 판단 근거**: 비서 세션은 PM 디스패치/L2/code-scan/brain/메모리브리핑/모델매핑 적용을 수행하지 않으므로 해당 섹션 부재가 행동 완결성을 해치지 않는다. 단 "도구 인지 맵"은 비서도 도구를 선제 활용하므로 잔류(코드-scan/brain "활용 규칙 상세"는 PM 행동이므로 이관, 인지 맵의 "용도→도구" 1줄은 비서 코어). (→ TASK §배경 분석 tier 진단표)

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R-1 AC (이관 섹션 제거) | 산출물 검사 | AGENT.md에서 이관 섹션 헤딩(`#### 하네스 모드 체계`·`#### 자동 전환 트리거`·`### code-scan 활용 규칙`·`### opal-brain 활용 규칙`·`## 프로젝트 메모리 브리핑`·`## 모델 매핑 자동 적용`·`## 프로젝트 부트스트래퍼 자동 관리`·`## 프로젝트 컨텍스트`) grep = 0건 |
| TS-002 | R-1 AC (부트스트랩 보존) | 회귀 테스트 | `## 부트스트랩` Phase A/B + step0 게이트 + 완료보고 grep 잔존 (049 TS-001~004 정합) |
| TS-003 | R-6 AC (비서 코어 완결) | 산출물 검사 | 필수 7항목(정체성·보고형식·도구인지맵·`//`불변식·주도성·핵심역할·상태정의표) grep 전부 잔존 |

---

### F-002: PM 섹션 → opal-pm.md 이관 + dedup 병합

#### 3.2.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 문서 | F-001에서 제거된 PM 섹션의 출처 (제거는 F-001 Step에서 일괄) | (→ §2.1.2) |
| 2 | `opal/core/references/opal-pm.md` | 문서 | PM 섹션 수신: 신규 절 추가(역할전환 상세·L2·메모리브리핑·모델매핑 적용·프로젝트 컨텍스트) + §9 code-scan 활용 규칙 병합 + opal-brain 활용 규칙 신설. **3-way·모델매핑 우선순위는 포인터로 단일화(dedup)** | (→ §2.2.2 dedup 표) |

#### 3.2.2 설계 — opal-pm.md 수신 구조

opal-pm.md에 추가할 신규 절(기존 §1~§11 뒤 또는 의미 위치):

```
## 12. 역할 전환 (PM 내부)            ← AGENT.md 127~192 이동
  ### PM 내 하네스 적용 기준 (대화/태스크)
  > 하네스 모드 3-way: opal-harness.md §2 모듈 구조 참조  ← dedup 포인터 (→ opal-harness.md §2)
  ### 자동 전환 트리거
  ### 소유자 오버라이드
  ### "그냥 해 / 직접 수행" = L2 경량 트랙 (진입기준·하네스 적용범위)
## 13. code-scan 활용 규칙             ← §9에 병합 또는 신규 절. AGENT.md 194~221 이동
  (상황→활용 방법 표 + brain↔code-scan 역할 분담 표)
## 14. opal-brain 활용 규칙            ← AGENT.md 222~252 이동 (search·ingest)
## 15. 프로젝트 메모리 브리핑          ← AGENT.md 350~382 이동
## 16. 모델 매핑 적용 (PM 행동)        ← AGENT.md 385~395 이동
  > 우선순위·레벨 정의: opal-harness.md §6 + opal-model-mapping.md §5 참조  ← dedup 포인터
## 17. 프로젝트 컨텍스트               ← AGENT.md 446~454 이동
```

> **[MUST] dedup (PRINCIPLES.md §2 신규 추상화 금지)**: 하네스 3-way 표·모델매핑 우선순위 표를 opal-pm.md에 **복사하지 않는다**. 각각 `opal-harness.md §2`·`opal-harness.md §6 + opal-model-mapping.md §5` 포인터로 단일화. (→ §2.2.2)
> **절 번호는 구현자 재량** — opal-pm.md 기존 §9(code-scan 관리 의무)와 신규 "code-scan 활용 규칙"은 의미 인접하므로 §9 확장 병합 또는 별도 절 모두 허용. 단 **중복 서술 금지**(§9 기존 "생성/갱신 의무" + 신규 "활용 방법 표"가 겹치지 않게).
> **문구 불변(Surgical)**: 이동되는 본문은 AGENT.md 원문을 그대로 옮긴다(헤딩 레벨만 opal-pm.md 구조에 맞게 조정 가능). 의미 재작성 금지.

#### 3.2.3 환경 변경
해당 없음.

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-004 | R-2 AC (목적지 존재) | 산출물 검사 | opal-pm.md에 이관 섹션(역할전환 상세·L2·code-scan 활용·opal-brain 활용·메모리브리핑·모델매핑 적용·프로젝트 컨텍스트) grep 잔존 |
| TS-005 | R-2 AC (중복 없이 병합 — dedup) | 산출물 검사 | opal-pm.md에 3-way 모드 표(`semi-agentic\|interactive\|agentic` 3행 표) 신설 부재 + 모델매핑 우선순위 표 신설 부재 → 대신 `opal-harness.md §2`·`§6` 포인터 grep 존재 |
| TS-006 | R-2 AC (포인터 정합) | 통합 테스트 | opal-pm.md 내 `→ opal-harness.md §2`·`opal-harness.md §6`·`opal-model-mapping.md §5` 포인터가 실제 존재 헤딩 지시(dangling 0) |

---

### F-003: 부트스트래퍼 자동관리 → 신규 reference 이관

#### 3.3.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/core/references/bootstrapper-management.md` | 문서 | 부트스트래퍼 자동관리 상세(4 플랫폼 정책 + 수동 삽입 마커 블록) | (→ TASK R-3) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 문서 | `## 프로젝트 부트스트래퍼 자동 관리` 절(397~445) 제거 (F-001 일괄). step6(L37) 포인터는 F-005에서 갱신 | (→ §2.3) |

#### 3.3.2 설계 — bootstrapper-management.md 구조

```
# OPAL 프로젝트 부트스트래퍼 자동 관리
> 설치/프로젝트 진입 시점 가이드 (런타임 비행동). 탐색: ~/.opal/references/bootstrapper-management.md
> 출처: opal/core/AGENT.md §프로젝트 부트스트래퍼 자동 관리 (050 이관)

## 개요 (2-tier: 전역=비서 / 프로젝트=PM·이식성)   ← AGENT.md 397~399 이동
## Claude Code — 자동 삽입 스킵                     ← 401~421 이동 (수동 삽입 마커 블록 포함)
## Cursor — 자동 삽입 스킵                           ← 423~425 이동
## Codex — 자동 삽입 스킵                            ← 427~434 이동
## Antigravity(Gemini) — 자동 삽입 수행              ← 436~444 이동
## 변경이력
| v1.0 | 2026-06-30 ... | AGENT.md §부트스트래퍼 자동 관리 이관 (050) |
```

> **[MUST] 마커 블록(414~421) 의미 불변 이동** — install `extract_bootstrap_content`는 bootstrapper/ 파일을 쓰므로 무영향(→ §2.3.2). **[MUST] TS-006(049) 2-tier 반전 서술 보존** — 049가 이 절에 심은 "전역 마커는 비서 tier 상시 활성화" 논리를 신규 문서에 그대로 유지.

#### 3.3.3 환경 변경
해당 없음.

#### 3.3.4 배치/마이그레이션
해당 없음. (install 재배포는 캡틴 — 배포 경계).

#### 3.3.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | R-3 AC (reference 존재) | 산출물 검사 | `bootstrapper-management.md` 존재 + 4 플랫폼 소절(Claude/Cursor/Codex/Gemini) + 수동 삽입 마커 블록(`# === OPAL START ===`) grep 잔존 |
| TS-008 | R-3 AC (AGENT.md 포인터만) | 산출물 검사 | AGENT.md에 `## 프로젝트 부트스트래퍼 자동 관리` 절 부재 + step6/포인터에 `bootstrapper-management.md` 참조 1줄 존재 |
| TS-009 | R-3 AC (install 불변) | 회귀 테스트 | `bash -n scripts/install-mac.sh` exit 0 + `install_opal_section`·`extract_bootstrap_content` 호출부 불변(AGENT.md 마커 블록 이동이 install 무영향) |

---

### F-004: 변경이력 trim

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 문서 | 변경이력 표를 최근 5(v3.8~v4.0) + 050 신규 행으로 trim + "전체 이력: git log" 안내 | (→ §2.4) |

#### 3.4.2 설계

```markdown
## 변경이력

> 전체 이력: `git log --follow opal/core/AGENT.md`

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v3.8 | 2026-06-28 | (보존) |
| v3.9 | 2026-06-28 | (보존) |
| v3.10 | 2026-06-28 | (보존) |
| v3.11 | 2026-06-28 | (보존) |
| v4.0 | 2026-06-30 16:37 | (보존 — 049) |
| v4.1 | 2026-06-30 17:xx | 다이제스트 — PM 섹션(역할전환 상세·L2·code-scan/brain 활용·메모리브리핑·모델매핑 적용·프로젝트 컨텍스트) → opal-pm.md 이관(dedup: 3-way·모델매핑 우선순위 포인터 단일화). 부트스트래퍼 자동관리 → bootstrapper-management.md 신규 이관. 변경이력 trim. 교차참조 갱신(X-1~X-3). (050) |
```

> **[MUST] 049(v4.0) 행 보존 + 050(v4.1) 신규 행 추가**(H-6). v1.0~v3.7 구간만 제거. KST 일시 필수.

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R-4 AC (≤5행+링크) | 산출물 검사 | 변경이력 표 데이터 행 ≤6(최근 5 + 050) + "전체 이력: git log" 안내 1줄 grep 존재 |
| TS-011 | R-4 AC (049·050 보존) | 산출물 검사 | 변경이력에 `(049)` 행 + `(050)` 행 grep 잔존 |

---

### F-005: 교차참조 갱신 (dangling 0)

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/AGENT.md` | 문서 | X-1(L37 부스 포인터)·X-2(L265 code-scan 포인터)·X-3(L266 brain 포인터) 갱신 | (→ §2.5.2 X 표) |

#### 3.5.2 설계 — 포인터 갱신 (3건)

| # | 변경 전 | 변경 후 |
|---|---------|---------|
| X-1 (L37) | `(아래 "프로젝트 부트스트래퍼 자동 관리" 참조)` | `(상세: references/bootstrapper-management.md)` |
| X-2 (L265 도구 인지 맵 "첫 사용 시 로드" 칼럼) | `§code-scan 활용 규칙` | `opal-pm.md §code-scan 활용 규칙` |
| X-3 (L266 도구 인지 맵 "첫 사용 시 로드" 칼럼) | `§opal-brain 활용 규칙` | `opal-pm.md §opal-brain 활용 규칙` |

> **[MUST] dangling 0 검증**: 갱신 후 `grep -rn "AGENT.md §" opal/ docs/`로 잔여 dangling 없음 확인. X-4~X-10(잔류·비-core)은 불변. (→ §2.5.2)

#### 3.5.3 환경 변경 / 3.5.4 배치
해당 없음.

#### 3.5.5 테스트 시나리오

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R-5 AC (dangling 0) | 통합 테스트 | `grep -rn "AGENT.md §\|프로젝트 부트스트래퍼 자동 관리\|§code-scan 활용 규칙\|§opal-brain 활용 규칙" opal/ docs/`에서 이동 섹션을 가리키는 dangling 0 (잔류·비-core 참조 제외) |
| TS-013 | R-5 AC (포인터 유효) | 통합 테스트 | X-2·X-3 갱신된 포인터의 대상 헤딩이 opal-pm.md에 실제 존재 + X-1 포인터 대상 `bootstrapper-management.md` 실제 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-002, F-003 | 1, 2 | opal-task-agent | 순차(동일 파일 충돌) | 수신처 먼저 작성(opal-pm.md 수신 + 신규 reference) |
| 2 | F-001, F-004 | 3, 4 | opal-task-agent | 순차(AGENT.md 동일 파일) | AGENT.md 이관 섹션 제거 + 변경이력 trim |
| 3 | F-005 | 5 | opal-task-agent | 순차 | 이동 확정 후 포인터 갱신 |

> **순차 근거**: Step 3·4·5가 모두 `opal/core/AGENT.md` 단일 파일을 수정 → 파일 충돌 방지 위해 한 워커가 순차 처리. Step 1(opal-pm.md)·Step 2(신규 reference)는 독립 파일이나, AGENT.md에서 원문을 옮기는 것이므로 **수신처 먼저(Phase 1) → AGENT.md 제거(Phase 2)** 순서가 안전(이동 중 원문 유실 방지).

### 4.2 실행 체크리스트

> 총 6개 Step | Phase 3개 | 실행 모드: 복잡 (변경/생성 파일 3개 + 다단계 이동·dedup·교차참조)

#### Step 1: opal-pm.md PM 섹션 수신 + dedup 병합
- [x] 완료
- **소속 기능**: F-002
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-pm.md` (수신), `opal/core/AGENT.md` (이동 원문 참조 — 이 Step에서는 Read만)
- **작업 내용**: AGENT.md 127~192(역할전환 상세·L2)·194~252(code-scan/brain 활용)·350~395(메모리브리핑·모델매핑)·446~454(프로젝트 컨텍스트)를 opal-pm.md 신규 절(§12~§17)로 **원문 복사 이동**. **[MUST] dedup**: 하네스 3-way → `opal-harness.md §2` 포인터, 모델매핑 우선순위 → `opal-harness.md §6 + opal-model-mapping.md §5` 포인터로 단일화(표 복사 금지). §9 code-scan 관리 의무와 신규 "활용 규칙" 중복 서술 제거. opal-pm.md 변경이력에 050 행 추가.
- **완료 기준**: opal-pm.md에 이관 7섹션 존재(TS-004) + 3-way/모델매핑 표 신설 부재 + 포인터 존재(TS-005) + 포인터 dangling 0(TS-006)
- **테스트**: TS-004, TS-005, TS-006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: bootstrapper-management.md 신규 생성 + 부트스트래퍼 절 수신
- [x] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/bootstrapper-management.md` (신규), `opal/core/AGENT.md` (397~445 Read만)
- **작업 내용**: AGENT.md 397~445 `## 프로젝트 부트스트래퍼 자동 관리`(4 플랫폼 정책 + 수동 삽입 마커 블록 414~421)를 신규 reference로 **원문 복사 이동**(§3.3.2 구조). 2-tier 반전 서술(049 TS-006) 보존. 변경이력 v1.0(050) 행 작성.
- **완료 기준**: reference 존재 + 4 플랫폼 소절 + 마커 블록 grep 잔존(TS-007)
- **테스트**: TS-007
- **실행 방법**: sub-agent
- **의존**: 없음 (Step 1과 독립 파일 — 병렬 가능하나 Phase 1 묶음)

#### Step 3: AGENT.md 이관 섹션 제거 (비서 코어 잔류)
- [ ] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: §2.1.2 표 "이관"·"dedup 제거" 행(127~252 중 PM 전용·350~395·397~454)을 제거. 유지 섹션 **문구 불변**. `### 역할 전환` 헤더 + `#### 상태 정의` 잔류. 도구 인지 맵·주도성·기억과학습 stub·보고형식·부트스트랩·정체성·핵심역할 잔류. (변경이력은 Step 4, 포인터 갱신은 Step 5)
- **완료 기준**: 이관 섹션 헤딩 grep 0(TS-001) + 부트스트랩 보존(TS-002) + 비서 코어 7항목 잔존(TS-003)
- **테스트**: TS-001, TS-002, TS-003
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2 (수신처 작성 완료 후 원문 제거 — 유실 방지)

#### Step 4: AGENT.md 변경이력 trim
- [ ] 완료
- **소속 기능**: F-004
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: 변경이력 표를 최근 5(v3.8~v4.0) + 050(v4.1) 신규 행 + "전체 이력: git log" 안내로 trim. v1.0~v3.7 제거. 049(v4.0) 행 보존.
- **완료 기준**: 표 ≤6행 + git 링크(TS-010) + 049·050 행 존재(TS-011)
- **테스트**: TS-010, TS-011
- **실행 방법**: sub-agent
- **의존**: Step 3 (동일 파일 순차)

#### Step 5: AGENT.md 교차참조 갱신 (X-1·X-2·X-3)
- [ ] 완료
- **소속 기능**: F-005
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: §3.5.2 표대로 X-1(step6 부스 포인터)·X-2(code-scan 포인터)·X-3(brain 포인터) 3건 갱신. 갱신 후 `grep -rn "AGENT.md §" opal/ docs/`로 dangling 0 확인.
- **완료 기준**: dangling 0(TS-012) + 포인터 대상 실존(TS-013)
- **테스트**: TS-012, TS-013
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 2, Step 3 (이동 확정 후)

#### Step 6: 회귀 검증 — 049 TS-001~004 재실행 + 비서 코어 완결 (PM 직접)
- [ ] 완료
- **소속 기능**: F-001 (R-6 가로 제약)
- **영역**: 문서
- **agent**: PM 직접 (TEST 단계 — 오케스트레이터 책임. opal-test-agent 디스패치는 PM 판단)
- **파일**: `opal/core/AGENT.md`, `tasks/049-.../TEST-SCENARIO.md` (회귀 기준)
- **작업 내용**: 049 TS-001(2-phase)·TS-002(게이트)·TS-003(`//`불변식)·TS-004(step0)의 정적 grep 단언을 다이제스트 후 AGENT.md에 재실행하여 PASS 확인. 부트스트랩 Eager 절차·완료보고·2-tier 게이트 보존 확인. L3 실세션은 캡틴 수동(graceful skip).
- **완료 기준**: 049 TS-001~004 재실행 PASS + 비서 코어 완결성 점검 통과
- **테스트**: TS-014 (회귀)
- **실행 방법**: direct (PM Gate / TEST 단계에서 수행)
- **의존**: Step 3, Step 4, Step 5

> **docs/ 갱신 Step 불요**: 본 태스크는 AGENT.md 내부 섹션 이동으로, docs/ARCHITECTURE.md의 2-tier 부트스트랩 서술(049에서 갱신됨)·PROJECT.md 레지스트리에 영향을 주는 **시스템 구조 변경·신규 API·신규 패턴이 아니다**. 신규 reference(bootstrapper-management.md)는 PROJECT.md 문서 레지스트리 등록 여부를 PM이 판단(레지스트리에 references/ 개별 파일을 등재하지 않는 관례면 스킵). → docs/ 갱신은 PM Gate에서 판단, 자동 Step 생성하지 않음.

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| Step 1 ∥ Step 2 | 독립 파일(opal-pm.md vs 신규 reference). 병렬 가능하나 Phase 1로 묶음 |
| Step 1·2 → Step 3 | 수신처 작성 완료 후 AGENT.md 원문 제거 (이동 중 유실 방지) |
| Step 3 → Step 4 → Step 5 | 동일 파일(`opal/core/AGENT.md`) 순차 수정 — 파일 충돌 방지 |
| Step 3·4·5 → Step 6 | 모든 변경 완료 후 회귀 검증 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA

| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | 이관 섹션 제거 + 비서 코어 완결 | TS-001, TS-003 | 이관 헤딩 grep 0 + 필수 7항목 잔존 |
| F-002 | opal-pm.md 수신 + dedup | TS-004, TS-005, TS-006 | 7섹션 존재 + 3-way/모델매핑 표 신설 부재 + 포인터 유효 |
| F-003 | bootstrapper-management.md 신규 + install 불변 | TS-007, TS-008, TS-009 | reference 4플랫폼+마커 + AGENT.md 포인터만 + bash -n exit 0 |
| F-004 | 변경이력 trim | TS-010, TS-011 | ≤6행+링크 + 049·050 보존 |
| F-005 | dangling 0 | TS-012, TS-013 | 이동 섹션 dangling 0 + 포인터 실존 |

### 5.2 회귀 테스트
- [ ] 049 TS-001(Eager 2-phase) 재실행 PASS — AGENT.md Phase A/B 구분 보존
- [ ] 049 TS-002(PM tier 게이팅) 재실행 PASS — `.opal/AGENT.md` 부재 시 Phase B 스킵 서술 보존
- [ ] 049 TS-003(`//` 불변식) 재실행 PASS — Phase A `//`(opi) 발동 + Lazy 트리거 전제조건 부재 보존
- [ ] 049 TS-004(step0 스킵게이트) 재실행 PASS — setting.json 게이트+fail-safe+models 보존
- [ ] 부트스트랩 완료 보고 형식(비서 세션 `⬜ harness ⬜ PM ⬜ PM모드`) 보존
- [ ] opal-pm.md §8 → `AGENT.md §보고 형식` 참조 불변(보고 형식 잔류)

### 5.3 코드/문서 품질
- [ ] 유지 섹션 문구 불변(Surgical — PRINCIPLES.md §3): 이관·trim·포인터화 외 인접 개선 없음
- [ ] 신규 reference는 bootstrapper-management.md 1개만(PRINCIPLES.md §2 — 추가 파일 생성 없음)
- [ ] 변경이력 행: AGENT.md(050) + opal-pm.md(050) + bootstrapper-management.md(v1.0/050) — KST 일시 포함
- [ ] dedup: 이동 본문이 목적지에서 중복 신설 아님(3-way·모델매핑 포인터 단일화)

### 5.4 보안
- [ ] 이동/신규 문서에 하드코딩 토큰/시크릿 없음(부트스트래퍼 마커는 진입 지시만)
- [ ] 신규 권한 표면 0(reference 문서는 Read 대상, 신규 MCP/권한 등록 없음)

---

## 6. 복잡도 판별

| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 6개 | 복잡 (6 이상) |
| 변경 파일 수 | 3개 (AGENT.md 수정 + opal-pm.md 수정 + bootstrapper-management.md 신규) | 단순 경계 |
| 모듈 범위 | 다중 문서(AGENT.md ↔ opal-pm.md ↔ 신규 reference + 교차참조 전수) | 복잡 |
| 작업 유형 | 대규모 다이제스트(이동·dedup·trim·교차참조) | 복잡 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **복잡** | (Step 6개 + 다중 문서 + 다단계 이동·dedup) |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지

```
Batch 1 (Phase 1, 병렬 가능 — 독립 수신처):
  W1: opal-task-agent — Step 1 (opal-pm.md 수신 + dedup)
  W2: opal-task-agent — Step 2 (bootstrapper-management.md 신규)
Batch 2 (Phase 2, 순차 — AGENT.md 단일 파일):
  W3: opal-task-agent — Step 3 → Step 4 (AGENT.md 제거 + 변경이력 trim, 한 워커 순차)
Batch 3 (Phase 3):
  W3(연속) 또는 신규: opal-task-agent — Step 5 (교차참조 갱신)
Batch 4 (검증):
  PM 직접 / opal-test-agent — Step 6 (049 회귀 재실행)
```

> **그룹핑 원칙**: AGENT.md를 수정하는 Step 3·4·5는 **반드시 같은 워커**(파일 충돌 방지). opal-pm.md(Step 1)·신규 reference(Step 2)는 독립 파일 → 별도 워커 병렬 가능.

### C-2. 스킬 요구사항

- 기존 스킬 매칭: **op-dev-execute**(EXECUTE 단계 문서 수정 — 일반 텍스트 이동). 신규 스킬 갭 없음(문서 이동은 인라인 지침으로 충분).
- 갭 판별: 동일 패턴(섹션 이동) 3 Step 이상이나 단일 태스크 1회성 → 스킬화 불요, 인라인 지침.

### C-3. 도구 요구사항

- `grep`(교차참조 전수·정적 단언), `bash -n`(install 구문 무결 TS-009). 신규 CLI/MCP/패키지 없음.

### C-4. 테스트 전략

- **RED-first 판단**: §TEST-SCENARIO RED-first 트랙 참조. 본 태스크는 문서 이동·정리라 동작 로직 RED-first 적격 항목이 **거의 없다**. TS-001~013은 정적 grep(구현-후-검증), TS-014는 049 회귀(L1 정적 재실행 + L3 캡틴 수동).
- **정적 단언 자동화**: opal-test-agent가 grep/`bash -n` 일괄 수행(결정론적 PASS/FAIL).
- **회귀**: 049 TEST-SCENARIO.md의 TS-001~004 grep 단언을 다이제스트 후 AGENT.md에 재실행.
- **L3 실세션**: 부트스트랩 LLM 거동 → 캡틴 수동(graceful skip). 정적 단언이 결정론적 핵심 게이트.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택

| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown (AGENT.md·opal-pm.md·references) | op-dev-execute |
| 검증 | grep(교차참조 전수·정적 단언), bash -n(install) | op-dev-test |

### 8.2 사용 MCP

| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 문서 이동 태스크 — 외부 라이브러리 문서 조회 불요 |

### 8.3 참조 문서 (설계 결정 근거)

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | AGENT.md (부트스트랩 SSOT) | `opal/core/AGENT.md` | 다이제스트 대상 — line 단위 섹션 진단(§2.1.2) |
| D-2 | 설계 | opal-pm.md (PM 행동 프로세스) | `opal/core/references/opal-pm.md` | PM 섹션 수신 목적지(주) + §8·§9 dedup 기준 |
| D-3 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | 하네스 3-way(§2)·모델매핑(§6) 기존 보유 — dedup 포인터 단일화 기준 |
| D-4 | 설계 | 049 TEST-SCENARIO (회귀 기준) | `tasks/049-260630-opds-부트스트랩-프로젝트레벨-전환/TEST-SCENARIO.md` | TS-001~004 회귀 재실행 + TS-006 2-tier 반전 보존 |
| D-5 | 소스 | install-mac.sh (배포 파이프라인) | `scripts/install-mac.sh:227,241,1042` | strip_deploy_md(변경이력 배포 strip — R-4 런타임 영향 0 근거) + extract_bootstrap_content(F-003 install 무영향 근거) |
| D-6 | 설계 | PRINCIPLES.md (헌법) | `opal/core/PRINCIPLES.md` §2·§3 | [MUST] Surgical(의미 불변)·신규 추상화 금지(reference 1개 한정) |

> [MUST] `opal/core/PRINCIPLES.md` §3 Surgical: 의미 개정·인접 개선 금지 — 순수 이동·dedup·trim.
> [MUST] `opal/core/PRINCIPLES.md` §2: 신규 추상화 금지 — 신규 reference(bootstrapper-management.md) 1개 외 불필요 파일 생성 금지.

---

## 9. 리스크 및 대응 (기능-리스크 연결)

| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | 잔류 도구 인지 맵 포인터(§code-scan/§opal-brain)가 이동 섹션 가리켜 dangling | F-002·F-005 | P1 | Step 5에서 `opal-pm.md §...`로 갱신 + TS-012/TS-013 grep 검증 |
| H-2 | 하네스 3-way dedup 누락 → opal-pm.md 중복 신설 | F-002 | P1 | Step 1 [MUST] dedup: `opal-harness.md §2` 포인터만. TS-005 표 신설 부재 검증 |
| H-3 | 비서 코어 정보 손실(과도한 절삭) | F-001 | P0 | §3.1.2 완결성 7항목 점검 + TS-003 grep. 도구 인지 맵 잔류(비서도 도구 선제 활용) |
| H-4 | step6 부스 포인터(L37) dangling | F-003·F-005 | P0 | Step 5 X-1 갱신 → `bootstrapper-management.md`. TS-008 검증 |
| H-5 | 부트스트랩 2-tier 게이트·완료보고 동작 회귀 | F-001 | P0 | 유지 섹션 문구 불변(Surgical) + Step 6 049 TS-001~004 재실행 + L3 캡틴 수동 |
| H-6 | 변경이력 049·050 행 누락 | F-004 | P2 | Step 4 [MUST] 049 보존+050 추가. TS-011 검증 |
| H-7 | opal-pm.md 비대화로 PM 세션 토큰 급증 | F-002 | P2 | 이동(중복 없음) → PM tier 토큰 중립. dedup 포인터로 추가 압축. 줄수 측정 |

---

## 설계 피드백 (PM 검토용)

1. **측정 정정(중요)**: TASK가 전제한 "493줄 매 세션 로드"는 부정확하다. 배포 시 `strip_deploy_md`가 변경이력을 제거하여 **런타임은 455줄**이다(직접 검증). 따라서 **R-4(변경이력 trim)는 런타임 토큰 경감 0**(소스 위생 항목)이고, 실제 비서 세션 경감은 **R-2·R-3(PM 섹션 이동 ≈ 250줄)**에서 발생한다. lean core ~205줄 목표는 **런타임 body 455줄 - 이관 250줄 ≈ 205줄**로 정합한다.

2. **dedup 2건 확정**: 하네스 3-way(`opal-harness.md §2`)·모델매핑 우선순위(`opal-harness.md §6`)는 목적지에 **이미 존재** → opal-pm.md에 표 복사 금지, 포인터 단일화. 이것이 "이동"이 아니라 "제거+단일화"인 핵심 dedup 지점이다.

3. **규모 판정 — Full Task(opd) 에스컬레이션 불요**: 변경 파일 3개(AGENT.md 수정·opal-pm.md 수정·신규 reference 1개) + Step 6개로 복잡 모드이나, **단일 영역(문서)·외부 의존 0·신규 추상화 0**이다. opds(Short) 범위 내 처리 가능. 다만 Step 수가 6개로 Short 권장(5 이하)을 1개 초과하므로, PM이 Step 3·4를 1 Step으로 병합(AGENT.md 일괄 편집)하면 5 Step으로 축소 가능 — **PM 재량 권고**.

4. **잔류 경계 미세 판단(구현자 주의)**: `### 역할 전환`의 `#### 상태 정의`(비서/PM 소형 표)는 비서 코어로 잔류, 그 하위 `#### PM 내 하네스 적용 기준`부터 L2까지는 PM 전용으로 이관한다. 헤더(`### 역할 전환`)는 잔류 표를 담기 위해 유지하되, "비서/PM 상태 정의" 의미만 남긴다. 이 경계가 모호하면 보수적으로 더 많이 잔류시켜 비서 코어 완결성(H-3)을 우선한다.
