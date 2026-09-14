---
template: sdlc-v2
---
# TEST-SCENARIO: WorkStudio Project Registry

> 입력: [TASK.md](TASK.md), [PLAN.md](PLAN.md) | 작성자: PM

## Setup

- 환경: WorkStudio Node/Electron main 모듈 테스트와 Vitest happy-dom renderer 테스트 환경. registry 저장소에는 실제 사용자 `userData` 대신 테스트별 임시 디렉터리를 주입한다.
- 공통 데이터: 정상 OPAL 프로젝트 폴더, 일반 프로젝트 폴더, 존재하지 않는 경로, 손상 JSON, 지원하지 않는 schema version fixture를 테스트별 격리해 사용한다.
- 대역 사용과 한계: Electron dialog와 renderer preload bridge는 단위 테스트에서 대역을 사용한다. 파일 존재·realpath·원자적 registry 저장·재로드·디스크 비삭제는 실제 임시 파일 시스템으로 검증하며, 대역 결과를 파일 시스템 통합 증거로 간주하지 않는다.
- 실행 조건: `npm --prefix workstudio run test`, `npm --prefix workstudio run typecheck`, `npm --prefix workstudio run lint`, `npm --prefix workstudio run electron:syntax`를 자동 실행한다.

## Scenarios

| ID | 검증 대상 | 조건 | 행동 | 기대 결과 | 방법·환경 | 시점 |
|---|---|---|---|---|---|---|
| S-1 | AC-1, C-1, C-4, H-2 | 비어 있는 임시 userData와 정상 프로젝트 폴더가 있다 | Electron main registry 공개 API로 폴더를 등록하고 registry 인스턴스를 새로 만들어 다시 목록을 읽는다 | versioned JSON이 저장되고 재생성한 인스턴스에서도 동일 id·realPath의 available 항목이 반환되며 renderer 직접 파일 접근은 없다 | Node integration, 실제 임시 파일 시스템 | 구현 전 RED |
| S-2 | AC-2, AC-3, C-1, H-1 | 서로 다른 두 프로젝트와 고정 가능한 접근 시각이 있고 renderer에는 typed preload bridge가 주입된다 | 두 프로젝트를 등록한 뒤 첫 프로젝트를 다시 열고 인트로에서 최근 목록 항목을 선택한다 | 중복 항목 없이 첫 프로젝트의 lastAccessedAt이 갱신되어 맨 앞에 오고, 선택 프로젝트가 현재 workspace와 Files root로 열린다 | Node integration + Vitest component integration | 구현 전 RED |
| S-3 | AC-4, AC-5, C-1, H-3 | 등록 후 원래 폴더를 이동해 registry 경로가 존재하지 않고 대체 폴더가 있다 | 목록을 다시 읽고 missing 항목의 일반 열기를 시도한 뒤 같은 항목 id에 대체 폴더를 선택해 복구한다 | missing 상태와 열기 차단이 표시되고, 복구 후 같은 id가 새 realPath·갱신된 OPAL metadata·available 상태를 가지며 별도 중복 항목은 생기지 않는다 | Node integration + Vitest component integration, 실제 임시 파일 시스템 | 구현 전 RED |
| S-4 | AC-6, C-3 | 등록 프로젝트 폴더 안에 보존 확인용 파일이 있다 | renderer의 목록 제거 동작을 통해 registry 항목을 제거한다 | 목록에서는 항목이 사라지지만 프로젝트 디렉터리와 보존 확인용 파일은 그대로 존재한다 | Node integration + Vitest component integration, 실제 임시 파일 시스템 | 구현 전 RED |
| S-5 | AC-7, C-4, H-2, H-3 | dialog 취소, 동일 realPath 중복 선택, 손상 JSON, 지원하지 않는 schema version 입력을 각각 준비한다 | 각 입력으로 등록 또는 registry load를 수행한다 | 취소는 상태를 바꾸지 않고, 중복은 기존 id 하나만 유지하며, 손상·미지원 데이터는 앱을 종료시키지 않고 빈 목록과 non-fatal recovery signal을 반환하고 원본을 보존한다 | Node integration, 실제 임시 파일 시스템 | 구현 전 RED |
| S-6 | AC-8, C-2, C-5, H-1 | 기존 최초 실행·프로젝트 선택·Files tree 테스트와 Electron BrowserWindow 설정이 있다 | 전체 WorkStudio 테스트·타입 검사·lint·Electron syntax 검사를 실행하고 신규 프로젝트 생성 UI를 점검한다 | 기존 welcome·프로젝트 선택·Files tree가 회귀하지 않고 `contextIsolation: true`, `nodeIntegration: false`가 유지되며 새 폴더 생성이나 `.opal` 초기화를 수행하는 실행 경로가 없다 | Vitest regression + 정적 설정 검사 | 구현 후 |
