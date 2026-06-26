# ANALYSIS: 메모리 관리 체계 개선 + memory-tool 신설

> 단계: ANALYSIS | 태스크: 045 | 작성: PM(워커 반환 내용을 spot-check 검증 후 확정)
> 입력: TASK.md | 출력: ANALYSIS.md

## §0. 참조 문서

| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 설계 | memory-learning.md (SSOT) | `opal/core/references/harness/memory-learning.md` | 개정 대상 |
| D-3 | 소스 | state-tool | `opal/tools/state-tool/` | memory-tool 구현 패턴 |
| D-4 | 소스 | tool-scan (044) | `opal/tools/tool-scan/` | 신규 도구 선례 |
| D-5 | 설계 | opal-harness.md §9 | `opal/core/references/opal-harness.md` | 도구 테이블 정합 |
| D-7 | 소스 | opal-project-init | `opal/skills/opal-project-init/SKILL.md` | MEMORY.md 템플릿 동기화 |
| D-8 | 소스 | install-mac.sh | `scripts/install-mac.sh` | memory-tool 배포 등록 |

## §1. 관련 파일 맵 (경로:줄번호 — PM 검증 완료)

### 1.1 개정 대상 — memory-learning.md (D-1)

| 항목 | 위치 | 현 원문(요지) | 개정 |
|------|------|-------------|------|
| 인덱스 형식 | `memory-learning.md:17` | `\| 등록일시 \| 카테고리 \| 상태 \| 파일 \| 설명 \|` | 제목 컬럼 맨 앞 신설(R1) + 요약 ≤80자(R2) |
| 히스토리 형식 | `memory-learning.md:18` | `\| 등록일자 \| 작업 \| 단계 \| 경로 \| 시작일시 \| 완료일시 \|` | 제목 컬럼 맨 앞 신설(R1) + 핵심결과 ≤2줄(R2) |
| FIFO 규칙 | `memory-learning.md:22` | `정리: 작업 히스토리 10개 FIFO, 소유자 요청 시 정리 제안` | 10→5(R3) |
| 라이프사이클 | 부재 | 상태값 정의·삭제/승격 트리거 없음 | active/promoted/superseded/dead 신설(R4) |

### 1.2 구현 패턴 레퍼런스 — state-tool (D-3) ★ memory-tool이 직접 재사용

| 요소 | 위치 | memory-tool 재사용 방식 |
|------|------|----------------------|
| JSON 응답 헬퍼 | `state_tool.py:121` `ok()`, `:125` `err()` | 동일 시그니처 복사 — `{"ok":bool,"command":...}` 계약 |
| 에러코드 카탈로그(SSOT) | `state_tool.py:68` `ERROR_CODES = {...}` | 동일 dict 패턴, memory-tool 전용 코드 신설 |
| 마크다운 직접편집 금지 가드 | `state_tool.py:70` `marker_missing` + `:302/:307` err 처리 | `<!-- ... -->` 마커 기반 → MEMORY.md 인덱스·히스토리 영역에 동일 마커 적용(R9) |
| run.sh 래퍼 | `state-tool/run.sh:1-12` | venv python 호출 동일 구조 |
| 테스트 | `state-tool/tests/` (pytest) | memory-tool/tests/ 동일 구조 |

> **Simplicity(PRINCIPLES §2)**: memory-tool은 state-tool의 `ok`/`err`/마커가드/run.sh 구조를 그대로 차용한다(중복 재발명 금지, 표준 라이브러리만 의존).

### 1.3 신규 도구 선례 — tool-scan (D-4, 044)

```
opal/tools/tool-scan/  ├─ run.sh  ├─ tool_scan.py  ├─ schema/  ├─ tests/
```
- RED-first 분리(작성자 test-agent ≠ 구현자 be-agent, 테스트 25개) — 045도 동일 적용
- install 등록: `install-mac.sh:1087-1091`
- federation은 외부(MCP/skills) 연동용 — **memory-tool은 내부 도구라 federation 불필요**

### 1.4 정합 대상 진입점

| 대상 | 위치 | 작업 |
|------|------|------|
| project-init 템플릿(R10) | `opal/skills/opal-project-init/SKILL.md:408` "2-4. MEMORY.md 형식" (★templates/ 아님 — 인라인) | 신포맷 반영 |
| install 등록(R11) | `install-mac.sh:1087-1091`(tool-scan) 직후 | memory-tool chmod +x 블록 추가 |
| harness §9 테이블(R12) | `opal-harness.md:242-248`(7행) | xlsx-tool 다음 행 또는 말미에 memory-tool 행 |
| tools.md 테이블(R12) | **소스 경로 PLAN에서 확정** (배포본 `~/.opal/references/tools.md`, 소스 추정 `opal/core/references/tools.md`) | harness §9와 동일 행 |

## §2. 현 MEMORY.md 비대화 baseline (개선 효과 측정 기준)

- 본 프로젝트 `.opal/MEMORY.md`: 히스토리 10행(FIFO 한도), **044 행 단일 셀 ~1,500자**(설계·버그·테스트 전체 인라인)
- 상태값 무질서: `대기`/`폐기 기록`/`예정`/`완료`/`~~완료~~`/`유지` 혼재 — R4 라이프사이클 미정의 탓
- 예상 효과: R2(길이캡) → 1,500자 행 → 제목+2줄, R3(FIFO 5) → 히스토리 33%↓

## §3. 미확정 → PLAN 결정 대상

| # | 미확정 | 후보 |
|---|--------|------|
| U-1 | 메모리 활성 상한 N | 전체 단일 상한 vs 유형별(feedback/project/architecture별) |
| U-2 | memory-tool 서브명령 최종 셋 | `append`/`update`/`prune`/`promote`/`validate`/`migrate` 중 확정 + 인자 설계 |
| U-3 | `migrate` 범위 | 구포맷→신포맷 자동 변환 정도, 제목 자동 추출 vs PM 보정 |
| U-4 | tools.md 소스 경로 | `opal/core/references/tools.md` 존재 확인 필요 |

## §4. 리스크

| # | 리스크 | 영향 | 대응 |
|---|--------|------|------|
| R-1 | 메모리 blind FIFO 삭제 시 살아있는 지식 소실 | 데이터 손실 | append 차단 게이트 방식(무손실) — TASK 제약 확정됨 |
| R-2 | MEMORY.md 마커 미존재 기존 프로젝트 | memory-tool 동작 불가 | `migrate`/`init`이 마커 삽입 보장(state-tool marker 패턴 준용) |
| R-3 | self-confirming(도구가 자기 출력 검증) | 거짓 GREEN | RED-first 작성자≠구현자(044 선례) |
| R-4 | 배포본만 수정하고 소스 누락 | drift | 배포 경계 — 소스만 수정, install 재배포는 캡틴 |

## §5. 결론 — PLAN 입력 확정

- **확정 설계**: R1(제목 컬럼)·R2(길이캡)·R3(FIFO 5)·R4(라이프사이클) — memory-learning.md 개정으로 즉시 반영 가능
- **구현 전략**: memory-tool = state-tool 구조 차용 + tool-scan 선례(RED-first·install·drift) 적용
- **PLAN 결정 필요**: U-1~U-4 (4건)
