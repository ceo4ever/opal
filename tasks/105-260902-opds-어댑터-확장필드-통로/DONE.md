# DONE: 플랫폼 sub-agent 어댑터 확장 필드 통로 신설 + effort 첫 적용

> 태스크: 105 | 스킬: opds | 모드: agentic | 착수 2026-09-02 18:13 → 마감 2026-09-03 13:15

## 1. 무엇을 했나

OPAL 에이전트 frontmatter를 플랫폼 sub-agent로 변환하는 install 어댑터가 `name`·`description`·`model` **3필드로 하드코딩**되어 있어, OPAL 측에 어떤 필드를 추가해도 배포 시점에 소실됐다. 이 emit 경로를 **선언적 JSON 스펙 순회**로 바꾸고, 그 위에 `effort`를 첫 확장 필드로 태웠다.

핵심 결과는 기능 자체보다 **검증 구조의 결함을 잡아낸 것**이다(§4).

## 2. 확정된 설계

### 통로의 형태

플랫폼 분기를 `OPAL_ADAPTER_FIELD_SPEC`(mac) / `$OpalAdapterFieldSpec`(windows) **단일 JSON 스펙 상수**에 가뒀다. emit은 배치 모드 3종에만 분기하며 **플랫폼명 조건문을 신규로 두지 않는다**.

| 배치 모드 | 의미 | 적용 |
|---|---|---|
| `key` | 독립 키로 출력 | Claude `effort` / Codex `model_reasoning_effort` |
| `model_param` | model 값에 파라미터 합성 | (예약 — Cursor 활성화 시) |
| `omit` | 출력하지 않음 | Gemini(미지원) · Cursor(정책 보류) |

### 스펙 필드 4종

| OPAL 키 | order | default | 비고 |
|---|---|---|---|
| `name` | 10 | 없음 | |
| `description` | 20 | 없음 | 공백 시 생략 |
| `model` | 30 | `standard` | 레벨→실모델 매핑 보유 |
| `effort` | 40 | **없음** | 미선언 시 pair 미생성 = 산출물 불변 |

### effort 값 도메인

| OPAL 값 | Claude | Codex |
|---|---|---|
| `minimal` | (미정의) | `minimal` |
| `low`~`xhigh` | 항등 | 항등 |
| `max` | `max` | **`xhigh`** (축약) |

미정의 값 입력 시 stderr 경고 + **해당 필드만 생략 + 종료코드 0** — install 전체를 중단시키지 않는다.

### 미러 규약의 승격

기존 "문자 단위 동일 정규식"이라는 **사람 규약**을, 센티넬 주석 구간의 **바이트 동일성 기계 검증**으로 바꿨다. 스펙 리터럴은 실제로 4곳(mac 전역 상수 1 + mac 함수 내 폴백 2 + windows 미러 1)에 존재하며, TS-011이 4곳 전수를 대조한다.

### Codex legacy alias 교체 (교체형)

`[agents] max_threads` → `max_concurrent_threads_per_session`. 단순 리터럴 교체로는 **기존 설치 머신이 영구히 legacy를 유지**한다는 사실(멱등 스킵 계약)을 PLAN이 발견해, 3분기 마이그레이션을 추가했다.

| 분기 | 조건 | 동작 |
|---|---|---|
| ① | `config.toml` 없음 | `[agents]` append |
| ② | 파일은 있으나 `[agents]` 없음 | 블록 신설, 타 블록 무손상 |
| ③ | `[agents]` + legacy 키 보유 | 해당 라인만 in-place 치환(값 보존) |

## 3. 변경 파일

| 파일 | 내용 |
|---|---|
| `scripts/install-mac.sh` | 스펙 상수 신설 + emit 테이블화 + codex 3분기 + `env` 경유 fix (v4.6~v4.8) |
| `scripts/install/windows.ps1` | 스펙 미러 + 전 키 수집 + pairs 순회 + codex 3분기 (v1.20.0~v1.21.0) |
| `opal/core/references/agents.md` | 변환 SSOT 표에 `effort` 행 + 「테이블 미등재 필드 = 제거」 정정 (v2.1) |
| `scripts/tests/test_agent_adapter_fields.sh` | **신규** — 15케이스 |
| `docs/ARCHITECTURE.md` | §배포 구조에 확장 필드 통로 서술 + codex 정정 |
| `docs/architecture-diagram/opal_framework_architecture.html` | legacy 키 표기 정정 |

## 4. 최대 산출 — 테스트 seam 결함

**단위 테스트 13/14 PASS인데 `install-mac.sh`가 한 줄도 실행되지 않는 상태가 있었다.**

- 원인: `:470`의 `readonly OPAL_ADAPTER_FIELD_SPEC`과 `:498`·`:819`의 커맨드 prefix-assignment가 같은 이름을 써서 `readonly variable` 오류
- **왜 안 걸렸나**: 테스트 하네스 `extract_fn`이 함수 본문만 추출해 독립 실행 → 전역 `readonly` 선언이 없는 컨텍스트라 충돌이 발생하지 않았다. 그 seam을 성립시키려 넣은 **함수 내 자기완결 폴백이 프로덕션과의 차이를 가렸다**
- 조치: `env` 경유 전달로 충돌 해소 + **하네스가 전역 센티넬을 먼저 로드하도록 seam 교정** + strict 기동 케이스 TS-024 신설
- **증명**: seam을 교정하자 fix 전 상태에서 TS-001·003·004·005·007·008·024가 전부 FAIL로 전환됐다. 교정된 seam이 이 버그를 잡는다는 것이 소급 확인됐다

> 교훈: **검증이 프로덕션 실행 형태와 다르면 통과 수치는 무의미하다.** 테스트를 위해 프로덕션에 없는 우회로(자기완결 폴백)를 만들면, 그 우회로가 곧 사각지대가 된다.

## 5. 검증 결과

| 스위트 | 결과 |
|---|---|
| `test_agent_adapter_fields.sh` | **15/15 PASS** |
| `test_archive_contents.sh` | 11/11 PASS |
| `test_version_stamp.sh` | 11/11 PASS |
| `bash -n scripts/install-mac.sh` | OK |
| 컨벤션 진단 | **Critical 0 / High 0** (Info 3, 조치 불요) |

### 실환경 실측 (install 재배포)

| 항목 | 결과 |
|---|---|
| 미선언 에이전트 산출물 | 차이 1건(`opal-test-agent`) — **미배포 소스 드리프트(커밋 `9d2644e`)로 전량 설명**, frontmatter 무변경 |
| 프로브 effort 도달 | Claude `effort: high` / Codex `model_reasoning_effort = "high"` / Gemini·Cursor **키 부재** |
| 프로브 회수 | 5경로 잔존 **0건**, 파일 수 15/21/16/15 복귀 |
| `~/.codex/config.toml` | `max_concurrent_threads_per_session = 6`, legacy 0건, `[hooks.state]` 무손상 |
| `codex doctor` | **17 ok · 1 idle · 1 notes · 0 warn · 0 fail** |

### 미검증 1건 (이월)

**S-14 Windows 런타임 검증** — 본 환경에 `pwsh` 미설치(실측)로 실행 불가. 정적 검증(TS-011 스펙 바이트 미러 / TS-014 PS7 구문 스캔)으로 대체했으나, **정적 미러 일치가 런타임 동치를 보장하지 않는다** — H-5(`ConvertFrom-Json`의 `PSCustomObject` 인덱싱 실패 유형)는 정적 스캔으로 배제되지 않는다. Windows 머신에서 `scripts/install/windows.ps1`을 1회 실행해 frontmatter 블록을 mac 산출물과 대조해야 R-4가 완결된다.

## 6. 태스크 도중 변경된 수용기준

**R-6 AC(a)** 「`grep -rn 'max_threads' scripts/` 0건」은 **원리적으로 충족 불가**였다 — legacy 키를 탐지·치환하는 로직이 그 리터럴을 품어야 동작하기 때문이다. 잔존 16곳은 전부 탐지 정규식·주석·변경이력·성공 메시지·테스트 픽스처이며 **install이 기록하는 키는 한 곳도 없었다**.

- 판정 대상을 **"소스 텍스트" → "install이 기록한 결과 파일"**로 이전 (캡틴 승인, 2026-09-02)
- 문자열 난독화(`'max_' + 'threads'`)는 금지로 명시 — 동작을 두고 판정만 속이는 방식이다
- 워커가 난독화를 거부하고 소견 보고로 올린 판단이 타당했다
- 잠긴 AC의 사후 수정이므로 `TASK.md` `[결정]` 항목에 승인 사실·날짜·사유를 기록해 추적 가능하게 했다

> 근본 원인은 AC 표현 방식이다 — 교체형 목표의 "구형 잔존 0"을 **소스 grep**으로 쓴 것. 산출물 기준으로 썼다면 문제가 없었다.

## 7. PM 대행 기록 요약

| 항목 | 건수 |
|---|---|
| 게이트 판단 | 9회 (전건 Pass, 예외 1건 명시) |
| 오류 발견 | 7건 |
| 수정 지시 | 5건 (전건 반영) |
| PM 의사결정 | 8건 |
| 에스컬레이션 | 1건 (캡틴 승인으로 해소) |

상세: `AGENTIC-LOG.md` (36행)

### 워커 산출물에서 잡은 결함 (검출 7건 중)

1. PLAN 내부 모순 — Step 8이 `~/.opal/` 직접 배치를 지시하면서 §9는 그것을 금지
2. TS-005 테스트 구현이 PLAN 설계를 미이행 (원천적으로 통과 불가한 검사)
3. 스펙 리터럴 4곳 중 2곳만 자동 검증 (PM 자신의 "3곳" 오보고 포함)
4. S-13 판정 기준이 정상 환경을 막음 (고아 `wtm-agent.md` 미반영)
5. readonly 충돌로 install 실행 불가
6. 테스트 seam이 프로덕션과 불일치 (§4)
7. R-6 AC 자기모순 (§6)

### PM 자기 과실 1건

워커의 install이 백그라운드로 돌 가능성을 확인하지 않고 PM이 Run C install을 실행해 **동시 실행 충돌 위험**을 만들었다. 워커가 이를 감지해 "두 install 결과를 확인해야 한다"고 지적한 것이 정확했다. 최종 상태는 PM이 재실측해 확정했다.

## 8. 이월 사항

| # | 항목 | 사유 |
|---|---|---|
| 1 | **S-14 Windows 런타임 검증** | `pwsh` 미설치 — Windows 머신에서 수동 확인 필요 |
| 2 | **에이전트별 effort 값 배정** | 통로와 값의 분리 원칙. 통로 검증이 끝나 이월 사유는 해소됨 |
| 3 | OPAL effort 레벨 정의 문서화 | `opal-model-mapping.md`와 나란히 6단(`minimal`~`max`) 용도·특성 명문화 |
| 4 | effort 매핑의 `setting.json` 이전 | 현재 install 스크립트에 하드코딩. 어댑터의 "스펙 자기포함" 규약과 충돌하므로 설계 재검토 필요 |
| 5 | 고아 어댑터 `wtm-agent.md` 2건 | cursor·gemini. 소스 개명(`opal-wtm-agent`) 후 잔존. 어댑터 디렉토리가 `clean_dirs` 미포함 |
| 6 | **install 동기 실행 금지 명문화** | 프론트엔드 빌드 포함 수 분 소요 → 도구 타임아웃 초과로 워커 2회 스톨. Step 8류 절차에 반영 필요 |
| 7 | 어댑터 전용 재생성 경로 분리 | 검증 목적에 전체 install(프론트엔드 재빌드 포함)은 과도 |
| 8 | `CONVENTIONS.md` 셸 변경이력 규정 | 현 규정이 "스킬·에이전트·참조 문서"만 명시, 셸/PowerShell 스크립트 공백 |
| 9 | mac/windows Codex 경로 비대칭 | mac은 본문 model 토큰 변환 미적용, windows는 적용. 이번에 고치면 바이트 동일성 제약과 충돌 |
| 10 | `opal-be-agent`·`opal-task-agent` 모델 강등 | 대화 중 검토했으나 2026-06-21 캡틴 결정의 번복이라 확인 미수령 상태로 보류 |

## 9. 미수행

- **커밋** — 워킹트리에만 변경이 남아 있다. 커밋·머지는 캡틴 권한.
