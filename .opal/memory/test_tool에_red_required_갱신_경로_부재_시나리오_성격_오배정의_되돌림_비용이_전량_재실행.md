# test-tool에 red_required 갱신 경로 부재 — 시나리오 성격 오배정의 되돌림 비용이 전량 재실행

- 유형: improvement
- 상태: candidate
- 기록일: 2026-09-15

## 내용

TEST-SCENARIO 작성 시 보존·회귀 가드형 시나리오(S-9)를 '구현 전 RED'로 잘못 배정했다. 구현 전에 이미 통과하는 시나리오…

## 본문 복구 경위

이 행은 `improve-tool record --scope local`이 `memory-tool append`에 위임하면서 생성됐다.
`append`는 인덱스 행과 `file` 포인터만 만들고 본문 `.md`는 호출자가 쓰도록 되어 있는데,
`improve-tool`의 local 경로에 그 쓰기가 없어 생성 시점부터 본문이 없었다.

태스크 139 CLOSE 후 정리에서 인덱스 행의 `summary`를 원문으로 삼아 본문을 복구했다.
행을 지우지 않은 이유는 `summary`가 유일하게 남은 지식이기 때문이다 — 삭제하면
`.memory_provenance.log`에만 남고 조회 경로에서 사라진다.
