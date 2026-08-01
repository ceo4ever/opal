# DONE: 코드 헤더 작성층 신설 — 인라인 + 외부 code-map 2소스

> 완료일: 2026-08-01 | 적용 스킬: opd (semi-agentic) | 태스크: 077

## 1. 무엇을 했나

`code-scan`이 `@header`를 **조회**만 하던 도구에서, **작성층**을 갖춘 도구가 됐다. 헤더를 소스 파일 안(인라인 주석)뿐 아니라 프로젝트 외부(`.opal/code-map/`)에도 기록할 수 있게 되어, 소스를 수정할 수 없거나 수정 부담이 과도한 코드베이스도 자산화 경로가 생겼다.

프레임워크에서 유일하게 도구 없이 "워커의 손"에만 맡겨져 있던 칸(`header-rules.md` §8 "별도 도구 없음")이 채워졌다.

## 2. 완료 산출물

**신규 3**

| 파일 | 역할 |
|------|------|
| `opal/tools/code-scan/run.sh` | 래퍼 — 도구 12종 공통 규약 준수(기존 code-scan만 누락돼 `tool-scan usage`가 실패하던 상태 해소) |
| `opal/tools/code-scan/code-map-hook.js` | PostToolUse hook — 기록 위치 미갱신 감지, 조기 이탈 9단 fail-safe |
| `opal/tools/code-scan/tests/` | 테스트 8파일(100 케이스) + 픽스처 8트리 + 골든 8 |

**수정 12** — `code-scan.js`(v1.2.0 → **v1.3.3**) · `tool-scan/manifest.json` · `claude-hooks.json` · `install-mac.sh` · `.gitignore` · 규칙 문서 7종(`header-standard`·`header-rules`·`code-scan-management`·`pm-review-gate`·`tools`·`opal-harness` §9·`brain-tool/README`) · `docs/` 3종(CONVENTIONS·ARCHITECTURE·PROJECT)

**신규 설정** — `.opal/code-scan.json`(scopes 3종·exclude 15종, gitignore 대상)

## 3. 핵심 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | 디렉토리(패키지) 단위 미러 1파일 — 파일별 사이드카 기각 | 파일 수의 1/5~1/15로 수렴, 점진 도입 경계가 트리로 드러남 |
| 2 | 5단 상속(인라인 → files → package → layerRules → domains), 인라인은 **파일 단독 승리** | 필드 병합은 출처 추적을 불가능하게 함 |
| 3 | 기록 위치 **4단 자동 판정**(`target`) — 사람·워커가 선택하지 않음 | 워커마다 다르게 기록하면 진실이 이중화됨 |
| 4 | `exports` **생성=워커 / 검증=도구** | 문법 파서 도입은 무의존 원칙 파기. 반면 "텍스트에 존재하는가"는 문법 지식 없이 검증 가능 — 생성의 어려움과 검증의 쉬움이 비대칭 |
| 5 | `scaffold --inline` **미채택** | 도구가 소스 파일에 주석을 삽입하는 위험 대비 이득이 목표 밖 |
| 6 | CLOSE 게이트는 **회귀만 차단** — `newly_uncovered` 0건, `pre_existing`은 비차단 보고 | 게이트 목적은 회귀 방지이지 레거시 소급 부여가 아님. 이 저장소 기준선이 `missing` 231건이라 전량 차단 시 모든 태스크가 막힘 |

## 4. QA 결과

| 검증 | 결과 |
|------|------|
| 테스트 | **100/100 pass, exit 0** (RED 시작점 17 pass → 최종 100) |
| 8커맨드 골든 회귀 | **바이트 동일** 18/18 — code-map 부재 프로젝트 동작 변화 0 (제약②) |
| 시나리오 | **All Pass** — S-25([SUPERVISOR]) 제외 24건 |
| 목표-커버 게이트 | coverage-check exit 0 + 평가자 `verdict: pass`(①목표 2 / ⑤채택 1 / ⑥경계 2, 평균 1.67) |
| 자기 게이트 | **exit 0** — 이 태스크의 변경 파일에 `validate --changed` 적용 시 `newly_uncovered` 0 · `worker_scope_violation` 0 |
| 컨벤션 진단 | Critical 0 / High 0 / Medium 0 · Low 3건 정리 완료 |
| 배포본 | `run.sh --help` exit 0 · `tool-scan usage code-scan` **`ok: true`**(기존 `help_exec_failed` 해소) · `node_missing` 폴백 · hook 배선 확인 |

## 5. dogfooding이 잡은 실제 결함 5건

시나리오가 형식적 통과용이 아니었음을 보여주는 기록.

| # | 결함 | 발견 경로 |
|---|------|----------|
| 1 | **게이트 과차단** — 레거시 미커버가 모든 태스크의 CLOSE를 막음 | Step 19 dogfooding ④ (이 태스크가 만든 게이트가 이 태스크를 막았다) |
| 2 | `--changed`가 `exclude`를 적용하지 않음 | PM이 전체 변경 파일로 재실행 |
| 3 | **산문 `@header` 오탐** — 문서 본문의 설명을 헤더로 오인해 `scan` 출력이 오염 | 게이트 잔여 위반 추적 |
| 4 | macOS 심볼릭 링크 좌표계 불일치(`/tmp` ↔ `/private/tmp`) | TS-038 hook 테스트 |
| 5 | **필터 비대칭** — `scaffold`가 제외한 파일을 `validate`가 위반으로 잡음 | 외부 프로젝트 실사용 (추가작업으로 처리) |

## 6. 잔여 미해결 (Known Issue)

| # | 항목 | 상태 |
|---|------|------|
| 1 | **S-25 hook 실세션 발동** | 캡틴 수동 확인 대기. hook 스크립트 자체는 자동 테스트 7건 + 실측 통과. 미확인은 "세션 런타임이 `Edit\|Write\|MultiEdit` matcher로 hook을 호출하는지"뿐. 미발동 시 폴백 = matcher 3엔트리 분리 등록 |
| 2 | install 스크립트 완주 | 대화형 프롬프트(계정 확인·메뉴 선택)에서 정지 → 자동 실행 불가. 산출물 배포·검증 4종은 완료. 확실히 하려면 사용자가 1회 직접 실행 |

## 7. 후속 태스크 (080로 이관)

**아래 결정은 전부 이 태스크의 테스트 과정에서 도출됐다.** 계약을 변경하는 성격이라 077 안에서 처리하지 않고 별도 태스크로 넘긴다 — 077은 "약속을 지켰는가", 080는 "약속을 바꾼다".

| # | 이관 결정 |
|---|----------|
| D-1 | 도구는 비대화형 유지 + `--header-source` 플래그. 최초 설정을 묻는 주체는 **PM(역할명 — 개인 식별자 기재 금지)** |
| D-2 | `readonly` **제거** → `headerSource`(전역 + 스코프별 오버라이드)로 통합. 기존 값은 `manifest` 동의어로 하위호환 후 deprecated |
| D-3 | `auto` **완전 제거** → `inline` / `manifest` 2택 |
| D-4 | 미설정 = **에러 거부**(`header_source_unset`) |
| D-5 | 차단 범위 = **code-scan 전 명령** |
| 개선 A | `scopes` 객체 형식 + `include`/`exclude` — 혼재 디렉토리 지원. 보강 5건(단일 `isInScope` 계약 / 검출기까지 필터 적용 / 스코프 중복 우선순위 / `dir` 부분집합 의미 명시 / `discover`는 include 추론 불가) |

**동반 필수 작업** — 전 명령 차단은 소비자를 함께 멈추므로 080에 반드시 포함한다: ① 이 저장소에 `headerSource: inline` 설정 ② 에러 메시지 품질(코드 + 해결 1줄) ③ `brain-tool sync-header` 대응 ④ `pm-review-gate.md` 8번 절차 보강 ⑤ hook은 미설정에서도 조용히 exit 0(fail-safe 유지)

**그 외 후속 후보** — `.md` 메타 규약 충돌(frontmatter ↔ `@header`) / 대형 레포 자산화 파일럿 / `feature` 태그 실채우기

## 8. 산출물 경로

`tasks/077-260727-opd-코드맵-헤더작성층/` — TASK.md · ANALYSIS.md · PLAN.md(1,790줄) · TEST-SCENARIO.md(25) · SCENARIO-GATE-1.md · TEST.md · GC-CONVENTION-*.md · RED-EVIDENCE 1~5 · AGENTIC-LOG.md · STATE.md · DONE.md
