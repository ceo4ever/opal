# stockctl

> 창고 재고를 JSON 파일로 관리하는 명령행 도구

## 프로젝트 개요

| 항목 | 값 |
|------|-----|
| 프로젝트명 | stockctl |
| 도메인 | 재고 관리 CLI |

## 프로젝트 구성

| 요소 | 경로 | 기술 스택 | 전문 에이전트 |
|------|------|-----------|--------------|
| CLI | `stockctl/`, `tests/` | Python 3 표준 라이브러리, pytest | opal-be-agent |

## 프로젝트 문서

| 문서 | 설명 | 용도 | 적용 범위 | 참조 시점 |
|------|------|------|----------|----------|
| `.opal/AGENT.md` | PM 프로필 | PM 역할 및 검토 기준 | CLI | `pm.activate` 이벤트 |
| `docs/PROJECT.md` | 프로젝트 정의·문서 레지스트리 | 문서 선별 기준 | CLI | `pm.activate` 이벤트 |
| `docs/CONVENTIONS.md` | 코드 컨벤션 | 구현 규칙 | CLI | 구현·검토 시 |
| `docs/CLI.md` | CLI 명령 계약 | 명령·옵션·종료 코드·출력 형식 | CLI | CLI 동작 변경 시 |
