# 테스트

1. AC마다 관찰 결과와 검증 명령을 plan.md에 대응시킨다. plan.json checks는 argv 배열이다.
2. 버그 수정은 먼저 실패 재현 로그를 확보한다. 예상 이유로 실패하는지 확인하고
   기준 테스트를 보존한다. plan.json의 red_checks에 argv/exit_code/실패 이유를 적고
   protected_tests에 파일 경로를 넣는다. PLAN에서 Verifier가 role=red로 명령을 실행한다.
   전이 도구는 지정 exit와 로그를 확인한 뒤 테스트 해시를 고정하며 BUILD 이후 변경을 거부한다.
   실패의 의미는 Verifier가 직접 확인한다. 파일 쓰기 자체를 막는 hook은 별도 플랫폼 통제다.
3. Builder가 승인 파일을 구현하고 collect-evidence로 모든 검증 명령을 실행한다.
4. 별도 Verifier 세션이 AC/spec/plan을 읽고 동일 명령과 인접 회귀를 실제 실행한다.
5. UI는 브라우저로 사용자 흐름과 화면을 확인한다. 환경 부재는 blocked다.
6. 실패 수정은 BUILD rewind, 요구 자체 변경은 이전 단계 rewind로 처리한다.

collect-evidence <task> --role builder --actor <plan.builder> --argv '["python3","-m","unittest"]'
Verifier는 별도 actor와 role=verifier를 사용한다.
exit, stdout/stderr, 코드/아티팩트/log 해시를 도구가 기록한다.
실행 중 제품 파일이 바뀌면 stable=false이며 성공 증거로 인정하지 않는다.
추가 회귀가 필요하면 기존 승인 checks가 그것을 포함하는지 확인한다. 임시 읽기 진단은
별도로 실행할 수 있으나 필수 게이트 증거로 쓰려면 PLAN을 rewind해 명령과 조건을 갱신한다.

범위 검사는 init baseline과 현재 Git-visible 파일을 비교한다. ignore된 출력과 task
아티팩트 디렉터리는 제외한다. 제품 소스/테스트를 ignore하거나 task 디렉터리에 넣지 않는다.
현재 증거 snapshot은 단일 Git repo용이다. multi-repo는 각 repo에 별도 검증이 필요하다.

검증 4층: 아티팩트 구조·해시, 제품 unit/integration/E2E, 에이전트 행동 eval,
게이트의 실패 테스트. 의미 없이 형식만 일치하는 테스트를 만들지 않는다.
