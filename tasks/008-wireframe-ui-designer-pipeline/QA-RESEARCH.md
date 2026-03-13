# QA: RESEARCH — wireframe-builder 개선 및 ui-designer 스킬 신규 개발

> 검토일: 2026-03-13 | 판정: ⚠️ Needs Revision

## 1. 요약

RESEARCH 산출물은 wireframe-builder를 HTML 생성 도구에서 wireframe.md 설계 도구로 전환하고, ui-designer 스킬을 신규 개발하는 파이프라인 구축에 대한 분석을 수행했다. 기존 wireframe-builder의 코드 구조, 프레임워크 스킬 공통 패턴, shadcn/ui 컴포넌트 체계를 분석하고, wireframe.md 스키마를 구체적으로 설계했다. 변경 파일 목록과 영향 범위, 리스크도 식별했으나, 일부 파일 경로 오류와 누락 항목이 존재한다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | TASK 커버리지 | 🟡 | TASK의 대부분 요구사항을 커버하나, Next.js 프로젝트 모드에 대한 분석이 얕음 (아래 지적 사항 참조) |
| R-2 | 코드 실독 여부 | ✅ | wireframe-builder SKILL.md의 구체적 구현 패턴(showPage, 그레이스케일 등)을 정확히 파악. shadcn 스킬의 컴포넌트/규칙도 분석됨 |
| R-3 | 변경 파일 완전성 | 🟡 | `install-mac.sh`의 스킬 개수 하드코딩("스킬 (6개)")이 7개로 변경 필요한 점 누락. 경로 오류도 존재 (아래 참조) |
| R-4 | 영향 범위 분석 | ✅ | 직접/간접 영향이 적절히 식별됨. install-mac.sh 자동 포함 판단, shadcn 스킬 참조만 등 정확 |
| R-5 | 리스크 식별 | ✅ | 스키마 동기화, HTML 인터랙션 한계, shadcn 업데이트 불일치, 대규모 서비스 대응 등 4개 리스크 식별 |
| R-6 | 분석 깊이 적정성 | ✅ | 신규 개발에 맞는 심층 분석 수행. wireframe.md 스키마 설계, shadcn 매핑 테이블, 기술 대안 비교 등 충분한 깊이 |

## 3. 지적 사항

### 심각도 분류

#### 🟡 Warning

**W-1. install-mac.sh 스킬 개수 하드코딩 미반영**
- `scripts/install-mac.sh` 234, 243, 252행에 `"스킬 (6개)"`가 하드코딩되어 있음
- ui-designer 추가 시 7개로 변경 필요하나, RESEARCH에서는 "변경 불필요"로 판단
- 간접 영향 테이블에서 `install-mac.sh`는 디렉토리 복사 로직은 변경 불필요가 맞으나, 표시 문자열 수정은 필요

**W-2. Next.js 프로젝트 모드 분석 부족**
- TASK.md 요구사항에 "Next.js 프로젝트 모드: shadcn 스킬과 연계하여 실제 프로젝트 파일 생성 (선택적 확장)"이 명시됨
- RESEARCH에서는 단일 HTML 모드에 대한 기술 조사는 상세하나, Next.js 모드의 구현 방식(shadcn 스킬 호출 방법, 파일 구조, 연계 인터페이스)에 대한 분석이 없음
- "선택적 확장"이라 하더라도 PLAN 수립을 위한 최소한의 아키텍처 방향은 RESEARCH에서 다뤄야 함

**W-3. 파일 경로에 `~` 사용**
- RESEARCH 전반에서 `~/.opal/references/skills.md`, `~/.opal/community-skills/...` 등 `~` 경로를 사용
- 프레임워크 내 소스 파일과 배포 경로가 혼재되어 있어, 어떤 것이 이 저장소 내 수정이고 어떤 것이 배포 경로인지 구분이 모호
- 소스 저장소 기준 경로와 배포 경로를 명확히 구분해서 기술하는 것이 PLAN 단계에서의 혼란을 방지

#### 🔵 Info

**I-1. 화면 유형에 `wizard` / `kanban` 유형 미포함**
- 현재 8개 화면 유형(dashboard, crud, detail, form, settings, report, auth, monitor)이 정의됨
- 위자드(단계별 폼), 칸반보드 등 일반적인 UI 패턴이 포함되지 않음
- 현재 범위에서는 충분하나, 확장성 측면에서 향후 추가 가능함을 언급하면 좋음

**I-2. wireframe.md 스키마에 반응형/모바일 고려 없음**
- TASK.md에 명시된 제약은 없으나, 실제 프로덕션 UI(Next.js 모드)에서는 반응형이 필요할 수 있음
- 스키마에 breakpoint 관련 필드를 예약해두는 것도 고려 가능

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md 요구사항 → RESEARCH 관련 파일 목록 | TASK의 모든 변경 대상이 RESEARCH에 포함되는가 | ✅ skills.md, CLAUDE.md, wireframe-builder, ui-designer 모두 포함 |
| TASK.md 성공 기준 → RESEARCH 분석 내용 | E2E 파이프라인 분석이 충분한가 | ✅ wireframe.md 스키마로 두 스킬 간 계약 정의 |
| TASK.md 제약 조건 → RESEARCH 설계 | 프레임워크 구조, shadcn 규칙, install 호환 검증 | 🟡 install-mac.sh 스킬 개수 하드코딩 미반영 |
| TASK.md ui-designer 요구사항 → RESEARCH 기술 조사 | 단일 HTML + Next.js 모드 모두 분석했는가 | 🟡 Next.js 모드 분석 부족 |

## 5. 판정

**⚠️ Needs Revision**

Warning 3개(W-1, W-2, W-3)가 식별되어 Needs Revision으로 판정한다.

**필수 수정 사항:**
1. **W-1**: install-mac.sh의 스킬 개수 표시 문자열 변경 필요성을 변경 파일 목록 또는 간접 영향에 추가
2. **W-2**: Next.js 프로젝트 모드에 대한 최소한의 아키텍처 방향 분석 추가 (shadcn 스킬 연계 방식, 예상 파일 구조 등)
3. **W-3**: 소스 저장소 내 경로와 배포 경로(`~/.opal/...`)를 구분하여 기술, 또는 RESEARCH 내에서 경로 기준을 명시

수정 후 재검토하면 Pass 판정이 가능할 것으로 보인다.
