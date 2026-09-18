# DONE — 132 OPPB 프로젝트빌드 파일럿 신설

## 무엇을 만들었나

확정된 실행 계약을 capability 단위 미니 태스크로 소화하는 신규 Pilot `oppb`
(`opal-pilot-project-build`)를 만들었다. 기존 OPPD를 교체하지 않고 병존한다 —
이 프레이밍 전환이 태스크의 출발점이었고, 27회 벤치마크·freeze tag·revert 기계를
전부 없애 단일 `//opd` 태스크로 수행 가능하게 만들었다.

### 신규 자산
| 자산 | 내용 |
|---|---|
| `opal/skills/opal-pilot-project-build/` | `//oppb` Product Flow(533행) + `references/pipeline.json` P0~P5 22행 |
| `opal/agents/opal-capability-agent/` | OPPB의 **유일한** 신규 owner 에이전트(210행) |
| `opal/skills/op-oppb-project-slice/` | capability 슬라이싱 단계 스킬(245행) |
| `opal/skills/op-oppb-knowledge-finalize/` | P5 지식 반영 단계 스킬(289행) |
| `opal/tools/oppb-runtime-tool/` | Controller·Supervisor·Lease·Evidence·Probe·Checkpoint·Cache·Recovery·Verifier adapter·Revalidation 12모듈 |

### 기존 자산 확장 (전부 additive, 제거 0건)
`state_tool.py` enum 2종 / `opal-skills-registry.json` / `agents.md` /
`harness/actor.md` / `opal-evaluator-agent`(acceptance phase) /
`op-scenario-gate`(OPPB 분기) / 프로젝트 문서 4종 / `install-mac.sh`

## 검증

| 스위트 | 결과 |
|---|---|
| oppb 런타임 | 130 passed |
| state-tool (신규 가드 포함) | 525 passed, 3 skipped, 339 subtests |
| 공용 도구 전체 | 1305+ passed |

잔여 실패 5건은 `tool-scan`의 상류 선재 결함이며 `git archive main` 대조로
태스크 132와 무관함을 확인했다.

## 실주행으로 드러난 결함 — 이 태스크의 실질 성과

RED 계약이 가정한 `project-run` 단일 진입점이 **존재하지 않고 존재해서도 안 되는
것**임을 밝히고 fixture를 실제 실행 주체대로 재구성한 것이 전환점이었다. 가짜
진입점을 걷어내고 실제로 돌리자 숨어 있던 결함이 드러났다.

1. **P5 pre-finalize guard가 상시 차단 상태** — `checkpoint.py`가 workgraph를
   `tasks`로 읽어 terminal 집합이 항상 공집합이었다(W-43).
2. **AC-12가 실주행에서 무동작** — `workgraph.json` 한 경로에 호환되지 않는 두
   문서 계약이 걸려 있었다. 동결 스키마로 흡수해 단일화했다(W-44~W-46).
3. **`profile` enum이 설계와 불일치** — §8은 fast/standard/critical인데 `full`이
   쓰이고 있었다.
4. **상태 어휘 이중화** — 동결 enum을 단일 SSOT로 확정했다.
5. **`//oppb` 무인 완주 서술이 제안서에도 있었다** — §13의 "18회 전부 무인
   headless"는 §4.1(P0~P2 무인 보장 제외)과 `p5.user_merge_gate`의 `--auto-pass`
   거부와 모순된다. 측정 구간을 P3~P4로 한정하도록 제안서와 PLAN을 정정했다.

다섯 건 모두 같은 뿌리다 — RED 계약 작성 시 구현·스키마를 참조하지 않고 자체
어휘를 만든 결과다.

## 실행 주체 — 오해하기 쉬운 지점

OPPB는 **프로젝트 전체를 무인으로 돌리지 않는다.**

| 구간 | 주체 | 무인 |
|---|---|---|
| P0~P2 | 대화형 세션(Product Flow) | 아니오 |
| P3~P4 | `start` 1회 → Supervisor headless | **예** |
| P5 | 대화형 세션 + 사용자 게이트 | 아니오 |

`p5.user_merge_gate`는 `--auto-pass`를 거부하고 소유자 발화를 요구한다.

## 이월

- **W-34 실주행 검증** — 소유자가 실제 프로젝트로 `//oppb`를 주행한 뒤 결과에
  따라 별도 태스크로 연다. 자동 18회 벤치마크는 측정 구간 정정(P3~P4 한정) 후에도
  9~16M 토큰·6~13시간 규모라 소유자 판단으로 보류했다.
- **미검증 구간** — P0~P2 대화형 구간과 P5 게이트·지식 반영은 실주행 검증 이력이
  없다. fixture로 확인한 것은 P3~P4뿐이다.
- **캐시 정확성** — cold/warm 최종 tree 동일성은 반복 측정이 필요하며 1회 주행으로
  판정할 수 없다.
- **W-36 최종 출시 판정** — W-34 결과가 있어야 차단 지표 5종을 판정할 수 있다.
- **상류 선재 결함 3건**(태스크 132 범위 밖) — CONVENTIONS alias 표의 `osw` 행
  누락, ARCHITECTURE의 `references/` 엔트리 표기 부정확, 트리의
  `opal-pilot-dev/` 행 중복.

## 남긴 상시 자산

`test_pilot_shared_contract.py`(W-49)는 이번 태스크 일회성이 아니다.
`opal-pilot-*`를 스캔해 발견되는 전부(현재 11종)에 공유 인프라 계약을 검사하므로
**앞으로 파일럿을 추가·수정할 때 그대로 회귀 판정에 쓴다.** 파일럿 목록·개수를
하드코딩하지 않는다.
