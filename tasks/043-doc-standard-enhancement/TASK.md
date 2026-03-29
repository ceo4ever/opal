# TASK: opal-doc-standard 문서 유형 확장 + 출력 형식 규칙 추가

> 작성일: 2026-03-29 | 작업 유형: 개선
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

opal-doc-standard.md의 문서 유형별 필수 섹션을 opw/opwt 커버 범위에 맞게 확장하고, 출력 형식 규칙을 추가한다.

## 배경

현재 opal-doc-standard.md는 5종(분석서, 명세서, 정책서, 설계서, 계획서)만 정의하고 있으나, opw는 보고서/가이드/기획 등을, opwt는 PRD/TRD/IA 등을 다룬다. 참조 문서로서 실제 커버 범위에 대한 가이드가 부족한 상태.

## 요구사항

- [ ] 문서 유형별 필수 섹션 6종 추가 (PRD, TRD, IA, 보고서, 가이드/매뉴얼, 기획/제안서)
- [ ] IA는 md로 구조 정보를 정리하되, 실질 내용은 JSON 형식 추천을 명시
- [ ] 출력 형식 규칙 섹션 추가 (.md 기본, .docx/.pdf 변환 시 주의사항)
- [ ] 기존 5종 유형은 그대로 유지

## 제약 조건

- opal-doc-standard.md 단일 파일 수정 (소스 + 배포본 동기화)
- 기존 구조(섹션 번호, 헤더 등) 유지
- 네트워크 정합성 규칙은 건드리지 않음 (consistency-rules.md 담당)

## 관련 문서

- `~/.opal/references/opal-doc-standard.md` (배포본)
- `opal/core/references/opal-doc-standard.md` (소스)
- `~/.opal/skills/opal-pilot-write/SKILL.md`
- `~/.opal/skills/opal-pilot-write-tech/SKILL.md`
