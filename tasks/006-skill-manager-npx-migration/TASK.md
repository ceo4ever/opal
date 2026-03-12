# TASK: skill-manager를 npx skills 기반으로 전환

> 작성일: 2026-03-12 | 작업 유형: 기능 개선

## 작업 목표

OPAL의 skill-manager 스킬을 자체 카탈로그(skills-catalog.md) 기반에서 `npx skills` CLI(vercel-labs/skills) 기반으로 전환하여, 실시간 생태계 검색 및 원커맨드 설치를 지원한다.

## 배경

- 현재 skill-manager는 정적 Markdown 카탈로그(549개)를 파싱하여 스킬을 검색
- 카탈로그에 없는 스킬은 찾을 수 없고, 업데이트도 수동
- [vercel-labs/skills](https://github.com/vercel-labs/skills) (9.7K stars, 주간 503.5K 설치)가 에이전트 스킬 패키지 매니저로 업계 표준화 추세
- 웹 카탈로그 [skills.sh](https://skills.sh/)에서 실시간 검색 가능
- `npx skills find/add/check/update` 명령으로 검색/설치/업데이트를 일원화

## 요구사항

- [ ] skill-manager SKILL.md의 검색 프로세스를 `npx skills find [query]`로 전환
- [ ] skill-manager SKILL.md의 설치 프로세스를 `npx skills add <pkg>`로 전환
- [ ] 설치된 스킬 목록 확인은 기존 방식(~/.opal/community-skills/ 탐색) 유지
- [ ] 스킬 삭제는 기존 방식(rm -rf) 유지
- [ ] skills-catalog.md 파일 삭제
- [ ] install-mac.sh에서 카탈로그 복사 로직 제거
- [ ] references/skills.md에 skill-manager 트리거 설명 업데이트
- [ ] AGENT.md에서 catalog/ 참조 제거
- [ ] Node.js 미설치 환경에 대한 폴백 안내 추가

## 제약 조건

- 기본 번들 31개는 현재 방식 유지 (프레임워크에 포함, install-mac.sh로 복사)
- 커뮤니티 스킬 설치 경로는 `~/.opal/community-skills/`로 유지
- `npx skills add`의 기본 설치 경로와 OPAL 경로 차이가 있을 수 있음 → RESEARCH에서 확인 필요

## 관련 문서

- `opal/skills/skill-manager/SKILL.md` — 현재 skill-manager 정의
- `opal/catalog/skills-catalog.md` — 삭제 대상 카탈로그
- `opal/core/references/skills.md` — 스킬 레지스트리
- `opal/core/AGENT.md` — 에이전트 정의 (catalog 참조)
- `scripts/install-mac.sh` — 설치 스크립트 (카탈로그 복사 로직)
