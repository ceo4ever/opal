# DONE: opwt 외부 참조 산출물 지원 + wtm wireframe 모드

> 완료일: 2026-04-01

## 요약

opwt(opal-pilot-write-tech)가 와이어프레임, ERD, API 명세서 등 외부 참조 산출물을 활용하여 기획 문서를 작성/검증할 수 있도록 하고, wtm(web-to-markdown)에 wireframe 분석 모드를 추가했다.

## 변경 파일

| # | 파일 | 변경 내용 |
|---|------|----------|
| 1 | `skills/web-to-markdown/SKILL.md` | wireframe 모드 추가 (v1.2 → v1.3) — 5섹션 산출물 형식, PROJECT.md 기반 저장 경로, `_index.md` 자동 생성 |
| 2 | `opal/skills/opal-pilot-write-tech/references/network-guide.md` | §10 외부 참조 산출물 가이드, `reference_artifacts[]` 스키마 확장, Phase 1/3 워커 프롬프트 확장 |
| 3 | `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | §8 외부 참조 검증 6쌍, QA 워커 프롬프트 확장, Tier 4 추가 |
| 4 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 커버 범위 "외부 참조" 추가, Phase 2 진단 확장, 참조 가이드 확장 (v1.2 → v1.3) |

## 설계 결정

| # | 결정 | 근거 |
|---|------|------|
| 1 | `reference_artifacts`는 optional 필드 | 기존 diagnosis.json 하위 호환성 유지 |
| 2 | 외부 참조 검증은 Tier 4 (최하위 우선순위) | reference_artifacts 없는 프로젝트에 영향 없음 |
| 3 | 스킬 간 파이프라인은 PM 오케스트레이션으로 해결 | opwt "문서가 인터페이스" 원칙 유지 |
| 4 | wtm wireframe 모드를 별도 스킬 대신 기존 wtm에 추가 | 기존 인프라(3단계 폴백, 병렬 처리) 재사용, 스킬 과다 방지 |
| 5 | 저장 경로는 PROJECT.md 문서 테이블에서 매칭 | 프로젝트별 기존 구조 존중 |

## 후속 작업

- [ ] `~/.opal/skills/web-to-markdown/SKILL.md` 배포 동기화 (install-mac.sh 또는 수동 cp)
