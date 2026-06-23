# TEST-SCENARIO: OPAL 부트스트랩 스킵 옵션 (`OPAL_BOOTSTRAP=off`)

> 태스크: 040-260624-opds-부트스트랩-스킵 | 작성일: 2026-06-24
> RED-first: 비해당 (bash/markdown 정적 산출물 — 단위 테스트 프레임워크 없음)
> 검증 계층: L1(산출물 grep) → L2(install 재배포 후 확인) → L3(수동 세션 동작)

---

## 1. 시나리오 목록

> 출처: PLAN.md §3.1.5/§3.2.5/§3.3.5 + §5 QA 체크리스트

### L1 — 산출물 검사 (정적·결정론적)

| TS-ID | 항목 | 대상 파일 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|---------|----------|----------|------|
| TS-001 | claude 마커 skip 게이트 문구 삽입 | `opal/bootstrapper/claude-bootstrap.md` | 코드블록 내용 grep: `OPAL_BOOTSTRAP` + `off` + `생략` | 3 키워드 모두 코드블록(`` ```markdown `` ~ `` ``` ``) 내부에 존재 | Pass — sed 추출 결과: OPAL_BOOTSTRAP·off·생략 3 키워드 코드블록 내부 존재 확인. grep 카운트: OPAL_BOOTSTRAP=2, off=2, 생략=1 (exit 0) |
| TS-002 | cursor `.mdc` skip 게이트 삽입 + frontmatter 무손상 | `opal/bootstrapper/cursor-bootstrap.mdc` | 파일 구조 확인(frontmatter `---` 유지) + 본문에 `OPAL_BOOTSTRAP` 존재 | frontmatter `---` 구조 무손상, 본문에 게이트 문구 존재 | Pass — frontmatter `---`/`alwaysApply: true` 무손상 확인. OPAL_BOOTSTRAP 본문 존재 확인 (grep count=1, exit 0) |
| TS-003 | codex 마커 skip 게이트 문구 삽입 | `opal/bootstrapper/codex-bootstrap.md` | 코드블록 내 `OPAL_BOOTSTRAP` 존재 grep | 코드블록 내부 존재 | Pass — sed 추출 코드블록 내 OPAL_BOOTSTRAP 확인. 출력: `**[스킵 게이트]** 먼저 Bash 도구로 \`echo $OPAL_BOOTSTRAP\`...` (exit 0) |
| TS-004 | gemini 마커 skip 게이트 문구 삽입 | `opal/bootstrapper/gemini-bootstrap.md` | 코드블록 내 `OPAL_BOOTSTRAP` 존재 grep | 코드블록 내부 존재 | Pass — sed 추출 코드블록 내 OPAL_BOOTSTRAP 확인. 출력: `**[스킵 게이트]** 먼저 Bash 도구로 \`echo $OPAL_BOOTSTRAP\`...` (exit 0) |
| TS-005 | 코드블록 추출 무결성 — 조기 종료 없음 (H-1) | claude/codex/gemini `.md` 3종 | `sed -n '/\`\`\`markdown/,/\`\`\`/p'` 추출 결과에 게이트 문구 포함 확인 | 게이트 문구 포함, 코드블록 조기 종료(`---` 등) 없음 | Pass — 3종 모두 코드블록 전체가 정상 추출됨. claude grep count=1, 코드블록 경계 정상(조기 종료 없음). 스킵 게이트 문구·MUST 지시·파일 목록 모두 포함 (exit 0) |
| TS-008 | AGENT.md Eager step 0 게이트 삽입 | `opal/core/AGENT.md` | `### Eager 단계` 섹션 내 step 0 존재 + step 1보다 앞에 위치 | `0.` 또는 `step 0`이 `1.` 앞에 존재 | Pass — line 13에 `0. **[스킵 게이트]**...` 존재, line 15에 `1. ~/.opal/identity.md...` — 순서 정확 (exit 0) |
| TS-009 | AGENT.md `[WORKER]` 스킵과 구분 표현 | `opal/core/AGENT.md` | 게이트 문구에 `[WORKER]`와의 구분 표현 포함 | `[WORKER]`·별개·독립 등 구분 표현 존재 | Pass — step 0 문구 말미: "이 게이트는 세션/캡틴 전역 토글이며, 위 `[WORKER 규칙]`...과는 **별개의 독립** 스킵 경로다" 명시 (exit 0) |
| TS-010 | 마커 ↔ AGENT.md 게이트 문구 의미 동기 (H-6) | bootstrapper 4종 + `opal/core/AGENT.md` | 조건(`off`)·동작(전부 스킵)·폴백(정상 진행) 표현 양측 일치 확인 | 조건·동작·폴백 의미 일치 | Pass — 5종 모두: 조건=`정확히 off`, 동작=`전체 생략/전부 생략`, 폴백=`정상 수행/정상 진행` 의미 일치. cursor.mdc는 약어체이나 의미 동일 (exit 0) |
| TS-011 | windows.ps1 인라인 마커 문구 부재 (H-7) | `scripts/install/windows.ps1` | `Register-Bootstrapper` 함수 grep — 인라인 마커 문구 잔존 여부 | 인라인 마커 문구 없음 + `Get-BootstrapContent`가 `opal/bootstrapper/` 소스 참조 확인 | Pass — `grep OPAL_BOOTSTRAP scripts/install/windows.ps1` 결과 없음 (exit 1 = 문구 부재 = PASS). 인라인 하드코딩 없음 확인 |
| TS-012 | windows Get-BootstrapContent 동일 소스 소비 | `scripts/install/windows.ps1` | `Get-BootstrapContent` 함수 소스 경로 확인 | `opal/bootstrapper/` 경로 참조 확인 | Pass — `$bsDir = [IO.Path]::Combine($RepoRoot, 'opal', 'bootstrapper')` 확인 (line 794). Claude/Codex/Gemini/Cursor 모두 $bsDir 기반 경로로 Get-BootstrapContent/Install-OpalSection 호출 (exit 0) |

### L2 — install 재배포 후 확인 (사용자 승인 후 수행)

| TS-ID | 항목 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|----------|----------|------|
| TS-006 | `OPAL_BOOTSTRAP=off` 세션 스킵 동작 | install 재배포 후 `export OPAL_BOOTSTRAP=off`로 새 Claude Code 세션 → 응답 전 Bash 1회 실행 + 부트스트랩 Read 0건 | 첫 응답에 부트스트랩 보고 없음, Read 도구 미호출 | 환경 의존 — 사용자(캡틴) 직접 확인 필요 (install 재배포 + 신규 세션 동적 검증) |

### L3 — 회귀 테스트 (수동, L2 이후)

| TS-ID | 항목 | 검증 방법 | PASS 조건 | 결과 |
|-------|------|----------|----------|------|
| TS-007 | 미설정/`on` 세션 기존 부트스트랩 정상 동작 | `OPAL_BOOTSTRAP` 미설정 또는 `on` 세션 시작 | 기존 7단계 부트스트랩 정상 수행, `[부트스트랩] ✅` 보고 포함 | 환경 의존 — 사용자(캡틴) 직접 확인 필요 (수동 세션 시작 후 보고 내용 확인) |

---

## 2. 코드 품질

> L1 정적 검사 기반 — 별도 lint/typecheck 없음 (마크다운/bash 산문 변경)

| 항목 | 기준 | 결과 |
|------|------|------|
| 변경이력 기록 | claude/codex/gemini `.md` 하단 표 + AGENT.md 변경이력에 행 추가 | Pass — claude v1.0.1(2026-06-24/040), codex v1.0.1(2026-06-24/040), gemini v1.1.1(2026-06-24/040), AGENT.md v3.6(2026-06-24/040) 모두 변경이력 행 추가 확인 |
| 코드 펜스 미사용 | 게이트 문구 내 `` ``` `` 미사용, 인라인 백틱만 사용 (H-1 방어) | Pass — python3 검증: claude/codex/gemini 3종 코드블록 내부 게이트 문구에 코드 펜스(```) 없음 확인 (gate_fence=False) |
| 4종 문구 의미 일치 | 조건(`정확히 off`) + 동작(전부 스킵) + 폴백(정상 진행) 동일 | Pass — 5종(claude/codex/gemini/cursor/AGENT.md) 모두: 조건=`정확히 off`, 동작=`전체 스킵/생략`, 폴백=`정상 수행/진행` 의미 일치 확인 |

---

## 3. 보안

| 항목 | 기준 | 결과 |
|------|------|------|
| 시크릿 없음 | 게이트 문구에 토큰/시크릿 없음 | Pass — 5종 파일 전체 token/secret/key/password/api_key 검색 결과 없음 |
| 권한 최소 | `OPAL_BOOTSTRAP` 환경변수 + Bash echo만 사용, 추가 권한 불요 | Pass — 게이트 문구: `echo $OPAL_BOOTSTRAP` 단일 Bash 명령만 사용. 파일 시스템 접근·네트워크·권한 상승 없음 |

---

## 4. 회귀 테스트

| 항목 | 기준 | 결과 |
|------|------|------|
| 기존 `[WORKER]` 스킵 불변 | 디스패치 프롬프트 첫 줄 `[WORKER]` 동작 — 마커 변경으로 영향 없음 | Pass — AGENT.md line 9 `[WORKER 규칙]` 원문 불변. step 0 게이트는 [WORKER] 규칙 이후(line 13)에 별개 항목으로 추가됨. [WORKER] 규칙 자체 변경 없음 확인 |
| install 멱등 마커 교체 정상 | 재배포 시 게이트 문구 중복 누적 없음 (`install_opal_section` 멱등) | Pass — windows.ps1 Install-OpalSection: OPAL_START 마커 블록 교체 로직 존재. 기존 마커 있으면 교체, 없으면 추가(멱등). 인라인 게이트 문구 없으므로 중복 누적 구조적 불가 |

---

## 5. 설계 피드백 및 미해결 빈틈

| 항목 | 상태 |
|------|------|
| R-8 TASK 전제 오류 (emit 함수 vs bootstrapper SSOT) | ✅ 해소 — §1.2 정정 설계 채택 |
| H-7 windows.ps1 인라인 잔존 | TS-011 검증 → 잔존 시 한정 수정 (현재 코드 확인상 없음) |
| H-4 Bash 미보유 플랫폼 | 문구 폴백("Bash 불가 시 게이트 무시·정상 진행")으로 설계 수준 대응 완료 |
| TS-006 install 재배포 | L2 — install 재배포는 사용자(캡틴) 직접 수행. TEST 단계에서 L1 통과 후 보고 포함 |
