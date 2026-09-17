# 워커 디스패치 시 worker.dispatch receipt 블록 누락

- 유형: improvement
- 상태: candidate
- 기록일: 2026-09-12

## 내용

태스크 118 TEST 단계에서 PM이 opal-convention-checker 디스패치 프롬프트에 worker.dispatch receip…

## 본문 복구 경위

이 행은 `improve-tool record --scope local`이 `memory-tool append`에 위임하면서 생성됐다.
`append`는 인덱스 행과 `file` 포인터만 만들고 본문 `.md`는 호출자가 쓰도록 되어 있는데,
`improve-tool`의 local 경로에 그 쓰기가 없어 생성 시점부터 본문이 없었다.

태스크 139 CLOSE 후 정리에서 인덱스 행의 `summary`를 원문으로 삼아 본문을 복구했다.
행을 지우지 않은 이유는 `summary`가 유일하게 남은 지식이기 때문이다 — 삭제하면
`.memory_provenance.log`에만 남고 조회 경로에서 사라진다.
