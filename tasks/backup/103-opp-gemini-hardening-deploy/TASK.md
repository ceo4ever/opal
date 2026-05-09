# TASK-103: Gemini Hardening 글로벌 배포

> 적용 스킬: opal-pilot-project (opp)
> 생성일: 2026-04-09

## 배경

`GEMINI HARDENING` 섹션은 Gemini 플랫폼의 행동 특성을 보정하는 전용 가드(GUARD-1~5)다.
현재 이 섹션은 프로젝트 루트 `GEMINI.md`와 `opal-project-init` 템플릿에만 존재하고,
글로벌 `~/.gemini/GEMINI.md`에는 배포되지 않아 Gemini와의 실제 작업 시 가드가 적용되지 않는다.

## 목표

HARDENING 섹션을 `OPAL START` 마커와 **독립된 별도 마커**로 `~/.gemini/GEMINI.md`에 배포한다.

- 두 섹션(OPAL 부트스트래퍼 / GEMINI HARDENING)은 마커로 분리되어 독립적으로 업데이트 가능해야 한다.
- 기존 `install_opal_section()` 패턴을 재사용한다 (마커만 다름).

## 요구사항

- [x] `opal/bootstrapper/gemini-hardening.md` 생성 — HARDENING 소스 파일
  - `gemini-bootstrap.md`와 동일한 파일 구조 (```markdown 블록으로 삽입 내용 정의)
  - 삽입 내용: 프로젝트 루트 `GEMINI.md`의 `GEMINI HARDENING` 섹션 그대로
- [x] `scripts/install-mac.sh` 업데이트
  - `install_gemini_hardening()` 함수 추가 — `GEMINI HARDENING START/END` 마커 기반
  - `install_opal_bootstrappers()` 내 Gemini 배포 직후 `install_gemini_hardening` 호출 추가
  - 설치 완료 요약 출력(`print_installed_summary`)에 `~/.gemini/GEMINI.md HARDENING` 항목 추가
- [x] 기존 `~/.gemini/GEMINI.md` 호환성 유지 — OPAL 섹션은 변경 없음

## 제약

- `install_opal_section()`은 수정하지 않는다 (하위 호환 유지)
- HARDENING 소스 내용은 프로젝트 루트 `GEMINI.md`의 것과 동일해야 한다 (SSOT)
- 배포 금지 원칙 준수: `~/.opal/` 직접 편집 금지 (해당 없음, `~/.gemini/`는 허용)
