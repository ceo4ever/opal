---
type: concept
title: 구형 Brain 정책 — Registry 진입점과 spawn 직전 게이트
tags:
- console
- brain
- security
sources:
- task:175
related: [opal-console, console-brain-subscription-auth, console-auth-default-deny-gate]
created: '2026-10-01'
updated: '2026-10-01'
status: draft
---
## 개요

구형 `claude -p` 기반 Brain은 서버 정책으로 기본 꺼져 있고, 켜면 위험 확인을 거쳐 `legacy` 배지가 붙는다. 정책은 HTTP 라우터가 아니라 세션 Registry 진입점과 프로세스 시작 직전에서 집행된다. (`dashboard/backend/adapters/brain_policy.py`, `tasks/175-261001-opd-콘솔-POST-인증-게이트/DONE.md:7`)

## 설계 배경 (WHY)

구형 경로는 파일 읽기 범위 비제한·임의 Bash·네트워크 유출 위험이 있어 새 Brain 출시 전까지 기본 차단하되, 소유자가 위험을 알고 켤 선택지는 남겼다. (근거: task:175 PLAN§D-19)

게이트를 라우터가 아닌 Registry 진입점(prime·prewarm·submit·ask·풀 리필)에 둔 것은 기동 선프라임과 풀 리필 같은 비HTTP 경로도 막아야 하기 때문이다. 어댑터의 시작 구간 락이 마지막 방어선이다. (근거: task:175 PLAN§D-17)

어댑터를 `subprocess.run`에서 `Popen`으로 바꿔 락을 프로세스 시작 구간에만 걸었다. 전체 실행(최대 180초)에 걸면 끄기 요청이 막히기 때문이다. 그 결과 끄기 요청이 반환된 뒤 신규 프로세스는 0회이고, 이미 시작된 turn은 끝까지 진행하며 화면에 진행 중 turn 수가 표시된다. (근거: task:175 PLAN§D-16)

## 결정 내용

- 저장 위치는 `console.config.json`이며 JSON `true`만 켜짐으로 해석한다(키 없음·파손은 꺼짐).
- 켜기는 위험 확인 값이 없으면 거절하고, 끌 때는 메모리 반영 후 저장한다. (근거: task:175 PLAN§D-18)
- 기존 어댑터 호출 계약(`shell=False`, `--allowedTools`, JSON 파싱)은 보존한다.
- 잔여: 켜기·끄기 경합 시 메모리와 파일 불일치 가능(재시작 시 꺼짐으로 복구). (근거: task:175 DONE§참고)

## 관련 페이지

- [[opal-console]]
- [[console-brain-subscription-auth]]
- [[console-auth-default-deny-gate]]
