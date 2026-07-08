# DONE: opwt 산출물 체계 v4 — interview 통합 + PRD 8섹션 + 시나리오·화면 흐름도 + WBS 제거

> 완료일: 2026-05-24 15:35 | 적용 스킬: opp | 모드: agentic
> 태스크 폴더: `tasks/008-260524-opp-opwt-v4-output-system/`

---

## 1. 태스크 요약

`app-planning-presentation` 교육 자료(`/Volumes/Data/AiStudio/workspace/ai-plan-dev/app-planning-presentation/`)의 내용·산출물·구성을 적극 흡수하여 opwt(opal-pilot-write-tech) 스킬을 **v3.4 → v4.0**으로 개편했다.

| 변경 영역 | Before (v3.4) | After (v4.0) |
|---------|------------|------------|
| 산출물 종수 | 9종 (필수 4 + 선택 4 + 외부 API + WBS) | **10종** (필수 4 + 선택 5 + 외부 API, PMO 제거) |
| PRD 섹션 | 6섹션 | **8섹션** (서비스 기획서 + 요구사항 명세서 통합 흡수) |
| 시나리오 산출물 | "순서도" (정의 모호) | **"기능 시나리오 다이어그램"** (flowchart + sequence + state 3종) |
| 화면 흐름도 | 없음 | **신규 선택 산출물** (화면 단위 Mermaid flowchart) |
| Mermaid 표준 | IA만 필수 | **§11 신규 절** — 필수 3 + 권장 4 |
| TASK 단계 | 4개 확인 항목 수동 | **interview 스킬 호출 + Round 1/2/3** |
| 정합성 검증 | 8쌍 (§1) + 7쌍 (§8) | **+5쌍 추가** (시나리오 3 + 화면 흐름도 2) |

## 2. 산출물 목록

### 2.1 본 태스크 산출물

| 파일 | 역할 |
|------|------|
| `tasks/008-260524-opp-opwt-v4-output-system/TASK.md` | 요구사항 R-1~R-8 정의 + 관련 문서 D-1~D-8 |
| `tasks/008-260524-opp-opwt-v4-output-system/PLAN.md` | 4 Step / 8 의사결정 / 7 리스크 (v1.0 + v1.1 보강) |
| `tasks/008-260524-opp-opwt-v4-output-system/QA-PLAN.md` | PLAN 검증 — Pass (Normal 4 / Minor 3 모두 PM 보정) |
| `tasks/008-260524-opp-opwt-v4-output-system/QA-EXECUTE.md` | EXECUTE 검증 — Pass (Minor 1건 즉시 보정) |
| `tasks/008-260524-opp-opwt-v4-output-system/AGENTIC-LOG.md` | PM 대행 일지 — 4 게이트 / 10 오류·수정 / 3 PM 결정 |
| `tasks/008-260524-opp-opwt-v4-output-system/STATE.md` | 파이프라인 현황판 (state-tool 관리) |
| `tasks/008-260524-opp-opwt-v4-output-system/DONE.md` | 본 완료 보고서 |

### 2.2 변경된 프레임워크 산출물 (배포 대상)

| 파일 | 핵심 변경 |
|------|---------|
| `opal/skills/opal-pilot-write-tech/SKILL.md` | 커버 범위 갱신(PMO 제거, 선택 5종) + TASK 절 재구성(interview 통합·Round 1/2/3·도메인 옵션 구성·TASK.md 신규 섹션 양식) + 변경이력 v4.0 추가 |
| `opal/skills/opal-pilot-write-tech/references/network-guide.md` | §1(산출물 유형 v4) + §2(연결 맵 신규 5쌍) + §5(diagnosis enum) + §6(분석 워커 프롬프트 일관성) + §7-3(PRD 8섹션 + 시나리오 가이드 + 화면 흐름도 가이드) + §10(외부 참조 텍스트 보정) + §11 신규 절(Mermaid 시각화 표준) |
| `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | §1(신규 4쌍: 시나리오 3 + 화면 흐름도 1) + §7(Tier 3·5 갱신·WBS 제거) + §8(화면 흐름도 ↔ 와이어프레임) |

## 3. 결과 검증

### 3.1 R-1 ~ R-8 AC 충족 결과

| 요구사항 | AC 충족 | 검증 위치 |
|---------|--------|---------|
| R-1 PRD 8섹션 표준 | ✅ 5/5 | network-guide.md §7-3 PRD 가이드 |
| R-2 기능 시나리오 다이어그램 (순서도 재정의) | ✅ 3/3 | network-guide.md §1 + §7-3 |
| R-3 화면 흐름도 신설 | ✅ 4/4 | network-guide.md §1·§2·§7-3 |
| R-4 Mermaid 시각화 표준 | ✅ 4/4 | network-guide.md §11 |
| R-5 WBS 제거 (PMO 그룹 폐기) | ✅ 7/7 (산출물 정의 영역 0건, 변경이력 영역은 역사적 기록으로 유지) | SKILL.md / network-guide.md / consistency-rules.md |
| R-6 interview 스킬 통합 | ✅ 6/6 (M-7 Round 3 PRD 작성 모드 조건 포함) | SKILL.md TASK 절 |
| R-7 정합성 검증 규칙 확장 | ✅ 3/3 | consistency-rules.md §1·§7·§8 |
| R-8 변경이력 + 메모리 갱신 | ✅ 3/3 | SKILL.md v4.0 행 / MEMORY.md 008 행 |

**총 AC 결과**: 35/35 충족 (R-8 MEMORY 행 완료일시 갱신은 본 CLOSE 단계 처리).

### 3.2 QA 결과

| QA | Verdict | Critical | Normal | Minor |
|----|---------|----------|--------|-------|
| QA-PLAN | Pass (조건부) | 0 | 4 → PM 즉시 반영 | 3 → PM 즉시 반영 |
| QA-EXECUTE | Pass | 0 | 0 | 1 → PM 즉시 반영 |

### 3.3 PM 의사결정 (AGENTIC-LOG)

| # | 결정 | 근거 |
|---|------|------|
| D-1 | 본 자료 흡수 범위 확정 (A+C+E+F+WBS제거+interview, B/D 미채택) | 캡틴 검토 6라운드 합의 |
| D-2 | QA-PLAN Normal 4 + Minor 3 PM 직접 보정 (워커 재지시 대신) | agentic 폴백 승인 규칙 — 텍스트 보강 수준 작업 |
| D-3 | EXECUTE Step 1 v2.4 변경이력 폴백 거부 / Step 2 §6 폴백 승인 | 역사적 사실 보존 vs SSOT 일관성 강화 — 사안별 판단 |

## 4. 리스크 및 잔여 미해결

### 4.1 PLAN.md §5 리스크 7건 — 모두 대응 완료

| # | 리스크 | 대응 결과 |
|---|--------|---------|
| RISK-1 | 시나리오·화면 흐름도 경계 모호 | M-3 경계 박스 + consistency-rules §1 중복 검증 체크 추가 |
| RISK-2 | 기존 "순서도" 마이그레이션 | 변경이력 v4.0 행에 "사용자 수동 재분류" 명시 |
| RISK-3 | interview Round 3 제한 | M-7 "PRD 작성 모드 한정" 조건 SKILL.md 명시 |
| RISK-4 | 한 페이지 응집 vs 8섹션 충돌 | §7-3 작성 원칙 박스에 응집·간결·모호 금지 안내 |
| RISK-5 | network-guide.md Step 2·3 충돌 | Phase 1·2 순차 분리 — 발생 없음 |
| RISK-6 | 인용 누락 | EXECUTE 워커 프롬프트에 비개발 트랙 매트릭스 주입 — 발생 없음 |
| RISK-7 | 변경이력 누락 | Step 1 완료 기준 명시 + EXECUTE QA grep 검증 — 정상 추가 |

### 4.2 신규 발견 리스크

없음.

### 4.3 후속 작업 (본 태스크 범위 외)

| 후속 항목 | 비고 |
|---------|------|
| `~/.opal/skills/opal-pilot-write-tech/` 배포본 동기화 | `scripts/install/install-mac.sh` 재실행 — 캡틴 결정 |
| 기존 프로젝트 "순서도" 산출물 수동 재분류 | v4 적용 후 사용자별 수행 |
| B안(구현 컨텍스트 번들) | 별도 태스크로 분리 (본 자료 templates/ 3종 흡수 — 본 태스크 미채택) |

## 5. 추가작업 (CLOSE 후 보강 — 2026-05-24 18:01)

### 5.1 누락 발견

CLOSE 후 캡틴이 v4 인터뷰 재구성 시 **v3.4 TASK 전용 확인 항목 #4 "산출물 저장 경로"가 Round 1/2/3 어디에도 매핑 안 된 누락**을 발견. 다른 프로젝트에서 opwt 호출 시 PROJECT.md에 폴더 등록이 없으면 워커가 산출물 저장 위치를 결정 못해 막히는 원인.

### 5.2 추가작업 내용 (row 21)

SKILL.md 5개 영역 보강:

| # | 영역 | 변경 |
|---|------|------|
| 1 | "산출물 저장 구조" 절 | **default v4 7폴더 트리** 명시 (100.기획/110.PRD~170.기능시나리오) + 한국어/kebab-case 컨벤션 충돌 안내 |
| 2 | Round 2 표 | 질문 수 2→3, **Q6 "산출물 저장 경로"** 추가 |
| 3 | Step 1 도메인 옵션 구성 | **(d) 저장 경로 자동 감지** 가이드 — PROJECT.md 등록 / 100.기획/ 존재 / 둘 다 없음 3분기 |
| 4 | Step 4 TASK.md 양식 | **"산출물 저장 경로" 섹션** 추가 (선택 경로 / PROJECT.md 등록 여부 / default 적용 여부) |
| 5 | 변경이력 | v4.1 행 추가 (2026-05-24 18:01) |

### 5.3 Default 폴더 트리 (v4)

```
100.기획/
├── 110.PRD/                     ← 필수
├── 120.TRD/                     ← 필수
├── 130.정책서/                  ← 필수 (도메인별 파일 분리)
├── 140.IA/                      ← 필수 (JSON + Mermaid)
├── 150.기능도/                  ← 선택
├── 160.화면흐름도/              ← 선택
└── 170.기능시나리오/            ← 선택 (시나리오별 파일 분리)
```

- 폴더 생성 규칙: 작성 결정된 산출물만 폴더 생성 (작성 안 함 → 폴더 없음)
- 10 간격 prefix로 향후 산출물 추가 시 사이 삽입 가능
- 외부API명세서·운영정책서·서비스 매뉴얼은 default 미포함 (작성 결정 시 사용자 정의 prefix 부여)

### 5.4 검증 결과

```
grep -c "100\.기획/"        SKILL.md → 5
grep -c "Q6"                SKILL.md → 9
grep -c "산출물 저장 경로"  SKILL.md → 5
grep "v4\.1"                SKILL.md → 1행 (변경이력 v4.1)
```

### 5.5 추가작업 완료

- row 21 mark ✅
- state-tool status → `additional_work_done` 전환 완료

---

## 6. 변경이력 (DONE.md 자체)

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-24 15:35 | 태스크 008 완료 보고서 작성 — R-1~R-8 AC 35/35 충족 / 4 게이트 Pass / 3개 파일 변경 (008) |
| v1.1 | 2026-05-24 18:01 | §5 추가작업 절 신설 — CLOSE 후 누락 발견(산출물 저장 경로) → row 21 추가작업 + SKILL.md 5개 영역 보강 + default v4 7폴더 트리 명시. 변경이력 v4.1 (008 추가작업) |
