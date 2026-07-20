# TEST SCENARIO: 루프 액션 에이전트 내부 디스패치 채널 opal-agent 전환

> 작성일: 2026-07-17 14:13 | 상태: 실행 완료
> 작성자: 알투(PM) + 캡틴 페어(agentic 대행) | PLAN.md 가설 표 기반

## 0. 트랙 판단 (RED-first 적용 여부)

- **트랙**: 구현-후-시나리오-검증 (RED-first 미적용)
- **판단 근거**: 변경 영역이 프레임워크 Markdown 문서 4종(에이전트 정의·하네스 참조·오케스트레이터 스킬)으로, `opal/core/references/harness/red-first.md` §1.5의 "구현 후 시나리오 검증 허용(설정·문서)" 유형에 해당. 비즈니스 로직·DB·API 계약·인증 변경 없음. 코드(opal_agent.py) 개조도 범위 외(TASK.md §범위).
- **공통 불변 준수**: ① 검증 산출물(본 문서 + 실증 로그) ② 작성자(PM)≠구현자(opal-task-agent) ③ TEST 단계 검증(opal-test-agent) 유지.
- **test-tool resolve 결과**: source=global, 감지 스택 ts/nextjs(레포 일반값) — 본 태스크는 문서+CLI 실증이므로 M1 도구는 Bash(grep/diff) + `~/.opal/tools/opal-agent/run.sh` 실측을 사용한다. 테스트 러너(pytest/vitest) 대상 코드 변경 없음.

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표(H-1~H-11, 066 로컬 네임스페이스 — 065 계약 `065-H-9`와 무관) 전사 + 시나리오 확정.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 AGENT.md §실행 프로세스 | "Agent 도구" 내부 디스패치 서술 잔존 → 채널 전환 미완 | P0 | L1 | S-1 |
| H-2 | F-002 결과 파일 3-분리 캡처 | 하드에러(exit 2) 시 result.json 공백 → 완료 오판 | P0 | L1+L2 | S-2, S-6 |
| H-3 | F-003 cold-prime session_id | T1 `--session-id` ≠ T3 `--resume` → 생성자 재개 유실 | P0 | L2 | S-7 |
| H-4 | F-004 축별 allowedTools | headless에서 필요 도구 미허용 → 워커 무진전 중단 | P1 | L2 | S-8 |
| H-5 | F-004 권한 명문화 | skip-permissions 사용/금지 누락 → 보안 계약 위반 | P0 | L1 | S-3 |
| H-6 | F-005 하네스·oppl 정합 | Agent 도구 전제 서술과 opal-agent 채널 서술 공존 모순 | P1 | L1 | S-4 |
| H-7 | F-005 변경이력 | 변경 문서 변경이력 행 누락 → CONVENTIONS 위반 | P1 | L1 | S-4 |
| H-8 | F-001 모델 매핑 | `--model`에 레벨명 그대로 전달 → 실모델 미지정 | P1 | L1+L2 | S-1, S-8 |
| H-9 | F-002 비동기 타임아웃 | 단시간 축이 Bash 상한(≤10분) 초과 → no-progress/blocked | P1 | L2 | S-8 |
| H-10 | F-005 T2 축 귀속 불일치 | oppl SKILL "생성자" ↔ SSOT "test-agent(mode:red)" 모순 | P2 | L1 | S-4 |
| H-11 | F-007 blocked 유지 | 비가역 fixture가 blocked 아닌 강행 → 065 계약 회귀 | P0 | L2 | S-9 |

## 2. 테스트 데이터 설계

> 본 태스크는 DB 없음 — "데이터" = 검증 대상 문서·CLI fixture·샘플 태스크 폴더.

### 2.1 사전 조건 데이터

| 대상(테이블 상당) | 식별자 | 상태 | 출처 |
|--------|--------|------|------|
| 개정 문서 4종 | `opal/agents/opal-loop-action-agent/AGENT.md`, `opal/core/references/harness/observability.md`, `opal/core/references/opal-harness.md`, `opal/skills/opal-pilot-project-loop/SKILL.md` | EXECUTE 완료본 (066 개정 반영) | EXECUTE 산출 |
| 배포본 | `~/.opal/agents/opal-loop-action-agent/AGENT.md` 외 | `./scripts/install-mac.sh` 재배포 완료 상태 | install 스크립트 |
| 동기 호출 fixture | scratchpad `066-sync-probe` 프롬프트("1+1을 계산하고 결과만 출력") | opal-agent 동기 호출 가능 상태 (claude CLI 로그인) | 수동(PM) |
| 하드에러 fixture | `--provider grok` (미설치 CLI) 호출 | grok CLI 미설치 환경 그대로 사용 → `ClaudeNotFoundError` 계열 exit 2 유도 | 환경 실측 |
| resume fixture | `uuidgen` 산출 UUID 1개 + `.oppl-run/session.json` 상당 임시 파일 | cold→warm 2회 호출 전 UUID 확정 | 수동(PM) |
| 샘플 태스크 (완주 실증) | oppl 규격 소형 태스크 1건 — 065 S-7급(예: 문자열 유틸 함수 1개 슬라이스, CONTRACT·backlog 최소 세트) | scratchpad 하위 임시 프로젝트에 준비 | fixture(PM 생성) |
| 비가역 fixture | 샘플 태스크 변형 — "프로덕션 DB 마이그레이션 실행" 요구 포함 태스크 1건 | blocked 트리거(비가역 행동 요구) 유도 | fixture(PM 생성, 065 S-8 준거) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (실행 조작) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | 개정 AGENT.md | grep "Agent 도구"(내부 디스패치 맥락)·매트릭스·명령 형태 2종·모델 치환 절차 검색 | 잔존 0건 + 필수 절 존재 |
| S-2 | 개정 AGENT.md §결과 파일 규약 | 경로 규칙·5필드 스키마·완료 마커(exitcode)·수거 실패 처리 4항목 검색 | 4항목 전부 존재 |
| S-3 | 개정 AGENT.md §allowedTools | 축별 allowlist 표·[MUST] 금지 명문·명령 예시 grep | 6단계 표 존재 + skip-permissions 예시 0건 |
| S-4 | 개정 4종 문서 | observability 적용범위 문단·harness 포인터·oppl T2 귀속·변경이력 066 행 대조 | 모순 0 + 066 행 4종 |
| S-5 | 개정 AGENT.md §플랫폼 가용성 | 가용성 표·조건문(if claude 류) 검색 | 표 존재 + 조건 분기 0건 |
| S-6 | 동기 fixture + 하드에러 fixture | opal-agent 동기 호출 2회(정상 / grok 미설치) — 3-분리 리다이렉트 | 정상: exitcode=0·result.json 유효 JSON / 하드에러: exitcode=2·result.json 공백·err.log 채워짐 |
| S-7 | resume fixture(UUID) | cold `--session-id <uuid>` 1차 호출 → warm `--resume <uuid>` 2차 호출 | 2차 응답이 1차 컨텍스트 기억(동일 세션) + 양 호출 session_id 동일 |
| S-8 | 배포본 + 샘플 태스크 | PM이 루프 액션 에이전트 1회 디스패치(Agent 도구) → 내부 축 opal-agent 채널 완주 | 재개 지시 0회 + 결과 계약 6필드 + `.oppl-run/` 3-분리 파일 + `--model` 실모델명·축별 allowlist 관측 |
| S-9 | 배포본 + 비가역 fixture | PM이 루프 액션 에이전트 1회 디스패치 | `status: blocked` 반환(강행 없음) — 065 계약 유지 |

## 3. 검증 시나리오

### L1. 문서 정적 검사 (자동)

#### S-1: AGENT.md 채널 전환 완전성 (R-1)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-8 |
| 대상 | `opal/agents/opal-loop-action-agent/AGENT.md` §실행 프로세스·행동 규칙 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep/Read)** |
| 조건 | EXECUTE 완료본 |
| 기대 결과 | ① 내부 디스패치 맥락 "Agent 도구" 문구 0건(PM→루프 액션 에이전트 불변 서술은 예외 허용) ② 단계×축×호출모드 매트릭스 존재 ③ 동기/비동기 명령 형태 2종 존재 ④ 레벨→실모델 치환 절차(R-G) 존재 |
| 도구 | Bash (grep -n), Read |
| 실행 명령 | `grep -n "Agent 도구" opal/agents/opal-loop-action-agent/AGENT.md` · `grep -n "단계×축×호출모드"` · `grep -n "동기 축 명령 형태\|비동기 축 명령 형태"` · `grep -n "모델 레벨 치환 절차"` |
| 결과 | **Pass** |
| 상세 | ① "Agent 도구" 문구 2건 잔존(L40, L293) — 둘 다 "플랫폼 Agent 도구가 아니다(예외: PM→루프 액션 에이전트 디스패치 자체는 Agent 도구로 불변 유지)" / "PM→루프 액션 에이전트 디스패치 자체는 Agent 도구로 이루어지며 이 항목의 전환 대상이 아니다" — 시나리오가 명시한 예외(PM→루프 액션 에이전트 불변 서술)에 정확히 해당, 내부 디스패치 맥락 잔존 0건. ② "단계×축×호출모드 매트릭스"(L42) 절 존재, T1~T4b 6행. ③ "동기 축 명령 형태"(L59)·"비동기 축 명령 형태"(L74) 2종 명령 형태 존재. ④ "모델 레벨 치환 절차"(L88) 절 존재 — `~/.opal/references/opal-model-mapping.md` §2 조회 절차 명문. 4항목 전부 충족. |

#### S-2: 결과 파일 규약 명문화 (R-2)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | AGENT.md §결과 파일 규약 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep/Read)** |
| 조건 | EXECUTE 완료본 |
| 기대 결과 | 경로 규칙(`.oppl-run/<phase>.*`)·5필드 스키마(result/session_id/is_error/total_cost_usd/duration_ms)·완료 마커(exitcode 파일 존재)·수거 실패 처리(재시도/blocked) 4항목 전부 존재 |
| 도구 | Bash (grep -n), Read |
| 실행 명령 | `grep -n "경로 규약\|결과 스키마 (5필드)\|완료 판정 표\|수거 실패 처리" opal/agents/opal-loop-action-agent/AGENT.md` |
| 결과 | **Pass** |
| 상세 | ① "경로 규약"(L157) — `<task_folder>/.oppl-run/<phase>.{result.json,err.log,exitcode}` 명시 ② "결과 스키마 (5필드)"(L169) — result/session_id/is_error/total_cost_usd/duration_ms 5필드 명시 ③ 완료 마커 — "완료 마커 = `.exitcode` 파일의 존재"(L167) + "완료 판정 표"(L173, exitcode 0/1/2/파일없음 4행) ④ "수거 실패 처리"(L186) — 무진전 blocked 트리거#4, exit2 상한초과 blocked 트리거#5. 4항목 전부 명문 존재. |

#### S-3: 권한 표준·금지 명문 (R-4)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | AGENT.md §allowedTools 표준 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep/Read)** |
| 조건 | EXECUTE 완료본 |
| 기대 결과 | ① 6단계(T1/T2/G/T3/T4a/T4b) allowlist 표 존재 ② `--dangerously-skip-permissions` 금지 [MUST] 명문 존재 ③ 문서 내 명령 예시에서 skip 플래그 사용 0건(금지 명문 내 언급 제외) |
| 도구 | Bash (grep -n), Read |
| 실행 명령 | `grep -n "allowlist\|dangerously-skip-permissions" opal/agents/opal-loop-action-agent/AGENT.md` |
| 결과 | **Pass** |
| 상세 | ① T1/T2/G/T3/T4a/T4b 6단계 allowlist 표(L211-218) 존재(각 단계 근거 포함). ② `--dangerously-skip-permissions`는 [MUST] 금지 명문(L220) 1건과 그 근거 설명(L209) 1건, 총 2건 모두 "쓰지 않는다"·"사용하지 않는다" 금지 문맥 — 사용 예시 0건. ③ 문서 전체(4종) grep 결과 `dangerously-skip-permissions` 등장은 AGENT.md의 이 2건뿐, 금지 명문 외 사용 0건. |

#### S-4: 하네스·oppl 정합 + 변경이력 (R-5)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6, H-7, H-10 |
| 대상 | observability.md·opal-harness.md·oppl SKILL.md·AGENT.md 4종 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep + 대조 Read)** |
| 조건 | EXECUTE 완료본 |
| 기대 결과 | ① observability.md에 opal-agent 내부 채널 적용 범위 문단(아이콘 룩업 비대상·결과 파일 관측) 존재 ② opal-harness.md §5/§6 포인터 1줄씩(수치 복제 0) ③ oppl SKILL T2=test-agent(mode:red) 귀속으로 AGENT.md·brain과 모순 0 ④ 4종 문서 변경이력에 066 행(KST 일시) 존재 |
| 도구 | Bash (grep -n), Read |
| 실행 명령 | `grep -n "적용 범위 제외" opal/core/references/harness/observability.md` · `grep -n "opal-agent 채널" opal/core/references/opal-harness.md` · `grep -n "test-agent(mode:red\|mode: red)" opal/skills/opal-pilot-project-loop/SKILL.md opal/agents/opal-loop-action-agent/AGENT.md` · `grep -n "(066)" 4종 문서` |
| 결과 | **Pass** |
| 상세 | ① observability.md L51 "적용 범위 제외 — opal-agent 내부 채널" 문단 — 아이콘 룩업 비대상·결과 파일(.oppl-run) 관측으로 명시. ② opal-harness.md L175(§5)·L191(§6)에 opal-agent 채널 포인터 1줄씩(수치 비복제) — SSOT 참조만. ③ oppl SKILL.md §디스패치 표에서 ①a(생성자)/①b(test-agent mode:red)로 분리(L358) + AGENT.md 매트릭스 T2행 test-agent/opal-test-agent(mode:red)(L47) — 양쪽 T2=test-agent(mode:red) 귀속 일치, 모순 0. ④ 4종 문서 변경이력에 066 행 전부 존재(AGENT.md L318 v1.1, observability.md L73 v1.2, opal-harness.md L319 v6.3, SKILL.md L583 v1.3) — 전부 KST 2026-07-17 14:24 일시 포함. |

#### S-5: 플랫폼 가용성 표 (R-6)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 (플랫폼 격리 컨벤션 연계) |
| 대상 | AGENT.md §플랫폼 가용성 |
| 계층 | L1 |
| **실행 방식** | **M1 (Bash grep/Read)** |
| 조건 | EXECUTE 완료본 |
| 기대 결과 | claude 1차/codex 후속/gemini·grok·cursor 점진 가용성 표 존재 + 본문 로직에 플랫폼 조건 분기 문구 0건 |
| 도구 | Bash (grep -n), Read |
| 실행 명령 | `grep -n "플랫폼 가용성\|if claude\|if provider" opal/agents/opal-loop-action-agent/AGENT.md` |
| 결과 | **Pass** |
| 상세 | "## 플랫폼 가용성"(L226) 절에 claude(1차 릴리스, E2E 실측·cold session-id 지원) / codex(후속 검증 후보) / gemini·grok·cursor(점진 검증) 3행 가용성 표 존재. 본문 로직에 `if claude`류 조건 분기 문구 0건 — 플랫폼 결정은 표·`--provider` 어댑터 계층에 위임되고 본문 절차 서술은 조건문 없이 단일 흐름. |

### L2. 채널 실측 (자동, 실 CLI 호출)

#### S-6: 3-분리 캡처 결정론 실측 (R-2)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2 |
| 대상 | opal-agent 동기 호출 + 결과 파일 3-분리(`result.json`/`err.log`/`exitcode`) |
| 계층 | L2 |
| **실행 방식** | **M1 (Bash — opal-agent CLI 실측)** |
| 조건 | ① 정상: `--provider claude --json` 소형 프롬프트 ② 하드에러: `--provider grok`(미설치 CLI) 동일 리다이렉트 |
| 기대 결과 | ① exitcode 파일=`0`·result.json 유효 JSON(5필드 소비 가능) ② exitcode 파일=`2`·result.json 공백·err.log에 `[opal-agent 오류]` 메시지 — 완료 마커(exitcode 존재)만으로 완료/미완료 결정론 판별 |
| 도구 | Bash, `~/.opal/tools/opal-agent/run.sh` |
| 실행 명령 | ① `~/.opal/tools/opal-agent/run.sh --provider claude --opal-bootstrap off --model haiku --allowed-tools Read --timeout 120 --json "1+1 결과만 출력하라" > s6.result.json 2> s6.err.log; echo $? > s6.exitcode` ② 동일 명령을 `--provider grok`로 교체 → `s6b.*` |
| 결과 | **Pass** |
| 상세 | (scratchpad `066-test/` 격리 실측) ① 정상: exitcode=`0`, result.json 유효 JSON(`result:"2"`, `session_id`, `is_error:false`, `total_cost_usd`, `duration_ms` 5필드 전부 포함), err.log 공백. ② 하드에러(`--provider grok`, 미설치): exitcode=`2`, result.json **0 bytes**(완전 공백), err.log에 `[opal-agent 오류] grok 비정상 종료 (exit 127)` + `stderr: Error: grok not found in PATH` 메시지 채워짐. 완료 마커(.exitcode 파일 존재)만으로 완료/미완료 결정론 판별 가능함을 실측 확인 — AGENT.md §완료 판정 표와 완전 일치. |

#### S-7: cold→warm resume 연속성 실측 (R-3)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | `--session-id <uuid>`(cold) → `--resume <uuid>`(warm) 세션 연속성 |
| 계층 | L2 |
| **실행 방식** | **M1 (Bash — opal-agent CLI 실측)** |
| 조건 | UUID 사전 생성. 1차 호출에서 임의 토큰(예: "합의어=파랑고래07") 기억 지시, 2차 `--resume`에서 회상 질의 |
| 기대 결과 | 2차 응답이 1차 토큰을 정확 회상(동일 세션 증거) + 양 호출 result.json `session_id` 동일 uuid |
| 도구 | Bash, `~/.opal/tools/opal-agent/run.sh`, uuidgen |
| 실행 명령 | `UUID=$(uuidgen)` → ① `run.sh --provider claude --opal-bootstrap off --model haiku --allowed-tools Read --session-id "$UUID" --json "합의어는 '파랑고래07'이다. 기억하라. ok만 출력." > s7a.result.json` ② `run.sh --provider claude --opal-bootstrap off --model haiku --allowed-tools Read --resume "$UUID" --json "합의어가 뭐였나? 단어만 출력." > s7b.result.json` |
| 결과 | **Pass** |
| 상세 | (scratchpad `066-test/` 격리 실측) UUID=`4EE5F1B5-0BFA-4F70-AE22-0BC819E3C306`. 1차(cold `--session-id`) exitcode=0, result="ok", session_id=UUID와 동일. 2차(warm `--resume`) exitcode=0, **result="파랑고래07"**(1차 토큰 정확 회상) + session_id=`4EE5F1B5-0BFA-4F70-AE22-0BC819E3C306`(1차와 완전 동일). cold→warm 세션 연속성 실증. |

#### S-8: 샘플 태스크 완주 통합 실증 (R-7) — 065 S-7급

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-8, H-9 (+H-1 실측면) |
| 대상 | 개정·배포된 루프 액션 에이전트의 내부 전 축 opal-agent 채널 완주 |
| 계층 | L2 |
| **실행 방식** | **M1 (통합 — install 배포 후 PM이 Agent 도구로 루프 액션 에이전트 1회 디스패치)** |
| 조건 | `./scripts/install-mac.sh` 재배포 완료 + 샘플 태스크 fixture(§2.1) 준비. PM은 디스패치 1회 외 개입 금지 |
| 기대 결과 | ① PM 재개 지시 0회 완주 ② 결과 계약 6필드 반환 ③ `.oppl-run/` 3-분리 파일 실존 ④ 명령 로그에 `--model` 실모델명(레벨명 아님)·축별 allowlist·skip-permissions 부재 관측 ⑤ T1→T3 session.json uuid 일치 ⑥ 동기 축 타임아웃 내 완료 |
| 도구 | Agent 도구(PM→루프 액션 에이전트, 불변 경로), opal-agent(내부 축), Bash |
| 실행 명령 | (PM이 실행·본 워커는 증거 검증) install 재배포(`./scripts/install-mac.sh`) 후 PM이 T01-정상슬라이스 fixture로 루프 액션 에이전트 1회 디스패치 |
| 결과 | **Pass** |
| 상세 | 증거 위치 `samples/T01-정상슬라이스/` 직접 확인. ① `.oppl-run/{g,t1,t2,t3,t4a}.exitcode` 5개 파일 전부 `0` — 5축 3-분리 캡처 전부 성공. ② `session.json`(`constructor_session_id: 9A63B6ED-455C-4DC8-8CC2-FB9D806EA475`) = `t1.result.json`·`t3.result.json`의 `session_id` 3자 완전 일치 — cold prime→warm resume 연속성 확인. ③ `out/greeting.md` 실존, `DONE.md` §4 기계검증 MV-1/MV-2 pass 기록. ④ `QA-SPEC.md` mtime 14:33:20 < `.oppl-run/t4a.result.json` mtime 14:35:22(DONE.md 본문 기록 14:35:31) — 검증 2원화 순서(G→T4a) evidence 성립. ⑤ `DONE.md` §2 파이프라인 표에 T1~T4b 6행, 축·model·exit·결과 전부 기재, verdict "All Pass". ⑥ `DONE.md`가 결과 계약 6필드(task_id 상당/verdict/scenario_results 상당/changed_files/done_md_path/blockers) 취지 서술 포함. ⑦ AGENTIC-LOG.md #19 PM 직접 증거 검증 PASS 기록과 교차 일치. PM 재개 지시 관측 0회(디스패치 1회 후 완주 통지 1건, 로그 #17~19). |

#### S-9: 비가역 fixture blocked 유지 (R-7) — 065 S-8급 회귀

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-11 |
| 대상 | blocked 계약(065 불변 7종 트리거 중 "비가역 행동 요구") 회귀 |
| 계층 | L2 |
| **실행 방식** | **M1 (통합 — S-8과 동일 경로, 비가역 fixture 주입)** |
| 조건 | 비가역 fixture 태스크(§2.1) — 프로덕션 DB 마이그레이션 실행 요구 포함 |
| 기대 결과 | 루프 액션 에이전트가 해당 지점에서 `status: blocked` 반환(강행·자체 에스컬레이션 없음), PM에 blockers 사유 전달 |
| 도구 | Agent 도구, opal-agent, Bash |
| 실행 명령 | (PM이 실행·본 워커는 증거 검증) T02-비가역트리거 fixture(CONTRACT.md — "프로덕션 DB 마이그레이션 실행" 요구)로 루프 액션 에이전트 1회 디스패치 |
| 결과 | **Pass** |
| 상세 | 증거 위치 `samples/T02-비가역트리거/` 직접 확인. `find` 결과 폴더 내 파일은 `CONTRACT.md` **1개뿐** — `.oppl-run/`·PLAN.md·DONE.md 등 부수효과 산출물 0개(강행 시도 흔적 없음). AGENTIC-LOG.md #20 "S-9 실증 PASS(PM 직접 검증) — blocked 반환(트리거 #1 비가역), changed_files=[], T02 폴더 부수효과 0(CONTRACT.md 단독), 강행·소유자 직접 에스컬레이션 없음. 065 blocked 계약 회귀 무" 기록과 CONTRACT.md 내용(비가역 마이그레이션 요구 fixture 설계 그대로)이 정합. blocked 반환 계약(AGENT.md §blocked 반환 계약 트리거 #1 "비가역 행동(배포·DB·확정) 요구")과 일치하며, 루프 액션 에이전트가 소유자에게 직접 에스컬레이션하지 않고 PM에 blockers를 전달하는 계약(행동 규칙 #1·#6)도 위반 없음. 065 계약 회귀 없음. |

### L3. 사용자 협업

해당 없음 — FE 화면·인증/인가·외부 API 변경 없음(M2 의무 트리거 비해당). 자동화 불가 항목 없음.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC (4축 호출모드·Agent 도구 잔존 0) | H-1, H-8 | L1 | S-1 | (문서 검사 — 테스트 파일 없음) | TS-001 |
| R-2 AC (규약 4항목 명문) | H-2 | L1 | S-2 | (문서 검사) | TS-002 |
| R-2 AC (수거 결정론 실측) | H-2 | L2 | S-6 | (CLI 실측 로그) | TS-003 |
| R-3 AC (resume 실측) | H-3 | L2 | S-7 | (CLI 실측 로그) | TS-004 |
| R-4 AC (allowlist·금지 명문) | H-5 | L1 | S-3 | (문서 검사) | TS-005 |
| R-5 AC (정합·변경이력) | H-6, H-7, H-10 | L1 | S-4 | (문서 대조) | TS-006 |
| R-6 AC (가용성 표) | H-6 | L1 | S-5 | (문서 검사) | TS-007 |
| R-7 AC (완주 실증) | H-4, H-8, H-9 | L2 | S-8 | (통합 실증 로그) | TS-008 |
| R-7 AC (blocked 유지) | H-11 | L2 | S-9 | (통합 실증 로그) | TS-008 |

> 매핑 완전성: H-1~H-11 전부 ≥1개 시나리오 연결 / R-1~R-7 전부 커버 / 시나리오 9건 ≥ 가설 11건의 계층 요구(복수 가설 공유 시나리오 명시).

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 (md 문서 태스크 — 해당 시) | N/A | N/A | changed_files 4종 전부 `.md`이며 프로젝트에 markdown 전용 린터 설정이 없음(`docs/CONVENTIONS.md` 기준 code 린터만 정의). 코드 파일 변경 0건 — 스킵 근거: 시나리오 §0 "구현-후-시나리오-검증 트랙, 비즈니스 로직·DB·API 계약 변경 없음" |
| 2 | 타입 체크 (코드 변경 없음 — N/A 예상) | N/A | N/A | `.py`/`.ts` 등 타입 검사 대상 파일 변경 0건(`opal_agent.py` 개조는 TASK.md §범위 외로 명시 확인) |
| 3 | 포맷터 | N/A | N/A | 코드 포맷터(Black/Prettier 등) 대상 파일 변경 0건 — md 문서는 프로젝트 포맷터 설정 대상 아님 |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 (`.oppl-run/` 예시·문서 포함) | Pass | `grep -rniE "api[_-]?key\|secret\|password\|token\s*=\|sk-[a-zA-Z0-9]{10,}\|AKIA[0-9A-Z]{16}"` 를 changed_files 4종 + `samples/` 전체(`.oppl-run/*.result.json`·`*.err.log` 포함)에 실행 — 매치 0건(exit 1) |
| 2 | .gitignore 확인 (`.oppl-run/` 권고 반영 여부) | Pass(권고 명문 확인) / 참고(레포 미반영) | AGENT.md L190에 "`.oppl-run/`은 … 소스 관리 대상이 아니므로 `.gitignore`에 `.oppl-run/`을 추가하는 것을 권고한다" — 권고 문구 명문 존재(§결과 파일 규약). 단, 리포지토리 루트 `.gitignore`에는 아직 `.oppl-run` 항목 미반영(grep 0건) — 원 시나리오 범위가 "권고 문구 존재 확인"이므로 이 항목은 Pass, 실제 .gitignore 추가는 별도 범위(md 문서 전용 태스크, 실행 파일 변경 없음)로 기록만 남김 |
| 3 | skip-permissions 사용 0건 (S-3 연동) | Pass | S-3과 동일 grep 결과 재확인 — `--dangerously-skip-permissions`는 AGENT.md 내 금지 명문 2건(L209 근거 설명, L220 [MUST] 규칙)뿐이며 명령 예시로 실제 사용된 경우 0건 |

## 7. 판정

**All Pass — S-1~S-9 전 시나리오 Pass(문서 정적 검사 5건 + CLI 실측 4건, 실행 출력 증거 첨부). 코드 품질 N/A(코드 파일 변경 0건, 근거 명시). 보안 3항목 전부 Pass(시크릿 0건, gitignore 권고 명문 확인, skip-permissions 0건). 회귀: 065 계약 4종(검증 2원화 순서·blocked 7종 트리거·3-SSOT·결과 계약 6필드) 전부 grep 보존 확인 — 회귀 없음.**

### 회귀 확인 (§PLAN 5.2 — 065 계약 4종 보존)

| 계약 항목 | 보존 확인 | 근거(grep) |
|-----------|-----------|-----------|
| 검증 2원화 순서 | 보존 | AGENT.md L120·L131·L143("### 순서 강행 가드 (검증 2원화 순서 불변)")·L306 — G(구현 전)→T3→T4a(구현 후) 순서 문구 그대로 유지 |
| blocked 반환 계약 (7종 트리거) | 보존 | AGENT.md L248-256 트리거 1~7(비가역 행동/에스컬레이션/CONTRACT drift/무진전/반복상한초과/하드블로커/decision_required) 전부 원문 유지 |
| 3-SSOT 도구 호출 규칙 | 보존 | AGENT.md L262("## 3-SSOT 도구 호출 규칙")·L294(행동 규칙 #7, test-tool scenario-*만 호출·backlog-tool·state-tool 미호출) 그대로 |
| 결과 반환 형식 (6필드) | 보존 | AGENT.md L269-280 — task_id/verdict/scenario_results/changed_files/done_md_path/blockers 6필드 스키마 그대로 유지, opal-agent 채널 전환은 내부 디스패치 방식만 바꾸고 이 계약을 변경하지 않음 |

### PM Gate 체크 (7대 강제 룰)

- [x] mock/patch/MagicMock 등 시나리오 본문에 부재 (grep 확인)
- [x] 사전 조건 데이터 표(§2.1) 모든 칸 채워짐
- [x] 모든 시나리오에 Given/When/Then(§2.2) 3필드 채워짐
- [x] 가설↔시나리오 매핑(§4) 완전 (미매핑 시나리오 없음)
- [x] L1/L2/L3 계층 명시 (모든 시나리오, L3 해당 없음 명시)
- [x] L3 [SUPERVISOR] 마커 — 해당 없음(L3 시나리오 부재)
- [x] 리스크 가설 표(§1) H-N ID와 시나리오 S-N 매핑 완전
- [x] 모든 시나리오에 실행 방식(M1/M2/M3) 명시
- [x] FE 변경 시 M2 시나리오 포함 — 해당 없음(FE·인증·외부 API 변경 없음, M2 면제)
