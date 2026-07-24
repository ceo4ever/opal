# DONE: 부트스트랩 스킵 게이트 — 환경변수 → 배포 설정파일(setting.json) 전환

> 완료일: 2026-06-24 | 스킬: opds (agentic) | 태스크: 043

## 1. 요약

040이 도입한 부트스트랩 스킵 게이트를 **Bash 환경변수 체크(`echo $OPAL_BOOTSTRAP`)에서 배포 설정파일(`~/.opal/setting.json`) Read 기반으로 전환**했다. `echo $VAR`는 셸 변수 확장(simple_expansion)이라 Claude Code가 매 세션 권한 프롬프트를 띄웠으나, 부트스트랩이 이미 무프롬프트로 사용하는 `Read(~/.opal/**)` 경로에 게이트를 얹어 **새 권한 표면 0**으로 프롬프트를 제거했다. `setting.json`은 향후 런타임 설정 확장의 거점이 된다.

## 2. 변경 사항

| F-ID | 내용 | 파일 |
|------|------|------|
| F-001 | `setting.json` 배포 소스 신규 + install create-if-absent 배포 (멱등 — 사용자 토글 보존) | `opal/core/setting.default.json`(신규), `scripts/install-mac.sh`(`install_opal_setting`), `scripts/install/windows.ps1`(Install-OpalCore 블록), `scripts/install/linux.sh`(exec 위임 자동 상속) |
| F-002 | 게이트 로직 전환 — 5곳 `echo $OPAL_BOOTSTRAP` → `~/.opal/setting.json` Read 게이트 | `opal/core/AGENT.md`(step 0), `opal/bootstrapper/{claude,gemini,codex}-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc` |
| F-003 | 환경변수 접근·권한 정리 — `install_claude_permissions` perm_entries에서 `Bash(echo $OPAL_BOOTSTRAP)` 제거 (직전 L2 미커밋분 reconcile) | `scripts/install-mac.sh` |
| F-004 | 변경이력 행 추가 (043) | AGENT.md(v3.7)·claude(v1.0.2)/gemini(v1.1.2)/codex(v1.0.2)-bootstrap.md·install-mac.sh(v3.6)·windows.ps1(v1.15.0). cursor는 변경이력 표 부재로 제외 |

### 게이트 동작 (전환 후)

- Read 도구로 `~/.opal/setting.json`을 읽어 `bootstrap` 필드가 정확히 `off`면 부트스트랩 전체 스킵.
- 파일 부재·필드 부재·`off` 외 값·JSON 파싱 실패 = 정상 진행 (fail-safe, 040 계승).
- create-if-absent: install이 setting.json을 없을 때만 생성 → 사용자 토글이 재설치에도 보존.

## 3. 검증 결과

**TEST All Pass — 14 PASS / 0 FAIL / 3 pending(캡틴 L2·L3)**

- RED-first(install create-if-absent 동작 계약): TS-002(멱등)·TS-003(생성) — opal-test-agent(red) 작성 → opal-be-agent GREEN, PASS 2/0 exit 0. bash 3.2.57 호환 하네스(named temp file source)로 수정.
- L1 산출물: TS-001(JSON 유효)·004·005~010(게이트 5곳 전환·echo 0·fail-safe·동기·추출/frontmatter 무결)·012(perm echo 0·`bash -n`)·013(Linux 위임)·014(Windows 블록)·015(소스 echo 게이트 잔존 0)·016(변경이력) 전부 PASS.
- PM 독립 재현 spot-check: 워커 보고와 100% 일치.

**캡틴 직접 확인 대기 (install 재배포 후)**:
- TS-002b: install 2회 재실행 시 `~/.opal/setting.json` off 토글 보존(멱등).
- TS-011a: `{"bootstrap":"off"}` 새 세션 → 프롬프트 없이 부트스트랩 스킵.
- TS-011b: `on`/필드제거/파일삭제 3케이스 → 정상 7단계 부트스트랩(fail-safe 회귀).

## 4. 핵심 결정

- **소스 위치**: `opal/core/setting.default.json` (`.default` 접미 — 불변 소스 vs 사용자 토글 배포본 구분). install이 `~/.opal/setting.json`로 create-if-absent 배포.
- **플랫폼 정합**: Linux는 install-mac.sh exec 위임 wrapper로 자동 상속, Windows는 명시 블록 추가. Read 기반이라 권한 등록 패리티는 불요(부트스트랩이 이미 쓰는 경로 재사용).
- **프로젝트 오버라이드**(`{프로젝트}/.opal/setting.json`): 범위 외 — 글로벌 단일 채택. 우선순위 규칙은 후속 태스크(H-8).

## 5. 특이사항

- **PM 프로세스 슬립**: state-tool mark 출력을 `>/dev/null`로 가려 PLAN 작업 행 누락 → stage guard가 후속 행 mark를 조용히 거부. 산출물·테스트 영향 없이 STATE만 순차 reconcile로 복구. 교훈: state mark 출력 억제 금지 (AGENTIC-LOG #9).
- **미발효**: 소스만 수정 — 실제 무프롬프트 동작은 캡틴 install 재배포 시 발효.
- **커밋**: 미수행 (지시 대기).

## 6. 후속

- 캡틴 install 재배포 + L2/L3 실세션 검증 (TS-002b·011a·011b).
- 프로젝트 단위 오버라이드(우선순위 규칙) — 별도 태스크.
- 기존 사용자 `~/.claude/settings.json`에 남은 `Bash(echo $OPAL_BOOTSTRAP)` 권한은 무해(미사용) — 캡틴 선택 정리.
