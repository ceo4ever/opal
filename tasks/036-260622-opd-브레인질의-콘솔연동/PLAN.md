# PLAN: OPAL Console 프로젝트 브레인 질의 메뉴 (아키텍처 B — 스파이크 학습·캡틴 확정 반영본)

> 작성일: 2026-06-22 | 개정: 2026-06-22 (Phase 1 스파이크 완료 + 캡틴 확정 결정 DECISION#22~25 반영)
> 입력: TASK.md (SSOT, 최신 정정본 — §확정방향1~6·명확화표), AGENTIC-LOG.md (GATE/DECISION 19~25 = 스파이크 결과·확정), TEST-SCENARIO.md (S-4·warm probe 결과)
> 모드: Multi-Feature (기능 7개, Framework+FE+BE 영역 분할) | 실행 모드: 복잡 (Step 16개, 변경 파일 11개, Framework/FE/BE 다중 레이어, 외부 도구 `claude` CLI + 관리형 지속 세션 + localStorage 이력)

> **[개정 사유 — 스파이크 학습 + 캡틴 확정]** 본 개정은 Phase 1 스파이크(F-000) **완료** 후 캡틴이 확정한 6개 결정(AGENTIC-LOG DECISION#20~25)을 반영한다.
> 1. **이 레포가 OPAL 원천** (DECISION#25). opbr `--read-only` 계약 추가는 별도 작업이 아니라 **036 안에서 소스(`opal/skills/opal-brain/SKILL.md`)를 직접 수정**한다. dashboard/(콘솔) + opal/skills/opal-brain/(opbr) **동시 수정** → CLOSE에서 install 재배포 **1회**(캡틴 L3)로 발효. 배포 경계 유지(`opal/` 소스만, `~/.opal` 직접편집 0).
> 2. **opbr 호출 = `//opbr query --read-only "<질의>"`** (DECISION#23). 기존 `//opbr ask`(대화형)는 폐기. `ask`=대화형(사용자가 페이지 선택), `query`=비대화형(자동 선별).
> 3. **세션 = B1 확정** (DECISION#22, B2 기각). 일회성 `claude -p` + 디스크 세션 `--session-id`(콜드 프라임)→`--resume`(웜). **실측: 콜드 90.8s / 웜 20.2s(78%↓)** — 콜드 100s는 웹 UI에 과대 → 지속 세션 필수 확정. prime-on-intent(브레인 메뉴 진입 시 백그라운드 프라임).
> 4. **backend 무상태/read-only** (DECISION#24). 질의 API는 `{answer, citations}`만 반환, **영속 저장 없음(SQLite 폐기)**.
> 5. **이력 = 브라우저 localStorage** (DECISION#24, FE). Q&A 스레드를 클라이언트 저장 → 표시·재질문(resume via session_id)·"새 대화"(새 세션). 질의 로그=각자 브라우저.
> - **[MUST] 금지**: `--safe-mode`(=opbr·CLAUDE.md 미로드)·`--bare`·anthropic SDK·`ANTHROPIC_API_KEY`·`ANTHROPIC_AUTH_TOKEN`·`ant auth login`·`~/.config/anthropic` 절대 금지 (구독 keychain 인증 유지).
> - **[폐기]** 직전 아키텍처 A(`--safe-mode --system-prompt` 중립 합성, backend 재구현) 전면 폐기. ANALYSIS §4·§5(Anthropic SDK / API 키 / ant OAuth) 무효, §1·§2·§3·§6·§7(변경지점·CORS·brain 흐름·리스크·인용)은 유효 인용.

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

읽기전용 OPAL Console(현 5개 메뉴, HTTP GET-only, LLM 호출 전무)에 6번째 메뉴 "프로젝트 브레인"을 신설한다. 웹 화면에서 brain 지식을 질의하면, backend가 **로컬 `claude` CLI 서브프로세스(사용자 Claude 구독)** 로 **`//opbr query --read-only "<질의>"`** 를 구동한다(DECISION#23 — `ask`=대화형 폐기, `query`=비대화형 자동선별). OPAL 프레임워크·opbr 스킬이 로드되어 실제 brain query(term-우선·자동 top-N 선별·페이지 Read·**항상 최종답변 합성**·인용)를 수행하고, opbr는 **JSON 코드펜스 하나**(`{"answer","citations":[{page,title,type}]}`)로 출력한다. backend는 `claude --output-format json` → `result`에서 그 JSON 펜스를 추출해 `{answer, citations[]}`로 정규화·반환한다(무상태, 영속 저장 없음 — DECISION#24). POST·LLM 호출 능력은 brain 라우터 하나에만 격리하고, 기존 5라우터의 GET·read-only 불변성을 코드로 보증한다.

**아키텍처 B 핵심 원칙**: backend는 brain 검색/페이지 읽기/인용/합성을 **재구현하지 않는다**. opbr 스킬이 SSOT로 전담하며 backend는 질의 전달 + opbr JSON 출력 추출 + 응답만 수행하는 얇은 프록시다(DRY). **backend·brain 완전 무상태/read-only** — 질의 결과는 영속 저장하지 않는다(SQLite 폐기, DECISION#24).

**[원천 변경] opbr `--read-only` 계약 추가 (DECISION#23·#25, → D-11)**: 이 레포가 OPAL 원천이므로 opbr 호출 계약 자체를 **소스(`opal/skills/opal-brain/SKILL.md` §STEP query)에서** 신설한다. `//opbr query --read-only "<질의>"`는 다음을 보장한다:
- **자동 선별 top-N**(기본 3) — 후보 목록에서 멈추지 않고 LLM이 자동으로 상위 페이지를 선택.
- **항상 최종답변 합성** — 후보 목록·검색 결과에서 멈춤 금지(스파이크 학습 DECISION#22: 웜 출력이 후보목록 형태로 멈추는 경우 발견 → 합성 강제).
- **순수 read-only** — 진입점③ draft term 제안·STEP5 synthesis 페이지 파일링·query log 기록을 **전부 생략**(brain 쓰기·제안 0건).
- **출력 = JSON 코드펜스 하나** — `{"answer":"...","citations":[{"page","title","type"}]}`. 부트스트랩 preamble이 앞에 붙어도 backend가 JSON 펜스만 발췌(견고).
- `//opbr ask` 대화형 분기는 **불변**. SKILL.md 변경이력 행 추가(036) + version bump(v1.3→v1.4).

**세션 모델 (관리형 지속 세션 — B1 확정, DECISION#22, → D-0)**: 데몬이 `BrainSession`을 관리한다.
- **B1 확정 (B2 기각)**: 일회성 `claude -p "//opbr query --read-only <질의>" --session-id <uuid> --output-format json`(콜드 프라임) + 이후 `--resume <uuid>`(웜 재개). **실측: 콜드 90.8s / 웜 20.2s(78%↓, AGENTIC-LOG#21)**. 웜 20.2s의 대부분은 opbr 검색+합성(불가역) — 프로세스 재기동 오버헤드 미미 → B2 상주 프로세스(stream-json) 이득 작음 대비 복잡도↑ 이유로 기각(DECISION#22). 디스크 세션 resume가 부트스트랩을 건너뜀이 실증됨(부트스트랩 노이즈 제거·멀티턴 맥락 유지).
- **prime-on-intent (DECISION#22)**: 브레인 메뉴 **진입 시** 백그라운드로 90s 콜드 프라임을 선행 → 사용자가 첫 질의를 칠 무렵 세션 웜화 → 체감 질의 지연 20s. `POST /api/brain/prime`(백그라운드 프라임 트리거).
- **5트리거 리셋**: ⓐ 서버 재실행 ⓑ 컨텍스트 임계(누적 턴/토큰 추정 초과) ⓒ 유휴 타임아웃 ⓓ 크래시(resume/프로세스 실패) ⓔ 수동 "새 대화"(FE). 리셋 = 세션 폐기 후 다음 질의/프라임이 재프라임.
- 단일 세션 → 동시 질의 **`threading.Lock` 직렬화**(로컬 단일 사용자). 크래시 시 **투명 재프라임**(resume 실패→새 session-id 콜드 1회 재시도).
- **출력 파싱**: `claude --output-format json` → `result` → opbr가 낸 JSON 펜스 추출 → `{answer, citations}`. 콜드에 부트스트랩 preamble이 섞여도 JSON 펜스만 발췌(견고 — 스파이크 출력오염 학습 DECISION#20).

**headless opbr 읽기전용 가드 (TASK §확정방향4·§제약③, → D-0)**: 일반 opbr query는 synthesis 페이지 파일링·draft term 등록을 *제안*할 수 있으나(`opal-brain` SKILL.md L292 진입점③, → D-11), **`--read-only` 계약이 이를 원천 차단**한다(brain 쓰기·제안 0). 추가로 콘솔 호출 프롬프트에 쓰기 금지 지시를 포함하고, 질의 전후 `.opal/brain` 파일 불변을 테스트로 검증(S-4 캡틴 검증서 read-only PASS — log.md조차 미기록, AGENTIC-LOG#19).

**이력 = 브라우저 localStorage (DECISION#24, FE)**: backend·brain 무상태이므로 Q&A 스레드 `{session_id, turns:[{q,a,citations}]}`를 **클라이언트(localStorage)** 에 저장한다. 화면에서 이력 표시·재질문(resume via session_id)·"새 대화"(새 세션 생성=트리거ⓔ)를 수행한다. 질의 로그도 각자 브라우저에 남는다(서버 로그 0).

**단계화 (TASK §확정방향6, → D-0)**:
- **Phase 1 (스파이크 — 캡틴 검증 게이트) = 완료**: 최소 BE(`opbr_adapter` + 최소 라우터 + `main.py`). L1 18 PASS + 기존 110 PASS(회귀 0) + 실 claude 0회. **S-4 캡틴 검증 PASS**(구독 작동·OPAL/opbr 실로딩·brain 근거 답변·read-only). warm probe로 콜드/웜 실측 → **B1 확정**. (AGENTIC-LOG#17·19·21·22)
- **Phase 2+ (나머지) — 재설계**: ① opbr 원천 `--read-only` 계약 추가(Framework) ② BE 세션 어댑터 강화(`//opbr query --read-only` + JSON펜스 추출 + `BrainSession`: prime-on-intent·resume·5트리거 리셋·Lock·크래시 재프라임 + `POST /query`·`POST /prime`·`GET /auth`) ③ FE 메뉴/라우트 + BrainPage(인증분기·진입 시 prime 호출·질의→답변+인용·localStorage 이력 저장/표시/재질문·"새 대화") ④ 격리 하드닝 + RED-first 테스트(mock) 갱신 + docs(ARCHITECTURE/PROJECT, opbr SKILL 변경이력).

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-000 | **[완료] 스파이크: BrainSession 콜드프라임 + `//opbr` 질의→답변 E2E (콜드/웜 지연 실측·B1 확정·read-only 검증)** | R3(핵심), R2(경량) | P0 | 없음 |
| F-006 | **[원천 변경] opbr `--read-only` 계약 추가** (`opal/skills/opal-brain/SKILL.md` §STEP query — 자동 top-N·항상 최종답변 합성·순수 read-only·JSON펜스 출력 + 변경이력·version bump) | R3(전제) | P0 | 없음 |
| F-001 | 읽기전용 격리 경계 (CORS POST 완화 + 기존 5라우터 GET-only 보존 + host 127.0.0.1) | R5 | P0 | F-000 |
| F-002 | BE 인증 상태 API (`GET /api/brain/auth` — `claude` CLI 가용·인증 여부) | R2 | P0 | F-000, F-001 |
| F-003 | BE 질의 API + 관리형 세션 (`POST /api/brain/query`·`POST /api/brain/prime` — BrainSession prime-on-intent·B1 resume·5트리거 리셋·Lock·크래시 재프라임·`//opbr query --read-only` 구동·JSON펜스 추출→answer+citations) + 읽기전용 가드 | R3 | P0 | F-000, F-006, F-001, F-002 |
| F-004 | FE 메뉴/라우트 (6번째 네비 "프로젝트 브레인" + `/brain` 라우트) | R1 | P0 | 없음 |
| F-005 | FE 질의 UI (BrainPage — 인증 분기 + 진입 시 prime 호출 + 질문 입력 → 답변+인용 렌더 + **localStorage 이력 저장/표시/재질문·"새 대화"**) | R4 | P0 | F-002, F-003, F-004 |

### 1.3 기능 의존 그래프 (ASCII)

```
[Phase 1 — 스파이크 게이트 = 완료]
F-000 (스파이크: 콜드프라임·//opbr·콜드/웜 실측·B1 확정·read-only) ✅ S-4 캡틴 검증 PASS
   │  └─ 게이트 통과 → Phase 2+ 진입 + 스파이크 학습(B1·콜드90.8s/웜20.2s·출력오염·후보목록멈춤) 반영
   ▼
[Phase 2+ — 나머지 (재설계)]
F-006 (opbr --read-only 원천 계약) ─── F-003 전제 (호출 계약 정의)
                                          │
F-001 (격리 경계) ─┬─ F-002 (auth API) ──┤
                   │                       ├─ F-003 (query+prime API + 세션·가드·JSON펜스) ─┐
                   └───────────────────────┘                                               │
                                                                                          ├─ F-005 (질의 UI + localStorage)
F-004 (FE 메뉴/라우트) ──────────────────────────────────────────────────────────────────────┘
```

> F-000(스파이크)은 **완료** — B1 확정·콜드/웜 지연·read-only·출력오염을 실측으로 확정했고, F-003의 세션·파싱 설계가 그 학습에 의존한다. **F-006(opbr 원천 계약)**은 F-003의 호출 계약(`//opbr query --read-only`)을 정의하는 전제로, dashboard와 **동시 수정**되어 CLOSE 1회 install 재배포로 함께 발효(DECISION#25). F-001은 BE의 모든 brain 엔드포인트 선행(POST preflight + 격리). F-004(FE 셸/라우트)는 BE와 독립이므로 BE와 병렬 가능. F-005(질의 UI + localStorage)는 BE 계약(F-002·F-003) + FE 라우트(F-004)에 모두 의존.

---

## 리스크 가설 표 (아키텍처 B 기준 재작성)

> PLAN 단계에서 작성. TEST-SCENARIO.md §1의 입력이 됨.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-006/F-003 **opbr 쓰기 누수** — query가 synthesis 파일링·draft term 등록·query log를 *제안→실행* (opbr SKILL §query 진입점③, → D-11). **`--read-only` 계약이 원천 차단**(F-006)하나 계약 누락·미적용 시 누수 | P0 | L1(F-006 SKILL 계약 문서 검증 + 호출 프롬프트에 read-only/쓰기금지 단언, mock) + L3(질의 전후 `.opal/brain` 해시 불변 — 캡틴, S-4서 PASS 실증) | S 후보: 질의 1건 후 brain 디렉토리 변경 0건 (S-4 PASS) |
| H-2 | F-003 **세션 성장/리셋** — 누적 턴/토큰이 컨텍스트 임계 초과 시 답변 품질 저하·실패 | P1 | L1(임계 추정·리셋 트리거 단위, mock) + L3(연속 질의 N회 후 리셋 발동 — 캡틴) | S 후보: 임계 초과 시 세션 폐기→재프라임 |
| H-3 | F-003 **동시성** — 단일 세션에 동시 질의/prime 도달 시 resume 충돌/세션 손상 | P0 | L1(`threading.Lock` 직렬화 단위 — 두 번째 요청 대기) | S 후보: 동시 2질의 → 직렬 처리, 세션 1개 유지 |
| H-4 | F-000/F-003 **크래시 재프라임** — `--resume` 실패(세션 만료/프로세스 죽음) 시 무한 실패 | P0 | L1(resume 실패 mock → 새 session-id 콜드 재프라임 1회 fallback) + L3(세션 파일 삭제 후 질의 — 캡틴) | S 후보: resume 실패→투명 재프라임 후 답변 |
| H-5 | F-000/F-003 **부트스트랩 지연** — 콜드 프라임(OPAL+opbr 로딩) 수십초 → UX 대기·timeout. **실측 콜드 90.8s/웜 20.2s** → **prime-on-intent로 콜드를 메뉴 진입 시 선흡수**, 질의는 웜(20s) | P1(완화됨) | L1(콜드180/웜60 timeout 검증 + prime 엔드포인트 비동기 단위) + **L3 실측 완료(콜드90.8s/웜20.2s, AGENTIC-LOG#21)** | S 후보: prime-on-intent 백그라운드 프라임 → 질의 시 웜 |
| H-5b | **F-003 prime-on-intent 경합** — 진입 prime이 아직 콜드 진행 중일 때 질의 도달 → Lock 대기/중복 콜드 프라임 | P1 | L1(prime 진행 중 플래그 + 질의가 진행 중 prime 완료를 대기, 중복 콜드 미발생 단위 mock) | S 후보: prime 진행 중 질의 → 중복 콜드 0, 완료 후 웜 응답 |
| H-6 | F-003 **출력 파싱(JSON펜스)** — `--output-format json`의 `result`에 opbr 답변. `result` 부재/`is_error:true`/비JSON/**JSON펜스 부재·preamble 오염**/citations 미파싱 시 빈 답변·500. (스파이크서 result에 부트스트랩 보고+PM preamble 혼입 실측 — AGENTIC-LOG#19) | P0 | L1(서브프로세스 mock: success/is_error/비JSON 3분기 + preamble 섞인 result서 JSON펜스만 발췌 + citations 파싱) | S 후보: result→JSON펜스 발췌→answer/citations, preamble 무시 |
| H-7 | F-002/F-003 **구독 keychain 인증** — `--bare`/`--safe-mode`/API 키 사용 시 구독 인증 파탄 또는 opbr 미로드 | P0 | L1(커맨드 배열 mock 캡처: `--safe-mode`·`--bare` 부재 단언) + L3(실 구독 답변 — 캡틴) | S 후보: 커맨드에 금지 플래그 0건 |
| H-8 | F-003 자동 테스트에서 실제 `claude` 호출 | 실 구독 토큰 소모 + 테스트 비결정성·지연 | P1 | L1(서브프로세스 **반드시 mock**; 실호출 금지) | S 후보: 단위테스트 0 토큰 소모 보증 |
| H-9 | F-001 `main.py` `allow_methods` POST 완화 → **읽기전용 경계 누수** (기존 5라우터에 POST 우발 등록) | P0 | L1(기존 5라우터 POST→405) + L3(실데몬 회귀) | S 후보: 5라우터 POST 405 / brain POST 200 |
| H-10 | F-002 `auth_adapter.check_auth()` — `claude` 미설치/미인증 시 graceful 안내 대신 500/예외 누수 | P1 | L1(`shutil.which` mock: 설치/미설치 분기) | S 후보: which=None → authenticated:false + 안내 |
| H-11 | F-003 brain 미초기화/검색0건 — opbr가 `brain_not_initialized` 또는 "관련 페이지 없음" 반환 시 미핸들 | P1 | L1(opbr 출력 mock: 미초기화 메시지) | S 후보: 미초기화 → graceful 안내 |
| H-12 | F-001/F-003 데몬 외부 노출 (127.0.0.1 바인딩 위반 → 외부에서 LLM POST 호출 = 구독 남용) | P0 | L1(host=127.0.0.1 단위) + L3(바인딩 회귀) | S 후보: uvicorn host 127.0.0.1 불변 |
| H-13 | F-003 셸 인젝션 — `<질문>`이 `//opbr query --read-only` 인자로 전달될 때 | P1 | L1(`subprocess.run(list, shell=False)` 단언) | S 후보: 인자 배열 전달, 셸 미경유 |
| H-14 | F-005 미인증 분기 렌더 — `authenticated:false`인데 질의 폼 노출 → 무의미 POST | P2 | L3(시각·E2E) | S 후보: 미인증 시 안내만, 폼 비노출 |
| H-15 | F-005 **localStorage 이력 정합** — Q&A 스레드 직렬화/역직렬화 깨짐·쿼터 초과·session_id↔turns 불일치 시 이력 손실·재질문 오작동 | P2 | L3(시각·E2E — 질의 후 새로고침 시 이력 유지·재질문 동일 session_id resume·"새 대화"로 새 세션) | S 후보: 질의→새로고침→이력 표시, 재질문 resume, 새 대화 새 세션 |
| H-16 | F-006 **opbr `--read-only` 계약 누락/오정의** — SKILL.md에 자동선별·항상합성·순수read-only·JSON펜스 중 일부 누락 시 콘솔 답변이 후보목록서 멈추거나(DECISION#22 학습) brain 쓰기 누수(H-1) | P0 | L1(SKILL.md 문서 검증 — 4계약 명시·`ask` 분기 불변·version bump·변경이력 행) — RED 불가(마크다운)→문서 검증 | S 후보: SKILL §query에 `--read-only` 4계약 전수 존재 |
| H-17 | F-006/F-003 **원천-콘솔 동시변경 발효 누락** — opbr SKILL 변경이 install 재배포 전엔 미발효 → 데몬이 구버전 opbr 호출(후보목록 멈춤/쓰기) | P1 | L1(콘솔은 `--read-only` 호출 일관 + CLOSE install 재배포 1회로 동시 발효 명시) + L3(재배포 후 통합 E2E — 캡틴) | S 후보: CLOSE install 재배포 후 query가 합성 답변+read-only |

**RED-first 트랙 적용 판정** (SSOT: `opal/core/references/harness/red-first.md` §1.5, → D-10):

| 영역 | 트랙 | 근거 |
|------|------|------|
| F-000 스파이크 **[완료]** | **RED-first 완화** | 스파이크는 실측·탐색이 목적(red-first.md §스파이크 예외). 커밋된 단위테스트는 서브프로세스 mock 유지(토큰 0 — H-8, 18 PASS). 검증 본체=캡틴 L3 SUPERVISOR(S-4 PASS) |
| F-006 opbr 원천 계약 | **RED 불가 → 문서 검증** | 스킬 마크다운 변경(`SKILL.md`)이므로 코드 RED 불가(red-first.md §1.5 적용 외). 검증=문서 정합(4계약·`ask` 분기 불변·version bump·변경이력 행) + 콘솔 호출 일관성 단위(F-003 RED서 `--read-only` 플래그 포함 단언) |
| F-001 격리 경계 | **RED-first 강제** | API 계약·인가 경계 (§1.5 "API 계약"·"인증·인가") |
| F-002 auth API | **RED-first 강제** | 인증 상태 판별 = 인가 (§1.5) — `shutil.which` mock 기반 RED |
| F-003 query+prime API + 세션·가드 | **RED-first 강제** | API 계약 + 세션 상태기계 + 비즈니스 로직(prime-on-intent·B1 resume·5트리거·Lock·크래시 재프라임·JSON펜스 추출). **[MUST] `claude`/`brain-tool` 서브프로세스 전부 mock** (H-8) — mock 기반 RED→GREEN |
| F-004 FE 메뉴/라우트 | 구현 후 시나리오 검증 | UI 화면·컴포넌트·라우트 등록 (§1.5 "UI 화면·컴포넌트") |
| F-005 FE 질의 UI + localStorage | 구현 후 시나리오 검증 | UI 화면 (§1.5). 인증 분기·localStorage 이력·재질문은 L3 시각 검증 |
| 실 구독 E2E (재배포 후 데몬→`//opbr query --read-only`→답변+인용) | **L3 `[SUPERVISOR]`** | 실 토큰 소모 — 캡틴 수동 검증 (red-first.md §4 공개 인터페이스 관측). CLOSE install 재배포 후 통합 |

> **[MUST]** RED 테스트 작성 주체(opal-test-agent, mode:red)는 EXECUTE 구현 워커와 분리한다 (red-first.md §2). GREEN 루핑 중 RED 테스트 파일 수정 금지 (§3).

---

## 2. 기능별 분석

### F-000: 스파이크 — BrainSession 콜드프라임 + `//opbr` E2E **[완료]**

#### 2.0.1 관련 파일 맵 (실제 산출)
| 영역 | 경로 | 역할 | 변경 유형 | 상태 |
|------|------|------|----------|------|
| BE | `dashboard/backend/adapters/opbr_adapter.py` | `claude -p` 서브프로세스 구동 + 세션 핸들(`--session-id`/`--resume`) + 출력 파싱 (스파이크 최소) | 신규 | 완료(119줄) |
| BE | `dashboard/backend/routers/brain.py` | `POST /api/brain/query` 최소 핸들러 (스파이크) | 신규 | 완료(117줄) |
| BE | `dashboard/backend/main.py` | brain 라우터 최소 등록 + `allow_methods` POST | 수정 | 완료 |
| BE | `dashboard/backend/tests/test_brain_spike.py` | 스파이크 단위테스트(mock, 실 claude 0회) | 신규 | 완료(263줄, 18 PASS) |

#### 2.0.2 현재 구현 (스파이크 완료)
`claude` 실측: `/Users/iskang/.local/bin/claude` v2.1.185, `shutil.which("claude")` 탐지 가능 (실측 2026-06-22). 인터프리터는 OPAL 공용 venv `~/.opal/.venv/bin/python3`(uvicorn0.42/fastapi0.137) — backend 소스 env엔 uvicorn 미설치, S-4는 TestClient 인프로세스 probe(재배포 불요, AGENTIC-LOG#18). `adapters/base.py:31 run_tool()`은 subprocess 공통 실행 제공이나 `claude` 출력은 `ok` 필드 없어 자체 `is_error` 판정 필요 → opbr_adapter는 자체 subprocess 호출 + JSON 파싱(timeout 별도).

**스파이크 실측 학습 (S-4 + warm probe, AGENTIC-LOG#19·21·22)**:
- ✅ 핵심 루프 성립 — 구독 작동·OPAL/opbr 실로딩·brain 근거 답변(`[[opal-first-use-guide]]` 인용)·read-only PASS(brain 0변경, log.md조차 미기록 = 가드 작동).
- ⚠️ **콜드 90.8s → 웜(resume) 20.2s(78%↓)** — 콜드 100s는 웹 UI에 과대 → **지속 세션 필수**. resume가 부트스트랩 건너뜀 실증(노이즈 제거·멀티턴 맥락 유지) → **B1 확정**(B2 기각, DECISION#22).
- ⚠️ **출력 오염** — `result`에 부트스트랩 보고+`📋 알투[PM]` preamble 혼입 → **프라임/질의 분리 + JSON펜스 추출** 필요(F-003·F-006 반영).
- ⚠️ **웜 출력이 후보목록 형태로 멈추는 경우** 발견 → **opbr에 항상 최종답변 합성 지시 보강** 필요(F-006 `--read-only` 계약으로 해결).

#### 2.0.3 영향 범위
- 스파이크 학습이 F-003(세션·timeout·JSON펜스 파싱)·F-006(`--read-only` 계약)의 설계를 확정 → F-000은 검증 게이트로서 **완료·통과**.
- 데몬은 사용자 권한 실행이므로 keychain 구독 인증 접근 가능. `--bare`/`--safe-mode` 사용 시 keychain 우회·opbr 미로드 → 인증 파탄/재구현(H-7).

---

### F-006: opbr `--read-only` 계약 추가 (원천 변경)

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| Framework | `opal/skills/opal-brain/SKILL.md` | §STEP query에 `--read-only` 비대화형 계약 추가 + version bump(v1.3→v1.4) + 변경이력 행(036) | 수정 |

#### 2.6.2 현재 구현
`opal/skills/opal-brain/SKILL.md` v1.3(2026-06-17). §모드 라우팅 L37: `//opbr ask "질문" / //opbr query` → STEP query. §STEP query(L274-296): "search는 후보 목록만 반환·선택 페이지만 주입", `//opbr ask` = 사용자가 직접 페이지 선택하는 **대화형 모드**(L280). 진입점③(L292-296): 미등록 업무 용어 발견 시 draft term 등록 **제안**(쓰기 가능 경로). 현재 **비대화형/자동선별/read-only 계약 부재** — 콘솔이 headless로 호출 시 후보목록서 멈추거나(스파이크 학습) draft 제안·synthesis 파일링으로 brain 쓰기 누수 가능(H-1).

#### 2.6.3 영향 범위
- 이 레포가 OPAL 원천(DECISION#25) → opbr 호출 계약은 별도 작업이 아니라 **036 소스 변경**으로 처리. dashboard(F-003)와 동시 수정 → CLOSE install 재배포 1회로 동시 발효.
- `//opbr ask` 대화형 분기는 **불변** — `--read-only`는 query 모드의 비대화형 하위 계약으로 추가(기존 사용처 회귀 0).
- F-003의 호출 계약(`//opbr query --read-only "<질의>"`)이 이 계약에 의존 → F-003 전제(H-16·H-17).

---

### F-001: 읽기전용 격리 경계

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/main.py` | FastAPI 앱·CORS·라우터 등록 | 수정 |
| BE | `dashboard/backend/tests/test_routers.py` | `test_no_brain_endpoints`(L258) — 현재 brain 부재 단언 | 수정 |
| BE | `dashboard/backend/tests/test_main.py` | CORS·host 바인딩 검증 | 수정 |

#### 2.1.2 현재 구현
`main.py:45` `allow_methods=["GET"]`로 전역 CORS 제한 (`(→ D-8 §main.py:45)`). 라우터 5개(`dashboard/projects/tasks/memory/doctor`) 모두 `@router.get`만 사용 (ANALYSIS §2 grep 0건 실증 — `(→ D-5 §2)`). `main.py:101` uvicorn `host="127.0.0.1"` 고정 (H-12). `main.py:8` `@header.depends`에 5라우터 명시 → `routers.brain` 추가 필요. 기존 테스트 `test_no_brain_endpoints`(`test_routers.py:258-264`, → D-9)는 `/api/brain` 404 단언 → brain 신설 시 갱신 필요.

#### 2.1.3 영향 범위
- CORS 미들웨어는 앱 전역 적용 → `allow_methods`는 브라우저 preflight(OPTIONS)만 제어. 실제 POST 가능 여부는 라우터에 POST 핸들러 등록 여부로 결정 (ANALYSIS §2 — `(→ D-5 §2)`).
- 기존 5라우터에 POST 핸들러를 추가하지 않으면 CORS 완화 후에도 405 유지 → 실질 read-only 보존.

---

### F-002: BE 인증 상태 API

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/brain.py` | `GET /api/brain/auth` 핸들러 | 수정 (F-000 신규 파일에 추가) |
| BE | `dashboard/backend/adapters/auth_adapter.py` | `claude` CLI 가용·인증 여부 경량 체크 | 신규 |
| BE | `dashboard/backend/models.py` | `BrainAuthResponse` 스키마 | 수정 |

#### 2.2.2 현재 구현
인증 관련 코드 전무. `claude` 실측 `shutil.which("claude")` 탐지 가능. 어댑터 계층 격리(PROJECT.md §3 플랫폼 독립성 — `(→ D-2 §원칙3)`)로 `claude` 탐지 로직을 `auth_adapter`에 캡슐화하여 라우터는 플랫폼 독립.

#### 2.2.3 영향 범위
- `GET /api/brain/auth`는 FE BrainPage 렌더 시 자주 호출(TanStack Query) → 네트워크/토큰 비용 없는 경량 체크가 UX·비용 측면 유리. 실 유효성은 `POST /api/brain/query`의 `is_error` 캐치로 자연 검증.

---

### F-003: BE 질의+프라임 API + 관리형 세션 (B1·prime-on-intent)

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| BE | `dashboard/backend/routers/brain.py` | `POST /api/brain/query` + `POST /api/brain/prime` 핸들러 (세션 오케스트레이션) | 수정 (F-000/F-002 신규 파일에 추가) |
| BE | `dashboard/backend/adapters/opbr_adapter.py` | `BrainSession` 상태기계(prime-on-intent·B1 resume·5트리거 리셋·Lock·크래시 재프라임) + `//opbr query --read-only` 구동 + **JSON펜스 추출** + 읽기전용 가드 | 수정 (F-000 스파이크본 `//opbr ask` → 교체·하드닝) |
| BE | `dashboard/backend/models.py` | `BrainQueryRequest`/`BrainQueryResponse`/`CitationItem`/`BrainPrimeResponse` 스키마 | 수정 (F-002와 동일 파일) |

#### 2.3.2 현재 구현
`//opbr query --read-only`(F-006 신설 계약)가 opbr를 비대화형 자동 read-only로 구동 — 후보에서 자동 top-N 선별 → Read → **항상 최종답변 합성** → **JSON 펜스 하나** 출력. draft term 제안·synthesis 파일링·query log는 전부 생략(brain 쓰기 0, H-1). 스파이크본(`//opbr ask`)은 대화형이라 후보목록서 멈추고 출력에 preamble 오염이 있었음(AGENTIC-LOG#19·22) → `--read-only`로 교체.

**`claude` CLI 출력 계약 (실측 + 스파이크 학습)**: `claude -p "//opbr query --read-only <질의>" --output-format json` → JSON 객체. 핵심 키:
- `type: "result"`, `subtype: "success"|"error_*"`, `is_error: bool`
- `result: str` ← **opbr 출력 (load-bearing)**. 콜드 시 부트스트랩 보고+PM preamble이 앞에 섞일 수 있으므로(스파이크 실측 — AGENTIC-LOG#19) backend가 **그 안의 JSON 펜스만 정규식 발췌** → `{answer, citations}` (H-6).
- `session_id: str` ← **세션 핸들 (B1 resume용, load-bearing)**.
- 그 외 `usage`, `total_cost_usd` 등 (무시). 실측 예: `{"type":"result","subtype":"success","is_error":false,"result":"...","session_id":"...",...}` (실측 2026-06-22).

#### 2.3.3 영향 범위
- `claude`+opbr 콜드 프라임(OPAL 부트스트랩+opbr 로딩) **실측 90.8s** → **prime-on-intent**(메뉴 진입 시 백그라운드 콜드 선흡수)로 질의는 웜(**실측 20.2s**)으로 처리(H-5). timeout 콜드180/웜60. 단일 세션 → 동시 질의 `threading.Lock` 직렬화(H-3).
- citations는 opbr가 JSON 펜스에 직접 담아 출력하므로 backend는 본문 정규식 파싱이 아니라 **JSON 펜스의 `citations` 배열을 그대로 매핑**(스파이크본 본문 정규식 파싱 → JSON 추출로 격상). 펜스 부재·파싱 실패 시 빈 배열(answer는 보존, H-6).

---

### F-004: FE 메뉴/라우트

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/router.tsx` | `/brain` 라우트 등록 | 수정 |
| FE | `dashboard/frontend/src/components/app-shell/AppShell.tsx` | `NAV_ITEMS` 6번째 항목 + 주석 갱신 | 수정 |
| FE | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 라우트 타깃 (F-005에서 본문 구현) | 신규 |

#### 2.4.2 현재 구현
`router.tsx:20-34` `createBrowserRouter` children에 5개 라우트. `AppShell.tsx:73-79` `NAV_ITEMS` 5개 항목(`Brain` 아이콘은 이미 `/memory`에 사용 중 — ANALYSIS R1 주의). `AppShell.tsx:65` 주석 `/** 5개 네비 항목 (C-11: 브레인 제외) */` 갱신 필요. `@header.description`(router.tsx, AppShell.tsx)도 "5개"→"6개" 갱신.

#### 2.4.3 영향 범위
- `Brain` 아이콘이 `/memory`에 선점됨 → "프로젝트 브레인"에는 다른 lucide 아이콘(`MessageCircleQuestion` 또는 `Sparkles`) 사용하여 시각 혼동 방지.
- `router.tsx`·`AppShell.tsx`는 BE와 무관 → Phase 2에서 BE와 병렬 가능.

---

### F-005: FE 질의 UI

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| FE | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | 인증 분기 + 질의 입력 + 답변/인용 렌더 | 수정 (F-004 신규 파일 본문) |
| FE | `dashboard/frontend/src/lib/api.ts` | `apiClient` 재사용 (POST options) | 참조 (변경 없음) |

#### 2.5.2 현재 구현
`apiClient<T>(path, options)` (`api.ts:19`)는 `RequestInit` 병합 → POST는 `{ method:"POST", body: JSON.stringify(...) }` 전달 (`(→ D-7 §api.ts:19)`). auth 조회는 useQuery, prime/질의는 useMutation(사이드이펙트 단발). 기존 페이지 패턴: `pages/{name}/{Name}Page.tsx`. **이력은 backend 무상태(DECISION#24)이므로 브라우저 `localStorage`에 보관** — Q&A 스레드 `{session_id, turns:[{q,a,citations}]}`.

#### 2.5.3 영향 범위
- `useMutation`은 자동 refetchInterval 미적용 → 질의 POST는 명시적 트리거만. 미인증 시 폼 비노출 → 무의미 POST·구독 호출 방지 (H-14).
- **prime-on-intent**: BrainPage 마운트(메뉴 진입) 시 1회 `POST /api/brain/prime` 호출(백그라운드 콜드 선흡수) → 첫 질의 무렵 세션 웜(H-5).
- **localStorage 이력**: 질의 응답의 `session_id`·`{q,a,citations}`를 스레드에 append·persist. 새로고침 후 표시 유지, 재질문은 동일 `session_id`로 resume, "새 대화"는 새 스레드(session_id="" → 다음 질의가 새 세션, 트리거ⓔ). 직렬화/쿼터/정합 리스크(H-15).

---

## 3. 기능별 설계

### F-000: 스파이크 — BrainSession 콜드프라임 + `//opbr` E2E **[완료]**

> **상태: 완료.** 아래 설계는 스파이크 최소본으로 구현되었고(opbr_adapter 119줄·brain.py 117줄·main.py·test 263줄), S-4 캡틴 검증 PASS + warm probe로 B1 확정. Phase 2(F-003)에서 `//opbr query --read-only` + JSON펜스 추출 + BrainSession 상태기계로 **교체·강화**된다. 스파이크본 `prime_and_ask`는 `//opbr ask` 기반이었으나 F-003서 `//opbr query --read-only`로 대체.

#### 3.0.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/adapters/opbr_adapter.py` | BE | `//opbr ask` 구동 + 세션 핸들 + 출력 파싱 (스파이크 최소본) | 실측 §2.0.2, (→ D-11) |
| 2 | `dashboard/backend/routers/brain.py` | BE | `POST /api/brain/query` 최소 핸들러 (스파이크) | (→ D-1) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/main.py` | BE | `allow_methods=["GET","POST"]` + brain 라우터 등록 (최소) | `main.py:45,51-55` |

#### 3.0.2 API·데이터 모델·화면 설계

**스파이크 어댑터 시그니처 (`opbr_adapter.py` 최소본)**:
```python
CLAUDE_BIN = "claude"   # shutil.which로 해석

def prime_and_ask(question: str, project_path: str,
                  session_id: str | None = None,
                  timeout: float = 180.0) -> dict:
    """B1 방식 스파이크:
       cmd = ["claude", "-p", f"//opbr ask {question}", "--output-format", "json"]
       if session_id is None: cmd += ["--session-id", <new uuid4>]   # 콜드 프라임
       else:                  cmd += ["--resume", session_id]        # 웜 재개
       subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False)
       → json.loads(stdout); is_error/subtype 판정
       → 반환: {"answer": parsed["result"], "session_id": parsed["session_id"],
                "elapsed_s": <측정>, "citations": <본문 파싱>}
    """
```
- **[MUST] backend는 brain 검색/페이지읽기/인용을 재구현하지 않는다** (TASK §확정방향1 — `(→ D-0 §1)`). `//opbr ask`가 전담(DRY/SSOT). backend는 질의 전달 + opbr 출력 파싱 + 응답만 수행하는 얇은 프록시.
- **[MUST] 금지 플래그** (TASK §제약② — `(→ D-0 §제약)`): `--safe-mode`(opbr·CLAUDE.md 미로드)·`--bare`·anthropic SDK·`ANTHROPIC_API_KEY`·`ANTHROPIC_AUTH_TOKEN`·`ant auth login`·`~/.config/anthropic` 일절 사용 금지. Python 신규 의존성 0.
- **[MUST] 읽기전용 가드** (TASK §확정방향4·§제약③ — `(→ D-0 §4)`): 프롬프트에 "질의만 수행, brain 페이지 파일링·draft term 등록·쓰기 금지" 지시를 포함. 질의 전후 `.opal/brain` 파일 불변을 검증(H-1).
- **콜드/웜 실측 항목**: ① `session_id=None`(콜드, OPAL+opbr 부팅 포함) 지연 ② 동일 session_id로 `--resume`(웜) 지연 ③ 두 지연 차이로 B1(resume) vs B2(상주 stream-json) 권고 결정.

**스파이크 라우터 (`POST /api/brain/query` 최소)**:
```
POST /api/brain/query {question, project} → 200 {answer, citations[], session_id, elapsed_s}
 1. project 경로 결정 (memory.py _find_project_path 패턴 — memory.py:30, → D-12)
 2. result = opbr_adapter.prime_and_ask(question, project_path, session_id=<세션 모듈 보관값>)
 3. return {answer, citations, session_id, elapsed_s}
```

**B1 vs B2 결정 매트릭스 (스파이크 산출)**:
| 방식 | 구동 | 장점 | 단점 | 채택 조건 |
|------|------|------|------|----------|
| **B1 (기본)** | 질의마다 새 프로세스 + `--session-id`(콜드)/`--resume`(웜) | 구현 단순, 프로세스 격리, 크래시 복원 쉬움 | resume 오버헤드(웜도 프로세스 재기동) | 웜 지연이 허용 범위(예: <10s) |
| **B2 (대안)** | 데몬이 `--input-format stream-json --output-format stream-json` 상주 프로세스 유지 | 최저 지연(프로세스 재기동 없음) | 데몬 프로세스 수명관리·stdin 스트림·크래시 복원 복잡 | 웜 지연이 B1에서 과대(예: >10s) |

#### 3.0.3 환경 변경
신규 패키지 없음. 런타임 의존: `claude` CLI(외부, 사용자 구독 인증).

#### 3.0.4 배치/마이그레이션
해당 없음.

#### 3.0.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-000 | 완료기준·확정방향6 | E2E(L3 SUPERVISOR) | 로컬 데몬 → `POST /api/brain/query` → `//opbr ask` 구동 → 답변+인용 반환 1건 PASS (캡틴 직접). ①구독 인증 작동 ②OPAL/opbr 로딩 ③E2E 답변 |
| TS-001 | H-5 | 성능 실측(L3) | 콜드(session_id=None) vs 웜(`--resume`) 지연 측정 → B1/B2 결정 (캡틴) |
| TS-002 | H-1 | 보안(L3) | 질의 1건 전후 `.opal/brain` 디렉토리 파일 해시 불변(쓰기 0건) — 캡틴 |
| TS-003 | H-7 | 보안(L1, mock 캡처) | `prime_and_ask` 커맨드 배열에 `--safe-mode`·`--bare` 부재, opbr 호출 포함 (mock — 실 claude 미호출) |

---

### F-006: opbr `--read-only` 계약 추가 (원천 변경)

#### 3.6.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-brain/SKILL.md` | Framework | §STEP query에 `--read-only` 비대화형 계약 추가 + §모드 라우팅 갱신 + version v1.3→v1.4 + 변경이력 행(036) | `SKILL.md:37,274-296,419-426`, (→ D-11) |

#### 3.6.2 계약 설계 (`SKILL.md` §STEP query 추가)

`//opbr query --read-only "<질의>"` — **비대화형 자동 read-only 질의 계약**:
1. **자동 선별 top-N (기본 3)** — `brain-tool search` 후보에서 LLM이 자동으로 상위 N개 페이지를 선택해 Read. 사용자 선택 대화 없음(대화형 `ask`와 대비).
2. **항상 최종답변 합성** — 후보 목록·검색 결과에서 **멈춤 금지**. 반드시 in-context 합성한 최종 답변을 낸다(스파이크 학습 DECISION#22: 웜 출력이 후보목록서 멈추는 회귀 차단).
3. **순수 read-only** — 다음을 **전부 생략**: 진입점③ draft term 등록 제안(L292-296), STEP5 synthesis 페이지 파일링, query log 기록. **brain 쓰기·제안 0건**(H-1 원천 차단).
4. **출력 = JSON 코드펜스 하나** — 답변 본문 텍스트가 아니라 정확히 하나의 JSON 펜스:
   ```json
   {"answer": "<합성 답변>", "citations": [{"page": "<brain 페이지 경로>", "title": "<제목>", "type": "concept|entity|flow|synthesis|term"}]}
   ```
   colsole backend가 `claude --output-format json`의 `result`에서 이 펜스만 발췌(부트스트랩 preamble 무시 — H-6).
- **[MUST] `//opbr ask` 대화형 분기 불변** — `--read-only`는 query 모드의 비대화형 하위 계약. 기존 `ask` 사용처 회귀 0.
- **[MUST] version bump v1.3→v1.4 + 변경이력 행 추가**: `| v1.4 | 2026-06-22 | query --read-only 비대화형 계약 추가(자동 top-N 선별·항상 최종답변 합성·순수 read-only[draft 제안·synthesis 파일링·query log 전면 생략]·JSON펜스 출력) — 콘솔 headless 호출용. ask 대화형 분기 불변 (036) |`
- **[MUST] 배포 경계** — `opal/skills/opal-brain/SKILL.md` 소스만 수정. `~/.opal/skills/...` 직접편집 금지. CLOSE install 재배포(L3, 캡틴 직접)로 dashboard와 동시 발효(DECISION#25, → D-3).

#### 3.6.3 환경 변경
없음 (마크다운 계약 문서 변경).

#### 3.6.4 배치/마이그레이션
CLOSE에서 `install` 재배포 1회 — dashboard + opbr SKILL을 함께 발효(캡틴 L3, DECISION#25).

#### 3.6.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-060 | H-16 | 문서 검증 | SKILL §STEP query에 `--read-only` 4계약(자동top-N·항상합성·순수read-only·JSON펜스) 전수 명시 |
| TS-061 | H-16 | 문서 검증 | `//opbr ask` 대화형 분기 설명 불변(회귀 0) + version v1.4 + 변경이력 행(036) 존재 |
| TS-062 | H-17 | 통합(L3 SUPERVISOR) | CLOSE install 재배포 후 `//opbr query --read-only` 실호출 → 합성 답변(후보목록 아님) + JSON펜스 + brain 쓰기 0 (캡틴) |

---

### F-001: 읽기전용 격리 경계

#### 3.1.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/main.py` | BE | `allow_methods=["GET","POST"]` + `from ...routers import ... brain` + `app.include_router(brain.router)` + `@header.depends`에 `routers.brain` 추가 | (→ D-5 §2), `main.py:45,51-55,8` |
| 2 | `dashboard/backend/tests/test_routers.py` | BE | `test_no_brain_endpoints` → brain 엔드포인트 **존재** 검증으로 전환 + 기존 5라우터 POST→405 회귀 테스트 추가 | `test_routers.py:258-264` |

#### 3.1.2 API·데이터 모델·화면 설계
- **CORS 완화 (격리 보증)**: `allow_methods=["GET","POST"]` (`main.py:45`). CORS는 preflight만 제어하며, 기존 5라우터는 POST 핸들러 미등록 → 405 유지로 실질 read-only 보존 `(→ D-5 §2)`.
- **[MUST]** `docs/CONVENTIONS.md` §배포 경계: "`~/.opal/` 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스(`opal/`, `skills/`, ...)에서 수행한다." → `dashboard/` 소스만 수정. 동작 발효는 install 재배포(L3, 캡틴 직접) `(→ D-3 §배포 경계)`.
- **[MUST]** uvicorn `host="127.0.0.1"` 불변 (`main.py:101`) — 외부 노출 금지 (H-12).
- **격리 단언(코드 검증 가능)**: `grep -rE "@router\.(post|put|delete)" dashboard/backend/routers/` 결과가 `brain.py`에만 매칭되어야 한다 (QA Q-1).

#### 3.1.3 환경 변경
해당 없음.

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-010 | R5 AC | 기능(L1) | 기존 5라우터에 POST 요청 시 405 Method Not Allowed |
| TS-011 | R5 AC | 회귀(L1) | `grep @router.post|put|delete routers/` 가 `brain.py`에만 매칭 (기존 5라우터 0건) |
| TS-012 | R5 제약 | 보안(L1) | uvicorn host=127.0.0.1 단언, 0.0.0.0 부재 (H-12) |

---

### F-002: BE 인증 상태 API

#### 3.2.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/backend/adapters/auth_adapter.py` | BE | `claude` CLI 가용·인증 경량 체크 | (→ D-2 §원칙3) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/routers/brain.py` | BE | `GET /api/brain/auth` 핸들러 추가 | (→ D-1) |
| 2 | `dashboard/backend/models.py` | BE | `BrainAuthResponse` 추가 (L197 이후) | `models.py:197` |

#### 3.2.2 API·데이터 모델·화면 설계

**데이터 모델 (`models.py` 추가)**:
```python
class BrainAuthResponse(BaseModel):
    authenticated: bool          # claude CLI 가용 + 인증 추정 여부
    cli_available: bool          # shutil.which("claude") is not None
    message: str                 # 미설치/미인증 시 안내, 인증 시 "" 또는 상태
```

**어댑터 시그니처 (`auth_adapter.py`)**:
```python
def check_auth() -> dict:
    """반환: {"authenticated": bool, "cli_available": bool, "message": str}"""
```
- **판별 방식 (권고·근거)**: **경량 체크 우선** — `shutil.which("claude")`로 CLI 설치 탐지. 미설치 시 `{authenticated:False, cli_available:False, message:"<설치/로그인 안내>"}`. 설치 시, 실 구독 토큰 소모를 피하기 위해 **실 `claude` 호출 없이** 인증 가용으로 간주하되, 실제 유효성은 `POST /api/brain/query`의 `is_error` 캐치로 자연 검증. 이유: auth는 UI 렌더 시 빈번 호출(H-10) → 매 호출 토큰 소모는 비현실적. **[MUST]** 실 `claude -p` 호출을 auth 엔드포인트에서 수행하지 않는다 (H-8 구독 토큰 보호).
- **[MUST] 종량제 경로 금지** (TASK §제약② — `(→ D-0 §제약)`): `anthropic` SDK·`ANTHROPIC_API_KEY`·`ANTHROPIC_AUTH_TOKEN`·`ant auth login`·`~/.config/anthropic` 일절 사용 금지. Python 신규 의존성 없음.
- **미설치 안내 메시지 (예)**: `"Claude Code CLI(claude)가 설치되어 있지 않거나 로그인되지 않았습니다. Claude Code를 설치하고 로그인하면 브레인 질의를 사용할 수 있습니다."`

**API 설계**:
```
GET /api/brain/auth → 200 BrainAuthResponse
```

#### 3.2.3 환경 변경
신규 패키지 없음. 런타임 의존: `claude` CLI(외부 도구, 사용자 환경에 설치·인증). 미설치 graceful (H-10).

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-020 | R2 AC | 기능(L1, mock) | `shutil.which`=경로 → `{authenticated:true, cli_available:true}` |
| TS-021 | R2 AC | 기능(L1, mock) | `shutil.which`=None → `{authenticated:false, cli_available:false, message:비어있지 않음}` |
| TS-022 | R2 제약 | 보안(L1) | auth 핸들러가 실 `claude -p` 서브프로세스를 호출하지 않음 (mock 호출 0회, H-8) |

---

### F-003: BE 질의+프라임 API + 관리형 세션 (B1·prime-on-intent)

#### 3.3.1 파일 변경 계획

**수정 (F-000 스파이크본 교체·하드닝 — `//opbr ask`→`//opbr query --read-only`)**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/backend/adapters/opbr_adapter.py` | BE | `BrainSession` 상태기계(prime-on-intent·B1 resume·5트리거 리셋·Lock·크래시 재프라임) + `//opbr query --read-only` 구동 + **JSON펜스 추출** + 읽기전용 가드 | 스파이크 학습 §2.0.2, (→ D-11) |
| 2 | `dashboard/backend/routers/brain.py` | BE | `POST /api/brain/query`(세션 위임·graceful·502/504) + `POST /api/brain/prime`(백그라운드 콜드 프라임) | (→ D-1) |
| 3 | `dashboard/backend/models.py` | BE | `BrainQueryRequest`/`CitationItem`/`BrainQueryResponse`/`BrainPrimeResponse` 추가 | `models.py:197` |

#### 3.3.2 API·데이터 모델·화면 설계

**데이터 모델 (`models.py`)**:
```python
class BrainQueryRequest(BaseModel):
    question: str
    project: str = ""            # 절대경로. 빈 값이면 첫 OPAL 프로젝트 (memory.py 패턴, → D-12)
    session_id: str = ""         # FE가 보유한 세션 핸들(재질문 resume). 빈 값=현 세션/콜드

class CitationItem(BaseModel):
    page: str = ""               # brain 페이지 경로 (opbr JSON펜스 citations에서 매핑)
    title: str = ""
    type: str = ""               # concept|entity|flow|synthesis|term

class BrainQueryResponse(BaseModel):
    answer: str
    citations: list[CitationItem] = []
    session_id: str = ""         # 현 세션 핸들 → FE가 localStorage에 저장·재질문 resume

class BrainPrimeResponse(BaseModel):
    priming: bool                # 백그라운드 콜드 프라임 시작/진행 여부
    session_id: str = ""         # 프라임 완료 시 핸들(미완 시 빈 값)
```

**`BrainSession` 상태기계 (`opbr_adapter.py` — 관리형 지속 세션, B1 확정)**:
```python
class BrainSession:
    """데몬 생애주기 동안 유지되는 단일 brain 세션 핸들 (B1: 일회성 -p + 디스크 세션 resume).
       - session_id: str | None  (None = 미프라임/리셋됨)
       - turns: int, last_used: float  (컨텍스트/유휴 임계 추적)
       - priming: bool            (콜드 프라임 진행 중 — prime-on-intent 경합 방지, H-5b)
       - lock: threading.Lock     (동시 질의/prime 직렬화 — H-3)

    prime-on-intent(DECISION#22): 메뉴 진입 시 prime()이 백그라운드로 콜드 프라임(90s) 선행.
       이후 query는 웜 resume(20s). priming 진행 중 질의는 락에서 대기→완료 후 웜.
    5트리거 리셋(=session_id=None): ⓐ 서버 재실행(프로세스 시작=초기 None)
       ⓑ 컨텍스트 임계(turns/토큰 추정 초과) ⓒ 유휴 타임아웃(now-last_used>IDLE)
       ⓓ 크래시(resume 실패/exit≠0) ⓔ 수동 새 대화(FE가 session_id="" + 새 대화 의도 전달).
    """

    def _run(self, prompt: str, cold: bool, timeout: float) -> dict:
        """공통 구동: cmd = ["claude","-p", prompt, "--output-format","json"]
           cmd += ["--session-id", new_uuid] if cold else ["--resume", self.session_id]
           subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False)
           parsed = json.loads(stdout); is_error/subtype 판정
           answer, citations = extract_json_fence(parsed["result"])  # preamble 무시, JSON펜스만 발췌 (H-6)
           self.session_id = parsed["session_id"]; self.last_used = now; return {...}
        """

    def prime(self) -> dict:
        """prime-on-intent: 콜드 프라임 1회(미프라임/리셋 상태일 때). 백그라운드 스레드서 호출.
           락 획득 → already priming/warm이면 noop → cold _run(워밍업 질의 또는 //opbr query --read-only 빈 워밍)
           → priming=False. 반환 {priming, session_id}. (H-5b: 중복 콜드 방지)"""

    def ask(self, question: str, project_path: str, session_id: str = "") -> dict:
        """직렬화 락 획득 →
           prompt = f'//opbr query --read-only "{question}"'   # F-006 계약 (대화형 ask 폐기)
           cold = (self.session_id is None or 유휴/임계 초과); resume용 session_id는 FE값 우선
           timeout = COLD_TIMEOUT(180) if cold else WARM_TIMEOUT(60)   # 스파이크 실측: 콜드90.8/웜20.2
           try: out = self._run(prompt, cold, timeout)
           except TimeoutExpired: self.reset()→콜드 1회 재시도 / 또는 504
           실패(resume 만료·exit≠0): self.reset(); 콜드 1회 재프라임 재시도 (H-4)
           self.turns += 1
           return {"answer": out["answer"], "citations": out["citations"], "session_id": self.session_id}

    def reset(self) -> None:
        self.session_id = None; self.turns = 0; self.priming = False
```
- **[MUST] backend는 opbr를 재구현하지 않는다** — `//opbr query --read-only`가 brain 검색·top-N 선별·Read·합성·인용을 전담(DRY/SSOT) (TASK §1 — `(→ D-0 §1)`, opbr SKILL §query F-006 계약 — `(→ D-11)`).
- **[MUST] 읽기전용 가드** — `--read-only` 계약(F-006)이 brain 쓰기/제안/log를 원천 차단 + 질의 전후 `.opal/brain` 불변 검증 (TASK §확정방향4·§제약③ — `(→ D-0 §4)`, S-4 PASS 실증 — AGENTIC-LOG#19).
- **[MUST] 금지 플래그** — `--safe-mode`(opbr 미로드)·`--bare`(keychain 우회) 절대 금지. 구독 keychain 인증 유지 (TASK §제약② — `(→ D-0 §제약)`, H-7).
- **[MUST] 동시 질의/prime 직렬화** — 단일 세션 보호 `threading.Lock`(H-3). prime 진행 중 질의는 대기→웜(H-5b).
- **[MUST] JSON펜스 추출** — `extract_json_fence(result)`: `result` 안에서 ```` ```json ... ``` ```` 또는 `{...}` 펜스를 정규식 발췌→`json.loads`→`answer`+`citations`. 콜드 부트스트랩 preamble은 무시(스파이크 출력오염 학습 — AGENTIC-LOG#19, H-6). 펜스 부재/파싱 실패 시 answer는 result 평문 폴백·citations 빈 배열(answer 보존).
- **timeout**: 콜드 180s / 웜 60s (스파이크 실측 콜드90.8s/웜20.2s 기반 — AGENTIC-LOG#21).

**라우터 핸들러**:
```
POST /api/brain/prime {project} → 200 BrainPrimeResponse
 1. project 경로 결정 (memory.py:30 패턴)
 2. 백그라운드 스레드로 brain_session.prime() 트리거 (논블로킹 — 즉시 {priming:true} 반환)
 3. (FE는 메뉴 진입 시 호출 → 첫 질의 무렵 세션 웜)

POST /api/brain/query {question, project, session_id} → 200 BrainQueryResponse
 1. project 경로 결정 (memory.py:30; 빈 값→첫 OPAL 프로젝트)
 2. result = brain_session.ask(question, project_path, session_id)   # 세션 모듈 싱글톤
 3. is_error/펜스 파싱 실패 → 502; timeout → 504; brain 미초기화("관련 페이지 없음"류) → graceful 200 안내 (H-11)
 4. return BrainQueryResponse(answer, citations, session_id)   # session_id→FE localStorage
```

**API 설계**:
```
POST /api/brain/prime
  Request: {"project": str}
  Response 200: {"priming": bool, "session_id": str}   # prime-on-intent 백그라운드 트리거

POST /api/brain/query
  Request: {"question": str, "project": str, "session_id": str}
  Response 200: {"answer": str, "citations": [{"page","title","type"}], "session_id": str}
  Response 502: claude/opbr 합성 실패 (is_error/펜스 파싱 실패)
  Response 504: 콜드/웜 timeout 초과 (재프라임 재시도 후에도 실패)
```

#### 3.3.3 환경 변경
신규 Python 패키지 없음 (TASK §기술스택). `claude` CLI(외부 도구) 런타임 의존.

#### 3.3.4 배치/마이그레이션
해당 없음 — **backend 무상태**(DECISION#24, SQLite 폐기). 이력은 FE localStorage(F-005).

#### 3.3.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-030 | R3 AC | 통합(L1, mock) | subprocess mock → `{answer, citations[], session_id}` 200, answer=펜스 추출값 |
| TS-031 | R3 합성 | 기능(L1, mock) | `claude` result에 JSON펜스 `{"answer":"답변","citations":[...]}` mock → answer="답변", citations 매핑, session_id 보관 |
| TS-032 | H-6 | 기능(L1, mock) | `{is_error:true}` 또는 비JSON mock → 502 |
| TS-032b | H-6 | 기능(L1, mock) | result에 부트스트랩 preamble+JSON펜스 혼입 mock → 펜스만 발췌→answer/citations (preamble 무시) |
| TS-033 | H-3 | 동시성(L1) | 동시 2질의 → 직렬 처리(락), 세션 1개 유지 |
| TS-034 | H-2 | 기능(L1, mock) | turns/유휴 임계 초과 → 다음 ask가 콜드 프라임(`--session-id`) |
| TS-035 | H-4 | 기능(L1, mock) | `--resume` 실패(exit≠0/만료) mock → reset 후 콜드 재프라임 1회 재시도 |
| TS-035b | H-5b | 기능(L1, mock) | prime 진행 중 query 도달 → 중복 콜드 0, prime 완료 후 웜 응답 |
| TS-036 | H-1 | 보안(L1, mock 캡처) | `ask` 호출이 `//opbr query --read-only` 사용 + 쓰기금지 지시 포함 단언 |
| TS-037 | H-7 | 보안(L1, mock 캡처) | 커맨드 배열에 `--safe-mode`·`--bare` 부재, `//opbr query --read-only` 포함, 첫 호출 `--session-id`/재호출 `--resume` |
| TS-038 | H-8 | 보안(L1) | 단위 테스트 전체에서 실 `claude` 서브프로세스 호출 0회 (mock 보증) |
| TS-039 | H-11 | 기능(L1, mock) | opbr "관련 페이지 없음" 출력 mock → graceful 200 안내 |
| TS-03A | R3 prime | 기능(L1, mock) | `POST /api/brain/prime` → 백그라운드 콜드 트리거, 즉시 `{priming:true}` 논블로킹 반환 |

---

### F-004: FE 메뉴/라우트

#### 3.4.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | FE | 라우트 타깃 (본문은 F-005) | (→ D-1) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/router.tsx` | FE | children에 `{ path:"brain", element:<BrainPage/> }` + import + @header desc/depends 갱신 | `router.tsx:20-34` |
| 2 | `dashboard/frontend/src/components/app-shell/AppShell.tsx` | FE | `NAV_ITEMS` 6번째 항목 + L65 주석 + @header desc 갱신 | `AppShell.tsx:65,73-79` |

#### 3.4.2 API·데이터 모델·화면 설계
- **라우트**: `{ path: "brain", element: <BrainPage /> }` 추가.
- **NAV_ITEMS 항목**: `{ to: "/brain", label: "프로젝트 브레인", icon: MessageCircleQuestion }` — `Brain` 아이콘은 `/memory` 선점이므로 미사용 (§2.4.3). lucide import 추가.
- **주석/헤더 갱신**: `AppShell.tsx:65` `5개 → 6개`, `router.tsx`·`AppShell.tsx` `@header.description` "5개" → "6개" 갱신.

#### 3.4.3 환경 변경
신규 패키지 없음 (lucide-react 기존 의존).

#### 3.4.4 배치/마이그레이션
해당 없음.

#### 3.4.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-040 | R1 AC | 산출물 검사 | `NAV_ITEMS`에 `/brain` "프로젝트 브레인" 항목 존재, `router.tsx`에 brain 라우트 존재 |
| TS-041 | R1 AC | 기능(L3 시각) | 사이드바 6번째 "프로젝트 브레인" 노출, 클릭 시 `/brain` 이동·BrainPage 렌더 |

---

### F-005: FE 질의 UI

#### 3.5.1 파일 변경 계획

**수정 (F-004에서 신규 생성한 파일 본문 구현)**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `dashboard/frontend/src/pages/brain/BrainPage.tsx` | FE | 인증 useQuery + 미인증 안내 + 질의 useMutation + 답변/인용 렌더 | (→ D-7 §api.ts:19) |

#### 3.5.2 API·데이터 모델·화면 설계

##### 화면: 프로젝트 브레인
- **ID**: FE-1
- **유형**: form
- **action**: new
- **경로**: /brain
- **파일**: dashboard/frontend/src/pages/brain/BrainPage.tsx
- **shadcn 컴포넌트**: Card, Textarea, Button, Alert, Badge, Skeleton
- **UI 작업**: ① 진입 시 `useQuery(["brain-auth"], GET /api/brain/auth)` + **인증 시 1회 `POST /api/brain/prime` 호출(prime-on-intent, 백그라운드 콜드 선흡수 — H-5)**. ② `authenticated:false`면 Alert로 미설치/미인증 안내(message) — 질의 폼 비노출(H-14). ③ `authenticated:true`면 Textarea + 제출 Button + **이력 패널(localStorage 스레드 표시)** + "새 대화" 버튼. ④ 제출 시 `useMutation(POST /api/brain/query {question, project, session_id})`. 진행 중 Skeleton/로딩(콜드 미선흡수 시 수십초 — 로딩 안내). ⑤ 성공 시 답변 Card + citations(Badge/리스트: page·title·type) → **응답 {session_id,q,a,citations}를 localStorage 스레드에 append·persist**. ⑥ 502/504/에러 Alert. ⑦ **재질문**: 이력 스레드의 `session_id`를 query에 실어 resume(멀티턴). ⑧ **"새 대화"**: 새 스레드(session_id="") 생성 → 다음 질의가 새 세션(트리거ⓔ). project는 현 컨텍스트(useUiStore.contextProject 또는 ?project=) 전달.
- **localStorage 스키마**: `opal.brain.threads` = `[{ session_id: string, project: string, turns: [{ q: string, a: string, citations: CitationItem[] }] }]`. 직렬화 안전·쿼터 가드(H-15).
- **API 연동**: `GET /api/brain/auth`(useQuery) + `POST /api/brain/prime`(useMutation/effect, 진입 1회) + `POST /api/brain/query`(useMutation, `apiClient("/api/brain/query",{method:"POST",body:JSON.stringify({question,project,session_id})})`)

#### 3.5.3 환경 변경
신규 패키지 없음 (shadcn 컴포넌트 중 미존재분은 EXECUTE에서 `shadcn` 스킬로 추가 — Textarea/Alert 존재 여부 EXECUTE 확인). localStorage는 브라우저 내장(신규 의존 0).

#### 3.5.4 배치/마이그레이션
해당 없음 (backend 무상태 — 이력은 클라이언트 localStorage).

#### 3.5.5 테스트 시나리오 (AC ↔ TS 매핑)
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-050 | R4 AC | 기능(L3 시각) | 미인증(auth false) → 안내 Alert 표시, 질의 폼 비노출 |
| TS-051 | R4 AC | 기능(L3 시각) | 인증 시 질문 입력→제출→답변 본문 + 근거 페이지 목록(citations) 렌더 |
| TS-052 | R4 흐름 | 기능(L3 E2E) | POST 응답 502/504 시 에러 Alert 표시 |
| TS-053 | H-5 | 기능(L3 시각) | 메뉴 진입 시 `POST /api/brain/prime` 1회 호출(prime-on-intent) → 첫 질의 체감 지연 단축 |
| TS-054 | H-15 | 기능(L3 E2E) | 질의→새로고침 시 localStorage 이력 유지·표시, 재질문은 동일 session_id resume, "새 대화"는 새 세션 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (단계화 — TASK §확정방향6, 스파이크 완료 반영)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| **1 (스파이크 — 캡틴 게이트) [완료]** | F-000 | 1, 2 | opal-be-agent | 순차 | 콜드프라임·`//opbr`·콜드/웜 실측·**B1 확정**·read-only. **S-4 캡틴 검증 PASS — Phase 2+ 진입 완료** |
| 2 | F-006 | 3 | opal-task-agent | 독립 | opbr 원천 `--read-only` 계약(SKILL.md) — F-003 전제, dashboard와 동시 발효 |
| 2 | F-001 | 4 | opal-be-agent | Step2(완료) 후 | BE 격리 경계 하드닝 |
| 2 | F-004 | 10, 11 | opal-fe-agent | BE와 병렬 가능 | FE 라우트/네비 — BE와 독립 |
| 3 | F-002 | 5, 6 | opal-be-agent / opal-test-agent[red] | Step4 후 | auth API + 어댑터 + RED |
| 3 | F-003 | 7, 8, 9 | opal-be-agent / opal-test-agent[red] | Step4·3 후 | query+prime API + 세션·JSON펜스·가드 하드닝 + RED + 스파이크 회귀 RED |
| 4 | F-005 | 12 | opal-fe-agent | Step5·7·11 후 | BE 계약 + FE 라우트 + localStorage 의존 |
| 5 | 격리 회귀/문서 | 13, 14 | opal-be-agent / PM 직접 | 구현 후 | 격리 회귀 검증 + docs 갱신(ARCHITECTURE/PROJECT + opbr SKILL 변경이력) |

### 4.2 실행 체크리스트
> 총 14개 Step | Phase 5개 | 실행 모드: 복잡 | Step 1~2 = Phase 1 스파이크 **완료**(S-4 캡틴 검증 PASS)

#### Step 1: [스파이크·완료] BE opbr 어댑터 — `//opbr` 구동 + 세션 핸들 + 출력 파싱
- [x] 완료 (S-4 검증 PASS)
- **소속 기능**: F-000
- **영역**: BE | **agent**: opal-be-agent
- **파일**: `dashboard/backend/adapters/opbr_adapter.py`(신규, 최소본 — 119줄)
- **작업 내용**: `prime_and_ask` — `claude -p` + (`--session-id`/`--resume`), `subprocess.run(shell=False)` → `json.loads` → 파싱. 스파이크본은 `//opbr ask` 기반(Phase 2서 `//opbr query --read-only`로 교체). 금지 플래그 부재. mock(0 토큰).
- **완료 기준**: 콜드/웜 양 경로 구동, 커맨드 금지 플래그 부재. **달성**(18 PASS).
- **테스트**: TS-003 (커맨드 mock 캡처)
- **실행 방법**: sub-agent | **의존**: 없음

#### Step 2: [스파이크·완료] BE 최소 query 라우터 + main.py 등록 + 캡틴 E2E 검증
- [x] 완료 (S-4 캡틴 L3 SUPERVISOR PASS)
- **소속 기능**: F-000
- **영역**: BE | **agent**: opal-be-agent
- **파일**: `dashboard/backend/routers/brain.py`(신규 117줄), `dashboard/backend/main.py`(allow_methods POST + 라우터 등록), `dashboard/backend/tests/test_brain_spike.py`(263줄)
- **작업 내용**: 최소 `POST /api/brain/query` → `opbr_adapter.prime_and_ask`. host 127.0.0.1 불변. **검증=캡틴 직접(L3)**: 실 질의 → 구독 인증·OPAL/opbr 로딩·답변 E2E·콜드/웜 실측·`.opal/brain` 불변·B1 결정.
- **완료 기준**: **달성** — S-4 PASS(brain 근거 답변·read-only PASS), warm probe로 **콜드90.8s/웜20.2s 실측 → B1 확정**(AGENTIC-LOG#19·21·22). 게이트 통과 → Phase 2+ 진입.
- **테스트**: TS-000, TS-001, TS-002 (캡틴 L3 SUPERVISOR — PASS)
- **실행 방법**: sub-agent (구현) + 캡틴 직접 (검증) | **의존**: Step 1

#### Step 3: [Phase 2] opbr 원천 `--read-only` 계약 추가 (SKILL.md)
- [ ] 완료
- **소속 기능**: F-006
- **영역**: Framework | **agent**: opal-task-agent
- **파일**: `opal/skills/opal-brain/SKILL.md`
- **작업 내용**: §STEP query에 `//opbr query --read-only "<질의>"` 비대화형 계약 추가(§3.6.2) — ① 자동 top-N(기본3) 선별 ② 항상 최종답변 합성(후보목록 멈춤 금지) ③ 순수 read-only(진입점③ draft 제안·synthesis 파일링·query log 전면 생략) ④ 출력=JSON 펜스 하나 `{"answer","citations":[{page,title,type}]}`. §모드 라우팅에 `--read-only` 분기 명기. **[MUST]** `//opbr ask` 대화형 분기 불변. version v1.3→v1.4 + 변경이력 행(036). **[MUST]** `opal/` 소스만 수정, `~/.opal` 직접편집 금지(→ D-3). RED 불가(마크다운)→문서 검증.
- **완료 기준**: §query에 4계약 명시 + `ask` 분기 불변 + v1.4 + 변경이력 행.
- **테스트**: TS-060, TS-061
- **실행 방법**: sub-agent | **의존**: 없음 (BE/FE와 병렬, F-003 전제)

#### Step 4: [Phase 2] BE 격리 경계 하드닝 — CORS·@header·host 단언
- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE | **agent**: opal-be-agent
- **파일**: `dashboard/backend/main.py`
- **작업 내용**: `allow_methods=["GET","POST"]` 확정(Step2와 동일 파일), `@header.depends`에 `routers.brain` 추가, uvicorn host=127.0.0.1 불변. 기존 5라우터 POST 핸들러 미등록 보존.
- **완료 기준**: `allow_methods`에 POST, brain 라우터 등록, host 127.0.0.1, @header 갱신.
- **테스트**: TS-010, TS-012
- **실행 방법**: sub-agent | **의존**: Step 2(완료)

#### Step 5: [Phase 2] BE 인증 어댑터 + auth 엔드포인트 + 스키마
- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE | **agent**: opal-be-agent
- **파일**: `dashboard/backend/adapters/auth_adapter.py`(신규), `dashboard/backend/routers/brain.py`(GET auth 추가), `dashboard/backend/models.py`(BrainAuthResponse)
- **작업 내용**: `auth_adapter.check_auth()` — `shutil.which("claude")` 경량 체크, graceful message. `GET /api/brain/auth`. `BrainAuthResponse`. **[MUST]** anthropic SDK·API 키·ant OAuth 미사용. auth에서 실 `claude -p` 호출 금지(H-8).
- **완료 기준**: `GET /api/brain/auth` 200 + 계약. which mock 분기 통과.
- **테스트**: TS-020, TS-021, TS-022
- **실행 방법**: sub-agent | **의존**: Step 4

#### Step 6: [Phase 2] RED — 인증 API 단위 테스트 작성
- [ ] 완료
- **소속 기능**: F-002
- **영역**: BE | **agent**: opal-test-agent (mode: red)
- **파일**: `dashboard/backend/tests/test_brain.py`(신규)
- **작업 내용**: `shutil.which` mock 설치/미설치 분기 + auth가 실 `claude` 미호출 단언. **[MUST]** 작성자≠구현자(red-first §2): RED=본 Step, GREEN=Step5.
- **완료 기준**: RED 실패(구현 전) → Step5 구현 후 GREEN.
- **테스트**: TS-020~TS-022
- **실행 방법**: sub-agent | **의존**: Step 4 (Step5와 병렬 작성, 작성 주체 분리)

#### Step 7: [Phase 2] BE 질의+프라임 API + BrainSession 하드닝 (세션·JSON펜스·가드)
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE | **agent**: opal-be-agent
- **파일**: `dashboard/backend/adapters/opbr_adapter.py`(BrainSession 하드닝), `dashboard/backend/routers/brain.py`(POST query + POST prime), `dashboard/backend/models.py`(Query/Citation/Response/Prime 추가)
- **작업 내용**: `BrainSession` 상태기계(§3.3.2) — **`//opbr query --read-only` 구동**(스파이크 `ask` 교체)·prime-on-intent·B1 resume·5트리거 리셋·`threading.Lock`(H-3)·크래시 재프라임(H-4)·콜드180/웜60 timeout·**`extract_json_fence`**(preamble 무시 — H-6). 라우터: `POST /api/brain/query`(project 결정→`ask`→is_error/펜스실패 502/timeout 504/미초기화 graceful 200, session_id 반환) + `POST /api/brain/prime`(백그라운드 콜드 트리거, 논블로킹). **[MUST]** opbr 재구현 금지(얇은 프록시), `--safe-mode`/`--bare` 금지, read-only 가드, `claude` 전부 mock(H-8).
- **완료 기준**: `POST /query` 200 `{answer,citations[],session_id}` + `POST /prime` 논블로킹. 세션 분기(콜드/웜/리셋/재프라임/prime경합/동시성)·JSON펜스 추출 mock 통과, 실 서브프로세스 0회.
- **테스트**: TS-030~TS-039, TS-032b, TS-035b, TS-03A
- **실행 방법**: sub-agent | **의존**: Step 4, Step 3(F-006 계약), Step 2(스파이크본)

#### Step 8: [Phase 2] RED — query+prime API + 세션·JSON펜스 단위 테스트 작성
- [ ] 완료
- **소속 기능**: F-003
- **영역**: BE | **agent**: opal-test-agent (mode: red)
- **파일**: `dashboard/backend/tests/test_brain.py`(query/prime/세션 케이스 추가)
- **작업 내용**: subprocess mock(success/is_error/비JSON + preamble 섞인 result서 JSON펜스 발췌 TS-032b)·세션 분기(콜드/웜/임계·유휴 리셋/크래시 재프라임/prime경합 TS-035b/동시성 락)·read-only 가드(`//opbr query --read-only` + 쓰기금지)·금지플래그 부재·prime 논블로킹·실 claude 0회. **[MUST]** 작성자≠구현자(red-first §2). GREEN 루핑 중 RED 수정 금지(§3).
- **완료 기준**: RED 실패(구현 전) → Step7 구현 후 GREEN.
- **테스트**: TS-030~TS-039, TS-032b, TS-035b, TS-03A
- **실행 방법**: sub-agent | **의존**: Step 4 (Step7과 병렬 작성, 작성 주체 분리)

#### Step 9: [Phase 2] RED — 스파이크 어댑터 회귀 테스트 보강 (read-only·금지플래그)
- [ ] 완료
- **소속 기능**: F-000/F-003
- **영역**: BE | **agent**: opal-test-agent (mode: red)
- **파일**: `dashboard/backend/tests/test_brain.py`(커맨드 캡처 케이스)
- **작업 내용**: `BrainSession.ask` 커맨드 배열 mock 캡처 → `--safe-mode`·`--bare` 부재, **`//opbr query --read-only` 포함**(`ask` 폐기 확인), 콜드 `--session-id`/웜 `--resume` 단언(TS-037). read-only 가드 프롬프트(TS-036).
- **완료 기준**: 커맨드/프롬프트 단언 통과(mock, 실 claude 0회).
- **테스트**: TS-003, TS-036, TS-037
- **실행 방법**: sub-agent | **의존**: Step 2 (Step7/8과 병렬 작성)

#### Step 10: [Phase 2] FE `/brain` 라우트 + BrainPage 스텁
- [ ] 완료
- **소속 기능**: F-004
- **영역**: FE | **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/router.tsx`, `dashboard/frontend/src/pages/brain/BrainPage.tsx`(신규 스텁)
- **작업 내용**: BrainPage 스텁, router children에 `{path:"brain", element:<BrainPage/>}` + import + @header desc/depends 갱신.
- **완료 기준**: `/brain` 라우트 렌더(빌드 통과).
- **테스트**: TS-040
- **실행 방법**: sub-agent | **의존**: 없음 (BE와 병렬)

#### Step 11: [Phase 2] FE NAV_ITEMS 6번째 항목
- [ ] 완료
- **소속 기능**: F-004
- **영역**: FE | **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/components/app-shell/AppShell.tsx`
- **작업 내용**: `NAV_ITEMS`에 `{to:"/brain", label:"프로젝트 브레인", icon:MessageCircleQuestion}` 추가, lucide import, L65 주석 "5개→6개", @header desc 갱신. `Brain` 아이콘 미사용(/memory 선점).
- **완료 기준**: 사이드바 6번째 항목 노출.
- **테스트**: TS-040, TS-041
- **실행 방법**: sub-agent | **의존**: Step 10

#### Step 12: [Phase 2] FE BrainPage 본문 (인증 분기 + prime-on-intent + 질의 UI + localStorage 이력)
- [ ] 완료
- **소속 기능**: F-005
- **영역**: FE | **agent**: opal-fe-agent
- **파일**: `dashboard/frontend/src/pages/brain/BrainPage.tsx`
- **작업 내용**: §3.5.2 화면 FE-1 구현 — auth useQuery, **인증 시 진입 1회 `POST /api/brain/prime`(prime-on-intent)**, 미인증 Alert(폼 비노출), 인증 시 Textarea+제출, query useMutation({question,project,session_id}), 답변 Card + citations 목록, **localStorage 스레드 저장/표시/재질문(resume)·"새 대화"(새 세션)**, 502/504 에러 Alert, 콜드 로딩 안내. 미존재 shadcn은 `shadcn` 스킬로 추가.
- **완료 기준**: 미인증 안내 + 인증 시 prime 호출 + 질의→답변+인용 렌더 + localStorage 이력 유지·재질문·새 대화(빌드·시각 검증).
- **테스트**: TS-050, TS-051, TS-052, TS-053, TS-054
- **실행 방법**: sub-agent | **의존**: Step 5, Step 7, Step 11

#### Step 13: [Phase 2] BE 격리 회귀 검증 테스트 갱신
- [ ] 완료
- **소속 기능**: F-001
- **영역**: BE | **agent**: opal-be-agent (RED 갱신은 opal-test-agent)
- **파일**: `dashboard/backend/tests/test_routers.py`
- **작업 내용**: `test_no_brain_endpoints`(L258) → brain 엔드포인트 **존재**(auth 200, query/prime POST 등록) 검증 전환. 기존 5라우터 POST→405 회귀 추가. grep 격리 단언(`@router.post` → brain.py만).
- **완료 기준**: brain 존재 + 기존 5라우터 405 + grep 격리 통과.
- **테스트**: TS-010, TS-011
- **실행 방법**: sub-agent | **의존**: Step 7

#### Step 14: [Phase 2] docs/ 갱신 (ARCHITECTURE/PROJECT + opbr SKILL 변경이력)
- [ ] 완료
- **소속 기능**: F-000~F-006
- **영역**: 문서 | **agent**: PM 직접
- **파일**: `docs/ARCHITECTURE.md`(§OPAL Console — 6번째 메뉴·brain 라우터·POST 격리·`//opbr query --read-only` 구동·BrainSession prime-on-intent·B1 resume·무상태/localStorage 이력), `docs/PROJECT.md`(Console 5→6 화면), 필요 시 `docs/CONVENTIONS.md`(read-only 격리·원천 동시발효 패턴). opbr SKILL.md 변경이력은 Step3서 처리.
- **작업 내용**: 새 API(query/prime/auth)·새 FE 페이지·시스템 구조(POST 격리·`//opbr query --read-only` 프록시·BrainSession·무상태·localStorage 이력·원천 동시발효 DECISION#25) 반영.
- **완료 기준**: 6번째 메뉴·brain 엔드포인트(3)·`//opbr query --read-only` 경로·prime-on-intent·B1·무상태·격리 원칙 문서화.
- **테스트**: 산출물 검사
- **실행 방법**: direct | **의존**: Step 12, Step 13

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 (완료) | 어댑터 구동 후 라우터에서 호출 (스파이크) |
| Step 2 = 캡틴 게이트 (PASS) | 스파이크 E2E 통과 → Phase 2+ 진입 (TASK §확정방향6) |
| Step 3 (F-006) 독립 | opbr 원천 계약은 dashboard와 무관 파일(SKILL.md) — BE/FE와 병렬. 단 F-003(Step7) 호출 계약 전제 |
| Step 4 → Step 5,7,13 | 격리 경계·라우터 등록이 모든 BE brain 하드닝의 선행 |
| Step 5 ∥ Step 6 | auth 구현 vs auth RED — 작성 주체 분리(red-first §2), 파일 다름 |
| Step 7 ∥ Step 8 ∥ Step 9 | query 구현 vs query RED vs 스파이크 회귀 RED — 작성 주체 분리 |
| Step 7 → Step 4,3,2 의존 | query 하드닝이 격리 + F-006 계약 + 스파이크 어댑터 위에 구축 |
| BE(3~9) ∥ FE(10,11) | opbr/BE / FE 라우트 상호 독립 (FE는 BE 게이트 무관하게 병렬) |
| Step 10 → Step 11 | BrainPage 존재 후 NAV/라우트 일관 (FE 워커 순차) |
| Step 12 → Step 5,7,11 | FE 질의 UI는 BE 계약(auth/query/prime) + FE 라우트 모두 의존 |
| Step 13 → Step 7 | 격리 회귀는 brain 엔드포인트 완성 후 |
| Step 14 → Step 12,13 | 문서는 코드 완성 후 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-000 [완료] | 스파이크 E2E(`//opbr` 구동·구독·세션 로딩) + 콜드/웜 실측 + read-only + 금지플래그 | TS-000~TS-003 | **캡틴 E2E PASS**, **B1 확정**, `.opal/brain` 불변, `--safe-mode`/`--bare` 0건 |
| F-006 | opbr `--read-only` 4계약 + ask 분기 불변 + version·변경이력 | TS-060, TS-061, TS-062 | §query에 자동top-N·항상합성·순수read-only·JSON펜스 명시, ask 불변, v1.4 변경이력 행 |
| F-001 | 기존 5라우터 POST 거부 + grep 격리 + host 바인딩 | TS-010, TS-011, TS-012 | 5라우터 POST→405, `@router.post` brain.py에만, host=127.0.0.1 |
| F-002 | auth API 가용·미가용 분기 + 실 claude 미호출 | TS-020, TS-021, TS-022 | which mock 분기 정확, auth가 `claude -p` 0회 호출 |
| F-003 | query+prime 세션 흐름(prime-on-intent·B1 resume·5리셋·Lock·재프라임·prime경합) + JSON펜스 추출 + graceful + 가드 | TS-030~TS-039, TS-032b, TS-035b, TS-03A | mock 200 답변+인용+session_id, is_error/펜스실패→502, timeout→504, 미초기화→graceful, preamble 무시, prime 논블로킹, 세션 분기 정확, 실 서브프로세스 0회 |
| F-004 | 6번째 메뉴·라우트 등록 | TS-040, TS-041 | NAV/라우트 존재, 클릭→/brain 렌더 |
| F-005 | 인증 분기 UI + prime-on-intent + 질의→답변+인용 + localStorage 이력 | TS-050~TS-054 | 미인증 안내(폼 비노출), 진입 prime 호출, 답변+citations, 이력 유지·재질문 resume·새 대화, 502/504 Alert |

### 5.2 회귀 테스트
- [ ] 기존 5라우터(dashboard/projects/tasks/memory/doctor) GET 200 불변 (기존 test_routers 통과)
- [ ] 기존 5라우터에 POST 시 405 (CORS 완화 후 read-only 보존 — TS-010)
- [ ] `test_no_brain_endpoints` 갱신 후 기존 main/doctor 테스트 스위트 그린 (스파이크 단계 110 PASS 회귀 0 유지)
- [ ] FE 기존 5개 페이지 라우트·네비 정상 (빌드 통과)
- [ ] **opbr `--read-only` 추가가 기존 `//opbr ask`/`ingest`/`init`/`lint` 동작에 회귀 없음** (ask 대화형 분기 불변 — TS-061)

### 5.3 코드/문서 품질
- [ ] 프로젝트 컨벤션 준수 (`@header` 블록 신규 파일 부착, 기존 라우터/어댑터 패턴 일치)
- [ ] **[MUST]** `dashboard/` 소스만 수정 — `~/.opal/dashboard-server/` 직접 편집 없음 (CONVENTIONS §배포 경계)
- [ ] **[MUST]** opbr `--read-only` 계약은 `opal/skills/opal-brain/SKILL.md` **소스만** 수정 — `~/.opal/skills/...` 직접편집 없음. dashboard와 함께 CLOSE install 재배포 1회로 동시 발효(DECISION#25, H-17)
- [ ] docs/ 갱신 (Step 14) — ARCHITECTURE/PROJECT 반영 + opbr SKILL 변경이력(Step3)
- [ ] 신규 Python 의존성 0건 (anthropic SDK 미추가). **backend 무상태 — SQLite 미도입(DECISION#24)**

### 5.4 보안
- [ ] **[MUST]** anthropic SDK·`ANTHROPIC_API_KEY`·`ANTHROPIC_AUTH_TOKEN`·`ant auth login`·`~/.config/anthropic` 코드 부재 (grep 0건)
- [ ] **[MUST]** `claude` 구동 커맨드에 `--safe-mode`·`--bare` 부재 — opbr 로드 + 구독 keychain 인증 유지 (H-7, TS-003·TS-037)
- [ ] **[MUST]** uvicorn host=127.0.0.1 불변, 0.0.0.0 부재 (외부 노출 금지 — H-12)
- [ ] **[MUST]** 읽기전용 가드 — `//opbr query --read-only` 계약(F-006)이 brain 쓰기/제안/log 원천 차단 + 질의 1건 후 `.opal/brain` 파일 불변(0건 — H-1, TS-002·TS-036, S-4 PASS 실증)
- [ ] POST·LLM 호출이 brain 라우터에만 격리 (grep `@router.post|put|delete` → brain.py only — TS-011)
- [ ] 자동 테스트에서 실 `claude` 서브프로세스 호출 0회 (구독 토큰 보호 — H-8, TS-038)
- [ ] 코드에 하드코딩된 토큰/시크릿 없음 / `.env`·인증 파일 `.gitignore` 포함
- [ ] **backend·brain 무상태** — 질의 결과 영속 저장 0(이력은 FE localStorage). 서버 질의 로그 0 (DECISION#24)
- [ ] question 입력이 `//opbr query --read-only` 인자로 전달될 때 셸 인젝션 방지 (`subprocess.run(list)` — shell=False 보장, H-13)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 14개 (Step1~2 = Phase1 스파이크 완료) | 복잡 |
| 변경 파일 수 | 11개 (신규 5 + 수정 6 — Framework/FE/BE) | 복잡 |
| 모듈 범위 | 다중 (Framework opbr SKILL + FE 3 + BE 라우터/어댑터/모델/테스트 + 세션 상태기계 + FE localStorage) | 복잡 |
| 작업 유형 | 신규 개발 (메뉴·API 3·어댑터·관리형 세션·opbr 원천 계약) + 스파이크 | 복잡 |
| 외부 의존성 | 신규 외부 도구 `claude` CLI(서브프로세스) + opbr 스킬 구동(`//opbr query --read-only`) | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
- **Batch 1 (Phase 1 스파이크 — 게이트) [완료]**: `opal-be-agent`(Step1 어댑터 → Step2 라우터·main, 순차) → **캡틴 직접 E2E 검증(L3 SUPERVISOR) PASS**.
- **Batch 2 (Phase 2 — 병렬)**: `opal-task-agent`(Step3 opbr 원천 `--read-only` 계약 — SKILL.md, 독립) ∥ `opal-be-agent`(Step4 격리) ∥ `opal-fe-agent`(Step10,11 라우트/네비).
- **Batch 3**: `opal-be-agent`(Step5 auth → Step7 query·prime·세션, 동일 BE 모듈 순차) ∥ `opal-test-agent[red]`(Step6 auth RED, Step8 query RED, Step9 스파이크 회귀 RED).
- **Batch 4**: `opal-fe-agent`(Step12 BrainPage 본문 + localStorage — BE 계약 의존).
- **Batch 5**: `opal-be-agent`(Step13 격리 회귀) → PM 직접(Step14 docs).
- **그룹핑 근거**: 동일 파일(`opbr_adapter.py`·`brain.py`·`models.py`·`main.py`)을 만지는 BE Step은 모두 `opal-be-agent`(파일 충돌 방지). opbr SKILL.md(Framework)는 `opal-task-agent`(dashboard와 무관 파일·병렬). FE 3파일은 `opal-fe-agent`. RED 작성은 별도 `opal-test-agent`(작성자≠구현자, red-first §2).

### C-2. 스킬 요구사항
- Framework(F-006): `op-dev-execute` — opbr SKILL.md 계약 추가는 마크다운 편집 + 변경이력/version 규칙(인라인 충분).
- BE: `op-dev-execute` + `trailofbits/modern-python`(서브프로세스·타입·threading). `//opbr query --read-only` 구동·JSON펜스 추출·세션 상태기계는 1~2 어댑터 — 인라인 지침으로 충분(신규 스킬 불요).
- FE: `op-dev-execute` + `ui-designer`(plan-driven, §3.5.2 FE-1 입력) + `vercel-labs/shadcn`(Textarea/Alert 추가 시) + `react-best-practices`(useMutation/useQuery·localStorage 패턴).
- RED: `opal-test-agent` mode:red (mock 기반 RED-first).

### C-3. 도구 요구사항
- 런타임: `claude` CLI v2.1.185(`/Users/iskang/.local/bin/claude`, 실측) — `-p`·`--output-format json`·`--session-id`·`--resume`·`--input-format/--output-format stream-json` 지원 확인.
- 테스트: pytest + httpx TestClient(기존), `unittest.mock`(서브프로세스 mock). 신규 패키지 0.
- MCP: 필요 시 shadcn MCP(컴포넌트 조회). context7 불요.

### C-4. 테스트 전략
- **문서 검증(F-006)**: `opal/skills/opal-brain/SKILL.md` §query에 `--read-only` 4계약·ask 분기 불변·v1.4 변경이력 행 정합 확인(TS-060·061). RED 불가(마크다운).
- **L1 단위(RED-first)**: `test_brain.py` — auth(which mock)·opbr_adapter/BrainSession(subprocess mock: success/is_error/비JSON + **preamble 섞인 JSON펜스 발췌** + 세션 분기 콜드/웜/리셋/재프라임/prime경합/동시성)·query+prime 라우터(전부 mock)·커맨드/프롬프트 가드(`//opbr query --read-only`·금지플래그 부재) 단언. **[MUST] 실 `claude` 호출 0회.**
- **L1 회귀**: `test_routers.py` 갱신(brain 존재 + 5라우터 405 + grep 격리), `test_main.py`(host 127.0.0.1).
- **L3 시각(FE)**: BrainPage 미인증 안내/인증 질의 렌더/prime-on-intent/localStorage 이력·재질문·새 대화 — opal-test-agent mode:fe 또는 캡틴 육안.
- **L3 SUPERVISOR(스파이크·실 구독 E2E)**: Phase 1 [완료] — `//opbr` 구동 → 답변+인용 + 콜드/웜 실측 + read-only + **B1 확정** (캡틴 PASS, TS-000~TS-002). Phase 2 — **CLOSE install 재배포(dashboard+opbr 동시 발효) 후** 통합 E2E(`//opbr query --read-only` 합성 답변+read-only — TS-062). **자동화 금지(토큰 소모).**

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| FE | React 19, TS, Vite, React Router v7, TanStack Query v5, Zustand v5, shadcn/ui | ui-designer, vercel-labs/shadcn, react-best-practices |
| BE | Python, FastAPI, uvicorn, threading(세션 락) | trailofbits/modern-python |
| LLM/지식 | 로컬 `claude` CLI v2.1.185 `//opbr query --read-only`(사용자 구독, OPAL+opbr 로드) | opal-brain(opbr) 스킬 구동 — backend는 프록시 |
| 이력 | 브라우저 localStorage (backend 무상태, SQLite 폐기 — DECISION#24) | — |
| 도구 | pytest+httpx, unittest.mock | op-dev-execute, opal-test-agent |

### 8.2 사용 MCP / 실측
| 출처 | 조회 결과 요약 |
|-----|--------------|
| `claude --version` (실측) | v2.1.185 (2026-06-22) |
| `claude --help` (실측) | `-p`·`--session-id <uuid>`·`--resume [value]`·`--input-format/--output-format stream-json`·`--output-format json`·`--no-session-persistence`·`--safe-mode`(금지)·`--bare`(금지) 확인 |
| `claude -p "..." --output-format json` (실측) | `{type:"result",subtype:"success",is_error:false,result:"<답변>",session_id:"...",...}` — `result`=답변, `session_id`=세션핸들(B1 resume) |
| **S-4 캡틴 E2E (실측)** | 핵심 루프 PASS — 구독 작동·OPAL/opbr 실로딩·brain 근거 답변(`[[opal-first-use-guide]]`)·read-only PASS(brain 0변경). 콜드 99.4s·출력오염(부트스트랩 preamble) 발견 (AGENTIC-LOG#19) |
| **warm probe (실측)** | 콜드 90.8s → 웜(resume) 20.2s(78%↓), 부트스트랩 노이즈 제거·멀티턴 맥락 유지 → **B1 확정**(AGENTIC-LOG#21·22) |
| shadcn MCP | EXECUTE Step12에서 Textarea/Alert 미존재 시 조회·추가 (필요 시) |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-0 | 기획 | TASK.md (SSOT, B 정정) | `tasks/036-260622-opd-브레인질의-콘솔연동/TASK.md` | R1~R5·확정방향§1·5·6(구독 기반·관리형 세션·단계화)·제약 |
| D-0b | 대행일지 | AGENTIC-LOG.md DECISION 19~25 | `tasks/036-.../AGENTIC-LOG.md` | 스파이크 결과·B1 확정·`--read-only` 계약·localStorage·무상태·이 레포=OPAL 원천(동시발효) |
| D-1 | 설계 | ARCHITECTURE.md §OPAL Console | `docs/ARCHITECTURE.md` | Console 구조·배포 모델 |
| D-2 | 설계 | PROJECT.md 프로젝트 구성 | `docs/PROJECT.md` §주요 컴포넌트(L99-119), 원칙 §3 | Console FE=opal-fe-agent / BE=opal-be-agent, 플랫폼 독립성 |
| D-3 | 컨벤션 | CONVENTIONS.md | `docs/CONVENTIONS.md` §배포 경계(L200), Guards(L156) | 배포 경계·[MUST] 인용 규칙 |
| D-5 | 설계 | ANALYSIS.md (구조 분석) | `tasks/036-.../ANALYSIS.md` §1·§2·§3·§6·§7 | 변경지점·CORS 완화·brain 흐름·리스크·인용 (§4·§5 SDK 섹션 폐기) |
| D-6 | 소스 | run_tool 패턴 | `dashboard/backend/adapters/base.py:31` | subprocess·ToolError 3종 참조 (claude는 ok 필드 없어 자체 판정) |
| D-7 | 소스 | FE API 클라이언트 | `dashboard/frontend/src/lib/api.ts:19` | apiClient POST 패턴 |
| D-8 | 소스 | main.py CORS/host | `dashboard/backend/main.py:45,51-55,101` | allow_methods·라우터 등록·host 바인딩 |
| D-9 | 소스 | 기존 brain 부재 테스트 | `dashboard/backend/tests/test_routers.py:258-264` | test_no_brain_endpoints 갱신 대상 |
| D-10 | 설계 | red-first 트랙 SSOT | `opal/core/references/harness/red-first.md` | RED-first 적용 기준·작성자≠구현자 |
| D-11 | 설계·**원천 수정대상** | opal-brain(opbr) 스킬 **소스** | `opal/skills/opal-brain/SKILL.md` §모드 라우팅(L37)·§query(L274-296)·변경이력(L419-426) | query 동작·search 후보·진입점③ + **F-006 `--read-only` 계약 추가 대상**. (배포본 `~/.opal/skills/...` 직접편집 금지 — 소스만 수정, CLOSE install 재배포) |
| D-12 | 소스 | memory 라우터 프로젝트 경로 | `dashboard/backend/routers/memory.py:30` | `_find_project_path` 패턴(첫 OPAL 프로젝트 폴백) |

> 인용 형식: `opal/core/references/harness/citation-rules.md` §3.1. [MUST] 제약은 citation-rules §2.4.

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| 9-1 | opbr 쓰기 누수 (synthesis 파일링·draft term 등록·log) | F-006/F-003 | 높음 | **`--read-only` 계약(F-006)이 원천 차단** + 프롬프트 쓰기금지 + 질의 전후 `.opal/brain` 불변(TS-002·TS-036, S-4 PASS 실증) |
| 9-2 | 세션 성장/리셋 (컨텍스트 임계 초과) | F-003 | 중간 | turns/토큰 추정 임계 → 콜드 재프라임(TS-034) |
| 9-3 | 동시성 (단일 세션 동시 질의/prime) | F-003 | 높음 | threading.Lock 직렬화(TS-033) |
| 9-4 | 크래시 재프라임 (resume 실패) | F-000/F-003 | 높음 | reset 후 새 session-id 콜드 재프라임 1회 재시도(TS-035) |
| 9-5 | 부트스트랩 지연 (콜드 90.8s 실측) | F-000/F-003 | 중간(완화) | **prime-on-intent**(메뉴 진입 시 백그라운드 콜드 선흡수→질의 웜 20.2s). 콜드180/웜60 timeout. B1 확정(B2 기각) |
| 9-5b | prime-on-intent 경합 (prime 진행 중 질의) | F-003 | 중간 | priming 플래그 + 질의가 prime 완료 대기(중복 콜드 0 — TS-035b) |
| 9-6 | 출력 파싱 (preamble 오염·JSON펜스) | F-003 | 높음 | is_error/subtype 판정→502. **result서 JSON펜스만 발췌**(preamble 무시 — TS-032b). 펜스 실패→answer 폴백·citations 빈배열 |
| 9-7 | 구독 keychain 인증 파탄 (`--bare`/`--safe-mode`/API 키) | F-002/F-003 | 높음 | **[MUST]** 금지 플래그 부재 단언(TS-003·TS-037). 구독 keychain 유지 |
| 9-8 | 자동 테스트 실 구독 토큰 소모 | F-003 | 중간 | **[MUST]** 전 서브프로세스 mock(TS-038). 실 E2E는 L3 SUPERVISOR |
| 9-9 | 읽기전용 경계 누수 (5라우터 POST 우발 등록) | F-001 | 높음 | brain만 POST. grep 격리(TS-011) + 5라우터 405(TS-010) |
| 9-10 | `claude` 미설치/미인증 | F-002 | 높음 | which 경량 체크 graceful. FE 미인증 분기(폼 비노출) |
| 9-11 | brain 미초기화/검색 0건 | F-003 | 중간 | opbr "관련 페이지 없음" → graceful 200 안내(TS-039) |
| 9-12 | 데몬 외부 노출 | F-001/F-003 | 높음 | host=127.0.0.1 불변(TS-012). 0.0.0.0 금지 |
| 9-13 | 셸 인젝션(question→`//opbr query --read-only` 인자) | F-003 | 중간 | `subprocess.run(list, shell=False)` — 인자 배열, 셸 미경유(H-13) |
| 9-14 | 배포 경계 위반 | 전체 | 높음 | `dashboard/` + `opal/skills/opal-brain/` **소스만**. `~/.opal` 직접편집 0. install 재배포 1회는 캡틴 직접(L3, DECISION#25) |
| 9-15 | localStorage 이력 정합/쿼터 | F-005 | 낮음 | 직렬화 안전·쿼터 가드. session_id↔turns 정합(TS-054) |
| 9-16 | opbr `--read-only` 계약 누락/오정의 | F-006 | 높음 | SKILL 문서 검증(4계약 전수·ask 불변·v1.4 — TS-060·061) |
| 9-17 | 원천-콘솔 동시변경 발효 누락 (구버전 opbr 호출) | F-006/F-003 | 중간 | 콘솔 `--read-only` 호출 일관 + CLOSE install 재배포 1회 동시 발효(TS-062, 캡틴 L3) |
