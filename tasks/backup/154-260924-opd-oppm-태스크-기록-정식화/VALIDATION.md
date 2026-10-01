# 실행 검증

- 공통 실행 ID 초기화·사건 append·중복 요청 멱등성·현재 기록 재조회·validate-run 통과
- Pilot 3-SSOT 미생성 확인

설치된 두 도구를 격리된 임시 태스크에서 실제 호출. 임시 디렉터리는 검증 후 제거. 스킬 지시를 에이전트가 끝까지 준수하는 독립 실사용 검증은 수행하지 않음.

- OPAL frontmatter 기존 확장 키·alias·triggers 유지, YAML 및 참조 경로 검증 통과. 일반 skill-creator 검사기는 기존 alias/domain/pipeline/triggers를 지원하지 않아 적용 불가(기존 스키마 유지).
- code-scan validate --changed 전체 변경 목록: exit 0, coverage 62.5% (5/8). 기존 docs 3개는 헤더가 없어 비차단이며 신규 스킬 참조 헤더 포함 확인.
- git diff --check 통과.
- scripts/install-mac.sh 메뉴 1 설치 성공, Console /health 정상. 스킬·참조 5개와 도구 README 배포본 총 6개 바이트 일치.

## 대상 프로젝트 적용 보강

대상 PROJECT 문서로 실제 동기화 경로를 선별하고, 8영역은 누락 방지 관점으로 사용한다. 수정 전 기존 공통·영역별 컨벤션·설정 확인, 테스트 증거 보존, opal-e2e 적용 검토를 필수화했다. README·프로젝트 레지스트리·brain에도 반영했다.

- 재현 정보·검사 명령·exit·원출력·소스 해시: [followup-validation.json](evidence/followup-validation.json)
- 소스/설치본 해시 일치: [followup-deployment.json](evidence/followup-deployment.json)
- 첫 검사 시 설치 도구 교체 중 경로 부재로 중단된 기록: [followup-attempt-1.txt](evidence/followup-attempt-1.txt). 설치 후 재검증 통과.
- E2E 적용 검토: `opal-e2e/SKILL.md` 확인. 앱 UI/API 동작 변경 없는 문서 변경이므로 E2E 미실행, 구조·참조·설치 정합 검사로 검증. 독립 에이전트의 전체 대화 루프 수행은 미검증.
