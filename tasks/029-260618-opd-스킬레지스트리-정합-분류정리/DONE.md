# DONE: opal/skills 레지스트리 정합 + 분류 정리 + opal-brain 오기재 교정 + validate lint

> 완료일: 2026-06-18 14:42 (KST) | 스킬: //opd (semi-agentic) | 판정: All Pass

## 1. 목표 달성

`opal-skills-registry.json`(스킬 SSOT)의 드리프트·분류 비일관을 해소하고, opal-brain의 잘못된 "Pilot" 분류를 교정하며, 재발 방지 `validate`를 추가했다. 4기능(F-001~F-004) 전부 완료.

## 2. 산출물 (수정 4 + 신규 1)

| 파일 | 변경 내용 |
|------|----------|
| `opal/core/references/opal-skills-registry.json` | dangling 2건(`op-sdd-tasks`·`opal-orchestrator`) 제거 / `op-sdd-action-plan` 신규 등록 / `op-brain` 그룹 신규 / 3건 재배치(`op-spec-validator`→op-sdd, `op-brain-ingest`→op-brain, `opal-pilot-project-dev`→opal-pilot) / `system-architecture-html` paths 보충 / v3.5.0·changelog |
| `docs/PROJECT.md` | op-sdd-tasks 컴포넌트 행 삭제 + opal-brain 유형 오기재("오케스트레이터/4모드 Pilot"→operator 멀티모드 라우터) 교정 |
| `docs/ARCHITECTURE.md` | opal-orchestrator 잔존 2행 삭제 |
| `opal/tools/skill-registry/skill-registry.js` | `validate()` 확장 — no-SKILL.md warning→error 격상 + `validateUnregistered()` 신규(소스 환경 전용, `opal/skills/`+`skills/` 양쪽 스캔) |
| `opal/tools/skill-registry/tests/test-validate.js` (신규) | TC1~TC5 단위 테스트 (RED-first) |

## 3. 검증 결과 (All Pass)

- **단위 테스트**: TC1~TC5 전부 PASS (RED였던 TC2 dangling·TC3 unregistered가 GREEN 전환)
- **통합 validate**: 실 레포 `node skill-registry.js validate` → errors 0, unregistered 0, exit 0
- **드리프트 해소**(S-5): op-sdd-tasks 0·opal-orchestrator 0·op-sdd-action-plan 1
- **그룹 재배치**(S-6): 3건 정합 배치, opal 그룹은 operator 7종만 잔류(opal-brain 포함)
- **문서 정합**(S-7·S-8): 본문 잔존 0(변경이력 행만), opal-brain "Pilot" 표기 제거
- **불변 회귀**(S-9): `opal/skills/opal-brain/`·`brain_tool.py` 변경 0건, `//opbr`→opal-brain 매칭 유지
- **회귀**(S-10): match/list/get 정상 (brain-tool pytest는 yaml 모듈 미설치로 SKIP — 변경 무관)
- **코드품질·보안**: JS 문법·JSON·@header PASS / 시크릿 0·path traversal 없음

## 4. 핵심 의사결정

1. **F-003 리네임 철회** (PLAN 게이트, 캡틴 지적): 초기엔 `opal-brain → opal-pilot-brain` + `opbr→opb` 리네임을 합의했으나, 실제 SKILL.md 검증 결과 opal-brain은 **pilot이 아님**(독립 4모드 라우터 + brain-tool 직접 호출, 워커 디스패치·STATE·단계 파이프라인 없음). 리네임은 새 오분류를 만드는 것이라 철회하고, **PROJECT.md의 "Pilot" 오기재 교정**으로 전환. → 9파일 cascade 소멸, 4파일 수정으로 축소.
2. **dangling 2건 모두 제거** (M2): git 이력으로 둘 다 삭제 확인(op-sdd-tasks→commit a940318 op-sdd-plan 통합, opal-orchestrator→commit 45d2118 opal-pm.md 대체). 리네임 매핑 아님.
3. **R4 = validate 확장**(신설 아님): 기존 `validate()`를 dangling error 격상 + unregistered 역방향 감지로 확장.
4. **validate가 즉시 효용 실증**: 작동 중 기존 잠복 드리프트 `system-architecture-html`(paths에 `~/.opal/skills/...` 누락) 추가 검출 → 형제 항목 패턴에 맞춰 보충.

## 5. 후속 태스크 후보

- **install 재배포** — `~/.opal/`에 레지스트리·skill-registry.js 동기화 (배포 경계 준수, 별도 작업)
- **validate를 커밋 훅/CI(opgc)에 연결** — 레지스트리 드리프트 상시 차단
- **validate 소스 경로 인식 확장** — standalone 스킬의 소스 위치(`skills/`)도 정합 검사(현재 배포 경로 의존)

## 6. 미커밋

커밋 규칙에 따라 **커밋하지 않음** — 캡틴의 명시 지시 시 수행.
