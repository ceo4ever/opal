# DONE: opal-cli install 서브커맨드 완전 제거

> 완료일: 2026-07-10 | 스킬: opds | 모드: agentic | 태스크: 055

## 무엇을 했나

`opal-cli install` 서브커맨드를 디스패처에서 완전 제거하고, 이를 전제하던 안내 문구를 컨텍스트별 이식 경로(원라이너/`opal-cli update`)로 리다이렉트했다.

## 배경

`opal-cli install`은 로컬 소스(FRAMEWORK_ROOT/소스 레포)를 전제하는 수동 진입점이라, 소스가 없는 머신에서 "설치 스크립트를 찾을 수 없음 → clone 하라"로만 안내되는 UX 함정이었다. 이식 경로는 이미 완비 — 신규는 원라이너(`scripts/install.sh` / `install.ps1`), 갱신은 `opal-cli update`(원격 tarball + 데이터 보존), 개발은 `install-mac.sh` 직접. 캡틴 결정: 완전 제거.

## 변경 내역

- `opal/tools/opal-cli/run.sh`: dispatch case에서 `install` 제거(동적 로딩 로직·나머지 파이프 보존), usage() install 행·예시 제거, 헤더 서브커맨드 목록 갱신, `--version` fallback 문구를 원라이너 안내로 교체, 변경이력 v1.2(055).
- `opal/tools/opal-cli/lib/install.sh`: **삭제**(git rm) — dispatch에서만 동적 로드되던 파일, 제거 후 참조 0.
- `opal/tools/opal-cli/lib/update.sh`: 미설치 감지 안내 → **원라이너**(순환 방지 — update 안에서 update 재실행 안내는 무의미).
- `opal/tools/opal-cli/lib/doctor.sh`·`lib/console.sh`: 컴포넌트 누락 안내 → **`opal-cli update`**(재배포, 데이터 보존).
- `opal/tools/opal-cli/README.md`: install 언급 5곳(인트로·표·예시·파일 트리) 제거 + 변경이력 v1.1(055).
- `docs/ARCHITECTURE.md`: 배포 채널 표 `opal-cli` 서브커맨드 목록에서 install 제거 + 변경이력(Task 055).

## 핵심 설계 결정

- **완전 제거(리다이렉트 스텁 없음)**: `opal-cli install` 입력은 dispatch `*)` unknown 분기로 흡수 → "알 수 없는 서브커맨드: install" + usage + exit 1(설치 시도 없음).
- **컨텍스트별 리다이렉트**: 미설치(~/.opal 부재)=원라이너 / 배포본 손상(~/.opal 존재, 컴포넌트 누락)=`opal-cli update`. `update.sh`를 update로 안내하면 순환이므로 원라이너 강제(H-3).
- **(A)안 기각**: "install=OS감지+삭제+원격재설치"는 사용자 데이터 소실 위험 또는 update 중복이라 배제.

## 검증 결과 (All Pass)

| 검증 | 결과 |
|------|------|
| help install 미노출 | ✅ 단어경계 grep=0, uninstall 보존=2 |
| `opal-cli install` unknown 흡수 | ✅ exit 1, 설치 시도 없음 |
| lib/install.sh 삭제·참조 0 | ✅ ABSENT |
| 회귀(update/doctor/uninstall/mcp/console) | ✅ 전부 정상 로드 |
| 미설치 리다이렉트 순환 없음 | ✅ 원라이너 안내, `opal-cli update` 재귀 0 |
| 손상 리다이렉트 = update | ✅ doctor/console `opal-cli update` |
| README·ARCHITECTURE 정합 + 변경이력 | ✅ |
| bash -n / shellcheck | ✅ 클린 (update.sh:222 SC2016은 pre-existing 무관) |

> 검증은 소스 직접 실행(비파괴, `OPAL_HOME` override). TEST-SCENARIO의 bare `grep install` 패턴이 `uninstall`·`mcp install-all`·부트스트랩 `install.sh`를 오탐 → 단어경계·제외 패턴으로 보정하여 실질 판정(코드 결함 아님).

## 변경 파일 (055 — 7개)

`opal/tools/opal-cli/{run.sh, lib/doctor.sh, lib/update.sh, lib/console.sh, README.md}` · `opal/tools/opal-cli/lib/install.sh`(삭제) · `docs/ARCHITECTURE.md`

## 남은 사항 / 후속

- **install 재배포 필요**: 소스 변경을 배포본 `~/.opal`에 반영하려면 재배포(`./scripts/install-mac.sh` 또는 원라이너/`opal-cli update`) 필요. 재배포 후 `opal-cli install`이 배포본에서도 unknown 처리됨을 확인 권장.
- **커밋 미수행**: 054·055 각각 분리 커밋(053 잔여 제외) — 캡틴 지시 대기.
- **개선 후보**: TEST-SCENARIO grep 패턴의 `uninstall` 오탐은 향후 시나리오 작성 시 단어경계 사용 권장(일반 교훈).
