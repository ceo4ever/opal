# Wireframe UI TASK 단계 가이드

## 목적

오케스트레이터가 직접 수행하는 Wireframe UI TASK 단계 가이드.
개발 태스크의 TASK.md 작성과 달리, UI 구현의 목표/환경/입력물을 분류한다.

---

## 프로세스

### 1단계: 목표 확인

사용자의 요청에서 아래 정보를 파악한다:

- **구현할 화면 목록**: 어떤 페이지/모듈을 만들 것인지
- **기술 환경**:
  - React 프레임워크 및 버전 (Next.js, Vite, CRA 등)
  - shadcn/ui 설치 여부
  - Tailwind CSS 설정 여부
  - 기존 프로젝트의 컴포넌트 패턴
- **출력 모드**: 프로토타입(bundle.html) vs 프로덕션(Next.js 프로젝트)
  - 사용자가 명시하지 않으면 **프로토타입**이 기본값

### 2단계: 입력물 분류 및 경로 결정

사용자가 제공한 입력물을 분류하고, 다음 단계 경로를 결정한다:

| 입력물 상태 | 판별 방법 | 다음 단계 |
|------------|----------|----------|
| wireframe.md 이미 존재 | 파일 존재 확인 (Read) | WIREFRAME 스킵 → **EXECUTE** |
| 정책서/요구사항 문서 | .md, .txt, .pdf 파일 | **WIREFRAME** (wireframe-builder 호출) |
| Word 문서 | .docx 파일 | **WIREFRAME** (docx 스킬 → wireframe-builder) |
| 이미지 (스케치/스크린샷) | .png, .jpg 파일 | **WIREFRAME** (wireframe-builder 호출) |
| 구두 요청만 | 파일 없음 | **interview** → **WIREFRAME** |
| 혼합 (문서 + 이미지 + 설명) | 복수 입력물 | **WIREFRAME** (wireframe-builder가 통합 처리) |

**interview 스킬 호출 조건**:
구두 요청만 있는 경우, wireframe-builder의 최소 입력 요건을 충족하는지 확인한다:
- 서비스 목적 (무엇을 하는 서비스인지)
- 주요 기능 또는 관리 대상 엔티티 1개 이상
- 대상 사용자 또는 역할

3가지 중 하나라도 불명확하면 interview 스킬로 보강한다.

### 3단계: TASK.md 작성

아래 템플릿으로 TASK.md를 작성한다:

```markdown
# TASK: {화면명} UI 구현

> 작성일: YYYY-MM-DD | 작업 유형: Wireframe UI

## 구현 목표
{구현할 화면 목록}

## 기술 환경
- 프레임워크: {React/Next.js 버전}
- shadcn/ui: {설치됨/미설치}
- Tailwind CSS: {설치됨/미설치}
- 출력 모드: {프로토타입/프로덕션}
- 기존 컴포넌트: {재활용 가능한 컴포넌트 목록, 또는 "없음"}

## 입력물
- {입력물 유형}: {경로 또는 설명}

## wireframe.md 경로
- {기존 wireframe.md 경로, 또는 "생성 필요"}

## 스코프
- 구현 디렉토리: {prototype/ 또는 app/(wireframe)/ 등}
- 본 프로젝트 통합 전략: {프로토타입 검증 후 이관 / 직접 프로덕션 구현}

## 제약 조건
{기술적/디자인 제약사항}

## 관련 문서
{참조할 기존 산출물 경로}
```

### 4단계: 보고 및 승인 요청

TASK.md 작성 완료 후 사용자에게 보고한다:

```
📋 [TASK] Wireframe UI 완료 보고

📎 산출물: tasks/{NNN}-{태스크명}/TASK.md

입력물 분류: {wireframe.md 존재 / 정책서에서 생성 / interview 필요}
출력 모드: {프로토타입 / 프로덕션}
다음 단계: {WIREFRAME / EXECUTE (wireframe.md가 있을 시)}

진행할까요?
```

사용자 응답에 따라:
- 승인 → 다음 단계 진행
- 피드백 → TASK.md 수정 후 재보고
- 출력 모드 변경 → TASK.md 갱신

---

## 주의사항

- wireframe.md 존재 여부를 반드시 확인한다. 존재하면 WIREFRAME 단계를 스킵하여 불필요한 재생성을 방지한다.
- 프로토타입과 프로덕션 모드의 차이를 사용자에게 명확히 설명한다:
  - 프로토타입: 단일 bundle.html, 빠른 시각 확인용
  - 프로덕션: Next.js 프로젝트 구조, 실서비스 배포용
- 기존 프로젝트에 컴포넌트가 있다면 반드시 파악하여 재활용 가능성을 검토한다.
