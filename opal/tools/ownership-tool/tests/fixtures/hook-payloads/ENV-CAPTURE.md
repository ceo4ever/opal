# ENV-CAPTURE — H-2 실측 (서브에이전트 Bash)

> 이 워커(opal-be-agent, 서브에이전트)의 Bash 호출에서 관측한 값을 해석 없이 그대로 기록한다.
> 실행 명령: `echo "OPAL_SESSION_ID=${OPAL_SESSION_ID:-<unset>}"; echo "CLAUDE_ENV_FILE=${CLAUDE_ENV_FILE:-<unset>}"; env | grep -i '^CLAUDE' | sort`

## 관측 결과 (원문)

```
OPAL_SESSION_ID=<unset>
CLAUDE_ENV_FILE=<unset>
CLAUDE_CODE_CHILD_SESSION=1
CLAUDE_CODE_ENTRYPOINT=cli
CLAUDE_CODE_EXECPATH=/Users/iskang/.local/share/claude/versions/2.1.273
CLAUDE_CODE_MESSAGING_SOCKET=/tmp/cc-socks/99673.sock
CLAUDE_CODE_MESSAGING_TOKEN=8ed357f769e9a51eff036c89d3bf33f8
CLAUDE_CODE_SESSION_ATTENDED=1
CLAUDE_CODE_SESSION_ID=4601076e-8901-4289-9b6d-381dc574eb44
CLAUDE_EFFORT=low
CLAUDE_PID=99673
CLAUDECODE=1
```

## 관측 사실만 (해석 금지)

- `OPAL_SESSION_ID`: 이 서브에이전트 Bash 호출에서 unset.
- `CLAUDE_ENV_FILE`: 이 서브에이전트 Bash 호출에서 unset.
- `CLAUDE_CODE_SESSION_ID`(하네스 자체 세션 ID, `4601076e-...`)는 존재하지만 `OPAL_SESSION_ID`와는 별개 변수이며 값이 다르다(비교 대상 아님, 단순 관측).
- 이 값은 opal-be-agent 서브에이전트의 Bash 실행 결과다. PM(오케스트레이터) 세션 자체의 Bash 호출이나 SessionStart hook 경로에서의 값은 이 관측에 포함되지 않는다 — H-2가 요구하는 "서브에이전트 Bash 호출"의 1차 실측으로 이 결과를 사용하고, PM 직접 Bash 경로는 별도 실측이 필요하면 S-29에서 보완한다.
