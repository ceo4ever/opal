# H-6 실측: 서브에이전트 frontmatter `effort: medium` 고정 여부

실측일 2026-10-01. 코드 루트 `.opal-worktrees/task_172`. 원본은 `run/test-evidence/h6/`.

## 판정 (한 줄)
**고정됨** (관찰 수준). probe-medium 서브 출력 토큰 중앙값은 부모 high 2480, 부모 low 2571로 차이 3.7%(기준 20% 이내). probe-none은 high 2386, low 1818로 high가 31% 크다.

## ① 프로브 정의와 부모 프롬프트
- 위치: 임시 프로젝트 `h6proj/.claude/agents/`(스크래치패드, 저장소 밖, 실험 후 삭제). 설치본 `~/.claude/agents`는 건드리지 않았다.
- 두 파일의 diff는 `name` 줄과 `effort: medium` 1줄뿐이다(본문 바이트 동일). 공통 frontmatter: `description: Constraint puzzle solver probe. Use when asked to call probe.`, `tools: [Read]`, `model: opus`.
- probe-medium.md 전문:

```
---
name: probe-medium
description: Constraint puzzle solver probe. Use when asked to call probe.
tools: [Read]
model: opus
effort: medium
---

다음 조건을 모두 만족하는 5자리 자연수를 찾아라. 도구는 사용하지 말고 직접 추론하라.
1. 다섯 자리 숫자는 모두 서로 다르다.
2. 각 자리 숫자의 합은 26이다.
3. 7로 나누어떨어진다.
4. 첫째 자리 숫자는 마지막 자리 숫자보다 크다.
5. 둘째 자리 숫자는 짝수이다.
6. 셋째 자리 숫자는 둘째 자리와 넷째 자리 숫자의 합과 같다.
7. 넷째 자리 숫자는 3의 배수이다(0 포함).
8. 마지막 자리 숫자는 홀수이다.
검증 과정을 단계별로 쓰고, 마지막 줄에 "ANSWER: <숫자>" 형식으로 답하라. 정답이 유일함을 확인하라.
```
- probe-none.md는 `name: probe-none`이고 `effort:` 줄이 없다. 나머지는 동일하다.
- 정답은 전수 탐색(python)으로 유일 해 **72863**임을 확인했다.
- 부모 프롬프트(전문): `Agent 도구로 \`probe-<none|medium>\` 서브에이전트를 한 번 호출하고 그 응답을 그대로 반환하라.`
- 부모 기준선 프롬프트: `OK만 답하라.`
- 호출: `~/.opal/tools/opal-agent/run.sh --effort <high|low> --model opus --cwd <h6proj> --allowed-tools Agent,Read --stream --opal-bootstrap off --timeout 300 "<프롬프트>"` (`--json` 대신 `--stream`을 쓴 이유는 ④). 총 16회(본 12 + 기준선 4)를 무작위(seed 172) 순서, 동시 4로 실행했다. 각 1회, 재시도 없음, 16회 모두 rc=0(실패 없음). 순서는 `test-evidence/h6/order.json`.
- 사전에 스모크 1회(부모 low, probe-medium)로 방법을 확인했으며 본 표에는 포함하지 않았다.

## ② 12행 표
서브 출력 토큰은 서브에이전트 transcript(`task_notification.output_file`)의 메시지별 `usage.output_tokens`를 message id별 최댓값으로 합산한 값이다. thinking 열은 같은 방식의 `output_tokens_details.thinking_tokens`이며 출력 토큰에 포함된다. 서브 소요는 transcript 첫~끝 timestamp 차이, 총 소요는 wrapper 벽시계(부모 포함)다.

| 부모 effort | 프로브 | 회차 | 서브 출력 토큰 | 그중 thinking | 서브 소요(s) | 총 소요(s) | 퍼즐 |
|---|---|---|---|---|---|---|---|
| high | probe-medium | 1 | 2559 | 1225 | 29.4 | 52.8 | 정답 |
| high | probe-medium | 2 | 2252 | 1060 | 28.0 | 47.7 | 정답 |
| high | probe-medium | 3 | 2480 | 1160 | 31.7 | 60.8 | 정답 |
| high | probe-none | 1 | 2386 | 1095 | 28.1 | 52.8 | 정답 |
| high | probe-none | 2 | 2100 | 884 | 23.8 | 55.3 | 정답 |
| high | probe-none | 3 | 2595 | 1261 | 27.6 | 48.7 | 정답 |
| low | probe-medium | 1 | 2264 | 877 | 26.6 | 63.7 | 오답(76391) |
| low | probe-medium | 2 | 2571 | 1093 | 27.6 | 54.1 | 정답 |
| low | probe-medium | 3 | 2624 | 1381 | 26.9 | 49.5 | 정답 |
| low | probe-none | 1 | 1734 | 587 | 20.1 | 41.6 | 정답 |
| low | probe-none | 2 | 1818 | 753 | 23.5 | 50.6 | 정답 |
| low | probe-none | 3 | 1825 | 870 | 19.1 | 39.1 | 정답 |

중앙값 요약:

| 조건 | 서브 출력 토큰 중앙값 | thinking 중앙값 | 서브 소요 중앙값(s) |
|---|---|---|---|
| 부모 high, none | 2386 | 1095 | 27.6 |
| 부모 high, medium | 2480 | 1160 | 29.4 |
| 부모 low, none | 1818 | 753 | 20.1 |
| 부모 low, medium | 2571 | 1093 | 26.9 |

정확도: 12회 중 11회 정답(72863). 오답 1회는 부모 low + probe-medium 1회차(76391)다. 표본이 작아 정확도로 effort 영향을 논하지 않는다.

부모 기준선(서브 호출 없이 "OK만 답하라"):

| 실행 | 부모 출력 토큰 | 벽시계 |
|---|---|---|
| high-base-1 | 6 | 14.7s |
| high-base-2 | 8 | 12.8s |
| low-base-1 | 4 | 8.9s |
| low-base-2 | 3 | 9.7s |

부모 기준선 출력은 3~8토큰, 벽시계 약 9~15초다. 서브 호출 실행에서도 부모 몫은 대부분 12~23토큰이다. 예외 3건(high-medium-1, high-none-1, low-none-1)은 부모가 서브 응답을 되풀이해 약 1100~1160토큰이었다. 서브 토큰은 transcript로 분리했으므로 부모 몫을 빼는 보정은 하지 않았고, 기준선은 총 소요의 부모 오버헤드(약 9~15초) 가늠용으로만 썼다.

## ③ 사전 판정 규칙 적용
- 규칙 1(probe-medium 중앙값이 부모 high와 low에서 20% 이내): 2480 vs 2571, 차이 91토큰(3.7%) -> 충족.
- 규칙 2(probe-none이 그보다 크게 벌어지거나 probe-medium과 구분): 2386 vs 1818, 차이 568토큰(31%) -> 충족. 부모 low에서는 none(1818)과 medium(2571)이 개별 값 범위도 겹치지 않는다(none 1734~1825, medium 2264~2624). 부모 high에서는 none 2386과 medium 2480이 거의 같다.
- 결과: **고정됨**. 부모 effort가 low여도 probe-medium은 high일 때와 같은 수준으로 동작했다.
- 부수 관찰: 이 과제에서 medium의 출력량은 부모 high를 상속한 none과 비슷했다. 서브 소요도 같은 경향이다(medium 27~29초, none-high 28초, none-low 20초).

## ④ 한계
- 조건당 3회뿐이고 모델 출력 변동이 크다(같은 조건 안에서도 high-none 2100~2595). 통계 주장은 하지 않으며 관찰이다.
- 서브 usage 분리: `--json`의 `usage`와 `modelUsage`는 부모+서브가 섞여 일치하지 않았고(스모크에서 `modelUsage.outputTokens` 4333 vs `usage.output_tokens` 1821), `--stream` 출력에는 서브 메시지가 흐르지 않았다. 그래서 `--stream`의 `task_notification.output_file`이 가리키는 서브에이전트 transcript(`~/.claude/projects/.../subagents/agent-*.jsonl`)를 읽어 서브 메시지 usage를 직접 얻었다(사본 `*.subagent.jsonl`). 이 파일은 CLI 내부 저장 형식이라 버전에 따라 달라질 수 있다.
- 서브가 받은 effort 값을 직접 읽은 것이 아니라 출력량으로 추정한 간접 증거다. 출력 토큰은 effort 외에 문제 난이도 체감과 표본 변동의 영향을 받는다. 이 퍼즐은 medium 수준에서 포화됐을 수 있어, medium보다 낮은 값(low)이 frontmatter에 적용되는지는 이 실험으로 알 수 없다.
- 프로젝트 에이전트(`.claude/agents`)로 측정했다. 설치본 `~/.claude/agents`의 evaluator가 같은 frontmatter 해석을 하는지는 별도 확인이 필요하다(로딩 경로만 다른 것으로 가정).
- 서브에이전트가 전역 `~/.claude/CLAUDE.md`의 OPAL 부트스트랩 지시를 읽고 "셸 도구가 없어 중단"을 언급하는 노이즈가 출력에 섞인다. 모든 조건에 공통이나 출력 토큰에 일부 더해졌다. 부모의 `--opal-bootstrap off`는 서브에이전트에 적용되지 않는다.
- 부모가 서브에 넘기는 프롬프트는 부모가 생성하므로(예: "Please run your probe task and return your response.") 조건 간 완전히 동일하지는 않다.
- 서브 모델은 frontmatter `model: opus`로 지정했고 `--model opus`와 같은 `claude-opus-5-5`로 동작했다.

## ⑤ evaluator `effort: medium` 결정에 주는 시사점
이 실측에서 frontmatter `effort: medium`은 호출 세션 effort(high/low)와 무관하게 비슷한 추론량(서브 출력 중앙값 2480 vs 2571)을 냈으므로, evaluator에 `effort: medium`을 명시하면 설계 게이트 판정의 추론 깊이를 오케스트레이터 세션의 effort 설정과 분리해 일정하게 유지하는 근거가 된다. 반대로 `effort`를 생략하면 부모 effort를 상속해 low 세션에서 출력이 약 24% 줄었으므로(2386 -> 1818), 시간 단축 목적으로 부모를 낮추면 evaluator 추론 깊이도 함께 낮아질 위험이 있다. 다만 이 실험에서 medium은 부모 high 상속과 같은 수준의 출력을 냈으므로 "medium이 high보다 시간을 줄인다"는 근거는 얻지 못했고(medium 서브 소요 27~29초, none-high 28초), 속도 이득을 주장하려면 medium과 high 명시를 직접 비교하는 별도 실험이 필요하다. 표본이 작고 설치본 evaluator 경로가 미검증이므로 결정의 보조 증거 수준이다.
