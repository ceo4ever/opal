# DONE: README 오픈소스 공개 P0 정비 — MIT LICENSE + 표시·실측 정정

> 시작: 2026-05-10 14:38 | 완료: 2026-05-10 16:56 | 모드: semi-agentic | 적용 스킬: opp

## 작업 결과

OPAL의 GitHub 공개 저장소 첫 표지(README.md) + 라이선스(LICENSE) + 시스템 아키텍처 문서(docs/ARCHITECTURE.md)를 오픈소스 공개 기준으로 정비했다. R-1 ~ R-8 핵심 8건 + 캡틴 검토에서 추가된 R-9(3-way 모드 체계) / R-10(Windows Python 자동 설치 안내) 2건 = 총 10건 완료.

## 최종 변경 파일

### 신규

| # | 경로 | 내용 |
|---|------|------|
| N-1 | `LICENSE` (저장소 루트) | SPDX 표준 MIT License 본문(21줄) + `Copyright (c) 2026 OPAL contributors` |

### 수정

| # | 경로 | 변경 |
|---|------|------|
| M-1 | `README.md` L1~5 | shields.io 배지 2종 헤더 직후 삽입 (`License: MIT` + `Latest Release` 동적) |
| M-2 | `README.md` L37 (주요 특징) | "Agentic Mode" → "3-way 실행 모드 — interactive / semi-agentic(기본) / agentic" |
| M-3 | `README.md` L59 (ToC) | "Agentic Mode — 자율 실행" → "Pilot 실행 모드 (3-way)" |
| M-4 | `README.md` L77 | Windows winget Python 3.14 자동 설치 안내 1줄 신규 |
| M-5 | `README.md` L96 | `OPAL_VERSION=v0.1` → `<원하는-태그>` placeholder + GitHub Releases 링크 (영구 정확) |
| M-6 | `README.md` L103 | 부트스트랩 첫 줄 6칼럼 → 7칼럼 (`PM모드` 추가) |
| M-7 | `README.md` L728 | agents 카운트 "10종" → 13개 분류 (전문 6 + 범용 5 + GC 2) |
| M-8 | `README.md` L729 | community-skills 카운트 "31개" → "30개 / 6개 조직" |
| M-9 | `README.md` L772 | MCP 트러블슈팅 "설치 메뉴 [2]/[3]" 라인 정정 → `claude mcp list` / `opal-cli doctor` 검증 명령 안내 |
| M-10 | `README.md` L676~702 | "Agentic Mode" 섹션 → "Pilot 실행 모드 (3-way)" 섹션 본문 재작성 (3-way 비교표 + 권장 모드 표) |
| M-11 | `README.md` L778 | 신규 `## License` 섹션 — MIT 명시 + LICENSE 상대 링크 + 저작권 표기 |
| M-12 | `docs/ARCHITECTURE.md` L186 | 배포 모델 다이어그램 `opal/agents/* (10개)` → `(12개)` |
| M-13 | `docs/ARCHITECTURE.md` §컴포넌트 유형 §에이전트 | 범용 에이전트 표에 `opal-security-checker` (advanced) / `opal-convention-checker` (standard) 2행 추가 — 합계 13개 분류 정합 |

## 요구사항 매핑

| ID | 핵심 | 결과 |
|----|------|------|
| R-1 | LICENSE 신규 (SPDX MIT) | ✅ |
| R-2 | README 배지 2종 | ✅ |
| R-3 | README License 섹션 | ✅ |
| R-4 | OPAL_VERSION generic placeholder + Releases 링크 | ✅ (캡틴 통찰: 매 릴리즈 갱신 부담 회피) |
| R-5 | 부트스트랩 첫 줄 형식 정정 | ✅ |
| R-6 | agents 카운트 13개 + ARCHITECTURE.md 동기화 | ✅ (M-9 GC 체커 표 보강 포함) |
| R-7 | community-skills 카운트 정정 (30개 / 6조직) | ✅ |
| R-8 | MCP 트러블슈팅 outdated 정정 | ✅ (검증 명령 1줄 대체) |
| R-9 | 3-way 모드 체계 설명 (추가작업) | ✅ |
| R-10 | Windows Python winget 자동 설치 안내 (추가작업) | ✅ |

## QA / 게이트 결과

- **PLAN QA**: pass_with_minor (Warning C-8 — R-8 단순 삭제 vs 검증 명령 대체. 사용자 친화적 개선이라 진행)
- **EXECUTE QA**: pass_with_minor (Warning C-1 — README L728의 "전문 6 + 범용 5 + GC 2" 표기와 ARCHITECTURE.md §에이전트 표의 "범용 7행(GC 내포) + 전문 6행" 사이 분류 레이블 표현 차이. **합계 13 정합 + 기능 영향 0**)
- **PM Gate**: TASK R-1 ~ R-10 AC 모두 충족, 변경이력 면제 검증 통과, 영역 간 용어 일관성 R-T1 자체 해결(M-9)

## 알려진 미해결 / 후속 분리

| ID | 내용 | 분리 대상 |
|----|------|----------|
| Warning C-1 | ARCHITECTURE.md §에이전트 표를 "GC 체커" 별도 서브섹션으로 분리 — README L728 분류와 표현 정합 | P1 README 보강 태스크 |
| 142 | community-skills 번들 → fetch 방식 전환 (skills.sh / npx skills) — TASK.md §확정된 설계 방향 §0 | 별도 태스크 142 |
| 143~ | P1 항목 (Quick Start / mini-glossary / opal-cli 표 / 트러블슈팅 강화) | 알투의 검토 보고 P1 #8~12 |
| 별도 문서 | 상세 설치 가이드 (옵트아웃 환경변수, 트러블슈팅 알려진 패턴 등) | 캡틴 결정 — `docs/INSTALL.md` 신설 가능 |

## 검증 상태

- README grep: `semi-agentic` 5건 / `3-way` 2건 / `winget Python 3.14` 1건 / `<원하는-태그>` 2건 / `[LICENSE](LICENSE)` 1건 / "설치 메뉴" 0건 (제거 검증) — **모두 PASS**
- 실측 카운트: `find community-skills -maxdepth 3 -name SKILL.md` = 30 / 디렉토리 6 / `opal/agents/*` = 12 / `agents/*` = 1 — **모두 정합**
- mac/Windows OS 분기: 무관 (텍스트 문서 변경만)
- install / doctor / 스킬 동작: 영향 없음 (회귀 위험 0)

## STATE 최종

| Phase | 행 수 | 상태 |
|-------|------|------|
| TASK | 1~3 | ✅ (사용자 확인 owner=user) |
| PLAN | 4~11 | ✅ (사용자 확인 owner=user) |
| EXECUTE | 12~19 | ✅ (행 18 추가작업 + 행 19 사용자 확인 owner=user) |
| CLOSE | 20~21 | 진행 중 (DONE.md 생성 → State Gate) |

## 후속 액션

1. 캡틴 명시 요청 시: `git add LICENSE README.md docs/ARCHITECTURE.md` + 적절한 commit message로 commit + main push
2. 별도 태스크 142(community-skills fetch 전환) 진행
3. P1 후속 태스크(Quick Start / mini-glossary / opal-cli 표 / 트러블슈팅 강화 / Warning C-1 정리 / 상세 설치 문서)는 별도 세션에서 결정
