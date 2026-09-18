# 새 템플릿 진입 확인

> 2026-09-09 | TASK 단계에서 수행한 검사 기록. ANALYSIS 단계 완료 보고가 아님.

- `opd` 레지스트리 매칭: `opal-pilot-dev`, `/Users/iskang/.opal/skills/opal-pilot-dev/SKILL.md`.
- 실행 모드: 명시 플래그가 없어 기본 `semi-agentic`.
- 태스크 번호: memory-tool 첫 응답 110이 기존 폴더와 충돌하여 한 번 더 원자 채번, 111 사용. 기존 110번 폴더 변경 없음.
- 기존 제안 폴더를 본 태스크 `templates/`로 이관. MAMS 원본 변경 없음.

## 검사 결과

명령:

```sh
/Users/iskang/.opal/tools/state-tool/run.sh verify tasks/111-260909-opd-SDLC-템플릿-하네스개편 --clarification-check
```

실제 응답:

```json
{"ok":true,"command":"verify","clarification_check":"skipped","reason":"no '## 명확화 결과' section (backward-compat skip)"}
```

판정: 오류 없이 반환했지만 새 TASK의 목표·범위·제약·완료 기준은 검사하지 않았다. **필수 정보 검증 PASS로 해석하지 않는다.** 새 양식의 누락 검사를 실제로 집행하도록 파서·게이트를 개편해야 한다.

TASK 본문의 4요소는 Proposed outcome / Affected users and systems / Constraints / Acceptance criteria에 있다. 시간 측정 기준과 실제 적용 대상은 Open questions에 남아 있다. 구현 및 성능 목표 달성을 승인·완료한 상태가 아니다.

## 다음 단계에 넘길 질문

1. 명확화 검사 외에 구형 절·열 이름에 의존하는 소비자는 어디인가?
2. 신규 형식 누락은 거부하면서 기존 태스크 호환성을 유지하려면 형식 판별을 어디서 해야 하는가?
3. 사용자에게 중복 표를 쓰게 하지 않고 새 형식으로 파이프라인을 진행하는 최소 변경 순서는 무엇인가?

## ANALYSIS 중 PM 추가 재현

실제 DB·외부 API 호출 없이 임시 입력 파일로 CLI를 호출했다. 임시 파일은 제거했고 반환 JSON만 보존했다.

| 검사 | 정상 입력 | 필수 항목 제거 입력 | 의미 |
|---|---|---|---|
| 새 TASK 명확화 | skipped, exit 0 | Acceptance criteria 절 제거도 skipped, exit 0 | 새 형식의 필수 정보 미검사 |
| 구형 TASK 명확화 | pass, exit 0 | 완료기준 행 제거 시 clarification_gate_unmet, exit 1 | 구형 양식의 누락 검사는 작동 |
| 커버리지 하위 도구 | AC-1이 있으나 시나리오가 없으면 exit 16 | 모든 배열이 빈 경우 all_covered=true, exit 0 | 추출 실패가 빈 분모로 넘어가면 누락을 검출하지 못함 |

증거: [clarification-probe.json](clarification-probe.json), [coverage-probe.json](coverage-probe.json).

커버리지 결과는 `scenario-coverage-check`만의 동작이다. 독립 평가자까지 포함한 전체 목표-커버 게이트를 실행·통과한 결과가 아니다.

현재 소스 `opal/tools/state-tool/state_tool.py:977`은 게이트 산출물의 존재를 검사하고, `:1004`는 체크리스트를 출력한다. 새 ANALYSIS의 내용 검토를 파일 존재 검사만으로 대체할 수 없다. `:2553`의 PLAN 파일 추출은 구형 `### 4.2`와 `**파일**:`에 의존한다. 이 사실은 ANALYSIS 워커 결과와 함께 검토한다.
