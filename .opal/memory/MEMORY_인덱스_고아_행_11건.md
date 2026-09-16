# MEMORY 인덱스 고아 행 11건

- 유형: improvement
- 상태: candidate
- 기록일: 2026-09-17 (태스크 137 CLOSE 회고)

## 관측

태스크 137 채번 시 `memory-tool task-number` 응답의 `review.violations`에 `memory_file_missing`이 11건 실렸다. `.opal/MEMORY.json` 인덱스 행의 `file` 포인터가 가리키는 `.opal/memory/*.md`가 실재하지 않는다.

## 왜 그냥 지우면 안 되는가

`delete`는 `dead`/`superseded` 상태 행만 제거한다(무손실 가드). 고아 행은 `promote`(본문 필수)와 `delete`(상태 가드) 어느 쪽으로도 도달할 수 없어 방치돼 있던 것이다.

## 정식 처방

`harness/memory-learning.md` §참조 무결성과 고아 행 정리가 규정한 `delete --orphan --ref <지식 귀착처>`가 정식 경로다. 본문이 실재하면 `memory_file_exists`로 거부하므로 무손실 가드를 우회하지 않고, 행의 `summary`가 `.memory_provenance.log`에 기록되어 데이터가 남는다.

상태를 임의 조작(`update --status superseded`)해 삭제를 강행하는 우회는 감사 추적을 오염시키므로 금지된다.

## 왜 별도 태스크인가

`--ref`에 각 행의 지식 귀착처를 적어야 하는데, 11건 각각이 어디로 졸업했거나 폐기됐는지 확인이 필요하다. 태스크 137과 무관한 선행 상태라 이번 범위에서 조치하지 않았다.
