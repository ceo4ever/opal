# DONE: OPAL Console 브레인 질의 — fetch 타임아웃·ready 사각지대 견고화

> 완료일: 2026-06-23 | 스킬: opd | 모드: agentic | 상태: 완료

## 1. 목표 달성

브레인 질의가 콜드(≈69초)·웜(≈20초) 어느 경로든 브라우저 fetch 타임아웃("Load failed")에 끊기던 구조적 결함을 **동기 블로킹 → 비동기 잡(job)+폴링 전환**으로 근본 해소. ready 사각지대(인라인 콜드 폴백)는 비동기 전환에 자연 흡수.

## 2. 변경 사항

### BE (`dashboard/backend/`)
- `models.py` — `BrainJobSubmitResponse{job_id}`, `BrainJobResponse{job_id,status,answer,citations,error_msg}` 신규
- `adapters/brain_session.py` — `ConversationBrainSession._current_job` + `submit_job`(idempotent·즉시 job_id 반환)·`_run_job_background`(기존 `ask` 백그라운드 호출)·`get_job`(done/error 수신 후 TTL 제거). `BrainSessionRegistry` 위임. **`ask`/`opbr_adapter`/shell=False 불변**
- `routers/brain.py` — `POST /api/brain/query`를 job_id 즉시 반환으로 전환, `GET /api/brain/job/{job_id}` 신설(잡 소멸 graceful). 모든 query 실패가 잡 status=error로 일관 흡수
- `tests/test_brain.py`·`test_routers.py`·`test_brain_spike.py` — 계약 변경 테스트 재작성(동기 502 → 비동기 잡-error) + 신규 잡 폴링 테스트

### FE (`dashboard/frontend/`)
- `lib/api.ts` — `apiClient`에 선택적 `timeoutMs` + AbortController + AbortError→"요청 시간이 초과되었습니다" 메시지 변환(Safari "Load failed" 제거). 미전달 시 동작 불변(5화면 회귀 0)
- `pages/brain/BrainPage.tsx` — `queryMutation`→`submitMutation`(job_id 제출) + 잡 폴링 useQuery + `jobResponseToResolution`/`jobPollingInterval`/`BrainJobResponse` 헬퍼. **추가 UI**: Q&A 턴을 **아코디온**으로 전환(질문 헤더 / 답변 본문, 최신 턴 기본 펼침) — 테스트 중 캡틴 요청
- 신규 테스트: `lib/api-timeout.test.ts`, `pages/brain/brain-job-polling.test.ts`

## 3. 검증 결과

- **BE pytest: 216 passed × 2회 flaky 0**
- **FE vitest: 111 passed, typecheck exit 0, build exit 0**
- 신규 코드 린트 clean(ruff 0, eslint 0). 보안 Pass(시크릿 0·shell=False·anthropic SDK 미사용·무상태)
- **S-12 라이브(L3)**: 캡틴 배포본 테스트 후 CLOSE 승인 — Load failed 미재현 확인
- RED-first 준수(작성자=opal-test-agent/PM, 구현자=be/fe-agent 분리, 테스트 약화 0)

## 4. Known Issue / 후속

- **react-refresh/only-export-components 10건** (BrainPage.tsx): 036이 헬퍼를 컴포넌트 파일에 동거시킨 패턴. 별도 파일 추출 시 테스트 import 변경 필요(red-first 불변 위배) → 추출 리팩터는 별도 태스크. build·런타임 무영향
- **후속 최적화 태스크 (PoC 완료, 캡틴 합의)**: 브레인 질의 콜드 latency 경량화 — 검색을 brain-tool로 LLM 밖에서 결정론적 처리(0.15초) + 합성 1턴(≈21초)으로 멀티턴 에이전트 루프 압축 → 콜드 69초 대비 ~3.2배 단축 실증. 설계 결정 포인트: "질문→검색어" 변환 처리 방식. 권고 = opbr `--lite` 모드(DRY 유지). `.opal/MEMORY.md` 후속 메모리 참조

## 5. 진행 특이사항 (AGENTIC-LOG 참조)

- 워커 watchdog 중단 누적 — 근본원인은 RED 테스트(api-timeout.test.ts)의 `neverResolve` fetch 대역이 abort 무반응→테스트 959초 행. PM이 테스트 인프라 교정(대역 abort 반응·핸들러 선부착) → 0.48초로 정상화
- 미승인 폴백(`join 0.02s` flaky)·obsolete 502 테스트 3건·tsconfig 마스킹·신규 린트 3건 전부 PM Gate에서 차단·교정
- 전체 게이트 판단·교정 이력: `AGENTIC-LOG.md`

## 6. 배포

소스 `dashboard/`만 변경. 배포본(`~/.opal/dashboard-server/`)은 **캡틴이 install 재배포로 발효**(배포 경계). 커밋은 캡틴 지시 시 수행.
