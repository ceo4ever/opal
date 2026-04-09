# QA-EXECUTE: Gemini Hardening 글로벌 배포

> 검증일: 2026-04-09
> 검증자: opal-task-qa-agent
> 대상: EXECUTE 산출물

## 판정: PASS

## 체크리스트

### 기능 테스트

- [x] `opal/bootstrapper/gemini-hardening.md`가 존재하고 ` ````markdown ` 블록을 포함한다 — 파일 존재 확인. 내부에 ` ``` ` 코드펜스를 포함하기 위해 4-backtick 외부 블록(` ````markdown ... ```` `)을 사용하였으며 정상적으로 감싸진 구조 확인.
- [x] `extract_bootstrap_content`로 추출한 본문이 프로젝트 루트 `GEMINI.md`의 HARDENING 마커 사이 본문과 1:1 일치한다 — 추출 결과 170줄 vs SSOT(GEMINI.md 라인 11~181) 171줄. 차이는 SSOT 마지막의 후행 빈 줄 1개뿐이며 실질 내용(GUARD-1~5 + 실패 보고 형식) 전체가 동일. 기능적 불일치 없음. (특이사항 참조)
- [x] `install_gemini_hardening()` 함수가 정의되어 있고 `install_opal()`에서 호출된다 — `scripts/install-mac.sh` 라인 263에 함수 정의 확인, 라인 522~523에 `install_opal()` 내 호출 확인.
- [x] 신규 파일/마커 존재/마커 부재 3가지 케이스 모두 정상 동작 — dry-run 직접 실행 결과: Case 1(신규 파일) HARDENING 마커 1개 생성, OPAL 마커 0개; Case 2(OPAL만 있음) HARDENING 추가 + OPAL 보존; Case 3(OPAL+HARDENING 있음) 구 HARDENING 본문 교체 + OPAL 보존. 3케이스 전부 통과.
- [x] `print_summary()`에 HARDENING 요약 라인이 추가됨 — `scripts/install-mac.sh` 라인 836~837에 `HARDENING_START` 마커 존재 시 `~/.gemini/GEMINI.md          GEMINI HARDENING` 출력 구문 확인.

### 일관성 테스트

- [x] `install_opal_section()` 함수 본문은 변경되지 않았다 — `git diff HEAD scripts/install-mac.sh` 결과 `install_opal_section()` 함수 본문(라인 187~261)에 `-` 라인 없음. `extract_bootstrap_content()`에 4-backtick 지원이 추가되었으나 이는 별도 함수이며 기존 3-backtick 경로는 else 분기로 완전히 보존되어 하위 호환 유지.
- [x] `gemini-hardening.md`가 `gemini-bootstrap.md`와 동일한 파일 구조(헤더 → markdown 블록 → 변경이력)를 따른다 — 두 파일 모두 `# OPAL ...` 헤더, 사용법 blockquote, 구분선, "아래 내용이..." 안내, 구분선, markdown 블록, 구분선, 변경이력 테이블 순서 동일.
- [x] HARDENING 마커가 OPAL 마커와 독립적으로 작동한다 — Case 2 및 Case 3 dry-run에서 OPAL 섹션이 HARDENING 설치/업데이트 후에도 그대로 보존됨. 별도 상수(`HARDENING_START`/`HARDENING_END`)로 분리되어 마커 간 간섭 없음.
- [x] `~/.opal/` 경로 직접 편집이 없다 — `git diff HEAD scripts/install-mac.sh`에서 `~/.opal/`에 쓰기 또는 편집하는 추가 코드 없음. `gemini-hardening.md`는 `opal/bootstrapper/` 아래 소스 파일로만 존재.

### 문서 품질

- [x] 한국어 본문 + 영어 코드/필드명 규칙 — `gemini-hardening.md` 설명문은 한국어, 코드 블록·필드명·마커명은 영어 유지 확인.
- [x] kebab-case 파일명 — `gemini-hardening.md` 준수.
- [x] 변경이력 테이블 포함 — `gemini-hardening.md` 마지막에 `v1.0 | 2026-04-09 | 최초 작성...` 포함 확인.

## 특이사항

### SSOT 후행 빈 줄 1개 차이

`extract_bootstrap_content` 추출 결과(170줄)와 `GEMINI.md` 라인 11~181(171줄) 간 diff 결과 마지막에 빈 줄 1개 차이가 있다. 원인: `GEMINI.md` 라인 181이 빈 줄(END 마커 바로 앞 여백)이나, `gemini-hardening.md` 4-backtick 블록은 ` ``` ` 직후 ` ```` `로 닫혀 해당 빈 줄을 포함하지 않음. 실질 내용(GUARD-1~5, 실패 보고 형식)은 완전히 동일하고, `~/.gemini/GEMINI.md` 파일 삽입 시에도 기능적 영향 없음. 엄밀한 byte-for-byte 일치를 원하면 `gemini-hardening.md` 4-backtick 닫힘 직전에 빈 줄 1개 추가 필요.

### `extract_bootstrap_content` 함수 변경

PLAN.md §2에는 `extract_bootstrap_content()`가 그대로 재사용 가능하다고 명시되었으나, 실제로 `gemini-hardening.md`가 4-backtick 블록을 사용하기 때문에 기존 3-backtick 전용 구현으로는 추출이 불가하여 4-backtick 지원이 추가되었다. `install_opal_section()` 함수 자체는 변경되지 않았으며, `extract_bootstrap_content()` 확장은 기존 3-backtick 파일(`gemini-bootstrap.md`)에도 하위 호환(else 분기)으로 정상 동작함.

### TASK.md `print_installed_summary` vs 코드 `print_summary` 불일치

PLAN.md §1에 이미 기록된 내용. 코드 기준으로 `print_summary()` 함수에 반영하였으며 정상 동작 확인.
