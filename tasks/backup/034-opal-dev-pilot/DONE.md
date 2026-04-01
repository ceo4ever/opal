# DONE: opal-project-dev-pilot 스킬 개발

> 완료일: 2026-03-27
> 모드: Short Task

## 작업 요약

개발 프로젝트의 전체 라이프사이클을 관리하는 `opal-project-dev-pilot` (약식: `//opdp`) 스킬을 개발했다.

## 수행 내용

### R1. 스킬 정의
- `opal/skills/opal-project-dev-pilot/SKILL.md` 작성
- 4 Phase 파이프라인: PRD → TRD → 로드맵 → 태스크 순차 실행
- 사전 조건 체크: docs/PROJECT.md 미존재 시 opi 자동 실행 → 완료 후 복귀
- tasks/ 구조: TASK.md(전체 그림) + STATE.md(진행 추적) + DONE.md(랩업)
- 세션 복원: tasks/*-opdp-* 패턴으로 기존 태스크 감지

### R2. PRD 작성 가이드
- `references/prd-guide.md` — PRD 구조, 캡틴 인터뷰 포인트, PM 검수 체크리스트

### R3. TRD 작성 가이드
- `references/trd-guide.md` — TRD 구조, PRD 매핑 규칙, PM 검수 체크리스트
- 기술 스택 버전 관리 규칙: ARCHITECTURE.md가 SSOT, TRD는 결정 근거만

### R4. 로드맵 가이드
- `references/roadmap-guide.md` — 태스크 분할 원칙, 스킬 판단 기준, PM 검수 체크리스트

### R5~R6. PM 검수 + 후속 조치
- 모든 Phase: PM 검수 → 캡틴 확정 → 후속 조치 (필수)
- 후속 조치: PROJECT.md 문서 테이블 등록 + STATE.md 갱신 + MEMORY.md 갱신
- Phase 2(TRD) 후속 조치: ARCHITECTURE.md 업데이트 추가 (기술 스택 버전 반영)
- 참조 가이드에도 후속 조치 체크 추가 (이중 안전장치)

### R7. opi 연동
- opi SKILL.md: `opal-dev-builder` → `opal-project-dev-pilot` / `//opdp` 명칭 교체
- 레지스트리: skills.md + skill-guide.md에 opdp 항목 추가

### 추가 개선 (테스트 피드백 반영)
- 프로젝트 메모리 갱신: opi, opdp 모든 Phase 완료 시 .opal/MEMORY.md 작업 히스토리 갱신
- 프로젝트 설정: docs/PROJECT.md에 "프로젝트 설정" 섹션 (태스크 폴더 경로 등 커스텀)
- 기술 스택 SSOT: ARCHITECTURE.md가 유일한 버전 정보 원천

## 산출물

### 신규 생성
| 파일 | 역할 |
|------|------|
| `opal/skills/opal-project-dev-pilot/SKILL.md` | opdp 스킬 본체 |
| `opal/skills/opal-project-dev-pilot/references/prd-guide.md` | PRD 작성 가이드 |
| `opal/skills/opal-project-dev-pilot/references/trd-guide.md` | TRD 작성 가이드 |
| `opal/skills/opal-project-dev-pilot/references/roadmap-guide.md` | 로드맵 수립 가이드 |

### 수정
| 파일 | 변경 |
|------|------|
| `skills/opal-project-init/SKILL.md` | 명칭 교체 + 메모리 갱신 절차 추가 |
| `skills/opal-project-init/references/docs-guide.md` | 프로젝트 설정 섹션 추가 |
| `opal/core/AGENT.md` | PM 컨텍스트 로드에 프로젝트 설정 적용 추가 |
| `opal/core/references/skills.md` | opdp 레지스트리 등록 |
| `opal/core/references/skill-guide.md` | opdp 브리핑 테이블 추가 |

## OPAL 스킬 체계 (최종)

```
//opi    프로젝트 WHAT/WHY 정의 + 셋업
//opdp   PRD/TRD → 로드맵 → 태스크 순차 실행 + PM 검수
//otpd   개별 태스크 (Full Task — 대규모 개발)
//otpds  개별 태스크 (Short Task — 소규모 개발)
//otpwf  개별 태스크 (와이어프레임 → UI)
```
