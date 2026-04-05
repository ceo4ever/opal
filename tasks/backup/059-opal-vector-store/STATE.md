# STATE: OPAL 프로젝트 문서 벡터 스토어

> 최종 갱신: 2026-04-01 09:30

## 현재 상태
- 모드: Project Task
- 단계: TASK ✅ / PLAN ✅ / EXECUTE
- 진행: -
- 상태: 대기 중

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | ✅ 완료 |
| PLAN.md | ✅ 완료 |
| QA-PLAN.md | ✅ Pass |
| QA-EXECUTE.md | 대기 |
| DONE.md | 대기 |

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | TASK | 글로벌 DB (~/.opal/vector.db) + 프로젝트별 네임스페이스 | git 영향 없음, 프로젝트 간 격리 |
| 2 | TASK | 로컬 임베딩 모델 사용 | 외부 API 의존 제거, 완전 로컬 동작 |
| 3 | TASK | opal/tools/ 소스 구조 | 기존 skill-registry와 동일한 배포 패턴 |
| 4 | PLAN | Node.js 런타임 선택 | 기존 도구 일관성, 의존성 경량 (~50MB vs PyTorch ~2GB) |
| 5 | PLAN | Xenova/all-MiniLM-L6-v2 임베딩 모델 | 384차원, ~22MB ONNX, 서버 불필요, 충분한 품질 |
| 6 | PLAN | @sqliteai/sqlite-vector + better-sqlite3 | 공식 Node.js 지원, npm 패키지 제공 |

## 블로커
없음

## 다음 액션
캡틴 승인 후 EXECUTE 단계 진행
