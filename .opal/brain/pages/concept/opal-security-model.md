---
type: concept
title: OPAL 보안 모델
tags:
- security
- install
- mcp
- supply-chain
- owasp
sources:
- doc:docs/SECURITY.md
related: []
created: '2026-06-11'
updated: '2026-06-11'
status: draft
---
## 개념 요약

OPAL 프레임워크의 보안 baseline — `opal-pilot-gc` 비교 기준선 + 사용자 신뢰 모델 SSOT (v0.4.x+, 적용 기준: OWASP Top 10 / CWE Top 25).

## 핵심 결정

- **install 무결성**: curl|bash 설치 시 SHA-256 검증. sha256sums.txt 부재 + 비대화형이면 기본 거부; `OPAL_ALLOW_UNVERIFIED=1` 옵트인으로만 우회.
- **MCP 등록 신뢰 경계**: command 필드는 `npx/npm/node/python3/python` 화이트리스트만 허용. fork repo install 시 경고 banner + 동의 확인.
- **third-party 스킬 fetch**: registry v2.1 `commit_sha` 고정 + `license: Unknown` 시 이중 확인. MCP 버전 마이너 핀 의무.
- **ReDoS/Path Traversal 방어**: `skill-registry.js`의 패턴 길이/dotstar 횟수 임계값 + `path.resolve()` 정규화.

## 적용 범위

`scripts/install*.sh`, `opal/tools/opal-cli/`, `opal/tools/skill-registry/skill-registry.js`, MCP 등록 로직.

## 관련

- [[skill-opal-pilot-gc]] — 이 문서를 보안 비교 기준선으로 참조하는 GC 진단 오케스트레이터
- [[opal-conventions]] — 보안 모델과 함께 컨벤션 체크의 기준이 되는 컨벤션 문서
- [[opal-project-definition]] — 보안 모델이 적용 범위를 정의하는 프레임워크 전체 정의

## 참조

`file_path: docs/SECURITY.md`
