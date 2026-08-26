# RED-EVIDENCE — RED 배치 R1·R2·R3 실패 증거

> 작성일: 2026-08-25 16:58 | 작성 주체: PM (워커 응답을 옮긴 뒤 **PM이 직접 재실행해 확증**)
> 규약: `~/.opal/references/harness/red-first.md` §1 — RED 증거 없이 GREEN 진입 금지
> 작성자≠구현자: RED 테스트 작성 워커와 BE 구현 워커는 별개 주체다

## 1. 생성·수정 파일

| 파일 | 상태 | 케이스 |
|------|------|--------|
| `dashboard/backend/tests/test_cache.py` | 신규 | 5 |
| `dashboard/backend/tests/test_stats.py` | 신규 | 11 함수 (파라미터화 전개 20건) |
| `dashboard/backend/tests/test_routers.py` | 기존 확장 (**추가만**, 기존 케이스 수정·삭제 0건) | +15 함수 (전개 16건) |
| `dashboard/backend/tests/fixtures/t103_states/` | 신규 | 동결 픽스처 22개 JSON |

**프로덕션 코드 변경 0건** — `git status` 실측으로 `dashboard/backend/` 하위 `tests/` 밖 변경이 없음을 확인했다. `stats.py`는 아직 존재하지 않는다.

## 2. RED 실행 결과 — PM 재실행 확증 (2026-08-25 16:57)

| 배치 | 명령 | 결과 | 실패 사유 | 판정 |
|------|------|------|----------|------|
| R1 | `python3 -m pytest dashboard/backend/tests/test_cache.py -q` | **2 failed, 3 passed** | `assert None == {'total_minutes': 425}` — `set(source_path=...)` 직후 `get()`이 `None`. P-8 시계 혼용(monotonic `cached_since` ≈ 6.1e5 vs epoch mtime ≈ 1.78e9)이 그대로 재현 | **의도한 RED** |
| R2 | `python3 -m pytest dashboard/backend/tests/test_stats.py -q` | **20 failed** | 전건 `ModuleNotFoundError: No module named 'dashboard.backend.stats'` | **의도한 RED** |
| R3 | `python3 -m pytest dashboard/backend/tests/test_routers.py -q` | **16 failed, 55 passed** | `KeyError: 'stats'` ×9 · `KeyError: 'workflow_stats'` · `'completed_tasks'` · `'artifact_by_type'` · `assert 'owner' in {'row','stage','status','updated_at'}` · `assert 5 == 9`(화이트리스트) · `assert [0,1,0,1,2,…] == [1..19]`(그룹별 0-based 리셋) | **의도한 RED** |

오타·문법 오류로 인한 실패 **0건**. R1의 3 passed는 이미 성립 중인 불변식(공개 시그니처 · `TTL_SECONDS` · `source_path=None` 경로)이다.

## 3. 기존 테스트 회귀 — 0건

| 시점 | 결과 |
|------|------|
| 작업 전 기준선 | `249 passed, 1 skipped` |
| 작업 후 기존 케이스만 | `249 passed, 1 skipped, 16 deselected` — **동일** |
| 전체 | `38 failed, 252 passed, 1 skipped` (38 = 2+20+16 신규 RED / 252 = 249 + R1의 3 통과) |

## 4. 커버리지

- **커버 21건** — TS-001~009(R2) · TS-010~015 · TS-018 · TS-020~023(R3) · TS-016(R1). PM이 지시한 RED-first 대상 전건.
- **범위 밖** — TS-017·024는 회귀 시나리오로 PLAN Step 8 소유. TS-030~047(FE vitest) · TS-050~053(산출물 검사) · TS-060~063(L2/L3)은 R1~R3 배치 밖. TS-019는 원 문서 결번.

## 5. 구현 워커에게 넘기는 제약 3건

1. **TS-008은 엄격하다** — `stats.py`의 import 허용 집합을 `{__future__, datetime, statistics}`로 닫았다(TS-008 · PLAN §8 문면 그대로). `from __future__ import annotations`를 쓰면 `typing` 없이 구현 가능하니 우회하지 마라.
2. **TS-018은 벽시계가 아니라 캐시 payload 구조로 단정한다** — 30초 대기 없이 결정론을 얻기 위해, `cache.get("task_detail:{project}:{task_id}")`가 돌려주는 payload의 키를 재귀 수집해 `is_running`·`current_elapsed_minutes`·`current_elapsed_label`이 **없어야** 한다고 단정한다. 캐시 키 형식은 PLAN §3.2.2가 현행 유지로 고정했다.
3. **TS-021은 이동값을 2단으로 나눴다** — 코호트 21건 ID로 필터한 `tasks[].total_minutes` 중앙값(799/276/75)은 무조건 단정하고, `wait_ratio` 21/4/54와 `median_minutes` 직접값은 「완료 태스크 집합 == 동결 코호트」인 동안에만 단정한다. `102`가 완료돼도 거짓 실패하지 않는다.

## 6. 절차 기록

본 문서는 RED 작성 워커가 아니라 **PM이 작성**했다. PM이 디스패치 프롬프트 §9에 「`tasks/` 폴더에 파일을 만들지 마라」를 넣어 워커가 `TEST-SCENARIO.md` §3.0이 지시한 `RED-EVIDENCE.md`를 남길 수 없었다(PM 지시 오류 — `SCENARIO-GATE-1.md` §5와 동일 패턴, 2회째). 표의 실행 결과는 PM이 직접 재실행해 확증한 값이다.
