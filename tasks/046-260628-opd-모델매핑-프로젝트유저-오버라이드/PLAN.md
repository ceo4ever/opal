# PLAN: 모델 매핑 provider별·등급별 오버라이드 (프로젝트/유저 2계층 setting)

> 작성일: 2026-06-28 | 입력: TASK.md, ANALYSIS.md
> 모드: Flat (단일 기능)
> 작성 주체: PM 직접 (op-dev-plan 워커 3회 연속 API 인프라 오류로 미산출 → agentic 완수 의무에 따른 PM 폴백, AGENTIC-LOG #9~#13)

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

OPAL 레벨↔모델 매핑(`light`/`standard`/`advanced` ↔ 플랫폼 모델)을 유저 전역(`~/.opal/setting.json`)·프로젝트(`{프로젝트}/.opal/setting.local.json`) `models` 블록으로 **provider별·등급별 오버라이드**한다. 우선순위는 **프로젝트 → 유저 → 매핑 표**(셀 단위 deep merge)이며, install 전역 베이킹은 무설정 시 fallback으로 불변 유지한다. 본 태스크는 Markdown 지시 문서 편집 + 정합 검증만 수행한다(실행 코드 경로 신설 없음).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | 모델 매핑 2계층 오버라이드 명세·지시·정합 | R-1, R-2, R-3, R-4, R-5 | P0 | 없음 |

### 1.3 기능 의존 그래프

단일 기능 — 생략 (Flat 모드).

---

## 리스크 가설 표

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | `opal-model-mapping.md` §5.1 (S1) | 폴백 입도 모호 → 런타임 오케스트레이터가 provider 블록 전체 누락 vs level 셀 누락을 다르게 해석 | P1 | L1(문서 정적) | S-1 |
| H-2 | `AGENT.md`:371 vs `opal-model-mapping.md` §5.1 (S1·S2) | 두 문서의 폴백 규칙 입도 불일치 → 지시-명세 모순 | P1 | L1(문서 정적·교차) | S-2 |
| H-3 | `opal-model-mapping.md` §5.2 Cursor (S1) | cursor=inherit인데 스키마가 등급핀 가능한 것처럼 오해 유발 | P2 | L1(문서 정적) | S-3 |
| H-4 | `agents.md` Codex 인라인 주입 (S4) | 오버라이드 도입 서술이 기존 Codex 매핑 서술과 충돌 | P2 | L1(문서 정적·교차) | S-4 |
| H-5 | 변경이력/헤더 버전 (S5) | 헤더 버전과 변경이력 최신 행 불일치 → 문서 표준 위반 | P2 | L1(grep) | S-5 |
| H-6 | install 스크립트 (R-4) | EXECUTE가 실수로 install 베이킹 dict를 건드려 전역 기본값 변동 | P1 | L1(git diff) | S-6 |
| H-7 | `setting.local.json` DX (S1) | 사용 예/위치 미문서화 → 사용자가 기능 미활용 | P2 | L1(문서 정적) | S-7 |

**가설 도출 근거**: ANALYSIS §5 리스크 R-T1~R-T6 + §8 결정사항 P-1~P-3 매핑. 본 태스크는 런타임 코드 경로가 없으므로 모든 검증은 L1(문서 정적/교차/grep/diff) 계층이다.

---

## 2. 기능별 분석 (Flat)

### 2.1 관련 파일 맵

| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/opal-model-mapping.md` | 매핑 SSOT + §5 오버라이드 명세 | 수정 |
| 문서 | `opal/core/AGENT.md` | §모델 매핑 자동 적용 — 디스패치 직전 머지 지시 | 수정 |
| 문서 | `opal/core/references/opal-harness.md` | §6 Model Mapping 공통 인프라 | 수정(1줄 포인터) |
| 문서 | `opal/core/references/agents.md` | Codex 인라인 주입 정합 확인 | 검토(필요 시 수정) |
| 환경 | `scripts/install-mac.sh` | 전역 베이킹 | **불변**(검증만) |

### 2.2 현재 구현 (ANALYSIS 참조)

- 모델 결정 경로 2종: install 전역 베이킹(`scripts/install-mac.sh:563-567`, `:738-741`) / 런타임 디스패치 직전 머지(`opal/core/AGENT.md:371`). 프로젝트 오버라이드는 런타임 경로로만 가능 (ANALYSIS §1.2).
- spike 편집 현황: `opal-model-mapping.md` §5(v1.6) 완성, `AGENT.md`(v3.8) 머지 지시 본체 초안 존재하나 폴백 입도 미명시 (ANALYSIS §4.1·§4.2).

### 2.3 영향 범위

- 직접: `opal-model-mapping.md`, `AGENT.md` (ANALYSIS §3.1).
- 간접: `agents.md`(정합), `opal-harness.md` §6(포인터), 배포본은 install 동기화 (ANALYSIS §3.2).
- DB/API/빌드 변경 없음 (ANALYSIS §3.3).

---

## 3. 기능별 설계 (Flat)

### 3.1 파일 변경 계획

**수정**

| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-model-mapping.md` | 문서 | §5.1 폴백 입도 정밀화 + §5.2/§5.3 Cursor inherit 주석 + setting.local.json 사용 예 스니펫 | ANALYSIS §8 P-1·P-2, R-T4 |
| 2 | `opal/core/AGENT.md` | 문서 | §모델 매핑 자동 적용 본체에 셀 단위 폴백 입도(provider 블록 vs level 셀) 명시 보강 | ANALYSIS §4.2 R-2/R-T2 |
| 3 | `opal/core/references/opal-harness.md` | 문서 | §6에 오버라이드 머지 1줄 포인터 추가 | ANALYSIS §8 P-3 |
| 4 | `opal/core/references/agents.md` | 문서 | Codex 인라인 주입 섹션 정합 확인, 모순 시 1줄 보강 | ANALYSIS §5 R-T5 |
| 5 | (위 1·2 문서) | 문서 | 변경이력 행 + 헤더 버전 정합 최종 확인 | R-3 |

### 3.2 설계 결정 (핵심)

- **D-결정1 (폴백 입도, P-1)**: `opal-model-mapping.md` §5.1에 다음 입도를 명문화한다 — "`models[provider]` 블록 전체가 없으면 그 provider의 모든 level 셀이 다음 우선순위로 폴백한다. 블록은 있으나 특정 level 키가 없거나 값이 `"default"`이면 그 셀만 폴백한다." (ANALYSIS §8 P-1, `opal/core/references/opal-model-mapping.md:86-87`)
- **D-결정2 (Cursor, P-2)**: cursor는 install에서 모든 레벨 `inherit`(IDE 위임, `scripts/install-mac.sh:565`)이므로 등급별 모델 핀 대상이 아니다. 스키마에 cursor 블록을 강제하지 않고 §5.2 또는 §5.3에 주석 1줄을 둔다 — "`cursor`: IDE 위임(inherit) — 등급별 모델 핀 N/A. `platform` 강제 시에도 실모델 지정 불가." (ANALYSIS §4.4, `opal/core/references/opal-model-mapping.md:64-73`)
- **D-결정3 (harness 포인터, P-3)**: `opal-harness.md` §6(`:178-187`)에 "오버라이드 우선순위: setting.local.json → setting.json → 표. 상세 §5" 1줄 포인터를 추가한다. (ANALYSIS §8 P-3)
- **D-결정4 (AGENT.md 본체, R-2)**: `AGENT.md:371` 머지 지시에 D-결정1의 입도 표현을 반영해 명세와 일치시킨다.
- **D-결정5 (install 불변, R-4)**: `scripts/install-mac.sh`는 변경하지 않는다. §5.3에 "install은 전역 베이킹만" 경계가 문서화되어 있음을 확인한다. [MUST] `opal/core/references/opal-model-mapping.md` §5.3: "install(배포)은 전역에만 작용한다 … 프로젝트 단위 베이킹은 수행하지 않으며 setting.local.json도 생성하지 않는다."

### 3.3 환경 변경

해당 없음 (패키지·빌드 무변).

### 3.4 배치/마이그레이션

해당 없음.

### 3.5 테스트 시나리오 (AC ↔ TS 매핑)

| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| S-1 | R-1 / H-1 | L1 정적 | `opal-model-mapping.md` §5.1에 "provider 블록 전체 누락→전 셀 폴백 / level 셀 누락·default→그 셀만 폴백" 입도 문구가 존재 |
| S-2 | R-2 / H-2 | L1 교차 | `AGENT.md` §모델 매핑 머지 지시의 폴백 입도가 §5.1과 동일 의미로 일치(모순 0건) |
| S-3 | R-1 / H-3 | L1 정적 | §5.2 또는 §5.3에 cursor=inherit·등급핀 N/A 주석 1줄 존재 |
| S-4 | R-5 / H-4 | L1 교차 | `agents.md` Codex 인라인 주입 서술과 오버라이드 명세 간 충돌 문장 0건 |
| S-5 | R-3 / H-5 | L1 grep | `opal-model-mapping.md` 헤더 버전 == 변경이력 최신 행, `AGENT.md` 동일 |
| S-6 | R-4 / H-6 | L1 diff | `git diff scripts/install-mac.sh` 결과 0줄 |
| S-7 | R-1 / H-7 | L1 정적 | §5에 setting.local.json 사용 예(JSON 스니펫) + 위치 안내 존재 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑

| Phase | 기능 | Step | 실행 | 비고 |
|-------|------|------|------|------|
| P1 | F-001 | S1, S2, S3 | 순차(동일 워커, 문서 간 정합 필요) | 명세·지시·포인터 작성 |
| P2 | F-001 | S4, S5 | 순차 | 정합 검토 + 버전 최종 확인 |

문서 편집은 상호 정합이 중요하므로 단일 워커가 S1→S5 순차 수행한다(병렬 이점 없음).

### 4.2 실행 체크리스트

> 총 5개 Step | Phase 2개 | 실행 모드: 단순

#### Step 1 (S1): opal-model-mapping.md §5 정밀화
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-model-mapping.md`
- **작업 내용**: §5.1에 폴백 입도(D-결정1) 명문화 / §5.2 또는 §5.3에 Cursor inherit 주석(D-결정2) / §5에 setting.local.json 사용 예 JSON 스니펫 + 위치 안내(R-T4) 추가
- **완료 기준**: S-1·S-3·S-7 PASS
- **테스트**: S-1, S-3, S-7
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2 (S2): AGENT.md 머지 지시 본체 보강
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/AGENT.md`
- **작업 내용**: §모델 매핑 자동 적용 머지 지시(`:371`)에 셀 단위 폴백 입도(D-결정4)를 §5.1과 동일 의미로 반영
- **완료 기준**: S-2 PASS
- **테스트**: S-2
- **실행 방법**: sub-agent
- **의존**: S1

#### Step 3 (S3): opal-harness.md §6 포인터
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-harness.md`
- **작업 내용**: §6 Model Mapping에 오버라이드 우선순위 1줄 포인터(D-결정3) 추가
- **완료 기준**: §6에 "setting.local.json → setting.json → 표 / 상세 §5" 포인터 존재
- **테스트**: 정적 확인
- **실행 방법**: sub-agent
- **의존**: S1

#### Step 4 (S4): agents.md 정합 검토
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/agents.md`
- **작업 내용**: Codex tool-backed 인라인 주입 섹션을 Read하여 오버라이드 명세와 모순 여부 검토. 모순 시 1줄 보강, 없으면 무수정 + 검토 결과 기록
- **완료 기준**: S-4 PASS
- **테스트**: S-4
- **실행 방법**: sub-agent
- **의존**: S1

#### Step 5 (S5): 버전 정합 + install 불변 최종 확인
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-model-mapping.md`, `opal/core/AGENT.md`, `scripts/install-mac.sh`(읽기만)
- **작업 내용**: 두 문서 변경이력 최신 행 ↔ 헤더 버전 일치 확인(필요 시 정정). install-mac.sh 미변경(diff 0) 확인
- **완료 기준**: S-5·S-6 PASS
- **테스트**: S-5, S-6
- **실행 방법**: sub-agent
- **의존**: S2, S3, S4

### 4.3 병렬/순차 판별 근거

| 관계 | 근거 |
|------|------|
| S1 선행 | §5.1 입도가 SSOT — S2(지시)·S3(포인터)·S4(정합)가 이를 참조 |
| S2·S3·S4 순차 | 동일 워커 단일 컨텍스트로 문서 간 정합 유지(병렬 이점 없음, 정합 리스크만 증가) |
| S5 최종 | 모든 편집 완료 후 버전·diff 검증 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | §5.1 폴백 입도 명문화 | S-1 | 입도 문구 존재 |
| F-001 | 지시-명세 정합 | S-2 | AGENT.md ↔ §5.1 의미 일치 |
| F-001 | Cursor 처리 | S-3 | inherit 주석 존재 |
| F-001 | 타 문서 정합 | S-4 | agents.md 충돌 0건 |
| F-001 | 버전 정합 | S-5 | 헤더==변경이력 |
| F-001 | install 불변 | S-6 | diff 0줄 |
| F-001 | DX 사용 예 | S-7 | JSON 스니펫 존재 |

### 5.2 회귀 테스트
- [ ] 기존 §2 매핑 표·§4 플랫폼 감지 서술 무손상 (S1 편집이 §2/§4를 깨지 않음)
- [ ] §5 → §6 재번호(기존 갱신 가이드라인) 정상 유지

### 5.3 코드/문서 품질
- [ ] Markdown 헤딩 계층·표 렌더 정상
- [ ] citation 포맷(경로:줄번호) 준수
- [ ] [MUST] 토큰 정확 인용

### 5.4 보안
- [ ] 시크릿/개인식별자 신규 노출 0건 (setting 예제에 실제 키·경로 개인정보 없음)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 5개 | 단순 |
| 변경 파일 수 | 3~4개(문서) | 단순 |
| 모듈 범위 | 단일(문서) | 단순 |
| 작업 유형 | 문서 명세·정합 | 단순 |
| 외부 의존성 | 없음 | 단순 |
| **실행 모드** | **단순** | |

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 문서 | Markdown (OPAL 지시 SSOT) | op-dev-execute |
| 설정 | JSON 스키마 (`models`) | - |
| 검증 | grep / git diff (L1 정적) | op-dev-test-agent |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 라이브러리 불필요 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | opal-model-mapping.md | `opal/core/references/opal-model-mapping.md` | §5 오버라이드 명세 대상 |
| D-2 | 설계 | AGENT.md | `opal/core/AGENT.md` | §모델 매핑 머지 지시 |
| D-3 | 설계 | opal-harness.md | `opal/core/references/opal-harness.md` | §6 포인터 추가 |
| D-4 | 설계 | agents.md | `opal/core/references/agents.md` | Codex 정합 |
| D-5 | 소스 | install-mac.sh | `scripts/install-mac.sh` | 전역 베이킹 불변 확인(:563-567, :738-741, :565 cursor) |
| D-6 | 설계 | ANALYSIS.md | `tasks/046-260628-opd-모델매핑-프로젝트유저-오버라이드/ANALYSIS.md` | 리스크·결정사항 입력 |

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| H-1 | 폴백 입도 모호 | F-001 | P1 | S1에서 명문화, S-1 검증 |
| H-2 | 지시-명세 불일치 | F-001 | P1 | S2에서 §5.1과 동기, S-2 교차 검증 |
| H-3 | Cursor 오해 | F-001 | P2 | S1 주석, S-3 검증 |
| H-4 | agents.md 충돌 | F-001 | P2 | S4 정합 검토, S-4 검증 |
| H-5 | 버전 불일치 | F-001 | P2 | S5 정합, S-5 검증 |
| H-6 | install 오변경 | F-001 | P1 | S5 diff 0 확인(S-6), EXECUTE Guard로 install 수정 금지 |
| H-7 | DX 미활용 | F-001 | P2 | S1 사용 예 스니펫, S-7 검증 |
