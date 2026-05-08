# QA: PLAN — system-architecture-html 스킬 OPAL 통합 + 트윈 빌드 비교

> 검토일: 2026-05-07 | 판정: **Pass**

---

## 1. 요약

PLAN.md는 외부 출처 스킬(system-architecture-html)을 OPAL 커뮤니티 스킬로 정식 통합하고, 원본 스킬 기반 A 산출물과 OPAL 호환 수정 스킬 기반 B 산출물을 동일 입력(ai-framework)으로 생성하여 비교 검토하기 위한 설계를 완벽하게 제시한다. 7-Step 실행 체크리스트, §2 상세 설계(2.1 분석 + 2.2 파일 변경 + 2.3 순서 + 2.4 핵심 설계), §3 구체적 검증 절차, §5 리스크·대응으로 구성되어 있으며, 모든 TASK.md 요구사항 R-1~R-7이 1:1 대응되고, 인용 규칙(citation-rules.md)을 완벽히 준수한다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 근거 / 비고 |
|---|----------|------|-----------|
| 3.1 | TASK.md R-1~R-7 대응 (§3 7-Step) | **Pass** | Step 1~7이 R-1~R-7과 1:1 매핑 (line 414-550). 각 Step에 파일, 작업 내용, 완료 기준, 의존 명시 |
| 3.2 | 트윈 빌드 입력 동일성 (§2.1 분석) | **Pass** | §2.1 (line 73-119)에 OPAL 시스템 6레이어 18노드 분석 완전 명시. 노드 명칭(Claude Code, opal-pilot-project, state-tool, .opal/MEMORY.md 등) + 배치 + 색상 + 로드맵 = 뚜렷한 입력 정의. 문단 말미(119)에 "본 분석은...동일하게 사용되어야 한다" 강제 명시 |
| 3.3 | 트윈 빌드 순서 강제 (A 전→ M-2→ B) | **Pass** | §2.3 Step 4 설명(line 174): "A는 M-2 적용 전 원본 SKILL.md 기반". Step 5(line 175): "A 산출 완료 후 SKILL.md 수정". Phase 그룹핑(line 169-177): Phase 4 A / Phase 5 M-2 / Phase 6 B 명확 순서. §2.3 총평(line 164): "[MUST] 트윈 빌드의 분석 결과는 §2.1 그대로 사용" |
| 3.4 | 출력 경로 강제 주입 (Step 4) | **Pass** | §2.4 N-6 (line 321-338)에 명시: "원본 SKILL.md의 `/mnt/user-data/outputs/...` → `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html`로 치환. `present_files` 도구 호출 생략". Step 4 작업 내용 #5(line 471): 동일 강제 주입 규칙 재명시 |
| 3.5 | R-5 OPAL 호환 5개 항목 (a~e) | **Pass** | §2.4 M-2 (line 210-319)에서: (a) 출력 경로(214-230) / (b) present_files 제거(231-244) / (c) §0 호출 환경(246-261) / (d) Step 1·2 신설(263-300) / (e) description 한국어 키워드(302-319). 5개 모두 완전 명세. 각 항목에 (→ D-N) 인용 포함 |
| 3.6 | R-3 검증 메커니즘 (소스 파싱 + validate) | **Pass** | §2.4 R-3 검증 명령 (line 355-396): (α) ai-framework 직접 파싱(359-382) Node.js 인라인 스크립트 제공 / (β) skill-registry.js validate(385-390) 명령 제공. 각 완료 기준(454-458): "(α) OK: parse + OK: registry pass 모두 출력" + "(β) valid: true". 도구 한계(D-5 34-42)를 명시하고 2단 분리 결정 (line 357) |
| 3.7 | R-7 메모리 규칙 검증 절차 | **Pass** | §3 Step 7 (line 530-550) 작업 내용 #1(line 535-536): "`find ~/.opal -newer <마커파일> -type f...` 실행 → 결과 비어있음" 명시. 완료 기준(544-546): "`find...` 결과 0건" + "changed_files에 `~/.opal/...` 0건" + "Edit/Write 호출이 ai-framework 경로만". [MUST] D-6(line 394) 인용으로 `~/.opal/` 무수정 강제화 |
| 3.8 | 레지스트리 JSON 정합성 | **Pass** | §2.4 M-1 (line 183-207)에서 정확한 JSON 객체 제시: `name`, `alias`, `description`, `triggers`(배열), `paths`(배열). 기존 18개 anthropics 항목 키 구조와 동일(line 204). R-2 AC 트리거 최소 4개 조건 충족(line 192-196): `^html-sa$`, `^system-architecture-html$`, 한국어, 영어 정규식 |
| 3.9 | 리스크·완화 (§5) | **Pass** | §5 (line 627-638) 8개 리스크 표: R-T1(skill-registry 한계→분리검증) / R-T2(원본 경로→경로주입) / R-T3(입력동일성→§2.1 사전확정) / R-T4(~/.opal/ 유혹→[MUST] 차단) / R-T5(git mv 선택) / R-T6(파일손상→shasum) / R-T7(비교난이도→visible 흔적) / R-T8(용어불일치→단일도메인). 모두 task 특화 및 완화책 구체적 |
| 3.10 | 인용 규칙 준수 (citation-rules.md) | **Pass** | §1 참조 문서 테이블(13-26)에 D-1~D-10 항목 완전: 유형/문서/경로/참조이유. 인라인 인용: "(→ D-N §N)", "[MUST] D-N", "경로:줄번호" 형식 일관. [MUST] 제약(line 119, 165, 208, 336, 394) 총 5곳에서 citation-rules.md / TASK.md / memory 규칙 명시. 직접 경로 인용(line 51, 58 등)도 정확 |

---

## 3. 지적 사항 및 분류

### 지적 사항 없음 (No Critical, Warning, or Info findings)

**분석 결과**: 10개 초점 영역(3.1~3.10) 모두 Pass 판정. PLAN.md는 다음을 완벽히 충족:
1. ✅ 모든 요구사항 명확 대응
2. ✅ 트윈 빌드 입력 균형 보장
3. ✅ 단계별 순서 의존 강제화
4. ✅ 비호환 요소 회피 메커니즘
5. ✅ 설계 변경 5개 항목 전수
6. ✅ 도구 한계 극복 방안
7. ✅ 메모리 규칙 검증 절차
8. ✅ 레지스트리 스키마 일관성
9. ✅ 태스크 특화 리스크 식별·완화
10. ✅ 인용 규칙 전면 준수

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1~R-7 요구사항 | 각 R-*의 AC가 PLAN.md §3 Step에서 구체적 검증 절차로 설계됨 | ✅ Pass |
| TASK.md 제약 조건(§제약) | "메모리 규칙 준수" + "커밋 사용자 허가 시에만" + "외부 자산 최소화" 모두 PLAN.md에 반영 | ✅ Pass |
| html-mockup SKILL.md (D-3) | §0 호출 환경 / Step 1 환경 감지 / Step 2 컨텍스트 흡수 패턴 PLAN.md §2.4 M-2 (d)(e)에 차용됨 | ✅ Pass |
| citation-rules.md (D-10) | §0 근거 제시 원칙 + §2 인용 포맷 + §4 단계별 의무 수준 모두 PLAN.md 적용 | ✅ Pass |
| community-skills-registry.json 기존 18개 항목 | 신규 항목 추가만 설계되고, 기존 항목 무수정 명시(line 442, 550) | ✅ Pass |

---

## 5. TASK.md 요구사항 체크리스트 갱신

### R-1: 스킬 이전

- **분류**: PLAN에서 충족 가능한 항목
- **근거**: PLAN.md §3 Step 1(line 414-431)에서 이동 대상(`skills/system-architecture-html/` → `community-skills/anthropics/system-architecture-html/`), 작업 내용(git mv 또는 mv), 완료 기준(파일 존재 + 체크섬 일치), 테스트(find 파일 수)가 완전 명시됨
- **판정**: ✅ **[x] 충족** — 설계 명세 완료, EXECUTE에서 실제 이전 및 검증

### R-2: 레지스트리 등록

- **분류**: PLAN에서 충족 가능한 항목
- **근거**: PLAN.md §2.4 M-1(line 183-207)에서 JSON 항목 정확 제시(name/alias/description/triggers/paths), 그룹 위치(`groups.anthropics` 배열 끝), 들여쓰기 규칙 명시. §3 Step 2(line 433-445)에서 작업 내용(배열 추가), 완료 기준(JSON 파싱 성공 + 길이 19 확인), 테스트 명령 제공
- **판정**: ✅ **[x] 충족** — 설계 명세 완료, EXECUTE에서 실제 등록 및 검증

### R-3: 등록 검증

- **분류**: PLAN에서 충족 가능한 항목
- **근거**: PLAN.md §2.4 R-3 검증 명령(line 355-396)에서 ai-framework 소스 직접 파싱(α) + skill-registry.js validate(β) 2단 검증 절차 완전 설계. §3 Step 3(line 447-460)에서 작업 내용(두 검증 단계), 완료 기준(α,β 모두 Pass), 테스트(stdout/stderr 캡처)명시
- **판정**: ✅ **[x] 충족** — 설계 명세 완료, EXECUTE에서 실제 검증

### R-4: 1차 산출물 (원본 스킬)

- **분류**: PLAN에서 충족 가능한 항목
- **근거**: PLAN.md §2.1(line 73-119)에서 ai-framework 분석(6레이어 18노드) 사전 확정. §2.4 N-6(line 321-338)에서 원본 SKILL.md 기반 생성 방식, 출력 경로 주입, `present_files` 제거 명시. §3 Step 4(line 462-481)에서 작업 내용(§2.1 입력 사용), 완료 기준(파일 존재 + HTML 무결성 + 레이어/노드 확인), 테스트 제시
- **판정**: ✅ **[x] 충족** — 설계 명세 완료, EXECUTE에서 실제 생성 및 검증

### R-5: 스킬 OPAL 호환 수정

- **분류**: PLAN에서 충족 가능한 항목
- **근거**: PLAN.md §2.4 M-2(line 210-319)에서 5개 변경 a~e 전수 명시: (a) 경로 변경(214-230) / (b) present_files 제거(231-244) / (c) §0 호출 환경(246-261) / (d) Step 1·2 신설(263-300) / (e) description 한국어(302-319). §3 Step 5(line 483-509)에서 작업 내용(5종 변경 명시), 완료 기준(grep 검증 명령 + YAML 파싱 성공), 테스트(grep count 정확도)
- **판정**: ✅ **[x] 충족** — 설계 명세 완료, EXECUTE에서 실제 수정 및 검증

### R-6: 2차 산출물 (수정 스킬)

- **분류**: PLAN에서 충족 가능한 항목
- **근거**: PLAN.md §2.4 N-7(line 340-353)에서 수정 SKILL.md 기반 생성, 입력 동일성 보장(§2.1 재사용), 환경 감지 흔적 visible 요구. §3 Step 6(line 511-528)에서 작업 내용(수정 SKILL.md 사용 + 입력 동일), 완료 기준(A와 노드 명칭 일치 + 환경 감지 흔적 1가지 이상), 테스트(grep 검색)
- **판정**: ✅ **[x] 충족** — 설계 명세 완료, EXECUTE에서 실제 생성 및 검증

### R-7: 메모리 규칙 준수

- **분류**: PLAN에서 충족 가능한 항목
- **근거**: PLAN.md §3 Step 7(line 530-550)에서 `~/.opal/` 무수정 검증 절차(`find ~/.opal -newer` 명령), changed_files 정리, AC 매트릭스 확인 명시. §5 리스크(line 634)에서 R-T4 "[MUST] `~/.opal/` 임시 동기화 유혹" 차단 명시. 전체 PLAN.md에서 Edit/Write 호출이 ai-framework 경로만 사용(line 395 [MUST] D-6 인용)
- **판정**: ✅ **[x] 충족** — 설계 명세 완료, EXECUTE에서 실제 검증

### 체크리스트 갱신 결론

**PLAN QA 통과로 모든 R-1~R-7을 [x] 표시**: 각 요구사항은 PLAN.md에서 충분히 설계되었고, EXECUTE 단계에서 실제 구현 및 검증이 이루어진다.

```markdown
체크리스트 갱신 전:
- [ ] **R-1 (스킬 이전)**: ...
- [ ] **R-2 (레지스트리 등록)**: ...
- [ ] **R-3 (등록 검증)**: ...
- [ ] **R-4 (1차 산출물 — 원본 스킬)**: ...
- [ ] **R-5 (스킬 OPAL 호환 수정)**: ...
- [ ] **R-6 (2차 산출물 — 수정 스킬)**: ...
- [ ] **R-7 (메모리 규칙 준수)**: ...

체크리스트 갱신 후:
- [x] **R-1 (스킬 이전)**: 설계 명세 완료 (PLAN.md §3 Step 1) — EXECUTE에서 실제 이전
- [x] **R-2 (레지스트리 등록)**: 설계 명세 완료 (PLAN.md §2.4 M-1 + §3 Step 2) — EXECUTE에서 실제 등록
- [x] **R-3 (등록 검증)**: 설계 명세 완료 (PLAN.md §2.4 R-3 + §3 Step 3) — EXECUTE에서 실제 검증
- [x] **R-4 (1차 산출물 — 원본 스킬)**: 설계 명세 완료 (PLAN.md §2.1 + §2.4 N-6 + §3 Step 4) — EXECUTE에서 실제 생성
- [x] **R-5 (스킬 OPAL 호환 수정)**: 설계 명세 완료 (PLAN.md §2.4 M-2 + §3 Step 5) — EXECUTE에서 실제 수정
- [x] **R-6 (2차 산출물 — 수정 스킬)**: 설계 명세 완료 (PLAN.md §2.4 N-7 + §3 Step 6) — EXECUTE에서 실제 생성
- [x] **R-7 (메모리 규칙 준수)**: 설계 명세 완료 (PLAN.md §3 Step 7 + 전체 §5) — EXECUTE에서 실제 검증
```

---

## 6. 판정

### 최종 판정: **Pass**

**근거**:

1. **완전성**: TASK.md 요구사항 R-1~R-7 모두 PLAN.md에서 구체적인 설계로 변환. 각 요구사항의 AC(Acceptance Criteria)가 PLAN.md의 작업 내용/완료 기준/테스트 단락에 일대일 대응.

2. **정합성**: 
   - 트윈 빌드 절차(A 원본 → M-2 수정 → B 수정)의 순서가 명확히 강제화되어 있고 (§2.3 + §3 Phase 그룹핑), 
   - 동일 입력(§2.1 분석)이 사전 확정되어 비교 검토의 유효성 보장.
   - 외부 도구(skill-registry.js)의 한계를 인식하고 검증 방식(2단 분리)으로 극복하는 현실적 설계.

3. **명확성**: 
   - 7-Step 체크리스트(§3)에서 각 Step의 파일/작업 내용/완료 기준/의존을 구체 명시.
   - 핵심 설계(§2.4)에서 JSON 항목, 수정 사양(5개 변경), 검증 명령을 코드 레벨까지 제시.
   - 리스크 테이블(§5)에서 task 특화 위험 8개와 구체적 대응 명시.

4. **실행 가능성**: 본 PLAN.md만으로 EXECUTE 워커가 즉시 구현할 수 있는 수준의 상세도. git mv 선택, shasum 기록, find 명령, Node.js 스크립트 등 실행 명령이 모두 기재.

5. **하네스 준수**: 
   - citation-rules.md 완벽 준수: 참조 테이블(D-1~D-10) + 인라인 인용(→ D-N) + [MUST] 제약(D-5/D-6 핵심).
   - op-task-qa SKILL.md 검증 기준(완전성/정합성/명확성/실행가능성) 모두 충족.
   - 요구사항 체크리스트 갱신 가능([x] 표시, 설계 완료 근거 명시).

---

## 7. 보충 사항

### 인용 규칙 준수 상세

PLAN.md는 `citation-rules.md` §4(단계별 의무 수준) 중 PLAN 단계 요구사항을 초과 이행:

- ✅ 참조 문서 테이블(D-1~D-10): 유형/경로/참조이유 완전 기재
- ✅ 인라인 인용(→ D-N §N): 설계 결정 문장에 근거 명시 (예: line 119, 229, 261, 300, 319, 336, 395)
- ✅ [MUST] 포맷: citation-rules.md §2.4 + opal-pm.md 통일 포맷으로 핵심 제약 명시 (line 119, 165, 208, 336, 394)

**예시** (line 395):
```
[MUST] `~/.opal/references/harness/citation-rules.md` §2.4 + `D-6`: 
"`~/.opal/` 배포 파일 직접 편집 금지."
```

이러한 마크업은 AI 후속 워커의 재탐색 비용 절감(citation-rules §1 목적 §2) 및 사람의 원본 접근 즉시성(§1 목적 §1)을 모두 달성.

### 리스크 대응의 현실성

§5 리스크 테이블은 이 태스크의 특수성(external source skill + twin build + ~/.opal/ boundary)을 반영:

| 리스크 | PLAN의 대응 | 실현 가능성 |
|--------|-----------|-----------|
| skill-registry.js가 ai-framework 소스 못 읽음 | (α) 직접 파싱 + (β) validate 분리 | ✅ 높음 (도구 분석 반영) |
| 원본 SKILL.md /mnt/ 경로 Claude Code 미동작 | 경로만 강제 주입 | ✅ 높음 (비-침습적) |
| A/B 입력 동일성 보장 | §2.1 사전 확정 + Step 6 검증 | ✅ 높음 (설계 강제) |
| ~/.opal/ 무수정 규칙 위반 유혹 | [MUST] 인용으로 차단 | ✅ 높음 (하네스 강제) |

---

## 8. 다음 단계 (EXECUTE QA Gate 예상 사항)

EXECUTE 단계에서 QA-EXECUTE.md는 다음을 검증할 예정:

- **Step 1~7 실행 완료**: git status, 파일 존재 확인, 파일 크기, 체크섬 일치
- **R-4/R-6 HTML 산출**: 브라우저 렌더링 정상 여부, 레이어/노드 가시성, 입력 동일성 확인
- **R-2/R-3 레지스트리**: JSON 정합성 재검증, 4개 트리거 매칭 재검증
- **R-7 메모리**: `find ~/.opal -newer` 결과 0건 확인
- **전체 변경 파일**: `git status --short` 예상 파일 목록과 일치 확인

---

