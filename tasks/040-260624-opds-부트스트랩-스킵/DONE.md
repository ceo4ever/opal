# DONE: OPAL 부트스트랩 스킵 옵션 (`OPAL_BOOTSTRAP=off`)

> 태스크: 040-260624-opds-부트스트랩-스킵 | 완료일시: 2026-06-24 07:53
> 스킬: opds | 모드: agentic

## 완료 요약

`OPAL_BOOTSTRAP=off` 환경변수로 OPAL 부트스트랩 전체(정체성 포함)를 스킵하는 옵션 추가 완료.
4종 플랫폼 마커 SSOT(`opal/bootstrapper/`)에 skip 게이트 문구 삽입 + `opal/core/AGENT.md` Eager 절차 step 0 명문화.

## 핵심 결정 사항

### TASK 전제 정정 (PLAN §1.2)
- **정정 전**: install-mac.sh / windows.ps1 emit 함수 수정 → 4종 플랫폼 분기
- **정정 후**: `opal/bootstrapper/` 4개 파일이 마커 텍스트 SSOT — 여기를 수정하면 macOS·Windows 어댑터가 자동으로 동일 게이트를 배포 (어댑터 계층 SSOT 원칙에 정확히 부합)

### skip 게이트 설계
- 조건: `echo $OPAL_BOOTSTRAP` 출력이 정확히 `off`
- 동작: 이하 부트스트랩 전체(정체성·헌법·하네스·PM 포함) 생략 → 순수 Claude Code 동작
- 폴백: `off` 아니거나 Bash 불가 → 게이트 무시, 정상 진행 (fail-safe)
- 기존 `[WORKER]` 스킵(디스패치 첫 줄)과 별개의 독립 경로

## 변경 파일

| 파일 | 변경 내용 |
|------|---------|
| `opal/bootstrapper/claude-bootstrap.md` | 코드블록 내 skip 게이트 문단 삽입 (v1.0.1) |
| `opal/bootstrapper/codex-bootstrap.md` | 코드블록 내 skip 게이트 문단 삽입 (v1.0.1) |
| `opal/bootstrapper/gemini-bootstrap.md` | 코드블록 내 skip 게이트 문단 삽입 (v1.1.1) |
| `opal/bootstrapper/cursor-bootstrap.mdc` | frontmatter 직후 본문 skip 게이트 문단 삽입 |
| `opal/core/AGENT.md` | Eager step 0 스킵 게이트 추가 + 변경이력 v3.6 (040) |

## 테스트 결과

- L1 (정적 검사): **10/10 All Pass** (TS-001~012)
- L2 (install 재배포 후): 환경 의존 — 캡틴 직접 확인 필요
  - `scripts/install-mac.sh` 재실행 후 `export OPAL_BOOTSTRAP=off` 세션 동작 검증
- L3 (회귀): 환경 의존 — 미설정 세션 기존 부트스트랩 정상 동작 확인

## 후속 작업

1. **install 재배포** (캡틴 직접): `scripts/install-mac.sh` 재실행 → 4종 배포 파일 갱신 후 L2/L3 검증
2. **커밋**: 캡틴 지시 시 수행 (5파일 + 태스크 산출물)
