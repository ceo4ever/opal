# DONE: OPAL 모델 매핑 최신화 + 최신 추종 전략 도입

> 완료일: 2026-06-02 20:18 KST | 태스크: 011 | 스킬: opp | 모드: agentic
> 시작: 2026-06-02 19:57 | 종료: 2026-06-02 20:18

## 결과 요약

OPAL의 플랫폼별 모델 매핑을 2026-06 최신 라인업으로 갱신하고, 가능한 플랫폼에 "최신 추종(부동 별칭)" 전략을 도입했다. TASK 배경 분석이 식별한 3개 동기화 지점에 더해 **windows.ps1(4번째 지점)을 신규 발견**하여 4곳 모두 정합화했다.

## 최종 확정 매핑

| 레벨 | Claude | Gemini | OpenAI (참조전용) | Codex |
|------|--------|--------|--------|-------|
| `light` | `haiku` | `gemini-3.1-flash-lite` (핀) | `gpt-5.4-mini` | `gpt-5.4-mini` |
| `standard` | `sonnet` | `gemini-flash-latest` (별칭) | `gpt-5.5` | `gpt-5.5` |
| `advanced` | `opus` | `gemini-pro-latest` (별칭) | `gpt-5.3` | `gpt-5.3-codex` |

- **부동 별칭 자동 추종**: Claude(`haiku/sonnet/opus`) + Gemini standard/advanced(`gemini-flash-latest`/`gemini-pro-latest`) → stale 자동 해소
- **핀 + 분기점검**: Gemini light(`gemini-3.1-flash-lite`)·Codex·OpenAI는 `-latest` 별칭 미존재 → §5 갱신 가이드에 "분기마다 공식 docs 점검" 운영 규칙 보강

## 변경 파일 (소스 4개 — ~/.opal 배포본 무수정)

| 파일 | 변경 |
|------|------|
| `opal/core/references/opal-model-mapping.md` | §2 표 4컬럼 최신화 + OpenAI "(참조전용)" 각주 + §5 운영 규칙 + 변경이력 v1.3 |
| `scripts/install-mac.sh` | gemini/codex dict + codex TOML map + 기본값 `gpt-5.5` + 변경이력 v2.7 |
| `opal/core/references/agents.md` | Gemini 변환 표 + 변경이력 v1.5 |
| `scripts/install/windows.ps1` | ModelMap gemini/codex + toml 기본값 + 변경이력 v1.9.0 |

## 요구사항 달성

| 요구사항 | 결과 |
|---------|------|
| R-1 Gemini 최신화 | ✅ 4곳 동기 (standard/advanced 별칭 + light 핀) |
| R-2 OpenAI 컬럼 처리 | ✅ 코드 근거로 "미배선 죽은 컬럼" 판정 → 참조전용 각주 + gpt-5.x 갱신 |
| R-3 Codex 최신화 | ✅ dict+TOML+기본값+SSOT 모두 gpt-5.4-mini/gpt-5.5/gpt-5.3-codex |
| R-4 최신 추종 전략 | ✅ Claude/Gemini(flash·pro) 별칭 + §5 분기점검 규칙 |
| R-5 동기화 검증 | ✅ 5위치(3곳→4곳 확대) 불일치 0건 |
| R-6 변경이력 | ✅ 4파일 모두 011 이력 기재 |

## QA / 검증

- **PLAN QA**: Critical 1건(`gemini-pro-latest` 미확인) → PM이 공식 [Gemini Changelog](https://ai.google.dev/gemini-api/docs/changelog)(2026-01-21)로 실재 확정 해소. `gemini-flash-lite-latest`는 미존재 확인([Firebase docs](https://firebase.google.com/docs/ai-logic/models)) → light는 stable GA 핀.
- **EXECUTE QA**: pass. 구값 0건, 5위치 동기 0건, `bash -n scripts/install-mac.sh` 통과.
- 모든 모델 ID는 공식 docs WebFetch 대조로 확정 (citation-rules §0 준수).

## 잔여 / 후속

- **install 재배포 미실행** — 소스만 수정됨. `~/.opal/` 반영은 `scripts/install-mac.sh` 재실행 필요 (캡틴 지시 시).
- `gemini-flash-latest`/`gemini-pro-latest`는 현재 preview 빌드 추종 (부동 별칭 특성 — GA 승격 시 자동 전환).
- 후속 후보: 순수 OpenAI API 어댑터 배선 시 OpenAI 컬럼 활성화.

## 상세 이력

PM 대행 일지: `AGENTIC-LOG.md` (게이트 3회 / 오류 1 / 수정 1 / 의사결정 3 / 개선 2 / 에스컬레이션 0)
