# DONE: 브레인 entity 지식 품질 개선 — ingest @header 전사 탈피

> 완료일: 2026-06-23 | 스킬: //opd (semi-agentic) | 태스크: 038

## 완료 요약

brain의 **entity 페이지**가 `//opbr init` 시드에서 code-scan @header를 기계 전사하여 WHAT 덤프로 전락하던 문제를, **코드 변경 없이 작성 규율 표준화**로 해결했다. entity 본문을 **5섹션 표준**(개요/책임 WHAT/설계배경 WHY/관계 HOW/소스 커버리지)으로 통일하고, @header 전사 금지·입력 큐레이션 선행·provenance 3종 태깅을 SKILL [MUST]로 명문화했다. 기존 저품질 brain은 **전체 삭제 후 재생성 런북**으로 처리한다(소급 보정·도구 게이트 미구현 — Simplicity).

## 변경 파일 (4종, 전부 `opal/` 소스 — Markdown만, 도구 코드 무변경)

| 파일 | 변경 | 버전 |
|------|------|------|
| `opal/skills/opal-brain/SKILL.md` | 핵심 엔티티 시드 entity 5섹션 표준 + @header 전사 금지·입력 큐레이션 선행·provenance 3종 [MUST] + 재생성 런북 신규 절 + ingest --all "코드→entity" drift 정정 | v1.4→v1.5 |
| `opal/skills/op-brain-ingest/SKILL.md` | STEP 4 entity 예시 5섹션 표준 + 동일 규칙 | v1.3→v1.4 |
| `opal/tools/brain-tool/templates/page-entity.md` | `## 코드 참조`→`## 소스 커버리지` 개명 + 섹션 가이던스 강화 + @header 전사 금지 주석 (frontmatter 무변경) | — |
| `opal/core/references/harness/citation-rules.md` | §8.5 brain ingest/init entity 워커 항목을 §8.2·§8.8 명문화로 구체화 + init 경로 연결 추가 | v2.2→v2.3 |

## 검증 결과

- **TEST L1 8/8 Pass** (opal-test-agent 독립 검증) — 5섹션 일관성·큐레이션/provenance 명문화·도구 무변경(git diff)·런북·§8.5 정합·drift 정정·§8.9 비위반.
- **pytest 109 passed, 회귀 0** — `## 코드 참조`→`## 소스 커버리지` 개명에도 brain-tool 무회귀.
- **S-7 [SUPERVISOR] Pass** (캡틴 확인) — 방법 A 경량 시연(배포 불요)으로 개선 규율 행동 변화 실측: state-tool 시연 entity가 5섹션·provenance(근거3/추론1/**미확보1**)·소스 커버리지 부록 분리·합성 서술 충족. 시연본: `S7-시연-state-tool-entity.md`.
- **4파일 cross-check Pass** — 3파일 entity 헤딩 완전 동일, @header 금지·provenance 일관.

## 핵심 설계 결정

1. **스코프 = entity 전용** — concept/flow/synthesis/term은 사고 기반 작성이라 양호, 손대지 않음.
2. **처리 = 전체 삭제 후 재생성** — enrich/소급보정/부분재시드/lint 신규검출/멱등 우회 전부 미구현(Simplicity).
3. **provenance = SKILL [MUST]만** — brain-tool 도구 게이트 미채택(도구는 의미 판정 불가 + "거짓 안심" 회피). 헌법 "Don't fake it"은 `(WHY 미확보)` 솔직 표기로 집행.
4. **입력 큐레이션 = SKILL 절차 강제** — why-sources 도구화 미채택(선별은 LLM 몫이라 SKILL 절차로 동일 효과).
5. **ingest --all drift 정정 포함** — 혼란의 원천이던 "코드→entity" 죽은 표 행을 코드 현실에 맞게 정정.

## 후속 (캡틴 직접/지시 대기)

- **[배포]** `opal/` 소스 → `~/.opal/` install 재배포 필요(L3 캡틴 직접). 재배포 전까지 배포본 `//opbr`는 구 규율 사용. (S-7은 소스 기준 시연으로 이미 검증)
- **[커밋]** 캡틴 지시 대기.
- **[재시드 적용]** 기존 저품질 entity(예: MAMS Google API)는 각 프로젝트에서 재생성 런북으로 정리 — 프레임워크는 도구·규율만 제공.
