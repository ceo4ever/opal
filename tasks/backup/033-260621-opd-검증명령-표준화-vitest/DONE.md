# DONE: OPAL 검증 명령 표준 명문화 + dashboard/frontend vitest 셋업

> 완료일: 2026-06-21 | 스킬: //opd --agentic | 결과: All Pass 13/13

## 작업 요약

OPAL 자동 검증 체계의 검증 명령을 캡틴 제시 4종 표준으로 명문화하고(트랙 A), 표준이 실제 동작하도록 `dashboard/frontend`에 vitest를 셋업했다(트랙 B). 두 트랙은 파일 집합이 분리되어 병렬 실행했다.

## 생성/수정 파일

### 트랙 A — 문서 정합 (5)
| 파일 | 변경 |
|------|------|
| `opal/skills/opal-pilot-project-dev/references/verification-loop-guide.md` | **SSOT** — §2 계층표 L1=`npm run lint:fix`·L3a=`npm test -- --run`, "watch 모드 금지(단발 실행)" 규칙 1문장 신규(L60 `[MUST]`), §검증 명령 결정 추론 키 보존, `--testPathPattern` 2건 Vitest식 치환 |
| `opal/skills/opal-pilot-project-dev/references/wbs-guide.md` | `--testPathPattern` 14건 → Vitest식(`--run <glob>`/`-t`) 치환, generic 금지 원칙(L46/175/264) 보존 |
| `opal/skills/opal-pilot-project-dev/references/roadmap-guide.md` | generic `&&` 명령의 `npm run lint`→`lint:fix` 정합 |
| `opal/skills/opal-pilot-project-dev/references/parallel-execution-guide.md` | 동일 lint:fix 정합 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | WBS 예시 표 lint:fix 정합 |

### 트랙 B — FE vitest 셋업 (5)
| 파일 | 변경 |
|------|------|
| `dashboard/frontend/package.json` | scripts `test`(`vitest run`)·`lint:fix`·`typecheck`(`tsc -b --noEmit`) + devDeps 4종 |
| `dashboard/frontend/package-lock.json` | 의존성 lock |
| `dashboard/frontend/vitest.config.ts` | 신규 — happy-dom/globals/setupFiles/@vitejs/plugin-react/alias |
| `dashboard/frontend/src/test/setup.ts` | 신규 — jest-dom 매처 등록 |
| `dashboard/frontend/src/lib/utils.test.ts` | 신규 — `cn()` 샘플 테스트 |

> 산출물: `TASK.md` / `ANALYSIS.md` / `PLAN.md` / `TEST-SCENARIO.md` / `AGENTIC-LOG.md` / `DONE.md`

## 검증 결과 (TEST — opal-test-agent 독립 재검증)

**All Pass 13/13** (트랙 A 문서 grep 6 + 트랙 B 동작 7)
- 트랙 B 실측: `npm test -- --run` exit 0(2 tests PASS, 202ms, watch 미진입) / `typecheck`(tsc -b --noEmit) exit 0 / `build` exit 0(회귀 0).
- 트랙 A 실측: `--testPathPattern` 실제 명령/예시 0건, watch 규칙 명문화, 추론 키 보존, generic 원칙 보존, 033 이력 5문서.
- 확정 버전: vitest@^4.1.9 / @testing-library/react@^16.3.2 / @testing-library/jest-dom@^6.6.3 / happy-dom@^20.10.6.

## agentic 진행 요약 (게이트 7회 — Pass 6 / Fail 1)

- **ANALYSIS 버전 환각 차단**: 워커가 구버전(vitest^2.1/RTL^15/happy-dom^12)을 "공식 입증"으로 단정 → PM `npm view` 실측 교차검증으로 차단, 정확 버전 재주입 후 재지시. (메모리 교훈 재현)
- **state-tool mock 가드 false positive 해소**: `state_tool.py:1321` 코드 패턴 정규식이 op-dev-test-scenario SKILL 표준 PM Gate 문구의 `MagicMock` **단어**를 오탐. 실제 mock 코드 0건 확인 후 문구의 트리거 단어 회피(의미 불변).
- 상세: `AGENTIC-LOG.md` 9개 엔트리.

## Known Issue / 후속

| 구분 | 내용 |
|------|------|
| Known Issue | `dashboard/frontend`의 기존 `shadcn/ui` 파일(badge/button/sidebar/toggle/use-mobile) eslint 위반 6건 — 본 태스크 무관(changed_files 미포함), Surgical 범위 밖. |
| 🐛 프레임워크 버그 | `state_tool.py` `_MOCK_CODE_PATTERNS`가 op-dev-test-scenario SKILL 표준 문구의 `MagicMock` 단어를 오탐(주석은 "단순 단어 제외" 의도). → 패턴을 코드 호출 형태(`MagicMock(`)로 한정하거나 SKILL 문구 조정 필요. **별건 후속 태스크 권고.** |
| 후속 — install 재배포 | 소스(`opal/skills/**`·`dashboard/frontend/**`) 변경이 `~/.opal/` 배포본에 미반영. 재배포해야 검증 표준·vitest 실발효. (캡틴 보류 — 별도 진행) |
| 후속 — 커밋 | task 032 + 033 변경 누적. 캡틴 명시 지시 시 커밋. |
