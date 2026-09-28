# 검증 증거

## V-1 관련 문서 누락 감사

- `docs/PROJECT.md`의 프로젝트 구성·문서 레지스트리와 변경 표면을 대조했다.
- `scripts/`, `opal/`, `docs/`, 루트 README에서 `opal-self-pm`, `knowledge-sync`, `knowledge_impact`, `PROJECT`, `지식 동기화`를 역검색했다.
- 후보별 update/no-op과 확인 결과는 `project-document-audit.md`에 기록했다.
- 판정: 기존 PROJECT 단독 선별은 완전성 증거가 아니었으며, 변경 표면·소비자 역추적과 경로별 폐쇄표를 추가해 보완했다.

## V-2 정적 계약 검사

- 검사 파일: `SKILL.md`, `question-loop.md`, `knowledge-sync.md`, README, `docs/PROJECT.md`
- 검사 문구 20건:
  - 초기 영향 후보 집합 승계
  - 실행 중 새 범위만 증분 보강
  - 종료 시 전체 재탐색 금지와 최종 변경 정합
  - PROJECT 라우팅 인덱스와 직접 소비자·참조자 역추적
  - 경로별 후보 폐쇄 증거
  - 선택 경로·패턴 실재 확인과 코드↔문서 별칭 매핑 근거
  - owner SSOT만으로 brain no-op 금지
  - `knowledge_impact` 전체 교체
  - 수정 의견을 최종 확인으로 해석하지 않음
- 결과: 5 files, 20 phrases, missing 0 — PASS

## V-3 도구 회귀 테스트

```bash
~/.opal/.venv/bin/python -m pytest opal/tools/self-pm-tool/tests/test_self_pm_tool.py -q
```

- 결과: 6 passed
- 의미: 문서가 요구하는 `--set-field` 전체 교체가 기존 CLI 계약에서 정상 동작한다.

## V-4 code-scan·diff

- `git diff --check`: PASS
- `code-scan validate --changed`:
  - `ok: true`
  - `newly_uncovered: 0`
  - `pre_existing: 3` (`opal-self-pm/README.md`, `docs/PROJECT.md`, brain entity)
- 판정: 신규 구조 위반 없음.

## V-5 Brain 동기화

- `brain-tool update-page pages/entity/opal-self-pm.md` 성공
- sources에 `task:166` 추가, WHY·PROJECT 한계·현재 판정 스냅샷 원칙 반영
- `brain-tool index`: 382 pages scanned
- `brain-tool search 'PROJECT 라우팅'`: `opal-self-pm` 반환
- 전체 lint 기존 이슈 321건 중 대상 `opal-self-pm` 이슈 0건
- `brain-tool log --op ingest`: 성공
- 판정: PASS

## V-6 실행 로그

- 중간 `run-log-tool validate-run`: 2 events, violations 0 — PASS
- 최종 확인 전 사건 추가 후 재검증한다.

## V-7 pug 읽기 전용 가상 실행

- 대상: `/Volumes/Data/StoreLinkStudio/pug`
- 입력 사례: 태스크 010(문의 담당자 자동 지정), 태스크 015(쇼핑적립 도메인)
- pug 쓰기: 없음
- 결과: PASS WITH FINDINGS
  - PROJECT가 존재하지 않는 `.opal/MEMORY.md`를 선언하고 실제 `MEMORY.json`·Brain을 제대로 반영하지 못함
  - `workspace/frontend_admin`과 `docs/pug/fe-admin` 별칭 매핑이 불명확함
  - 태스크 010의 자동 담당자 정책이 800 운영공통 정책서에 없음
  - 태스크 015의 쇼핑적립이 포인트 정책·IA·사전·논리·물리·DDL에 반영되지 않음
  - Brain은 해당 불일치와 WHY를 이미 부분적으로 보유함
- 보정: PROJECT에서 선택한 경로·패턴의 실재 확인과 코드↔문서 별칭 매핑 근거를 `knowledge-sync.md`에 추가
- 프로세스 보정: 가상 실행처럼 초기 조사에서 확보한 PROJECT·Brain·관련 문서 후보를 TASK에 승계하고, 작업 중 증분과 종료 정합으로 재사용하도록 변경
- 상세: `evidence/pug-virtual-run.md`

## E2E 적용 검토

- 미실행
- 이유: 런타임 코드·API·화면·설치 경로를 바꾸지 않는 operator 규범·지식 문서 변경이다.
- 대체 검증: 문서 후보 역추적, pug 실제 구조 읽기 전용 가상 실행, 정적 계약 검사, self-pm-tool 회귀 테스트, code-scan, Brain 검색·lint.
- 미검증 한계: 다음 실제 oppm 실행에서 PM의 의미 기반 후보 선별 품질은 장기 관측이 필요하다. 텍스트·코드에 드러나지 않는 외부 관계는 절대 완전성을 보장하지 않는다.
