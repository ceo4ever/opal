# DONE: OPAL Brain 프로젝트별 비즈니스 용어집(term) 관리 체계

> 완료일시: 2026-06-17 15:17 KST | 스킬: opp | 모드: semi-agentic | 태스크: 027

## 완료 요약

OPAL Brain을 "검색 위키"에서 **업무 언어 번역 계층**으로 격상하기 위한 프로젝트별 비즈니스 용어(`term`) 관리 체계를 설계·반영했다. 진짜 레버는 새 스키마가 아니라 ① 용어가 자동 축적되는 경로(ingest), ② 답변이 업무 언어로 번역되는 행동 규칙(advisory), ③ 일관성을 결정론적으로 집행하는 단 한 지점(lint 신규 2종)이라는 골격(★1~★5 + 진입점 ③)을 그대로 구현했다.

## 최종 산출물 (changed_files)

| 구분 | 파일 | 핵심 |
|------|------|------|
| 코드 | `opal/tools/brain-tool/brain_tool.py` | lint `term_duplicate`·`alias_collision` 신설 + search `--include-draft`(R-6 **term 한정**) + cmd_init 동적 로드 + @header |
| 테스트 | `opal/tools/brain-tool/tests/test_brain_tool.py` | TestTermDraft027·TestTermLint027 (term 동적로드·draft 필터·lint 일관성·회귀) + DRY 정리 |
| 템플릿 | `opal/tools/brain-tool/templates/page-term.md` | 신규 term 페이지 템플릿 |
| SCHEMA | `opal/tools/brain-tool/templates/schema-template.md` | §1.5 term 타입(도메인·채택 게이트) + §2 frontmatter(aliases/actors/surfaces) + §4 다층 근거 토큰(POL-/ia:) |
| 헌법 | `opal/core/references/harness/citation-rules.md` | §8.6~8.9 델타(다층 근거·업무 표면·개발자 부록 분리·5W1H 사고 프레임). §8.1~8.5 원문 불변 |
| 스킬 | `opal/skills/opal-brain/SKILL.md` v1.3 | init term 채택 가이드 / ingest draft term 추출 / query business-first + **진입점 ③(미등록 용어 발견→draft 제안→확정 시 active)** / lint 8종 |
| 스킬 | `opal/skills/op-brain-ingest/SKILL.md` v1.3 | CLOSE 채택 게이트(채택 프로젝트만) + term 작성 규칙(draft) |
| 지식 | `.opal/brain/pages/concept/brain-business-term-layer.md` | 027 설계 설명 concept 페이지(+ D-7 역링크) |

## 핵심 결정

- **수혜자 = 다운스트림 실서비스**(★1): OPAL 자기 brain은 term 미채택, concept 1장만. 변경은 SSOT 3종 + brain_tool.py.
- **타입명 `term`**(★2), **CLOSE ingest 자동 draft 축적**(★3), **인용 형식=SCHEMA §4 / 원칙=citation §8 분리**(★4).
- **R-6 결정**: draft 검색 필터는 `type==term` 한정 — 비-term 페이지 가시성 회귀 0(캡틴 승인).
- **진입점 ③**(캡틴 승인): query 중 미등록 업무 용어 발견 시 draft 제안 → 사용자 확정 시 active 승격(승격 빈틈 해소). 자동 등록 금지.

## 검증 결과

- 단위 테스트 **100 passed, 회귀 0** (OPAL venv 독립 재현).
- 컨벤션 진단 **Critical/High 0** (Medium GC-C002 DRY 즉시 정리). 보고서: `GC-CONVENTION-2026-06-17T14-00-39.md`.
- 027 산출물 brain validate **clean**, 변경이력 027 행 4건 확인.
- ★5 검증 경계: query 번역 품질은 advisory(LLM 행동)로 OPAL 내 실증 불가 → 다운스트림 실서비스에서 실증.

## 잔여·후속

- **install 재배포 필요**: 변경은 프로젝트 소스에만 존재. `~/.opal/` 배포 후에야 `//opbr` 런타임에 반영됨.
- **사전 brain 위생 부채**(027 무관): `sources/` 디렉토리 부재 + 무관 페이지 2건 구식 인라인 YAML → 별도 정리 태스크 후보.
- 컨벤션 Low/Info 3건(@header exports·scenarios, page-term frontmatter 미등록) → 후속 노트.
- **미커밋**: 커밋은 캡틴 지시 시에만.
