# DONE: html-mockup 일반 스킬 신규 개발

> 완료일시: 2026-04-30 13:14 | 태스크: 132 | 적용 스킬: opp | 모드: interactive
>
> ※ 태스크 번호 변경 이력: 채번 시점(MEMORY.md `last_task_number: 130` +1) **131**로 시작했으나, 작업 중 브랜치(`opal-v2-260427`)에 이미 `feat(131): Python 오케스트레이터 런타임 도입` 커밋이 존재 — **132로 재번호**(2026-04-30 13:25, 캡틴 승인). 폴더명·MEMORY·TASK·DONE 모두 132로 정합. PLAN.md 안의 `PLAN.md:NNN` 줄번호 인용은 본 PLAN.md 자체의 줄 위치라 변경하지 않음.

---

## 1. 태스크 요약

태스크 진행 중 또는 일반 작업 중에도 호출 가능한 **일반 스킬 `html-mockup`** 신규 개발. 컨텍스트(태스크 폴더 자동 감지 + TASK/ANALYSIS/PLAN/PROJECT 흡수)와 7단계 인터뷰를 결합하여 **CDN 기반 정적 HTML 화면**을 빠르게 생성한다. 기본 스택: Tailwind + DaisyUI + Alpine.js + Lucide + Pretendard. 빌드 0, 외부 자원 분리(`shared/`)로 토큰 절약.

---

## 2. 수행 내용 (R-1 ~ R-19)

### 스킬 정의 / 호출 인프라 (R-1, R-8, R-10)

- `skills/html-mockup/SKILL.md` 신규 — YAML frontmatter + §0~§10 + 부속 A/B/C
- `opal-skills-registry.json` `groups.standalone`에 `html-mockup` 항목 추가 (name + alias `mockup` + triggers 3 + paths 2)
- `//html-mockup` / `//mockup` 양쪽 호출 + 자연어 자동 매칭(목업/모크업/HTML 화면 만들/HTML 목업)

### 컨텍스트 자동 흡수 / 인터뷰 (R-2, R-3, R-19)

- 환경 감지 — cwd `.opal/AGENT.md` / `tasks/{NNN}-*/TASK.md` / 비-OPAL 3분기
- 감지 결과별 자원 흡수 (TASK·ANALYSIS·PLAN·PROJECT)
- 7단계 인터뷰 — 저장 위치(필수) + 화면/액션/분리 모드/UI 라이브러리/다크모드/입력 자원
- 컨텍스트 추론 가능 단계는 1줄 통지 후 스킵

### 산출물 구조 / 외부 분리 (R-4)

- 트리: `{저장 위치}/shared/{style.css, main.js, nav.html(선택)}` + `{화면명}.html` × N
- 외부 분리 원칙으로 토큰 절약. 화면 HTML은 본문 마크업만

### 기술 스택 / CDN 핀 (R-5, R-14)

- Tailwind CDN(latest), DaisyUI(`@4` 핀), Alpine.js(`@3` 핀), Lucide(latest), Pretendard(`@v1.3.9` 핀)
- 대안: Flowbite / 없음(Tailwind만)

### 다중 화면 / 인덱스 (R-6, R-13)

- 화면 1개 → 단일 파일 / 화면 2개+ → `index.html` 자동 생성 (DaisyUI card 그리드 + Lucide 아이콘)
- 화면 간 상대 링크 자동 연결

### 보일러플레이트 / 파일명 / 디자인 (R-7, R-11, R-12, R-15)

- 보일러플레이트 4종 토큰: `{{TITLE}}`, `{{BODY}}`, `{{NAV}}`, `{{EXTRA_HEAD}}`
- 화면명 변환 — AI 의미 기반 영문 제안 + 사용자 확인 (Hangul Romanization 미사용)
- 반응형 ON / 다크모드 OFF 기본

### 에러 처리 / 입력 자원 / 보고 (R-16, R-17, R-18)

- 에러 5종 케이스 표 + AskUserQuestion 템플릿 3건
- 입력 자원 4종(이미지/Figma URL/참고 사이트/텍스트) 처리 가이드
- 보고 형식 3분기(단일/다중/수정)

### 배포 동기화 / 반복 수정 (R-9, R-7 반복 수정 부분)

- `install-mac.sh`는 `skills/` 일괄 복사 패턴 — 변경 불필요 (M-2 결론)
- 반복 수정 시 같은 파일 덮어쓰기, CHANGELOG 미생성

---

## 3. 변경 파일 (6개 — 신규 5 + 수정 1)

| # | 파일 | 종류 | 크기/변경 |
|---|------|------|---------|
| 1 | `skills/html-mockup/SKILL.md` | 신규 | 15,981 bytes |
| 2 | `skills/html-mockup/templates/boilerplate.html` | 신규 | 1,463 bytes |
| 3 | `skills/html-mockup/templates/shared/style.css` | 신규 | 1,463 bytes |
| 4 | `skills/html-mockup/templates/shared/main.js` | 신규 | 833 bytes |
| 5 | `skills/html-mockup/templates/index.html.tmpl` | 신규 | 2,513 bytes |
| 6 | `opal/core/references/opal-skills-registry.json` | 수정 | `groups.standalone` 배열 끝에 1항목 추가 |

---

## 4. 산출물

| 파일 | 내용 |
|------|------|
| `TASK.md` | 작업 목표 + 배경 분석 + 17개 확정 설계 방향 + 19개 요구사항(R-1~R-19) + 4개 미확정(M-1~M-4) + 8개 검증 시나리오(V-1~V-8) + 3개 out-of-scope |
| `PLAN.md` | §1 현황 조사(D-1~D-19, B-1 trigger 충돌 매트릭스) + §2 핵심 설계(N-1~N-5, M-1, 부속 (a)~(f)) + §3 7 Step 체크리스트 + changed_files 6개 + §4 QA 체크리스트 + §5 리스크 7건 |
| `QA-PLAN.md` | 1차 검증 Pass(Warning 2) + 보강 검증(R-1~R-13, Warning 2 추가) + §6 PM 처리 노트(R-2 수정·R-7 false-positive) → Pass 회복 |
| `QA-EXECUTE.md` | EXECUTE 검증 **Pass** (Critical 0 / Warning 0 / Info 2) — 6개 산출물 + GE-1~GE-3 + E-1~E-12 모두 Pass |
| `STATE.md` | 20행 파이프라인 현황판 + 의사결정 로그 23건 |
| `DONE.md` | 본 문서 |

---

## 5. 성공 기준 달성 (TASK §요구사항 R-1 ~ R-19)

R-1 ~ R-19 모두 [x] (1차 QA에서 갱신, EXECUTE QA에서 재검증 — `TASK.md:227 이하`).

---

## 6. 회귀/안전망 검증 결과

| 항목 | 결과 |
|------|------|
| 기존 6개 standalone 스킬과 name/alias 충돌 | 없음 |
| trigger 정규식 충돌 | 없음 |
| 의미 영역 모호성 (목업 vs 프로토타입) | SKILL.md description 분기 안내로 해소 |
| 기존 6개 standalone 항목 보존 | ✅ (api-analyzer/interview/wireframe-builder/ui-designer/web-to-markdown/erd-modeler 모두 원본 유지) |
| @apply 미사용 (Tailwind Play CDN 외부 파일) | ✅ (R-2 PM 처리 결과) |
| DaisyUI v4 `tabs-boxed` 클래스 | ✅ (공식 문서 확인 — 정확) |

---

## 7. 게이트 / QA 요약

| 단계 | QA Gate | State Gate | PM Gate | 사용자 확인 |
|------|--------|---------|--------|-----------|
| TASK | (없음) | ✅ | (없음) | ✅ (보강 13항목 추가 후) |
| PLAN | ✅ Pass + 재소환 Pass(PM 처리) | ✅ ×2 | ✅ ×2 | ✅ |
| EXECUTE | ✅ Pass | ✅ ×2 | ✅ | ✅ ("확인") |
| CLOSE | (없음) | ✅ | (없음) | (CLOSE 진입 게이트로 흡수) |

---

## 8. 특이사항 / 후속 조치

- **배포 미수행**: `~/.opal/skills/`로의 배포는 본 태스크 범위 밖. 캡틴 명시 지시(`./scripts/install-mac.sh` 실행) 시에만 수행 (개발/배포 경계 원칙, AGENT.md §금지사항).
- **호출 가능 시점**: 배포 후. install-mac.sh가 `skills/` 일괄 복사 패턴이라 추가 작업 없이 자동 포함.
- **검증 명령** (배포 후 실행 권장):
  ```bash
  node ~/.opal/tools/skill-registry/skill-registry.js validate
  node ~/.opal/tools/skill-registry/skill-registry.js match "html-mockup"
  node ~/.opal/tools/skill-registry/skill-registry.js match "mockup"
  ```
- **커밋**: 미수행. 캡틴 명시 요청 시 별도 수행.
- **127번 태스크**: TASK 단계 진행 중 상태 유지 (본 태스크와 독립).

---

## 9. 의사결정 타임라인 (요약)

대화 기반 설계 17개 확정 항목 + 캡틴 보강 요청 13개 항목 + QA 재소환 후 PM 처리 2건 = 총 32개의 명시적 의사결정으로 구성. 상세는 `STATE.md §의사결정 로그` 참조.

주요 분기점:
1. **A+B+C 13개 보강 (캡틴 요청)** — EXECUTE 일관성 / 회귀 안전망 / 절차 정밀도 강화 (시드 코드, 인터뷰 템플릿, 매칭 케이스 등)
2. **R-2 (style.css `@apply`) PM 수정** — Tailwind Play CDN 공식 문서 확인 후 일반 CSS로 대체
3. **R-7 (`tabs-boxed`) PM false-positive 확인** — DaisyUI v4 공식 문서 직접 확인
