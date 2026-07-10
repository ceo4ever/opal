---
type: concept
title: state-tool {owner_name} write-time 치환 메커니즘
tags:
- state-tool
- identity
- note
- mechanism
sources:
- task:054
related:
- owner-honorific-contamination-prevention
- state-tool
created: '2026-07-10'
updated: '2026-07-10'
status: active
---
## 개념 요약

state-tool은 note를 저장하는 순간에 note 텍스트 안의 `{owner_name}` 플레이스홀더를 로컬 identity 설정(`identity.md`)의 `owner_name` 값으로 치환한다(`resolve_owner_placeholder()`, `opal/tools/state-tool/state_tool.py`). 플레이스홀더가 없는 note는 파일 I/O 없이 그대로 저장되어 기존 동작과 완전히 동일하다.

## 배경·문제 (WHY)

note 예시가 이미 `{owner_name} 확인: …` 형태의 플레이스홀더를 쓰도록 정리되어 있었지만, 그 플레이스홀더를 실제 값으로 채우는 책임이 순수히 모델에게 맡겨져 있었다. 모델은 로컬 identity보다 세션에 로드된 레포 컨텍스트의 지배적 호칭을 관성적으로 따라 쓰기 쉬워, "플레이스홀더 규칙이 있다"는 사실만으로는 오염을 막지 못했다([[owner-honorific-contamination-prevention]] 참고). 구조적 대안(state 파일 스키마에 표시용 소유자 필드를 신설)은 스키마 변경과 하위호환 파손 부담이 커 기각되었고, 검증형(개인 호칭을 note에서 거부)은 이름을 미리 열거할 수 없어 실효성이 없었다.

## 결정 내용 (HOW)

- 저장 직전 note 텍스트에 `{owner_name}` 플레이스홀더가 있으면, 로컬 identity 설정 파일에서 `owner_name` 값을 읽어 치환한다. 없으면 파일 I/O 자체를 건너뛰고 원문을 그대로 반환한다(fast-path — 기존 note에 대한 회귀 없음).
- identity 설정 파일의 위치는 환경변수(`OPAL_HOME`, 기본값 `~/.opal`) 기준으로 해석해 플랫폼 독립성을 지킨다.
- identity 설정 파일이 없거나, `owner_name` 값이 비어 있거나, 파싱에 실패하는 모든 경우는 예외 없이 원문(플레이스홀더 그대로)을 유지한다 — note 저장 자체를 실패시키지 않는 fail-safe 설계.
- 이 치환은 note를 남기는 모든 경로(진행 기록 갱신·상태 전환·행 추가·차단·상태 조회·초기화)에 동일하게 적용된다 — 어느 한 경로만 치환되면 "왜 이 경로는 개인화되고 저 경로는 안 되는가"라는 비일관성이 생기기 때문에 단일 규칙으로 통일했다.

## 영향·관계

- [[owner-honorific-contamination-prevention]] — 이 메커니즘이 구현하는 상위 원칙(A: 도구 집행)
- [[state-tool]] — note-write 경로 6곳이 이 메커니즘의 적용 지점
- 기존(치환 도입 이전) state 파일의 note는 소급 정정하지 않는다 — 신규 note부터 적용되는 전방 호환 정책.

## 근거 출처

- task:054 — `opal/tools/state-tool/state_tool.py`(`resolve_owner_placeholder()` 신설, note-write 6경로 적용) + 테스트(RED→GREEN, 회귀·폴백 케이스)
