# QA: PLAN — community-skills 번들 → fetch 방식 전환 (skills.sh / npx skills)

> 검토일: 2026-05-10 | 판정: Pass (Warning 1건 / Info 3건)

---

## 1. 요약

PLAN은 TASK.md 캡틴 결정 D-1~D-4를 §0 SSOT로 명시 고정한 후, P-1~P-12 자율 결정으로 구체화한다. 레지스트리 스키마 v2 변환 → skill-registry.js 미설치 감지 + fetch 정보 노출 → opal-skill-manager SSOT 갱신 → install 스크립트 번들 제거 → 폴더 git rm → 문서 갱신 → mac/Windows 양 OS 회귀 검증의 11단계 순서가 명확하다. 핵심 설계(§2.3)는 JSON 샘플 코드, before/after 비교, 함수 시그니처 수준의 의사코드를 갖추어 EXECUTE 워커가 PLAN만으로 즉시 착수 가능하다. TASK.md R-1~R-8 및 캡틴 D-1~D-4가 빠짐없이 Step에 매핑되어 있고, 변경이력 의무 4개 파일 모두 번호·형식까지 명시되어 있다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | §0 SSOT → §1.1 참조 → §1.2 [MUST] → §2.3 핵심 설계 → §3 Step별 완료 기준·테스트 명령어 모두 완비 |
| GP-2 | 의존성 순서 | Pass | `1→2→3→(4‖5)→6→(7‖8‖9)→10/11` 순서가 의존성 방향(데이터→도구→스킬→install→폴더→문서→회귀)과 정합 |
| GP-3 | TASK 반영 | Pass | R-1~R-8 모두 Step AC 매핑 확인. 캡틴 D-1~D-4 §0 SSOT 명시 후 §2.3에서 각각 설계 |
| GP-4 | 파일 목록 완전성 | Pass | M-1~M-8 + 삭제 R-1로 TASK.md 관련 대상 전체 포함. docs/PROJECT.md(M-8)는 PLAN 자율 결정(P-11)으로 합리적 추가 |
| GP-5 | 설계 구체성 | Pass | §2.3.1~§2.3.9 각 파일별 JSON 샘플/코드/before-after 명시. 4개 함수 변경 시그니처 + 응답 스키마 확장 완비 |
| GP-6 | 체크리스트 커버리지 | Pass | §4.1 기능 10항목 / §4.2 일관성 6항목 / §4.3 문서 품질 6항목 / §6 PM-1~PM-12 12항목 — 3계층 QA 체크리스트 |
| D-2 매핑 | 스키마 v2 구체성 | Pass | JSON 샘플 + 필드 결정 P-1~P-4 표 + 라이선스 매핑 표 + paths 동적 처리 함수(`getCommunitySkillPath`) 명시 |
| D-3 매핑 | skill-registry.js 로직 | Pass | 4개 함수 변경 명시 + 기존 main 스킬 호환성 유지 선언 + 기존 `match` 동작 무변화 확인 |
| D-4 매핑 | 기존 사용자 보존 | Pass | clean_dirs 배열에서 community-skills 제거 명시(§2.3.4/§2.3.5 양쪽). D-4 의도 코멘트로 강조 |
| 변경이력 | 4개 파일 의무 | Pass | skill-registry.js(P-9 신설 v1.0) / opal-skill-manager(v1.1) / install-mac.sh(v2.0) / windows.ps1(v1.6.0) — Step 2~5에 모두 명시 |
| 회귀 위험 | mac + Windows 시나리오 | Pass | §5 R-1~R-6 리스크 명시. Step 10(mac 6개 검증) + Step 11(Windows 4개 검증) 구체적 명세 |
| agent 라우팅 | opal-task-agent 폴백 | Pass | 모든 Step에 `agent: opal-task-agent` — PROJECT.md Framework 단일 영역 폴백과 정합 |
| 캡틴 환경 의무 | Step 10/11 검증 명시 | Pass | Step 10 `(캡틴 머신에서 실행)` 명시. §워커 자체 결정에 "Step 10/11 결과 보고 후 CLOSE 진입 승인" 명시 |
| 용어 일관성 | `owner/repo@skill` 토큰 | Pass | §5 R-T1에서 4개 영역 모두 `{owner}/{repo}@{skill}` 단일 토큰 사용 확인. `community-skills` 표현 PLAN 전체 kebab 일관 |
| citation-rules | §2.4 / §7 준수 | Pass | §1.2 [MUST] 인용 원문 포함. §2.3 각 섹션 인라인 인용(D-N §N) 기재. §5 R-T1 영역 간 용어 일관성 검토 완료 |
| W-1 | Windows Step 11 회귀 비대칭 | Warning | Mac Step 10에 6개 검증(installed 필드 확인 포함)인 반면 Windows Step 11은 4개 — `match "//pdf"` 응답의 `installed` 필드 검증 미포함 |
| I-1 | openai source_repo 미확인 | Info | §2.3.1 라이선스 매핑 표 `openai`의 source_repo가 "(실제 owner/repo 확인 필요)"로 표기 — EXECUTE 워커 추가 조사 의무. §5 R-1로 리스크 관리됨 |
| I-2 | opal-skill-manager 변경이력 신설 조건 | Info | 기존 SKILL.md에 변경이력 표 없으면 신설 조건이 있으나 신설 형식과 추가 형식이 같아 실질 영향 없음 |
| I-3 | README L37 vs L39 행 번호 불일치 | Info | TASK.md §R-6 "L37"과 PLAN §2.3.7 "L39" 표기가 다름. 실측 기반으로 PLAN 번호 우선 사용 권장 |

---

## 3. 지적 사항

### Warning

#### W-1: Windows Step 11 회귀 검증 비대칭 (Warning)

**영역**: §3 Step 11

**내용**: mac Step 10에는 6개 검증 항목(install 정상 종료 / community-skills 보존 / validate 통과 / `match "//pdf"` 응답 `installed` 확인 / `//skill-manager` 매칭 / `npx skills find` 호출)이 있으나, Windows Step 11은 4개(install 정상 종료 / community-skills 보존 / validate 통과 / `npx skills find` 호출)만 명시되어 있다. `match "//pdf"` 응답에서 `installed` 필드 확인과 `//skill-manager` 매칭 검증이 빠져 있어 EXECUTE 단계에서 Windows측 skill-registry.js v2 동작 검증이 누락될 수 있다.

**권장 조치**: Step 11 작업 내용에 항목 5 `node ~\.opal\tools\skill-registry\skill-registry.js match "//pdf"` 응답의 `installed: false` 확인 추가. 사용자 판단으로 진행 가능한 수준.

---

### Info

#### I-1: openai source_repo 미확인 (Info)

PLAN §2.3.1 라이선스 매핑 표에서 `openai`의 source_repo prefix가 `openai/skills@{skill} (실제 owner/repo 확인 필요)`로 표기되어 EXECUTE 워커에 추가 조사를 위임함. §5 R-1 리스크로 관리되어 있고, 검증 불가 시 `source_repo: null`로 처리하는 폴백이 명시되어 있어 EXECUTE 진행에 영향 없음.

#### I-2: opal-skill-manager 변경이력 신설 조건 (Info)

§2.3.3에 "기존 SKILL.md에 변경이력 표가 없으면 §참고 다음에 신설" 조건이 기술되어 있으나, 신설과 추가의 최종 결과물은 동일하므로 실질적 모호성 없음.

#### I-3: README 행 번호 불일치 (Info)

TASK.md R-6에서 "L37 + L729"로 표기하고 PLAN §2.3.7에서 "L39"와 "L732"로 표기함. 기존 141 태스크 후속 정리 과정에서 행 번호가 이동한 것으로 추정되며 PLAN 번호가 더 최신 실측 기반일 가능성이 높음. EXECUTE 워커는 실제 파일을 Read하여 정확한 행을 직접 확인 후 수정 요망.

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1~R-8 | PLAN §3 Step 1~11 AC 매핑으로 전부 커버 | Pass |
| TASK.md D-1~D-4 (캡틴 결정) | PLAN §0 SSOT 명시 + §2.3.1~§2.3.5 각각 설계 | Pass |
| TASK.md §제약 조건 변경이력 의무 | PLAN Step 2~5 각각 변경이력 행 번호·형식 명시 | Pass |
| TASK.md §제약 조건 사용자 데이터 보존 | PLAN §2.3.4/§2.3.5 양 OS clean_dirs 제거 + D-4 코멘트 강조 | Pass |
| TASK.md §제약 조건 mac/Windows 동등 처리 | PLAN §2.3.4 vs §2.3.5 대조 — 4개 변경 패턴(clean_dirs/복사블록/종료안내/변경이력) 대칭 | Pass |
| TASK.md §제약 조건 141 후속 정리 의무 | PLAN Step 7 README L39+L732 갱신 명시 | Pass |
| citation-rules.md §2.4 | PLAN §1.2 [MUST] 원문 인용 + §2.3 인라인 D-N §N 인용 | Pass |
| citation-rules.md §7 | PLAN §5 R-T1 영역 간 용어 일관성 검토 완료 (decision_required 없음) | Pass |

---

## 5. 판정

**Pass**

TASK.md R-1~R-8 및 캡틴 D-1~D-4가 PLAN에 빠짐없이 반영되었고, 핵심 설계(스키마 v2 / skill-registry.js 변경 / 변경이력 4개 파일 / 회귀 검증 시나리오)가 의사코드·샘플 수준으로 명세되어 EXECUTE 즉시 착수 가능하다. Warning 1건(Windows Step 11 회귀 검증 비대칭)은 EXECUTE 워커가 검증 항목을 자체 보완할 수 있는 수준으로, 다음 단계 진행에 영향을 주지 않는다.
