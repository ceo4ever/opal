# TASK: OPAL JSON 레지스트리 + 파싱 도구 개발

> 작성일: 2026-03-29 | 작업 유형: 신규
> 입력: 사용자 요청
> 출력: TASK.md

## 작업 목표

현재 마크다운 기반의 스킬 레지스트리(skills.md, skill-guide.md)를 JSON으로 전환하고, Node.js 파싱 도구를 `opal/tools/`에 개발하여 트리거 매칭(정규식), 스킬 조회, 검증을 프로그래밍적으로 처리한다.

## 배경

현재 스킬 트리거 매칭은 LLM이 마크다운 테이블을 "읽고 해석"하는 방식:
- `//otpd` → LLM이 skills.md 테이블에서 "otpd" 문자열을 눈으로 찾음
- 부정확: LLM이 매칭을 실패하거나, 유사한 트리거를 혼동할 수 있음
- 확장 어려움: 스킬이 늘어날수록 테이블이 길어지고 컨텍스트 소모 증가

JSON + 정규식으로 전환하면:
- 코드가 파싱하므로 **100% 정확한 매칭**
- 정규식으로 **유연한 트리거 패턴** (자연어 포함)
- 스킬 메타데이터를 **구조화된 데이터**로 활용 가능

## 설계 원칙: 코드로 확실히 나아지는 것만

전부 JSON으로 옮기지 않는다. **코드 처리가 LLM 해석보다 확실히 나은 영역만** 적용한다.

| 영역 | JSON 적용 | 이유 |
|------|----------|------|
| 트리거 매칭 | ✅ | 정규식 = 100% 정확, LLM 추론 제거 |
| 스킬 경로 조회 | ✅ | 즉시 반환, 탐색 경로 우선순위 자동 처리 |
| 도메인 감지 | ✅ | 결정론적 필드 조회 |
| 스킬 존재 검증 | ✅ | 코드 신뢰 |
| 기술 스택별 추천 | ❌ 마크다운 유지 | LLM 맥락 판단 필요 |
| 커뮤니티 스킬 설명 | ❌ 마크다운 유지 | 사람이 읽는 문서 |
| 브리핑 텍스트 | ❌ 마크다운 유지 | 사용자에게 보여주는 포맷 |

## 요구사항

### JSON 레지스트리 (`opal/tools/opal-skills-registry.json`)

- [ ] 프레임워크 스킬 + OPAL 전용 스킬의 **트리거/경로/도메인** 정보만 JSON화
- [ ] 각 스킬에 정규식 기반 트리거 패턴 (`triggers[]`)
- [ ] 스킬 유형 (`type`: otp / dtp / opal / community)
- [ ] 도메인 프로파일 (`domain`: dev / write / wf / write-tech / skill / 없음)
- [ ] 탐색 경로 (`paths[]`: 우선순위 순서)
- [ ] 약어 (`alias`: otpd, otpds 등)
- [ ] 커뮤니티 스킬은 포함하지 않음 (기존 마크다운 유지)

### Node.js 파싱 도구 (`opal/tools/skill-registry.js`)

- [ ] `match(input)` — 사용자 입력에서 `//` 위치 무관하게 약어 추출 + 정규식 트리거 매칭
- [ ] `get(name)` — 스킬명으로 메타데이터 반환
- [ ] `list(filter?)` — 유형별/도메인별 필터링
- [ ] `validate()` — 스킬 경로 존재 확인, JSON 구조 검증
- [ ] CLI 실행: `node opal/tools/skill-registry.js match "로그인 개발해줘"`
- [ ] CLI 실행: `node opal/tools/skill-registry.js list --type=otp`
- [ ] CLI 실행: `node opal/tools/skill-registry.js validate`

### 환경 체크 (`opal/tools/check-env.js`)

- [ ] Node.js 설치 여부 + 버전 확인
- [ ] install-mac.sh에서 호출하여 사전 검증

### 기존 마크다운과의 관계

- [ ] skills.md는 **유지** — 기술 스택별 추천, 커뮤니티 스킬 등 LLM이 읽어야 하는 부분
- [ ] skill-guide.md는 **유지** — 부트스트랩 브리핑용
- [ ] JSON은 **트리거 매칭/경로 조회** 전용 SSOT
- [ ] 새 스킬 추가 시: JSON에 등록 + skills.md에도 등록 (이중 관리, 향후 자동화 검토)

## 제약 조건

- `opal/tools/` 디렉토리에 배치
- Node.js 내장 모듈만 사용 (외부 패키지 없음)
- JSON 스키마는 향후 opal-harness.json 등으로 확장 가능하게 설계
- install-mac.sh에서 node 존재 체크 추가

## 기술 스택

- Node.js (내장 모듈 우선)
- JSON Schema

## 관련 문서

- [opal/core/references/skills.md](opal/core/references/skills.md) — 현재 스킬 레지스트리 (전환 대상)
- [opal/core/references/skill-guide.md](opal/core/references/skill-guide.md) — 현재 스킬 가이드 (전환 대상)
- [.opal/memory/project_json_tooling.md](.opal/memory/project_json_tooling.md) — 프로젝트 메모리
