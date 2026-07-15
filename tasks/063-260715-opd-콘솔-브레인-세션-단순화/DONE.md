# DONE: 콘솔 프로젝트 브레인 — 휘발성 단일 세션 + 진입/새대화 즉시 워밍

> 완료일: 2026-07-15 | 적용 스킬: opd | 모드: agentic
> 태스크: 063-260715-opd-콘솔-브레인-세션-단순화

## 작업 목표 (달성)

콘솔 프로젝트 브레인을 "멀티 대화 관리 + localStorage 이력 영속" 구조에서 **"휘발성 단일 세션 + 진입/새대화 즉시 워밍"**으로 단순화했다. 진행 중 대화 소멸 경로에 이탈 가드(R-8, 추가작업)를 더했다.

## 요구사항 이행

| R | 내용 | 결과 |
|---|------|------|
| R-1 | 단일 대화창 (멀티대화 UI 제거) | ✅ 좌측 사이드바·`BrainConversation[]`·`filterConversationsByProject`·`ConversationView` 제거 |
| R-2 | 이력 비영속 (localStorage 제거) | ✅ `STORAGE_KEY`·`loadConversations`/`saveConversations` 제거, 재오픈 시 백지 |
| R-3 | 오픈마다 새 세션 | ✅ mount 시 `sessionId = makeSessionId()` 발급 + 자동 prime |
| R-4 | 세션 내 멀티턴 유지 | ✅ 동일 sessionId `--resume` 웜 재개(BE 계층 불변) |
| R-5 | "새 대화" 버튼 (초기화+새세션+즉시) | ✅ `handleNewSession` — 내역 초기화+새 sessionId+prime |
| R-6 | 프라임 풀 여유 | ✅ `DEFAULT_POOL_SIZE=2` + `prewarm` need-based 충전(H-1 결함 수정) |
| R-7 | 세션 계층 정리 | ✅ 죽은 심볼 제거, `new_conversation` 폐기 필드 제거. prime/resume/status/job/멀티턴 유지 |
| R-8 | 이탈 가드 4경로 (추가작업) | ✅ 메뉴(useBlocker)·새로고침(beforeunload)·프로젝트 스위처(brainDirty)·"새 대화" — turns>0 시 확인 다이얼로그 |

## 변경 파일

**FE** (`dashboard/frontend/`)
- `src/pages/brain/BrainPage.tsx` — 단일세션 리팩터 + R-8 이탈 가드
- `src/components/app-shell/AppShell.tsx` — 프로젝트 스위처 이탈 가드
- `src/store/ui-store.ts` — `brainDirty`(non-persist) 추가
- `src/components/ui/alert-dialog.tsx` — shadcn 벤더 컴포넌트(신규)
- `src/test/setup.ts` — localStorage 폴리필(테스트 인프라)
- `src/pages/brain/brain-storage.test.ts`·`brain-new-conversation-prime.test.ts`·`brain-job-polling.test.ts` — 새 시그니처 정합·비영속 검증
- `src/pages/brain/brain-navigation-guard.test.tsx` — R-8 RTL 13케이스(신규)
- `package.json`·`package-lock.json` — `@radix-ui/react-alert-dialog`

**BE** (`dashboard/backend/`)
- `adapters/brain_session.py` — pool_size 2 + prewarm need 충전
- `models.py`·`routers/brain.py` — `new_conversation` 폐기 필드 제거
- `tests/test_brain.py` — pool 충전·연속 checkout·동시성 회귀 + S-2 결정론화

**문서**
- `docs/ARCHITECTURE.md` §OPAL Console — 휘발성 세션·풀 크기 2·need 충전
- `docs/PROJECT.md` — 변경이력 063

## 검증 결과 (All Pass)

- **자동**: FE vitest 85/85, BE pytest 249/1 skip. S-2 flaky→결정론화(10/10). tsc 0, ruff clean.
- **캡틴 통합**: E2E(멀티턴 S-7·재진입 S-9)·시각(레이아웃 S-18·답변품질 S-15)·R-8 4경로 — 전부 PASS(재배포본).
- **컨벤션**(GC-CONVENTION-2026-07-15T18-10): Critical 0/High 0 → 통과. Medium 4(@header exports)는 CLOSE에서 정합 완료. Low 3(PascalCase 관례 등)은 범위 밖.

## 설계 하이라이트

1. **H-1 결함 발견·수정**: `pool_size` 상수만 상향하면 `prewarm`이 풀당 1개만 충전해 R-6 무효 → `need=pool_size-have` 충전 로직 수정으로 연속 새대화 즉시 웜 확보.
2. **RED-first로 3개 테스트 설계결함 포착**: S-11(제거 헬퍼 의존)·brain-job-polling(옛 시그니처)·S-2(옛 타이밍 가정 flaky) — 모두 구현이 아닌 테스트/PLAN 결함으로, 구현-후 정비에서 해소.
3. **R-8 프로젝트 스위처 가드**: `useBlocker`가 라우트만 잡으므로, `brainDirty`를 ui-store에 노출해 AppShell 스위처가 인터셉트하는 방식으로 store 변경 경로를 가드.
4. **BE 세션 계층은 이미 대화별 격리** → 멀티대화 UI 제거해도 BE 로직 변경 최소(엔드포인트 5종 유지).

## 특이사항

- **완료기준 ④ 범위(R-63)**: "연속 새대화 즉시 웜"은 프라임 풀 토글 ON 프로젝트에 한정(060 opt-in 모델 유지 — 캡틴 확정).
- **잔여(범위 밖·후속)**: FE PascalCase 파일명·mypy 미설치·CONVENTIONS 명문화(PascalCase/shadcn 예외 061·063 반복 지적).
- **커밋 미수행**: 캡틴 지시 시에만 커밋.
- 전 과정 대행 일지: `AGENTIC-LOG.md`(게이트 6회 Pass·의사결정·오류·수정 이력).
