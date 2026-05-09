# DONE — TASK 109

**태스크**: @header 표준 + code-scan 통합 워크플로우  
**완료일**: 2026-04-12

---

## 완료 요약

코드 파일 분석 시 토큰 낭비를 줄이기 위한 `@header` 메타블록 표준을 정의하고, code-scan 통합 워크플로우 전반에 적용했다.

---

## 산출물

| # | 파일 | 유형 | 내용 |
|---|------|------|------|
| 1 | `opal/core/references/header-standard.md` | 신규 | @header 포맷 표준 (필드 7개, 언어별 예시 6개, layer별 exports 가이드, 삽입 위치 규칙) |
| 2 | `opal/core/references/opal-harness.md` | 수정 | §8 EXECUTE @header 규칙 + code-scan 활용 가이드 (B안) 추가. 기존 §8 OPAL Tools → §9. v3.6 |
| 3 | `opal/core/references/opal-pm.md` | 수정 | §3 디스패치 전 code-scan 사전 범위 파악 + §4 8번 @header 검증 + §9 code-scan.json PM 관리 의무. v1.1 |
| 4 | `opal/core/references/tools.md` | 수정 | PM 관리 방안 서브섹션 + exports 커맨드 사용 예시 추가. v1.2 |
| 5 | `opal/skills/op-task-execute/SKILL.md` | 수정 | Step 3-H @header 작성 규칙 추가. v1.2 |
| 6 | `opal/skills/op-dev-execute/SKILL.md` | 수정 | Step 3-H @header 작성 규칙 추가. v1.1 |
| 7 | `opal/tools/code-scan/code-scan.js` | 수정 | `exports <keyword>` 커맨드 추가 — exports 필드 전용 검색. v1.1.0 |
| 8 | `opal/core/AGENT.md` | 수정 | 비서 모드 code-scan 활용 규칙 추가 (상황별 커맨드 표 + 적용 조건). v1.8 |

---

## 주요 설계 결정

- **exports 통합 필드**: 역할별로 exports에 담는 내용이 달라지도록 layer 기준으로 가이드 제공
- **header-gen.js 없음**: 워커(LLM)가 harness 규칙 + header-standard.md 참조로 직접 작성
- **code-scan 활용 B안**: harness에 규칙 정의 → PM/오케스트레이터가 읽어 워커에 주입
- **알투(비서) code-scan 활용**: AGENT.md에 비서 모드 전용 규칙 추가

---

## 후속 처리

- `opal-harness.md §9 "현재 등록된 도구" 테이블에 code-scan 추가` → 별도 opi 대상
