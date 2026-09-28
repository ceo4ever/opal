# TASK: oppm 지식 동기화 판정 강화

## 요청과 문제

태스크 165에서 `opal-self-pm`이 하네스 작성 규칙을 바꾸면서도 “owner 문서가 SSOT”라는 이유로 brain을 처음 `no-op` 판정했다. 캡틴의 피드백 뒤에야 변경의 WHY를 brain에 반영했으며, 기존 `knowledge_impact`에는 이미 잘못된 판정이 남아 전체 교체가 필요했다.

캡틴은 태스크 165 마무리 후 이 `oppm` 문제를 직접 개선하라고 요청했다.

## 목표와 완료 기준

- 의미 있는 하네스·스킬 규칙 변경을 Brain `no-op`으로 닫을 때 허용되는 근거를 제한한다.
- owner 문서의 현재 사실(WHAT)과 Brain의 결정 이유(WHY)를 중복 없이 함께 유지하는 기준을 명시한다.
- 지식 판정을 재수행하면 `knowledge_impact`의 현재 8영역 판정을 전체 교체해 상충 기록이 남지 않게 한다.
- 최종 확인 뒤 수정 요청을 받은 경우 기존 gate 응답과 보정 후 새 최종 확인을 기록하는 절차를 명시한다.
- `PROJECT.md`를 유일한 완전성 증거로 오인하지 않고, 변경 표면과 소비자·참조자를 역추적해 관련 문서 후보를 닫는 절차를 명시한다.
- 수정 범위 조사에서 찾은 지식·문서를 영향 후보로 승계하고, 실행 중 증분 보강·종료 시 최종 변경 정합성 검증만 수행해 중복 탐색을 없앤다.

## 작업 계약

1. 목표/완료조건: `oppm`이 규범 변경의 지식 영향을 놓치지 않고, 재판정 시 현재 판정이 단일하게 남도록 계약을 강화한다.
2. 포함/제외 범위: `opal-self-pm` 규범·PROJECT 해당 요약·Brain과 pug 읽기 전용 가상 실행 포함; pug 파일 쓰기, CLI 스키마·상태 머신·다른 파이프라인 변경 제외.
3. 변경 대상: `opal/skills/opal-self-pm/SKILL.md`, `references/knowledge-sync.md`, `references/task-records.md`, README, `docs/PROJECT.md`, 관련 Brain 페이지와 태스크 166 증거. pug는 변경 대상이 아니다.
4. 결정/가정: owner 문서는 WHAT, Brain은 재사용할 WHY를 소유한다. “owner가 SSOT”만으로 Brain `no-op`은 불가하다. PROJECT는 라우팅 인덱스이며 초기 영향 후보를 만들 때 경로 실재·별칭과 변경 표면을 교차 확인한다. 종료 시 전체 재탐색 없이 증분·최종 정합만 확인하고 재판정은 8건 전체 교체한다.
5. 검증 방법: PROJECT 후보 폐쇄 감사, pug 태스크 010·015 읽기 전용 가상 실행, 정적 계약 검색, 관련 도구 테스트, code-scan validate, Brain 검색·lint.
6. 예상 영향: `oppm`의 완료 직전 지식 판정과 수정 피드백 처리 규범이 강화된다. pug에는 쓰기 영향이 없으며 제품 런타임·보안·CLI 데이터 형식은 바뀌지 않는다.

## 승인 근거

- 실행 요청: “태스크 마무리 후에, oppm 스킬의 문제점을 개선해줘”
- 범위 근거: 직전 피드백 “기존 하네스를 수정하는건데, 지식에 반영이 되어야 하지 않나?”
- 추가 검증 요청: “관련 문서들이 PROJECT.md를 읽어서 판정을 해서 누락없이 업데이트가 가능한지 다시 확인해줘.”
- 실제 프로젝트 가상 검증 요청: “`/Volumes/Data/StoreLinkStudio/pug` 해당 프로젝트를 기준으로 스킬 작동을 가상으로 테스트”
- 프로세스 보정 승인: 수정 범위 조사 때 찾은 지식·문서를 정리하고, 변경 후 3·4·5 검증을 거쳐 적용하는 흐름에 “승인”
- 위 발화가 문제와 후속 작업을 구체적으로 지정하므로 동일 범위의 직접 수정 승인을 충족한다.

## 참조와 제약

- `opal/skills/opal-self-pm/SKILL.md`
- `opal/skills/opal-self-pm/references/knowledge-sync.md`
- `opal/skills/opal-self-pm/references/task-records.md`
- `docs/PROJECT.md`
- `docs/CONVENTIONS.md`
- `.opal/brain/pages/entity/self-pm-tool.md`
- 프로젝트 소스만 수정하며 설치본 `~/.opal/`에는 쓰지 않는다.
- 태스크 165의 오판과 보정 기록은 역사적 증거로 보존한다.
- 기존 사용자 변경 `.claude/skills/`, `docs/proposals/gc-verification-task-drafts.md`는 건드리지 않는다.

## 실행 기록

- run_id: `run_0a9a9cb4-30ce-4ef7-9dfe-ab5dfdf1f43f`
- self-pm: `.opal/self-pm/run_0a9a9cb4-30ce-4ef7-9dfe-ab5dfdf1f43f.json`
- run-log: `run/run-log-run_0a9a9cb4-30ce-4ef7-9dfe-ab5dfdf1f43f-0001.jsonl`

## 상태

- 최종 승인 완료
