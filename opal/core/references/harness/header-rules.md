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

PM·오케스트레이터·알투(비서)는 code-scan을 통해 프로젝트 구조를 파악한 뒤 필요한 파일만 선택적으로 Read한다.

#### 활용 시점

| 역할 | 활용 시점 | 권장 커맨드 |
|------|---------|-----------|
| 알투(비서) | 구조 파악 요청 / 파일 탐색 / 소유자 질문 응답 | `scan`, `domain`, `layer`, `search`, `exports` |
| PM(오케스트레이터) | TASK/PLAN 수립 전 도메인 파악, 디스패치 전 범위 확인 | `scan`, `domain`, `depends` |
| PM Gate | EXECUTE 완료 후 @header 검증 | `scan <file> --json` |

#### 활용 절차

1. `.opal/code-scan.json` 존재 여부 확인 → 없으면 PM이 생성 (`opal-pm.md §9` 참조)
2. `code-scan scan <scope>` 로 전체 개요 파악
3. 필요 시 `code-scan domain <name>` / `code-scan layer <name>` 으로 범위 좁히기
4. 특정 기능 탐색: `code-scan exports <keyword>` (exports 필드 전용) 또는 `code-scan search <keyword>` (전체 필드)
5. 식별된 파일만 선택적으로 Read

#### 적용 조건

`.opal/code-scan.json`이 존재하는 프로젝트에서만 활용한다. 없으면 일반 파일 탐색(Glob/Grep)을 사용한다.
