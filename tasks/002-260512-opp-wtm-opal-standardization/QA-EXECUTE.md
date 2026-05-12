# QA: EXECUTE — wtm-agent OPAL 표준화 + cmux 통합 + 사용자 surface 재사용

> 검토일: 2026-05-12 | 판정: **Pass**

## 1. 요약

EXECUTE 워커가 PLAN §3의 12 Step을 모두 완료하여 11개 파일 변경 + 2개 파일 삭제(agents/wtm-agent/ 디렉토리)를 수행했습니다.

- **신규 도구**: `opal/tools/cmux-tool/` (래퍼 + README)
- **신규 에이전트**: `opal/agents/opal-wtm-agent/AGENT.md` (표준 7단계 구조, JSON 8필드)
- **SSOT 갱신**: 5개 파일(SKILL.md v1.9, agents.md, install-mac.sh v2.2, docs 3개)
- **삭제**: `agents/wtm-agent/` 완전 제거, 모든 참조 갱신

산출물의 완전성, 정합성, 안전 가드 3계층이 모두 검증되었습니다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| **GE-1** | PLAN §3 Step 1~12 체크박스 | Pass | 모두 [x] 갱신 |
| **GE-2** | 변경된 파일 11개 + 삭제 2개 | Pass | 모두 존재/삭제 확인 |
| **GE-3** | TASK R-1~R-13 AC 충족 | Pass | 모두 구현 완료 |
| **C-1** | wtm-agent 단어 경계 잔존 | Pass | 0건 (변경이력 제외) |
| **C-2** | Crawl4AI web-to-markdown 관련 잔존 | Pass | 0건 (SKILL 변경이력 v1.1/1.2/1.4 예외) |
| **C-3** | agents/wtm-agent/ 삭제 + opal-wtm-agent 존재 | Pass | 디렉토리 미존재 + AGENT.md 존재 |
| **C-4** | SKILL.md + agents.md 워커 경로 일치 | Pass | opal-wtm-agent로 통일 |
| **C-5** | install-mac.sh 멱등성 | Pass | chmod 블록 + 재실행 무방 |
| **C-6** | docs 5개 파일 wtm-agent 갱신 | Pass | 모두 opal-wtm-agent 또는 공백 처리 |
| **C-7** | 변경이력 포맷 통일 | Pass | YYYY-MM-DD HH:mm KST + (002) 통일 |
| **Q-1** | 한국어 + 영어 규칙 준수 | Pass | 본문/코드/필드명 구분 준수 |
| **Q-2** | kebab-case 네이밍 | Pass | opal-wtm-agent, cmux-tool |
| **Q-3** | YAML frontmatter 유효성 | Pass | opal-wtm-agent frontmatter 정상 |
| **Q-5** | 변경이력 행 포맷 일관 | Pass | 모든 파일 단일 표준 포맷 |
| **F-6** | 환경 외부 호출 → fallback:phase3 | Pass | JSON 오류 + exit 2 |

## 3. 지적 사항

### Info (진행 영향 없음)

1. **TASK.md 체크박스 미갱신** (Info)
   - R-9, R-10, R-12, R-13은 실제로 구현되었으나 TASK.md의 [ ]가 [x]로 업데이트되지 않음
   - 원인: EXECUTE 워커가 PLAN 검증 범위만 담당, TASK.md 갱신은 PM 책임 (opal-harness.md §1 Guards)
   - 해소: 추가 작업 불필요 (PM이 QA Pass 후 사후 갱신 처리)

2. **PM 사전 발견 사항 재검증 완료** (Info)
   - wtm-agent 단어 경계 5건: 모두 변경이력 행 (허용)
   - Crawl4AI 2건: SKILL v1.1/v1.2/v1.4 변경이력 + docs-guide.md 초기화 가이드 (web-to-markdown 무관)
   - 판정: 모두 예외 정책 적용 OK, 지적 사항 없음

### Warning (없음)

모든 검증 항목이 Pass. Warning 미발견.

### Critical (없음)

모든 구현이 설계와 정합, 제약 조건 위반 미검출.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1~R-8 AC | Step 1~8 산출물 정합 | Pass |
| PLAN.md §2 핵심 설계 | JSON 8필드 SSOT 스키마 | Pass — 4개 산출물 일치 |
| PLAN.md §3 Step 1~12 | 실행 체크리스트 완료 기준 | Pass — 모두 [x] |
| 안전 가드 3계층 | cmux-tool ↔ opal-wtm-agent ↔ SKILL.md | Pass — 계층 간 정합 |
| install-mac.sh 배포 | cmux-tool chmod +x + 변경이력 | Pass — 멱등성 보장 |

## 5. 판정

**Pass**

EXECUTE 산출물이 PLAN의 모든 설계 요구사항을 충족하였습니다.

- GE-1~GE-3: 모두 통과 (파일 완전성, TASK AC 충족)
- C-1~C-7: 모두 통과 (일관성 및 정합성)
- Q-1~Q-5: 모두 통과 (문서 품질)
- F-6 (정적 검증): 통과 (폴백 분기 정상)
- 안전 가드: 통과 (3계층 책임 분리 정합)

**F-1~F-5, F-7~F-10 skip 항목**은 cmux 실환경 통합 테스트 필요로 EXECUTE 단계 QA 범위 외. PM Gate에서 별도 처리 예정.

**TASK.md 체크박스 미갱신** (R-9, R-10, R-12, R-13)은 구현은 완료되었으나 PM 책임 항목.

---

## 부록: 스킬별 산출물 명세

### 신규 산출물 (3개)

1. **`opal/tools/cmux-tool/run.sh`** (8.4 KB, chmod +x)
   - 입력: `<url> [--mode <full|clean|wireframe>] [--wait <ms>]` + `--surface <handle> [<url>]`
   - 출력: JSON 8필드 (`ok`, `method`, `mode`, `surface`, `user_owned`, `title`, `final_url`, `content`)
   - 모드: A (신규), B (현재 페이지), C (surface + navigate)
   - 안전: B/C 모드 cleanup 절대 금지 (정적 검증 1회만 tab close)

2. **`opal/tools/cmux-tool/README.md`** (5.3 KB)
   - 도구 사용 가이드 + 의존성 + 에러 코드 + 안전 가드

3. **`opal/agents/opal-wtm-agent/AGENT.md`** (5.9 KB)
   - Frontmatter: `name: opal-wtm-agent`, `model: light`, `color: green`, `icon: 🌐`
   - 프로세스: opal-task-agent 표준 7단계
   - 결과: JSON 8필드 (표준 5 + 도메인 3: `method`, `mode`, `user_owned`)
   - 변경이력: v1.0 (2026-05-12 21:35 KST, 002)

### 수정 산출물 (8개)

| 파일 | 변경 내용 | 버전/날짜 |
|------|----------|----------|
| `skills/web-to-markdown/SKILL.md` | §호출 인터페이스 3모드 + §Phase 2 cmux + §Phase 3 playwright-tool CLI + §의존성 표 + §워커 이름 + §결과 보고 B/C 경고 | v1.9 (2026-05-12 21:35) |
| `opal/core/references/agents.md` | §opal-wtm-agent 섹션명 + 역할 재정의 + Phase 폴백 명시 + JSON 8필드 + 에이전트 경로 | v1.4 (2026-05-12 21:35) |
| `scripts/install-mac.sh` | 변경이력 v2.2 + cmux-tool chmod +x 블록 + cmux 의존성 안내 | v2.2 (2026-05-12 21:35) |
| `docs/PROJECT.md` | L50 agents/ 행: wtm-agent 제거, 현재 비어있음 표기 | - |
| `docs/CONVENTIONS.md` | L21 범용 에이전트: wtm-agent 제거, 현재 비어있음 표기 + OPAL 표준 명시 | - |
| `docs/ARCHITECTURE.md` | L49 다이어그램 + L141 표 + L275 트리뷰: wtm-agent → opal-wtm-agent | - |
| `opal/skills/opal-agent-creator/SKILL.md` | L66 예시: wtm-agent → opal-wtm-agent | - |

### 삭제 산출물 (2개)

| 항목 | 상태 |
|------|------|
| `agents/wtm-agent/AGENT.md` | 삭제 |
| `agents/wtm-agent/` (디렉토리) | 삭제 |

