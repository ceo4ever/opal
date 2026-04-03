# TASK: storelink.io 웹 페이지 마크다운 변환

> 작성일: 2026-04-03 | 작업 유형: 분석/수집 | 적용 스킬: opp | 모드: interactive
> 입력: https://www.storelink.io
> 출력: references/www-storelink-io.md

## 작업 목표

`https://www.storelink.io` 웹 페이지를 마크다운으로 변환하여 저장한다.

## 배경

wtm 스킬을 사용하여 storelink.io 사이트 콘텐츠를 정제된 마크다운으로 추출한다.

## 요구사항

- [ ] `https://www.storelink.io` 페이지를 마크다운으로 변환
- [ ] `tasks/078-opp-storelink-wtm/references/www-storelink-io.md`에 저장

## 제약 조건

- full 모드 (기본) — 사이트 전체 구조 보존
- Phase 1(WebFetch) 실패 시 Phase 2(Playwright MCP)로 폴백

## 기술 스택

- wtm (web-to-markdown) 스킬
