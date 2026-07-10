# ADD_DONE-3: backlog-tool update-task 서브명령

| 필드 | 내용 |
|------|------|
| 추가작업 번호 | ADD-3 |
| 일시 | 2026-07-10 17:57 ~ 18:37 (KST) |
| 사유 | 056 드라이런에서 Evaluator가 T01 수용기준 표기 불일치를 지적했으나 반영 경로 부재(손편집 금지 원칙상 재등록만 가능). "Evaluator 지적 → PM 반영" 사이클의 tool-gated 경로 필요 |
| 변경 내용 | `update-task --id [--title/--slice/--acceptance/--area/--priority/--depends/--parallel-group]` 신설 — 지정 필드만 갱신 + updated_at + BACKLOG.md 재렌더 + fcntl 락. 가드: 무필드 `no_fields_to_update`·done 태스크 `task_already_done` 거부·status 인자 자체 부재(상태 전이는 mark 전용)·depends 실재 검증. harness §9 backlog-tool 행 7서브명령 현행화(v6.2, PM 직접) |
| 변경 파일 | opal/tools/backlog-tool/{backlog_tool.py, README.md(v1.1), tests/test_backlog_tool.py(+4)} · opal/core/references/opal-harness.md(v6.2, PM) |
| 검증 결과 | RED 4 failed → GREEN 22/22. 통합 256 passed. install 재배포 후 배포본 `update-task -h` 정상 |
