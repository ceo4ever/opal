---
name: JSON 기반 하네스/레지스트리 도구화 계획
description: opal-harness + skills-registry를 JSON화하고 Node.js MCP 서버로 파싱/트리거 매칭/검증 도구 개발 예정 (041)
type: project
---

## 계획

040(마크다운 기반 opal-harness.md)이 완료되면, 검증된 구조를 JSON으로 전환하고 Node.js 도구를 개발한다.

**Why:** 캡틴이 JSON 파싱 도구를 여러 곳에서 활용 필요. 스킬 트리거를 정규식으로 정확하게 매칭하고 싶음. 마크다운은 LLM이 "해석"하지만 JSON은 코드가 "파싱"하므로 신뢰도가 높음.

**How to apply:**
- 041 태스크로 설계
- opal-harness.json (pipeline, gates, guards, state)
- opal-skills-registry.json (스킬 목록 + 정규식 트리거 + 도메인 프로파일)
- Node.js MCP 서버로 구현 (Claude Code/Cursor/Gemini 공용)
- 기능: 트리거 매칭, 도메인 감지, Pipeline 조회, STATE.md 생성/파싱, 구조화된 데이터 검증
