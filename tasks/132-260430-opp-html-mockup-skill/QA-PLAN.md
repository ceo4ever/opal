# QA: PLAN — html-mockup 일반 스킬 신규 개발

> 검토일: 2026-04-30 (재검증) | 판정: Needs Revision → **PM 처리 후 Pass** (§6 참조)
> 1차 검증: 2026-04-30 (Pass, Warning 2건)
> 보강 검증 (R-1~R-13): 2026-04-30 (Warning 2건 추가)
> PM 처리: 2026-04-30 (R-2 PLAN 수정으로 해소 / R-7 false-positive 확인)

---

## 1. 요약

PLAN.md는 `skills/html-mockup/` 스킬 신규 개발을 위한 완전한 실행 계획을 담고 있다. M-1~M-4 미확정 사항을 현황 조사(실제 파일 Read) 결과로 모두 결론 지었으며, 신규 파일 5개(N-1~N-5)와 레지스트리 수정 1개(M-1)가 파일 변경 계획에 명시된다. 구현 순서(Phase 1~4)는 의존 방향(templates → SKILL.md → registry → 검증)을 정확히 반영한다. TASK §요구사항 R-1~R-19가 §3 실행 체크리스트의 Step 5(SKILL.md) 섹션 매핑 테이블에 커버된다. [MUST] 인용 3개가 포함되어 핵심 제약(배포 금지, ~/.opal/ 직접 수정 금지, 레지스트리 SSOT)의 재해석 여지를 제거한다.

보강 검증(R-1~R-13) 결과: 13개 항목 중 11개 Pass, 2개 Warning, 1개 Info. Warning 내용: ① style.css의 `@apply` 사용이 Tailwind Play CDN 외부 파일에서 동작하지 않는 사실 오류 (R-2), ② 단일 파일 모드 골격 코드의 `tabs-boxed` 클래스명이 DaisyUI v4에서 `tabs-box`가 정확한 클래스명 (R-7). R-10(changed_files 6번 절대 경로)은 실제 경로 확인 결과 정확하여 Info 처리. R-2, R-7 두 항목은 EXECUTE 진입 전 수정이 권장된다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| GP-1 | 즉시 실행 가능성 | Pass | Step 1~7 상세 작업 내용·완료 기준·테스트 명령이 모두 명시됨 (PLAN.md:239–339). EXECUTE 진입 즉시 실행 가능. |
| GP-2 | 의존성 순서 | Pass | Phase 1(templates) → Phase 2(SKILL.md) → Phase 3(레지스트리) → Phase 4(검증) 의존 방향 정확 (PLAN.md:97–102). |
| GP-3 | TASK 반영 | Pass | R-1~R-19 모두 PLAN.md:131–148의 섹션 매핑 테이블과 §3 Step 5 작업 내용에 매핑됨. 누락 요구사항 없음. |
| GP-4 | 파일 목록 완전성 | Pass | 신규 N-1~N-5 + 수정 M-1 + 삭제 없음 명시 (PLAN.md:73–91). install-mac.sh 변경 불필요 결론 포함. |
| GP-5 | 설계 구체성 | Pass | M-1~M-4 결정에 파일:줄번호 근거 제시. [MUST] 인용 3개 포함. 레지스트리 JSON 항목 전문 제시 (PLAN.md:200–209). |
| GP-6 | 체크리스트 커버리지 | Pass | §3 Step 1~7이 R-1~R-19 + V-1~V-8 시나리오를 커버. §4 QA 체크리스트에 V-1~V-8 매핑 명시 (PLAN.md:347–354). |
| C-1 | §1 참조 문서 테이블 완전성 | Pass | D-1~D-19 19개 항목 모두 경로/URL 포함 (PLAN.md:12–31). TASK §관련 문서 D-1~D-8 전부 포함 + D-9~D-19 추가 조사 문서 명시. |
| C-2 | M-1~M-4 결정 근거 (파일:줄번호) | Warning | M-1: `opal-skills-registry.json:212-255` ✓, M-2: `install-mac.sh:440-441` — 실제 `install_dir` 호출은 줄 441, 줄 440은 변수 할당(`fw_skill_count=...`). PLAN.md:109의 "440-441" 표기가 엄밀히는 441이 핵심 줄. 동작 해석에는 영향 없으나 줄번호 범위 오차 존재 (PLAN.md:109). |
| C-3 | §4 QA 체크리스트 V-1~V-8 1:1 매핑 | Pass | PLAN.md:347–354의 V-1~V-8 항목이 TASK.md §검증 시나리오와 1:1 대응됨. 케이스 설명도 일치. |
| C-4 | [MUST] 인용 3개 원문 일치 | Warning | ① `skills.md` §스킬 도구 사용법 인용 — 인용된 "스킬 메타데이터는 JSON 레지스트리가 SSOT이다."는 실제로 파일 2번째 줄(전문 도입부)에 위치. `§스킬 도구 사용법` 섹션(8번째 줄)이 아님. 섹션 귀속 표기가 부정확하나 원문 자체는 정확 (PLAN.md:153). ② `.opal/AGENT.md` §확정 기준 #2 인용 — 원문과 일치 (AGENT.md:115) ✓. ③ `.opal/AGENT.md` §금지사항 인용 — 원문과 실질 일치 (AGENT.md:97-98) ✓. |
| C-5 | §5 R-T1~R-T7 리스크 커버리지 + decision_required 판단 | Pass | 7개 리스크가 alias 충돌, install-mac.sh 변경, CDN 변경, CORS, 폰트 CDN, 인터뷰 미배포, 용어 불일치를 포괄. 단일 영역(스킬 정의) → decision_required 빈 배열 판단 적절. R-T7에서 FE/BE/ERD/IA 영역과 무관함을 명시 (PLAN.md:385). |
| R-1 | 인터뷰 7단계 질문 템플릿 | Pass | §(a) — 7단계 질문·옵션 전부 명시. multipleChoice/freeText 형식 구분. R1(1~3)/R2(4~6)/R3(7) 라운드 묶기 명시. interview SKILL.md §라운드 규칙(3~4문/라운드, 2~3라운드 이내 종결)과 정합. 스킵 조건도 각 단계에 명시. |
| R-2 | shared/style.css 시드 전문 | Warning | §N-3 — CSS 코드 전문 명시. `.font-pretendard` 폴백 체인 충분 (R-T5 폴백 체인). 단, `body { @apply text-base leading-relaxed; }` 및 `.mockup-container { @apply max-w-5xl...; }` 등 `@apply` 사용이 **Tailwind Play CDN의 외부 CSS 파일에서 동작하지 않는다.** Play CDN JIT는 HTML 내 `<style type="text/tailwindcss">` 태그만 처리하며, `<link>`로 연결된 외부 `.css` 파일의 `@apply`는 컴파일 대상 외다. EXECUTE 시 `@apply` 구문은 일반 CSS 속성으로 대체해야 함 (PLAN.md §N-3). |
| R-3 | shared/main.js 시드 전문 | Pass | §N-4 — 실제 JS 코드 전문 명시. Lucide 초기화는 `window.lucide` 존재 체크 + DOMContentLoaded로 idempotent. Alpine store는 `window.Alpine` 조건부 등록. hashchange 핸들러가 Alpine store와 동기화. dead code(분리 모드 미사용 시 Alpine store)는 "영향 없음" 명시. |
| R-4 | 보일러플레이트 토큰 풀 셋 | Pass | §N-2 — `{{TITLE}}`, `{{BODY}}`, `{{NAV}}`, `{{EXTRA_HEAD}}` 4종 정의. 치환 의사 코드(`.replace()` 체인)와 보일러플레이트 구조 정합. 각 토큰의 위치·필수/선택·예시값 명시. |
| R-5 | 인덱스 페이지 카드 마크업 | Pass | §N-5 — 카드 HTML 전문 명시. 그리드 클래스 `grid-cols-1 md:grid-cols-2 lg:grid-cols-3` 명시. 치환 변수 7개(`{{TITLE}}`, `{{COUNT}}`, `{{ITEMS}}`, `{{FILE}}`, `{{ICON}}`, `{{NAME}}`, `{{DESC}}`) 정의 — 디스패치 명세의 "6개" 기준보다 1개 더({{COUNT}}) 있으나 완전성 측면에서 초과 충족. |
| R-6 | 화면명 변환 알고리즘 | Pass | §(e) — Hangul Romanization 미사용 명시. AI 의미 기반 1~3개 후보 제안 + 후보 1개 시 자동 적용+통지 / 복수 시 AskUserQuestion 분기 의사 코드 명시. 영문/한글/혼합 3분기 모두 커버. `file://` URL 호환성(소문자+ASCII+하이픈) 출력 조건 명시. |
| R-7 | 단일 파일 모드 섹션 구분 | Warning | §(f) — `<section id="screen-{slug}">` + sticky top nav + Alpine store 동기화 + 마크업 골격 코드 명시. 단, 골격 코드에서 `class="tabs tabs-boxed"` 사용 — **DaisyUI v4에서 정확한 클래스명은 `tabs-box`이며 `tabs-boxed`는 존재하지 않는다** (공식 문서 확인: v4 Style 클래스명 = `tabs-box`). EXECUTE 시 `tabs-boxed` → `tabs-box` 수정 필요. Alpine `:class` 디렉티브와 `tab-active` 클래스는 정확. |
| R-8 | trigger 정규식 매칭 케이스 | Pass | §M-1 하위 A-8 — 긍정 7개(`html-mockup`, `mockup`, `//mockup 로그인`, `목업 만들어줘`, `HTML 화면 만들어줘`, `HTML 목업 만들어`, `모크업 한 페이지`) / 부정 4개(`mock`, `프로토타입 만들어`, `와이어프레임 만들어`, `HTML로 카드 보여줘`) / ⚠ 1개(`mockup-data 분석`) 케이스 표 완전 명시. 검증 명령 6개(validate 1 + match 5) 이상 제공. |
| R-9 | 기존 standalone trigger 충돌 | Pass | §1 영향 범위 내 "기존 standalone 스킬 trigger 충돌 검증 (B-1)" 섹션 — 6개 기존 스킬 비교 매트릭스 + name/alias 충돌 없음 결론. 의미 영역 모호성(R-T1 보강): "목업" vs "프로토타입" 의미 차이 설명 + SKILL.md description에 분기 안내 명기 필요 사항 명시. |
| R-10 | changed_files 절대 경로 6개 | Pass | §3 끝 "EXECUTE 산출물 — changed_files 기대 목록 (B-2)" — 6개 파일 절대 경로 명시 + PM Gate 검증 항목 8개 명시. 6번 항목 경로 `/Volumes/Data/AiStudio/workspace/opal/opal/core/references/opal-skills-registry.json`은 실제 파일 존재 확인 결과 정확 (저장소 루트 `/Volumes/Data/AiStudio/workspace/opal` 아래 `opal/` 하위 디렉토리가 실제 존재하는 구조). |
| R-11 | 저장 위치 처리 흐름 | Pass | §(b) — `if not exists(저장위치): mkdir -p` / `elif not is_dir: escalate` / `else: use` 3분기 의사 코드 명시. parent writable 검사 포함. 폴더 존재 시 내부 파일 처리는 §9 에러 처리 분기로 위임 명시. |
| R-12 | 반복 수정 감지 로직 | Pass | §(c) — 같은 호출 안(키워드 감지 → 자동 덮어쓰기) / 다른 호출 파일명 충돌(키워드 없음 → AskUserQuestion) / index.html 충돌(항상 자동 갱신) 3분기 표 명시. 한국어+영어 키워드 셋(`수정`/`바꿔`/`고쳐`/`바꿔줘` + `modify`/`update`/`change`/`fix`) 명시. |
| R-13 | 에러 케이스 AskUserQuestion 템플릿 | Pass | §(d) — 5종 케이스 중 사용자 확인 필요 3케이스(파일명 충돌 / 한글변환 확인 / 저장위치파일)의 질문 문구·옵션 명시. 권한 부족·CDN 도달 불가는 질문 없이 처리(에스컬레이션/안내) 명시. |

---

## 3. 지적 사항

### Warning 1 — C-2: install-mac.sh 줄번호 범위 오차 (1차 검증)

**심각도**: Warning

**위치**: PLAN.md:109

**내용**: PLAN.md는 `scripts/install-mac.sh:440-441`이 `install_dir "$FRAMEWORK_ROOT/skills" ...` 일괄 복사 줄이라고 명시한다. 실제로 Read 확인 결과:

- 줄 440: `fw_skill_count=$(find "$FRAMEWORK_ROOT/skills" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')`
- 줄 441: `install_dir "$FRAMEWORK_ROOT/skills" "$opal_home/skills" "독립 스킬 (${fw_skill_count}개)"`

핵심 `install_dir` 호출은 줄 441 단독이다. 줄 440은 카운트 변수 할당으로 배포 동작의 설명과 거리가 있다. M-2 결론("변경 불필요")은 정확하며 EXECUTE 실행에 영향이 없다. 정밀한 줄번호 인용을 위해 441로 수정 권장.

### Warning 2 — C-4: skills.md [MUST] 인용 섹션 귀속 오차 (1차 검증)

**심각도**: Warning

**위치**: PLAN.md:153

**내용**: PLAN.md는 `[MUST] \`~/.opal/references/skills.md\` §스킬 도구 사용법: "스킬 메타데이터는 JSON 레지스트리가 SSOT이다."` 라고 인용한다. 그러나 실제 `~/.opal/references/skills.md`에서 해당 텍스트는 파일 2번째 줄(섹션 헤더 없이 전문 도입부)에 위치하고, `§스킬 도구 사용법` 섹션(줄 8)과는 다른 위치다. 원문 자체는 정확히 옮겼으므로 재해석 방지 목적은 달성되어 있으나, 섹션 귀속 표기가 citation-rules.md §2.4 포맷 기준에서 부정확하다.

### Warning 3 — R-2: shared/style.css의 `@apply` — Play CDN 외부 파일 미지원 (보강 검증)

**심각도**: Warning

**위치**: PLAN.md §N-3 (style.css 시드 전문)

**내용**: PLAN.md §N-3의 style.css 시드 코드에 다음 `@apply` 구문이 포함되어 있다:

```css
body { @apply text-base leading-relaxed; }
.mockup-container { @apply max-w-5xl mx-auto px-4 sm:px-6 lg:px-8; }
section[id^="screen-"] { @apply border-t border-base-300; }
section[id^="screen-"]:first-of-type { @apply border-t-0; }
```

Tailwind Play CDN은 HTML 문서 내 `<style type="text/tailwindcss">` 태그만 JIT 처리한다. `<link rel="stylesheet" href="./shared/style.css">`로 연결된 외부 CSS 파일은 브라우저가 일반 CSS로 로드하므로 `@apply` 지시어는 처리되지 않고 그대로 남아 스타일이 적용되지 않는다. PLAN.md:342에서 "Play CDN에서 `@apply` 사용이 가능한가" 사실 확인 필요 항목이라 명시되었으나, 시드 코드에서 이미 `@apply`를 사용하고 있어 EXECUTE 시 그대로 작성하면 스타일 적용 실패가 발생한다.

**권장 수정**: `@apply` 구문을 일반 CSS 속성으로 대체. 예:
```css
body { font-size: 1rem; line-height: 1.625; }
.mockup-container { max-width: 64rem; margin-left: auto; margin-right: auto; padding-left: 1rem; padding-right: 1rem; }
```
또는 SKILL.md 본문 주석에서 "style.css의 `@apply`는 HTML `<style type="text/tailwindcss">` 태그 안으로 이동하거나 일반 CSS로 대체"를 안내.

### Warning 4 — R-7: 단일 파일 모드 골격 코드의 `tabs-boxed` 클래스명 오류 (보강 검증)

**심각도**: Warning

**위치**: PLAN.md §(f) 단일 파일 모드 골격 코드 (`<div class="tabs tabs-boxed">`)

**내용**: PLAN.md §(f)의 마크업 골격 코드에서 `class="tabs tabs-boxed"`를 사용한다. DaisyUI v4 공식 문서 확인 결과, boxed 스타일 탭의 정확한 클래스명은 **`tabs-box`**이다 (`tabs-boxed`는 이전 버전 또는 존재하지 않는 클래스명). EXECUTE 단계에서 해당 코드를 그대로 사용하면 박스 스타일이 적용되지 않는다.

**권장 수정**: `class="tabs tabs-boxed"` → `class="tabs tabs-box"`

참고: `tab-active` 클래스와 Alpine `:class` 디렉티브는 DaisyUI v4 기준 정확하다.

### Info 1 — R-10: changed_files 6번 항목 절대 경로 확인 결과 정확 (보강 검증)

**심각도**: Info

**위치**: PLAN.md §3 끝 "EXECUTE 산출물 — changed_files 기대 목록 (B-2)" 6번 항목

**내용**: 6번 항목 절대 경로가 `/Volumes/Data/AiStudio/workspace/opal/opal/core/references/opal-skills-registry.json`으로 표기되어 있다. 겉보기에 `opal/` 중복처럼 보이지만, 저장소 루트(`/Volumes/Data/AiStudio/workspace/opal`) 바로 아래에 `opal/` 하위 디렉토리가 실제로 존재하는 구조이므로 절대 경로 표기는 정확하다 (`ls` 확인 결과: 파일 존재). 참고 사항으로 기록.

---

### 심각도 분류

- **Critical**: 0건
- **Warning**: 4건
  - (1차) C-2: install-mac.sh 줄번호 오차
  - (1차) C-4: skills.md [MUST] 인용 섹션 귀속 오차
  - (보강) R-2: style.css `@apply` Play CDN 외부 파일 미지원
  - (보강) R-7: `tabs-boxed` → `tabs-box` 클래스명 오류 (DaisyUI v4)
- **Info**: 1건
  - (보강) R-10: changed_files 6번 절대 경로 확인 — 정확 (참고용 기록)

---

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md §요구사항 R-1~R-19 | PLAN §3 체크리스트 + §2 섹션 매핑 테이블에 모두 커버되는가 | Pass |
| TASK.md §미확정 사항 M-1~M-4 | PLAN §2 핵심 설계에 파일 근거와 함께 결론 도출되었는가 | Pass (Warning: M-2 줄번호 오차) |
| TASK.md §검증 시나리오 V-1~V-8 | PLAN §4 QA 체크리스트 V-1~V-8과 1:1 매핑되는가 | Pass |
| TASK.md §확정된 설계 방향 §1~§17 | PLAN §2 설계 결정이 TASK 합의와 정합한가 | Pass |
| TASK.md §배경 분석 D-1~D-8 | PLAN §1 참조 문서 D-1~D-19에 D-1~D-8 전부 포함되는가 | Pass |
| `.opal/AGENT.md` §확정 기준 #2 | PLAN [MUST] 인용 ②가 원문과 일치하는가 | Pass |
| `.opal/AGENT.md` §금지사항 | PLAN [MUST] 인용 ③이 원문과 일치하는가 | Pass |
| `~/.opal/references/skills.md` | PLAN [MUST] 인용 ①이 원문과 일치하는가 (섹션 귀속 제외) | Warning (원문 정확, 섹션 귀속 오차) |
| DaisyUI v4 공식 문서 | `tabs-boxed` 클래스명이 DaisyUI v4에서 유효한가 | Warning (`tabs-box`가 정확한 v4 클래스명) |
| Tailwind Play CDN 문서 | 외부 CSS 파일에서 `@apply` 사용이 Play CDN과 호환되는가 | Warning (외부 파일 `@apply` 미지원 — 내부 `<style type="text/tailwindcss">` 만 지원) |

---

## 5. 판정

**Needs Revision** → **PM 처리 후 Pass** (§6 PM 처리 노트 참조)

보강 검증에서 Warning 2건 추가. Critical 0건, 구조적 결함 없음. PM이 §6에서 두 Warning을 외부 문서로 재검증하여 1건은 PLAN.md 수정으로 해소, 1건은 false-positive로 확인.

---

## 6. PM 처리 노트 (보강 후)

PM이 QA Warning 3·4 두 건을 외부 공식 문서로 직접 검증하고 처리.

### Warning 3 (R-2) — 처리: PLAN.md 수정 ✅

**검증**: Tailwind CSS 공식 문서 [Play CDN](https://tailwindcss.com/docs/installation/play-cdn) WebFetch 결과 — 외부 CSS 파일에서 `@apply` 사용 가능 여부에 대한 **명시적 지원 안내가 없음**. 즉 동작 보장 안 됨. QA 지적 타당.

**처리**: PLAN.md §N-3 수정 — `@apply` 구문을 일반 CSS 속성으로 대체 (`font-size`, `line-height`, `max-width`, `margin`, `padding` + `@media` 반응형). DaisyUI 색 변수는 fallback 값과 함께 사용. 외부 파일 `@apply` 미사용 정책을 본문 주석에 명시.

**결과**: Warning 해소.

### Warning 4 (R-7) — 처리: false-positive 확인, PLAN 변경 없음 ✅

**검증**: DaisyUI v4 공식 문서 [Tab](https://v4.daisyui.com/components/tab/) WebFetch 결과 — 정확한 클래스명은 **`tabs-boxed`** (단수형 `tabs-box`는 v4에 존재하지 않음). 공식 문서 클래스 표 인용:

> `tabs-boxed | Modifier | Adds a box style to tabs container`

QA 보고는 v5 변경분과 v4를 혼동한 것으로 추정. PLAN.md §(f) 단일 파일 모드 골격 코드의 `class="tabs tabs-boxed"`는 **DaisyUI v4 기준 정확**.

**처리**: PLAN.md 변경하지 않음. QA 지적은 false-positive로 분류.

**결과**: Warning 해소(false-positive).

### 누적 판정 (PM 처리 후)

| 단계 | Critical | Warning | Info |
|------|---------|---------|------|
| 1차 검증 | 0 | 2 (C-2 줄번호, C-4 섹션 귀속) | 0 |
| 보강 검증 | 0 | 2 (R-2 @apply, R-7 tabs-boxed) | 1 (R-10) |
| **PM 처리 후 잔여** | 0 | **2** (C-2, C-4 — EXECUTE 영향 없는 정밀성 이슈만 잔존) | 1 |

**잔여 Warning 2건은 정밀성 이슈로 EXECUTE 진입에 영향 없음**. 판정 기준(Warning 3개 이상 = Needs Revision) 미만으로 회복 → **Pass**.
