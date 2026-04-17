# DONE: opal-pilot-gc 경량 Pilot + 보안/컨벤션 에이전트 개발

> 완료일시: 2026-04-17 17:09
> 태스크 번호: 122
> 적용 스킬: opp
> 모드: interactive
> 시작: 2026-04-17 07:42 / 소요: 약 9시간 27분 (대화 + 파이프라인)

## 작업 요약

커밋 전 코드 보안·컨벤션 체크를 수행하는 **경량 Pilot `opal-pilot-gc`(opgc)** 와 2개의 전문 에이전트(`opal-security-checker`, `opal-convention-checker`)를 OPAL 프레임워크 기본 컴포넌트로 신설. 030 태스크에서 분리되어 보류되던 보안 컴포넌트 생성 작업의 **TEST(코드 보안)** 부분을 흡수하여 완료.

## 산출물

### 신규 파일 (10종)

| 경로 | 역할 |
|------|------|
| `opal/skills/opal-pilot-gc/SKILL.md` | 경량 Pilot 정의 (5단계 파이프라인) |
| `opal/skills/opal-pilot-gc/references/report-security-template.md` | 보안 보고서 템플릿 |
| `opal/skills/opal-pilot-gc/references/report-convention-template.md` | 컨벤션 보고서 템플릿 |
| `opal/skills/opal-pilot-gc/references/base-security-checklist.md` | OWASP Top 10 + CWE Top 25 + SANS Top 25 + 도메인 체크리스트 |
| `opal/skills/opal-pilot-gc/references/base-convention-checklist.md` | 컨벤션 카테고리 체크리스트 |
| `opal/skills/opal-pilot-gc/references/done-template.md` | DONE.md 템플릿 |
| `opal/skills/opal-pilot-gc/references/sample-report-security.md` | 보안 샘플 보고서 (7건 이슈, 5단계 상태 전부) |
| `opal/skills/opal-pilot-gc/references/sample-report-convention.md` | 컨벤션 샘플 보고서 (14건 이슈, 5단계 상태 전부) |
| `opal/agents/opal-security-checker/AGENT.md` | 보안 전문 에이전트 |
| `opal/agents/opal-convention-checker/AGENT.md` | 컨벤션 전문 에이전트 |

### 수정 파일 (4종)

| 경로 | 변경 |
|------|------|
| `opal/core/references/skills.md` | opal-pilot-gc 행 추가 |
| `opal/core/references/opal-skills-registry.json` | v3.2.0 → v3.3.0, opal-pilot-gc 엔트리 추가 (alias `opgc`, 별칭 `gc`) |
| `opal/core/references/agents.md` | "opal-pilot-gc 서브에이전트" 섹션 신설 + 매핑 테이블 행 2개 추가 |
| `docs/PROJECT.md` | "주요 컴포넌트 (GC 파이프라인)" 섹션 신설 |

### 미수정 (의도적)

- `scripts/install-mac.sh` — 제네릭 배포 구조(`for skill_dir in ...`/`for agent_dir in ...`)이므로 신규 폴더 자동 배포됨

## 핵심 설계 결정 (PLAN에서 확정한 10가지)

| # | 결정 | 근거 |
|---|------|------|
| 1 | 빈도 임계값 N = **3 파일** | N=2 노이즈, N=5 staged에서 미발동 |
| 2 | 심각도 트리거 = **Critical + High 둘 다** | TASK §9 원문 준수 |
| 3 | Fingerprint = **카테고리 + 정규화 토큰 시퀀스 SHA-1 8byte prefix** | 주석/문자열/숫자/식별자 정규화, 라인 제외 |
| 4 | 새 카테고리 감지 = **헤더 인덱스 + 정규화 키워드 매칭** | docs §2~§3 헤더 수집 → 차집합 |
| 5 | 문서 갱신 방식 = **opi 재사용** | 백업/섹션 등록 프로토콜 이미 존재 |
| 6 | 캡틴 승인 UX = **항목별 번호 입력 + a/n 일괄 + d 상세** | 안전 + 효율 균형 |
| 7 | 커뮤니티 보안 스킬 | `openai/security-best-practices` 채택 (Apache 2.0), `getsentry/code-review` 부분 채택 |
| 8 | APPLY 자동 판정 = **5분기 + 3-tier stash 롤백** | 파일 단위 즉시 + 세션 체크포인트 + commit 금지 |
| 9 | 체크리스트/샘플 | OWASP 10 + CWE 25 + SANS 25 + 컨벤션 8종 전량, 샘플 2부 (보안 7건 / 컨벤션 14건) |
| 10 | 초안 생성 = **opi 재사용** | §5와 일관 |

## 핵심 설계 원칙 (TASK에서 확정)

- **5단계 경량 Pilot**: SCAN → CHECK → REPORT → APPLY → CLOSE
- **트래커 없음** — 단일 실행 내 빈도/심각도 감지로 충분
- **자기완결 보고서** — 통합 요약 파일 없음, 각 에이전트가 체크리스트 내장
- **5단계 체크박스 상태**: `[ ]` open / `[x]` done / `[~]` pending / `[?]` review / `[!]` failed
- **보안 2축 구조**: Base 원칙(강제) + `docs/SECURITY.md`(있으면 누적)
- **컨벤션 단일 기준**: `docs/CONVENTIONS.md` 유일 + 부재 시 초안 유도
- **STATE.md 허브**: 통합 요약 파일 대체

## 의사결정 로그 (요약, 22건)

STATE.md 의사결정 로그 1~22 참조. 주요 전환점:

- 결정 1~5: 초기 구조 (스킬+에이전트 → 후에 Pilot으로 상향)
- 결정 6~7: 컨벤션·보안 기준 분리 정책 정립
- 결정 8: 단순 스킬 → **경량 Pilot** 전환
- 결정 9: APPLY 기본 승인 + `--apply` 자동 모드
- 결정 10: 보안 2축 구조(Base + SECURITY.md) — context7은 SECURITY.md 작성 시점에만
- 결정 11: 보고서에 심각도/카테고리/지표 포함
- 결정 12~14: 트래커 도입 검토 → **철회** (단일 실행 내 빈도/심각도로 대체)
- 결정 15~16: 보고서 C안 → D+안 (통합 요약 제거, 각 에이전트 자기완결)
- 결정 18~22: D+안 확정, CLOSE 단계 추가, GC-APPLY-LOG 제거, 5단계 상태 모델, 자동 판정 규칙

## QA 결과

| Gate | 판정 | 비고 |
|------|------|------|
| QA-PLAN | Pass | Warning 2건 (W-1 컨벤션 URL placeholder, W-2 트리거 분리 표기) — EXECUTE에서 반영 |
| QA-EXECUTE | Pass | Warning 4건 — PM Gate에서 전부 조치 (JSON SSOT 등록, model 정합화, 샘플 참조명 통일, 트리거 3종 분리 재작성) |

## 030 보안 보류 흡수

- `project_security_task.md` 상태 → `완료(TEST 부분)` 전환 (`task` → `project` 타입)
- 설계 보안(PLAN 단계) 범위는 **별도 후속 태스크로 분리 유지**

## 후속 작업

| # | 항목 | 비고 |
|---|------|------|
| 1 | **자동화** — 훅/git pre-commit 통합 | 본 태스크 범위 밖. 수동(`//opgc`) 안정화 후 후속 태스크 |
| 2 | **PLAN 보안** — 설계 단계 보안 검토 (위협 모델링/아키텍처) | 030 분리 보안 중 PLAN 부분. 별도 태스크 정의 필요 |
| 3 | **opi 통합 검증** — 문서 갱신 흐름(SECURITY/CONVENTIONS 초안 + §10 갱신) 실제 동작 확인 | opal-pilot-gc 첫 실행 시 검증 |
| 4 | **샘플 보고서 URL placeholder 실 URL 매핑** | TBD 마킹된 ESLint/CWE 링크를 최종 URL로 갱신 |

## 변경이력

| 버전 | 일시 | 내용 |
|------|------|------|
| 1.0 | 2026-04-17 17:09 | 최초 완료 — opal-pilot-gc 경량 Pilot + 에이전트 2개 + 레지스트리 + docs 정합 + 030 메모리 정리 |
