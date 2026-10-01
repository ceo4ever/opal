# 권한과 통제

lifecycle CLI: 단계 순서, 구조, source/승인/코드 해시, 파일 범위, 실행 exit/log,
역할 ID 분리, 재시도 상한을 검사한다. 기존 OPAL 도구는 작업본을 통제한다.

approve <task> --gate PLAN --actor <사용자이름> --reference <실제메시지ID>
는 승인 기록 인터페이스이지 인증 서비스가 아니다. 실제 승인 없이 호출하지 않는다.
고위험 운영은 승인 쓰기 권한을 별도 서비스·보호 CI 환경으로 제한한다.
Reviewer 이름이 다르다는 것만으로 독립성은 증명되지 않으므로 실제 별도 세션을 호출한다.

로컬 도구를 우회한 직접 파일/API 변경까지 차단하지 않는다. 필요한 강제 경계는
플랫폼 hook·OS sandbox·required checks·CODEOWNERS·환경 승인으로 집행한다.
미설치 통제를 활성 상태로 보고하지 않는다. 로그에 비밀을 남기지 않는다.
