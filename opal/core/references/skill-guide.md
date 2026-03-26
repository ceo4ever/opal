# OPAL 스킬 퀵 가이드

> 부트스트랩 시 소유자에게 브리핑하는 사용 가능 스킬 요약.
> 에이전트는 이 가이드를 읽고, 브리핑 하단에 스킬 목록을 포함한다.

---

## 개발 (Development)

코드 변경이 수반되는 작업. 분석 → 설계 → 구현 → 테스트 파이프라인을 자동 수행한다.

| 스킬 | 제목 | 용도 | 사용 예시 | 약식 |
|------|------|------|----------|------|
| otp-dev-short | Short Task | 코드 변경의 기본 진입점. 분석+설계를 통합하여 빠르게 진행 | `otpds 로그인 버그 수정해줘` | `otpds` |
| otp-dev | Full Task | 대규모 개발. 별도 ANALYSIS + TODO 단계 포함 | `otpd 회원가입 기능 전체 개발해줘` | `otpd` |
| otp-wf | Wireframe UI | 와이어프레임 설계 → UI 구현 | `otpwf 대시보드 화면 설계해줘` | `otpwf` |

**사용 방법**: `{약식} {작업 설명}` 형식으로 호출. 약식 없이 작업만 말하면 에이전트가 적절한 스킬을 제안한다.

---

## 분석 (Analysis)

외부 API나 요구사항을 체계적으로 조사한다.

| 스킬 | 제목 | 용도 | 사용 예시 |
|------|------|------|----------|
| api-analyzer | API 분석기 | 외부 API 7단계 분석 → 명세서 생성 | `이 API 분석해줘 {URL}` |
| interview | 인터뷰 | 구조화된 Q&A로 요구사항 수집 | `요구사항 확인해줘` |

---

## 문서 (Documentation)

표준 형식의 기술 문서를 작성한다.

| 스킬 | 제목 | 용도 | 사용 예시 |
|------|------|------|----------|
| doc-writer | 문서 작성기 | 기술 문서 표준 템플릿 | `API 명세서 작성해줘` |
| version-mgr | 버전 관리 | 산출물 버전 태깅 (v{Major}.{Minor}) | `이 문서 버전 올려줘` |

---

## UI/UX

화면 설계와 구현을 지원한다.

| 스킬 | 제목 | 용도 | 사용 예시 |
|------|------|------|----------|
| wireframe-builder | 와이어프레임 빌더 | 정책서/요구사항 → wireframe.md 생성 | `화면 설계해줘` |
| ui-designer | UI 디자이너 | wireframe.md → React + shadcn/ui 구현 | `UI 구현해줘` |

---

## 프로젝트 관리 (OPAL)

프로젝트 초기 셋팅과 스킬 관리를 수행한다.

| 스킬 | 제목 | 용도 | 사용 예시 |
|------|------|------|----------|
| opal-project-init | 프로젝트 초기화 | 프로젝트 문서(docs/) + OPAL 에이전트 생성 | `프로젝트 셋팅해줘` |
| opal-skill-creator | 스킬 생성기 | 새 프레임워크 스킬 생성/개선 | `새 스킬 만들어줘` |
| opal-skill-manager | 스킬 매니저 | 커뮤니티 스킬 검색/설치/삭제 | `스킬 검색해줘` |

---

## 웹 도구 (Web)

| 스킬 | 제목 | 용도 | 사용 예시 |
|------|------|------|----------|
| web-to-markdown | 웹→마크다운 | 웹 페이지를 마크다운으로 변환 | `이 URL 마크다운으로 변환해줘` |

---

## 브리핑 포함 형식

부트스트랩 브리핑 시 아래 형식으로 스킬 목록을 포함한다:

```
📌 스킬 가이드

개발:  otpds (기본) | otpd (Full) | otpwf (와이어프레임)
분석:  api-analyzer | interview
문서:  doc-writer | version-mgr
UI:    wireframe-builder | ui-designer
관리:  opal-project-init | opal-skill-creator | opal-skill-manager
웹:    web-to-markdown

사용법: {스킬명 또는 약식} {작업 설명} (예: otpds 로그인 버그 수정해줘)
```
