# EXECUTE @header 규칙

> 출처: opal-harness.md §8
> 로드 시점: EXECUTE 단계에서 코드 파일 생성/수정 시
> 역할: @header 작성 규칙 + code-scan 활용 가이드

---

## 8. EXECUTE @header 규칙

> **트리거**: 코드 파일 생성/수정 시. code-scan 지원 확장자 파일에만 적용.
> **작성 주체**: 워커(LLM)가 직접 작성. 별도 도구 없음.

### 적용 대상 확장자

code-scan.js 기본 지원 확장자와 동일하다:

```
.py  .js  .ts  .jsx  .tsx  .vue  .svelte  .kt  .kts  .java  .swift
```

위 확장자 외 파일(예: `.json`, `.yaml`, `.md`, `.sh`)은 @header 작성 대상이 아니다.
단, 프로젝트 `.opal/code-scan.json`에 `.md`가 추가된 경우 md 파일도 적용 대상이 된다.

### 파일 생성 시

@header가 없는 신규 파일을 생성할 때, 워커는 언어에 맞는 주석 문법으로 @header를 파일 최상단에 작성한다.

- 포맷 표준: `~/.opal/references/header-standard.md` 참조
- 필수 필드: `module`, `layer`, `domain`, `description`, `exports`
- 선택 필드: `depends` (외부 의존 있을 때), `note` (특이사항 있을 때)

#### 테스트 파일 전용 선택 필드 (`layer: test`)

테스트 파일(`layer: test`)은 아래 선택 필드를 추가로 작성한다:

| 필드 | 타입 | 설명 | 예시 |
|------|------|------|------|
| `task` | string | 이 테스트가 처음 작성된 태스크 번호 | `"016"` |
| `scenarios` | list | 연결된 TEST-SCENARIO.md S-ID 목록 | `["S-1", "S-2", "S-7"]` |

### 파일 수정 시

기존 파일에 @header가 있으면, 변경된 내용에 따라 해당 필드만 갱신한다.

| 변경 내용 | 갱신 대상 필드 |
|----------|-------------|
| 함수/엔드포인트 추가 | `exports` |
| 파일 역할 변경 | `description` |
| 새 의존 모듈 추가 | `depends` |
| 레이어/도메인 이동 | `layer`, `domain` |

기존 파일에 @header가 없으면, 파일 생성 규칙과 동일하게 신규 작성한다.

### 주석 문법

언어별 주석 포맷은 `~/.opal/references/header-standard.md` §3을 따른다.

---

### code-scan 활용 가이드

PM·오케스트레이터·에이전트(비서)는 code-scan을 통해 프로젝트 구조를 파악한 뒤 필요한 파일만 선택적으로 Read한다.

#### 활용 시점

| 역할 | 활용 시점 | 권장 커맨드 |
|------|---------|-----------|
| 에이전트(비서) | 구조 파악 요청 / 파일 탐색 / 소유자 질문 응답 | `scan`, `domain`, `layer`, `search`, `exports` |
| PM(오케스트레이터) | TASK/PLAN 수립 전 도메인 파악, 디스패치 전 범위 확인 | `scan`, `domain`, `depends` |
| PM Gate | EXECUTE 완료 후 @header 검증 | `scan <file> --json` |

#### 활용 절차

1. `.opal/code-scan.json` 존재 여부 확인 → 없으면 PM이 자동 생성 (`code-scan-management.md §생성 시점` 참조) 후 진행
2. `code-scan scan <scope>` 로 전체 개요 파악
3. 필요 시 `code-scan domain <name>` / `code-scan layer <name>` 으로 범위 좁히기
4. 특정 기능 탐색: `code-scan exports <pattern>` (exports 필드 전용, 정규식 지원) 또는 `code-scan search <pattern>` (전체 필드, 정규식 지원)
5. 식별된 파일만 선택적으로 Read

#### 빈 결과 폴백

code-scan 결과가 충분하지 않을 때 아래 3분기 기준으로 대응한다.

| 분기 | 조건 | 대응 |
|------|------|------|
| ① 매칭 0건 | `search`/`exports` 결과 0건 | Glob/Grep **보강** (code-scan 결과 + 추가 탐색 병행) |
| ② 저커버리지 | `scan`/`domain`/`layer` @header 커버리지 30% 미만 | code-scan **+ Glob/Grep 동시** 활용 |
| ③ 정상 | 그 외 | code-scan 결과만 사용 |

**STATE 기록 규약**: 폴백(①②) 발동 시 STATE.md **자유 텍스트 영역**(블로커/다음 액션 — **현황판 표 행 아님, state-tool 비경유**)에 `code-scan 폴백: {사유}` 1줄을 기록한다.

[MUST] TASK §제약: "STATE.md 폴백 기록은 자유 텍스트 영역만 사용, 현황판 행 직접 편집 금지."

#### 적용 조건

`.opal/code-scan.json`이 존재하지 않으면 PM이 `code-scan-management.md §생성 시점`에 따라 즉석 자동 생성한 뒤 활용한다 — 미생성 상태로 직행 Glob/Grep 사용 금지. 이 파일은 PM이 디스패치 전 Read할 수 있는 경로: `opal/core/references/harness/header-rules.md`.

---

변경이력:

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-09 18:30 | 개인 식별자 누설 정정 — "알투(비서)" → "에이전트(비서)" 치환 (139) |
| v1.1 | 2026-06-10 10:13 | 테스트 파일 선택 필드 task/scenarios 정의 추가 (016) |
| v1.2 | 2026-06-11 22:36 | §code-scan 활용 가이드 — 빈 결과 폴백 3분기 표 신설 + STATE 자유 텍스트 기록 규약 + §적용 조건 자동 생성 정합 (010) |
