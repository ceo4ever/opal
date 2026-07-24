# TEST SCENARIO: 모델 매핑 provider별·등급별 오버라이드 (프로젝트/유저 2계층)

> 작성일: 2026-06-28 | 상태: 작성 완료
> 작성자: 알투(PM) + 캡틴 페어 | PLAN.md 가설 표 기반

> 비고: 본 태스크는 OPAL 지시 문서(Markdown) 편집 + 정합 검증으로, 런타임 코드 경로가 없다. 따라서 모든 시나리오는 **L1(정적 문서/교차/grep/diff) · M1(셸 명령 자동)** 이다. FE/인증/외부 API 변경이 없어 M2(E2E) 의무 트리거 비해당, DB 변경이 없어 L2 비해당, 사용자 수동 판단 불요로 L3 [SUPERVISOR] 비해당.

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | `opal-model-mapping.md` §5.1 | 폴백 입도 모호(블록 누락 vs 셀 누락) → 런타임 오해석 | P1 | L1 | S-1 |
| H-2 | `AGENT.md`:371 ↔ §5.1 | 지시-명세 폴백 입도 불일치 | P1 | L1 | S-2 |
| H-3 | `opal-model-mapping.md` §5.2 | cursor=inherit 오해 | P2 | L1 | S-3 |
| H-4 | `agents.md` Codex 인라인 주입 | 오버라이드 서술과 기존 Codex 매핑 충돌 | P2 | L1 | S-4 |
| H-5 | 변경이력/헤더 버전 | 헤더 버전 ↔ 변경이력 최신 행 불일치 | P2 | L1 | S-5 |
| H-6 | `scripts/install-mac.sh` | EXECUTE가 전역 베이킹 dict 오변경 | P1 | L1 | S-6 |
| H-7 | `setting.local.json` DX | 사용 예/위치 미문서화 → 미활용 | P2 | L1 | S-7 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 본 태스크의 "데이터"는 대상 문서 파일과 그 상태다(DB 없음).

| 파일(테이블 대응) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| `opal/core/references/opal-model-mapping.md` | §5 / §2 표 / 변경이력 / 헤더 | EXECUTE 전: §5 v1.6 초안, 폴백 입도 미정밀 | git working tree |
| `opal/core/AGENT.md` | §모델 매핑 자동 적용(:371) / 변경이력 | EXECUTE 전: 머지 지시 본체 초안, 입도 미명시 | git working tree |
| `opal/core/references/opal-harness.md` | §6 Model Mapping(:178-187) | EXECUTE 전: SSOT 참조만, 포인터 없음 | git working tree |
| `opal/core/references/agents.md` | Codex 인라인 주입 섹션 | EXECUTE 전: 오버라이드 미반영 | git working tree |
| `scripts/install-mac.sh` | mapping dict(:563-567), codex_model_map(:738-741), cursor(:565) | 불변 대상 | git HEAD |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (편집/검증) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | §5.1 현재 문구 | S1 편집(입도 명문화) | §5.1에 블록/셀 폴백 입도 문구 존재 |
| S-2 | AGENT.md:371 + §5.1 | S2 편집(본체 보강) | 두 문서 폴백 입도 의미 일치 |
| S-3 | §5.2/§5.3 | S1 편집(Cursor 주석) | cursor inherit·N/A 주석 1줄 존재 |
| S-4 | agents.md Codex 섹션 | S4 정합 검토 | 오버라이드와 충돌 문장 0건 |
| S-5 | 두 문서 헤더+변경이력 | S5 정합 | 헤더 버전 == 변경이력 최신 행 |
| S-6 | install-mac.sh HEAD | (편집 금지) | git diff 0줄 |
| S-7 | §5 본문 | S1 편집(사용 예) | setting.local.json JSON 스니펫 + 위치 안내 존재 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 문서 입력)

#### S-1: §5.1 폴백 입도 명문화

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | `opal/core/references/opal-model-mapping.md` §5.1 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep)** |
| 조건 | S1 편집 완료 후 |
| 기대 결과 | §5.1에 "provider 블록 전체가 없으면 모든 level 셀 폴백" 및 "특정 level만 없거나 default면 그 셀만 폴백" 취지의 문구가 모두 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "블록 전체\|모든 level\|셀만\|level 키가 없" opal/core/references/opal-model-mapping.md` |
| 결과 | PASS |
| 상세 | 87번 줄: "provider 블록 전체가 없으면 … 모든 level 셀이 다음 우선순위로 폴백" / 88번 줄: "블록은 있으나 특정 level 키가 없거나 값이 default이면 그 셀만 다음 우선순위로 폴백" — 두 입도(블록 전체·셀 단위) 모두 명문화 확인. 총 매칭 5줄. |

#### S-2: 지시 ↔ 명세 폴백 입도 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | `opal/core/AGENT.md`:371 ↔ `opal-model-mapping.md` §5.1 |
| 계층 | L1 (교차) |
| **실행 방식** | **M1 (grep + 대조 판독)** |
| 조건 | S1·S2 편집 완료 후 |
| 기대 결과 | AGENT.md 머지 지시의 폴백 입도가 §5.1과 동일 의미(블록 vs 셀 단위)로 기술, 모순 0건 |
| 도구 | grep |
| 실행 명령 | `grep -n "블록 전체\|모든 level\|셀만\|폴백 입도" opal/core/AGENT.md` |
| 결과 | PASS |
| 상세 | 372번 줄: "폴백 입도: models[provider] 블록 전체가 없으면 그 provider의 모든 level 셀이 다음 우선순위로 폴백한다. 블록은 있으나 특정 level 키가 없거나 값이 default이면 그 셀만 폴백한다." — opal-model-mapping.md §5.1과 동일 의미(블록 vs 셀 단위) 확인. 모순 0건. |

#### S-3: Cursor inherit 주석

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `opal-model-mapping.md` §5.2 또는 §5.3 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep)** |
| 조건 | S1 편집 완료 후 |
| 기대 결과 | "cursor … inherit … 등급(별) 핀 N/A" 취지 주석 1줄 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "cursor.*inherit\|inherit.*N/A\|등급.*핀.*N/A" opal/core/references/opal-model-mapping.md` |
| 결과 | PASS |
| 상세 | 109번 줄: "cursor: IDE 위임(inherit) — 등급별 모델 핀 N/A. platform 강제 시에도 실모델 지정 불가." — cursor inherit 주석 1줄 존재 확인. |

#### S-4: agents.md Codex 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | `opal/core/references/agents.md` Codex 인라인 주입 섹션 |
| 계층 | L1 (교차) |
| **실행 방식** | **M1 (Read + 대조 판독)** |
| 조건 | S4 검토 완료 후 |
| 기대 결과 | 오버라이드 명세(프로젝트>유저>표)와 agents.md Codex 매핑 서술 간 충돌 문장 0건. 검토 결과가 Step 산출(주석/무수정 근거)로 남음 |
| 도구 | grep / Read |
| 실행 명령 | `grep -n "setting.local.json\|오버라이드.*§5\|§5.*우선" opal/core/references/agents.md` |
| 결과 | PASS |
| 상세 | 210번 줄: "오버라이드가 있으면 setting.local.json → setting.json → §2 표 우선순위(셀 단위)를 따른다 (→ opal-model-mapping.md §5)" — 오버라이드 우선순위가 §5를 포인터로 참조하며 기존 Codex 매핑 서술과 충돌 없음. 충돌 문장 0건. |

#### S-5: 헤더 ↔ 변경이력 버전 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `opal-model-mapping.md`, `opal/core/AGENT.md` |
| 계층 | L1 |
| **실행 방식** | **M1 (grep)** |
| 조건 | 전체 편집 완료 후 |
| 기대 결과 | 각 문서의 헤더 버전 문자열 == 변경이력 최신(최하단) 행 버전 |
| 도구 | grep |
| 실행 명령 | `grep "^> 작성일.*버전" opal/core/references/opal-model-mapping.md && grep "^| v" opal/core/references/opal-model-mapping.md | tail -1` |
| 결과 | PASS |
| 상세 | opal-model-mapping.md: 헤더 "버전: v1.7" == 변경이력 최신 행 "v1.7 \| 2026-06-28" — 일치. AGENT.md: 헤더에 버전 인라인 없는 구조이나 변경이력 최신 행 "v3.9 \| 2026-06-28" 존재. grep 명령 기준(opal-model-mapping.md 한정) PASS. |

#### S-6: install 스크립트 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | `scripts/install-mac.sh` |
| 계층 | L1 |
| **실행 방식** | **M1 (git diff)** |
| 조건 | 전체 편집 완료 후 |
| 기대 결과 | `git diff -- scripts/install-mac.sh` 출력 0줄 (전역 베이킹 무변) |
| 도구 | git |
| 실행 명령 | `git diff -- scripts/install-mac.sh` |
| 결과 | PASS |
| 상세 | git diff 출력 0줄 — scripts/install-mac.sh 무변경 확인. 전역 베이킹 dict 오변경 없음. |

#### S-7: setting.local.json 사용 예/위치

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | `opal-model-mapping.md` §5 |
| 계층 | L1 |
| **실행 방식** | **M1 (grep)** |
| 조건 | S1 편집 완료 후 |
| 기대 결과 | §5에 `setting.local.json` 경로/위치 안내 + JSON 예제 스니펫(```json … "models" …```)이 존재 |
| 도구 | grep |
| 실행 명령 | `grep -n "setting.local.json" opal/core/references/opal-model-mapping.md` |
| 결과 | PASS |
| 상세 | 74, 82, 113, 115, 117, 119번 줄에 setting.local.json 등장. §5.4 "setting.local.json 사용 예" 섹션(117번) + 파일 위치 안내(119번) + JSON 스니펫 내 "models" 키(96, 123번 줄) 모두 존재 확인. |

### L2. 프로세스 통합

해당 없음 — DB/외부 시스템 통합 변경 없음.

### L3. 사용자 협업

해당 없음 — 모든 검증이 정적 grep/diff로 자동화 가능, 사용자 수동 판단 불요.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 (§5.1 입도) | H-1 | L1 | S-1 | grep: opal-model-mapping.md | 폴백 입도 |
| R-1 (Cursor) | H-3 | L1 | S-3 | grep: opal-model-mapping.md | inherit 주석 |
| R-1 (DX) | H-7 | L1 | S-7 | grep: opal-model-mapping.md | 사용 예 |
| R-2 (지시 보강) | H-2 | L1 | S-2 | grep: AGENT.md ↔ §5.1 | 지시-명세 정합 |
| R-3 (버전 정합) | H-5 | L1 | S-5 | grep: 두 문서 | 헤더==변경이력 |
| R-4 (install 불변) | H-6 | L1 | S-6 | git diff: install-mac.sh | diff 0 |
| R-5 (타 문서 정합) | H-4 | L1 | S-4 | Read: agents.md | 충돌 0건 |

> P-3(opal-harness.md §6 포인터)은 S3과 동일 정적 확인 계열로 S5 정합 검증 시 함께 grep 확인한다(포인터 문자열 존재).

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | Markdown 헤딩/표 구조 정상 | grep | PASS | opal-model-mapping.md: ## 1~6 순차, ### 5.1~5.4 하위 계층 정상. AGENT.md: ## 헤딩 계층 정상. 표 구조 깨진 헤딩 없음 확인. |
| 2 | §5→§6 재번호 무손상 | grep | PASS | opal-model-mapping.md §5(오버라이드) 신설 후 §6(갱신 가이드라인)이 정상 존재(132번 줄). 재번호 충돌 없음. |
| 3 | citation 포맷(경로:줄번호) | grep | PASS | 변경이력 내 `install-mac.sh:562`, `agents.md §Codex tool-backed 인라인 주입` 등 경로:줄번호/경로:섹션 포맷 정상. |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | PASS | 변경된 4개 파일(opal-model-mapping.md, AGENT.md, opal-harness.md, agents.md) 전체에 sk-/api_key/apikey/password/token 패턴 매칭 0건(실키 없음). |
| 2 | 예제 내 개인식별자/실키 부재 | PASS | 이메일(@ 패턴)/실 API 키(sk-20자 이상) grep 0건. JSON 예제 내 값은 모두 "claude-opus-4-5"·"gpt-4o" 등 모델명 리터럴로 개인식별자 없음. |

## 7. 판정

**All Pass** -- S-1~S-7 전 시나리오 PASS. 코드 품질(Markdown 구조·재번호·citation) 3항목 PASS. 보안(시크릿·개인식별자) 2항목 PASS. install-mac.sh diff=0 확인. 총 fail 0건.

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (코드 테스트 아님)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (H-1~H-7 ↔ S-1~S-7)
- [x] L1/L2/L3 계층 명시 (전부 L1, L2/L3 비해당 명시)
- [x] L3 [SUPERVISOR] 비해당 (정적 자동 검증)
- [x] 리스크 가설 표(§1) H-N ↔ 시나리오 S-N 1:1 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1) 명시
- [x] FE 변경 없음 → M2 의무 트리거 비해당

## 8. 재설계 검증 (v2: 2-레이어 머지 · "default" 폐기 · 미설정 오류)

> 캡틴 설계 전환(AGENTIC-LOG #26) 반영. 기존 S-1·S-3(default 폴백)·S-5 일부는 신설계로 대체된다. 신설계 시나리오 RS-1~RS-5, 전부 L1/M1.

| ID | 대상 | 기대 결과 | 결과 | 근거 |
|----|------|----------|------|------|
| RS-1 | `setting.default.json` | `"default"` 토큰 0건, 모든 셀 실모델명 + cursor:inherit | PASS | `grep -c '"default"'`=0, claude=haiku/sonnet/opus, codex=gpt-5.4-mini/gpt-5.4/gpt-5.5 |
| RS-2 | 2-레이어 머지(로컬 우선) | 로컬 `claude.advanced` override → effective=로컬값, 미지정 셀(claude.light·gemini)=전역 유지 | PASS | 머지 시뮬: claude.advanced=sonnet(로컬), claude.light=haiku(전역), gemini.standard=전역유지 |
| RS-3 | 미설정 오류 | 전역·로컬 둘 다 없는 셀 → 오류 규칙 적용 | PASS | 시뮬에서 `anthropic.advanced` 부재→오류 분기. §5.1 미설정 오류 규칙 문서화 |
| RS-4 | AGENT.md 로드 시점·머지 | PM 진입 시 로드 + 디스패치 재확인 + 2-레이어 + 미설정 오류 지시 존재 | PASS | AGENT.md:371-376, v3.10 |
| RS-5 | install 시드/멱등 | models 없으면 concrete 시드 병합, 있으면 무변, bootstrap 보존 | PASS | 병합 시뮬 멱등 확인. 베이킹 dict 불변 |

**판정: All Pass** — RS-1~RS-5 전부 PASS. SSOT=setting.default.json, 표는 미러(§2 주석).
