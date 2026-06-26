# Memory & Learning (기억과 학습)

> 출처: opal/core/AGENT.md §기억과 학습
> 로드 시점: 메모리 쓰기 요청 시 / "이거 기억해줘" 발화 시 / 태스크 완료 후 기록 시
> 역할: 저장소 구조 / 저장 대상·비대상 / 갱신 트리거 / 인덱스·히스토리 형식 / 타임스탬프 규칙 / FIFO / 라이프사이클 / 이관 워크플로우

---

프로젝트 경험을 `{프로젝트}/.opal/` 하위에 축적한다:

- **저장소**: `{프로젝트}/.opal/MEMORY.md` (인덱스) + `{프로젝트}/.opal/memory/*.md` (개별 파일)
- **저장하는 것**: 프로젝트 패턴, 소유자 선호, 반복되는 이슈와 해결법, 아키텍처 결정 근거
- **저장하지 않는 것**: 일회성 작업 내용, 임시 상태, 검증되지 않은 추측
- **활용 방법**: 새 작업을 시작할 때 MEMORY.md를 읽고, 관련 메모리를 선택적으로 로드
- **소유자 요청 시**: "이거 기억해둬" → 즉시 해당 유형의 메모리 파일에 기록 (없으면 생성)
- **갱신 트리거**: 태스크 단계 전환, 태스크 완료, 아키텍처 결정, 소유자 명시 요청, 반복 이슈, 패턴 인식
- **메모리 인덱스 형식**: `| 제목 | 등록일 | 유형 | 상태 | 파일 | 요약 |`
  - `제목`: 짧은 명사구(≤30자). 스캔 1순위 키.
  - `등록일`: `YYYY-MM-DD` (KST).
  - `유형`: project / architecture / feedback / preferences / issues / task.
  - `상태`: active / promoted / superseded / dead (§메모리 라이프사이클).
  - `파일`: `memory/<name>.md` 상대경로(포인터).
  - `요약`: **≤80자, 1줄** [MUST]. 상세는 개별 `.md` 본문 전용. 인덱스는 포인터이지 본문이 아니다.
- **작업 히스토리 형식**: `| 제목 | 등록일 | 단계 | 경로 | 핵심결과 |`
  - `제목`: 태스크 명사구(맨 앞). 예: "045 메모리 관리 개선".
  - `등록일`: `YYYY-MM-DD` (TASK 시작일, KST).
  - `단계`: 진행중 `PLAN ✅ → TODO 대기` / 완료 `완료`.
  - `경로`: `tasks/<폴더>/`.
  - `핵심결과`: **≤2줄** [MUST]. 무엇을 바꿨는지 + 결과(테스트/회귀). 설계 전문·버그 서사는 금지(개별 메모리 또는 brain으로).
- **타임스탬프 취득**: 시작일시/완료일시 기록 시 `node ~/.opal/tools/date/date.js datetime` 실행 필수 (bash 생략 금지).
- **타임존**: 모든 일시는 **KST(한국 표준시, UTC+9)** 기준으로 기록한다. 시스템 시간이 UTC인 경우 소유자에게 현재 시간을 확인한다.
- **일회성 프로세스 변경**: QA 생략, 테스트 생략 등 소유자의 일회성 지시는 해당 태스크에만 적용. 다음 태스크는 기본 프로세스로 복귀
- **정리**:
  - 작업 히스토리는 **최대 5개 FIFO** [MUST] — 6번째 추가 시 가장 오래된 1개를 memory-tool이 결정론적으로 제거. 이전 히스토리는 git log + tasks/ 폴더에서 추적.
  - 메모리(지식)는 **blind 삭제 금지** [MUST] — 갯수 상한을 두지 않는 대신, 성숙한 지식은 `promote`로 영구 거처(docs/brain)로 졸업한 뒤 삭제하고, 진부화는 `dead`/`superseded` 전이 후 자가검토(`review`)로 정리한다(데이터 무손실).
- **독립 생성**: 프로젝트 에이전트 없이도 소유자 요청 시 메모리 생성 가능

---

## 마커 규약

MEMORY.md에는 아래 HTML 주석 마커가 반드시 존재해야 한다:

```
<!-- memory:index:start -->   ... 메모리 인덱스 표 ...   <!-- memory:index:end -->
<!-- memory:history:start --> ... 작업 히스토리 표 ...   <!-- memory:history:end -->
```

**[MUST] memory-tool이 이 마커로만 테이블을 변경한다 — LLM 직접 편집 금지.** 마커가 없으면 모든 변경 명령(append/update/promote/prune/migrate)이 `marker_missing` 오류로 거부된다.

---

## 메모리 라이프사이클

| 상태 | 의미 | 진입 트리거 | 도구 동작 |
|------|------|-----------|----------|
| `active` | 살아있는 지식. 인덱스에 노출·로드 대상 | 신규 등록(append) | 인덱스 행 유지 |
| `promoted` | 영구 거처(docs/brain)로 졸업 완료 | PM이 본문을 docs 규칙/brain 페이지로 이전했다고 판단 | `promote --to <docs\|brain>`: 이전 확인 후 인덱스 행 + `.md` 파일 삭제 + provenance 기록(SSOT 이중화 해소) |
| `superseded` | 더 새로운 메모리/결정이 대체 | PM이 대체 관계 식별 | `update --status superseded`: 행 보존(추적용), 로드 제외. 자가검토 `cleanup_candidates`로 표면화 후 `delete`로 제거(`--with-file`로 `.md`도 정리) |
| `dead` | 완료·진부화(task 완료, 이슈 해소) | task 완료 / 이슈 해소 / 철회 | `update --status dead`: 로드 제외. 자가검토 `cleanup_candidates`로 표면화 후 `delete`로 제거 |

> **[MUST] `delete` 무손실 가드**: `delete`는 `dead`/`superseded` 상태 행만 제거한다. `active`/`promoted` 행 삭제 시도는 `delete_requires_dead_or_superseded`로 거부 — 살아있는 지식의 blind 삭제를 차단한다. migrate가 단 crude 제목은 `update --new-title`로 보정한다.

> **갯수 상한 없음**: 본 체계는 메모리 활성 갯수 상한을 두지 않는다(캡틴 지시 2026-06-26). 비대화 방지는 **졸업(promote)·자가검토(review)·요약 길이캡**이 담당하며, promoted/superseded/dead는 로드 대상에서 제외되어 토큰을 잠식하지 않는다.

---

## 메모리 이관(졸업) 워크플로우

메모리는 **임시 보관소**다. 성숙한 지식은 영구 거처로 졸업(promote)한다.
핵심 구분: **docs = 규범(행동을 지배)**, **brain = 설명(왜·어떻게)**.

### 라우팅 표 (졸업지 결정)

| 메모리 성격 | 졸업지 | 비고 |
|------------|--------|------|
| 행동 규칙·금지·확정 기준·선호 | `docs/AGENT.md` | feedback / preferences 유형 |
| 코드·문서 컨벤션 | `docs/CONVENTIONS.md` | — |
| 프로젝트 정의·범위 | `docs/PROJECT.md` | — |
| 설계 WHY·도메인 지식·비자명 해법 | `brain` (`//opbr ingest` / `brain-tool add-page` 재사용) | architecture / issues 유형 |
| 완료·진부화·철회 | 삭제(`dead` / `superseded` → 정리) | task 유형 |

> 메모리 `유형`이 기본 졸업지 힌트다(feedback/preferences→docs/AGENT.md, architecture/issues→brain, task→삭제).
> 최종 졸업지·성숙 여부 판단은 **PM**이 한다. 도구는 후보를 표면화(자가검토)하고 이전을 집행(promote)할 뿐이다.

### 졸업 절차 (역할 분담)

1. **PM 판단**: 자가검토 `promote_candidates`를 보고 성숙 여부 + 졸업지(docs냐 brain이냐) 결정.
2. **PM authoring**: docs면 해당 문서에 규칙 반영, brain이면 `//opbr ingest` / `brain-tool add-page`로 페이지 작성(기존 brain 파이프라인 재사용 — 중복 금지).
3. **도구 집행**: 이전 완료 확인 후 `promote --to <docs|brain> --ref <위치>`로 메모리 행 + `.md` 삭제 + provenance(삭제 전 위치·대상) 기록. 이전 미확인이면 거부(무손실).

> **[MUST] `PRINCIPLES.md` §2 Simplicity**: brain 이관은 기존 `//opbr ingest` / `brain_tool.py:465 cmd_add_page`를 재사용한다 — memory-tool에 별도 brain 쓰기 파이프라인을 재발명하지 않는다.

### 자가검토 트리거

memory-tool의 모든 변경 명령(`init`/`append`/`update`/`promote`/`prune`/`migrate`/`delete`) 응답 JSON에는 `review` 블록이 자동 첨부된다 → "호출할 때마다 기존 메모리·히스토리를 검토"가 ambient하게 강제된다. 단독 `review` 명령으로도 같은 health 점검을 수행한다.

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 다운사이징 — AGENT.md §기억과학습 분리 (128) |
| v1.1 | 2026-06-26 | 045 메모리 관리 개선 — 제목 컬럼·길이캡·FIFO5·라이프사이클·이관 워크플로우 + memory-tool 집행 |
