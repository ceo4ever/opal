# OPAL 스킬 퀵 가이드

> 부트스트랩 시 소유자에게 브리핑하는 사용 가능 스킬 요약.
> 에이전트는 이 가이드를 읽고, 브리핑 하단에 스킬 테이블을 포함한다.

---

## 스킬 목록

| 구분 | 스킬명 | 명령어 (정식/약식) | 설명 | 예시 | 비고 |
|------|--------|-------------------|------|------|------|
| 개발 | otp-dev-short | otp-dev-short / otpds | 코드 변경의 기본 진입점. 분석+설계 통합 4단계 | `otpds 로그인 버그 수정해줘` | 기본 모드 |
| 개발 | otp-dev | otp-dev / otpd | 대규모 개발. ANALYSIS+TODO 포함 7단계 | `otpd 회원가입 기능 전체 개발해줘` | Full Task |
| 개발 | otp-wf | otp-wf / otpwf | 와이어프레임 설계 → UI 구현 | `otpwf 대시보드 화면 설계해줘` | |
| 분석 | api-analyzer | api-analyzer | 외부 API 7단계 분석 → 명세서 생성 | `이 API 분석해줘 {URL}` | |
| 분석 | interview | interview | 구조화된 Q&A로 요구사항 수집 | `요구사항 확인해줘` | |
| 문서 | doc-writer | doc-writer | 기술 문서 표준 템플릿 | `API 명세서 작성해줘` | |
| 문서 | version-mgr | version-mgr | 산출물 버전 태깅 (v{Major}.{Minor}) | `이 문서 버전 올려줘` | |
| UI | wireframe-builder | wireframe-builder | 정책서/요구사항 → wireframe.md 생성 | `화면 설계해줘` | |
| UI | ui-designer | ui-designer | wireframe.md → React + shadcn/ui 구현 | `UI 구현해줘` | |
| 관리 | opal-project-init | opal-project-init | 프로젝트 문서(docs/) + OPAL 에이전트 생성 | `프로젝트 셋팅해줘` | |
| 관리 | opal-skill-creator | opal-skill-creator | 새 프레임워크 스킬 생성/개선 | `새 스킬 만들어줘` | |
| 관리 | opal-skill-manager | opal-skill-manager | 커뮤니티 스킬 검색/설치/삭제 | `스킬 검색해줘` | |
| 웹 | web-to-markdown | web-to-markdown | 웹 페이지를 마크다운으로 변환 | `이 URL 마크다운으로 변환해줘` | |

**사용법**: `{명령어} {작업 설명}` 형식으로 호출. 명령어 없이 작업만 말하면 에이전트가 적절한 스킬을 제안한다.

---

## 브리핑 포함 형식

부트스트랩 브리핑 시 위 테이블을 그대로 포함한다.
