# TEST: 부트스트랩 이벤트 하네스 경량화

## 판정

- 결과: **All Pass**
- 시나리오: S-1~S-12, 12 pass / 0 fail / 0 blocked
- 환경: macOS source worktree + `~/.opal` 설치본
- Windows: `pwsh` 미설치로 installer 정적 parity만 검증했다. 실제 Windows 실행은 별도 환경의 후속 확인 대상이다.

## 시나리오 결과

| ID | 결과 | 실행 근거 |
|---|---|---|
| S-1 | Pass | 잠긴 RED 증거 3건을 보존했고 event-loader 회귀 8/8이 missing receipt, stale hash, wrong event, missing required document를 구조화 오류로 거부했다. |
| S-2 | Pass | 잠긴 RED 증거를 보존했고 memory-tool 회귀 188/188이 `--boot-brief --max-bytes 1024 --memories 3 --history 0`를 포함해 통과했다. 실프로젝트 boot brief는 370 bytes, active memory 1개, history 0개였다. |
| S-3 | Pass | 잠긴 RED 증거를 보존했고 opal-agent 회귀 27/27과 source audit resolver 6케이스가 marker/setting 우선순위를 통과했다. |
| S-4 | Pass | 3회 측정에서 일반 비서 41,703→9,374 bytes(77.52% 감소), 프로젝트 인지 비서 119,644→9,744 bytes(91.86% 감소)로 모두 30KB 이하·70% 이상 감소를 만족했다. |
| S-5 | Pass | `[WORKER]`, `[ASSISTANT]`, 무마커 프로젝트/비프로젝트, `bootstrap: off`, 첫 줄이 아닌 marker를 포함한 6케이스가 명시된 session event로 해석됐다. |
| S-6 | Pass | 14개 표준 event 전체가 원문·SHA-256·bytes를 담아 load/verify 통과했고, missing/stale/wrong-event fixture는 non-zero JSON 오류로 거부됐다. |
| S-7 | Pass | `opal-harness.md`는 40,265→3,688 bytes(90.84% 감소)의 event/owner 호환 인덱스로 축소됐고 event static-check와 금지 구형 문구 검색이 0건이었다. |
| S-8 | Pass | 실제 TEST dispatch receipt를 `worker.dispatch`/4 documents/41,932 bytes로 재검증했다. 15개 worker 모두 missing/wrong/stale receipt의 blocked 계약을 갖고 static-check 누락 0건이었다. |
| S-9 | Pass | static-check가 pilot 10개·worker 15개를 전부 검사해 violation 0건을 반환했고 4개 bootstrapper body parity가 통과했다. |
| S-10 | Pass | 설치 전 snapshot 후 `OPAL_AUTO_INSTALL=1 ./scripts/install-mac.sh`를 실행했고 부모 installer exit 0을 확인했다. source/installed 핵심 15경로 SHA-256 parity와 설치본 static-check가 통과했다. |
| S-11 | Pass | 아래 payload/time 3회 측정, 설치 로그, parity, hub/worktree status를 기록했다. |
| S-12 | Pass | PM이 설치 전부터 존재한 W5B hub 교차 작성 15파일을 직접 복구한 뒤, hub에는 기존 `.opal/AGENT.md`, `.opal/worktree.json`, untracked task112/task113만 남았다. worktree HEAD는 `abbeda6`, branch는 `feat/OP-TASK-113`이며 commit·merge·worktree 제거·CLOSE 진입은 없었다. |

## Cold-start 측정

`scripts/tests/task113_bootstrap_audit.py --mode source --iterations 3`로 측정했다. 변경 전은 git `HEAD` blob을 materialize한 뒤 3회 읽었고, 변경 후는 event-loader `measure`와 제한된 memory-tool subprocess를 3회 실행했다. 사용자별 `identity.md`는 양쪽에서 제외했다.

| 상태 | 변경 전 payload | 변경 후 payload | 감소율 | 변경 전 평균/최대 | 변경 후 평균/최대 |
|---|---:|---:|---:|---:|---:|
| 일반 비서 | 41,703 B | 9,374 B | 77.52% | 0.069 / 0.088 ms | 0.587 / 0.760 ms |
| 프로젝트 인지 비서 | 119,644 B | 9,744 B | 91.86% | 45.633 / 47.271 ms | 44.677 / 45.416 ms |

일반 비서의 후처리 시간은 단순 blob read보다 manifest/receipt 처리가 추가되어 커졌다. 이 수치는 LLM 컨텍스트 적재 시간이 아닌 로컬 I/O·subprocess 측정이므로, payload 감소와 분리해 해석해야 한다. 프로젝트 boot brief는 370 B, active memory 1개, history 0개였다.

## 설치·회귀 검증

- 설치 전 `~/.opal` 핵심 16파일의 존재·bytes·SHA-256를 `/tmp/task113-preinstall.json`에 기록했다.
- 비대화형 설치 부모는 exit 0으로 완료했고 Console health `ok` 출력을 확인했다. 설치 후 선택적 `console scan` 하위 `find`가 장기 I/O 대기하여 installer가 non-fatal로 규정한 해당 자식만 TERM했고, 부모는 강제 종료하지 않았다.
- `events.json`, event-loader 3파일, `opal-harness.md`, harness owner 9파일, `pm/activation.md` 총 15경로의 source/installed SHA-256가 일치했다.
- 설치본 event-loader static-check는 14 events, violation 0건이었다.

## 회귀·품질 검증

| 검증 | 결과 |
|---|---:|
| event-loader | 8 pass |
| memory-tool | 188 pass |
| opal-agent | 27 pass |
| state-tool | 420 pass, 3 skip |
| task113 source integration | 2 pass |
| `git diff --check` | Pass |
| Bash syntax + Python compile | Pass |
| 변경 69파일 hardcoded secret pattern scan | 0 hit |
| 변경 Markdown 수기 누적 이력 절 | 0 hit |

## 증거 산출물

- 설치 전 snapshot: `/tmp/task113-preinstall.json`
- 설치 로그·exit: `/tmp/task113-install.log`, `/tmp/task113-install.exit`
- source 측정: `/tmp/task113-source-audit-postinstall.json`
- 설치 parity: `/tmp/task113-installed-parity-after-rerun.json`
- state-tool 회귀: `/tmp/task113-state-tests.log`, `/tmp/task113-state-tests.exit`
- 결과 SSOT: `test-scenario.json`
