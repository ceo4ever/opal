# oppm 태스크 기록 정식화 — 수행 결과

## 변경

- 신규 oppm 작업은 정식 `tasks/{NNN}-{YYMMDD}-oppm-{태스크명}/`에서 관리한다. 기존 oppm 재개는 같은 폴더를 유지한다.
- TASK.md·DONE.md를 PM 수행·사용자 검토 기록으로 필수화했다. PLAN.md 등은 필요 시 작성하며 문서별 파이프라인·승인 게이트는 만들지 않는다.
- PROJECT 레지스트리 기반 문서·코드·컨벤션 선별을 진입에 연결했다. 이미 읽은 유효한 내용은 재사용하고 변경·범위 확대 시 다시 확인한다.
- self-pm-tool과 run-log-tool에 공통 실행 ID를 전달한다. 진행·결정·검증·재시도와 보고·사용자 게이트 사건을 발생 시점에 기록하고 종료 전에 검증한다.
- 지식 영향이 있으면 실제 갱신·추가·검증 후 반영 경로와 근거를 남기도록 보강했다.

규칙 원문: `opal/skills/opal-self-pm/SKILL.md`, `references/task-records.md`, `references/question-loop.md`, `references/knowledge-sync.md`.

## 검증·배포

실제 CLI에서 공통 ID 초기화·표준 사건 append·중복 요청 멱등성·재조회·validate-run 통과. Pilot 3-SSOT가 생기지 않음을 확인했다. YAML·참조·code-scan·diff 검사와 설치 스크립트 배포를 마쳤고 배포본 6개 파일이 소스와 바이트 일치한다. 자세한 결과와 검증 범위는 [VALIDATION.md](VALIDATION.md).

일반 skill-creator 검사기는 기존 OPAL 확장 메타데이터를 지원하지 않아 OPAL 스키마를 유지한 별도 검사로 확인했다. 독립 에이전트의 전체 대화 루프 실사용 검증은 수행하지 않았다. 도구 코드나 Console 태스크 집계 동작은 변경하지 않았다.

## 지식 동기화

| 영역 | 결과·근거 |
|---|---|
| 기획 | update — oppm 스킬·수행 기록 참조에 사용자 요구 반영 |
| 설계 | update — docs/ARCHITECTURE.md에 문서·현재 기록·사건 로그 책임 반영 |
| 프로젝트 문서 | update — docs/PROJECT.md의 oppm·self-pm-tool 설명 갱신 |
| CONVENTIONS | update — 정식 oppm 태스크의 필수·선택 기록 구분 |
| SECURITY | no-op — 도구 권한·외부 입력·보안 기준 변경 없음 |
| brain | update — brain-tool update-page로 opal-self-pm의 추적·재개 설계 이유 갱신, 인덱스 자동 갱신 |
| memory | no-op — 별도 운영 주의사항 없음. 정식 채번은 memory-tool로 154 발급 |
| code-scan | update — 스킬과 신규 참조의 현재 설명·exports 헤더 반영, validate 통과 |

## 기록

- 태스크: 154 / 사용자 변경 요청: 2026-09-24
- 실행 ID: `run_154_oppm_records`
- 실행 사건: `run/run-log-run_154_oppm_records-0001.jsonl`
- 사용자 보강 의견을 반영했으며, 사용자 요청에 따라 태스크 변경을 커밋한다. push는 요청되지 않음.

## 대상 프로젝트 적용 보강

대상 PROJECT 문서로 실제 동기화 경로를 선별하고, 8영역은 누락 방지 관점으로 사용한다. 수정 전 기존 공통·영역별 컨벤션·설정 확인, 테스트 증거 보존, opal-e2e 적용 검토를 필수화했다. README·프로젝트 레지스트리·brain에도 반영했다.

- 재현 정보·검사 명령·exit·원출력·소스 해시: [followup-validation.json](evidence/followup-validation.json)
- 소스/설치본 해시 일치: [followup-deployment.json](evidence/followup-deployment.json)
- 첫 검사 시 설치 도구 교체 중 경로 부재로 중단된 기록: [followup-attempt-1.txt](evidence/followup-attempt-1.txt). 설치 후 재검증 통과.
- E2E 적용 검토: `opal-e2e/SKILL.md` 확인. 앱 UI/API 동작 변경 없는 문서 변경이므로 E2E 미실행, 구조·참조·설치 정합 검사로 검증. 독립 에이전트의 전체 대화 루프 수행은 미검증.
