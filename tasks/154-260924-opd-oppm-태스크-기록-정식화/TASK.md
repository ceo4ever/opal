# oppm 태스크 기록 정식화

사용자 요청(2026-09-24)에 따라 `oppm`의 기록 위치와 PM 수행 문서 계약을 수정한다.

- 정식 태스크 폴더를 채번해 사용하고 임시 폴더·프로젝트 루트로 폴백하지 않는다.
- PROJECT 문서 레지스트리에서 관련 문서·코드·컨벤션을 선별한다. 현재 세션에서 읽은 유효한 내용은 재사용한다.
- TASK.md·DONE.md는 필수 수행 기록, PLAN.md와 기타 문서는 필요할 때 작성한다. 단계 산출물이나 별도 문서 승인 게이트로 만들지 않는다.
- 실행 사건은 run-log-tool로 남기며 self-pm-tool의 현재 기록과 역할을 구분한다.
- 마무리에는 관련 프로젝트 문서를 실제 갱신·추가하고 검증 근거를 남긴다.

범위: `opal/skills/opal-self-pm/`, 도구 사용 안내, `docs/PROJECT.md`, `docs/CONVENTIONS.md`, `docs/ARCHITECTURE.md`, 관련 brain 페이지. 도구 스키마·파이프라인·Console 변경은 제외한다.

완료 기준: 스킬의 진입·재개·기록·종료 지시가 모순 없이 연결되고, 예시 명령이 실제 도구에서 동작하며, 관련 문서와 배포본이 일치한다.

근거: `opal/skills/opal-self-pm/SKILL.md` §2·§7, `opal/core/references/pm/dispatch-process.md` Steps 1~3, `opal/core/references/harness/task-process.md` §태스크 번호 채번 규칙, `docs/run-log/CONTRACT.md` §1.2·§1.3.

## 사용자 보강 요구

- 이 저장소는 OPAL FW 소스이며 oppm의 사용처는 실제 구현 프로젝트다. 대상 PROJECT에서 동기화할 실제 문서와 지식 경로를 찾아야 한다.
- 코드·설정 수정 전에 기존 공통·영역별 컨벤션 및 실제 설정을 확인한다.
- 테스트의 실행 대상·명령·결과·증거를 보관하고 opal-e2e 스킬 적용을 반드시 검토한다. E2E 실행이 불필요하거나 불가능하면 이유·대체 검증·남은 한계를 기록한다.
