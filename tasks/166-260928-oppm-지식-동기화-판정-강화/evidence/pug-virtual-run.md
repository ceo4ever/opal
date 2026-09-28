# pug 프로젝트 기준 oppm 가상 실행

## 범위와 안전

- 대상: `/Volumes/Data/StoreLinkStudio/pug`
- 방식: 읽기 전용 가상 실행. pug 파일·상태·Brain에는 쓰지 않았다.
- 입력 사례:
  1. 태스크 010 — `frontend_admin`의 문의 답변 시 담당자 자동 지정
  2. 태스크 015 — 백엔드 쇼핑적립(affiliate) 도메인·포인트 상태·DB·배치 신설
- 목적: 새 `knowledge-sync.md` 절차가 PROJECT 단독 선별의 누락을 실제 프로젝트에서 드러내는지 확인

## PROJECT 라우팅 무결성 사전검사

| 관측 | 결과 | 새 절차의 판정 |
|---|---|---|
| PROJECT 구조맵은 `.opal/MEMORY.md`를 선언 | 해당 파일은 없고 `.opal/MEMORY.json`만 존재 | PROJECT update 후보. 깨진 경로를 no-op 근거로 사용 금지 |
| 실제 `.opal/brain/` 존재 | PROJECT 문서 표에는 Brain 미등재 | 8영역 brain 검사와 실제 구성 대조로 후보에 포함 |
| 코드 경로 `workspace/frontend_admin` | 문서 폴더는 `docs/pug/fe-admin` | 별칭 매핑 근거 없이는 PROJECT 패턴만으로 자동 연결 불가. 역검색으로 보완 |
| 현재 Phase `초기화 (opi)` | 완료 태스크 15개와 대규모 기능 구현 기록 존재 | 최신성 재검토 후보. 이 가상 실행만으로 새 Phase 값은 결정하지 않음 |

판정: PROJECT를 읽는 것만으로는 누락 없는 선별이 불가능하다. 선택 경로 실재 검사와 변경 표면 역추적이 반드시 필요하다.

## 사례 A — 태스크 010 문의 담당자 자동 지정

### 입력 변화

- 변경: `workspace/frontend_admin/.../InquiryButtons.tsx`
- 의미: 담당자가 비어 있으면 담당자 지정 API 성공 후 답변 API 호출
- 경계: 임시저장·기존 담당자·JP·backend 불변

### 가상 후보 폐쇄

| 후보 | 선별 근거 | 가상 판정 |
|---|---|---|
| `docs/PROJECT.md` | frontend_admin 영역·문서 패턴 | no-op — 컴포넌트·경로 자체는 기존 등재로 충분. 단 `frontend_admin`↔`fe-admin` 별칭 문제는 별도 PROJECT 보정 후보 |
| `docs/ARCHITECTURE.md`·`docs/CONVENTIONS.md` | 개발 작업 시 항상 | no-op — 구조·공통 규칙 불변 |
| `docs/pug/fe-admin/{ARCHITECTURE,CONVENTIONS,GUIDE}.md`·`workspace/frontend_admin/CLAUDE.md` | 영역 문서와 종속 원문 | no-op 또는 영향 확인 — 기능 구현 방식은 owner 코드와 기존 API 조합에 한정 |
| `100.기획/130.정책서/800-운영공통-정책.md` | 문의 담당자·답변 상태의 정책 owner, 역검색 적중 | **update 후보** — 담당자 자동 지정 규칙은 없고 수동 지정·상태 전이만 기술 |
| `100.기획/140.IA/systems/admin.json` | 1:1 문의 관리 화면 역검색 | 검토 후 no-op 가능 — 현재 기능 설명이 답변·담당자 지정을 포괄하지만 자동 순서는 표현하지 않음 |
| `.opal/brain/pages/concept/inquiry-manager-answer-guard.md` | brain 검색 `문의 담당자` 적중 | update/기존 반영 확인 — 비가역성과 호출 순서 WHY가 이미 기록됨. 대상 lint에는 기존 frontmatter 이슈 1건 존재 |
| 직접 소비자 코드 | hook·InfoSection·InquiryButtons·InquiryList 역검색 | 확인 완료 — 단건/목록/임시저장 경계 후보를 분리 가능 |

### 8영역 가상 판정

- 기획: `update` — 800 운영공통 정책에 자동 지정과 실패 시 답변 중단 규칙 반영 필요
- 설계: `no-op` — API·데이터 모델 구조 불변
- 프로젝트 문서: `update` 후보 — `frontend_admin`↔`fe-admin` 별칭 라우팅 보완
- CONVENTIONS: `no-op`
- SECURITY: `no-op`
- brain: `update 또는 existing-WHY no-op` — 기존 페이지가 WHY를 담지만 lint 이슈 해결·확인 필요
- memory: `no-op`
- code-scan: 대상 프로젝트 설정 존재 여부 확인 후 판정; 이번 읽기 전용 실행에서는 미집행

결론: PROJECT만 따르면 정책서 800권을 놓칠 수 있지만, 의미 키워드·소비자 역검색을 합치면 포착한다.

## 사례 B — 태스크 015 쇼핑적립 도메인

### 입력 변화

- 신규 affiliate 도메인·외부 연동·배치 모듈·테이블 3종·공통코드·포인트 상태 2종·실제 지급일
- 회원 정책: 쇼핑적립금, 지급 예정일, 지급/예정 취소/소멸
- 운영·배포·어드민 API와 OUT 경로 1건 혼입

### 가상 후보 폐쇄

| 후보 | 관측 | 가상 판정 |
|---|---|---|
| `docs/pug/backend/ARCHITECTURE.md` | affiliate와 신규 batch 실행 단위 기술 | 기존 update 확인 |
| `docs/pug/backend/CONVENTIONS.md` | `Af` 접두사 규칙 기술 | 기존 update 확인 |
| `workspace/backend/docs/**` | affiliate 관련 9개 문서 적중 | 기존 update 확인 |
| `100.기획/130.정책서/200-포인트-정책.md` | affiliate·쇼핑적립·예정 취소 검색 0건 | **update 필수** |
| `100.기획/140.IA/` | affiliate·쇼핑적립 검색 0건 | **update 여부 결정 필수** — 운영 API·배치 기능 등재 기준 적용 |
| `200.설계/210.사전` | 신규 코드·용어 검색 0건 | **update 필수 후보** |
| `200.설계/230.논리모델링` | 신규 `pug_af_*` 검색 0건 | **update 필수 후보** |
| `200.설계/240.물리모델링/pug.dbml` | 신규 테이블 검색 0건 | **update 필수** |
| `200.설계/250.DDL/pug_mysql.sql` | 신규 테이블 검색 0건 | **update 또는 별도 migration SSOT 연결 결정 필요** |
| Brain affiliate·point 페이지 6종 | 검색 성공, task:015 WHY 존재 | 기존 update 확인. `point-ledger-flow`가 정책서 구버전을 명시해 문서 불일치를 직접 증명 |
| OUT `revup` 경로 | PROJECT Lock과 changed surface 충돌 | 문서 동기화 이전에 범위 위반으로 차단·사용자 보고 |

### 8영역 가상 판정

- 기획: **update** — 포인트 정책과 IA가 현재 구현을 반영하지 않음
- 설계: **update** — 사전·논리·물리·DDL에 신규 도메인/테이블/상태 반영 또는 owner 연결 필요
- 프로젝트 문서: **update 후보** — Brain/MEMORY 경로와 영역 문서 별칭 라우팅 보완
- CONVENTIONS: 기존 `Af` 규칙 update 확인
- SECURITY: 기능 보안 검증은 존재하나 프로젝트 보안 기준의 의미 변경은 없어 `no-op` 가능
- brain: 기존 update 확인, 단 관련 페이지 lint 기존 이슈 존재
- memory: 후속 P-6/P-7/P-8이 다음 세션 주의사항이면 update 후보
- code-scan: 프로젝트 설정 부재 시 근거 있는 no-op

결론: 새 절차는 태스크 015 DONE이 실제로 남긴 P-6(정책서), P-7(IA), P-8(OUT 경로)뿐 아니라 데이터 설계 문서 4계층까지 후보로 끌어낸다. 기존 PROJECT 단독·8영역 산문 판정으로는 이 폐쇄가 강제되지 않았다.

## 종합 판정

- 가상 실행 결과: **PASS WITH FINDINGS**
- 새 절차는 두 실제 사례에서 과거 누락을 후보로 드러냈다.
- 추가로 발견한 절차 결함: PROJECT의 선택 경로가 실제로 존재하는지 확인하는 문장이 부족했다.
- 보정: `knowledge-sync.md`에 경로·패턴 실재 확인과 별칭 매핑 근거를 추가했다.
- 실행 최적화: 위 PROJECT·Brain·정책·설계 후보는 수정 범위 조사 때 한 번 수집해 TASK에 승계하고, 실행 중 새 범위만 보강하며, 종료 시 최종 변경과 정합성만 확인한다. 동일 검색을 완료 직전에 다시 수행하지 않는다.
- 남는 한계: 의미적으로만 연결된 외부 시스템은 자동 완전 탐지가 불가능하다. 따라서 미확인 한계를 기록하고 완료 조건 영향 시 최종 확인을 차단하는 규칙을 유지한다.
