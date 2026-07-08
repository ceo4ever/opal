# DONE: OPAL Project Brain 지능화 — opal-wiki-pilot 완성

> 완료일: 2026-06-11 21:43 | 적용 스킬: opp | 모드: agentic (semi-agentic에서 18:59 전환)
> 산출물: TASK.md / PLAN.md / AGENTIC-LOG.md / GC-CONVENTION-20260611-1950.md / DONE.md

## 완료 요약

015 brain 코어를 opal-wiki-pilot 비전으로 지능화했다. init이 origin을 분석해 구조를 제안하고(W1), ingest --all이 문서 전체를 적재하며(W2), tasks/가 3계층 장기기억으로 검색되고(W3), PM 판단 ingest(W4)·on-demand search 선택 주입(W5)이 규칙화되었으며, 7 pilot CLOSE 확산(W6)과 install 배포·이름·git 정책(W7)까지 완료. 캡틴 실사용 테스트(ingest --all 멱등·ask 질의)로 동작을 실증했다.

## 요구사항 달성 (W1~W7 전부 ✅)

| W | 결과 | 증거 |
|---|------|------|
| W1 init 동적 구조 제안 | brain-tool 타입 SCHEMA §1.5 동적 로드(`load_page_types`+`DEFAULT_PAGE_TYPES` 폴백) + `analyze` 신설 + `init --types` + SKILL init STEP 0 | pytest 83 passed (기존 66 회귀 0 + 신규 17) |
| W2 ingest --all 문서 전체 | `ingest-scan` 신설(docs/skills/tasks 멱등 목록) + SKILL ingest 확장(M-2: 3~6줄 요약+포인터) | dogfooding 49페이지 + 재실행 시 skip 49 실증 |
| W3 tasks 장기기억 3계층 | SCHEMA 3계층 명문화 + `ingest task:NNN` + 001~015 선별 백필 9건(`task:NNN` drill-down) | search "codex" → 후보 2건 + task:009 링크 실재 |
| W4 PM 판단 ingest | AGENT.md v3.2 — 가치 지식 감지 시 ingest, agentic 자율/그 외 제안 | opal/core/AGENT.md 활용 규칙 |
| W5 search 선택 주입 + index 비상주 | search=후보 목록만(본문 X)→선택 페이지만 주입. 부트스트랩 index 자동 로드 제거 | AGENT.md·dispatch-process v1.3·SKILL query 3문서 일관 + ask 실사용 검증 |
| W6 7 pilot CLOSE 확산 | opd/opds/opdw/opwt/oppd/opsdd/opgc에 op-brain-ingest 훅 | rows_count 전건 불변(15/10/9/10/Phase3/24/7) |
| W7 배포·이름·git | install 실행(`//opbr` 매칭 검증) + **opal-brain 유지(M-4)** + **brain만 git 예외 추적(M-5)** | 배포 4종 동작 증거 + git check-ignore 증거 |

## 확정 의사결정 (PLAN §0 — agentic PM 대행, 캡틴 사후 확인 완료)

- M-1: init 정량 기준 = brain-tool `analyze`(결정론 집계) + LLM 큐레이션
- M-2: ingest 깊이 = 섹션 요약 3~6줄 + `file_path` 포인터 (본문 복제 금지)
- M-3: 백필 = 선별(op-brain-ingest 포함/제외 기준 재사용) — 9건 적재, 3건 제외(trivial 1·DONE 없음 2)
- M-4: 이름 = **opal-brain 유지** ("opal-wiki-pilot"=비전 용어, 설계 SSOT §13 명문화)
- M-5: git = **brain만 예외 추적** (`.opal/*` + `!.opal/brain/`, code-scan.json 계속 무시)

## 변경 파일

| 영역 | 파일 |
|------|------|
| 도구 | `opal/tools/brain-tool/brain_tool.py`(8→10 서브명령) / `tests/test_brain_tool.py`(66→83) / `templates/schema-template.md`(§1.5 타입 SSOT + 3계층) |
| 스킬 | `opal/skills/opal-brain/SKILL.md`(v1.1 4모드 지능화 + v1.2 source_ref [MUST]) / `op-brain-ingest/SKILL.md`(v1.1) |
| PM 규칙 | `opal/core/AGENT.md`(v3.2) / `opal/core/references/pm/dispatch-process.md`(v1.3) |
| 7 pilot | `opal-pilot-{dev,dev-short,dev-wireframe,write-tech,project-dev,sdd,gc}/SKILL.md` CLOSE 훅 |
| 정책·문서 | `.gitignore`(brain 예외) / `docs/proposals/opal-brain-design.md`(v2.0) |
| brain 자산 | `.opal/brain/` 3→50페이지 (docs 5 + skills 32 + 백필 9 + synthesis 1 + 시드 3) |

## 검증 증거 (헌법 §4 — 동작 증거)

- pytest 83 passed (PM 독립 재실행 포함, 회귀 0)
- brain validate violations 0 / lint issues 0 (orphan 35건 → 링크 패스 해소)
- install 배포 후 4종 검증: brain-tool validate·analyze 인식·`//opbr` 레지스트리 매칭·스킬 배포 존재
- git check-ignore: `.opal/brain/index.md` 추적 / `.opal/code-scan.json` 무시
- 캡틴 실사용: `//opbr ingest --all` 멱등(skip 49/pending 6 정당 제외) + `//opbr ask` 후보→선택→합성 + synthesis 파일링
- 컨벤션 자동 진단: Critical/High 0 (GC-CONVENTION-20260611-1950.md)

## 테스트 중 발견·해소 결함

- **source_ref 형식 불일치** (AGENTIC-LOG #17~18): dogfooding 워커가 `--sources`를 전체 경로로 기록 → ingest-scan 멱등 기준(`skill:<폴더명>`)과 불일치. 32페이지 정정 + SKILL v1.2에 [MUST] 형식 규칙 명시 + 재배포로 재발 방지 (추가작업 행 9).

## 잔여·후속 후보

1. 컨벤션 Medium/Low 2건 정리 — 테스트 섹션 주석 번호(`# 14`→`# 13`), `__import__("yaml")` → 상단 import (GC 보고서 참조)
2. 에이전트 정의 model 레벨명(`standard` 등)이 플랫폼 서브에이전트 디스패치에서 미해석 — install 어댑터는 변환하나 세션 내 Agent 도구 호출 시 수동 오버라이드 필요 (AGENTIC-LOG #15)
3. brain git merge 전략 (멀티PC 동시 ingest 충돌 — 설계 §R2 후속)
4. search 다중 단어 질의가 AND 매칭으로 0건 빈발 — 토크나이즈/OR 스코어링 개선 검토
5. 미커밋 상태 — 캡틴 지시 시 커밋 (브랜치 `feat/opal-brain-wiki`)
