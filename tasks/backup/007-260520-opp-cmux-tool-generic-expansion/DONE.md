# DONE: 007 cmux-tool 범용 확장 + wtm-agent fallback 체인 재배선

> 적용 스킬: opp | 모드: semi-agentic
> 시작: 2026-05-20 20:02 | 완료: 2026-05-23 00:02
> 태스크 폴더: `tasks/007-260520-opp-cmux-tool-generic-expansion/`

## 작업 목표 (TASK.md 인용)

기존 `opal/tools/cmux-tool/`을 cmux browser 공식 명령을 다목적으로 노출하는 디스패처로 확장하고, `opal/references/tools.md`에 정식 등록하여 알투/워커가 웹 크롤링·E2E·정보 수집·웹 테스트에 자동으로 도구를 인식·활용하도록 한다. 동시에 `opal-wtm-agent`의 호출 체인을 cmux-tool 1순위·playwright-tool fallback 형태로 재배선한다.

## 산출물

### 태스크 산출물 (5건)

| 파일 | 역할 |
|------|------|
| `TASK.md` | F-1~F-7 / R-1~R-7 / M-1~M-7 / D-7a~e (재채번 + cmux/ 흡수·재배치 결정 포함) |
| `PLAN.md` | v1.3 — §2.1~§2.9 핵심 설계 + 10 Step + QA 25항목 + 리스크 R-T1~R-T8 |
| `QA-PLAN.md` | verdict=pass_with_recommendations (25/28 Pass + 3 Info) |
| `QA-EXECUTE.md` | verdict=pass (25/25 Pass) |
| `AGENTIC-LOG.md` | semi-agentic 모드 경계 통과 기록 + 워커 디스패치 이력 |

### 변경 파일 (16건 + 1건 정리)

**신규 8건** (cmux-tool 디스패처 확장)

| 파일 | 역할 |
|------|------|
| `opal/tools/cmux-tool/lib/dispatch.sh` | 12+1종 서브명령 라우터 + B/C cleanup 가드 |
| `opal/tools/cmux-tool/lib/cmux-helpers.sh` | `_lib.sh` 흡수 — surface 헬퍼 |
| `opal/tools/cmux-tool/lib/branch.sh` | `test-browser.sh` L65-100 분기 결정 일반화 |
| `opal/tools/cmux-tool/lib/json.sh` | python3 JSON 직렬화 헬퍼 |
| `opal/tools/cmux-tool/examples/e2e-form-fill.sh` | click+fill+wait+snapshot E2E 레시피 |
| `opal/tools/cmux-tool/examples/e2e-branch-auto.sh` | A/B/C 분기 자동 결정 (test-browser 원형 보존) |
| `opal/tools/cmux-tool/examples/claude-hooks.sample.json` | Claude Code hooks 3종 샘플 |
| `opal/tools/cmux-tool/docs/CMUX-REFERENCE.md` | CLI 18종 + Socket API + 단축키 + hooks 통합 참조 |

**수정 6건**

| 파일 | 변경 내용 |
|------|---------|
| `opal/tools/cmux-tool/run.sh` | 디스패처 재설계, URL 자동 라우팅, `phase3→phase2` 치환 |
| `opal/tools/cmux-tool/README.md` | 12+1종 사용법 + 흡수 자산 출처 표 + 변경이력 v1.1 (007) |
| `opal/core/references/tools.md` | `## cmux-tool` 섹션 신규 + 5행 트리거 매트릭스 + 변경이력 |
| `opal/agents/opal-wtm-agent/AGENT.md` | silent fallback 분기(`command -v cmux`) + method `cmux\|playwright-cli` + 변경이력 v1.1 (007) |
| `skills/web-to-markdown/SKILL.md` | Phase 호칭 일관 + `--browser` 보존(deprecated alias) |
| `scripts/install-mac.sh` | L843-848 lib/examples chmod 블록 확장 |

**정리 (git 추적 보존 후 삭제)**

| 자산 | 처분 |
|------|------|
| `tasks/007-260520-opp-cmux-tool-generic-expansion/cmux/` (전체) | git commit 866c766 사전 add 후 `rm -rf` — 흡수 출처는 신규 파일 헤더 주석 + README §흡수 자산 출처 표 + git 히스토리 3중 추적 |

## 핵심 결정 (M-1 ~ M-7) + 캡틴 정책 (2026-05-22)

| # | 결정 |
|---|------|
| M-1 | WebFetch 완전 제거 — 2단(cmux → playwright) 체인 |
| M-2 | 12+1종 서브명령 노출 (필수 7 + 선택 5 + 레거시 `extract`) |
| M-3 | 공통 5필드(`ok`/`command`/`surface`/`user_owned`/`error`) + 명령별 특화. `extract` 8필드 100% 보존 |
| M-4 | tools.md 5행 트리거 매트릭스 (웹 크롤링/정보 수집/웹 테스트/E2E/로컬 SPA) |
| M-5 | playwright 폴백 트리거 4종(`not_in_cmux`/`cmux_not_installed`/`surface_parse_failed`/`open_failed`). 입력 정정 5종은 즉시 에스컬레이션 |
| M-6 | `cmux-tool/` 하위 `lib/` + `examples/` + `docs/` 3개 디렉토리 |
| M-7 | cmux/ 자산 11종 처분 — 흡수 7 / 폐기 4 |
| 캡틴 정책 | cmux 사용자 선택 옵션 / playwright 자동 설치 유지 / silent fallback (wtm-agent 경유 한정) / 단독 호출 시 cmux-tool 단일 책임 / `command -v cmux` 단일 분기로 OS+설치 동시 흡수 |

## QA 결과

| 단계 | verdict | 결과 |
|------|---------|------|
| PLAN QA | pass_with_recommendations | 25/28 Pass + 3 Info (영역 간 용어 / WebFetch 제거 근거 / Step 의존성 표현) |
| EXECUTE QA | pass | 25/25 전항목 통과, 발견 문제 0건 |
| PM 자체 검증 | pass | B/C 가드(L512·535) / silent 분기 4회 / `--browser` 7회 / git commit 866c766 / install-mac.sh L843-848 확장 |

## sparring 검증 5건 처리 결과

| 공격 | 처리 |
|------|------|
| #1 cmux/ git 추적 미검증 | EXECUTE Step 1 직전 git add + commit 866c766 — git log 추적 보존 |
| #2 Chromium 자동 설치 누락 우려 | `install-mac.sh:976-981` 자동 설치 확인 — 해소 |
| #3 cmux 시그니그 PLAN 미검증 | EXECUTE Step 2 외부 SSOT(D-20 cmux 공식 문서) WebFetch 검증 — `fill --text` 플래그 발견 반영 |
| #4 `--browser` 모드 외부 호환성 | `skills/web-to-markdown/SKILL.md` 4곳 발견 — 보존(deprecated alias)로 재결정 |
| #5 fallback 에러 코드 SSOT 불명확 | PLAN §2.5에 "cmux-tool/run.sh가 SSOT, 갱신 순서 (1)run.sh→(2)README→(3)tools.md→(4)AGENT.md" 명시 |

## 캡틴 정책 적용 결과 (PLAN v1.2/v1.3)

- cmux 미설치 시 사용자 안내·유도 단계 없음 — silent로 playwright 직행
- `summary` 필드에 cmux 미감지 표기 없음 (캡틴 Q1=b)
- cmux-tool 단독 호출 시 자체 fallback 로직 없음 — 단일 책임 유지
- `uname -s` 명시 OS 분기 없음 — `command -v cmux` 단일 분기로 흡수
- install-mac.sh Chromium 자동 설치 흐름 그대로 (캡틴 Q1=d)

## 006 충돌 처리

- 다른 PC 알투의 `006-260520-opp-install-linux` (CLOSE 완료)와 채번 충돌
- 본 태스크는 006 → 007로 재채번 (폴더 rename + 4개 파일 19곳 일괄 치환 + MEMORY.md `last_task_number: 7`)
- `tasks/006-260520-opp-install-linux`는 그대로 보존
- Linux 사용자는 `scripts/install/linux.sh`로 OPAL 설치 + 이번 silent fallback 정책으로 자동 playwright 직행 (자연 정합)

## 잔여 미해결

없음. 모든 R-1~R-7 / M-1~M-7 / R-T1~R-T8 처리 완료.

## 후속 태스크 후보

| 후보 | 사유 |
|------|------|
| `playwright-tool` tools.md 등록 | 이번 범위 외(캡틴 Q2=b 결정). 동일 골격으로 등록 필요 |
| cmux 워크플로우 자산(start-all/stop-all/open-dev/analyze-log) OPAL 통합 | F-5 분리 — `tasks/006-260520-opp-install-linux`(다른 PC)의 후속 흐름과 결합해 별도 태스크에서 처리 |
| cmux 명령 시그니처 버전별 어댑터 | R-T1 후속 — cmux 0.65+ 시그니처 변경 대응 (`cmux_subcommand_unsupported` 에러 코드 추가 검토) |
| `--browser` 모드 정식 deprecation cycle | R-T4 — 현재 alias 유지, 후속 태스크에서 사용 빈도 측정 후 제거 판단 |
| EXECUTE 후 통합 테스트 | cmux 설치 환경에서 12+1종 서브명령 + wtm-agent silent fallback 실제 동작 검증 |

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-23 00:02 | 초기 작성 — 태스크 007 CLOSE 마감 보고 |
