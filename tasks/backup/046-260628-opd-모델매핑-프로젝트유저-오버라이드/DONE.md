# DONE: 모델 매핑 provider별·등급별 오버라이드 (프로젝트/유저 2계층 setting)

> 완료일: 2026-06-28 | 스킬: //opd --agentic | 모드: agentic
> 태스크: 046-260628-opd-모델매핑-프로젝트유저-오버라이드

## 1. 최종 결과 요약

OPAL 레벨↔모델 매핑을 **setting.json의 실모델명**을 SSOT로 삼아 사용자가 LLM별·레벨별로 직접 지정하고, OPAL이 그 값을 그대로 사용하도록 전환했다. 전역(`~/.opal/setting.json`)과 프로젝트(`{프로젝트}/.opal/setting.local.json`)의 **2-레이어 머지**(로컬 우선, 없으면 전역, 둘 다 없으면 오류)를 **부트스트랩 step 0**에서 수행한다.

대화 중 설계가 3차 진화했고, 최종 설계는 아래와 같다(초기 "default 폴백" 안은 폐기됨).

## 2. 최종 동작 (설계 v3)

| 항목 | 동작 |
|------|------|
| SSOT | `opal/core/setting.default.json` (실모델 JSON). install이 `~/.opal/setting.json`에 시드. |
| 머지 | 부트스트랩 step 0: 전역 setting.json 읽고 → 프로젝트 setting.local.json 셀 단위 덮어쓰기(로컬 우선) → effective setting |
| 적용 대상 | effective setting의 `bootstrap`(스킵 게이트) + `models`(모델 매핑) |
| 미설정 | 감지 플랫폼의 해당 레벨 셀이 전역·로컬 둘 다 없으면 **오류**(디스패치 중단). 표 폴백·`"default"` 없음 |
| install | setting.json 없으면 concrete 시드, 있고 `models` 키 없으면 멱등 병합(기존 값·bootstrap 보존) |

## 3. 변경 파일 (12)

| 파일 | 변경 | 버전 |
|------|------|------|
| `opal/core/setting.default.json` | `models` concrete 실모델 SSOT(claude/gemini/openai/codex/cursor × light/standard/advanced) | - |
| `opal/core/AGENT.md` | Eager step 0 게이트에 setting.local.json 머지(bootstrap+models) + §모델 매핑 2-레이어·미설정 오류 | v3.11 |
| `opal/core/references/opal-model-mapping.md` | §5 전면 신설·개정(2-레이어 머지·오류·시드), §2 SSOT 주석, 머지 시점 step 0 | v2.0 |
| `opal/core/references/opal-harness.md` | §6 오버라이드 포인터 1줄 | - |
| `opal/core/references/agents.md` | Codex 인라인 주입 §5 오버라이드 참조 | v1.9 |
| `opal/bootstrapper/claude-bootstrap.md` | 스킵 게이트 setting.local.json 머지 | v1.0.3 |
| `opal/bootstrapper/gemini-bootstrap.md` | 동일 | v1.2 |
| `opal/bootstrapper/codex-bootstrap.md` | 동일 | v1.0.3 |
| `opal/bootstrapper/cursor-bootstrap.mdc` | 동일 | - |
| `scripts/install-mac.sh` | `install_opal_setting` models 멱등 병합(베이킹 dict 불변) | - |
| `scripts/install/windows.ps1` | 동일 병합 미러링 | - |
| `.opal/MEMORY.md` | 채번 last_task_number 46 | - |

## 4. 검증

- S-1~S-7 + RS-1~RS-5 (TEST-SCENARIO §3·§8) **All Pass** — 2-레이어 머지(로컬우선·전역유지·미설정오류) 시뮬, install 멱등 병합, `"default"` 0건, 헤더↔변경이력 버전 정합, 모델 베이킹 dict 불변, step 0 머지 일관 반영(AGENT.md+4 bootstrapper).

## 5. 특이사항 (투명성)

- **PLAN.md = PM 직접 작성**: op-dev-plan 워커가 API 인프라 오류 3회(connection drop)로 미산출 → agentic 완수 의무에 따른 PM 폴백 (AGENTIC-LOG #9~#14).
- **부트스트랩 step 0 머지 = PM 직접 편집**: 부트스트랩 핵심·정밀 편집 + 워커 반복 실패로 PM이 직접 수행 (#30~#31).
- **Windows 병합**: mac에서 PowerShell 런타임 테스트 불가 — 구문 정합만 검증. **후속: 실제 Windows 환경 검증 필요.**
- 설계 3차 진화: ①provider×등급 오버라이드 → ②inert "default" scaffold → ③"default" 폐기·실모델 SSOT·step0 머지·미설정 오류 (최종).

## 6. 적용(배포) 안내 — 캡틴 환경

1. **재배포(install) 필수**: 수정은 소스에 있음. `~/.opal`·프로젝트 `CLAUDE.md` 반영하려면 재설치.
2. **전역 setting.json 과도기 `"default"` 잔재**: `rm ~/.opal/setting.json` 후 재설치 → concrete 시드.
3. **invest-stock**: `setting.local.json`이 `"bootstrap":"off"`라 재배포 후 그 프로젝트에서 OPAL이 꺼진다. OPAL 켜고 모델 오버라이드를 쓰려면 bootstrap 키 제거(또는 on) + models를 실모델로(현재 전부 `"default"`는 무효).

## 7. 후속 과제

- [ ] Windows install 병합 실제 환경 검증.
- [ ] (선택) install 에이전트 frontmatter 베이킹 dict(`install-mac.sh:563-567`)를 setting.default.json SSOT에서 읽도록 통일 — 현재 베이킹 dict / 표 / setting.default.json 삼중 유지 잔존.
- [ ] (선택) 전역 setting.json에 과도기 `"default"` 셀이 있는 사용자 자동 마이그레이션(현재는 rm+재설치 수동).

## 8. 커밋

미커밋 상태 유지 (커밋은 캡틴 명시 지시 시에만).
