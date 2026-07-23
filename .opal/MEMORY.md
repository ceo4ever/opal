# opal Memory Index

> 최종 갱신: 2026-06-26 (044 도구·MCP·스킬 통합 검색·사용법·활용 체계 — TASK)
> last_task_number: 74


| 카테고리 | 설명 | 완료 시 |
|----------|------|---------|
| task | 일회성 작업 계획/예정 | 삭제 |
| project | 프로젝트 비전, 방향성 등 지속 지식 | 유지 (폐기 시 삭제) |
| architecture | 아키텍처 설계 결정과 근거 | 유지 (변경 시 갱신) |
| feedback | 캡틴의 작업 방식 피드백 | 유지 (철회 시 삭제) |
| preferences | 이 프로젝트에서 캡틴이 선호하는 방식 | 유지 |
| issues | 반복되는 이슈와 해결법 | 유지 |

> 메모리 파일은 `memory/` 디렉토리에 저장한다.
> 새 메모리가 생기면 이 인덱스에 파일 경로와 설명을 추가한다.
> **task 타입은 완료 시 메모리 파일 + 인덱스 항목을 삭제한다.**





> v0.5.0 베이스라인 시작 — 이전 작업 히스토리는 git log + tasks/ 폴더(삭제됨)에서 추적
> 새 태스크는 001부터 채번

## 메모리
<!-- memory:index:start -->
| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |
|------|--------|------|------|------|------|
| Console 브레인 구독 인증 | 2026-06-22 | project | active | `memory/console-brain-subscription-auth.md` | Console 브레인 질의는 종량제 API 아닌 사용자 Claude 구독(로컬 claude -p). API키·SDK 금지 |
| 브레인 질의 콜드 경량화(037후속) | 2026-06-23 | task | active | `memory/follow-up-brain-query-lite.md` | 브레인 질의 콜드 latency 경량화 — 검색을 LLM 밖 brain-tool로. opbr --lite 권고 |
| 후속 069·070 액션에이전트 관측 확장 | 2026-07-17 | task | active | memory/후속_069_070_액션에이전트_관측_확장.md | oppd·opsdd를 opal-agent 채널+규약 전환→action-monitor 공용화. phase 동적발견 필수 |
<!-- memory:index:end -->

## 작업 히스토리 (최대 5개, FIFO)
<!-- memory:history:start -->
| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |
|------|--------|------|------|----------|
| 074 import-existing key 유실 수정 | 2026-07-23 | 완료·미배포·미커밋 | tasks/074-260723-opds-import-existing-키유실/ | --import-existing가 lossy STATE.md 재파싱으로 key 유실 → (stage,item) 순서매칭 재접합(state.json→pipeline.json→keyless경고). RED→GREEN 신규5·전량254. 후속=배포·커밋 |
| 072 다음 액션 자동 파생 | 2026-07-23 | 완료·커밋(f6ec48b) | tasks/072-260723-opd-다음액션-자동파생/ | advance/mark 프론티어 자동파생+next_action SSOT·설계반전. 회귀249·RED-first |
| 071 브레인 미실체 지식 등록 차단 게이트 | 2026-07-23 | 완료·미커밋·미배포(캡틴 배포) | tasks/071-260722-opds-브레인-미실체지식-차단/ | 미실체 지식 차단 2층(기준 명문화+add-page 거부·lint speculative). 127 Pass. 후속=배포·state-tool |
| 070 state-tool task-step 키 주소 1차 | 2026-07-23 | 완료·미커밋·미배포 | tasks/070-260720-opd-태스크스텝-키주소-1차/ | pipeline.json 스펙 표준화+`--task-step`/`--task-step-id` key 주소+`--action-step` 개명+그룹A 4종 전환(본문 포함)+opdd enum+schema 1.1 stamp. 240 PASS+선재1. 후속=install 재배포(라이브 --row 잔존)·커밋(071 제외)·2차/3차 |
| 058 PM 개선 루프 tool-gated 재설계 | 2026-07-20 | 완료·커밋 | tasks/058-260713-opd-학습루프-도구화-개선수집/ | opal-improve(//opim)·improve-tool·fw-inbox·4pilot 회고 하드스텝·SSOT 통합. 14+88 Pass |
<!-- memory:history:end -->
