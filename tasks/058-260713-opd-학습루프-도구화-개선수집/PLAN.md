# PLAN: PM 학습 루프 tool-gated 재설계 + 로컬/FW 학습 분리 + fw-inbox 수집

> 작성일: 2026-07-13 | 입력: TASK.md, ANALYSIS.md
> 모드: Multi-Feature (6개 기능)
> 실행 모드: **복잡** (신규 스킬 + 신규 도구 + 4-pilot CLOSE 수정 + 문서 SSOT 재편 + 멀티 플랫폼 install)

---

## 1. 태스크 개요 + 기능 리스트업

### 1.1 요약

정의만 있고 호출 0건으로 죽어있는 PM 학습 루프를 `op-brain-ingest`의 tool-gated CLOSE 훅 패턴으로 재설계한다. ①태스크 경로는 CLOSE 회고 하드스텝으로 자동 enforce, ②비태스크 경로는 `//opim`(opal-improve) 온디맨드 스킬로 처리한다. 학습을 **로컬 PM 개선**(프로젝트 `.opal/`)과 **FW 개선**(전역 `~/.opal/fw-inbox/`)으로 분류하고, 신규 `improve-tool`이 기록을 결정론적으로 집행한다. 정의 3문서는 단일 SSOT(`pm-improvement-loop.md`)로 통합한다.

### 1.2 기능 목록

| F-ID | 기능명 | 포함 요구사항 | 우선순위 | 의존 |
|------|--------|-------------|---------|------|
| F-001 | improve-tool 결정론 집행 도구 (로컬/FW 분기) | R3 | P0 | 없음 |
| F-002 | fw-inbox 수집 디렉토리 + 항목 스키마 | R4 | P0 | F-001 (write 계약) |
| F-003 | opal-improve 스킬 (`//opim`) + registry | R2 | P0 | F-001, F-006(SSOT) |
| F-004 | CLOSE 회고 하드스텝 (4 pilot) | R1 | P0 | F-001, F-003 |
| F-005 | install 배포 반영 (mac + windows) | R6 | P0 | F-001, F-002, F-003 |
| F-006 | 문서 SSOT 통합 + dangling 정리 | R5 | P0 | 없음 |

> R1~R6 ↔ F-ID는 1:1 매핑이되, 빌드 의존순서에 맞춰 F 번호를 재배치했다(도구=F-001 최우선). R 번호는 TASK.md 원본을 보존한다.

### 1.3 기능 의존 그래프 (ASCII)

```
F-006 (SSOT 문서) ──────────────┐
                                 ├─→ F-003 (opal-improve 스킬)
F-001 (improve-tool) ──┬─────────┤
                       ├─→ F-002 (fw-inbox 스키마·dir)
                       └─────────┴─→ F-004 (CLOSE 회고 하드스텝)
                                          │
   F-001 + F-002 + F-003 ────────────────┴─→ F-005 (install 배포)
```

---

## 리스크 가설 표

> PLAN 단계 작성. TEST-SCENARIO.md §1의 입력이 된다.

| ID | 변경 단위 | 깨질 수 있는 계약 | 운영 영향 | 검증 계층 권고 | 시나리오 후보 |
|----|----------|----------------|---------|------------|------------|
| H-1 | F-004 회고 하드스텝 (4 pilot) | 회고 스텝이 CLOSE를 차단 — brain-ingest no-op 패턴 미준수 시 대상 부재에서 CLOSE 블로킹 | P0 | L1(스킬 프로세스 검토) + 동적(dry-run CLOSE) | S: 개선후보 0건 태스크에서 CLOSE 완주 |
| H-2 | F-003 scope 분류 판단(2원화) + F-001 분기 집행 | 로컬/FW 오분류 — LLM 분류가 scope를 잘못 정해 로컬↔FW 역기록 | P0 | L1(2원화: 결정론 게이트→루브릭, 동점 에스컬레이션) + 기능(도구 분기) | S: 결정론 명확건 즉시확정 / 경계건 루브릭 과반 / 동점 소유자 질의 |
| H-3 | F-006 rename/delete | `self-improvement.md`·구 `pm-learning-loop.md` 경로를 가리키는 dangling 참조 잔존 | P1 | L1(grep 0건 검증) | S: 정리 후 전수 grep 0건 |
| H-4 | F-001 improve-tool JSON 계약 | 모든 출력에 `"ok"` 필드 누락 → 호출자(스킬/CLOSE 스텝) 파싱 실패 | P1 | L1(단위) | S: 성공/실패/no-op 모두 `{"ok":...}` |
| H-5 | F-005 install fw-inbox 초기화 | 멱등성 위반 — 재설치 시 기존 fw-inbox 항목 삭제 (clean_dirs 오염) | P0 | L2(install 반복 실행) | S: 2회 install 후 기존 항목 보존 |
| H-6 | F-001 로컬 memory-tool 위임 | `.opal/MEMORY.md` 부재/포맷 불일치 시 위임 실패 → 예외 전파 | P2 | L1(단위) + no-op 안전 | S: MEMORY.md 부재 프로젝트에서 graceful skip |
| H-7 | F-004 4-pilot 일관성 | 4개 파일 동일 삽입 누락 — 일부 pilot만 회고 스텝 보유 | P1 | L1(4파일 grep 대칭) | S: opd/opwt/opgc/oppd 모두 회고 스텝 존재 |
| H-8 | F-002 fw-inbox 항목 스키마 | 출처 메타(host·project·situation·datetime) 누락 → 자기완결성 상실, FW 개선 출처 추적 불가 | P1 | L1(frontmatter 필수키) | S: record --scope fw 산출 항목에 4메타 전부 존재 |
| H-9 | F-006 §5 stub / 트리거 테이블 지칭 | SSOT 통합 후에도 `opal-pm.md §5` stub이 여전히 구 파일/잘못된 위치 지칭 | P1 | L1(참조 정합) | S: §5 stub이 pm-improvement-loop.md 지칭, 자기참조 지칭 오류 소멸 |

**가설 도출 근거**: H-1/H-7은 ANALYSIS §5 "CLOSE 4단계 일관성"(중간) 리스크, H-3은 ANALYSIS §5 "self-improvement.md 삭제 dangling"(낮음) 리스크, H-5는 CONVENTIONS 배포경계 [MUST]에서 파생.

---

## 2. 기능별 분석

### F-001: improve-tool 결정론 집행 도구

#### 2.1.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 도구 | `opal/tools/improve-tool/run.sh` | venv 래퍼 (표준 패턴) | 신규 |
| 도구 | `opal/tools/improve-tool/improve_tool.py` | 서브명령 디스패치 본체 | 신규 |
| 문서 | `opal/core/references/tools.md` | 도구 레지스트리 등록 | 수정 |

#### 2.1.2 현재 구현
ANALYSIS §1.2-B 확인: 기존 3도구(state/brain/memory)는 동일 `run.sh` 골격 — venv 경로 체크 후 `exec "$VENV_PYTHON" "$SCRIPT_DIR/<tool>.py" "$@"`, 실패 시 `{"ok":false,"error":"..."}` stderr (`opal/tools/brain-tool/run.sh:1-12`, `opal/tools/state-tool/run.sh:1-12`). python 본체는 argparse 서브파서 디스패치, 모든 출력 `"ok"` 필드 포함. memory-tool은 `append`/`update`/`promote` 등 8서브명령을 `--file <MEMORY.md>` 기준으로 제공 (`opal/tools/memory-tool/memory_tool.py:1202-1261`).

#### 2.1.3 영향 범위
- **피호출자(위임)**: local scope에서 `memory-tool run.sh append`를 subprocess 호출 (재사용).
- **호출자**: F-003 opal-improve 스킬 STEP 3, F-004 4-pilot CLOSE 회고 스텝.
- **신규 deps 없음**: `json`/`argparse`/`socket`/`datetime`/`subprocess`/`os`/`pathlib` 전부 stdlib — `opal/tools/requirements.txt` 변경 불필요.

---

### F-002: fw-inbox 수집 디렉토리 + 항목 스키마

#### 2.2.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 환경 | `~/.opal/fw-inbox/` | FW 개선 제안 수집 런타임 디렉토리 | 신규 (install 초기화) |
| 도구 | `opal/tools/improve-tool/improve_tool.py` | fw-inbox 항목 write 로직 (F-001과 공유) | 신규 |

#### 2.2.2 현재 구현
현재 부재. `~/.opal/`은 install 배포 대상이며 `fw-inbox/`는 런타임 데이터 디렉토리(사용자 데이터 보존 대상 — install `clean_dirs`에 미포함, `scripts/install-mac.sh:1035` 참조). brain의 `.opal/brain/`이 프로젝트 자산인 것과 달리, fw-inbox는 **전역** 수집소다.

#### 2.2.3 영향 범위
- fw-inbox 항목 write는 F-001 improve-tool `record --scope fw`가 전담(단방향 append). 디렉토리 초기화는 F-005 install.
- 소비자(후속 태스크): install 시 수집된 항목을 소유자/PM이 검토 → 프레임워크 소스 개선 반영 (이번 범위는 **기록까지**).

---

### F-003: opal-improve 스킬 (`//opim`) + registry

#### 2.3.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 스킬 | `opal/skills/opal-improve/SKILL.md` | 5단계 개선 프로세스 정의 | 신규 |
| 문서 | `opal/core/references/opal-skills-registry.json` | `opim` alias 엔트리 | 수정 |

#### 2.3.2 현재 구현
registry는 `groups` dict 구조(8그룹: opal-pilot/op-dev/op-sdd/op-data/op-task/standalone/opal/op-brain). PM-대면 온디맨드 operator 스킬(opal-brain=opbr, opal-skill-manager=osm 등)은 `opal` 그룹 소속 (`opal-skills-registry.json` groups.opal). 엔트리 스키마(단수 `alias`): `name`/`alias`/`description`/`triggers[]`/`paths[]`/`domain` (`opal-skills-registry.json:101-116` opgc 엔트리).

#### 2.3.3 영향 범위
- opal-improve는 F-001 improve-tool을 호출(기록 집행)하고, F-006 `pm-improvement-loop.md`(SSOT)를 프로세스 근거로 참조.
- F-004 회고 하드스텝이 이 스킬의 관찰→분류→기록 프로세스를 참조 모델로 삼는다.

---

### F-004: CLOSE 회고 하드스텝 (4 pilot)

#### 2.4.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 오케스트레이터 | `opal/skills/opal-pilot-dev/SKILL.md` | opd CLOSE (STEP 6) | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt CLOSE | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-gc/SKILL.md` | opgc CLOSE (STEP 4) | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd CLOSE (DONE.md 작성) | 수정 |

#### 2.4.2 현재 구현 (실제 Read로 확정 — ANALYSIS 미확정 2건 중 1건 해소)

4개 pilot CLOSE의 op-brain-ingest 훅 위치를 실제 Read로 확정했다:

| pilot | CLOSE 섹션 | op-brain-ingest 훅 줄 | 회고 스텝 삽입 지점 (확정) |
|-------|-----------|---------------------|------------------------|
| opd | STEP 6 CLOSE (`opal-pilot-dev/SKILL.md:230-262`) | 3번 항목 `:239-247` | brain-ingest(3) 직후 · 완료보고(4, `:248`) 직전 |
| opwt | CLOSE 단계 (`opal-pilot-write-tech/SKILL.md:377-410`) | 3번 항목 `:390-398` | brain-ingest(3) 직후 · 완료보고(4, `:399`) 직전 |
| opgc | STEP 4 CLOSE (`opal-pilot-gc/SKILL.md:324-365`) | 4.2 내 `:355-364` | brain-ingest 블록 직후 · 4.3 opds 체인(`:366`) 직전 |
| oppd | DONE.md 작성 (`opal-pilot-project-dev/SKILL.md:631-668`) | `:660-668` | brain-ingest(`:668`) 직후 · 문서 등록 프로토콜(`:672`) 직전 |

> **[확정] ANALYSIS "oppd 761+ 추정" 정정**: oppd의 op-brain-ingest 디스패치 훅은 `opal-pilot-project-dev/SKILL.md:660-668`에 실재한다(DONE.md 작성 `:631-658` 직후). 761대는 CLOSE 진입 게이트(`:765`)로 별개다. 회고 스텝은 `:668`(brain-ingest) 직후에 삽입한다.

공통 CLOSE 순서(3 pilot): ①DONE.md+mark → ②관련문서 업데이트 → ③op-brain-ingest → ④완료보고. 관련문서 업데이트가 brain-ingest **직전**에 오는 것은 "ingest 품질 보장"을 위한 의도적 순서(`opal-pilot-dev/SKILL.md:238`)다.

#### 2.4.3 영향 범위
- 회고 스텝은 op-brain-ingest와 나란한 CLOSE 지식/개선 훅. 입력은 **태스크/세션 궤적 신호**(STATE.md 검증 루프·재설계 루프·PM 검수 로그 등), 산출은 프로세스·규칙 개선점.
- oppd SKILL.md는 F-006(§561-566 naming 정리)과 **동일 파일**을 수정 → §4.3에서 순차 처리 명시.

---

### F-005: install 배포 반영 (mac + windows)

#### 2.5.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 배치 | `scripts/install-mac.sh` | 도구 chmod + fw-inbox 초기화 | 수정 |
| 배치 | `scripts/install/windows.ps1` | tools 복사 + fw-inbox 초기화 | 수정 |

#### 2.5.2 현재 구현 (실제 Read로 확정)
- **스킬**: `opal/skills/*/` 디렉토리 루프로 **자동 배포** (`install-mac.sh:1058-1070`). opal-improve는 신규 함수 불필요 — 디렉토리 존재만으로 배포됨.
- **도구**: `install_dir "$opal_dir/tools" ...`로 **자동 복사** (`install-mac.sh:1113`) 후, **도구별 명시 `chmod +x run.sh` 블록** 필요 (state/brain/cmux/memory/backlog 등 각각 블록 존재, `:1122-1178`). improve-tool은 **신규 chmod 블록** 필요(backlog-tool 블록 `:1173-1178` 직후).
- **런타임 dir**: `clean_dirs=(skills agents references templates tools dashboard-server)` — fw-inbox 미포함(사용자 데이터 보존, `:1035`). fw-inbox 초기화는 **신규 `mkdir -p` 블록** 필요(create-if-absent).
- **windows.ps1**: 스킬 loop(`windows.ps1:482-501`), 도구 `Copy-Item`(`:542-548`)로 자동. fw-inbox `New-Item -ItemType Directory` 블록 신규 필요.

#### 2.5.3 영향 범위
멱등성 [MUST]: fw-inbox는 절대 `rm` 대상이 되어선 안 되며 `mkdir -p`(존재 시 no-op)로만 초기화한다 (H-5).

---

### F-006: 문서 SSOT 통합 + dangling 정리

#### 2.6.1 관련 파일 맵
| 영역 | 경로 | 역할 | 변경 유형 |
|------|------|------|----------|
| 문서 | `opal/core/references/harness/pm-learning-loop.md` → `pm-improvement-loop.md` | SSOT 본문화(rename+흡수) | 수정(rename) |
| 문서 | `opal/core/references/pm/self-improvement.md` | 삭제 (내용 흡수) | 삭제 |
| 문서 | `opal/core/references/opal-pm.md` | §5 stub 갱신 (`:71-76`) | 수정 |
| 에이전트 | `opal/core/references/pm/specialist-agent.md` | `:69` 지칭 정리 | 수정 |
| 오케스트레이터 | `opal/skills/opal-project-init/references/agent-guide.md` | `:135`,`:148` 지칭 정리 | 수정 |
| 문서 | `opal/core/AGENT.md` | `:35` 지칭 정리 | 수정 |
| 오케스트레이터 | `opal/skills/opal-pilot-project-dev/SKILL.md` | `:561-566` 지칭 정리 | 수정 |

#### 2.6.2 현재 구현 — dangling 참조 전수 목록 (실제 grep으로 확정 — ANALYSIS "5개" 정정)

전수 grep(`self-improvement` / `pm-learning-loop` / `학습 루프` / `자기 개선`) 결과, 정리 대상을 **경로 dangling(AC 차단)** 과 **지칭·명명 정리** 로 분류하여 확정한다:

| # | 위치 | 현재 참조 | 유형 | 정리 조치 |
|---|------|----------|------|----------|
| ① | `opal-pm.md:75` | → `harness/pm-learning-loop.md` | **경로 dangling** | `pm-improvement-loop.md`로 재지정 |
| ② | `pm-learning-loop.md:32` | → `pm/self-improvement.md` | **경로 dangling** | 병합으로 제거(내용 흡수, 교차참조 소멸) |
| ③ | `self-improvement.md:7` | "트리거 테이블은 opal-pm.md §5에 유지" (실제 표는 `pm-learning-loop.md:22-30`) | **지칭 오류** | 파일 삭제 + 단일 SSOT 통합으로 소멸 |
| ④ | `specialist-agent.md:69` | "opal-pm.md §5 학습 루프" | 명명·지칭 | "개선 루프"로 명명 정리 |
| ⑤ | `agent-guide.md:135` | "PM 학습 루프에서 새로운 도메인 지식…" | 명명 | "PM 개선 루프" |
| ⑥ | `agent-guide.md:148` | "PM 학습 루프에서 누적되는…" | 명명 | "PM 개선 루프" |
| ⑦ | `opal/core/AGENT.md:35` | "…검토 게이트, 학습 루프 등" | 명명 | "개선 루프" |
| ⑧ | `oppd SKILL.md:561-566` | "PM 검수 → 학습 루프 연결" / "PM 학습 루프로 승격" | 명명·SSOT 지칭 | "PM 개선 루프" + 신규 SSOT 지칭 |
| (참고) | `opal-pm.md:344` | 변경이력에 `pm-learning-loop.md` 언급 | 이력 기록 | **불변**(과거 마이그레이션 기록 — live 포인터 아님) |

> **[확정] "self-improvement.md·구 pm-learning-loop.md를 가리키는 dangling 참조"의 실제 경로-포인터는 2건(①②)**이며, ②는 rename+병합으로 자연 소멸한다. 나머지 ④~⑧은 "학습 루프" 개념명을 "개선 루프"로 통일하는 명명 정리(§5 stub 갱신·지칭 오류 수정 AC 포함). ⑨(`:344`)는 changelog 이력이므로 소급 변경하지 않는다(CONVENTIONS §변경이력 이력 보존 원칙). AC "dangling 0건"은 ①②③ 해소로 충족된다.

#### 2.6.3 영향 범위
- 정리 순서: **rename+병합 먼저(신규 SSOT 확정)** → 그 다음 dangling/명명 참조를 신규 경로·명으로 재지정 → 마지막 self-improvement.md 삭제. (삭제 전 참조 소멸 확인 — H-3)

---

## 3. 기능별 설계

### F-001: improve-tool 결정론 집행 도구

#### 3.1.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/tools/improve-tool/run.sh` | 도구 | venv 래퍼 (표준 골격 복제) | (→ D-11 `brain-tool/run.sh:1-12`) |
| 2 | `opal/tools/improve-tool/improve_tool.py` | 도구 | argparse 서브명령 디스패치 | (→ D-13 memory_tool argparse 패턴) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/tools.md` | 문서 | improve-tool 등록 행 추가 | (→ D-1 R3 "tools.md 등록") |

#### 3.1.2 API·데이터 모델·설계

**run.sh 골격** (표준 답습):
```bash
#!/bin/bash
# improve-tool 래퍼 — OPAL .venv python 호출
# @header: shell script — 적용 대상 아님 (header-rules.md)
VENV_PYTHON="$HOME/.opal/.venv/bin/python"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -x "$VENV_PYTHON" ]]; then
  echo '{"ok":false,"error":"OPAL .venv not found. Run install-mac.sh first."}' >&2
  exit 1
fi
exec "$VENV_PYTHON" "$SCRIPT_DIR/improve_tool.py" "$@"
```
- [MUST] `docs/CONVENTIONS.md` §도구 우선 원칙: "파일 처리·데이터 변환 작업이 필요할 때, 직접 코드를 작성하기 전에 OPAL 도구를 우선 검토한다" → local scope는 memory-tool을 재사용(위임)한다 (→ D-17 §189-193).
- [MUST] `docs/CONVENTIONS.md` §@header 규칙: shell run.sh는 @header 적용 대상 아님, `improve_tool.py`는 파일 상단 @header 블록 작성 (→ D-17 §171-175).

**improve_tool.py 서브명령 스펙**:

| 서브명령 | 인자 | 동작 | 반환 |
|---------|------|------|------|
| `record` | `--scope {local\|fw}`(req) · `--title`(req) · `--body`(제안 본문) · `--situation`(발생 맥락 유형) · `--source-task`(태스크번호/경로) · `--project-root`(로컬 목적지/메타 해석) | scope 분기 기록 | `{"ok":true,"scope":...,"path":...,"id":...}` |
| `list` | `--scope {local\|fw}` · `--project-root`(local 시) | 항목 목록 (read-only) | `{"ok":true,"scope":...,"items":[...]}` |
| `show` | `--scope {local\|fw}` · `--id`/`--path` | 단일 항목 조회 (read-only) | `{"ok":true,"item":{...}}` |

**scope 분기 로직 (핵심 — H-2)**:
- `record --scope local`: 프로젝트 로컬 개선 후보. `<project-root>/.opal/MEMORY.md`가 존재하면 **memory-tool 위임** — `memory-tool/run.sh append --file <root>/.opal/MEMORY.md --kind memory --title <title> --type improvement --status candidate --summary <body 요약 ≤80자>` subprocess 호출 (→ D-13 `memory_tool.py:1202-1212` append 시그니처). MEMORY.md 부재 시 `{"ok":true,"scope":"local","skipped":true,"reason":"no MEMORY.md"}` no-op 반환 (H-6). AGENT.md 확정기준 실제 편집은 5단계 中 **승인 후 PM 수행**(도구는 후보 기록까지).
- `record --scope fw`: 프레임워크 개선 제안. `~/.opal/fw-inbox/{YYYYMMDD-HHmmss}-{host}-{slug}.md` 파일을 결정론적으로 write (F-002 스키마). host=`socket.gethostname()`, datetime=`datetime.now()` KST, project=`--project-root` basename.

**JSON 계약 [MUST]** (→ D-1 R3 AC, D-11/D-13 기존 도구 패턴): 성공 `{"ok":true,...}` / 실패 `{"ok":false,"error":"..."}` / no-op `{"ok":true,"skipped":true,...}`. 모든 경로에서 `"ok"` 필드 보장 (H-4).

#### 3.1.3 환경 변경
해당 없음 (stdlib만 사용, requirements.txt 불변).

#### 3.1.4 배치/마이그레이션
해당 없음.

#### 3.1.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-001 | R3 AC | 기능 테스트 | `record --scope fw` → `~/.opal/fw-inbox/*.md` 생성 + `{"ok":true}` |
| TS-002 | R3 AC | 기능 테스트 | `record --scope local` (MEMORY.md 존재) → memory-tool append 위임 성공 |
| TS-003 | R3 AC / H-4 | 단위 | 성공/실패/no-op 3경로 모두 `"ok"` 필드 포함 |
| TS-004 | H-6 | 단위 | MEMORY.md 부재 시 `record --scope local` graceful skip |

---

### F-002: fw-inbox 수집 디렉토리 + 항목 스키마

#### 3.2.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `~/.opal/fw-inbox/` (install 초기화) | 환경 | FW 개선 수집소 | (→ D-1 R4) |
| 2 | `~/.opal/fw-inbox/README.md` (install seed, create-if-absent) | 환경 | 수집소 용도·항목 스키마 안내 | (→ D-1 R4 자기완결) |

> fw-inbox 항목 write 로직은 F-001 `improve_tool.py`에 구현. 스키마는 아래 3.2.2가 SSOT.

#### 3.2.2 데이터 모델 — fw-inbox 항목 스키마 (자기완결 md, H-8)

파일명: `{YYYYMMDD-HHmmss}-{host}-{slug}.md` (정렬 가능·충돌 회피).

```markdown
---
type: fw-improvement
title: <제안 제목>
created: <YYYY-MM-DD HH:mm KST>
host: <hostname>                    # 출처 메타 — 어느 PC
project: <프로젝트명>                # 출처 메타 — 어느 프로젝트
project_root: <절대경로>
source_task: <NNN | task-path | "">
situation: <retrospective | feedback | conversation>   # 발생 맥락 유형
status: inbox
---

## 제안 요약
<1-2문장>

## 상황 (Context)
<어떤 상황에서 이 개선이 필요하다고 판단했는지 — 궤적 신호>

## 제안 내용
<구체적 개선 — 어느 프레임워크 소스 SSOT(스킬/도구/참조문서)를 어떻게 바꿔야 하는지>
```

- 출처 메타 4종 [MUST] (→ D-1 R4): `host`·`project`·`situation`·`created`(일시). 자기완결 = 이 파일만으로 출처·맥락·제안이 재구성 가능.
- [MUST] `docs/CONVENTIONS.md` §배포 경계: "~/.opal/ 배포 파일을 직접 편집하지 않는다" — fw-inbox는 **런타임 데이터 디렉토리**로 예외(install이 `mkdir -p`로 초기화, 항목 write는 improve-tool 전담) (→ D-17 §201-204).

#### 3.2.3 환경 변경
`~/.opal/fw-inbox/` 디렉토리 (F-005 install이 초기화).

#### 3.2.4 배치/마이그레이션
해당 없음.

#### 3.2.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-005 | R4 AC / H-8 | 산출물 검사 | fw 항목 frontmatter에 host·project·situation·created 전부 존재 |
| TS-006 | R4 AC | 기능 테스트 | FW 분류→fw-inbox, 로컬 분류→`.opal/` 목적지로 실제 분기됨 |

---

### F-003: opal-improve 스킬 (`//opim`) + registry

#### 3.3.1 파일 변경 계획

**신규 생성**
| # | 경로 | 영역 | 역할 | 근거 |
|---|------|------|------|------|
| 1 | `opal/skills/opal-improve/SKILL.md` | 스킬 | 5단계 개선 프로세스 | (→ D-1 R2) |

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/core/references/opal-skills-registry.json` | 문서 | `opal` 그룹에 opim 엔트리 추가 | (→ D-14 groups.opal) |

#### 3.3.2 설계

**SKILL.md frontmatter** (→ D-17 §YAML Frontmatter): `name: opal-improve`, `version`, `description`(트리거 상황 포함), `domain: improvement`.

**5단계 프로세스** (관찰→분류→기록→보고→승인 — self-improvement.md `:20-32` 흡수):
1. **관찰**: 개선 대상 발견 — (온디맨드) 대화/L2/피드백, (회고 참조) 태스크·세션 궤적 신호.
2. **분류 (로컬 PM 개선 vs FW 개선 — 2원화 판단: 결정론 → 루브릭)**:

   개선 후보의 scope를 **2단계**로 판단한다. 단일 LLM 직관 판단을 지양하고, 이 프로젝트의 검증 2원화(전단 루브릭 심판 / 후단 결정론 검증 — oppl `opal-evaluator-agent` + `opal-test-agent`) 사상을 **분류 판단에 적용**한다.

   **1차 — 결정론 게이트 (deterministic)**: 개선이 반영될 **대상**으로 즉시 판별. 한쪽이 명확하면 확정하고 2차를 건너뛴다.
   | 대상 시그널 | scope |
   |------------|-------|
   | 프레임워크 소스(`opal/`·`skills/`·`agents/`·`scripts/`·`~/.opal` 배포물)·보고형식·하네스·스킬·도구·부트스트랩 | **fw** |
   | 그 프로젝트 고유 도메인 규칙·코드·기획 산출물 (프레임워크 무관) | **local** |

   **2차 — 루브릭 평가 (경계 사례만)**: 1차로 한쪽이 명확하지 않을 때만 아래 루브릭으로 채점하여 과반 scope로 확정. **동점이면 소유자에게 질의(에스컬레이션)**.
   | 루브릭 항목 | fw 쪽 | local 쪽 |
   |-----------|-------|---------|
   | 재사용성 — 다른 프로젝트에서도 유효한 개선인가 | 유효 | 이 프로젝트 한정 |
   | 프로젝트 독립성 — 특정 도메인/코드에 의존하는가 | 독립 | 의존 |
   | 귀속 SSOT — 반영될 SSOT가 프레임워크 문서/코드인가 | 프레임워크 | 프로젝트 |

   > **결정 테스트 (역할 일반어)**: "이 개선이 프로젝트에 독립적으로 **모든 프로젝트/PM에 유효한가?**" → Yes = **fw** / No = **local**. (특정 정체성 이름이 아니라 역할 일반어 `PM`을 사용한다 — 재사용·공유 지식에 개인 호칭 배제 원칙, `AGENT.md §정체성 적용 > 재사용 지식(brain) 예외` 정합.)

   **분류 결과별 저장 위치**:
   - **로컬 PM 개선** → 프로젝트 `.opal/`: AGENT.md 확정기준·PM 검토기준, 전문 에이전트 확정기준, `.opal/memory/` (self-improvement.md `:9-18` 기록위치 테이블 흡수).
   - **FW 개선** → `~/.opal/fw-inbox/`: 에이전트 행동(보고형식·프로세스)·스킬·도구·하네스 SSOT 개선. [MUST] `TASK.md §확정방향 8`: "에이전트 행동 개선은 개인 memory가 아니라 프레임워크 소스 SSOT 수정 → install 배포 대상" (프레임워크-우선).

   > ⚠️ **이 repo(ai-framework) 특수성**: 프로젝트 자체가 프레임워크라 대부분 **fw로 수렴**한다. 일반 프로젝트(회사 서비스 등)에선 결정론 게이트만으로 대부분 갈린다.
   > **판단 주체·집행 경계**: 위 2원화 판단은 **LLM(스킬/회고 스텝)** 이 수행하고, 확정된 scope는 `improve-tool record --scope <local|fw>`가 **결정론적으로 집행(기록)** 한다. 도구는 판단하지 않는다.
3. **기록**: `improve-tool record --scope <local|fw>` 호출 (결정론 집행 — F-001).
4. **보고**: "개선 후보 N건 기록: {요약}" 소유자에게 간략 보고.
5. **승인**: 소유자 이의 없으면 확정. [MUST] `pm/self-improvement.md` §자기 개선 제한 흡수: "기존 확정 기준 수정/삭제·금지사항 추가는 소유자 승인 필수", "프레임워크 에이전트(`~/.opal/agents/`)는 수정 안 함".

**registry 엔트리** (opal 그룹, → D-14 opgc 스키마 `:101-116`):
```json
{
  "name": "opal-improve",
  "alias": "opim",
  "description": "PM 개선 루프 — 관찰→분류→기록→보고→승인. 로컬 PM 개선 / FW 개선 분류 기록",
  "triggers": ["^opal-improve$", "^opim$", "(?i)(개선\\s*제안|프레임워크\\s*개선|개선\\s*기록|회고)"],
  "paths": ["{project}/.opal/skills/opal-improve/SKILL.md", "~/.opal/skills/opal-improve/SKILL.md"],
  "domain": "improvement"
}
```
- [MUST] `docs/CONVENTIONS.md` §38 약어: `op+2글자` 컨벤션 부합 확인 — `opim` 25개 alias 충돌 없음 (→ D-1 §확정방향 4).

#### 3.3.3 환경 변경 / 3.3.4 배치
해당 없음.

#### 3.3.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-007 | R2 AC | 산출물 검사 | SKILL.md에 5단계 + 로컬/FW 분류 분기 명시 |
| TS-007b | R2 AC / H-2 | 산출물 검사 | 분류 단계에 결정론 게이트표 + 루브릭표 + 동점 에스컬레이션 + 역할일반어(PM) 명시 |
| TS-008 | R2 AC | 기능 테스트 | registry match로 `//opim` 해석됨 |

---

### F-004: CLOSE 회고 하드스텝 (4 pilot)

#### 3.4.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `opal/skills/opal-pilot-dev/SKILL.md` | 오케스트레이터 | STEP6 brain-ingest(`:247`) 직후 회고 스텝 삽입 | (→ D-4) |
| 2 | `opal/skills/opal-pilot-write-tech/SKILL.md` | 오케스트레이터 | CLOSE brain-ingest(`:398`) 직후 삽입 | (→ D-5) |
| 3 | `opal/skills/opal-pilot-gc/SKILL.md` | 오케스트레이터 | STEP4 brain-ingest(`:364`) 직후·4.3 직전 삽입 | (→ D-6) |
| 4 | `opal/skills/opal-pilot-project-dev/SKILL.md` | 오케스트레이터 | brain-ingest(`:668`) 직후·문서등록(`:672`) 직전 삽입 | (→ D-7) |

#### 3.4.2 설계 — 회고 하드스텝 계약 (op-brain-ingest 답습)

**설계 결정 D-R1 — 인라인 오케스트레이터 스텝 (dispatched worker 아님)**: op-brain-ingest는 격리 컨텍스트에서 무거운 page 저술을 하므로 워커 디스패치이나, 회고 입력은 **오케스트레이터만 보유한 세션 궤적 신호**(STATE.md 검증/재설계/PM 검수 로그 + 세션 기억)다. 따라서 회고는 **CLOSE 인라인 스텝**으로 설계하고, opal-improve(F-003)의 관찰→분류→기록 프로세스를 참조 모델로 삼는다.

**삽입 스텝 공통 템플릿** (4 pilot 동일 — H-7):
```markdown
N. **회고(개선 루프) 하드스텝** (op-brain-ingest 직후 실행):
   - 입력: 태스크/세션 궤적 신호 — 워커 재시도·폴백, 소유자 재지시·피드백,
     PM Gate 반복 이슈, PLAN 재진입, 검증/재설계 루프 로그(STATE.md).
     ※ 산출물 재독이 아님(그건 PM Gate/QA 담당). 산출 = 프로세스·규칙 개선점.
   - 관찰→분류(로컬 PM 개선 / FW 개선)→기록: 개선 후보별로
     `~/.opal/tools/improve-tool/run.sh record --scope <local|fw> --title ... --body ...
      --situation retrospective --source-task <NNN> --project-root <루트>` 호출.
   - 산출 결정론 기록: 개선 후보 N건은 improve-tool이 결정론적으로 기록(로컬→.opal / FW→fw-inbox).
   - **no-op 안전 [MUST]**: 궤적 신호에서 개선 후보가 **없으면** 기록 없이 "개선후보 0건" 보고 —
     op-brain-ingest의 skipped와 동일하게 **CLOSE를 중단시키지 않는다**.
   - 개선 루프 프로세스 SSOT: `opal/core/references/harness/pm-improvement-loop.md`.
```

- [MUST] `TASK.md §확정방향 1`: "CLOSE 단계에 회고 하드스텝 삽입 → 자동 enforce(tool-gated)".
- [MUST] `TASK.md §제약`: "op-brain-ingest 성공 패턴 답습(CLOSE 하드연결 + 도구 집행 + 증거 산출)" + "no-op 안전(대상 없으면 CLOSE 비차단)" (→ D-3 `op-brain-ingest/SKILL.md:281` 집행 경계).
- **변경이력 행 추가 의무** [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무: 4개 SKILL.md 변경이력 표에 행 추가 (→ D-17 §195-198).

#### 3.4.3 환경 변경 / 3.4.4 배치
해당 없음.

#### 3.4.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-009 | R1 AC / H-7 | 산출물 검사 | 4 pilot CLOSE 모두 회고 스텝이 op-brain-ingest와 나란히 존재 |
| TS-010 | R1 AC | 산출물 검사 | 회고 스텝이 improve-tool 호출 + 개선후보 N건/없음 결정론 기록 명시 |
| TS-011 | H-1 | 기능 테스트 | 개선후보 0건 시나리오에서 CLOSE 비차단 (no-op 안전) |

---

### F-005: install 배포 반영 (mac + windows)

#### 3.5.1 파일 변경 계획

**수정**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `scripts/install-mac.sh` | 배치 | improve-tool chmod 블록 + fw-inbox mkdir 블록 | (→ D-15) |
| 2 | `scripts/install/windows.ps1` | 배치 | fw-inbox New-Item 블록 (도구/스킬은 자동) | (→ D-16) |

#### 3.5.2 설계

**install-mac.sh 추가 지점** (실제 Read 확정):
1. **improve-tool chmod 블록** — backlog-tool 블록(`:1173-1178`) 직후 삽입:
   ```bash
   # ── improve-tool 실행 권한 (058) ──
   local improve_run="$opal_home/tools/improve-tool/run.sh"
   if [[ -f "$improve_run" ]]; then
       chmod +x "$improve_run"
       success "improve-tool run.sh 실행 권한 설정"
   fi
   ```
   > opal-improve 스킬·improve-tool 파일 복사는 기존 skills 루프(`:1058`)·`install_dir tools`(`:1113`)가 자동 처리 — 신규 복사 함수 불필요.
2. **fw-inbox 초기화 블록** [MUST] 멱등 (H-5) — `install_opal` 내 tools 처리부 이후:
   ```bash
   # ── fw-inbox 런타임 디렉토리 초기화 (058, create-if-absent — 사용자 데이터 보존) ──
   mkdir -p "$opal_home/fw-inbox"
   [[ -f "$opal_home/fw-inbox/README.md" ]] || cp "$opal_dir/tools/improve-tool/fw-inbox-README.md" "$opal_home/fw-inbox/README.md"
   ```
   - [MUST] `docs/CONVENTIONS.md` §배포 경계 + `install-mac.sh:1035` clean_dirs: fw-inbox는 clean_dirs에 **추가하지 않는다**(rm 금지). `mkdir -p`는 존재 시 no-op → 재설치 멱등.

**windows.ps1 추가 지점**: 도구/스킬 자동 복사(`:482-548`) 후 fw-inbox 초기화:
```powershell
$fwInbox = Join-Path $OpalHome 'fw-inbox'
New-Item -ItemType Directory -Path $fwInbox -Force | Out-Null   # -Force = 존재 시 no-op(멱등)
```
> `$cleanDirs`(`windows.ps1:433`)에 fw-inbox 미추가 유지.

#### 3.5.3 환경 변경
`~/.opal/fw-inbox/` 생성. 3.5.4 배치: install 스크립트 자체가 배포 배치.

#### 3.5.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-012 | R6 AC | 통합 테스트 | install 실행 후 `~/.opal/skills/opal-improve/`·`~/.opal/tools/improve-tool/`·`~/.opal/fw-inbox/` 존재 |
| TS-013 | H-5 | 회귀 테스트 | install 2회 실행 후 fw-inbox 기존 항목 보존 (멱등) |

---

### F-006: 문서 SSOT 통합 + dangling 정리

#### 3.6.1 파일 변경 계획

**수정/rename/삭제**
| # | 경로 | 영역 | 변경 내용 요약 | 근거 |
|---|------|------|--------------|------|
| 1 | `pm-learning-loop.md` → `pm-improvement-loop.md` | 문서 | git mv + self-improvement 내용 흡수·재구성 | (→ D-8, D-9) |
| 2 | `pm/self-improvement.md` | 문서 | 삭제 | (→ D-9) |
| 3 | `opal-pm.md:71-76` | 문서 | §5 stub 갱신(개선 루프 명 + 신규 SSOT 지칭) | (→ D-10) |
| 4 | `specialist-agent.md:69` / `agent-guide.md:135,148` / `AGENT.md:35` / `oppd SKILL.md:561-566` | 에이전트/오케스트레이터 | 명명·지칭 정리 (2.6.2 ④~⑧) | (→ D-19, D-7) |

#### 3.6.2 설계 — pm-improvement-loop.md (단일 SSOT) 구조

두 얼굴 명확 분리 [MUST] (`TASK.md §확정방향 6`):
```markdown
# PM 개선 루프 (Improvement Loop)
## 1. 두 트랙 개요
   - 트랙 A (회고): 태스크 CLOSE 회고 하드스텝 — 자동 enforce(tool-gated), 입력=궤적 신호
   - 트랙 B (피드백·질문): //opim 온디맨드 + 피드백 nudge(soft), 입력=대화/L2
## 2. 트리거 테이블            # pm-learning-loop.md:22-30 흡수 (지칭 오류 소멸)
## 3. 5단계 프로세스           # self-improvement.md:20-32 흡수
## 4. 학습 2분류 + 기록 위치   # self-improvement.md:9-18 흡수 + FW/fw-inbox 행 추가
## 5. 도구 집행                # improve-tool / opal-improve 연결
## 6. hook 미채택 근거         # TASK 배경분석 흡수 (플랫폼 독립)
## 변경이력
```
- [MUST] `TASK.md §확정방향 2`: 로컬 PM 개선→프로젝트 `.opal/` / FW 개선→`~/.opal/fw-inbox` (§4 기록위치 테이블에 명문화).
- [MUST] `TASK.md §확정방향 5`: "hook 인프라 전면 폐기 — 순수 스킬 온디맨드 + 태스크 CLOSE 하드스텝만" (§6 근거 기록).
- **정리 순서** (H-3): ①rename+병합(SSOT 확정) → ②참조 재지정(③④~⑧) → ③self-improvement.md 삭제 → ④전수 grep 0건 확인.
- **변경이력 행 추가** [MUST] `docs/CONVENTIONS.md` §변경이력 작성 의무 — 변경 문서 전부 (→ D-17 §195-198).

#### 3.6.3 환경 변경 / 3.6.4 배치
해당 없음 (rename은 install skills/references 재배포로 반영).

#### 3.6.5 테스트 시나리오
| TS-ID | AC 매핑 | 유형 | 기대 결과 |
|-------|---------|------|----------|
| TS-014 | R5 AC① | 산출물 검사 | pm-improvement-loop.md에 트리거 테이블·5단계·기록위치 모두 존재 |
| TS-015 | R5 AC② | 산출물 검사 | self-improvement.md 파일 제거됨 |
| TS-016 | R5 AC③ / H-3 | 회귀 테스트 | `self-improvement`·구 `pm-learning-loop` 경로 grep 0건 |
| TS-017 | R5 AC④ / H-9 | 산출물 검사 | §5 stub이 신규 SSOT 지칭, 자기참조 지칭 오류 소멸 |

---

## 4. 통합 실행 계획

### 4.1 Phase 그룹핑 (기능 의존 기반)

| Phase | 기능 | Step | agent | 실행 | 비고 |
|-------|------|------|-------|------|------|
| 1 | F-001, F-002 | 1, 2 | opal-task-agent | 순차(동일 도구 파일) | 도구 write 계약 먼저 |
| 1 | F-006 | 3, 4 | opal-task-agent | Phase1 내 병렬 가능 | 문서군 독립 |
| 2 | F-003 | 5, 6 | opal-task-agent | 순차 | 도구·SSOT 완료 후 |
| 2 | F-004 | 7, 8, 9, 10 | opal-task-agent | 병렬(파일 독립)·oppd만 F-006과 순차 | 4 pilot |
| 3 | F-005 | 11, 12 | opal-task-agent | 병렬(mac/win 독립) | 전체 완료 후 |
| 4 | 문서 | 13 | PM 직접 | 최종 | docs/PROJECT.md 등록 |

### 4.2 실행 체크리스트

> 총 13개 Step | Phase 4개 | 실행 모드: **복잡**

#### Step 1: improve-tool 골격 + record/list/show 서브명령 구현
- [x] 완료
- **소속 기능**: F-001, F-002
- **영역**: 도구
- **agent**: opal-task-agent
- **파일**: `opal/tools/improve-tool/run.sh`, `opal/tools/improve-tool/improve_tool.py`, `opal/tools/improve-tool/fw-inbox-README.md`(install seed)
- **작업 내용**: run.sh 표준 골격 복제(§3.1.2) + improve_tool.py argparse 서브명령(record/list/show) + scope local(memory-tool 위임)/fw(fw-inbox write §3.2.2 스키마) 분기 + JSON `"ok"` 계약 + @header
- **완료 기준**: `record --scope fw` 및 `--scope local`(MEMORY.md 존재) dry-run 성공, 3경로 모두 `"ok"` 포함
- **테스트**: TS-001~006
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 2: tools.md 도구 등록
- [x] 완료
- **소속 기능**: F-001
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/tools.md`
- **작업 내용**: improve-tool 등록 행 추가(서브명령·용도·JSON 계약 요약)
- **완료 기준**: tools.md에 improve-tool 항목 존재
- **테스트**: TS-003
- **실행 방법**: sub-agent
- **의존**: Step 1

#### Step 3: pm-improvement-loop.md rename + 병합 + 재구성
- [x] 완료
- **소속 기능**: F-006
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/harness/pm-learning-loop.md`→`pm-improvement-loop.md`, `opal/core/references/pm/self-improvement.md`(삭제)
- **작업 내용**: git mv rename → self-improvement.md 내용 흡수 → §3.6.2 6섹션 구조(두 트랙/트리거/5단계/2분류·기록위치/도구집행/hook미채택) 재구성 → self-improvement.md 삭제 → 변경이력 행
- **완료 기준**: 단일 SSOT에 트리거 테이블·5단계·기록위치 존재, self-improvement.md 제거
- **테스트**: TS-014, TS-015
- **실행 방법**: sub-agent
- **의존**: 없음

#### Step 4: dangling 참조 + 명명 정리 (opal-pm §5 stub 포함)
- [x] 완료
- **소속 기능**: F-006
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal-pm.md`, `specialist-agent.md`, `agent-guide.md`, `opal/core/AGENT.md`, `oppd SKILL.md`(§561-566만)
- **작업 내용**: §2.6.2 ①④~⑧ 정리 — §5 stub 신규 SSOT 지칭·"개선 루프" 명명 통일. 완료 후 전수 grep 0건(`self-improvement`/구 `pm-learning-loop`)
- **완료 기준**: grep 0건, §5 stub 정합, 지칭 오류 소멸
- **테스트**: TS-016, TS-017
- **실행 방법**: sub-agent
- **의존**: Step 3
- **주의**: oppd SKILL.md는 Step 10과 동일 파일 → §4.3 순차

#### Step 5: opal-improve SKILL.md 작성
- [x] 완료
- **소속 기능**: F-003
- **영역**: 스킬
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-improve/SKILL.md`
- **작업 내용**: frontmatter + 5단계 프로세스(§3.3.2) + 로컬/FW 분류 분기 + improve-tool 호출 계약 + pm-improvement-loop.md SSOT 참조 + 변경이력
- **완료 기준**: 5단계 + 분류 분기 명시
- **테스트**: TS-007
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 3

#### Step 6: registry opim 엔트리 등록
- [x] 완료
- **소속 기능**: F-003
- **영역**: 문서
- **agent**: opal-task-agent
- **파일**: `opal/core/references/opal-skills-registry.json`
- **작업 내용**: `groups.opal`에 §3.3.2 opim 엔트리 추가 (스키마 준수) + changelog 갱신
- **완료 기준**: JSON 유효 + `//opim` 트리거 매칭
- **테스트**: TS-008
- **실행 방법**: sub-agent
- **의존**: Step 5

#### Step 7: opd CLOSE 회고 하드스텝 삽입
- [x] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-dev/SKILL.md` (STEP6 `:247` 직후)
- **작업 내용**: §3.4.2 공통 템플릿 삽입 + 변경이력 행
- **완료 기준**: brain-ingest 직후·완료보고 직전 회고 스텝 존재
- **테스트**: TS-009~011
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 8: opwt CLOSE 회고 하드스텝 삽입
- [x] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-write-tech/SKILL.md` (`:398` 직후)
- **작업 내용**: 동일 템플릿 삽입 + 변경이력
- **완료 기준**: 회고 스텝 존재
- **테스트**: TS-009
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 9: opgc CLOSE 회고 하드스텝 삽입
- [x] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-gc/SKILL.md` (STEP4 `:364` 직후·4.3 직전)
- **작업 내용**: 동일 템플릿 삽입 + 변경이력
- **완료 기준**: 회고 스텝 존재
- **테스트**: TS-009
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 10: oppd CLOSE 회고 하드스텝 삽입
- [x] 완료
- **소속 기능**: F-004
- **영역**: 오케스트레이터
- **agent**: opal-task-agent
- **파일**: `opal/skills/opal-pilot-project-dev/SKILL.md` (`:668` 직후·문서등록 `:672` 직전)
- **작업 내용**: 동일 템플릿 삽입 + 변경이력
- **완료 기준**: 회고 스텝 존재
- **테스트**: TS-009
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5, **Step 4**(동일 파일 순차)

#### Step 11: install-mac.sh 배포 반영
- [x] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install-mac.sh`
- **작업 내용**: §3.5.2 improve-tool chmod 블록(`:1178` 직후) + fw-inbox `mkdir -p`/README seed 블록 + 스크립트 상단 변경이력 주석
- **완료 기준**: install 실행 후 opal-improve·improve-tool·fw-inbox 배포/초기화
- **테스트**: TS-012, TS-013
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 12: windows.ps1 배포 반영
- [x] 완료
- **소속 기능**: F-005
- **영역**: 배치
- **agent**: opal-task-agent
- **파일**: `scripts/install/windows.ps1`
- **작업 내용**: §3.5.2 fw-inbox `New-Item -Force` 블록 (스킬·도구는 자동 복사) + 변경이력 주석
- **완료 기준**: 멱등 초기화 블록 존재
- **테스트**: TS-012
- **실행 방법**: sub-agent
- **의존**: Step 1, Step 5

#### Step 13: docs/PROJECT.md 컴포넌트 등록
- [x] 완료
- **소속 기능**: 문서 (docs/ 갱신 자동 생성)
- **영역**: 문서
- **agent**: PM 직접
- **파일**: `docs/PROJECT.md`
- **작업 내용**: opal-improve(opim) 스킬·improve-tool 도구·fw-inbox를 컴포넌트/문서 테이블에 등록 + 변경이력 행. 필요 시 ARCHITECTURE.md에 개선 루프 서브시스템 1줄
- **완료 기준**: PROJECT.md에 신규 컴포넌트 반영
- **테스트**: 산출물 검사
- **실행 방법**: direct
- **의존**: Step 5, Step 6, Step 11

### 4.3 병렬/순차 판별 근거
| 관계 | 근거 |
|------|------|
| Step 1 → Step 2 | 도구 존재 후 등록 |
| Step 3 → Step 4 | SSOT 확정 후 참조 재지정 (H-3 정리 순서) |
| Step 1·3 → Step 5 | 스킬이 도구·SSOT 참조 |
| Step 5 → Step 6 | 스킬 존재 후 registry 등록 |
| Step 7 ∥ 8 ∥ 9 | 독립 파일(opd/opwt/opgc), 동일 템플릿 |
| Step 4 → Step 10 | **oppd SKILL.md 동일 파일** — 파일 충돌 방지 순차 |
| Step 11 ∥ 12 | mac/windows 독립 파일 |
| (F-006 Step 3·4) ∥ (F-001 Step 1·2) | 문서군 vs 도구군 독립 → Phase1 병렬 |

---

## 5. QA 체크리스트 (기능-QA 매트릭스)

### 5.1 기능별 QA
| F-ID | QA 항목 | TS-ID | Pass 조건 |
|------|---------|-------|----------|
| F-001 | improve-tool JSON 계약·scope 분기 | TS-001~004 | 3경로 `"ok"` 포함, local/fw 분기 정상 |
| F-002 | fw-inbox 항목 자기완결 스키마 | TS-005, TS-006 | host·project·situation·created 전부 존재 |
| F-003 | opal-improve 5단계 + registry | TS-007, TS-008 | 5단계·분류 분기 명시, `//opim` 매칭 |
| F-004 | 4-pilot 회고 하드스텝 일관성·no-op | TS-009~011 | 4 pilot 모두 존재 + 0건 시 CLOSE 비차단 |
| F-005 | install 배포·멱등 | TS-012, TS-013 | 3자산 배포 + 재설치 항목 보존 |
| F-006 | SSOT 통합·dangling 0 | TS-014~017 | 단일 SSOT + grep 0건 + §5 stub 정합 |

### 5.2 회귀 테스트
- [ ] 기존 4 pilot CLOSE(brain-ingest·관련문서·완료보고) 순서·동작 비파괴
- [ ] memory-tool 기존 서브명령 회귀 없음 (위임 호출만 추가)
- [ ] install 기존 배포 자산(스킬/도구 25개) 정상

### 5.3 코드/문서 품질
- [ ] 프로젝트 컨벤션 준수 (@header, JSON `"ok"` 계약, run.sh 표준 골격)
- [ ] 변경이력 기록 (스킬·도구·참조문서·install 스크립트 전부)
- [ ] citation-rules 준수 (설계 근거 인용)

### 5.4 보안
- [ ] improve-tool이 fw-inbox 외 경로에 임의 write 안 함 (경로 화이트리스트)
- [ ] fw-inbox 항목에 시크릿/토큰 하드코딩 방지 (본문은 제안 텍스트만)
- [ ] `~/.opal/` 직접 편집 금지 준수 (fw-inbox는 improve-tool 경유 write만)

---

## 6. 복잡도 판별
| 기준 | 값 | 판정 |
|------|---|------|
| Step 수 | 13개 | 복잡 |
| 변경 파일 수 | 신규 4 + 수정 11 ≈ 15개 | 복잡 |
| 모듈 범위 | 도구·스킬·오케스트레이터·참조문서·install | 복잡(다중) |
| 작업 유형 | 신규 도구+스킬 개발 + 대규모 개선 | 복잡 |
| 외부 의존성 | 신규 도구(improve-tool) — 단 stdlib만 | 복잡 |
| **실행 모드** | **복잡** | |

---

## 7. 실행 아키텍처 (복잡 모드)

### C-1. 에이전트 토폴로지
전 Step **opal-task-agent(공통/Framework)** 배정 — FE/BE/DB 분리 없음(Console 무관). 파일 충돌 방지 그룹핑:
- **Batch 1 (병렬)**: {A그룹: Step 1→2 (improve-tool)} ∥ {B그룹: Step 3→4 (SSOT 문서)}
- **Batch 2 (병렬, Batch1 후)**: {C그룹: Step 5→6 (opal-improve)} ∥ {D그룹: Step 7∥8∥9 (opd/opwt/opgc)}
- **Batch 3**: Step 10 (oppd — D그룹 회고 + B그룹 Step4 완료 후, 동일 파일 순차)
- **Batch 4 (병렬)**: Step 11 ∥ 12 (install mac/win)
- **Batch 5**: Step 13 (PM 직접 docs/)

> 파일 충돌 주의: oppd SKILL.md는 Step 4(§561-566)와 Step 10(§668)이 동일 파일 → 반드시 순차(같은 에이전트 세션 권장).

### C-2. 스킬 요구사항
- 신규 스킬 1개: opal-improve (F-003). 기존 스킬 매칭 없음(개선 루프 전용).
- 3개 이상 Step 동일 패턴(회고 스텝 4 pilot) → 공통 템플릿(§3.4.2)으로 인라인 지침화(별도 스킬화 불필요 — 오케스트레이터 인라인 스텝).

### C-3. 도구 요구사항
- 신규 CLI: improve-tool (run.sh + python, stdlib). venv 재사용, requirements.txt 불변.
- 재사용: memory-tool(로컬 위임), state-tool(궤적 신호 소스는 STATE.md).
- MCP: 없음.

### C-4. 테스트 전략
- **기능 테스트**: improve-tool dry-run (`record --scope fw/local`, list, show) — JSON `"ok"`·파일 산출 확인.
- **회귀 테스트**: 4 pilot CLOSE 순서 비파괴, install 기존 자산 배포.
- **정적 검증**: dangling grep 0건, registry JSON 유효성, frontmatter 필수키.
- **멱등 테스트**: install 2회 실행 후 fw-inbox 항목 보존.
- TEST-SCENARIO.md는 opal-pilot-dev STEP 3.5에서 PM이 위 H-1~H-9·TS-001~017 기반으로 별도 작성.

---

## 8. 기술 컨텍스트

### 8.1 기술 스택
| 영역 | 기술 | 적용 스킬 |
|------|------|----------|
| 스킬·참조문서 | Markdown, YAML frontmatter | opal-skill-creator(필요 시) |
| 도구 | Python 3(stdlib) + Bash run.sh | 기존 도구 패턴 답습 |
| registry | JSON | - |
| install | Bash(mac) + PowerShell(win) | - |

### 8.2 사용 MCP
| MCP | 조회 결과 요약 |
|-----|--------------|
| (없음) | 외부 API 미사용 — 전부 로컬 파일/도구 |

### 8.3 참조 문서 (설계 결정 근거)
| # | 유형 | 문서/사이트 | 경로/URL | 참조 이유 |
|---|------|-----------|---------|----------|
| D-1 | 기획 | TASK.md | `tasks/058-260713-opd-학습루프-도구화-개선수집/TASK.md` | R1~R6·확정방향·제약 SSOT |
| D-2 | 기획 | ANALYSIS.md | `tasks/058-.../ANALYSIS.md` | 현황 사실·리스크 |
| D-3 | 설계 | op-brain-ingest SKILL | `opal/skills/op-brain-ingest/SKILL.md` | 답습 모델(CLOSE 훅·no-op 안전 `:281`) |
| D-4 | 소스 | opd CLOSE | `opal/skills/opal-pilot-dev/SKILL.md:230-262` | 회고 삽입 지점(`:247` 직후) |
| D-5 | 소스 | opwt CLOSE | `opal/skills/opal-pilot-write-tech/SKILL.md:377-410` | 삽입 지점(`:398` 직후) |
| D-6 | 소스 | opgc CLOSE | `opal/skills/opal-pilot-gc/SKILL.md:324-365` | 삽입 지점(`:364` 직후) |
| D-7 | 소스 | oppd CLOSE/brain-ingest | `opal/skills/opal-pilot-project-dev/SKILL.md:631-668` | 삽입 지점(`:668` 직후) + §561-566 지칭 |
| D-8 | 설계 | pm-learning-loop.md | `opal/core/references/harness/pm-learning-loop.md` | rename+SSOT 본문화 원본 |
| D-9 | 설계 | self-improvement.md | `opal/core/references/pm/self-improvement.md` | 삭제·내용 흡수 원본(5단계·기록위치·제한) |
| D-10 | 설계 | opal-pm.md §5 | `opal/core/references/opal-pm.md:71-76,344` | §5 stub 갱신·changelog |
| D-11 | 소스 | brain-tool run.sh | `opal/tools/brain-tool/run.sh:1-12` | run.sh 표준 골격 |
| D-12 | 소스 | state-tool run.sh | `opal/tools/state-tool/run.sh:1-12` | run.sh 표준 골격 |
| D-13 | 소스 | memory_tool.py | `opal/tools/memory-tool/memory_tool.py:1202-1261` | append 위임 시그니처 |
| D-14 | 소스 | skills registry | `opal/core/references/opal-skills-registry.json:101-116` | 엔트리 스키마·opal 그룹 |
| D-15 | 소스 | install-mac.sh | `scripts/install-mac.sh:1058-1178,1035` | 스킬/도구 자동배포·chmod·clean_dirs |
| D-16 | 소스 | windows.ps1 | `scripts/install/windows.ps1:433,482-548` | 스킬/도구 복사·cleanDirs |
| D-17 | 설계 | CONVENTIONS.md | `docs/CONVENTIONS.md:153-209` | Guards/도구/배포경계/@header/변경이력/State |
| D-18 | 소스 | tools.md | `opal/core/references/tools.md` | 도구 레지스트리 등록 대상 |
| D-19 | 소스 | dangling 참조 | `specialist-agent.md:69`, `agent-guide.md:135/148`, `AGENT.md:35` | 명명·지칭 정리 대상 |
| D-20 | 기획 | PROJECT.md | `docs/PROJECT.md` | 컴포넌트 등록 대상 |

> **[MUST] 인용 (CONVENTIONS §구현 규칙)**:
> - `docs/CONVENTIONS.md` §도구 우선 원칙: "직접 코드를 작성하기 전에 OPAL 도구를 우선 검토한다" (`:189-193`)
> - `docs/CONVENTIONS.md` §배포 경계: "~/.opal/ 배포 파일을 직접 편집하지 않는다. 변경은 항상 프로젝트 소스에서 수행한다" (`:201-204`)
> - `docs/CONVENTIONS.md` §변경이력 작성 의무: "스킬·에이전트·참조 문서를 변경하면 '## 변경이력' 표에 행을 추가한다" (`:195-198`)
> - `docs/CONVENTIONS.md` §State 관리: "STATE.md 행 상태 변경은 state-tool로만 수행한다. 표 직접 편집 금지" (`:185-187`)
> - `docs/CONVENTIONS.md` §플랫폼 분기 격리: "스킬·에이전트 본문에 플랫폼 조건문을 추가하지 않는다" (`:206-209`) — hook 미채택·플랫폼 독립 원칙과 정합

---

## 9. 리스크 및 대응 (기능-리스크 연결)
| # | 리스크 | 관련 F | 영향 | 대응 |
|---|--------|--------|------|------|
| R-1 | 회고 스텝 CLOSE 차단 | F-004 | P0 | no-op 안전 [MUST] 명문화, brain-ingest 패턴 답습 (H-1/TS-011) |
| R-2 | 로컬/FW 오분류 | F-001,F-003 | P0 | scope 명시 필수 인자, 분류 기준 SSOT 테이블 (H-2/TS-006) |
| R-3 | install 멱등성 위반 | F-005 | P0 | fw-inbox clean_dirs 제외 + mkdir -p only (H-5/TS-013) |
| R-4 | dangling 잔존 | F-006 | P1 | 정리 순서 강제 + 전수 grep 0건 게이트 (H-3/TS-016) |
| R-5 | 4-pilot 삽입 누락 | F-004 | P1 | 공통 템플릿 + 4파일 대칭 grep (H-7/TS-009) |
| R-6 | oppd 동일파일 충돌 | F-004,F-006 | P1 | Step 4→10 순차, 같은 에이전트 세션 (§4.3) |
| R-7 | fw-inbox 스키마 불완전 | F-002 | P1 | 출처 메타 4종 frontmatter 필수키 (H-8/TS-005) |
| R-8 | memory-tool 위임 실패 | F-001 | P2 | MEMORY.md 부재 graceful skip (H-6/TS-004) |

---

## 변경이력
| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-13 | 초기 작성 — R1~R6 6기능 청사진. oppd brain-ingest 훅 `:660-668` 실 Read 확정(ANALYSIS 761 정정), dangling 참조 전수 grep 확정(경로 2건+명명 5건), improve-tool 서브명령/scope 분기·fw-inbox 스키마·회고 하드스텝 계약·install 삽입지점 확정. 복잡 모드 13 Step (058) |
