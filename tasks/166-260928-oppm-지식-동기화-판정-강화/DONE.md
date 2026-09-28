# DONE: oppm 지식 동기화 판정 강화

## 결과

- PROJECT를 관련 문서의 라우팅 인덱스로 한정하고, 레지스트리만으로 완전성을 주장하지 못하게 했다.
- TASK 직접 지목, 변경·추가·삭제 파일, 직접 소비자·참조자, PROJECT 적용 범위, 필수 종속 원문을 합쳐 후보 집합을 닫게 했다.
- 역검색 범위·검색어·결과와 경로별 `선별 근거 / 의미 영향 / 판정 / 확인`을 증거로 남기게 했다.
- PROJECT에서 선택한 경로·패턴의 실재 여부와 코드 경로↔문서 폴더 별칭 매핑까지 확인하게 했다.
- 수정 범위 조사에서 찾은 지식·문서를 영향 후보로 승계하고, 실행 중에는 새 범위만 증분 보강하며, 종료 시에는 전체 재탐색 없이 최종 변경과 정합성만 검증하게 했다.
- 의미 있는 하네스·스킬 규범 변경은 Brain WHY 동기화 대상으로 우선 판정하며, “owner 문서가 SSOT”는 단독 no-op 사유가 될 수 없게 했다.
- `knowledge_impact`는 append 이력이 아니라 현재 8영역 스냅샷으로 전체 교체하게 했다.
- 최종 확인에 대한 수정 의견은 확인으로 간주하지 않고, 기존 gate를 보정 응답으로 닫은 뒤 재검증·새 gate를 요구하게 했다.

## PROJECT 기반 누락 가능성 재확인

기존 상태로는 누락 없는 업데이트를 보장할 수 없었다. PROJECT 자체가 불완전할 때 이를 탐지할 독립 절차가 없었기 때문이다. 이번 보강 뒤에도 의미적으로만 연결된 외부 관계까지 절대적으로 탐지한다고 주장하지 않는다. 대신 저장소에서 관측 가능한 변경 표면과 소비자·참조자를 재현 가능한 검색으로 닫고, 검색 불가능한 관계가 완료 조건을 좌우하면 미확인 한계로 남겨 최종 확인을 차단한다.

상세 후보 폐쇄표: `evidence/project-document-audit.md`

## pug 가상 실행 결과

`/Volumes/Data/StoreLinkStudio/pug`에는 쓰지 않고 기존 태스크 010·015를 입력으로 절차를 재생했다.

- PROJECT의 `.opal/MEMORY.md` 포인터는 깨져 있고 실제 자산은 `MEMORY.json`이다.
- 실제 Brain이 존재하지만 PROJECT 문서 레지스트리에는 반영되지 않았다.
- 코드 영역 `frontend_admin`과 문서 폴더 `fe-admin`의 별칭이 명시되지 않았다.
- 문의 담당자 자동 지정은 Brain에는 있지만 정책서 800권에는 없다.
- 쇼핑적립은 Brain·backend 문서에는 있지만 포인트 정책·IA·사전·논리·물리·DDL에서 검색되지 않았다.
- 기존 태스크 015가 남긴 정책·IA·OUT 경로 후속뿐 아니라 데이터 설계 4계층까지 새 절차가 후보로 포착했다.

가상 판정은 `PASS WITH FINDINGS`다. 세부 후보와 8영역 판정은 `evidence/pug-virtual-run.md`에 기록했다.

## 변경 파일

- `opal/skills/opal-self-pm/SKILL.md`
- `opal/skills/opal-self-pm/references/knowledge-sync.md`
- `opal/skills/opal-self-pm/references/task-records.md`
- `opal/skills/opal-self-pm/references/question-loop.md`
- `opal/skills/opal-self-pm/README.md`
- `docs/PROJECT.md`
- `.opal/brain/pages/entity/opal-self-pm.md`
- `.opal/brain/index.md`
- `.opal/brain/log.md`
- `.opal/MEMORY.json`
- 태스크 166 수행·검증 문서

## 검증

- PROJECT 관련 문서·소비자 역추적 및 후보 폐쇄표: PASS
- 정적 계약 20문구: missing 0
- self-pm-tool 회귀 테스트: 6 passed
- `git diff --check`: PASS
- `code-scan validate --changed`: `ok: true`, `newly_uncovered: 0`, 기존 pre-existing 3
- Brain 검색 노출·대상 lint: PASS, 대상 이슈 0
- pug 읽기 전용 가상 실행: PASS WITH FINDINGS, 경로 실재·별칭 검증 규칙 추가
- E2E: 비런타임 규범 문서 변경으로 미실행; 대체 검증·미검증 한계 기록

## 지식 동기화

| 영역 | 판정 | 근거 |
|---|---|---|
| 기획 | no-op | 제품 정책·사용자 흐름은 바뀌지 않았다. |
| 설계 | no-op | 런타임 구조·인터페이스·데이터 모델은 바뀌지 않았다. |
| 프로젝트 문서 | update | `docs/PROJECT.md`의 oppm 설명을 PROJECT 라우팅+변경 표면 역추적+현재 판정 전체 교체로 갱신했다. |
| CONVENTIONS | no-op | 전역 코드·문서 형식 규칙이 아니라 oppm 전용 절차이며 기존 owner 규칙을 지켰다. |
| SECURITY | no-op | 권한·인증·비밀·입력·외부 쓰기 경계 변경이 없다. |
| brain | update | 기존 `pages/entity/opal-self-pm.md`에 task:166의 설계 WHY를 갱신하고 검색·lint를 확인했다. |
| memory | no-op | 재사용할 장기 WHY는 Brain에 반영했고 별도 다음 세션 주의사항은 없다. 태스크 번호 bump는 실행 메타데이터다. |
| code-scan | no-op | 변경 대상 validate 결과 신규 uncovered 0이며 기존 pre-existing 3뿐이다. |

## 미해결·후속

- 문서 의미 관계의 절대 완전성은 자동 증명할 수 없다. 이번 변경은 관측 가능한 후보의 누락 방지와 미확인 한계의 명시적 차단을 보장한다.
- pug 자체에서 발견한 정책·설계·PROJECT 불일치는 이번 읽기 전용 검증에서 수정하지 않았다.
- 설치본 `~/.opal/`에는 쓰지 않았다. 소스 배포·install은 별도 권한과 절차가 필요하다.

## 사용자 확인

- 캡틴 최종 승인: “승인”
- 태스크 166 종료 승인 확인
