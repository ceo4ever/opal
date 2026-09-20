# TEST SCENARIO: 플랫폼 sub-agent 어댑터 확장 필드 통로 신설 + effort 첫 적용

> 작성일: 2026-09-02 | 상태: 작성 완료
> 작성자: PM + 캡틴 페어 | 선작성 트랙 — Block A(TASK 유래) 선작성 후 PLAN.md §리스크 가설 표로 Block B 보강 완료

## 1. 리스크 가설 표

> PLAN.md §리스크 가설 표 H-1~H-9 전건 전재. 선작성 초안의 잠정 항목 (A-1)~(A-3)은 H-1·H-6·H-3에 흡수되어 삭제했다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 | 시나리오 |
|----|----------|----------------|---------|---------|---------|
| H-1 | F-001 — 3필드 하드코딩 emit → 스펙 순회 흡수 (`scripts/install-mac.sh:584-589`) | 배포 산출물 바이트 계약 — 필드 순서·`description` 공백 시 생략·`yaml_escape` 적용 지점이 어긋나면 15에이전트 × 4플랫폼 전량 재작성 | P0 | L1 + L2 | S-1, S-10 |
| H-2 | F-001 — Codex TOML 경로 스펙 흡수 (`scripts/install-mac.sh:795-802`) | TOML 직렬화 계약 — `toml_escape` 미적용·따옴표 누락 시 `codex doctor`가 malformed로 거부 → Codex 에이전트 15종 전량 미로드 | P0 | L1 + L2 | S-3, S-12 |
| H-3 | F-001 R-3 — 미정의 effort 값 처리 | install 완주 계약 — 예외 시 배포 불능 / 무검증 통과 시 Codex가 unknown value로 파일 거부 | P0 | L1 | S-4 |
| H-4 | F-002 — PowerShell 미러 | 미러 규약 (`scripts/install/windows.ps1:93`) — 두 언어 스펙 표현이 갈리면 플랫폼별 산출물이 갈리고 로컬에서 회귀 미탐지. `pwsh` 미설치(실측)로 런타임 검증 불가 | P1 | L1 + L3(이월) | S-5, S-14 |
| H-5 | F-002 — PowerShell 값 처리 세부 | 타입 계약 — `ConvertFrom-Json`은 `PSCustomObject` 반환이라 hashtable 인덱싱 실패. `Get-AgentFrontmatter`(`:1601-1657`)가 3키만 추출해 `effort`가 파싱 단계에서 소실 | P1 | L1 + L3(이월) | S-6, S-14 |
| H-6 | F-004 — `max_threads` 교체 | 멱등 스킵 계약 (`scripts/install-mac.sh:823-826`) — `[agents]` 헤더 존재 시 통째 스킵 → 기존 설치 머신에 legacy 키 영구 잔존 | P1 | L1 + L2 | S-8, S-12 |
| H-7 | F-003 — SSOT 표 갱신 | 문서-코드 축자 일치 계약 — 표 셀 값이 스펙 JSON과 어긋나면 다음 필드 추가자가 표를 믿고 잘못 구현 | P2 | L1 | S-7 |
| H-8 | F-001/F-002 — 본문 토큰 변환 경로 (`_sub_body_model` `:596-620`) | 경계 계약 — `mapping` dict를 스펙 파생값으로 바꾸면 본문 치환 입력이 바뀌어 body 변환 결과가 달라질 수 있음 | P0 | L1 | S-1 |
| H-9 | 전체 — 실 install 재배포 | 사용자 파일 충돌 가드 — 배포 디렉토리에 사용자 관리 파일이 있으면 스킵되어 "변화 없음"이 오탐(false pass) | P2 | L2 | S-13 |

## 2. 테스트 데이터 설계

### 2.1 사전 조건 데이터

> 본 태스크는 DB 없는 셸/문서 변경이므로 "테이블" 축을 **자원(파일·디렉토리)** 으로 읽는다.

| 테이블(자원) | 식별자 | 상태 | 출처 |
|--------------|--------|------|------|
| 구판 어댑터 소스 | `git show HEAD:scripts/install-mac.sh` | 커밋된 HEAD 상태 (워킹트리 클린 확인 후 기준 확정) | git (읽기 전용) |
| 신판 어댑터 소스 | 워킹트리 `scripts/install-mac.sh` | Step 3·4 수정 반영 | 워킹트리 |
| 에이전트 정의 15종 | `opal/agents/*/AGENT.md` | 현행 (effort 미선언) | 프로젝트 소스 |
| effort 선언 픽스처 | 스크래치 임시 에이전트 (`effort: high`) | 테스트 런타임 생성 | `mktemp -d` fixture |
| 미정의 effort 픽스처 | 스크래치 임시 에이전트 (`effort: hihg` 오타) | 테스트 런타임 생성 | `mktemp -d` fixture |
| codex config — 파일 없음 | 스크래치 `config.toml` 미생성 | 3분기 케이스 ① | fixture |
| codex config — `[agents]` 없음 | 스크래치 `config.toml` (`[mcp_servers]`만 보유) | 3분기 케이스 ② | fixture |
| codex config — legacy 키 보유 | 스크래치 `config.toml` (`[agents]` + `max_threads = 6` + `[mcp_servers]`) | 3분기 케이스 ③ | fixture |
| 실 배포본 스냅샷 | `~/.claude|.cursor|.gemini/agents/*.md` 45건 + `~/.codex/agents/*.toml` 15건 | 재배포 직전 백업 | 스크래치 백업 |
| 실 codex 설정 스냅샷 | `~/.codex/config.toml` | 재배포 직전 백업 | 스크래치 백업 |
| 프로브 에이전트 | `opal/agents/{프로브명}/AGENT.md` (`effort: high`) | Step 8에서 생성 → 검증 후 삭제 | 프로젝트 소스 (install 경유 배포) |

### 2.2 시나리오별 데이터 흐름

| 시나리오 | Given (read) | When (CUD/호출) | Then (re-read) |
|---------|------------|----------------|---------------|
| S-1 | HEAD 구판 emitter + 에이전트 15종 | 구판·신판 emitter로 각각 60건 생성 | 두 산출물 트리 `diff -r` → 공집합 |
| S-2 | 신판 `scripts/install-mac.sh` emit 함수 구간 | 플랫폼명 리터럴 비교 패턴 스캔 | 매치 0건 |
| S-3 | effort 선언 픽스처 1종 | 4플랫폼 emit 실행 | Claude=`effort` 키 / Codex=`model_reasoning_effort` 키 / Cursor·Gemini=키 부재 |
| S-4 | `effort: max` · `effort: minimal` · `effort: hihg` 3픽스처 | 각각 emit 실행 | 값 변환 결과 + 오타 케이스는 stderr 경고 1행·필드 생략·exit 0 |
| S-5 | 두 스크립트의 센티넬 구간 | 스펙 JSON 블록 추출 | 두 블록 바이트 diff 공집합 |
| S-6 | 신판 `windows.ps1` 변경 구간 | PS 7 전용 구문 스캔 | 매치 0건 |
| S-7 | `agents.md` effort 행 4셀 + 스펙 JSON `to`/`values` | 양측 값 추출 | 축자 일치 |
| S-8 | codex config 3분기 픽스처 | `install_codex_config` 상당 로직 실행 (2회 연속) | legacy 0건 · 정식 키 1건 · `[mcp_servers]` 무손상 · 2회차 바이트 무변화 |
| S-9 | 변경 전 워킹트리 | 테스트 스위트 실행 → 변경 → 재실행 | RED → GREEN 전이 관측 |
| S-10 | 재배포 직전 60건 스냅샷 | `./scripts/install-mac.sh` 재배포 | 스냅샷 대비 diff 공집합 + 각 플랫폼 15/15 수량 유지 |
| S-11 | 프로브 에이전트(`effort: high`) 소스 배치 | install 재배포 → 검증 → 프로브 삭제 → install 재실행 | Claude·Codex 배포본에 effort 키 존재 / Gemini·Cursor 부재 / 삭제 후 프로브 잔존 0건 |
| S-12 | 재배포된 Codex 산출물 + `~/.codex/config.toml` | `codex doctor --json` 실행 | 0 warn · 0 fail · `max_concurrent_threads_per_session = 6` 존재 · `max_threads` 0건 |
| S-13 | 4개 배포 디렉토리 + `opal/agents/` 소스 목록 | 재배포 **전** AUTO-GENERATED 헤더 보유 파일 집합을 소스 집합과 대조 | 4개 디렉토리 모두 AUTO-GENERATED 집합 ⊇ 소스 15종 (누락 0건). 소스에 없는 AUTO-GENERATED 파일(고아)은 목록으로 열거하되 미달 판정에서 제외. 헤더 없는 파일(사용자 관리)은 카운트 제외하고 존재만 기록 |
| S-14 | Windows 머신 + 신판 `windows.ps1` | Windows에서 install 실행 | frontmatter 블록이 mac 산출물과 동일 · effort 키 보존 |

## 3. 검증 시나리오

### L1. 기능 단위 (자동, 실 데이터 입력)

#### S-1: 차등 골든 — 구판·신판 emitter 산출물 바이트 동일

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-8 |
| 대상 | R-1·R-4 완료기준 (a) — effort 미선언 에이전트 산출물 불변 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `git show HEAD:scripts/install-mac.sh`로 구판 emitter를 추출하고, 워킹트리 신판과 각각 `opal/agents/*` 15종 × 4플랫폼 = 60건을 스크래치에 생성 |
| 기대 결과 | 두 산출물 트리의 `diff -r`이 공집합. 본문(body) 인라인 `model: <레벨>` sub-dispatch 토큰 변환 결과도 파일 전체 비교에 포함되어 불변 |
| 도구 | `scripts/tests/test_agent_adapter_fields.sh` (TS-001, TS-010) |
| 실행 명령 | `bash scripts/tests/test_agent_adapter_fields.sh` |
| 결과 | PASS |
| 상세 | `[NOTE] scripts/install-mac.sh 가 HEAD 대비 dirty — baseline=HEAD로 차등 골든을 계산한다`. `[PASS] TS-001/TS-010: 구판 vs 신판 emitter 산출물 diff 공집합 (15 에이전트 × 4플랫폼, body 포함)`. 15에이전트×4플랫폼=60건 전량 바이트 동일, 본문 인라인 `model:` 토큰 변환 결과 포함하여 불변 확인. op-dev-test-agent가 직접 재실행하여 재현 확인함(PASS=15 FAIL=0 SKIP=0). |

#### S-2: 플랫폼명 하드코딩 분기 미신설

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | R-1 AC — "emit 함수 본문에 플랫폼명 조건 분기가 신규로 추가되지 않는다" |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 신판 emit 함수 구간을 추출하여 플랫폼명 리터럴 비교 패턴을 스캔 |
| 기대 결과 | 매치 0건 — 플랫폼명은 스펙 조회 키로만 등장한다 |
| 도구 | TS-002 |
| 실행 명령 | `bash scripts/tests/test_agent_adapter_fields.sh` (내부 TS-002) |
| 결과 | PASS |
| 상세 | `[PASS] TS-002: emit_platform_agent_adapter/install_codex_agents 본문에 플랫폼명 리터럴 비교 0건`. 신판 emit 함수 구간에서 플랫폼명 조건 분기(하드코딩 if/case)가 스캔되지 않음 — 플랫폼명은 스펙 조회 키로만 등장. |

#### S-3: 배치 모드 4형태 동작

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | R-2 — ①독립 키 ②이름 다른 독립 키 ③model 값 합성 ④미지원 생략 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `effort: high` 픽스처를 4플랫폼 emit에 통과. ③(`model_param`)은 현재 활성 플랫폼이 없으므로 임시 스펙 주입으로 경로를 실행(dead code 방지) |
| 기대 결과 | Claude=`effort: high`, Codex=`model_reasoning_effort = "high"`, `model_param` 모드=model 값에 파라미터 합성, Gemini·Cursor=effort 관련 키 부재 |
| 도구 | TS-003, TS-004, TS-005, TS-006 |
| 실행 명령 | `bash scripts/tests/test_agent_adapter_fields.sh` (TS-005는 cursor.effort→`mode:"model_param"` 임시 스펙 주입 후 `emit_platform_agent_adapter`를 cursor 플랫폼으로 재실행) |
| 결과 | PASS |
| 상세 | `[PASS] TS-003: Claude md frontmatter에 effort: high 존재 (①독립 키)`. `[PASS] TS-004: Codex toml에 model_reasoning_effort = "high" 존재 (②이름 다른 독립 키)`. `[PASS] TS-005: model_param 합성(base[effort=...]) 경로 확인 — cursor.effort→model_param 임시 주입 시 model: "inherit[effort=high]" 합성`. `[PASS] TS-006: Gemini/Cursor 산출물에 effort 키/[effort= 0건 (④미지원 생략)`. 4형태 전부 확인. |

#### S-4: 값 도메인 변환 + 미정의 값 부정 경로

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-3 |
| 대상 | R-3 — 값 축약 규칙 및 오타 방어 (⑥경계·부정 축) |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | (a) `effort: max` (b) `effort: minimal` (c) `effort: hihg`(오타) 3픽스처를 emit |
| 기대 결과 | (a) Claude=`max` / Codex=`xhigh` 축약 (b) Codex=`minimal` / Claude는 스펙 규칙대로 처리 (c) **stderr 경고 1행 + 해당 필드만 생략 + 나머지 필드 정상 + 종료코드 0** (install 전체 중단 금지) |
| 도구 | TS-007, TS-008 |
| 실행 명령 | `bash scripts/tests/test_agent_adapter_fields.sh` (내부 TS-007, TS-008) |
| 결과 | PASS |
| 상세 | `[PASS] TS-007: effort:max → Claude=max / Codex=xhigh 축약 확인`. `[PASS] TS-008: 미정의 effort 값 → stderr 경고 + 필드 생략 + 나머지 필드 정상 + install 계속`. 오타(`hihg`) 케이스에서 install 전체 중단 없이 exit 0으로 계속 진행함을 확인. |

#### S-5: 스펙 JSON 미러 바이트 동일

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4 |
| 대상 | R-4 — mac·windows 미러 규약의 기계 검증 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 두 스크립트의 센티넬 주석 구간에서 스펙 JSON 블록을 추출 |
| 기대 결과 | 두 블록의 바이트 diff가 공집합 |
| 도구 | TS-011 |
| 실행 명령 | `bash scripts/tests/test_agent_adapter_fields.sh` (내부적으로 `awk '/# >>> OPAL_ADAPTER_FIELD_SPEC >>>/,/# <<< OPAL_ADAPTER_FIELD_SPEC <<</'` 를 install-mac.sh/windows.ps1 양쪽에 적용 후 문자열 비교) |
| 결과 | PASS |
| 상세 | `[PASS] TS-011: 스펙 JSON 리터럴 4곳(mac 센티넬·mac 폴백×2·windows 미러) 전수 바이트 동일 (count=4/4 all bytes identical (mac_sentinel, mac_fallback x2, win_mirror))`. **주의**: 이는 정적 텍스트(JSON 리터럴) 바이트 동일성만 검증한다 — PowerShell 런타임에서 이 스펙을 실제로 소비하는 파싱 계약(H-5, `PSCustomObject` 인덱싱)까지 보장하지 않는다(S-6·S-14 참조). |

#### S-6: PowerShell 5.1 호환 정적 검증

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-5 |
| 대상 | R-4 — `pwsh` 미설치 환경에서의 정적 방어 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `windows.ps1` 변경 구간에 PS 7 전용 구문(`-AsHashtable` 등) 스캔 |
| 기대 결과 | 매치 0건. `Get-AgentFrontmatter` 반환이 기존 4키를 유지한 채 `Fields`만 추가(하위호환) |
| 도구 | TS-014 |
| 실행 명령 | `bash scripts/tests/test_agent_adapter_fields.sh` (내부적으로 `grep -nE -- '-AsHashtable|\?\?|\?\.|\\u\{' scripts/install/windows.ps1`) — Windows 실행 검증(TS-012·013)은 본 환경 `pwsh` 미설치로 미수행 |
| 결과 | PASS (정적 검증 한정) |
| 상세 | `[PASS] TS-014: windows.ps1에 PS7 전용 구문(-AsHashtable/??/?./\u{}) 0건`. **주의**: 이는 정적 구문 스캔이며 런타임 동치를 보장하지 않는다 — H-5(`ConvertFrom-Json`의 `PSCustomObject` 반환으로 인한 인덱싱 실패 가능성)는 이 스캔으로 완전히 배제되지 않는다. 실제 PowerShell 실행 검증은 S-14로 이월(pwsh 미설치, 실측 확인). |

#### S-7: SSOT 표와 스펙의 축자 일치

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-7 |
| 대상 | R-5 — `opal/core/references/agents.md` §frontmatter 변환 규칙 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 표의 `effort` 행 4셀 값과 스펙 JSON의 `to`/`values`를 추출해 대조 |
| 기대 결과 | 4셀이 모두 채워져 있고(Gemini는 미지원 표기) 스펙과 축자 일치. `(기타 OPAL 전용 필드)` 문언이 `(변환 테이블 미등재 필드)`로 정정. 변경이력 `v2.1` 행에 `(105)` 포함 |
| 도구 | TS-015, TS-016, TS-017 |
| 실행 명령 | Python 인라인 검증 — `opal/core/references/agents.md` §frontmatter 변환 규칙 표에서 `effort` 행 4셀·`(변환 테이블 미등재 필드)` 문언·`v2.1` 변경이력 행을 정규식으로 추출하고, `scripts/install-mac.sh`의 `OPAL_ADAPTER_FIELD_SPEC` 센티넬 구간을 `json.loads`로 파싱하여 `effort.platforms.claude.to`/`codex.to`/`codex.values.max`와 축자 비교 (EXECUTE 워커 자가 점검 시 1회 실행, 스크립트는 상세란 참조) |
| 결과 | PASS |
| 상세 | effort 행 4셀: Claude `` `effort` (그대로) ``, Cursor `(제거 — 예약, `inherit` 정책 해제 전 미적용)`, Gemini `(제거 — 미지원)`, Codex `` `model_reasoning_effort` (`max`→`xhigh`, 그 외 그대로) `` — 스펙 JSON 실측값 `claude.to="effort"`, `codex.to="model_reasoning_effort"`, `codex.values.max="xhigh"`와 축자 일치(TS-016). 표 본문에 `(기타 OPAL 전용 필드)` 잔존 0건, `(변환 테이블 미등재 필드) \| (제거) \| (제거) \| (제거) \| (제거)` 존재(TS-015). 변경이력 최종 행 `v2.1 \| 2026-09-02 19:32 KST \| ... (105)` 확인(TS-017). |

#### S-8: Codex config 3분기 마이그레이션 + 멱등 (교체형 — 채택·잔존)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-6 |
| 대상 | R-6 — legacy alias 교체 및 기존 설치 머신 마이그레이션 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | ①파일 없음 ②`[agents]` 없음 ③`[agents]` + `max_threads` 보유 3픽스처에 대해 로직을 각 2회 연속 실행 |
| 기대 결과 | **구형 잔존 0** — 3케이스 모두 `max_threads` 0건. **신형 채택** — `max_concurrent_threads_per_session` 1건. ③에서 기존 값이 보존되고 `[mcp_servers]` 등 타 블록 무손상. 2회차 실행 후 바이트 무변화(멱등) |
| 도구 | TS-018(케이스②: `[agents]` 없음·타 블록 보유 → append), TS-019(케이스①: 파일 없음 → append), TS-020(케이스③: legacy 보유 → in-place 치환), TS-021(멱등) |
| 실행 명령 | `bash scripts/tests/test_agent_adapter_fields.sh` (내부 TS-018~021) |
| 결과 | PASS |
| 상세 | `[PASS] TS-018: 기존 머신([agents] 없음) — legacy 0건 + [agents] 신설(정식 키) + [mcp_servers] 무손상`. `[PASS] TS-019: 신규 머신 — [agents] + max_concurrent_threads_per_session=6 등 정식 키 3종 존재`. `[PASS] TS-020: 기존 머신 legacy 키 in-place 치환 (값 9 보존) + [mcp_servers] 무손상`. `[PASS] TS-021: 2회차 실행 후 파일 바이트 무변화 (멱등)`. 3분기 전건 구형 잔존 0·신형 채택 1건·타 블록 무손상·멱등 확인. |

#### S-9: 테스트 자산 RED→GREEN 전이 관측

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 (안전망 건전성) |
| 대상 | F-005 — 차등 골든이 실제로 회귀를 잡는지 |
| 계층 | L1 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 코드 변경 전 스위트 실행(RED 기록) → Step 3~5 반영 → 재실행 |
| 기대 결과 | 변경 전 effort 관련 케이스가 FAIL로 명확히 리포트되고, 변경 후 전건 GREEN으로 전이. `bash -n` 문법 통과 |
| 도구 | TS-023 |
| 실행 명령 | `bash scripts/tests/test_agent_adapter_fields.sh` — 스크립트 내 각 TS 케이스 주석에 `RED 예상` 사전 명시(예: TS-003/004/007/008/011/018/019/020/021의 `fail()` 분기가 "스펙 미도입 — RED 예상"으로 라벨링). op-dev-test-agent는 라벨링 존재와 현재 전건 PASS(GREEN) 상태를 함께 확인 |
| 결과 | PASS |
| 상세 | 테스트 스크립트 13~16행 주석: "Step 3~4·2 완료 후 재실행하면 전건 PASS(GREEN)해야 한다" — 설계 의도가 RED-first임을 명시. 현재 실행 결과 PASS=15 FAIL=0 SKIP=0으로 GREEN 상태 확인(재현 완료). `bash -n scripts/install-mac.sh` 통과. 단, op-dev-test-agent는 HEAD 체크아웃 상태로 되돌려 실제 RED 재현까지는 수행하지 않았다(워킹트리 변경 보존 제약, PLAN 범위 내 EXECUTE 워커의 RED 캡처 로그를 신뢰). |

### L2. 프로세스 통합 (자동, 실 재배포 → 산출물 re-read)

#### S-13: 사전 가드 — 오탐 차단 (S-10보다 먼저 실행)

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-9 |
| 대상 | 사용자 파일 충돌 가드로 인한 false pass 차단 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 재배포 **전** 4개 배포 디렉토리에서 AUTO-GENERATED 헤더 보유 파일의 (확장자 무관) 베이스명 집합을 뽑아 `opal/agents/` 소스 15종 집합과 대조한다. 판정 기준은 "파일 수 15/15"가 아니라 **집합 포함 관계**다 — 총 파일 수는 사용자 관리 파일·고아 파일 혼입으로 15와 달라질 수 있다(예: cursor 21 = AUTO-GENERATED 16 + 사용자 파일 5, gemini 16 = AUTO-GENERATED 16) |
| 기대 결과 | 4개 디렉토리 모두 AUTO-GENERATED 집합이 소스 15종을 빠짐없이 포함(누락 0건). 소스에 없는 AUTO-GENERATED 항목(고아)이 있으면 목록으로 열거하되 그 자체로는 FAIL 사유가 아니다 — cursor·gemini의 `wtm-agent.md`는 소스가 `opal-wtm-agent`로 개명된 뒤 남은 **기존 상태**(이번 태스크 무관, 어댑터 디렉토리가 install `clean_dirs` 대상이 아니어서 발생)로 알려진 고아다. 이 고아는 재배포 대상이 아니므로 재배포 전후 존재가 불변이며, S-10의 "스냅샷 대비 diff 공집합" 판정을 무효화하지 않는다. AUTO-GENERATED 헤더가 없는 파일(사용자 관리 파일)은 존재만 기록하고 카운트·판정 대상에서 제외한다(H-9 원목적 — 사용자 파일 스킵으로 인한 오탐 차단 — 유지). 누락이 있으면 S-10의 "변화 없음"은 무효이므로 즉시 중단하고 PM에 보고 |
| 도구 | grep + 집합 대조 |
| 실행 명령 | `SRC_LIST="$(ls opal/agents | sort)"; for d in "$HOME/.claude/agents:md" "$HOME/.codex/agents:toml" "$HOME/.cursor/agents:md" "$HOME/.gemini/agents:md"; do dir="${d%%:*}"; ext="${d##*:}"; autos="$(grep -l 'AUTO-GENERATED' "$dir"/*."$ext" 2>/dev/null | xargs -n1 basename | sed "s/\.${ext}\$//" | sort)"; missing="$(comm -23 <(echo "$SRC_LIST") <(echo "$autos"))"; orphans="$(comm -13 <(echo "$SRC_LIST") <(echo "$autos"))"; echo "$dir missing=[${missing:-none}] orphans=[${orphans:-none}]"; done` |
| 결과 | PASS |
| 상세 | op-dev-test-agent가 재배포 완료 후 시점에 직접 재실행하여 교차 확인함(원 시점 값은 PM 실측): `/Users/iskang/.claude/agents total=15 missing=[none] orphans=[none]`, `/Users/iskang/.codex/agents total=15 missing=[none] orphans=[none]`, `/Users/iskang/.cursor/agents total=21 missing=[none] orphans=[wtm-agent]`, `/Users/iskang/.gemini/agents total=16 missing=[none] orphans=[wtm-agent]`. 4개 디렉토리 모두 소스 15종 누락 0건. cursor·gemini의 `wtm-agent` 고아는 기존 알려진 상태로 판정 무효화 대상 아님. |

#### S-10: 실 재배포 회귀 — 배포본 60건 불변

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1 |
| 대상 | 완료기준 (a) — 기존 동작 100% 보존 |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | S-13 통과 후, 60개 산출물 + `~/.codex/config.toml` 스냅샷을 스크래치에 백업하고 `./scripts/install-mac.sh` 재배포 |
| 기대 결과 | 스냅샷 대비 60건 `diff` 공집합. 각 플랫폼 15/15 수량 유지 |
| 도구 | install + diff |
| 실행 명령 | PM이 `./scripts/install-mac.sh`로 재배포 실행(op-dev-test-agent는 재실행하지 않음 — install은 프론트엔드 빌드 포함 수 분 소요로 도구 타임아웃 초과, 지시사항에 따라 재실행 금지) |
| 결과 | PASS (PM 실측 근거 + op-dev-test-agent 사후 상태 교차 확인) |
| 상세 | PM 보고: 재배포 후 백업(`/tmp/opds105-backup.b1D0Tu`) 대비 diff — 차이는 `opal-test-agent` 1건×4플랫폼뿐이며 원인은 미배포 소스 드리프트(커밋 `9d2644e`, 본문 `캡틴`→`사용자` 1행)로 frontmatter 무변경 = emit 회귀 아님. op-dev-test-agent 교차 확인: 현재 배포 디렉토리 파일 수 claude=15, codex=15, cursor=21(AUTO-GENERATED 16 + 사용자 5), gemini=16 — S-13 재확인 결과와 일치하며 15/15 수량 유지 확인. 원본 백업 파일과의 바이트 diff 자체는 재실행하지 않았으므로 PM 서술을 그대로 인용함(재현 불가 항목으로 명시). |

#### S-11: 목표달성 — effort가 실제 배포본에 도달한다

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-1, H-2 |
| 대상 | 태스크 목표 문장 + 완료기준 (b)(c) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | `effort: high`를 선언한 프로브 에이전트를 **프로젝트 소스** `opal/agents/`에 생성하고 install을 경유해 배포. 검증 후 소스 프로브를 삭제하고 install 재실행 |
| 기대 결과 | `~/.claude/agents/{프로브}.md`에 `effort: high` 존재, `~/.codex/agents/{프로브}.toml`에 `model_reasoning_effort` 존재, `~/.gemini/agents/{프로브}.md`·`~/.cursor/agents/{프로브}.md`에 effort 관련 키 **부재**(Cursor `model`은 `inherit` 유지, 대괄호 파라미터 없음). 삭제·재실행 후 4플랫폼에서 프로브 잔존 0건 |
| 도구 | install + grep |
| 실행 명령 | PM이 프로브 `probe-effort-105`(`effort: high`)를 `opal/agents/`에 배치 → install 경유 배포 → grep 검증 → 소스 삭제 → install 재실행(op-dev-test-agent는 재실행하지 않음 — install 재실행 금지 지시) |
| 결과 | PASS (PM 실측 근거 + op-dev-test-agent 사후 잔존 확인) |
| 상세 | PM 보고: Claude `effort: high` / Codex `model_reasoning_effort = "high"` 배포본에 존재, Gemini·Cursor는 키 부재(Cursor `model: inherit` 유지) 확인 후 소스 삭제 → 5경로(4배포처+소스) 잔존 0건, 파일 수 15/21/16/15 복귀. op-dev-test-agent 교차 확인: `ls ~/.claude/agents \| grep -i probe`, `~/.codex/agents`, `~/.gemini/agents`, `~/.cursor/agents`, `opal/agents` 5곳 전부 grep 결과 없음(잔존 0건, 위 실행 로그 참조) — PM 서술과 일치. |

#### S-12: Codex 파서 수용 + 설정 교체 실측

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-2, H-6 |
| 대상 | 완료기준 (d) + R-6 AC (c) |
| 계층 | L2 |
| **실행 방식** | **M1 (테스트 도구)** |
| 조건 | 재배포 후 `~/.codex/config.toml`을 re-read하고 `codex doctor --json` 실행 |
| 기대 결과 | `max_concurrent_threads_per_session = 6` 존재, `max_threads` 0건, `codex doctor` **0 warn · 0 fail**. 에이전트 TOML에 대한 malformed 경고 0건 |
| 도구 | `codex doctor --json` (미설치 시 SKIP 사유 기록) |
| 실행 명령 | `grep -n 'max_threads\|max_concurrent_threads_per_session' ~/.codex/config.toml` + `codex doctor --summary` (op-dev-test-agent가 직접 재실행) |
| 결과 | PASS |
| 상세 | op-dev-test-agent 직접 실측: `~/.codex/config.toml`에 `max_concurrent_threads_per_session = 6` 존재, `max_threads` 매치 0건. `codex doctor --summary` 실행 결과 `17 ok · 1 idle · 1 notes · 0 warn · 0 fail` — PM 보고와 완전 일치. 상세 출력에 agent TOML malformed 관련 경고 없음(`rollout DB malformed file names 0`만 관측, 이는 별도 항목). |

### L3. 사용자 협업 (수동, [SUPERVISOR] 마커)

#### S-14: Windows 머신 실행 검증 [SUPERVISOR]

| 항목 | 내용 |
|------|------|
| 가설 매핑 | H-4, H-5 |
| 대상 | R-4 — PowerShell 어댑터 런타임 정합 |
| 계층 | L3 |
| **실행 방식** | **M3 (사용자 협업)** — 본 환경에 `pwsh` 미설치(실측)로 M2 자동화 불가 |
| 조건 | Windows 머신에서 `scripts/install/windows.ps1` 실행 |
| 기대 결과 | 배포된 에이전트 파일의 frontmatter 블록이 mac 산출물과 동일하고, effort 선언 에이전트의 키가 소실되지 않는다 |
| 실행자 | [SUPERVISOR] — 캡틴 수동 확인 필요 |
| 결과 | 미검증 — L3 [SUPERVISOR] 시나리오 감지, PM에 위임 |
| 상세 | op-dev-test-agent는 본 시나리오를 실행하지 않았다(마커 규칙에 따름). 본 환경 `pwsh` 미설치가 실측으로 확인되어 M2 자동화(playwright/cmux 경유 대체 포함)도 적용 불가 — Windows 런타임 검증이 필요하다. S-5·S-6의 정적 검증(스펙 JSON 바이트 미러 일치, PS7 전용 구문 스캔 0건)은 이 시나리오를 대체하지 않는다: 정적 미러 일치는 두 스크립트가 같은 텍스트를 담고 있음만 보장하며, `ConvertFrom-Json`이 `PSCustomObject`를 반환해 hashtable 인덱싱이 실패하는 유형의 런타임 결함(H-5)은 정적 스캔으로 완전히 배제되지 않는다. 따라서 R-4 AC "Windows 런타임 정합"은 미검증 상태로 이월한다. |

**PM 표준 요청 양식**

> 캡틴, Windows 머신에서 아래를 확인해 주세요 (TS-012·TS-013).
> 1. 저장소를 Windows에 동기화한 뒤 `scripts/install/windows.ps1`을 실행합니다.
> 2. 배포된 `~/.claude/agents/*.md` 중 아무 1개의 frontmatter 블록(`---` 사이)을 mac 산출물과 대조합니다.
> 3. `effort`를 선언한 에이전트가 있다면 그 키가 배포본에 남아 있는지 확인합니다.
> 4. 결과(동일/상이 + 상이 시 diff)를 알려주시면 이 표에 기록합니다.
>
> **본 태스크는 이 항목을 미검증 상태로 이월합니다** — 완료 보고에 미검증 사실을 명시합니다.

## 4. AC ↔ 가설 ↔ 계층 ↔ 시나리오 매핑 표

| AC ID | 가설 ID | 검증 계층 | 시나리오 | 테스트 파일:케이스 | 비고 |
|-------|---------|---------|---------|-----------------|------|
| R-1 AC — 테이블에 effort 1행 + 3필드 동일 경로 | H-1 | L1 | S-1 | `scripts/tests/test_agent_adapter_fields.sh`:TS-001 `[T105/L1-R1]` | 흡수 후 바이트 불변 |
| R-1 AC — 신규 플랫폼 조건 분기 0 | H-1 | L1 | S-2 | 〃:TS-002 `[T105/L1-R1]` | 분기 회귀 방지 |
| R-2 AC — 배치 4형태 각 1케이스 이상 | H-1, H-2 | L1 | S-3 | 〃:TS-003~006 `[T105/L1-R2]` | `model_param` 임시 주입 포함 |
| R-3 AC — `max`→Codex `xhigh` 축약 | H-3 | L1 | S-4 | 〃:TS-007 `[T105/L1-R3]` | 값 도메인 |
| R-3 AC — 미정의 값 경고+생략+exit 0 | H-3 | L1 | S-4 | 〃:TS-008 `[T105/L1-R3]` | ⑥경계·부정 |
| R-4 AC — mac·windows 산출물 동일 (frontmatter 블록 한정) | H-4 | L1 | S-5 | 〃:TS-011 `[T105/L1-R4]` | 판정 범위 한정 근거: PLAN §9 R-3·R-4 기존 결함 |
| R-4 AC — PS 5.1 호환 | H-5 | L1 | S-6 | 〃:TS-014 `[T105/L1-R4]` | 정적 방어 |
| R-4 AC — Windows 런타임 정합 | H-4, H-5 | L3 | S-14 | TS-012, TS-013 | **이월** (pwsh 미설치) |
| R-5 AC — 표 effort 행 4셀 + 축자 일치 | H-7 | L1 | S-7 | 〃:TS-015~017 `[T105/L1-R5]` | SSOT 정합 |
| R-6 AC (a) — 구형 잔존 0 (결과 파일 기준, 3케이스) | H-6 | L1 | S-8 | 〃:TS-018(케이스②)·TS-019(케이스①)·TS-020(케이스③) `[T105/L1-R6]` | 교체형 잔존 — 판정 대상은 install 결과 `config.toml`(재정의, TASK.md `[결정]` 참조), 탐지·치환 로직 자체의 리터럴은 예외 |
| R-6 AC (b) — 신형 채택 (3케이스 1건·값 보존·타 블록 무손상·멱등) | H-6 | L1 | S-8 | 〃:TS-018·TS-019·TS-020·TS-021 `[T105/L1-R6]` | 교체형 채택 + 마이그레이션 |
| R-6 AC (c) — 실환경 확인 (정식 키 존재·legacy 0건·doctor 0 fail) | H-6 | L2 | S-12 | TS-009, TS-022 | 파서 수용 — PM 실측 완료 |
| 완료기준 (a) — 미선언 산출물 바이트 동일 | H-1, H-8 | L1 + L2 | S-1, S-10 | 〃:TS-001·010 / TS-012(mac) | 최상위 제약 |
| 완료기준 (b) — Claude·Codex 올바른 키/값 | H-1, H-2 | L2 | S-11 | 실측 (install 경유) | 목표달성 |
| 완료기준 (c) — Gemini effort 키 부재 | H-1 | L2 | S-11 | 실측 (install 경유) | ⑥경계·부정 |
| 완료기준 (d) — `codex doctor` 0 warn·0 fail | H-2, H-6 | L2 | S-12 | TS-009, TS-022 | 파서 수용 |
| (안전망) 테스트 자산 건전성 | H-1 | L1 | S-9 | 〃:TS-023 | RED→GREEN 전이 |
| (오탐 차단) 사용자 파일 가드 | H-9 | L2 | S-13 | 사전 헤더 카운트 | S-10 선행 필수 |

## 5. 코드 품질

| # | 검사 | 도구 | 결과 | 상세 |
|---|------|------|------|------|
| 1 | 린트 | `bash -n scripts/install-mac.sh` | PASS | 문법 오류 0, 종료코드 0 |
| 2 | 타입 체크 | N/A (셸/PowerShell — 정적 타입 없음). 대체: PS 7 전용 구문 스캔(TS-014) | PASS | TS-014 PASS — `-AsHashtable`/`??`/`?.`/`\u{}` 0건 |
| 3 | 포맷터 | N/A (프로젝트에 셸 포맷터 미도입). 대체: bash 3.2 호환 스캔(연관배열·`mapfile` 미사용) | PASS | `test_agent_adapter_fields.sh`에 `declare -A`/`mapfile`/`readarray` 0건 (주석 명시: "bash 3.2 호환 — 연관배열·mapfile 미사용") |
| 4 | 기존 테스트 회귀 | `test_archive_contents.sh` · `test_version_stamp.sh` | PASS | 둘 다 종료코드 0 (각 11/11 PASS) |

## 6. 보안

| # | 항목 | 결과 | 상세 |
|---|------|------|------|
| 1 | 하드코딩 시크릿 스캔 | PASS | `test_agent_adapter_fields.sh`·`install-mac.sh` 전체에 `password=`/`secret=`/`api_key=`/`/Users/<name>/` 패턴 0건 (grep 실측) |
| 2 | .gitignore 확인 | PASS | 테스트는 `mktemp -d` 스크래치에서만 픽스처 생성 — 저장소 유입 대상 없음. `git status --short` 결과에 스크래치·백업 경로 0건 |
| 3 | 사용자 설정 무손상 | PASS | TS-020: legacy 키 in-place 치환 시 값 보존(9 유지) + `[mcp_servers]` 블록 무손상 확인(테스트 픽스처). 실 `~/.codex/config.toml` 대상은 S-12에서 op-dev-test-agent가 직접 재실측 — `max_concurrent_threads_per_session = 6` 존재, `max_threads` 0건, `codex doctor --summary` 17 ok·0 warn·0 fail로 실환경도 무손상 확인 완료 |
| 4 | 홈 디렉토리 오염 0 | PASS | `test_agent_adapter_fields.sh` 47행 `SCRATCH_DIR="$(mktemp -d)"` + 48행 `trap 'rm -rf "$SCRATCH_DIR"' EXIT`로 정리 보장(테스트 픽스처). 프로브(`probe-effort-105`)는 S-11에서 op-dev-test-agent가 4배포처+소스 5경로 grep으로 잔존 0건 직접 재확인 완료 |

## 7. 판정

**Partial Fail (핵심 기능은 전건 Pass, 1건 미검증 이월) — S-1~S-13, §5, §6 전건 PASS(자동 스위트 재현 PASS=15/FAIL=0/SKIP=0 포함 op-dev-test-agent 직접 재현 및 실환경 항목 교차 확인 완료). 단 S-14(Windows 런타임 실행 검증, R-4 AC "Windows 런타임 정합")는 `pwsh` 미설치로 미검증 상태이며, S-5·S-6의 정적 미러/구문 검증은 이를 대체하지 않는다(H-5 `PSCustomObject` 인덱싱 결함 유형은 정적 스캔으로 완전 배제되지 않음). 핵심 기능(mac 배포 경로 전체, effort 값 변환, Codex 설정 마이그레이션, 실 재배포 회귀, 실 codex doctor 검증)은 전부 실측 Pass이므로 Critical Fail은 아니나, R-4 AC의 Windows 런타임 축은 미충족 상태로 다음 단계 진행 시 명시적으로 이월해야 한다.**
