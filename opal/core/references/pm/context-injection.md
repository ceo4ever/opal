# 에이전트 컨텍스트 주입 원칙

> 출처: opal-pm.md §6
> Lazy 트리거: 디스패치 전 컨텍스트 주입 상세 판단 필요 시
> 탐색 경로: `opal/core/references/pm/context-injection.md`

워커에게 **문서 누락 없이 최적의 컨텍스트**를 제공하는 것이 목적이다.

## 최소 보장 (모든 에이전트에 항상 주입)

- `TASK.md` — 작업 목표와 요구사항
- `PLAN.md` 해당 Step 섹션 — EXECUTE 시 해당 기능 설계만 슬라이싱
- 에이전트 자체 로드 문서 — 각 전문 에이전트 AGENT.md에 정의된 문서 (에이전트가 자체 Read)

## 트리거 기반 동적 선별

PM이 작업 영역을 감지하여 관련 문서를 추가 선별한다. 정적 목록이 아닌 **원칙 기반 판단**:

| 감지 조건 | 탐색 방법 | 선별 기준 |
|----------|----------|----------|
| DB 모델/엔티티 관련 작업 | Glob: DB 설계 디렉토리 | 도메인명·테이블명 매칭 |
| FE 화면 구현 포함 | Glob: 와이어프레임/디자인 디렉토리 | 화면명 매칭 |
| 외부 API 연동 포함 | Glob: API 분석 디렉토리 | 매체/서비스명 매칭 |
| 기존 코드 수정 | code-scan: 변경 대상 파일의 depends 확인 | 의존 관계 파일 포함 |
| 이전 태스크 결과 참조 | .opal/MEMORY.md 관련 항목 | 관련 태스크 산출물 경로 |
| 작업 대상 파일 경로 | docs/PROJECT.md "## 프로젝트 구성" 섹션 | 요소 경로 prefix 매칭 → 매칭 요소의 전문 에이전트 참조 주입 (아래 §라우팅 참조) |

## PM 상황 판단 (추가 주입)

최소 보장 + 트리거로 부족한 경우, PM이 프로젝트 지식을 바탕으로 **추가 컨텍스트를 언제든 주입**한다:

- 프로젝트 메모리 (`.opal/memory/`에서 관련 항목)
- 이전 태스크 결정 사항
- 소유자 확정 기준 (`.opal/AGENT.md`)
- 다른 에이전트 결과물 (인터페이스 계약, API 스펙 등)
- 소유자 임시 지시 ("이번에는 이 방식으로 해")

## 목적: 누락 방지 + 최적 컨텍스트

```
최소 보장     → 기본 문서 누락 방지
트리거 선별   → 작업 관련 문서 자동 감지
PM 판단       → 위 두 가지로 못 잡는 맥락적 문서 보완
= 문서 누락 없이 최적의 컨텍스트 제공
```

## 기술 스택 연동 지시

`docs/PROJECT.md` 또는 `docs/ARCHITECTURE.md`의 기술 스택을 확인하고, 해당 기술에 맞는 MCP/스킬 활용을 디스패치에 명시적으로 포함한다:
- shadcn/ui 포함 → "shadcn MCP로 컴포넌트 조회 후 구현하라" 명시
- Python 프로젝트 → "context7로 최신 API 확인하라" 명시
- 외부 API 연동 → "웹 검색으로 최신 문서 확인하라" 명시

## 검증

워커 결과 검토(§4 PM Gate) 시, 주입한 참조 문서의 내용이 산출물에 반영되었는지 확인한다.

---

## PROJECT.md 프로젝트 구성 기반 라우팅

워커 디스패치 시 대상 파일 경로를 `docs/PROJECT.md`의 "## 프로젝트 구성" 섹션 요소 경로와 매칭하여 적합한 `전문 에이전트`를 자동 선정한다. opgc의 SCAN 동적 분할 병렬 디스패치도 동일 규약을 사용한다.

### 절차

1. `docs/PROJECT.md`의 "## 프로젝트 구성" 섹션 파싱 → `[(요소, 경로, 기술스택, 전문에이전트), ...]`
2. 디스패치 대상 파일 목록에서 파일별 경로 → **가장 긴 prefix** 매칭 요소 선정
3. 매칭된 요소의 `전문 에이전트`를 워커 디스패치 시 참조로 주입
4. 섹션 부재 시 또는 매칭 실패 시: `opal-task-agent`(범용)으로 폴백

### 의사코드

```python
def route(file_path, project_config):
    if not project_config.has_section("프로젝트 구성"):
        return "opal-task-agent"  # 하위호환 폴백
    best = None
    for element in project_config.elements:
        # 경로 필드는 쉼표로 복수 경로 허용 (예: "opal/, skills/, agents/")
        for prefix in element.paths:
            if file_path.startswith(prefix):
                if best is None or len(prefix) > len(best.matched_prefix):
                    best = element
                    best.matched_prefix = prefix
    return best.agent if best else "opal-task-agent"
```

### 예시

**프로젝트 구성 테이블**:

```
| 요소 | 경로 | 기술 스택 | 전문 에이전트 |
|------|------|-----------|---------------|
| frontend | web/ | React | opal-fe-agent |
| backend | api/ | FastAPI | opal-be-agent |
| batch | batch/ | (Backend 상속) | opal-be-agent |
```

**라우팅 결과**:

- `web/components/Button.tsx` → `frontend` 매칭 → **opal-fe-agent**
- `api/routers/user.py` → `backend` 매칭 → **opal-be-agent**
- `batch/daily_report.py` → `batch` 매칭 → **opal-be-agent** (Backend 상속)
- `scripts/deploy.sh` → 매칭 요소 없음 → **opal-task-agent** (폴백)

### opgc SCAN 동적 분할 연계

opgc(opal-pilot-gc)는 SCAN 단계에서 이 규약을 사용하여 `target_files`를 요소별로 분할하고, CHECK 단계에서 `(요소 × 체커)` 매트릭스로 병렬 디스패치한다. 각 체커 호출에는 매칭된 전문 에이전트 정보가 참조로 주입된다.

상세: `opal/skills/opal-pilot-gc/SKILL.md` STEP 1.5 / STEP 2.2.
