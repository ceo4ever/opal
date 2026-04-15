# DONE: opal-pm.md 핵심 제약 인용 의무 규칙 추가 + 파일럿 디스패치 템플릿 보완

> 완료일시: 2026-04-15 15:24 | 스킬: opp | 모드: agentic

## 완료 요약

PM이 워커에게 디스패치할 때 정책서·명세·도메인 규칙을 `[MUST] <문서명> §N: <규칙 원문>` 원문 인용 형식으로 주입해야 한다는 규칙을 opal-pm.md에 추가하고, opal-pilot-dev/opal-pilot-sdd 디스패치 템플릿에 `**핵심 제약**:` 필드를 반영했다.

## 변경 파일

| 파일 | 변경 내용 | 버전 |
|------|----------|------|
| `opal/core/references/opal-pm.md` | §3 Step 3에 `#### 인용 의무 규칙` 소섹션 추가 + 워커 컨텍스트 주입 템플릿 `[MUST]` 포맷 추가 | v1.6 |
| `opal/skills/opal-pilot-dev/SKILL.md` | ANALYSIS/PLAN/EXECUTE 디스패치 프롬프트에 `**핵심 제약**:` 필드 추가 | v3.0 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | Phase 1(SPEC)/Phase 3(DESIGN) 디스패치 프롬프트에 `**핵심 제약**:` 필드 추가 | v2.8.0 |

## 요구사항 충족 확인

| 요구사항 | 완료 |
|---------|------|
| R-1: opal-pm.md §3 Step 3 인용 의무 규칙 추가 | ✅ |
| R-2: 워커 컨텍스트 주입 템플릿 `[MUST]` 포맷 추가 | ✅ |
| R-3: opal-pilot-dev 디스패치 템플릿 `**핵심 제약**:` 필드 추가 | ✅ |
| R-4: opal-pilot-sdd 디스패치 템플릿 `**핵심 제약**:` 필드 추가 | ✅ |

## 후속 조치

- **재설치 필요**: `opal/core/references/opal-pm.md`, `opal/skills/opal-pilot-dev/SKILL.md`, `opal/skills/opal-pilot-sdd/SKILL.md` 변경 적용을 위해 `install-mac.sh` 재실행 필요 (캡틴이 별도 결정).
