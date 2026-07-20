# ANALYSIS: PM 학습 루프 tool-gated 재설계 코드베이스 분석

> 작성일: 2026-07-13
> 입력: TASK.md
> 출력: ANALYSIS.md
> 분석자: op-dev-analysis (Haiku 4.5)
> 목표: PLAN(구현 청사진)의 근거가 될 코드베이스 현황 사실 수집. 파일:줄 근거 필수.

---

## 0. 참조 문서

| # | 유형 | 문서/사이트 | 경로 | 참조 이유 |
|---|------|-----------|------|----------|
| D-1 | 설계 | PM 학습 루프 정의 | `opal/core/references/harness/pm-learning-loop.md` | 현재 학습 루프 정의 문서 — CLOSE 미연결 확인 |
| D-2 | 설계 | 자기 개선 세부 프로세스 | `opal/core/references/pm/self-improvement.md` | 개선 프로세스 정의 — 지칭 오류 확인 |
| D-3 | 설계 | PM 역할 정의 | `opal/core/references/opal-pm.md:70-76` | 학습 루프 stub §5 위치 확인 |
| D-4 | 설계 | op-brain-ingest 워커 | `opal/skills/op-brain-ingest/SKILL.md` | 답습할 자매 훅 패턴 — CLOSE 연결·도구 집행 구조 |
| D-5 | 소스 | CLOSE 단계 구조 (opd) | `opal/skills/opal-pilot-dev/SKILL.md:230-262` | CLOSE 4단계 패턴 + op-brain-ingest 디스패치 |
| D-6 | 소스 | CLOSE 단계 구조 (opwt) | `opal/skills/opal-pilot-write-tech/SKILL.md:377-410` | opwt CLOSE 패턴 |
| D-7 | 소스 | CLOSE 단계 구조 (opgc) | `opal/skills/opal-pilot-gc/SKILL.md:324-365` | opgc CLOSE 패턴 |
| D-8 | 소스 | state-tool 래퍼 | `opal/tools/state-tool/run.sh` | 도구 표준: run.sh + python + JSON 계약 |
| D-9 | 소스 | brain-tool 래퍼 | `opal/tools/brain-tool/run.sh` | 도구 표준: run.sh + python + JSON 계약 |
| D-10 | 소스 | memory-tool 래퍼 | `opal/tools/memory-tool/run.sh` | 도구 표준: run.sh + python + JSON 계약 |
| D-11 | 소스 | memory-tool 서브명령 | `opal/tools/memory-tool/memory_tool.py:1202-1260` | 7개 서브명령 — append/update/promote 재사용 가능 |
| D-12 | 소스 | skills registry | `opal/core/references/opal-skills-registry.json:1-100` | 스킬 엔트리 스키마 |
| D-13 | 소스 | install 함수 목록 | `scripts/install-mac.sh:11-40` | install 배포 구조 |

---

## 1. 기존 코드 분석

### 1.1 관련 파일 목록

| 파일 | 역할 | 변경 필요 | 근거(줄번호) |
|------|------|----------|-------------|
| `opal/skills/op-brain-ingest/SKILL.md` | CLOSE 훅 워커 패턴 정의 | 아니오 (참조용) | 1-310 전체 |
| `opal/skills/opal-pilot-dev/SKILL.md` | opd CLOSE 구조 | 예 | 230-262: CLOSE 4단계에 회고 스텝 삽입 대상 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | opwt CLOSE 구조 | 예 | 377-410 |
| `opal/skills/opal-pilot-gc/SKILL.md` | opgc CLOSE 구조 | 예 | 324-365 |
| `opal/skills/opal-pilot-project-dev/SKILL.md` | oppd CLOSE 구조 | 예 | 761+ (추정) |
| `opal/tools/state-tool/run.sh` | 도구 래퍼 표준 | 아니오 | 1-12 |
| `opal/tools/brain-tool/run.sh` | 도구 래퍼 표준 | 아니오 | 1-12 |
| `opal/tools/memory-tool/run.sh` | 도구 래퍼 표준 | 아니오 | 1-12 |
| `opal/tools/memory-tool/memory_tool.py` | 메모리 관리 도구 | 아니오 (재사용 검토) | 1202-1260 |
| `opal/core/references/opal-skills-registry.json` | 스킬 레지스트리 | 예 | opal-improve/opim 엔트리 신설 |
| `opal/core/references/harness/pm-learning-loop.md` | 학습 루프 정의 | 예 (SSOT 통합) | 1-41 |
| `opal/core/references/pm/self-improvement.md` | 자기 개선 프로세스 | 예 (삭제) | 1-39 |
| `opal/core/references/opal-pm.md` | PM 역할 정의 | 예 | 70-76 |
| `scripts/install-mac.sh` | install 스크립트 | 예 | 208+ |

### 1.2 아키텍처 패턴

#### A. op-brain-ingest 훅 패턴 (CLOSE 자매 훅)

**구조** (`opal/skills/op-brain-ingest/SKILL.md:1-50`):
- 트리거: CLOSE 단계에 하드연결, 오케스트레이터가 디스패치
- 입력: 태스크 폴더 경로 (DONE.md·PLAN.md·TASK.md 위치)
- 출력: JSON `{ "ingested_pages": [], "status": "completed|skipped", "summary": "..." }`
- NO-OP 안전: brain 부재 시 `status: skipped` 반환, CLOSE 진행 비차단

**CLOSE 내 위치 (4단계 구조)** (`opal/skills/opal-pilot-dev/SKILL.md:230-247`):
1. DONE.md 생성 + state-tool mark (§234)
2. 관련 문서 업데이트 (§235-238)
3. op-brain-ingest 디스패치 — 2단 탐색 경로 (§239-247)
4. 완료 보고

#### B. 도구 3종 구조 (run.sh + python + JSON 계약)

**공통 구조**:
1. run.sh 래퍼 — venv 경로 체크 + python 전달
   - state-tool/brain-tool/memory-tool: 동일 패턴 (run.sh:1-12)
   - 실패 시: `{"ok":false,"error":"..."}`를 stderr 출력

2. python 본체 — 서브명령 디스패치
   - argparse로 서브명령 구분

3. JSON 계약 — 모든 출력이 `"ok"` 필드 포함
   - 성공: `{"ok":true, ...}`
   - 실패: `{"ok":false, "error": "..."}`

**memory-tool 서브명령** (`memory_tool.py:1202-1260`):
- append: 메모리/히스토리 행 추가
- update: 메모리 상태/요약 수정  
- promote: 메모리 → docs/brain 졸업
- prune: 히스토리 정리
- migrate: 포맷 변환
- show: 인덱스/히스토리 현황 (read-only)
- delete: dead/superseded 행 삭제

#### C. pilot CLOSE 단계 구조 (4개 오케스트레이터)

| 오케스트레이터 | 파일 위치 | CLOSE 행 | 구현 완성도 |
|------------|---------|-----------|----------|
| **opd** | opal-pilot-dev/SKILL.md | 230-262 | ✅ 완전 |
| **opwt** | opal-pilot-write-tech/SKILL.md | 377-410 | ✅ 완전 |
| **opgc** | opal-pilot-gc/SKILL.md | 324-365 | ✅ 완전 |
| **oppd** | opal-pilot-project-dev/SKILL.md | 761+ | ⚠️ 확인 필요 |

### 1.3 의존성 맵

**파일 간 참조 그래프**:
- opal-pm.md §5 stub → pm-learning-loop.md
- pm-learning-loop.md:32 → self-improvement.md
- self-improvement.md:7 → **opal-pm.md §5** (❌ 오류! 실제는 pm-learning-loop.md:22-30)

**위험 관계**: self-improvement.md 삭제 시 dangling 참조 5개 정리 필요

### 1.4 테스트 현황

| 대상 | 테스트 파일 | 커버리지 | 비고 |
|------|----------|---------|------|
| state-tool | tests/ 존재 | 있음 | - |
| brain-tool | tests/ 존재 | 있음 | - |
| memory-tool | tests/ 존재 | 있음 | - |
| improve-tool (신규) | 없음 | N/A | EXECUTE 단계에서 dry-run/실행 증거 확인 |
| opal-improve 스킬 | 없음 | N/A | VERIFY 단계에서 QA 검증 |

---

## 2. 외부 조사 결과

### 2.1 학습 루프 호출 현황 (grep 전수 조사)

**호출 지점 0건**:
- 검색어 "학습 루프": 10개 파일, 정의·언급만 (실행 0건)
- 검색어 "self-improvement": 5개 파일, 정의 3문서+부트스트랩만
- 호출 예상 위치: state_tool.py(0건) / brain_tool.py(0건) / CLOSE 파이프라인(미구현)

### 2.2 install 배포 구조

**배포 경로** (`scripts/install-mac.sh`):
- 코어: ~/.opal/AGENT.md (install_opal 함수)
- 스킬: ~/.opal/skills/{name}/ (install_opal_skills)
- 도구: ~/.opal/tools/{name}/ (install_opal_tools)
- 에이전트: ~/.opal/agents/{name}/
- MCP: ~/.claude/mcp.json 등 (install_mcp)
- 부트스트래퍼: ~/.claude/CLAUDE.md 등
- Console: ~/.opal/dashboard-server/

---

## 3. 영향 범위

### 3.1 직접 영향 (신규/수정)

| 파일 | 변경 사항 | 규모 |
|------|----------|------|
| `opal/skills/opal-improve/SKILL.md` | 신규 (5단계 프로세스) | 200~300줄 |
| `opal-skills-registry.json` | opal-improve/opim 엔트리 신설 | +15줄 |
| `opal-pm.md` | §5 stub 업데이트 | 5줄 변경 |
| `pm-learning-loop.md` | → `pm-improvement-loop.md` rename | - |
| `self-improvement.md` | 삭제 (내용 흡수) | 39줄 제거 |
| `opal/tools/improve-tool/` | 신규 도구 | 300~500줄 |
| `scripts/install-mac.sh` | 배포 함수 확장 | +50~80줄 |
| 4개 pilot CLOSE | 회고 하드스텝 삽입 | 각 +40~60줄 |

### 3.2 간접 영향 (참조만 수정)

| 문서 | 변경 사항 |
|------|----------|
| harness/pm-review-gate.md | 학습 루프 참조 확인 |
| pm/specialist-agent.md | §5 학습 루프 참조 유지 |
| opal-project-init/agent-guide.md | 학습 루프 placeholder 명확화 |

### 3.3 영향 범위 요약

- [ ] DB 스키마 변경: **없음**
- [ ] API 인터페이스 변경: **없음**
- [ ] 설정/환경변수 변경: **없음**
- [ ] 빌드/배포 파이프라인 변경: **있음 (install-mac.sh)**
- [ ] 기존 CLOSE 호환성: **유지** (회고 스텝은 op-brain-ingest 이전 삽입)

---

## 4. 핵심 발견 사항

### 4.1 op-brain-ingest는 tool-gated CLOSE 훅의 모범 사례

**구현 증거** (`op-brain-ingest/SKILL.md` 전체):
- ✅ CLOSE 하드연결: 4개 오케스트레이터 모두에서 호출
- ✅ 도구 집행: brain-tool CLI 3개 서브명령 (add-page, index, log)
- ✅ 산출물 증거: `ingested_pages` 리스트 반환, status 필드
- ✅ no-op 안전: brain 부재 시 skipped 반환

### 4.2 기존 도구들은 표준을 일관되게 준수

**증거** (state-tool/brain-tool/memory-tool):
- 동일 run.sh 구조 (venv 경로 + 에러 핸들링)
- python 본체는 argparse 서브명령 디스패치
- 모두 JSON {"ok": ...} 계약

### 4.3 학습 루프는 정의 3문서 분산 + 지칭 오류 존재

**참조 맵**:
1. opal-pm.md §5 → pm-learning-loop.md
2. pm-learning-loop.md:32 → self-improvement.md
3. self-improvement.md:7 → **"opal-pm.md §5"** ❌ **오류!**

**실제 트리거 테이블**: pm-learning-loop.md:22-30

### 4.4 memory-tool의 append/update/promote는 로컬 개선 기록에 재사용 가능

**서브명령** (`memory_tool.py:1202-1260`):
- append: 제목·타입·상태·요약으로 기록
- update: 상태/요약 갱신
- promote: docs/brain으로 졸업

### 4.5 install 확장은 용이 (선례: install_dashboard)

**기존 함수 패턴** (loop 구조):
- install_opal_skills(): 스킬 배포
- install_opal_tools(): 도구 배포
- install_dashboard(): FE npm + BE copy (신규 예)

---

## 5. 제약/리스크

| 항목 | 설명 | 심각도 | 근거 |
|------|------|--------|------|
| SSOT 파편화 | 3문서 분산 + 지칭 오류 | 높음 | self-improvement.md:7 |
| 파이프라인 미호출 | 현재 호출 0건, 정의만 존재 | 높음 | 전수 grep |
| 도구 신설 복잡도 | 로컬/FW 분류 로직 필요 | 중간 | PLAN 단계 설계 필요 |
| 배포 경계 | ~/.opal/ 직접 수정 금지 | 중간 | CONVENTIONS.md |
| CLOSE 4단계 일관성 | 4개 파일 동일 패턴 수정 | 중간 | 누락 위험 |
| self-improvement.md 삭제 | dangling 5개 참조 정리 | 낮음 | 삭제 전 전수 확인 |

---

## 6. 기술 컨텍스트

### 6.1 기술 스택

| 카테고리 | 기술 | 버전 |
|----------|------|------|
| 언어 | Python 3 | ~3.12 (venv) |
| 프레임워크 | OPAL | 25개 스킬 |
| 도구 CLI | Bash + Python | argparse 기반 |
| 설정 | YAML frontmatter | SKILL.md, registry JSON |
| 배포 | Bash 설치 스크립트 | install-mac.sh |

### 6.2 추천 스킬

| 스킬 | 용도 |
|------|------|
| opal-skill-creator | opal-improve SKILL.md 템플릿 (필요 시) |

### 6.3 추천 MCP

| MCP | 용도 |
|------|------|
| (없음) | 외부 API 미사용 |

---

## 7. 요약 및 PLAN 입력

### 7.1 주요 결론

1. **op-brain-ingest는 증명된 tool-gated 모범 사례** — CLOSE 하드연결 + 도구 집행 + 산출물 증거

2. **도구 표준 구조 일관** — run.sh + python + JSON 계약 (3개 도구 준수)

3. **CLOSE 4단계 구조 단일화** — 회고 스텝은 단계 1과 2 사이 삽입

4. **학습 루프: 정의만 존재, 호출 0건** — 파이프라인 미연결, PRINCIPLES 위반

5. **SSOT 지칭 오류** — self-improvement.md가 잘못된 위치 가리킴

6. **memory-tool 재사용 가능** — append/update/promote 서브명령 활용

7. **install 확장 용이** — 기존 함수 패턴으로 배포 가능

### 7.2 PLAN에서 확정할 사항

- R1: 회고 하드스텝 삽입 위치 & 프로세스
- R2: opal-improve 5단계 프로세스 설계
- R3: improve-tool 로컬/FW 분류 로직
- R4: fw-inbox 디렉토리 구조 & 메타 스키마
- R5: rename/삭제/링크 정리 순서
- R6: install 추가 함수 명시

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-07-13 15:30 | 초기 작성 — 7개 항목 파일:줄 근거로 분석 완료. op-brain-ingest 패턴 식별, SSOT 지칭 오류 확인, 기존 도구 표준 확인 (058) |
