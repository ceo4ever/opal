@header {
  "module": "todo-web-project",
  "layer": "project-doc",
  "domain": "todo-web",
  "description": "todo-web 기반 저장소의 프로젝트 개요, 구조, 문서 레지스트리를 정의한다.",
  "exports": []
}

# todo-web

> OPAL Pilot 기능 시나리오에서 사용하는 작은 Python 표준 라이브러리 TODO 웹 앱이다.

## 프로젝트 개요

| 항목 | 값 |
|------|-------|
| 프로젝트 | todo-web |
| 도메인 | TODO CRUD 웹 애플리케이션 |

## 프로젝트 구조

| 요소 | 경로 | 기술 스택 | 에이전트 |
|---------|------|-------|-------|
| 웹 앱 | `todo_web/`, `tests/` | Python 3 표준 라이브러리, pytest | opal-be-agent |

## 프로젝트 문서

| 문서 | 용도 | 적용 범위 | 참조 시점 |
|----------|---------|-------|-----------|
| `.opal/AGENT.md` | PM 역할과 검토 기준 | 웹 앱 | `pm.activate` |
| `docs/PROJECT.md` | 프로젝트 정의와 문서 레지스트리 | 웹 앱 | `pm.activate` |
