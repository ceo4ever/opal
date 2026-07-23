# DONE: 브레인 미실체 지식 등록 차단 게이트

> 완료일: 2026-07-23 | 적용 스킬: opds | 모드: agentic | 태스크: 071

## 1. 태스크 요약

브레인(지식 위키)에 "미실체 지식"(개선사항·오류·향후 계획·미확정 설계 등 아직 실재하지 않는 것)이 등록되는 것을 방지하는 **2층 차단 장치**를 추가했다. 확정·실재 지식(사용자가 판단해 지식화하는 query/ask synthesis 포함)은 그대로 허용한다.

**계기**: pointail 프로젝트의 `direct-delivery-mission-design.md`가 본문에 "아직 미착수, 설계 기록 단계"·"미확정 이슈"를 명시했음에도 `type: concept` / `status: active`로 등록되어, 미확정 설계가 확정 지식처럼 작동하는 문제가 실증됨. 근본 원인은 (1) 미실체 제외 판별 기준 부재, (2) 도구 게이트 부재였다.

## 2. 결과물 (2층 장치)

### 1층 — 판별 기준 명문화 (WHAT 규칙)
- `op-brain-ingest/SKILL.md` §STEP3 제외 기준에 "미실체 지식(개선·오류·향후·미확정 설계)" 행 + 판별 신호 1줄 + 에러 대응 표에 `speculative_content` skip-and-continue(CLOSE 비차단) 행 추가.
- `opal-brain/SKILL.md`는 op-brain-ingest §STEP3를 **SSOT로 참조만**(재정의 없음) + lint issue kind 표에 `speculative` 행.

### 2층 — 도구 게이트 (결정론적 backstop)
- `brain_tool.py` `cmd_add_page`: 신규 `--body-file`로 본문을 받아 미실체 마커 감지 시 거부(`speculative_content`). `--force --note "<사유>"`로만 우회(note 없는 `--force`는 백도어로 차단), 우회 시 frontmatter에 `speculative_override`/`override_note` 기록.
- `cmd_lint`: 신규 `speculative` kind로 이미 등록된 미실체 페이지 소급 검출(검출까지만, 자동 삭제·수정 없음).
- 탐지 = `detect_speculative_markers(title, body)`: title + `#` 섹션 헤딩만 스캔(산문 제외 → 오검출 최소화), 보수적 복합 토큰 사전(`SPECULATIVE_MARKERS`).
- `_score_page` term 한정 draft 필터(M-3)는 불변.

## 3. 변경 파일 (5개, 전부 `opal/` 소스)

| 파일 | 변경 |
|------|------|
| `opal/tools/brain-tool/brain_tool.py` | SPECULATIVE_MARKERS·detect_speculative_markers·ERROR_CODES[speculative_content]·add-page 게이트(--body-file/--force/--note)·lint speculative kind·argparse·@header [071] (+84줄) |
| `opal/tools/brain-tool/tests/test_brain_tool.py` | TestSpeculativeGate071 (TS-201~209) + make_args 확장 (+327줄, RED 작성) |
| `opal/skills/op-brain-ingest/SKILL.md` | §STEP3 미실체 행·에러표 speculative_content·--body-file 예시·변경이력 v1.6 |
| `opal/skills/opal-brain/SKILL.md` | 미실체 제외 SSOT 참조·lint speculative 행·--body-file·변경이력 v1.9 (M-3 무변경) |
| `opal/tools/brain-tool/README.md` | add-page --force/--note/--body-file·speculative_content·lint speculative·변경이력 v1.2 |

## 4. 검증 (All Pass)

- **pytest 127/127 통과** (신규 9 + 기존 118, 회귀 0) — PM 독립 3회 재확인.
- **RED-first 준수**: RED 5건 실패 증거(작성자 opal-test-agent) → GREEN 9/9 통과(구현자 opal-be-agent), 작성자≠구현자, RED 테스트 불변, `verify --red-check` pass.
- **실증**: pointail 등가 fixture(미착수·미확정 헤딩) → add-page 거부 + lint 검출, 정상 지식 → 통과(오검출 없음).
- **코드품질·보안 Pass**: 구문 유효, 시크릿 0, `--body-file` 읽기전용, 배포 경계 준수.

## 5. 배포 상태

- **install 배포는 캡틴이 직접 수행** (2026-07-23 캡틴 지시). 현재 소스(`opal/`)만 변경, `~/.opal/` 배포본 미갱신.
- 배포 후 검증: `~/.opal/tools/brain-tool/brain_tool.py`에 `speculative`/`body-file` 반영·소스 일치 확인 필요 (TEST-SCENARIO S-13).
- **op-brain-ingest(CLOSE Step3) 유보**: 신규 op-brain-ingest SKILL(--body-file 예시)은 미배포 brain-tool과 버전 불일치하므로, 배포 후 실행 권고. 배포 전 실행 시 skip 처리.

## 6. 미해결/후속

- **state-tool "다음 액션" 미갱신 결함** — STATE.md "## 다음 액션"이 init 값에 영구 고정(advance/mark에 갱신 경로 없음). 071과 별개의 state-tool(070 라인) 결함으로, 후속 태스크로 착수(캡틴 지시 2026-07-23).
- draft-term 경로(M-3)·미실체→memory 자동 이관(M-4)은 이번 범위 제외(향후).

## 7. 범위 밖 (의도적 제외)

- query/ask synthesis 지식화 흐름 — 정당하므로 불변.
- pointail 프로젝트 파일 정리 — 타 프로젝트 소관(별건).
