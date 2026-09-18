---
template: sdlc-v2
---
# TASK: OPAL Docs 스킬 문서 화면

## Problem
OPAL Console의 전역 내비게이션과 라우터에는 대시보드·프로젝트·태스크·메모리·환경·프로젝트 브레인·설정만 있고, 사용자가 스킬을 목적별로 찾고 호출 규격과 예시를 읽을 수 있는 문서 화면이 없다 (`dashboard/frontend/src/components/app-shell/AppShell.tsx:89-97`, `dashboard/frontend/src/router.tsx:23-37`). 기존 환경 화면은 레지스트리의 목록만 표시하고 상세 스펙을 제공하지 않으며 (`dashboard/backend/routers/doctor.py:157-172`, `dashboard/frontend/src/pages/doctor/DoctorPage.tsx:409-410`), 소스 스킬과 레지스트리의 이름 집합도 일치하지 않아 신규 OPPB 파일럿과 내부 단계 스킬이 도움말에서 누락된다 (`opal/skills/opal-pilot-project-build/SKILL.md:1-20`, `opal/core/references/opal-skills-registry.json:1-68`).

## Proposed outcome
OPAL Console에 `OPAL Docs` 메뉴가 생기고, 사용자는 전체 스킬을 검색·분류해 빠르게 찾은 뒤 각 스킬의 목적, 호출 형식, 옵션, 사용 예시, 파이프라인과 관련 스킬을 shadcn/ui 문서 스타일의 상세 화면에서 확인하고 명령을 복사할 수 있다. 화면에 노출되는 카탈로그는 소스 스킬과 레지스트리 사이의 누락·이름 불일치를 해소한 완전한 레지스트리를 사용한다.

## Affected users and systems
OPAL을 처음 도입하거나 적합한 `//` 스킬을 선택하려는 사용자와 숙련 사용자가 영향을 받는다. 변경 범위는 OPAL Console 프론트엔드의 메뉴·라우팅·스킬 문서 화면, 필요한 읽기 전용 백엔드 조회 표면, 프레임워크 스킬 레지스트리와 그 검증·배포 경계다. 기존 프로젝트·태스크·메모리·환경·브레인·설정 화면의 동작 변경은 범위에서 제외한다.

## Constraints
- C-1: 기존 OPAL Console의 React·TypeScript·Vite·Tailwind·shadcn/ui 구조와 전역 색상 토큰을 재사용하고 별도 문서 프레임워크나 외부 런타임 의존성을 추가하지 않는다 (`docs/PROJECT.md` §주요 컴포넌트 (OPAL Console), `dashboard/frontend/src/components/markdown-view.tsx:298-323`).
- C-2: 스킬 메타데이터를 프론트엔드에 하드코딩하지 않고 레지스트리·각 `SKILL.md`·`pipeline.json` 등 기존 소스 자산에서 읽기 전용으로 파생한다.
- C-3: 사용자 호출 가능 스킬과 파일럿이 디스패치하는 내부 단계 스킬을 구분해 표시하되, 어느 그룹도 데이터 누락 때문에 사라지지 않아야 한다.
- C-4: 명령 예시는 그대로 복사해 사용할 수 있어야 하며 터미널 프롬프트 문자나 정규식 메타문자를 사용자 대면 예시에 포함하지 않는다.
- C-5: 기존 Console의 읽기 전용 원칙을 유지하고 스킬 문서 화면에서 스킬 실행·파일 수정·설치를 수행하지 않는다 (`docs/ARCHITECTURE.md` §OPAL Console (로컬 프로젝트 관리 대시보드)).
- C-6: 소스 변경은 프로젝트 경로에서 수행하고 `~/.opal/` 배포본을 직접 편집하지 않으며, 배포 확인은 install 경유로 한다 (`docs/CONVENTIONS.md` §배포 경계).
- C-7: 데스크톱과 모바일에서 탐색·상세 열람·명령 복사가 가능하고 키보드 포커스와 접근 가능한 이름을 제공한다.

## Acceptance criteria
- AC-1: Console 좌측 내비게이션에 `OPAL Docs`가 표시되고 `/docs/skills` 및 공유 가능한 스킬 상세 URL로 이동할 수 있다.
- AC-2: 카탈로그에서 스킬명·alias·설명·자연어 용도로 검색하고 파일럿·독립·오퍼레이터·내부 단계 그룹과 도메인으로 필터링할 수 있다.
- AC-3: 스킬 상세 화면에 제목·설명·분류, Quick Start, Usage, Arguments/Options, 사용 시점, 복사 가능한 예시, 파이프라인, 관련 스킬 및 원본 경로가 표시된다. 적용할 수 없는 섹션은 거짓 기본값 대신 명시적으로 생략하거나 없음으로 표현한다.
- AC-4: `opal/skills/*/SKILL.md`와 `skills/*/SKILL.md`의 실제 스킬 집합을 레지스트리와 기계 대조했을 때 의미상 미등재 스킬이 0건이고, OPPB 파일럿과 그 내부 단계 스킬이 올바른 그룹·alias·파이프라인 정보로 조회된다.
- AC-5: 온보딩과 스킬 관리처럼 폴더·레지스트리 canonical 이름이 다른 기존 항목도 중복 카드 없이 하나의 스킬로 정규화되어 조회된다.
- AC-6: 목록·상세 조회 실패, 빈 결과, 존재하지 않는 alias, 상세 원본 부재에 대한 로딩·빈 상태·오류 상태가 제공된다.
- AC-7: 프론트엔드 빌드·린트·관련 컴포넌트 테스트와 백엔드 관련 테스트가 통과하고, 기존 Console 주요 라우트 회귀가 없다.
- AC-8: 설치 스크립트 경유 배포 후 OPAL Console에서 신규 메뉴와 스킬 상세가 표시되고, 설치본 레지스트리에서도 AC-4의 누락 0건 검사가 통과한다.
