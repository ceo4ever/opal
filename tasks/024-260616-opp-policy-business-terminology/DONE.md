# DONE: 기획 산출물 비즈니스 용어 우선 원칙 내재화

> 태스크: 024 | 스킬: //opp --agentic | 완료: 2026-06-16 17:26 KST
> 모드: agentic | 게이트: PLAN PM Gate ✅ / EXECUTE PM Gate ✅ / CLOSE 캡틴 승인 ✅

---

## 1. 목표 달성

opwt로 소스 코드를 역설계해 정책서 등 기획 산출물을 만들 때 코드 변수·식별자를 본문에 그대로 나열하던 문제를 차단했다. 근거/용어 SSOT(`citation-rules.md`)에 "비즈니스 용어 우선 원칙(§8)"을 신설하고, opwt 작성·QA·brain·문서표준 4개 지점이 §8을 참조하도록 연결했다.

핵심 명제: **"코드는 SSOT 근거이지 본문 서술의 주어가 아니다."**

## 2. 변경 파일 (7개)

| # | 파일 | 변경 | 배포 |
|---|------|------|------|
| 1 | `opal/core/references/harness/citation-rules.md` | §8 비즈니스 용어 우선 원칙 신설(8.1~8.5 + [MUST] + 자연어 변환 표 + 조건/코드근거 분리 표) + 변경이력 v2.1 | ✅ |
| 2 | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | §7-0 공통 작성 원칙 블록(§8 참조) | ✅ |
| 3 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | §3.1 비즈니스 용어 우선 검증 절 + §6 QA 절차 5-1단계 | ✅ |
| 4 | `opal/skills/op-brain-ingest/SKILL.md` | STEP 4 비즈니스 용어 우선 불릿 + 변경이력 v1.2 | ✅ |
| 5 | `opal/core/references/opal-doc-standard.md` | §3 정책서 행 §8 포인터 + 변경이력 v2.2 | ✅ |
| 6 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 변경이력 v4.4 (network-guide·consistency-rules 변경 추적) | ✅ |
| 7 | `.opal/AGENT.md` | 확정 기준 #2 행 추가 (캡틴 문안 원문) | N/A(프로젝트 설정) |

> 배포: 1~6은 install과 동일 strip 변환(`## 변경이력` 제거)으로 `~/.opal/` 미러 타깃 배포. 7은 프로젝트 PM 설정이라 배포 대상 아님.

## 3. PM 의사결정 (agentic)

| # | 결정 | 근거 | 캡틴 확인 |
|---|------|------|----------|
| D-1 | SSOT 위치 = citation-rules.md §8 | 이미 근거/용어 SSOT, 헌법 거버넌스(참조 상속) | - |
| D-2 | 확정 기준 행번호 #7 → **#2** 정정 | 표에 #1만 존재 → 비연속 깨진 표 방지. "7"은 원본 표 행번호로 추정 | ✅ 동의 |
| D-3 | network-guide·consistency-rules 변경이력은 부모 opwt SKILL.md v4.4에 기록 | 두 파일 자체 변경이력 표 부재 + v1.3 선례 | - |
| D-4 | Step 7 배포 = 타깃 strip 배포(전체 install 미실행) | 문서 변경에 대시보드 재빌드/서버 재기동 불요(외과적) | - |

## 4. 검증

- grep 검증 10건(소스) + 5건(배포본) 전부 통과.
- 동작검증(TEST): 문서/프롬프트 변경으로 코드 로직 무변경 → 불요(TASK.md §5).
- SSOT 단일화: 원칙 본문 §8 1곳, 나머지 참조만(재서술 0).

## 5. 후속

- 미커밋 상태로 마감(커밋 규칙 — 캡틴 지시 시 커밋). 본 태스크 7개 파일 + 태스크 폴더가 미커밋.
- 다음 opwt 실행 시 §8이 워커 프롬프트(§7-0)·QA(§3.1)에 실제 반영되는지 운영 확인 권장.
