# DONE: 산출물 소유자 호칭을 identity.md owner_name 기준으로 하네스 통일

> 완료일: 2026-07-10 | 스킬: opds | 모드: agentic | 태스크: 054

## 무엇을 했나

산출물의 소유자 호칭이 로컬 `~/.opal/identity.md`의 `owner_name`이 아니라 세션에 로드된 레포 컨텍스트(MEMORY 브리핑·brain·직전 태스크 산출물)의 지배 호칭에 오염되던 결함을 **A(도구 집행) + B(문서 규칙) 공조**로 차단했다. 캡틴 질의로 발견된 brain ingest 경로 갭까지 추가 확장했다.

## 배경 (실증)

pointail 레포에서 확인: git author가 `Yoonhwan Jung <unani92@naver.com>`인 태스크 030·029·027 산출물이 전부 "캡틴 승인/직접확인"으로 기록됨(승인 호칭 29건 전부 캡틴, 그 외 0건). 원인은 `{owner_name}` 플레이스홀더 해석을 LLM에 맡겨, 로컬 identity 대신 레포 지배 호칭을 계승한 것. "매번 읽는다 ≠ 매번 그 값을 쓴다".

## 변경 내역

### A — 도구 집행 (state-tool)
- `opal/tools/state-tool/state_tool.py`: `resolve_owner_placeholder(text)` 헬퍼 신설 — note 저장 직전 `{owner_name}` 플레이스홀더를 `~/.opal/identity.md` `owner_name`으로 write-time 치환. note-write 6경로(`cmd_advance`/`cmd_mark`/`cmd_add_row`/`cmd_block`/`cmd_status`/`cmd_init`) 적용. fast-path(플레이스홀더 미포함 시 파일 I/O 없이 원문 반환)로 회귀 0, `OPAL_HOME` 기준 경로(플랫폼 독립), identity 부재/공란/파싱실패 시 원문 유지(try/except fail-safe), stdlib only(PyYAML 미도입).
- `opal/tools/state-tool/tests/test_state_tool.py`: `TestOwnerNamePlaceholder` 6케이스(S-1~S-7 매핑) — 치환·회귀·폴백 3종·advance+auto-pass 조합.
- `opal/tools/state-tool/README.md`: 6개 명령 절에 치환·폴백 계약 문서화 + 변경이력.

### B — 문서 규칙 (오염 차단 SSOT + 예시 통일)
- `opal/core/AGENT.md` §정체성 적용: "영속 산출물 호칭 = 매 작성 시점 identity.md `owner_name` 재해석, 레포 컨텍스트 계승 금지(오염 금지)" SSOT 신설.
- `opal/core/references/harness/state.md`: `{owner_name}` 플레이스홀더 사용 안내 참조 1줄(재서술 없이 AGENT.md 참조).
- pilot SKILL 8개(write-tech·data-design·sdd·project-dev·dev-wireframe·dev·dev-short·project) note 예시 `소유자 확인:` → `{owner_name} 확인:` 통일.

### B 확장 — brain ingest 오염 차단 (캡틴 질의 후속)
캡틴 확정 원칙: **운영 기록(작성자·승인)=owner_name(개인) / 재사용 지식(brain 페이지) 본문의 소유자 지칭=역할 일반어 "소유자"(특정 호칭 금지)**.
- `opal/core/AGENT.md` §정체성 적용: "재사용 지식(brain) 예외" 하위 규칙 추가 — 지식 본문은 역할 일반어로 일반화(출처가 개인 호칭 써도 지식엔 '소유자'), 운영 기록은 owner_name 유지.
- `opal/skills/op-brain-ingest/SKILL.md`: 하드코딩 "캡틴/PM 확정" → "소유자/PM 확정" + 작성 규칙에 "소유자 지칭 일반화(오염 금지)" 불릿 신설. (ingest 워커는 부트스트랩 스킵이라 규칙을 자기 SKILL.md에서 직접 적용.)

## 검증 결과

| 검증 | 결과 |
|------|------|
| TestOwnerNamePlaceholder 6케이스 (S-1~S-7) | ✅ All PASS (RED→GREEN, 회귀·폴백·조합) |
| 전체 스위트 회귀 | ✅ 203중 202 OK, 회귀 0 (1 FAIL은 034 하드코딩 경로 참조 기존 결함 — 무관) |
| S-8 `소유자 확인:` grep | ✅ 0건 |
| S-9 SSOT 규칙 존재 | ✅ AGENT.md + state.md 확인 |
| B 확장: op-brain-ingest 개인호칭 | ✅ "캡틴" 0건, "소유자/PM"+일반화 규칙 존재 |
| 배포 경계 | ✅ `opal/` 소스만 수정, `~/.opal/` 딸린 복사본 원상복구 확인 |

## 변경 파일 (054 — 15개, 053 잔여분과 분리)

`opal/tools/state-tool/{state_tool.py, tests/test_state_tool.py, README.md}` · `opal/core/AGENT.md` · `opal/core/references/harness/state.md` · `opal/skills/op-brain-ingest/SKILL.md` · `opal/skills/opal-pilot-{write-tech,data-design,sdd,project-dev,dev-wireframe,dev,dev-short,project}/SKILL.md`

## 남은 사항 / 후속

- **install 재배포 필요**: `opal/` 소스 변경 → `~/.opal/` 배포본 반영(state_tool.py 치환 로직 포함)은 install 실행 시 적용. (배포 경계 원칙)
- **커밋 미수행**: 캡틴 지시 대기. 커밋 시 **054 파일만** 스테이징 — 작업 트리의 `tools.md·brain-tool·.opal/brain` 등은 [053] 미커밋 잔여분이므로 분리.
- **기존 결함 후보**: `test_verify_passes_own_test_scenario_md`가 타 머신 하드코딩 경로(034) 참조로 상시 FAIL — 별도 태스크 후보.
