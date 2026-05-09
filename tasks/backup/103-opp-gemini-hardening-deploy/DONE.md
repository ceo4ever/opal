# DONE: Gemini Hardening 글로벌 배포

> 완료일: 2026-04-09

## 작업 요약

`GEMINI HARDENING` 섹션을 `~/.gemini/GEMINI.md`에 독립 마커로 배포하는 인프라를 구현했다.

## 산출물

| 파일 | 변경 | 설명 |
|------|------|------|
| `opal/bootstrapper/gemini-hardening.md` | 신규 | HARDENING 소스 파일 (4-backtick 블록으로 SSOT 일치 보장) |
| `scripts/install-mac.sh` | 수정 | HARDENING_START/END 상수, extract_bootstrap_content 4-backtick 지원, install_gemini_hardening() 함수, install_opal() 호출, print_summary() 항목 추가 |

## 특이사항

- `extract_bootstrap_content()`에 4-backtick 외부 블록 지원 추가 — PLAN 미명시였으나 내부 ` ``` ` 보존을 위해 필요. 기존 3-backtick 블록 하위 호환 유지
- TASK.md의 `print_installed_summary` vs 코드 `print_summary` 불일치 — PLAN.md에 기록, 코드 기준 처리

## 운영 노트

HARDENING SSOT는 프로젝트 루트 `GEMINI.md`다. GEMINI.md HARDENING 섹션 내용 변경 시 `opal/bootstrapper/gemini-hardening.md`도 함께 갱신해야 한다.
