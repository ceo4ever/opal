# Plan-Driven 모드

> execution-plan.json의 frontend.screens 배열에서 개별 screen 객체를 입력으로 받아 구현한다.
> 기존 프로젝트 구조에 맞춰 파일을 추가하거나 수정한다.
> shadcn Critical Rules와 화면 유형별 패턴은 `SKILL.md`를 참조한다.

---

## 입력

execution-plan.json의 screen 객체 1개:

| 필드 | 설명 |
|------|------|
| `id` | 화면 식별자 (FE-1, FE-2, ...) |
| `name` | 화면명 |
| `type` | 화면 유형 (dashboard, crud, form, auth, detail, settings, report, monitor) |
| `action` | `new` (새 파일 생성) 또는 `modify` (기존 파일 수정) |
| `route` | URL 경로 |
| `files` | 대상 파일 경로 목록 |
| `shadcn_components` | 사용할 shadcn 컴포넌트 목록 |
| `ui_work` | 생성/수정할 컴포넌트 상세 |
| `ui_work.description` | UI 작업 설명 |
| `ui_work.components_to_create` | 새로 만들 컴포넌트 |
| `ui_work.components_to_modify` | 수정할 기존 컴포넌트 |
| `api_work` | API 연동 상세 |
| `api_work.endpoints` | 연동할 API 엔드포인트 |
| `api_work.description` | API 연동 설명 |

---

## 실행 프로세스

### Step 1: 프로젝트 구조 파악

1. 프로젝트 루트에서 기존 구조를 파악한다:
   - `src/` 또는 `app/` 디렉토리 구조 확인
   - 기존 컴포넌트 패턴 (파일 구조, import 스타일, 네이밍 컨벤션)
   - shadcn/ui 설치 여부 (`components.json` 존재, `components/ui/` 디렉토리)
   - 라우팅 패턴 (Next.js App Router / Pages Router / React Router 등)
2. **기존 패턴과 일관성을 유지하는 것이 최우선**
3. 프로젝트 `docs/`가 있으면 `docs/client/ARCHITECTURE.md`를 참조

### Step 2: action별 실행

#### action: new (새 화면 생성)

1. `screen.type`에 따라 SKILL.md의 "화면 유형별 구현 패턴" 참조
2. `screen.files`의 각 파일을 생성
3. `screen.shadcn_components`의 컴포넌트를 import
4. `screen.ui_work.components_to_create`를 순서대로 구현:
   - SKILL.md의 해당 화면 유형 패턴을 기반으로 코드 생성
   - 기존 프로젝트의 컴포넌트 스타일/구조와 일관성 유지
5. `screen.api_work`의 엔드포인트를 연동:
   - 기존 API 호출 패턴(fetch, axios, openapi-fetch 등) 확인 후 동일 방식 사용
   - API 응답이 아직 없으면 더미 데이터로 대체 (한국어, 현실적인 데이터)
6. 라우팅/네비게이션에 새 화면 등록 (프로젝트 패턴에 따라)

#### action: modify (기존 화면 수정)

1. `screen.files`의 각 파일을 Read하여 현재 구현 파악
2. `screen.ui_work.components_to_modify`의 변경 사항 적용:
   - 기존 코드 구조를 유지하면서 수정
   - 새 컴포넌트 추가 시 기존 import 패턴 따름
3. `screen.api_work`의 엔드포인트 연동 추가/수정 (해당 시)

### Step 3: shadcn 컴포넌트 확인

1. `screen.shadcn_components`에 명시된 컴포넌트가 프로젝트에 설치되어 있는지 확인
   - `components/ui/` 디렉토리에서 해당 컴포넌트 파일 존재 여부
2. 미설치 시:
   - `npx shadcn@latest add {component}` 실행
   - shadcn MCP 활용: `search_items_in_registries`로 컴포넌트 확인, `view_items_in_registries`로 사용법 확인
3. 설치된 컴포넌트의 실제 export를 확인하여 정확한 import 경로 사용

### Step 4: 검증

1. **shadcn Critical Rules** 준수 확인 (SKILL.md 참조):
   - FieldGroup + Field 폼 구조 (raw div 금지)
   - gap-* 레이아웃 (space-x/y 금지)
   - 시맨틱 컬러 변수 사용
   - data-icon 속성 사용
   - Items는 Group 안에 배치
   - Dialog/Sheet/Drawer Title 필수
2. **기존 프로젝트 패턴 일관성** 확인:
   - import 경로 (@/ alias 등)
   - 파일 네이밍 컨벤션
   - 컴포넌트 구조 (함수형, export 방식 등)
3. **TypeScript 타입 안전성**:
   - props 인터페이스 정의
   - API 응답 타입 정의

---

## 산출물

변경된 파일 목록을 반환한다:

```
- artifact_path: [생성/수정된 파일 경로 목록]
- summary: {화면명} {action} 완료 — {주요 변경 내용}
- status: success | blocked
- changed_files: [파일 경로 목록]
```

> scaffold 모드와 달리 별도 번들링은 하지 않는다. 기존 프로젝트의 빌드 시스템을 사용한다.
