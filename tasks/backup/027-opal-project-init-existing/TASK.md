# TASK: opal-project-init 기존 프로젝트 지원 (모드 분기)

> 작성일: 2026-03-21 | 작업 유형: 개선

## 작업 목표

현재 신규 프로젝트 전용인 opal-project-init 스킬에 "기존 프로젝트" 모드를 추가하여, 이미 코드가 있는 프로젝트에서도 docs/ 문서와 AI 지시 파일을 생성할 수 있게 한다.

## 배경

- 현재 SKILL.md는 인터뷰 → context7 조회 → 템플릿 치환 → 파일 생성의 신규 프로젝트 플로우만 존재
- 기존 프로젝트에서는: 코드 자동 분석 → 분석 결과로 플레이스홀더 자동 채움 → 인터뷰는 확인/보정만 → 적용 가능한 템플릿만 필터링
- 템플릿이 특정 기술 스택(FastAPI+Next.js+uv)을 전제하므로, 기존 프로젝트 구조와 불일치 가능 → 필터링 필요

## 요구사항

### SKILL.md 변경
- [ ] Step 0에 모드 선택 추가: "신규 프로젝트" / "기존 프로젝트"
- [ ] 기존 모드: 자동 분석 단계 추가 (package.json, pyproject.toml, 디렉토리 구조 등 스캔)
- [ ] 분석 결과로 플레이스홀더 자동 채움 → 인터뷰는 확인/보정 형태로 변경
- [ ] 기존 프로젝트 기술 스택과 매칭되지 않는 템플릿은 자동 제외
- [ ] 기존 파일(CLAUDE.md, .cursorrules, GEMINI.md) 병합 로직 구체화

### apply.js 변경
- [ ] `--mode existing` 옵션 추가 (기존 파일 병합 모드)
- [ ] 기존 CLAUDE.md 병합: OPAL 부트스트래퍼 보존 + 기존 내용 유지 + 새 섹션 추가
- [ ] 기존 파일 존재 시 백업 생성 (.bak)

### triggers 확장
- [ ] "기존 프로젝트 문서화", "프로젝트 문서 만들어줘", "docs 생성" 등 기존 프로젝트 관련 트리거 추가

## 제약 조건

- 기존 신규 프로젝트 플로우 그대로 유지 (기능 깨지지 않게)
- 템플릿 파일(.md) 자체는 수정 최소화
- skills/opal-project-init/ 범위 내에서만 변경
- README.md도 업데이트

## 관련 문서

- `skills/opal-project-init/SKILL.md` — 현재 스킬 정의
- `skills/opal-project-init/scripts/apply.js` — 템플릿 적용 스크립트
- `skills/opal-project-init/README.md` — 스킬 문서
