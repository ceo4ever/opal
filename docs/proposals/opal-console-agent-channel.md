# OPAL Console 에이전트 채널 도입 비교안

> 상태: 검토 | 작성: 알투(PM) | 작성일: 2026-09-09
> 발단: "Buzz처럼 설정에서 LLM CLI를 등록하고, 채널 방에서 에이전트와 대화하며 업무를 수행하고 싶다"
> 범위: 방향 결정용 비교 문서. 구현 계획(PLAN)이 아니며 코드 변경을 포함하지 않는다.

---

## 1. 이 문서가 답하는 질문

세 가지다.

1. 지금 콘솔에 무엇이 있고 무엇이 없는가 (§2)
2. 갈 수 있는 길이 몇 개이고 각각 무엇을 치르는가 (§4~§6)
3. 그래서 어디로 가야 하는가 (§7)

판단의 전제가 되는 사실은 전부 실측했다. 추정은 §8에 분리했다.

---

## 2. 실측 확정 사실

### 2.1 Buzz 측

| 사실 | 근거 |
|------|------|
| Buzz는 CLI가 아니라 **ACP 서버**를 등록한다 | `Application Support/Buzz/node-tools/bin/claude-agent-acp` → `@agentclientprotocol/claude-agent-acp@0.70.0` |
| 통신은 **stdio JSON-RPC** | `dist/index.js`가 `console.log = console.error`로 stdout을 프로토콜 전용 회선으로 확보 |
| 등록 화면의 `Underlying CLI`는 **env 주입값** | `claudeCliPath()`의 1순위가 `CLAUDE_CODE_EXECUTABLE`. 기본값은 SDK 번들 바이너리인데 화면에 nvm 경로가 찍힌 것은 Buzz가 사용자 claude를 감지해 핀했다는 뜻 |
| `Ready` 배지는 **LLM 호출이 아니라 존재 확인** | 어댑터 설치 + 하부 CLI 해석. `--cli` 플래그가 인자를 원본 CLI로 포워딩하는 진단 경로를 내장 |
| **Buzz 채널의 claude는 `~/.claude/CLAUDE.md`를 로드한다** | `dist/acp-agent.js:4868` — `settingSources: ["user", "project", "local"]` |
| 전역 기본값은 런타임/모델을 분리 보관 | `agents/global-agent-config.json` — `{preferred_runtime:"claude", model:"sonnet", provider, env_vars}` |
| Buzz는 **Nostr relay 기반**이고 CLI가 있다 | `/Users/lucas/.local/bin/buzz` — `channels`·`messages`·`agents`·`workflows`·`mem` 등. NIP-OA/01/02/23/34/MP/AE |

**가장 중요한 귀결**: Buzz 채널에서 OPAL 부트스트래퍼는 **이미 로드된다.** 스크린샷의 `System prompt 5 sections`·`Commands available: 57`이 그 흔적이다. "채널에서 OPAL 에이전트와 대화한다"는 목표의 절반은 오늘 이미 충족돼 있다.

### 2.2 OPAL Console 측

| 사실 | 근거 |
|------|------|
| 대화 런타임의 상당 부분이 **이미 있다** | `adapters/brain_session.py` — 대화별 상태기계(idle/priming/ready/error), 웜 핸들 풀, 비동기 잡 제출·폴링, 크래시 시 콜드 재시도, 5트리거 리셋 |
| **프로젝트 cwd 격리가 구현돼 있다** | `opbr_adapter.prime_and_ask(cwd=project_path)` |
| LLM 경로는 **3중으로 잠겨 있다** | `--allowedTools Bash,Read,Grep,Glob` + `//opbr query --read-only` + 프롬프트 첫 줄 `[ASSISTANT]` tier 캡 |
| 런타임 설정이 **하드코딩** | `CLAUDE_BIN = "claude"`, `--model sonnet`, `--effort medium` (`opbr_adapter.py:141-143`) |
| 출력은 **일괄 수신**이다 (스트리밍 아님) | `subprocess.run` + JSON 펜스 파싱. 콜드 실측 ~56초, 타임아웃 180초 |
| 라우터가 **전부 동기**다 | `routers/*.py`의 `async def` 개수 = **0** |
| 동시성은 **2를 전제**로 튜닝 | `DEFAULT_MAX_CONCURRENT_PRIME=2`, 세션당 `threading.Lock`, 락 순서 계약(`_lock`→`_pool_lock`, 역순 금지) |
| **인증이 없다** | `main.py`에 인증 미들웨어 없음. 읽기 전용이라 성립했던 설계 |

### 2.3 ACP 생태계

ACP는 프로그램이 아니라 **규약**이다. MCP가 에이전트↔도구라면 ACP는 호스트↔에이전트다(LSP와 같은 발상). `claude-agent-acp`가 두 SDK를 동시에 물고 있는 것이 이 층위 관계의 실물 증거다.

| 항목 | 값 |
|------|-----|
| 파이썬 SDK | `pip install agent-client-protocol` — **Zed 공식**, 0.12.1 (2026-08-16), Python >=3.10 <3.15 |
| 제공 내용 | pydantic 스키마 모델, async 베이스 클래스, stdio JSON-RPC 배관 |
| **클라이언트 측 포함** | 세션 누산기, **permission broker**, 기존 CLI stdio 래퍼 |

---

## 3. 목표의 분해

"채널에서 대화하며 업무"는 실제로는 성격이 다른 요구 5개다. 안별 평가는 이 5축으로 한다.

| 축 | 내용 | 현행 콘솔 | 현행 Buzz |
|----|------|:---:|:---:|
| **R1 런타임 등록** | 설정에서 CLI/런타임을 등록하고 Ready 판정 | ✗ 하드코딩 | ✓ |
| **R2 대화 UX** | 스트리밍, 툴 호출 가시화, 멀티턴 | △ 폴링·일괄 | ✓ |
| **R3 채널 영속** | 대화방이 남고 나중에 돌아올 수 있음 | ✗ 의도적 비영속 | ✓ |
| **R4 쓰기 실행** | 파일 수정·명령 실행·파이프라인 완주 | ✗ 3중 잠금 | ✓ bypassPermissions |
| **R5 OPAL 결합** | PM tier 승격 + 프로젝트 컨텍스트(태스크·state·brain·memory) 결합 | ✓ cwd 격리 보유 | **△ 미확인** |

R5의 `△`가 이 검토 전체의 분기점이다. 다음 절에서 다룬다.

### 3.1 R5가 왜 분기점인가

OPAL의 PM tier 승격 조건은 **cwd에 `.opal/AGENT.md`가 존재**하는 것이다(`~/.opal/AGENT.md` Phase B 게이트). 즉 —

- Buzz 채널이 프로젝트 루트를 cwd로 잡으면 → 부트스트래퍼 로드 + **PM 승격까지 성립** → 콘솔에 채널을 지을 이유가 거의 사라진다
- cwd가 프로젝트가 아니면 → CLAUDE.md는 읽히지만 **비서 tier에 머문다** → 태스크 파이프라인·state-tool·하네스가 안 붙는다

콘솔은 이 cwd 바인딩을 **이미 구현해 두었다**(§2.2). 이것이 콘솔이 가진 유일한 구조적 우위이고, 동시에 Buzz 쪽에서 확인해야 할 단 하나의 항목이다.

---

## 4. 네 가지 안

### 0안 — 현행 유지: Buzz를 그대로 쓴다

콘솔은 읽기 전용 대시보드로 두고, 대화형 업무는 Buzz 채널에서 한다.

- **하는 일**: 없음. (필요시 Buzz 에이전트의 작업 디렉토리를 프로젝트 루트로 설정)
- **얻는 것**: R1~R4 즉시. 비용 0
- **못 얻는 것**: R5 결합. 콘솔의 칸반·진행 통계·brain·memory와 대화가 분리된 채로 남는다
- **전제**: §3.1의 cwd 확인이 통과할 것

### A안 — 콘솔을 ACP 호스트로 만든다

콘솔 백엔드가 파이썬 ACP SDK로 `claude-agent-acp`·`codex-acp`를 자식 프로세스로 띄우고, FE는 SSE/WS로 스트리밍을 받는다.

- **하는 일**: ACP 클라이언트 구현 / 라우터 asyncio 전환 / 런타임 레지스트리 신설 / 채널 영속 계층 / 인증 / 권한 승인 UX
- **얻는 것**: R1~R5 전부. **스트리밍·권한 왕복·멀티 런타임이 프로토콜에 정의돼 있어 자체 설계 불요**
- **치르는 것**: 콘솔 아키텍처 원칙 3개 반전(§5). 동기→비동기 전환. 0.x 스키마 추종 유지보수

### B안 — 콘솔↔Buzz 연동

채널·에이전트·메시지는 Buzz에 두고, 콘솔은 `buzz` CLI(또는 relay)를 통해 읽고 쓴다. 콘솔은 OPAL 컨텍스트(태스크·state·brain)를 채널에 주입·회수하는 쪽을 맡는다.

- **하는 일**: `buzz` CLI 어댑터 1종 추가(콘솔이 이미 잘하는 패턴) / relay 인증(`BUZZ_PRIVATE_KEY`) / 컨텍스트 브리지 설계
- **얻는 것**: R1~R4는 Buzz가 제공. R5는 브리지 품질만큼
- **치르는 것**: Buzz 종속(Nostr relay·키 관리). 두 앱을 오가는 UX. 콘솔이 대화 주체가 아니라 곁다리가 됨
- **미확인**: relay 운영 형태. 로컬 3000은 미가동이고 `BUZZ_*` 환경변수도 미설정 상태 — 원격 relay 추정

### C안 — 현행 어댑터를 직접 확장 (Buzz 흉내)

`opbr_adapter`를 일반화해 CLI를 직접 spawn하고, 등록 레코드·채널 UI를 자체 구현한다.

- **하는 일**: A안과 같은 목록에서 "ACP SDK 사용"만 "자체 구현"으로 바뀜
- **얻는 것**: 초기 진입이 가장 가벼움. 기존 코드 연장선
- **치르는 것**: **스트리밍 파싱·권한 승인 왕복·런타임 추상화를 전부 자체 설계.** A안이 공짜로 얻는 것을 손으로 만든다
- **평가**: R4(쓰기 실행)까지 가면 A안보다 비싸진다. R2까지만 할 거면 합리적

---

## 5. 아키텍처 원칙 충돌 매트릭스

`docs/ARCHITECTURE.md` §OPAL Console에 명문화된 원칙 기준. ✗ = 반전 필요(캡틴 승인 대상).

| 원칙 | 출처 | 0안 | A안 | B안 | C안 |
|------|------|:---:|:---:|:---:|:---:|
| 읽기 전용 대시보드 | ARCHITECTURE §Console | ✓ | ✗ | △ | ✗ |
| backend 무상태 — 대화 내용 영속 금지 | `brain_session.py` `[MUST]` / 태스크 063 | ✓ | ✗ | ✓ (Buzz가 보관) | ✗ |
| LLM 경로 단일 라우터 격리 | ARCHITECTURE §브레인 질의 | ✓ | ✗ | ✓ | ✗ |
| 127.0.0.1 바인딩 | H-7 / S-5 | ✓ | ✓ | ✓ | ✓ |
| 하네스 구현 금지 원칙(승인 게이트) | `opal-harness.md` §1 | ✓ | **결정 필요** | **결정 필요** | **결정 필요** |
| 인증 부재가 안전한 전제 | 읽기 전용이라 성립 | ✓ | ✗ | △ | ✗ |

### 5.1 가장 무거운 항목 — 하네스 게이트를 채널 안에 둘 것인가

R4(쓰기 실행)를 열면 반드시 갈라진다.

| 선택 | 결과 |
|------|------|
| **채널 안에 승인 UX를 둔다** | 하네스 구현 금지 원칙·CLOSE 진입 게이트가 채널에서 살아 있음. A안은 ACP `permission broker`가 이 왕복을 제공 |
| **bypassPermissions로 연다** | 프레임워크가 스스로 하네스 우회 경로를 만드는 셈. `docs/SECURITY.md` §1이 위협 표면으로 지목한 CWE-78을 콘솔이 자기 손으로 여는 모양 |

무인증 로컬 HTTP 서버(§2.2) 위에서 후자를 택하면, 브라우저에서 도달 가능한 임의 명령 실행 표면이 된다. **A·C안은 인증·권한 모델 확정이 UI보다 반드시 앞선다.**

---

## 6. 축별 종합 비교

| 축 | 0안 | A안 (ACP 호스트) | B안 (Buzz 연동) | C안 (직접 확장) |
|----|:---:|:---:|:---:|:---:|
| R1 런타임 등록 | ✓ | ✓ | ✓ | ✓ |
| R2 스트리밍 UX | ✓ | ✓ (프로토콜 제공) | ✓ | △ 자체 구현 |
| R3 채널 영속 | ✓ | ✓ (신설) | ✓ (Buzz 보관) | ✓ (신설) |
| R4 쓰기 실행 | ✓ | ✓ (broker 제공) | ✓ | △ 자체 구현 |
| R5 OPAL 결합 | ✗ | **✓ 최상** | △ 브리지 품질 | ✓ |
| 멀티 런타임(codex 등) | ✓ | ✓ 무상 | ✓ | ✗ 런타임마다 구현 |
| 구현 규모(추정) | 없음 | **L** | **S~M** | **M~L** |
| 원칙 반전 건수 | 0 | 4 | 1 | 4 |
| 외부 종속 | Buzz | ACP 0.x 스키마 | Buzz + Nostr relay | 없음 |
| 되돌리기 | 즉시 | 어려움 | 쉬움 | 어려움 |

---

## 7. 권고

### 7.1 결론

**단계적 접근을 권고한다. 지금 A안을 착수하지 않는다.**

이유는 셋이다.

1. **§3.1이 아직 안 닫혔다.** Buzz 채널의 cwd가 프로젝트 루트면 0안이 R1~R4를 비용 0으로 제공한다. 이 확인 전에 L 규모를 착수하는 것은 순서가 틀렸다.
2. **A안의 가치는 R5 하나에 걸려 있다.** R1~R4는 Buzz가 이미 준다. 콘솔에 지어야 할 유일한 이유는 "칸반·state·brain·memory와 같은 화면에서, 그 프로젝트에 바인딩된 PM과 대화한다"는 결합이다. 이 결합의 실제 효용이 L 규모를 정당화하는지는 아직 검증되지 않았다.
3. **선행 정리가 A안과 무관하게 이득이다.** 런타임 하드코딩 제거(§7.2 S1)는 어느 안으로 가든 필요하고, 원칙을 하나도 건드리지 않는다.

### 7.2 단계

| 단계 | 내용 | 규모 | 원칙 반전 | 선행 |
|------|------|:---:|:---:|------|
| **S0** | §3.1 확인 — Buzz 에이전트 cwd를 프로젝트 루트로 잡고 부트스트랩 2줄에 `✅ PM모드`가 뜨는지 실측 | 30분 | 0 | — |
| **S1** | `~/.opal/setting.json`에 `runtimes` 키 신설(§7.3) + `opbr_adapter` 하드코딩 제거 | S | 0 | — |
| **S2** | 인증·권한 모델 확정 (§5.1 결정) — 문서 결정, 구현 아님 | S | 0 | S1 |
| **S3** | 파이썬 ACP SDK 스파이크 — `claude-agent-acp` 1개 띄워 한 턴 왕복 + 스트리밍 수신 확인 | S | 0 | S2 |
| **S4** | 이후 분기: S0 결과와 S3 실측으로 A안/B안 확정 | — | — | S0·S3 |

S0~S3은 전부 되돌릴 수 있고 원칙을 건드리지 않는다. **되돌릴 수 없는 결정은 S4에 모아 둔다.**

### 7.3 런타임 등록 스키마 (S1 제안)

Buzz도 런타임과 모델을 분리 보관한다(§2.1). OPAL의 `models`는 레벨→모델명 매핑이라 층이 다르므로, 경쟁 SSOT가 아니라 **나란히 두는 것**이 정합적이다.

```jsonc
// ~/.opal/setting.json
{
  "models":   { /* 기존 — 플랫폼 x 레벨 → 모델명. 무변경 */ },
  "runtimes": {                      // 신설
    "claude": {
      "command": "claude",           // 또는 ACP 어댑터 경로
      "args": [],
      "env": {},                     // 예: CLAUDE_CODE_EXECUTABLE
      "protocol": "cli"              // "cli" | "acp"
    }
  }
}
```

`protocol` 필드가 C안과 A안을 같은 스키마로 수용한다 — S4 분기 결과와 무관하게 S1을 먼저 해도 손실이 없다.

---

## 8. 미확인 항목 (추정과 사실의 분리)

| # | 항목 | 왜 중요한가 | 확인 방법 |
|---|------|------------|----------|
| U1 | Buzz 에이전트/채널이 **cwd를 프로젝트 루트로 잡는지** | **0안 성립 여부 = 이 검토의 분기점**(§3.1) | S0 실측 |
| U2 | Buzz relay 운영 형태 | B안의 실제 비용. 로컬 3000 미가동·`BUZZ_*` 미설정 확인됨 | `buzz` CLI 설정 확인 |
| U3 | 파이썬 ACP SDK가 `claude-agent-acp`와 실제로 물리는지 | A안의 전제. JS SDK는 1.3.0, 파이썬은 0.12.1로 번호 체계가 달라 스키마 호환을 실측해야 함 | S3 스파이크 |
| U4 | 콘솔 asyncio 전환 시 웜풀 락 순서 계약 재설계 범위 | A안 규모 추정의 최대 오차원 | S3 이후 |
| U5 | R5 결합의 실제 효용 | A안 정당화의 근거. 현재는 가설 | S0 이후 Buzz를 실사용해 결핍을 실측 |

---

## 9. 캡틴 결정이 필요한 것

| # | 질문 | 기본 권고 |
|---|------|----------|
| D1 | S0(30분 실측)을 먼저 하는 데 동의하는가 | **예** |
| D2 | 쓰기 실행(R4)을 열 때 하네스 승인 게이트를 채널 안에 둘 것인가, bypass할 것인가 | **채널 안에 둔다** (§5.1) |
| D3 | 콘솔 "읽기 전용"·"무상태" 원칙을 반전할 의사가 있는가 | S4까지 보류 |
| D4 | S1(런타임 스키마 정리)을 S0 결과와 무관하게 선행할 것인가 | **예** — 어느 안이든 필요 |

---

## 참고

- [Agent Client Protocol — Python](https://agentclientprotocol.com/libraries/python)
- [PyPI: agent-client-protocol](https://pypi.org/project/agent-client-protocol/)
- [ACP Python SDK 문서](https://agentclientprotocol.github.io/python-sdk/)
- 프로젝트 내부: `docs/ARCHITECTURE.md` §OPAL Console / `docs/SECURITY.md` §1 / `dashboard/backend/adapters/brain_session.py` / `dashboard/backend/adapters/opbr_adapter.py`
