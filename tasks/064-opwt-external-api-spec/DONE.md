# DONE: opwt 외부 API 명세서 관리 타입 추가

> 완료일: 2026-04-01 | 태스크: 064

## 완료 요약

외부(서드파티) API 명세서를 opwt의 프로젝트 특화 선택 관리 타입으로 추가했다.
메타, 구글광고 등 외부 API 연동 프로젝트에서 기획 단계에 API 스펙을 산출물로 작성·관리하고, 정책서·IA·TRD와 논리적으로 연결할 수 있다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/opal-pilot-write-tech/SKILL.md` | v1.4 — 프로젝트 특화 선택 타입에 외부 API 명세서 추가, 커버 범위 업데이트 |
| `opal/skills/opal-pilot-write-tech/references/network-guide.md` | §1 유형 정의 추가, §2 연결 맵 4쌍 추가, §5 diagnosis.json 타입 추가, §7-4 워커 프롬프트 추가, §10 api-spec 역할 재정의 |
| `opal/skills/opal-pilot-write-tech/references/consistency-rules.md` | §1 크로스 체크 3쌍 추가, §7 Tier4/5 재편, §8 구분 주석 추가 |

## 핵심 설계 결정

- **외부 API 명세서** (기획 단계, opwt 관리) vs **api-spec** (개발 참조, reference_artifacts) 명확 구분
- 모든 프로젝트에 강제하지 않는 "프로젝트 특화 선택 타입" 분류 신설
- 기존 reference_artifacts.api-spec 제거 없이 역할 재정의로 하위 호환 유지
