# DONE: OPAL 프레임워크 문서 구조 + PM 역할 재설계

> 완료일: 2026-03-27
> 모드: Short Task

## 작업 요약

OPAL 프레임워크의 프로젝트 문서 구조를 재설계하고, 프로젝트 PM(AGENT.md) 역할을 실질적으로 작동하게 개선했다.

## 수행 내용

### R1. LLM 플랫폼 문서 경량화
- CLAUDE.md, GEMINI.md, .cursorrules 템플릿 → OPAL 부트스트래퍼만 (~10줄)
- 프로젝트 정보, 기술 스택, 코드 컨벤션 등 모두 제거

### R2~R3. docs 문서 체계 전환
- 기존 템플릿(server/* 6개, client/* 6개, INDEX.md 등) 전체 삭제
- 알투가 프로젝트 분석 후 직접 작성하는 방식으로 전환
- docs-guide.md 작성 가이드 생성 (PROJECT.md, ARCHITECTURE.md, CONVENTIONS.md, BACKEND.md, FRONTEND.md 구조 지침)
- docs/PROJECT.md가 프로젝트 허브 — 문서 레지스트리(문서 테이블) 역할
- 문서 등록 프로토콜: 새 문서 생성 시 캡틴에게 용도 인터뷰 → 승인 시 등록

### R4. .opal/AGENT.md 재설계
- 기존 페르소나/의사결정 원칙 → PM 전문 역할 + PM 검토 기준 + 업무 수행 지침으로 대체
- 확정 기준 섹션 신설 (PM 학습 루프에서 누적)
- 참조 문서 전달 의무 명시
- agent-guide.md 작성 가이드 생성

### R5. 부트스트랩 절차 변경
- 글로벌 AGENT.md에 "PM 컨텍스트 로드" 단계 삽입 (5단계)
- .opal/AGENT.md + docs/PROJECT.md + docs/CONVENTIONS.md Read
- 프로젝트 컨텍스트 목록 갱신

### R6. otp 파이프라인 변경
- otp-dev, otp-dev-short 디스패치: CLAUDE.md → docs/PROJECT.md + 문서 테이블 매칭 문서로 전환
- PM 검토 게이트 참조 추가 (글로벌 AGENT.md의 PM 컨텍스트 로드 절차 참조)
- docs/ 미존재 시 CLAUDE.md 폴백 (하위 호환)

### R7. opi 스킬 전면 재설계
- "고정 인터뷰 → 플레이스홀더 치환 → apply.js" → "분석 → 작성 → 검토" 방식 전환
- 초기화 모드 / 최신화 모드 2가지
- 객관식 중심 인터뷰 (한 번에 하나씩, 이전 답변 기반 맞춤 선택지)
- 완료 후 원래 요청으로 자동 복귀 (개발 요청 → opal-dev-builder 또는 otp 바로 실행)
- apply.js 역할 축소: 플랫폼 파일(부트스트래퍼)만 처리
- //opi 약식 명령어 등록

### R8. PM 학습 루프
- 글로벌 AGENT.md에 학습 루프 행동 규칙 추가
- 판단 불확실 → 캡틴 질문 → 답변 분류 (반복 원칙 → 확정 기준, 일회성 → memory/)
- 확정 기준 관리 원칙 (캡틴만 추가/삭제, 10개 초과 시 정리 제안)

## 산출물

### 신규 생성
| 파일 | 역할 |
|------|------|
| `skills/opal-project-init/references/docs-guide.md` | docs 문서 작성 가이드 |
| `skills/opal-project-init/references/agent-guide.md` | AGENT.md 작성 가이드 |
| `tasks/034-opal-dev-builder/TASK.md` | 후속 태스크 — opal-dev-builder 스킬 개발 |

### 수정
| 파일 | 변경 |
|------|------|
| `skills/opal-project-init/SKILL.md` | 전면 재설계 (초기화/최신화, 분석→작성→검토) |
| `skills/opal-project-init/scripts/apply.js` | 역할 축소 (PLATFORM_FILES만) |
| `skills/opal-project-init/templates/common/platform/CLAUDE.md` | 부트스트래퍼만 |
| `skills/opal-project-init/templates/common/platform/GEMINI.md` | 부트스트래퍼만 |
| `skills/opal-project-init/templates/common/platform/.cursorrules` | 부트스트래퍼만 |
| `opal/core/AGENT.md` | PM 컨텍스트 로드 + 검토 게이트 + 학습 루프 |
| `opal/core/references/skills.md` | opi 약식 명령어 등록 |
| `opal/core/references/skill-guide.md` | opi 약식 명령어 + 설명 갱신 |
| `skills/otp-dev/SKILL.md` | 디스패치 docs/ 참조 + PM 검토 게이트 |
| `skills/otp-dev-short/SKILL.md` | 디스패치 docs/ 참조 + PM 검토 게이트 |

### 삭제
| 파일/디렉토리 | 이유 |
|-------------|------|
| `templates/common/docs/*` | 알투 직접 작성으로 전환 |
| `templates/common/opal/*` | 알투 직접 작성으로 전환 |
| `templates/web/` | 알투 직접 작성으로 전환 |
| `templates/ai-agent/` | 알투 직접 작성으로 전환 |
| `templates/optional/` | 알투 직접 작성으로 전환 |

## 변경 규모

28개 파일, +421줄 / -4,477줄

## 후속 태스크

- **034: opal-dev-builder** — PRD/TRD 작성 + 로드맵 + 태스크 순차 실행 스킬
