# TEST SCENARIO: 브레인 답변 생성 내부 워크플로우 — content-driven 레이아웃 선택

> 작성일: 2026-07-14 | 상태: 실행 완료 (S-1~S-6 PASS / S-7 PENDING[SUPERVISOR])
> 작성자: opal-plan-agent (시나리오) / 실행·기록: PM 직접 (TEST 워커가 S-6 백그라운드 후 결과 미기록 종료 → PM 수습, S-1~S-5는 EXECUTE 강화검토에서 직접 확인)
> 입력: TASK.md + PLAN.md §리스크 가설 표

## 0. RED-first 트랙 적용 판단

**RED-first 미적용 (타당).** 본 태스크는 **문서(스킬) 1개 절 재작성**이며 결정론적 코드 로직 변경이 아니다. 답변 레이아웃 준수는 brain-tool이 강제하지 못하는 **advisory LLM 행동**이므로, 실패하는 단위 테스트를 먼저 쓰는 RED-first 트랙은 적용 대상이 아니다. 대신:

- **L1 (주 계층, M1)**: SKILL.md 산출물 **구조 검증** — 6단계·6축·5후보·판정·가드3종·2예시·공통적용·v1.8 이력이 문서에 존재하는지 결정론적 grep/Read로 확인.
- **L2 (보조, M2)**: 이 레포 `.opal/brain/`(146p, **프레임워크 도메인**) 대상 read-only **스모크** — JSON 출력 계약(펜스 하나·펜스 밖 raw 마크다운 0)·citations 유실 0·claude 호출 1회를 관측. **[제한 명시] 실제 커머스/여정형 도메인 brain이 이 레포에 없어, "캠페인→Flow" 같은 여정형 레이아웃 도출의 품질 검증은 불가하다.** L2는 계약 비파손 관측에 한정하며 레이아웃 품질의 정량 판정이 아니다.
- **L3 (선택, M3)**: 캡틴 육안 확인 — 실 도메인 질의에서 레이아웃이 content-driven하게 도출되는지 정성 관찰(선택적).

## 1. 리스크 가설 표

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 §답변 구조 재작성 | read-only JSON 이스케이프(펜스 밖 raw 마크다운 금지)·citations 유실 방지 | P0 | L1 + L2 | S-1, S-6 |
| H-2 | F-001 6단계 서술 | claude 호출 1회(G2) — 단계≠호출 | P1 | L1 + L2 | S-2, S-6 |
| H-3 | F-001 (v1.7 대체) | v1.7 자산 회귀(리드 문단·인라인 코드 병기·과한 헤딩 금지) | P2 | L1 | S-3 |
| H-4 | F-002 변경이력/버전 | 버전 추적성 정합(frontmatter vs changelog) | P2 | L1 | S-4 |
| H-5 | F-003 adapter | SSOT 전파(답변 구조 미하드코딩) | P1 | L1 | S-5 |
| H-6 | F-001 공통 절 | ask·read-only 공통 적용 + 헤딩 앵커 무결성 | P1 | L1 | S-1 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

| 대상 | 식별자 | 상태 | 출처 |
|------|--------|------|------|
| 변경 대상 문서 | `opal/skills/opal-brain/SKILL.md` | Step 1·2 반영 완료 | 프로젝트 소스 |
| 배포본 | `~/.opal/skills/opal-brain/SKILL.md` | `install-mac.sh` 재배포 후 (v0.6.8-16-g8dbab98) | 배포 산출 |
| 무변경 확인 대상 | `dashboard/backend/adapters/opbr_adapter.py` | 원본 그대로 (git diff 빈 결과) | 프로젝트 소스 |
| 스모크용 brain | `.opal/brain/` (index.md + pages 146개, 프레임워크 도메인) | 기존 존재 | 레포 |
| 스모크 질의 | Q1="opal-brain은 어떻게 동작하나?" | 실행됨(Q2는 콜드 비용상 생략) | 수동 |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (호출/조작) | Then (re-read/관측) |
|---------|------------|----------------|---------------------|
| S-1 | 재작성된 SKILL.md §답변 구조 | 절 텍스트 Read(6단계·공통 문구·헤딩 앵커) | 6단계·"대화형·read-only 공통"·앵커 텍스트 존재 |
| S-2 | 재작성된 §답변 구조 | 6축·5후보·판정·가드 Read | 축6·후보5·판정(매핑+tie-break)·G1~G3 존재 |
| S-3 | 재작성된 §답변 구조 | v1.7 자산·예시 Read | 리드 문단·인라인 코드 병기·과한 헤딩 금지·2예시 보존 |
| S-4 | SKILL.md §변경이력·frontmatter | v1.8 행·version grep | v1.8(KST+062) 행 + `version:"1.8"` |
| S-5 | `opbr_adapter.py` | 답변 구조 하드코딩 grep + git diff | 하드코딩 부재 + diff 무변경 |
| S-6 | 재배포된 배포본 + `.opal/brain/` | `//opbr query --read-only "<Q>"` 1회 실행 | JSON 펜스 하나·펜스 밖 raw 0·citations 유실 없음·호출 1회 |

## 3. 검증 시나리오

### L1. 문서 구조 검증 (자동, 산출물 검사)

#### S-1: §답변 구조 — 6단계·공통 적용·앵커 무결성

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-6 |
| 대상 | `opal/skills/opal-brain/SKILL.md` §답변 구조 절 (R1·R4) |
| 계층 | L1 · 실행 방식 M1 |
| 기대 결과 | 6단계 순서·역할·출력여부 서술 / "대화형·read-only 공통" 문구 + 출력계약 관계 / 헤딩 앵커 보존 |
| 실행 명령 | `Read SKILL.md:322-377`, `grep -n "답변 구조 — 적응형 마크다운 계층" SKILL.md` |
| **결과** | **PASS** |
| 상세 | 6단계 표 L330~337(출력여부 열 포함: 1~4 비출력/5~6 출력). 공통 문구 L324·L326(read-only는 JSON answer 이스케이프 관계 명시). 헤딩 앵커 `### 답변 구조 — 적응형 마크다운 계층 (대화형·read-only 공통)` L322 보존 → §비대화형 read-only(L467) 역참조 유효, §출력 형식 차이(L377) 보존 |

#### S-2: §답변 구조 — 6축·5후보·판정 규칙·가드 3종

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | §답변 구조 절 (R2·R3) |
| 계층 | L1 · 실행 방식 M1 |
| 기대 결과 | 관측 축 6종(신호·후보) / 후보 5종 정의 / 판정 규칙(매핑1차+동점tie-break단순+가중합미채택) / 가드 G1~G3 |
| 실행 명령 | `Read SKILL.md:339-364` |
| **결과** | **PASS** |
| 상세 | 관측 축 6종 표 L341~348(여정·순서성·값보유·병렬성·주제수·분량 + 신호 + 매핑후보). 후보 5종 L352~356(Flat/그룹핑/Flow/표/복합, 정의+언제). 판정 규칙 L358(축→후보 매핑 1차 + 동점 시 단순한 쪽 + 가중합 미채택 + 축 충돌 시 지배 축 우선). 가드 G1(비출력)·G2(호출1회)·G3(JSON 이스케이프) L362~364 |

#### S-3: §답변 구조 — 두 예시 + v1.7 자산 보존

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | §답변 구조 절 (R5 + 회귀) |
| 계층 | L1 · 실행 방식 M1 |
| 기대 결과 | 예1 캠페인→Flow(여정 지배) / 예2 미션유형+정책→복합(주제 수) / v1.7 자산 보존 |
| 실행 명령 | `Read SKILL.md:366-375` |
| **결과** | **PASS** |
| 상세 | 예1 L368("방문형 캠페인 정책 설명→Flow", 표면상 표 오판 지적 + 참여 여정/라이프사이클 축 지배). 예2 L369("미션 유형+정책→복합", 독립 주제 2개 + 섹션 내부 재판정). v1.7 자산 L371~375(리드 문단 1~2문장 필수·코드 식별자 인라인 코드 병기(확정기준#2)·짧은 답 과한 헤딩 금지→분량Flat 흡수) |

#### S-4: §변경이력 v1.8 + frontmatter version 정합

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | SKILL.md §변경이력·frontmatter (R6) |
| 계층 | L1 · 실행 방식 M1 |
| 기대 결과 | v1.8 행(KST+062) + frontmatter `version:"1.8"` |
| 실행 명령 | `grep -n "v1.8" SKILL.md`, `sed -n '12p' SKILL.md` |
| **결과** | **PASS** |
| 상세 | §변경이력 v1.8 행 L569(`2026-07-14 16:59 KST … (062)`, content-driven 6단계·6축·5후보·판정·가드3종·2예시 요약). frontmatter `version: "1.8"` L12 — changelog 최신 행과 정합(기존 "1.5" 부채 해소) |

#### S-5: `opbr_adapter.py` 무변경 확인

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | `dashboard/backend/adapters/opbr_adapter.py` (R7) |
| 계층 | L1 · 실행 방식 M1(grep + git diff) |
| 기대 결과 | 답변 구조 하드코딩 부재 + `prime_and_ask` 프롬프트만 전달 + git diff 무변경 |
| 실행 명령 | grep(answer/layout/heading/…) + `git diff -- dashboard/backend/adapters/opbr_adapter.py` |
| **결과** | **PASS** |
| 상세 | 답변 구조/레이아웃 하드코딩 부재(매치는 `extract_json_fence` JSON 필드 파싱·docstring 설명뿐). `prime_and_ask()`가 `//opbr query --read-only "{question}"`만 전달(`:133`). git diff 빈 결과(무변경). 전체 diff-stat: SKILL.md만 51+/6- 변경, adapter 0. → SSOT 전파(SKILL.md 반영만으로 read-only 경로 전파) 성립 |

### L2. read-only 스모크 (반자동, 실 CLI 실행 → 계약 관측)

#### S-6: read-only JSON 계약·citations·호출 1회 스모크

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | 재배포된 SKILL.md 반영이 read-only 경로에서 계약을 깨지 않는지 (R1·R3 런타임 관측) |
| 계층 | L2 · 실행 방식 M2 |
| 조건 | Step 4 재배포 완료. `.opal/brain/`(146p) 존재 |
| 기대 결과 | JSON 펜스 하나 / 펜스 밖 raw 마크다운 0 / answer 파싱+citations 유실 0 / claude subprocess 1회 |
| 실행 명령 | `cd <repo> && claude --allowedTools Bash,Read,Grep,Glob --model sonnet --effort medium -p '[ASSISTANT]\n//opbr query --read-only "opal-brain은 어떻게 동작하나?"' --output-format json` |
| **결과** | **PASS** |
| 상세 | (1) ```json 펜스 **정확히 1개**. (2) 펜스 밖 raw 마크다운 헤딩0/표0/불릿0 — 펜스 밖 텍스트는 부트스트랩 preamble 1줄(93자)뿐이며 `extract_json_fence`가 펜스만 발췌하므로 무해. (3) `answer` 파싱 OK(899자), `citations` 3개(skill-opal-brain·opal-brain-system·opal-brain-not-pilot-decision, 전부 concept, 유실 0). (4) `is_error:false subtype:success num_turns:15` — num_turns는 claude 내부 tool_use(brain-tool search/Read) 횟수이며 claude subprocess 호출은 1회(G2 준수). (5) **G1 누출검사**: answer 내 내부 단계용어(질의 분해/구조 분석/레이아웃 설계/워크플로우 등) 매치 **0** → 1~4단계 비출력 준수. answer는 리드 문단 → `## 4모드 라우팅` 번호 리스트로 content-driven 구조화됨 |
| **제한** | 프레임워크 도메인 brain만 존재 → 여정형(캠페인=Flow) 레이아웃 도출 **품질**은 검증 대상 외. 본 시나리오는 JSON 계약 비파손 관측에 한정 |

### L3. 정성 육안 확인 (선택, 수동)

#### S-7: content-driven 레이아웃 도출 정성 관찰 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 (품질 관점) |
| 대상 | 실 질의에서 레이아웃이 질의 표면이 아니라 주입 내용 구조를 따르는지 |
| 계층 | L3 · 실행 방식 M3(사용자 협업, 선택) |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 (선택) |
| **결과** | **PENDING([SUPERVISOR])** — 도메인 brain 미보유로 정량화 불가, 선택 시나리오 |
| 상세 | 미실행. 캡틴이 실 커머스 도메인 프로젝트에서 성격이 다른 질의로 근사 관찰 가능 |

> **[SUPERVISOR] PM 요청 양식**: "opal-brain 재배포 후, 성격이 다른 질의 3~4건(나열형/값비교형/여정형/다주제)을 `//opbr ask`로 실행하고, 답변 레이아웃이 질의 표면이 아니라 주입된 페이지 내용 구조를 따르는지, 그리고 1~4단계 사고가 답변에 노출되지 않는지 확인 부탁드립니다. 도메인 brain 부재로 여정형은 근사 관찰만 가능합니다."

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 결과 | 비고 |
|-------|---------|---------|---------|------|------|
| R1 (6단계 재작성) | H-1, H-2 | L1 | S-1 | PASS | 문서 산출물 검사 |
| R2 (6축·5후보·판정) | H-1, H-2 | L1 | S-2 | PASS | 문서 산출물 검사 |
| R3 (가드 3종) | H-1, H-2 | L1 | S-2 | PASS | 문서 산출물 검사 |
| R4 (공통 적용) | H-6 | L1 | S-1 | PASS | 앵커 무결성 포함 |
| R5 (두 예시) | H-3 | L1 | S-3 | PASS | 캠페인/미션유형 + v1.7 보존 |
| R6 (v1.8 이력) | H-4 | L1 | S-4 | PASS | version 정합 포함 |
| R7 (adapter 무변경) | H-5 | L1 | S-5 | PASS | 무변경 |
| R1·R3 (런타임 계약) | H-1, H-2 | L2 | S-6 | PASS | 계약 비파손 관측 |
| (정성) | H-1, H-2 | L3 | S-7 | PENDING | 선택·[SUPERVISOR] |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 문서 언어 규칙(본문 한국어·필드 English) | 육안/Read | PASS | 본문 한국어, frontmatter 키·version English (`docs/CONVENTIONS.md §언어 규칙`) |
| 2 | 변경이력·version 정합 | grep | PASS | v1.8 행 + frontmatter `version:"1.8"` 정합 (S-4) |
| 3 | 배포 경계(소스 편집 후 install) | 절차 확인 | PASS | 프로젝트 소스 `opal/skills/opal-brain/SKILL.md` 편집 → `install-mac.sh` 재배포(v0.6.8-16-g8dbab98). `~/.opal/` 직접 편집 없음 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | PASS | 문서 변경만 — 신규 시크릿/토큰 없음 |
| 2 | read-only 가드 불변 | PASS | `opbr_adapter.py:138` `--allowedTools Bash,Read,Grep,Glob`(Write·Edit 미허용) 계약 무변경(git diff 빈 결과) |

## 7. 판정

**All Pass** — L1(S-1~S-5)·L2(S-6) 전부 PASS. S-7은 선택 [SUPERVISOR] PENDING(도메인 brain 미보유로 정량화 불가, 완료 차단 요소 아님).

근거: 6단계·6축·5후보·판정규칙·가드3종·2예시·공통적용·앵커무결성·v1.8/version·adapter무변경이 문서에 모두 존재(L1), read-only 스모크에서 JSON 펜스 하나·펜스 밖 raw 마크다운 0·citations 3개 유실 0·claude 호출 1회·G1 내부단계 누출 0으로 계약 비파손 확인(L2).

### PM Gate 체크

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (해당 없음 — 문서 검증·실 CLI 스모크만)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오)
- [x] L3 [SUPERVISOR] 마커 존재 + PM 요청 양식 첨부
- [x] 리스크 가설 표(§1) H-N ↔ 시나리오 S-N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 없음 → M2(E2E FE) 의무 트리거 비해당. read-only CLI 스모크(S-6)는 M2로 별도 포함
- [x] RED-first 미적용 근거 명시(§0) — advisory LLM 행동 + 문서 재작성
