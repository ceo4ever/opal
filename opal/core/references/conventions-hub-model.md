# 컨벤션·보안 허브+링크 모델

> OPAL 체커 에이전트(opal-convention-checker / opal-security-checker)의 참조 문서 체이닝 규약.
> Lazy 트리거: 체커가 프로젝트 `docs/CONVENTIONS.md` 또는 `docs/SECURITY.md`를 Read할 때.
> 선택 모델 — 기존 프로젝트에 적용 강제하지 않는다. OPAL 자체는 단일 문서 모델을 유지한다.
> 탐색 경로: `opal/core/references/conventions-hub-model.md`

---

## 1. 개념

`docs/CONVENTIONS.md` / `docs/SECURITY.md`를 **허브(hub) 문서**로 유지하고, 영역(FE/BE/Batch/Mobile)별 상세 규칙은 별도 파일로 분리하여 허브에서 **링크**로 연결한다. 체커는 scope 파라미터를 받아 허브와 해당 영역 상세 문서만 병합 로드한다.

## 2. 허브 문서의 역할

- **단일 진입점**: 체커는 항상 허브를 먼저 Read한다. 허브 미존재 시 체크 비활성화(초안 유도).
- **영역별 공통 원칙만 기술**: 언어 규칙, 네이밍 대원칙, 문서 규칙, 커밋 규칙 등 전 영역 공통.
- **영역별 상세는 외부화**: React 컴포넌트 규칙, FastAPI 라우팅 규칙, Batch 스케줄러 규칙 등은 `FE-CONVENTIONS.md`, `BE-CONVENTIONS.md`, `BATCH.md` 등으로 분리.
- **링크 레지스트리**: 허브 상단(또는 전용 섹션)에 영역별 상세 문서를 링크 목록으로 유지.

> "CONVENTIONS.md 유일 기준" 원칙은 허브가 유일 진입점이 됨으로써 유지된다. 체커가 자체 규칙을 만들거나 허브를 우회하는 것은 여전히 금지다.

## 3. 링크 규약

허브 문서 상단에 전용 섹션을 두고 아래 포맷으로 영역별 상세 링크를 배치한다:

```markdown
> 영역별 상세:
> - [FE-CONVENTIONS.md](./FE-CONVENTIONS.md) — Frontend
> - [BE-CONVENTIONS.md](./BE-CONVENTIONS.md) — Backend
> - [BATCH.md](./BATCH.md) — Batch (Backend 상속)
```

- **경로**: `./{파일명}.md` (허브와 같은 `docs/` 디렉토리 기준)
- **라벨**: `— {영역명}` (Frontend / Backend / Batch / Mobile / 기타)
- **상속 표기**: `(Backend 상속)` 등 상위 영역을 괄호로 명시
- **정규식 파싱용**: `\[([\w-]+\.md)\]\(\.?/([^)]+)\)` — 체커가 파싱 시 사용

## 4. 체커 참조 체이닝 흐름

체커는 scope 입력에 따라 아래 4단계로 문서를 로드한다:

1. **허브 Read** — `docs/CONVENTIONS.md`(컨벤션 체커) 또는 `docs/SECURITY.md`(보안 체커). 부재 시 `check_enabled = false` 처리 + 초안 유도.
2. **링크 파싱** — 허브 본문에서 §3 링크 규약 정규식으로 `[파일, 영역]` 매핑 추출.
3. **scope 매칭** — 입력 `scope`(frontend/backend/batch/mobile/all)와 매칭되는 상세 문서 선택. `scope` 미지정 또는 `all` 시 허브 전체만 적용(하위호환).
4. **상세 문서 Read + 병합** — 선택된 상세 문서를 Read하여 허브의 공통 원칙과 병합한 뒤 체크를 수행.

> 이 흐름은 `check_enabled` 판정과 공존한다. 허브가 존재하면 `check_enabled = true`가 되고, 상세 문서가 없어도 허브 전체로 체크가 정상 수행된다.

## 5. 예시 블록

### 예시 A — 풀스택 프로젝트 (FE + BE)

**허브 (`docs/CONVENTIONS.md`)**:

```markdown
# 코드 컨벤션

> 영역별 상세:
> - [FE-CONVENTIONS.md](./FE-CONVENTIONS.md) — Frontend
> - [BE-CONVENTIONS.md](./BE-CONVENTIONS.md) — Backend

## 언어 규칙
| 대상 | 규칙 |
...
```

**상세 (`docs/FE-CONVENTIONS.md`)**:

```markdown
# Frontend 컨벤션

- React 컴포넌트 네이밍: PascalCase
- 상태 관리: Zustand 우선
...
```

**호출 시나리오** (scope="frontend"):

```
1. 체커가 docs/CONVENTIONS.md Read (허브)
2. 링크 파싱 → [(FE-CONVENTIONS.md, Frontend), (BE-CONVENTIONS.md, Backend)]
3. scope="frontend" 매칭 → docs/FE-CONVENTIONS.md 선택
4. docs/FE-CONVENTIONS.md Read → 허브 공통 원칙 + FE 상세 병합 → 체크 수행
```

### 예시 B — 단일 문서 프로젝트 (OPAL 자체 포함)

```
1. 체커가 docs/CONVENTIONS.md Read (허브 = 단일 문서)
2. 링크 파싱 → [] (상세 링크 없음)
3. scope="all" 또는 미지정 → 허브 전체만 적용
4. 허브 Read만으로 체크 수행 (기존 동작과 동일, 하위호환)
```

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-04-17 | 초기 작성 — 허브+링크 모델, 링크 규약, 체커 참조 체이닝 흐름, 예시 블록 2종 (125) |
