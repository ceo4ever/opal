# TASK: 브레인 entity 지식 품질 개선 — ingest @header 전사 탈피 (신규 작성 규율)

> 작성일: 2026-06-23 | 작업 유형: 개선 | 적용 스킬: opd | 모드: semi-agentic
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

brain의 **entity 페이지**가 `//opbr init` 시드 과정에서 code-scan @header를 **기계적으로 전사(transcription)**하여 code-scan 복제물로 전락하는 문제를 해결한다. brain 취지(WHY/HOW 지식 위키)·구성에 맞게 **사고하여 합성**하도록 **entity 작성 규율(템플릿 + 규칙)을 개선**한다. 기존 저품질 brain은 별도 보정 기능 없이 **전체 삭제 후 개선된 스킬로 재생성**하는 방식으로 처리한다(소급 보정·부분 재시드·enrich 미구현).

## 배경

`opal-brain`의 ingest는 코드 @header를 흡수해 entity 페이지를 생성한다. 그러나 입력이 코드뿐이면 WHY(설계 의도)는 코드에 없으므로 **WHAT 덤프**만 산출된다. 실제 MAMS `pages/entity/`의 Google Ads API 지식이 코드 식별자·enum·DTO·매핑 테이블 나열로 채워져 brain의 WHY/HOW 취지를 위반한 사례가 발견되었다.

현 brain 4모드 능력 지도: init(부트스트랩)·ingest(신규 누적, 기존 skip)·query(질의)·lint(무결성 정비)·sync-header(WHAT 신선도). **"콘텐츠 품질(WHY) 보강"** 축이 구조적으로 부재하다.

## 배경 분석 (대화에서 도출)

**근본 원인** — brain은 전사가 아니라 "지식 문서 취지·구성에 맞게 사고하여 재해석·합성"해야 한다. WHY 품질의 80%는 **입력 큐레이션**이 결정한다(실증: pointail `advertiser-admin-management.md`는 sources에 정책서+cross-repo code+task:007이 주입되어 진짜 WHY가 나옴 / MAMS Google은 code-only 입력이라 실패).

**참조 좋은 예시 분석** (`pointail/.opal/brain/pages/entity/advertiser/advertiser-admin-management.md`):
- GOOD: 다층 sources(§8.6) / 개요=비즈니스 프레이밍 / 책임(WHAT)=기능별+`file:line` 인용 / 설계배경(WHY)=실질 근거 / "## 소스 커버리지" 표로 코드 식별자 부록 분리(§8.8 실천).
- NOT-100%(개선 여지): (a) WHY에 HOW 누수 (b) WHY가 사실진술 수준 — *왜/기각된 대안* 부재 (c) provenance 문장단위 태깅 비일관 (d) 소스커버리지 표 일부 행 line number 누락.

**규칙 SSOT 위치** (프레임워크):
- §8 비즈니스 용어 우선 — `opal/core/references/harness/citation-rules.md` §8 (§8.1 적용대상에 brain entity/concept 명시, §8.8 개발자 부록 분리, §8.9 5W1H 섹션 강제 금지[MUST]).
- ingest 작성 규율 — `opal/skills/op-brain-ingest/SKILL.md` STEP 4.
- 모드/query/lint — `opal/skills/opal-brain/SKILL.md`.
- 결정론 집행 — `opal/tools/brain-tool/`.

## 확정된 설계 방향 (대화에서 합의)

**스코프 확정 (캡틴)**: 문제는 **entity 페이지에 국한**된다. concept/flow/synthesis/term은 사고하며 작성되어 양호 — **현행 유지, 손대지 않는다**. entity 대량 시드는 `//opbr init`(`analyze`→seed_candidates)에서 @header를 기계 적용해 문제가 발생한다(검증: `brain_tool.py` ingest-scan은 docs/skills/tasks→concept만, 코드→entity 분기 없음 → entity 주 경로는 init 시드).

**처리 방식 = brain 전체 삭제 → 개선된 스킬로 재생성** (단순화 — 부분 재시드·enrich·멱등 우회·lint 검출 전부 불필요).

**개선 방향 — "입력 큐레이션 선행 + entity 5섹션 작성 규율"** (init 시드 + 단건/CLOSE ingest entity 경로):

```
entity 작성 개선
 ① 입력 큐레이션 선행 — entity 작성 전 WHY 소스를 충분히 주입
     = PROJECT.md 문서레지스트리 관련 docs + PLAN 결정 + 정책/proposal + 관련 페이지
       (SKILL 절차로 강제할지, brain-tool why-sources 도구로 할지는 PLAN 결정)
 ② entity 5섹션 작성 규율 (pointail 참조)
     = 개요(비즈니스) / 책임(WHAT, `file:line` 인용) / 설계배경(WHY)
       / 관계(HOW) / 소스 커버리지(코드 식별자 부록 분리, line number 포함)
     + @header 전사 금지[MUST] · WHY 순도(HOW 분리) · WHY 깊이(기각대안, §8.9 사고틀)
       · provenance 태깅[필수]
```

**provenance 절대 가드**: entity WHY 각 주장은 `(근거: doc/POL/task:NNN PLAN§X)` / `(추론: 코드패턴)` / `(WHY 미확보)` 중 하나 — 헌법 "Don't fake it" 집행선.

**재생성 런북 (운영 절차 — 프로젝트별 실행)**:
```
① synthesis/ + 수기 편집 페이지 백업   (소스 없어 재생성 불가 → 유실 방지)
② .opal/brain 삭제 (또는 //opbr init --force)
③ //opbr init (+ 필요 시 ingest --all)  ← 개선된 스킬 적용
④ 백업한 synthesis/ 복원
```
> ⚠️ 리스크: 전체 재생성은 entity(@header)·concept(docs/skills/tasks)·term은 복구하나 **synthesis(질의 파생)·수기 지식은 유실** → 절차 ① 백업 필수.

## 명확화 결과

> TASK 4요소를 잠근다.

| 요소 | 확정값 | 미확정(있으면) | 의존 사실 |
|------|--------|--------------|----------|
| 목표 | brain **entity** 페이지의 @header 기계 전사를 탈피 — `//opbr init` 시드가 취지·구성에 맞게 합성하도록 entity 작성 규율을 개선한다. 기존 brain은 전체 삭제 후 개선된 스킬로 재생성한다(소급 보정 미구현) | - | entity 주 경로는 init 시드(analyze) — ingest --all은 concept/term만 |
| 범위 | **포함**: ① `opal-brain` init 시드 + `op-brain-ingest`의 **entity** 작성 규율 개선(@header 전사 금지·입력 큐레이션 선행·WHY 합성·provenance) ② entity 5섹션 템플릿 표준화(pointail 기반, 격차 a~d 보완) ③ 입력 큐레이션 수단(SKILL 절차 vs `why-sources` 도구 — PLAN 결정) ④ 전체 삭제→재생성 런북 문서화(synthesis 백업 포함) ⑤ citation-rules §8 정합. **제외**: concept/flow/synthesis/term(현행 유지) · enrich/소급 보정·부분 재시드 · lint 신규 검출 issue · 멱등 skip 우회 개조 · term draft 변경 · 타 프로젝트 실데이터 보정 | 입력 큐레이션을 도구화할지 여부는 PLAN | synthesis는 소스 없어 재생성 불가 → 런북 백업 필요 |
| 제약 | 헌법(Enforce not advise=가능 시 도구 게이트 / Don't fake it=provenance / Simplicity First=삭제-재생성으로 최소화 / 플랫폼 독립) · §8.9 5W1H 섹션 강제 금지[MUST] 회피(사고틀로만) · §8.1 brain entity가 §8 대상 · 배포 경계(~/.opal 직접편집 금지, opal/ 소스 수정→install 재배포) · brain-tool 단방향(wiki→origin 역수정 금지) · 변경이력/@header 규칙 | - | brain-tool은 Python CLI(pytest) |
| 완료기준 | ① entity 템플릿이 개요/책임(WHAT 인용)/설계배경(WHY)/관계(HOW)/소스커버리지(부록) 5섹션을 강제하고 @header 전사 금지가 [MUST]로 명문화됨 ② init 시드 + ingest entity 경로에 입력 큐레이션 선행 + provenance 태깅 규율이 반영됨 ③ 전체 삭제→재생성 런북(synthesis 백업·init --force·복원)이 문서화됨 ④ 도구 변경 시(why-sources 채택 시) RED-first pytest 통과·회귀0; 배포본에서 개선된 init로 entity 1건 재생성 시연 | - | - |

## 요구사항

- [ ] **R-1** brain **entity** 템플릿을 pointail 5섹션 구조로 표준화하고 격차 a~d(WHY 순도/깊이/provenance/인용완결)를 보완한다 — `opal-brain/SKILL.md` init 시드 entity + `op-brain-ingest/SKILL.md` STEP 4 entity 예시. AC: 템플릿에 5섹션 헤딩(개요/책임 WHAT/설계배경 WHY/관계 HOW/소스 커버리지) + WHY순도·provenance·소스커버리지 line number 규칙이 명문화되고, @header 전사 금지가 [MUST]로 기재된다. (concept/flow/synthesis/term 템플릿은 손대지 않는다)
- [ ] **R-2** entity 작성 규율에 "@header 전사 금지 + 입력 큐레이션 선행 + WHY 합성 + provenance 태깅"을 명문화한다 — `//opbr init` 시드 entity 경로 + 단건/CLOSE ingest entity 경로. AC: 입력 큐레이션(PROJECT.md 문서/PLAN/관련 페이지 주입) 선행 절차와 provenance 태깅 3종 규칙이 추가된다.
- [ ] **R-3** 입력 큐레이션 수단을 결정·구현한다 (SKILL 절차 강제 vs `brain-tool why-sources <source_ref>` 도구 — PLAN 결정). 도구 채택 시 AC: source_ref 입력 시 git blame→task / 정책·proposal grep / 관련 brain page 후보를 JSON 반환, RED-first pytest 통과·회귀0. (도구 미채택 시 SKILL 절차로만 처리, 코드 변경 없음)
- [ ] **R-4** brain 전체 삭제→재생성 런북을 문서화한다. AC: synthesis 백업 → 삭제(또는 `init --force`) → 개선된 `init` 재생성 → 복원 절차가 `opal-brain/SKILL.md`(또는 적절 위치)에 기재되고, synthesis 유실 리스크가 명시된다.
- [ ] **R-5** citation-rules §8과 brain entity SKILL/도구 연결을 정합한다(가벼운 정합). AC: §8.5 검증 연결 표가 변경 내용과 모순되지 않는다.

## 제약 조건

- **헌법 준수**: Enforce don't just advise(가능한 한 도구 게이트) / Don't fake it(provenance 태깅) / Simplicity First(P0→P3 점증) / 플랫폼 독립.
- **§8.9 [MUST]**: 5W1H를 페이지 섹션 헤딩으로 강제 금지 — 사고 프레임으로만 사용. (5섹션 구조 표준은 허용, ##누가/##왜 류 금지)
- **배포 경계**: `~/.opal/` 직접 편집 금지. `opal/` 소스 수정 후 install 재배포로 발효(L3는 캡틴 직접 수행 가능).
- **brain-tool 단방향**: origin→wiki만, wiki→origin 역수정 절대 금지.
- **추적성**: 스킬·참조·도구 수정 시 변경이력 표 행 추가(일시 KST + 태스크 번호).

## 기술 스택

- Python 3 (brain-tool CLI, pytest) / Markdown·YAML (스킬·참조 문서) / Bash (run.sh 래퍼)

## 관련 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | OPAL 헌법 | `~/.opal/PRINCIPLES.md` | Enforce/Don't fake it/Simplicity 원칙 |
| D-2 | 설계 | 인용 규칙 | `opal/core/references/harness/citation-rules.md` §8 | §8.1 적용대상·§8.8 부록분리·§8.9 5W1H 금지 |
| D-3 | 소스 | CLOSE ingest 워커 | `opal/skills/op-brain-ingest/SKILL.md` | STEP 4 entity 작성 규율·템플릿 수정 대상 |
| D-4 | 소스 | brain operator | `opal/skills/opal-brain/SKILL.md` | init 시드 entity 규율·템플릿 + 재생성 런북 수정 대상 |
| D-5 | 소스 | brain-tool | `opal/tools/brain-tool/` | (선택) why-sources 입력 조립 도구 — PLAN 결정 |
| D-6 | 참조 | 좋은 예시 | `pointail/.opal/brain/pages/entity/advertiser/advertiser-admin-management.md` | 5섹션 구조·부록분리 참조 기준 |
| D-7 | 참조 | 나쁜 예시 | `mams/.opal/brain/pages/entity/` (Google Ads API) | @header 전사 안티패턴 |
