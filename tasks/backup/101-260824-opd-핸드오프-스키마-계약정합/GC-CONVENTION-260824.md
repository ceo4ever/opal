# GC CONVENTION REPORT — 2026-08-24

## 1. 헤더

- 실행 일시: 시작 2026-08-24 23:10:00 / 완료 2026-08-24 23:19:21 / 소요 약 9분
- 범위: `all` (스코프 미지정) / 대상 파일 7개
  - `opal/skills/op-dev-analysis/SKILL.md`
  - `opal/skills/op-dev-plan/references/plan-guide.md`
  - `opal/core/references/harness/analysis-core.md`
  - `opal/skills/opal-pilot-dev/references/pipeline.json`
  - `opal/skills/op-dev-qa/SKILL.md`
  - `opal/skills/op-dev-qa/references/qa-dev-guide.md`
  - `opal/skills/op-dev-plan/SKILL.md`
  - (제외: `opal/core/AGENT.md` — 본 태스크와 무관한 동시 편집, PM 지시로 진단 제외)
- 에이전트: opal-convention-checker
- 기준 문서: `docs/CONVENTIONS.md` 존재 확인 (v1.8.0) — §네이밍/§파일구조/§변경이력/§State 관리 적용. 추가로 PM 지정 확인 항목 `opal/core/references/opal-doc-standard.md` §0/§0.1(실행 지시문 산문 규칙) 병행 확인
- APPLY 수행 여부: N (수동 대기 — 본 에이전트는 진단 전담, 수정 없음)

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 2 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 1 / Info 0 |
| 자동 수정 가능 | 0 |
| 수동 조치 필요 | 2 |
| 파일별 상위 Top 5 | `opal/skills/op-dev-analysis/SKILL.md` (1건) / `opal/skills/op-dev-plan/SKILL.md` (1건) |
| 카테고리별 빈도 | 문서화 (2개 파일) |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 (빈도 트리거 0건 + 새 카테고리 트리거 0건) |

**검증 통과 항목** (근거 확인 완료, 이슈 없음):
- `docs/CONVENTIONS.md` §State 관리 SSOT 규칙 — PM Gate `checklist` 신규 항목(`pipeline.json:13`)이 `opal-pilot-dev/SKILL.md`에 표로 중복 게재되지 않음을 확인 (`grep` 결과 미발견).
- 변경이력 `(101)` 태그 — 표 보유 6개 문서(`op-dev-analysis/SKILL.md:212`, `op-dev-plan/SKILL.md:471`, `plan-guide.md:469`, `analysis-core.md:185`, `op-dev-qa/SKILL.md:199`, `qa-dev-guide.md:165`) 전건 확인. `pipeline.json`은 표 미보유로 예외 대상 확인.
- `op-dev-qa/SKILL.md:123` ↔ `qa-dev-guide.md:93` P-8 거울 사본 — 공통 실질 문자열 `"ANALYSIS 핸드오프 2원천(§1.1 관련 파일 목록 = 파일 맵 4필드 영역·경로·역할·변경 유형 / §8 다음 단계 입력 = 결정형 확정값 3열)을 재도출 없이 인용"` 완전 일치 확인 (서술형 vs 의문형 어미 차이는 097 이전부터의 기존 포맷 차이로 신규 결함 아님).
- `변경 유형` 컬럼명 표기 통일 — `analysis-core.md:102`(SSOT) / `op-dev-analysis/SKILL.md:100` / `op-dev-plan/SKILL.md:117,218` / `plan-guide.md:94,101,360` / `pipeline.json:13` 전건 공백 포함 `변경 유형`으로 일치.
- `pipeline.json` JSON 구문 유효성 — `python3 -m json.load` 통과.
- `git diff --check` 공백 오류 — 0건.

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-C001 [`opal/skills/op-dev-analysis/SKILL.md:87`] ANALYSIS.md 산출물 템플릿에 삽입된 구값 폐지 안내 문장이 "행동을 만들지 않는 산문"에 해당
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(`opal/core/references/opal-doc-standard.md` §0.1 실행 지시문 규칙 — PM이 본 태스크에서 명시적으로 확인을 요청한 항목). `docs/CONVENTIONS.md`에는 이 규칙의 원문이 없으나 §0.1이 opal-doc-standard.md 소유의 확립된 SSOT이며 실행 지시문(스킬 md) 전반에 적용된다.
  - 설명: §22-31 "확정 입력 소비 규약"의 본문(`:27`)에서 이미 "구 `승계` 값은 폐지되어 `유효(대조 확인)`로 흡수된다"를 1회 명시했음에도, `## ANALYSIS.md 통일 형식` 코드펜스(즉 워커가 매 태스크 ANALYSIS.md에 그대로 복제하는 산출물 템플릿) 안의 `:87`에 동일 취지 문장을 재서술했다. §0.1 판정식("이 문장을 지우면 에이전트의 행동이 달라지는가?")에 대입하면: 워커가 산출물을 채울 때 필요한 값 도메인은 `:87` 앞 문장("판정값 도메인 — 결정 계열: ... 사실 계열: ...")만으로 완결되며, 뒤에 붙은 "구 `승계` 값은 폐지되어 ... 흡수한다"는 삭제해도 산출물 작성 행동이 달라지지 않는다 — §0.1이 명시한 "설명"(사람을 납득시킬 뿐 행동 불변) 유형에 해당하고, "도입 경위·논의 경과·대안 검토 기록"의 제거 대상 예시와 성격이 같다. 게다가 이 문장은 코드펜스 내부이므로 향후 모든 태스크의 실제 ANALYSIS.md 산출물에 "예전에 `승계`라는 값이 있었다"는 이력성 문구가 영구 보일러플레이트로 반복 삽입된다.
  - 해결 방안: `:87`의 "구 `승계` 값은 폐지되어 `유효(대조 확인)`로 흡수한다" 절을 산출물 템플릿(`:87`)에서 제거한다. 이력 설명은 `:27`(스킬 본문, 워커 대상 안내) 한 곳과 변경이력 표(`:212`)만으로 충분하다.
  - 자동 수정: N (문구 삭제 범위 판단 필요 — 문장 경계가 다른 필수 도메인 설명과 같은 줄에 있어 단순 정규식 치환 시 인접 필수 문구 손상 위험)
  - 참조: `opal/core/references/opal-doc-standard.md` §0.1 (프로젝트 내부 문서, URL 없음 — 경로 자체가 참조)

### Low (1건)

- [ ] GC-C002 [`opal/skills/op-dev-plan/SKILL.md:56-57`] ANALYSIS/PLAN 2단계의 동형 "확정 입력 판정" 절이 본 태스크에서 편측(ANALYSIS만)으로 갱신되어 값 도메인이 갈라짐
  - 카테고리: 문서화
  - 위반 기준: `docs/CONVENTIONS.md`에 두 절의 값 도메인 동일성을 명시한 규칙은 없음 — 확정 위반이 아닌 정합성 관찰 사항으로 Low 등재
  - 설명: 본 태스크(101)에서 `op-dev-analysis/SKILL.md:26-27,84-88`의 "확정 입력 판정" 값 도메인을 구 4값(`유효`/`승계`/`수정필요`/`사실오류`)에서 결정 계열(`해당없음(결정)`/`사실오류`)·사실 계열(`유효(대조 확인)`/`수정필요`/`사실오류`) 2계열로 교체했다. 그런데 `op-dev-plan/SKILL.md`도 동일 목적("TASK.md `[결정]` 태그 항목은 재도출·재설계 대상이 아니다")의 거울 절을 `:52-60`에 갖고 있으며, 이 절은 098에서 신설된 이래 3값(`유효`/`수정필요`/`사실오류`)을 그대로 유지한 채 이번 diff에서 손대지 않았다(`op-dev-plan/SKILL.md`는 본 태스크의 changed_files 7개 중 하나이나, 실제 diff는 §관련 파일 맵 컬럼명 표기 통일 1줄뿐 — `:56-57`은 무변경). ANALYSIS 단계와 PLAN 단계에서 동일한 TASK.md 태그를 서로 다른 이름의 값으로 판정하게 되어, 두 산출물을 나란히 리뷰하는 PM/QA 입장에서 "같은 개념인데 왜 이름이 다른가"라는 해석 비용이 생긴다. 다만 두 절은 이미 098 시점부터 값 개수(4값 vs 3값)가 달랐던 비대칭 구조였으므로(ANALYSIS는 상류 대조확인 상황을 `승계`로 별도 표기할 수 있었던 반면 PLAN에는 애초에 그 값이 없었음), 이번 변경이 새로운 비대칭을 "만든" 것이 아니라 기존 비대칭의 표현 형태를 심화시킨 것으로 판단해 Medium이 아닌 Low로 분류한다.
  - 해결 방안: 소유자 확인 필요 — (a) PLAN의 절은 원래 별개 개념(PLAN 단계 자체 판단)이라 통일 대상이 아니라면 현행 유지, (b) 동일 개념의 거울 절이 맞다면 후속 태스크에서 PLAN 쪽도 2계열 도메인으로 동기화.
  - 자동 수정: N
  - 참조: TBD — 프로젝트 내부 설계 의사결정 사항이라 외부 린트 규칙 없음. 소유자 판단 필요.

### Info (0건)

---

## 4. 문서 업데이트 제안 (§9·§10, 트리거 발동 시만)

트리거 미발동 — 빈도 트리거(N=3 이상 파일)·새 카테고리 트리거 모두 해당 없음. 발견된 2건은 각각 1개 파일에 국한.

---

## 5. 문서 작성 유도 (해당 시)

`docs/CONVENTIONS.md` 존재 — 작성 유도 생략.
