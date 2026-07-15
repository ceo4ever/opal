---
type: concept
title: 설정 파일 동시 쓰기 방어 표준
tags:
- architecture
- concurrency
- backend
- pattern
- file-io
sources:
- task:061
related:
- console-write-exception-router-isolation
- pool-lock-idiom-contract
- opal-console
created: '2026-07-14'
updated: '2026-07-14'
status: active
---
## 개념 요약

콘솔 설정 라우터처럼 JSON 설정 파일에 쓰기가 필요한 경우, 동시 요청에도 안전하도록 락으로 갱신 사이클을 직렬화하고 임시 파일 교체로 쓰기를 원자화하며 기존 값을 머지 보존하는 표준 조합이다.

## 배경·문제 (WHY)

- 설정 쓰기 인프라를 설계하는 과정에서 "`open('w')` 단일 호출은 원자적"이라는 가정이 있었으나, 이는 부정확한 것으로 정정되었다 — POSIX에서 truncate+write는 원자적이지 않고, 파일을 읽어 갱신 후 다시 쓰는 read-modify-write 사이클은 더더욱 원자성이 보장되지 않는다(근거: task:061 PLAN.md §3.1.2 "ANALYSIS §2.1 정정 반영").
- 동시에 두 요청이 같은 설정 파일을 갱신하면, 락 없이는 한쪽의 갱신이 유실되거나 파일이 중간 상태로 파손된 채 노출될 위험이 있다.
- 설정 파일은 다른 도구(예: `opal-cli console scan`)도 갱신하는 공용 파일이므로, 갱신 시 이 도구가 채운 필드까지 보존해야 한다는 요구가 있었다.

## 결정 내용 (HOW)

- **직렬화**: 모듈 레벨 락으로 읽기→수정→쓰기 사이클 전체를 하나의 임계구역으로 묶는다(`_WRITE_LOCK`, `dashboard/backend/config.py:77`).
- **원자적 교체**: 임시 파일에 먼저 쓴 뒤 이름 바꾸기로 원본을 교체한다 — 임시 파일 쓰기 도중 프로세스가 죽어도 원본은 훼손되지 않는다(`_atomic_write_json`, `dashboard/backend/config.py:80-85`).
- **머지 보존**: 갱신 시 파일 전체를 새로 쓰는 대신, 기존 내용을 읽어 전달된 키만 부분 갱신한다 — 다른 필드나 다른 도구가 채운 미지 키가 유실되지 않는다(`save_config`, `dashboard/backend/config.py:88-99`).
- 이 세 요소(직렬화·원자적 교체·머지 보존)는 개별로는 불충분하다 — 락만으로는 파손을 막지 못하고, 원자적 교체만으로는 동시 갱신 유실을 막지 못하며, 머지만으로는 중간 파손을 막지 못한다. 세 요소가 함께 적용되어야 동시 쓰기 안전성이 성립한다.

## 영향·관계

- `dashboard/backend/config.py` — `_WRITE_LOCK`·`_atomic_write_json`·`save_config`.
- [[console-write-exception-router-isolation]] — 이 표준이 적용되는 쓰기 라우터([[opal-console]] 설정 라우터)의 상위 격리 패턴.
- [[pool-lock-idiom-contract]] — 브레인 프라임 풀의 락 관용구와는 보호 대상(서브프로세스 상태 vs JSON 파일)이 다르지만, "락으로 임계구역을 좁히고 위험 구간을 최소화한다"는 설계 사고는 공유한다.
- 향후 유사한 JSON 설정 파일 쓰기 기능(예: console.config 전반 편집·프로젝트 로컬 설정 편집 — task:061에서 범위 축소로 회수된 후속 후보, [[console-settings-incremental-scope-policy]] 참조)에도 이 표준을 재사용할 것을 권고한다.

## 근거 출처

task:061 PLAN.md §3.1.2("동시 쓰기 전략" 정정 문단) · `dashboard/backend/config.py:72-99`.
