# STATE: OPAL Vector Store — sqlite-vec 기반 문서 벡터 검색 도구

> 최종 갱신: 2026-04-08 15:30

## 현재 상태
- 모드: Project Task
- 단계: TASK ✅ / PLAN ✅ / EXECUTE
- 진행: -
- 상태: 사용자 확인 대기

## 완료 산출물
| 산출물 | 상태 |
|--------|------|
| TASK.md | ✅ |
| PLAN.md | ✅ |
| QA-PLAN.md | ✅ Pass (조건부) |
| QA-EXECUTE.md | ⬜ |
| DONE.md | ⬜ |

## 의사결정 로그
| # | 시점 | 결정 | 근거 |
|---|------|------|------|
| 1 | TASK | sqlite-vec(MIT) 선택 | sqlite-vector Elastic License 2.0 라이선스 리스크 제거 |
| 2 | TASK | 전체 내용 청크 저장 | 제목만 저장 시 시맨틱 검색 품질 대폭 저하 |
| 3 | TASK | opal + {project} 2계층 네임스페이스 | 프레임워크 공통 vs 프로젝트별 격리 |
| 4 | TASK | tasks 인덱싱은 완료 상태만 | 진행 중 태스크 포함 시 노이즈 |
| 5 | TASK | --json 출력 플래그 필수 | 스킬·PM이 Bash로 파싱 가능해야 통합 가능 |
| 6 | TASK | 읽기는 opal-pm 프로세스 내 명시적 호출 | 훅 블랙박스 처리보다 투명성 우선 |

## 블로커
없음

## 다음 액션
캡틴 승인 후 PLAN 단계 진행
