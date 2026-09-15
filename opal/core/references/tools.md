# OPAL Tools

> OPAL 에이전트가 파일 처리, 데이터 변환 등 특정 작업 시 호출하는 CLI 도구 레지스트리.
> 새 도구 추가 시 이 파일에 등록하고 install-mac.sh의 `install_opal_venv()`를 통해 배포한다.

---

## 공통 도구 출력 계약

규범 원문은 `opal/core/references/harness/tool-output-contract.md`가 소유한다 — 응답 형식(단일 라인 JSON), 오류 코드 식별자 안정성, 종료 코드 성패 구분 3항목이다.

이 파일은 도구 레지스트리이므로 그 계약을 복제하지 않는다. 도구별 준수 사항·예외는 각 도구의 README가 적는다.

---

## 도구 레지스트리

OPAL이 배포하는 도구 전수 목록이다. 이 표는 **어떤 도구가 있고 어디서 실행하며 사용법이 어디에 있는지**만 소유한다. 서브명령 목록·옵션·오류 코드·종료 코드·사용 예시는 각 도구의 README와 소스가 소유하며 여기에 복제하지 않는다 — 복제된 수치가 낡는 것이 이 파일의 반복 결함이었다.

| 도구 | 용도 | 실행 경로 | README |
|------|------|-----------|--------|
| `backlog-tool` | oppl 2-루프 오케스트레이터의 백로그(`backlog.json`) SSOT 관리 | `~/.opal/tools/backlog-tool/run.sh` | `opal/tools/backlog-tool/README.md` |
| `brain-tool` | `.opal/brain/` 지식 위키의 인덱스·log·링크 무결성·frontmatter 결정론 집행 | `~/.opal/tools/brain-tool/run.sh` | `opal/tools/brain-tool/README.md` |
| `cmux-tool` | cmux browser 명령을 캡슐화한 자동화 래퍼(단일 진입점 서브명령 디스패처) | `~/.opal/tools/cmux-tool/run.sh` | `opal/tools/cmux-tool/README.md` |
| `code-scan` | 코드 파일의 `@header` 메타블록 스캔·조회·검증·기록 | `~/.opal/tools/code-scan/run.sh` | `opal/tools/code-scan/README.md` |
| `date` | KST(Asia/Seoul) 기준 시점 문자열을 평문 한 줄로 출력하는 공용 시점 취득 창구 | `node ~/.opal/tools/date/date.js` | `opal/tools/date/README.md` |
| `doctor` | OPAL 환경 상태 진단(Dependencies·OPAL Paths·MCP Registration·Bootstrappers) | `~/.opal/tools/doctor/run.sh` | `opal/tools/doctor/README.md` |
| `ego-browser-tool` | Ego Lite 설치 상태 조회·검증 설치·실제 브라우저 텍스트 assertion을 JSON 계약으로 제공 | `~/.opal/tools/ego-browser-tool/run.sh` | `opal/tools/ego-browser-tool/README.md` |
| `event-loader` | `events.json` 기준 이벤트 시점 문서 전문·sha256 receipt 반환과 최신성 검증 | `~/.opal/tools/event-loader/run.sh` | `opal/tools/event-loader/README.md` |
| `git-sync-tool` | 워크스페이스 아래 독립 git 저장소를 순회해 clean + fast-forward 가능한 것만 최신화 | `~/.opal/tools/git-sync-tool/run.sh` | `opal/tools/git-sync-tool/README.md` |
| `improve-tool` | 개선 후보를 로컬(프로젝트 `.opal/`)·FW(`~/.opal/fw-inbox/`) 2원으로 분기 기록 | `~/.opal/tools/improve-tool/run.sh` | `opal/tools/improve-tool/README.md` |
| `memory-tool` | 프로젝트 메모리 인덱스·히스토리(`MEMORY.json` 단독 SSOT) 결정론 집행 | `~/.opal/tools/memory-tool/run.sh` | `opal/tools/memory-tool/README.md` |
| `opal-action-monitor` | 루프 액션 에이전트의 `.oppl-run/` 산출물을 단계×축 현황판으로 렌더(읽기 전용) | `~/.opal/tools/opal-action-monitor/run.sh` | `opal/tools/opal-action-monitor/README.md` |
| `opal-agent` | 여러 LLM CLI(claude·gemini·codex·grok)를 비대화형 서브에이전트로 호출 | `~/.opal/tools/opal-agent/run.sh` | `opal/tools/opal-agent/README.md` |
| `opal-cli` | OPAL 프레임워크 관리 단일 진입점(업데이트·진단·제거·MCP 관리) | `~/.opal/tools/opal-cli/run.sh` (PATH 별칭 `opal-cli`) | `opal/tools/opal-cli/README.md` |
| `oppl-runtime-tool` | oppl 2-루프 실행의 유한 실행 계약(설정·ledger·lock·admission) 집행 | `~/.opal/tools/oppl-runtime-tool/run.sh` | `opal/tools/oppl-runtime-tool/README.md` |
| `playwright-tool` | URL을 headless Chromium으로 렌더해 Markdown으로 변환 | `~/.opal/tools/playwright-tool/run.sh` | `opal/tools/playwright-tool/README.md` |
| `self-pm-tool` | `opal-self-pm`의 PM 직접 수행 실행을 경량 JSON으로 기록(SSOT 무접촉) | `~/.opal/tools/self-pm-tool/run.sh` | `opal/tools/self-pm-tool/README.md` |
| `skill-registry` | 스킬 레지스트리 로드 기반 매칭·조회·검증·마이그레이션·위험 스캔 | `node ~/.opal/tools/skill-registry/skill-registry.js` | `opal/tools/skill-registry/README.md` |
| `state-tool` | OPAL 파이프라인 현황판 JSON SSOT(`state.json`) 관리와 이벤트 receipt 검증 | `~/.opal/tools/state-tool/run.sh` | `opal/tools/state-tool/README.md` |
| `test-tool` | `test-tools.yaml`을 읽어 FE/BE×단계별 테스트 도구를 실행·판정하는 얇은 래퍼 | `~/.opal/tools/test-tool/run.sh` | `opal/tools/test-tool/README.md` |
| `tool-scan` | capability(도구·MCP·스킬) 검색과 권위 출처(live `--help`) 사용법 확인 | `~/.opal/tools/tool-scan/run.sh` | `opal/tools/tool-scan/README.md` |
| `worktree-tool` | 태스크별 코드 작업본을 git worktree로 격리 | `~/.opal/tools/worktree-tool/run.sh` | `opal/tools/worktree-tool/README.md` |
| `xlsx-tool` | xlsx 파일의 메타데이터 조회·읽기·검색·쓰기 | `~/.opal/tools/xlsx-tool/run.sh` | `opal/tools/xlsx-tool/README.md` |

> `date`와 `skill-registry`는 `run.sh` 래퍼가 없고 단일 스크립트를 `node`로 직접 호출한다. 두 도구는 단일 라인 JSON 출력 계약의 예외이기도 하다 — 각 README가 그 경계를 소유한다.

---

## 도구 등록 절차

1. `opal/tools/<도구명>/`에 소스와 `README.md`를 만든다. README가 서브명령·옵션·오류 코드·종료 코드·예시의 SSOT다.
2. 위 레지스트리 표에 행 1개를 추가한다 — 도구·용도 1줄·실행 경로·README 경로만 적고 수치는 적지 않는다.
3. `install-mac.sh`의 `install_opal_venv()` 배포 대상과 실행 권한(`chmod`) 블록에 필요한 항목을 추가한다.
4. `harness/tool-output-contract.md`의 공통 출력 계약(단일 라인 JSON·안정 오류 코드 식별자·종료 코드)을 지킨다. 예외가 있으면 README에 명시한다.
5. 변경이력 표에 행을 추가한다.

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v2.14 | 2026-08-15 19:40 | worktree-tool `init` 서브명령 추가(4→**5서브명령**) — 프로젝트 구조 탐지 기반 `.opal/worktree.json` 초안 생성. 독립 `.git` ≥1이면 multi-repo, 0이면 monorepo(추적 최상위 중 manifest 보유). `setup[]`은 lock 파일로 결정론 매핑(repos 이하 depth 2까지, 빌드 산출물 디렉토리 제외), `copy[]`·`portOffset`은 미추측(후보는 `_copy_candidates` 주석 키). 기존 파일은 `CONFIG_EXISTS` 거부·`--force`로만 덮어씀, `--dry-run`은 쓰지 않고 `draft` 키 반환 (092 ADD-1 DEC-8) |
| v2.15 | 2026-08-16 13:26 | STATE.md 저널화 — state-tool 섹션 `:71` 용도 서술을 "`state.json` 파이프라인 JSON SSOT 관리(STATE.md는 의사결정 로그·블로커 저널)"로 교체, `show` 커맨드 주석 2곳(`:87,:170`) "현황판" → "파이프라인 행 현황"으로 치환. `marker_missing`(validate 응답 예시·종료 코드 표) → `user_confirmation_owner_mismatch`로 교체, `--import-existing` 옵션·사용 예시 삭제 (094) |
| v1.0 | 2026-04-03 | xlsx-tool 등록 (076) |
| v1.1 | 2026-04-11 | code-scan 등록 |
| v1.2 | 2026-04-12 | code-scan 섹션에 PM 관리 방안 서브섹션 추가 + exports 커맨드 사용 예시 추가 (109) |
| v1.3 | 2026-05-01 | state-tool 섹션 신규 추가 — 파이프라인 현황판 JSON SSOT 관리 CLI 9개 서브 명령 등록 (134) |
| v1.4 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — note 예시 "캡틴 확인" → "{owner_name} 확인" placeholder 치환 (139) |
| v1.5 | 2026-05-22 10:00 KST | cmux-tool 섹션 신규 추가 — 12+1종 서브명령 + 트리거 조건 5행 매트릭스 + 에러 코드 9종 + fallback 4종 (007) |
| v1.6 | 2026-06-07 | state-tool gate-pass deprecated 표기 — 사용법 블록·예시 2곳에 [deprecated] 레거시 전용 안내 추가. 신규는 PM Gate 통과 후 단일 mark 사용. Phase4 완료 반영 (014 Phase 4) |
| v1.7 | 2026-06-23 | test-tool 섹션 신규 추가 — 테스트 단계별 도구 결정론적 집행 4서브명령(resolve/check/unit/integration) + 트리거 조건 + 커맨드 + 출력 형식. cmux-tool 포맷 답습. 루프 한도 수치 비복제(harness §1 포인터) (039) |
| v1.8 | 2026-06-26 | brain-tool 섹션 신설(8 서브명령) + tool-scan 섹션 신설(5 서브명령 — capability 검색·live 사용법) + harness §9 drift 정합(code-scan·cmux-tool·tool-scan 행 추가). tools.md ↔ harness §9 도구 집합 7종 동일화 (044) |
| v1.9 | 2026-06-26 | memory-tool 섹션 신설(9 서브명령 init/append/update/promote/prune/migrate/show/review/delete) — 프로젝트 메모리 인덱스·히스토리 결정론적 집행, 메모리→docs/brain 졸업 워크플로우·히스토리 FIFO5·요약 길이캡·마커 직접편집 금지·매 변경 후 자가검토·delete(dead/superseded 무손실 정리)·update --new-title(제목 보정). harness §9 drift 정합 (045) |
| v2.0 | 2026-07-02 | git-sync-tool 섹션 신설(단일 서브명령 sync) — 워크스페이스 git 저장소 일괄 동기화, 직속 자식 순회 + ff-only pull + 5종 skip 판정 + JSON 출력. opal-workspace-sync 스킬이 호출. harness §9 drift 정합 (052) |
| v2.1 | 2026-07-10 13:11 | brain-tool validate 설명에 링크필드(related) 값 검사('[[', ']]', '.md' 거부) 반영 + add-page에 `--related` 플래그 설명 추가 (053) |
| v2.2 | 2026-07-17 19:58 KST | oppl-monitor 섹션 신규 추가 — `.oppl-run/` 파싱·단계×축 현황판 렌더(텍스트/`--json`/`--watch`), 상세 수치·규칙은 도구 README 포인터. opal-agent는 레지스트리 항목이 아니라 소스 경로로만 표기(R-REG) (067) |
| v2.3 | 2026-07-17 23:04 KST | 도구명 리네임 — `oppl-monitor` → `opal-action-monitor`(향후 oppd·opsdd 액션 에이전트 공통 관측 도구로 확장 예정이라 이름 중립화). 섹션 제목·경로·본문 명칭 전체 갱신, 로직 무변경 (067) |
| v2.4 | 2026-07-17 | improve-tool 섹션 신설(3 서브명령 record/list/show) — PM 개선 루프 결정론 집행, 로컬(memory-tool 위임)/FW(fw-inbox write) scope 분기, IMPROVE_FW_INBOX 테스트 격리 훅. memory-tool VALID_TYPES/VALID_STATUSES에 improvement/candidate additive 확장 반영 (058) |
| v2.5 | 2026-07-28 21:40 | code-scan 섹션 — 실행 경로를 `run.sh`(권장)·`node code-scan.js`(하위호환) 병기로 갱신, 헤더 작성층 신규 5서브명령(discover/scaffold/target/validate/feature) + 신규 옵션(`--out`/`--dry-run`/`--changed`) + `validate` 종료 코드 표 추가 (077) |
| v2.6 | 2026-07-28 | memory-tool 섹션 — MEMORY.json 단독 SSOT 전환 반영: `migrate` 서브명령 삭제 + `task-number` 서브명령 신설, `show --brief`/`--history N` 추가, lazy 자동 마이그레이션(md→json) 안내, 에러 코드 표를 현행 ERROR_CODES(`memory_json_not_found`/`schema_validation_failed`/`migration_failed`/`lock_timeout`/`task_number_regression`/`invalid_args` 등)로 정정, `marker_missing`·`import_failed` 제거, 모든 사용 예시 `--file`을 `.opal/MEMORY.json`으로 갱신 (078) |
| v2.7 | 2026-07-28 23:28 | code-scan `validate` — `uncovered` 위반 git 기준 2분류(`newly_uncovered` 차단 / `pre_existing` 비차단) 절 신설 + 종료 코드 표에 `pre_existing`-only 시 exit 0 명시 — Step 19에서 CLOSE 게이트가 레거시 파일에 막히던 결함 재작업 (077) |
| v2.8 | 2026-07-30 | memory-tool `update`에 `--kind history` 정정 경로 반영 — `--stage`/`--result`/`--path` 옵션 추가, 용도 1줄에 히스토리 오기재 정정 명시(FIFO 미적용·행 수 불변, 삭제 아님) (079) |
| v2.9 | 2026-08-02 14:50 | code-scan 섹션 헤더 소스 단일화 반영 — `target` 판정 주석의 구 4단 표기를 전역 `headerSource` 직결로 교체하고 `write_to` 3값과 `reason` 3값을 축별로 분리 서술(M-2 교정), `--header-source` 옵션 행 추가, 종료 코드 표를 `validate` 전용에서 전 명령 공통으로 확장 + 에러 코드 4종(`header_source_unset`/`header_source_invalid`/`code_scan_config_invalid`/`scope_ambiguous`) 등재, 프로젝트 설정 예시에 `headerSource` + `scopes` 객체형 추가 및 모드별 동작 요약 신설, `scaffold` inline no-op 1줄 추가, `auto` 유효값 서술 제거(폐기 표기만 유지) (080) |
| v2.10 | 2026-08-03 13:20 | code-scan 섹션 — 매니페스트 샤딩 반영: `scaffold`/`target`/`validate` 커맨드 주석에 `_shards/` 예약 폴더·샤드 라우팅·`manifestMaxBytes` 비차단 상한 서술 추가, 신규 에러 코드 2종(`shard_declaration_invalid`/`reserved_name_collision`) 표 신설, `target`의 신규 실패 표면 `manifest_parse_failed` 명시, §매니페스트 샤딩 서브섹션(`shards` 스키마 + `manifestMaxBytes` 설정 예시) 신설 (082) |
| v2.11 | 2026-08-04 17:18 | code-scan 섹션 — 샤드 정책 확장 반영(v1.6.0 / 13→15서브명령): `split`(제안 `--plan`·집행 `--groups`)·`init`(비대화형 설정 초안, 차단 게이트 앞 배치) 커맨드 등재, 옵션 표에 `--write`/`--force`/`--plan`/`--groups`/`--trace`/`--stop-after` 6행 추가 및 `--out`/`--dry-run` 설명 확장, 에러 코드 `init` 2종(`init_header_source_required`/`config_exists`)·`split` 7종(쓰기 상태 열 포함) 표 신설, §샤드 정책 신설 — `shardPolicy` 설정 3단 우선순위(프로젝트 > 전역 `~/.opal/setting.json` > 코드 상수 10240/40, 셀 단위 머지)·구 위치 `manifestMaxBytes` 폐기 안내(값 미독·자동 변환 없음)·2축 판정(바이트 `>` AND 엔트리 `>=`, 비차단 + 페이로드 4필드)·분할 절차 4단·제안 사다리 S1~S5 표·표준단어사전 탐색 3단/폴백 3분기(부재 침묵·파손 안내 1줄·매칭 0건 통과) 서술, `ladder` 설정 노출 후속 이관 명시, PM 관리 방안에 `init` 생성·`init --force` 복구 경로 반영 (083) |
| v2.12 | 2026-08-13 16:57 | state-tool 행 원천 지시 정정 — `--rows-from` 시놉시스·실행 예시를 `references/pipeline.json` 기준으로 교체(구형 `.md` 파싱 지시 제거). 10/10 pilot 전환에 맞춘 pilot 밖 정합 (090) |
| v2.13 | 2026-08-15 16:30 | worktree-tool 섹션 신설(git-sync-tool 직후) — 4서브명령(create/list/status/remove) 커맨드·ERROR_CODES 18종 카탈로그·응답 필드·exit code. 태스크별 코드 작업본 git worktree 격리 도구, 실물 `worktree_tool.py` 구현 기준 작성 (092) |
| v2.16 | 2026-08-16 15:05 | 종료 코드 표 근거 각주 정정 — 에러 코드 카탈로그 종수 리터럴(23종, stale) 삭제 후 `opal/tools/state-tool/README.md` §에러 코드 카탈로그 SSOT 포인터로 교체 (중복 SSOT 재발 방지, R-9 D-5 ①) (094 Step 14) |
| v2.17 | 2026-08-20 12:23 | memory-tool 섹션 정합 — `delete` 커맨드에 `--orphan --ref` 예시 추가, `review` 출력 예시 주석에 참조 무결성 검사(memory_file_missing/memory_file_unresolvable) 명시, 주요 에러 코드 표에 `memory_file_exists`·`orphan_ref_missing`·`memory_file_unresolvable` 3행 추가 + `memory_file_not_found` 의미를 "해석 성공 + 본문 부재"로 한정. 커맨드 종수(9) 무변경 (096) |
| v2.18 | 2026-09-02 14:05 | git-sync-tool 섹션 — `sync`에 `--root <경로>` 옵션 등재(순회 대상 밖 상위 root 저장소를 대상 선두 추가, `.git` 없으면 조용히 제외, 순회 결과와 중복 시 미계상, 미전달 시 현행 동일) + 출력 JSON에 `root` 필드 1행 추가. `<프로젝트>/workspace` 순회 시 프로젝트 root repo 누락 교정 |
| v2.19 | 2026-09-02 17:22 | 에이전트명·소유자 호칭 리터럴 제거 — 규범 산문은 역할어(`PM`/`사용자`/`소유자`)로, 산출물·보고 문면은 `{owner_name}` 플레이스홀더로 전환해 런타임에 소유자 호칭으로 대체된다. 프레임워크 재사용성 확보 (L2 직접 수정) |
| v2.20 | 2026-09-14 | §공통 도구 출력 계약 본문을 `opal/core/references/harness/tool-output-contract.md`(신규 하네스 owner 문서, `load: stage.execute`)로 분리하고 이 파일에는 포인터 2행만 남김 — tools.md는 정적 도구 카탈로그이므로 `harness/capability.md` 정적 카탈로그 금지 조항상 이벤트에 실을 수 없고, 런타임 가용성과 무관한 출력 규범만 `events.json` `stage.execute` `required_docs`에 편입했다. 규범 문면 무변경(이동), 기존 인용 6개소를 신규 owner 문서로 재지정 (131 W-13) |
| v2.21 | 2026-09-14 | 도구 절 13개(각 13~312행)를 제거하고 §도구 레지스트리 표 1개 + §도구 등록 절차로 축소 — 서브명령 수·오류 코드 수 등 복제 수치를 표에서 배제하고(낡음의 원천) 사용법 SSOT를 각 README로 단일화했다. 등재 범위를 13개에서 배포 도구 22개 전수로 확장(backlog-tool·date·doctor·event-loader·opal-agent·opal-cli·playwright-tool·self-pm-tool·skill-registry 9개 신규 등재). 각 행의 용도 1줄은 대응 README 개요에서 대조 확인했다 (131 W-16) |
