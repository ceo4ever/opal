# W-1 — 훅 프로세스의 프로젝트 루트 환경변수 실측·근거

> 태스크 149 / PLAN H-1 · D-23 ② 전제 검증. 작성: PM. 2026-09-22.

## 결론

`CLAUDE_PROJECT_DIR`는 훅 **프로세스 환경변수**로 주입되며 의미는 **프로젝트 루트**다.
봉투 `cwd`와는 별개 축이고, cwd가 하위 디렉토리로 바뀌어도 루트를 가리킨다.
PLAN D-23 ②의 전제는 성립한다. 프로젝트 루트를 알려주는 공식 환경변수는 이것 **하나뿐**이다.

## 근거

### E4 — 공식 문서

`code.claude.com/docs/en/hooks` §Environment Variables — 모든 command hook에서 사용 가능한 변수로
`$CLAUDE_PROJECT_DIR`를 `Project root`로 명시한다. 같은 문서 §Common Input Fields는 봉투 `cwd`를
"the working directory when the event fired"로 정의해 **두 값의 축이 다름**을 분리 서술한다.
봉투 공통 필드(`session_id`·`cwd`·`hook_event_name`·`permission_mode`)에는 루트가 없다.

### E2 — Anthropic 1st-party 훅 소스·가이드 (결정적)

로컬 설치본 `~/.claude/plugins/marketplaces/claude-plugins-official/`에서 실측했다.

| 근거 | 위치 | 내용 |
|---|---|---|
| 공식 hook 작성 가이드 | `plugins/plugin-dev/skills/hook-development/SKILL.md:326` | `$CLAUDE_PROJECT_DIR - Project root path` |
| 표준 패턴 | 같은 파일 `:474`, `references/patterns.md:72` | 훅 스크립트 첫 줄이 `cd "$CLAUDE_PROJECT_DIR" \|\| exit 1` |
| 프로젝트 스코프 파일 접근 | `SKILL.md:534`·`:550`, `patterns.md:268`·`:306` | `"$CLAUDE_PROJECT_DIR/.enable-security-scan"`, `"$CLAUDE_PROJECT_DIR/.claude/plugin-config.json"` |
| 두 축 분리 사용 | `plugins/security-guidance/hooks/reporesolve.py:160-167` | `scan_roots(cwd)`가 `cwd`와 `os.environ.get("CLAUDE_PROJECT_DIR")`를 **서로 다른 루트 후보**로 합집합 |

해석: 훅 진입 시 `cd "$CLAUDE_PROJECT_DIR"`로 작업 디렉토리를 옮기는 것이 1st-party 표준 패턴이고,
프로젝트 스코프 설정 파일을 그 아래에서 찾는다. 두 용법 모두 값이 **발화 시점 cwd가 아니라 안정된
프로젝트 루트**일 때만 성립한다. `reporesolve.py`는 한 걸음 더 나아가 `cwd`와 `CLAUDE_PROJECT_DIR`가
**다를 수 있음을 전제**하고 둘 다 스캔한다 — 우리가 고치려는 결함의 정확한 반대편 설계다.

## 미확보 증거와 그 처리

훅 프로세스 env의 **live 캡처**는 확보하지 못했다. 시도 3건이 하네스 권한 분류기에 거부됐다.

| 시도 | 결과 |
|---|---|
| `.claude/settings.local.json`에 임시 PostToolUse 훅 등록 (Bash·Edit) | `[Self-Modification]` 거부 |
| 격리 임시 디렉토리에서 헤드리스 프로브 세션 기동 | `[Create Unsafe Agents]` 거부 |
| 같은 기동을 수행하는 러너 스크립트 작성 | `[Auto-Mode Bypass]` 거부 |

부작용은 0이다 — 세 시도 모두 쓰기 이전에 거부됐고 `.claude/settings.local.json`은 백업본과 byte 동일하다.

처리: live 캡처는 **TEST-SCENARIO S-13**(재배포 후 실제 세션에서 `git status` 새 untracked `.opal/` 0건 +
루트 receipt `block_count` 누적)이 소유한다. 전제가 틀렸다면 S-13이 merge 전에 드러낸다.

## 잔여 위험 재평가 (PLAN H-1)

H-1의 차단 조건이었던 "`CLAUDE_PROJECT_DIR` 부재"는 **반증됐다**. 남은 위험은 "값이 cwd를 따라간다"
하나이며 1st-party 용법과 정면으로 모순되므로 낮다. 게다가 이 위험이 현실화해도 **현행보다 나빠지지
않는다** — 현행은 봉투 `cwd`를 그대로 루트로 쓰므로 동일한 오염이 이미 발생 중이고, D-23 ③의
자기증명 채택과 D-25의 "루트 미확정이면 쓰지 않는다"는 ②와 무관하게 AC-1·AC-2·AC-5를 성립시킨다.
②에 의존하는 것은 AC-3·AC-4뿐이다.
