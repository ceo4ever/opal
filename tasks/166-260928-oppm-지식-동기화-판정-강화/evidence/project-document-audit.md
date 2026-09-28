# PROJECT 기반 문서 동기화 감사

## 결론

기존 계약만으로는 누락 없는 업데이트를 보장할 수 없었다. `PROJECT.md`를 읽고 레지스트리와 변경 파일을 대조하라고 했지만, 레지스트리 자체가 누락·노후했는지 확인하는 의무적 역추적과 경로별 종료 증거가 없었다. 따라서 “PROJECT에 없음” 또는 “기존 등재로 충분”이라는 자기참조 판정이 가능했다.

이번 변경은 PROJECT를 라우팅 인덱스로 한정하고 다음 독립 근거를 합쳐 후보 집합을 닫도록 보강한다.

1. TASK·계약·사용자 직접 지목
2. 변경·추가·삭제 파일과 프로젝트 구성 매핑
3. 변경된 규칙·인터페이스·경로·명칭의 직접 소비자·참조자 역검색
4. PROJECT의 용도·적용 범위·참조 시점 및 선별 문서의 필수 종속 원문
5. 8영역 의미 영향과 지식 저장소

이 후보 집합은 수정 범위 조사에서 한 번 만들고 TASK에 승계한다. 실행 중 새 결정·변경 파일로 넓어진 부분만 추가하며, 종료 시에는 처음부터 재검색하지 않고 최종 변경과의 정합성만 검증한다.

## 이번 변경의 후보 폐쇄표

- 역검색 범위: `scripts/`, `opal/`, `docs/`, 루트 `README.md`
- 검색어: `opal-self-pm`, `knowledge-sync`, `knowledge_impact`, `PROJECT`, `지식 동기화`
- 제외 근거: `docs/backup/`은 과거 백업, `docs/proposals/archives/`는 적용 완료 역사 기록이므로 현재 규범 후보에서는 제외하되 아래 archive 원천의 no-op을 별도로 확인했다.

| 경로 | 선별 근거 | 의미 영향 | 판정 | 확인 |
|---|---|---|---|---|
| `opal/skills/opal-self-pm/SKILL.md` | 절차 owner·직접 변경 | 지식 판정 기록과 보정 gate 절차 | update | §7·§8·호출표 정합화 |
| `opal/skills/opal-self-pm/references/knowledge-sync.md` | 판정 owner·직접 변경 | PROJECT 한계, 역추적, brain 기준, 스냅샷 교체 | update | 새 MUST와 예외 근거 확인 |
| `opal/skills/opal-self-pm/references/task-records.md` | 최종 확인 소비자 | 수정 요청과 새 gate 기록 | update | 종료 확인 4~5 정합화 |
| `opal/skills/opal-self-pm/README.md` | 사용자 대면 요약 소비자 | 변경된 절차 설명 | update | 동작 흐름 4~5 정합화 |
| `docs/PROJECT.md` | 컴포넌트·문서 라우팅 요약 | oppm의 선별 방식이 달라짐 | update | opal-self-pm 행 갱신 |
| `.opal/brain/pages/entity/opal-self-pm.md` | 기존 관련 WHY 페이지 | 누락 방지 설계 이유 재사용 | update | task:166 근거와 WHY 보강 |
| `opal/tools/self-pm-tool/**` | `knowledge_impact` 저장 소비자 | 기존 `--set-field`로 충분, 스키마 불변 | no-op | CLI README와 구현의 전체 교체 지원 확인 |
| `.opal/brain/pages/entity/self-pm-tool.md` | `opal-self-pm`의 도구 관계 페이지 | 도구의 책임·인터페이스 불변 | no-op | `--set-field` 설명이 이미 존재함 |
| `docs/ARCHITECTURE.md` | PROJECT 설계 문서 | 런타임 구조·인터페이스 불변 | no-op | 변경이 operator 규범 문서에 한정됨 |
| `docs/CONVENTIONS.md` | PROJECT 컨벤션 문서 | 새 프로젝트 전역 문서 형식 규칙 없음 | no-op | 기존 owner·도구 전용 쓰기 규칙 준수 |
| `docs/SECURITY.md` | PROJECT 보안 문서 | 권한·입력·비밀·외부 경계 불변 | no-op | 보안 표면 없음 |
| `README.md` | `//oppm` 공개 진입 링크 | 세부 동작은 skill 원문 포인터가 소유 | no-op | 링크·분류·사용자 표면 불변 |
| `scripts/install-mac.sh` | 스킬·도구 설치 소비자 | 파일 경로·실행 권한·복사 방식 불변 | no-op | 기존 자동 복사 루프가 수정 문서를 포함함 |
| `docs/proposals/archives/opal-pm-direct-execution.md` | 적용 완료된 역사 제안서 | 현재 규범 owner가 아님 | no-op | archive는 소급 수정하지 않고 owner·Brain에 반영 |

## 남는 한계

텍스트·코드 역검색은 의미적으로 암시된 비명시 관계까지 수학적으로 증명하지 못한다. 이번 계약이 보장하는 것은 “PROJECT 하나만 읽고 끝내지 않고, 관측 가능한 변경 표면과 직접 소비자·참조자 후보를 경로별로 닫는 것”이다. 검색 불가 외부 시스템이나 미등록 비문서 지식은 사용자·프로젝트 지침 없이는 완전성을 보장할 수 없으며, 발견 시 미확인 한계로 기록해야 한다.
