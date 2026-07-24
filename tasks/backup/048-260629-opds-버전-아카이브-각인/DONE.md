# DONE: 버전을 릴리스 아카이브에 각인 (export-subst) — 설치 시점 API 의존 제거

> 완료일: 2026-06-29 | 스킬: opds | 모드: agentic | 태스크: 048

## 결과 요약

설치·업데이트가 GitHub API로 버전을 결정하던 구조를 제거하고, 릴리스(`git archive`) 시점에 git이 `VERSION` 파일에 실제 태그를 각인(`export-subst` + `$Format:%(describe:tags)$`)하도록 전환했다. 설치기 4종은 "추출한 tarball의 `VERSION`을 읽되, 미치환 플레이스홀더면 기존 폴백"으로 동작한다. API 403(rate limit)·네트워크 차단 시 버전 라벨이 `main`으로 오염되던 문제를 근본 제거했다.

## 변경 파일

| 구분 | 파일 | 내용 |
|------|------|------|
| 신규 | `VERSION` | 한 줄 `$Format:%(describe:tags)$` (각인 플레이스홀더, tracked) |
| 신규 | `scripts/tests/test_version_stamp.sh` | git archive 3경로 + 설치기 판별 + 보안 회귀 테스트 (11 케이스) |
| 수정 | `.gitattributes` | `VERSION export-subst` 규칙 + 주석 |
| 수정 | `scripts/install.sh` | `adopt_stamped_version()` 추가, extract 후 호출 → `OPAL_VERSION` override |
| 수정 | `opal/tools/opal-cli/lib/update.sh` | 추출 직후 각인값으로 `version` override |
| 수정 | `scripts/install-mac.sh` | `record_installed_version()` 함수 분리(D-피2) + 우선순위 재배치(각인값 최우선) |
| 수정 | `scripts/install.ps1` | 추출 후 `$extractDir/VERSION` 읽어 `-notlike '*$Format:*'` 판별 후 override |
| 수정 | `scripts/install/windows.ps1` | `$repoRoot/VERSION` 각인값 최우선 읽기(install-mac.sh 대칭, D-피1) |
| 수정 | `.github/workflows/release.yml` | `git archive HEAD` 각인 적용 주석 보강(코드 무변경) |

## 버전 결정 우선순위 (전환 후)

1. 추출된 소스 루트의 각인 `VERSION` (치환값) — **최우선, API 미사용**
2. `$OPAL_VERSION` (one-liner installer 전달값)
3. `git describe --tags` (개발자 git clone 경로 — placeholder 미치환 시)
4. `main` (모든 폴백 실패 시)

## 검증 (RED-first)

- RED: 계약 TC 6개 FAIL / 메커니즘 TC 3개 PASS, EXIT=1 (구현 전)
- GREEN: 11/11 PASS, EXIT=0 (커밋 없이 달성) — PM 독립 재실행 확인
- 검증 계층: L1(설치기 셸 함수 판별·기록) + L2(실 `git archive` 각인 메커니즘)
- 보안: 시크릿 스캔 0건, bash 3.2 호환(case 패턴), PS `.Trim()` 처리 확인

## 특이사항 (AGENTIC-LOG 참조)

- **가드 위반 1건 적발·정정**: 구현 워커가 `커밋 금지` 가드를 위반해 VERSION+.gitattributes를 커밋(`9bf6727`) → `git reset --soft`로 제거, origin/main 동기 복원.
- **근본 원인 교정**: RED 테스트 TC-A4가 실저장소 `git archive HEAD` 치환을 검증해 커밋을 구조적으로 강요한 결함 → "VERSION tracked + export-subst attr" 검증으로 교정(메커니즘 증명은 scratch TC-B1 유지) → 커밋 없이 GREEN 재확보.

## 후속 (캡틴 수행)

1. **커밋** — 변경 전부 워킹트리 미커밋 상태. 캡틴 지시 시 커밋.
2. **v0.6.5 태깅** — export-subst는 설정 커밋 이후 생성되는 archive부터 실효. v0.6.4 이하 소급 불가. 커밋 후 새 태그를 끊어야 첫 효과.
3. **install 재배포 / opal-cli update** — 재배포 후 `opal-cli --version`이 정확한 태그를 표시(API 무관).
