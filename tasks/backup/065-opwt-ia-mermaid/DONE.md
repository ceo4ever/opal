# DONE: opwt IA 산출물 JSON + Mermaid 이중 출력

> 완료일: 2026-04-01 | 태스크: 065

## 완료 요약

IA 산출물을 JSON + Mermaid 사이트맵 이중 출력으로 확정했다.
`ia.json` (구조 데이터) + `ia-sitemap.md` (Mermaid 시각화)가 IA 작성의 기본 산출물이 된다.

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/skills/opal-pilot-write-tech/SKILL.md` | v1.5 — IA 설명에 JSON+Mermaid 명시 |
| `opal/skills/opal-pilot-write-tech/references/network-guide.md` | §9 전면 재작성 — 이중 출력 정의, Mermaid 변환 스펙, JSON 스키마 확장, xlsx 단일 시트 컬럼 정의 |

## 핵심 설계 결정

- `ia.json` + `ia-sitemap.md` 필수 / `ia.xlsx` 선택
- depth별 classDef 스타일 + access(admin/member) 오버라이드 방식
- 50개 초과 시 1depth 기준 도메인별 분리
- JSON 스키마: `type`(html/app/popup/batch/external-api), `description`(화면 설명) 필드 추가, `conditions` → `features[].description`에 통합
- xlsx 단일 시트 14컬럼: 번호/1~4Depth/타입/화면ID/화면명/화면설명/URL/접근권한/기능/기능설명/비고
