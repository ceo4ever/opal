# TASK: opi docs 백업 기능 추가

- 적용 스킬: opp
- 모드: interactive
- 시작일시: 2026-04-06 HH:mm
- 상태: 진행 중

## 요청

opi 스킬에서 `/docs` 문서를 수정할 때, 수정 전 백업을 `/docs/backup/`에 저장하는 기능 추가.

백업 파일명 규칙: `{파일명}_{YYYYMMDDHHMM}.md`

## 변경 대상

- `opal/skills/opal-project-init/SKILL.md`

## 요구사항

- [ ] 백업 대상: `docs/` 하위 문서를 **수정**할 때만 적용 (신규 생성은 백업 불필요)
- [ ] 백업 위치: `docs/backup/`
- [ ] 백업 파일명: `{원본파일명}_{YYYYMMDDHHMM}.md` (예: `PROJECT_202604061530.md`)
- [ ] 백업 타이밍: 파일 수정(Write/Edit) 직전에 수행
- [ ] 적용 범위: 최신화 모드 Phase 3 (문서 업데이트 직전) + 초기화 모드 Phase 2/3 (기존 문서 덮어쓸 때)
- [ ] `docs/backup/` 폴더가 없으면 자동 생성
