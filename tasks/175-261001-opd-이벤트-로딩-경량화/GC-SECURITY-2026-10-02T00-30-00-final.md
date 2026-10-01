# GC SECURITY REPORT — 2026-10-02T00-30-00 (final)

## 1. 헤더

- 실행 일시: 시작 2026-10-02 00:09 / 완료 2026-10-02 00:14 (KST)
- 범위: `명시 target_files` / 대상 파일 20개 (py 4 + AGENT.md 16)
- 에이전트: opal-security-checker (dispatch dsp-f1b5f3ff66c345f5aae2ef0e77000fbc)
- APPLY 수행 여부: N (read-only, 수동 대기)
- 이전 보고서: `GC-SECURITY-2026-10-02T00-03-00.md` 수정분 재검증 + 새 우회 탐색

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 5 |
| 심각도 분포 | Critical 0 / High 0 / Medium 1 / Low 3 / Info 1 |
| 자동 수정 가능 | 1 |
| 수동 조치 필요 | 3 |
| 파일별 상위 | event_loader.py (3건) / 액션 에이전트 AGENT.md 3종 (1건, 공통 문장) / gates.py (1건, info) |
| disposition | blocking 1 / advisory 3 / informational 1 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |
| 이전 finding 해소 | GC-001 원 경로 해소(잔여 변형 GC-008) / GC-002 해소 / GC-003 진입 게이트 해소(잔여 GC-009) / GC-005 해소 / GC-004·GC-006 이월 |
| 판정(스키마 §6) | FAIL — 모든 check 실행, missing_capabilities 0, blocking 1건(GC-008) |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (1건)

- [ ] GC-008 [opal/tools/event-loader/event_loader.py:686] CWE-345 Insufficient Verification of Data Authenticity (manifest provenance, GC-001 잔여 변형)
  - 위반 기준: CWE-345 / OWASP-A08 / tier T1 / disposition blocking / confidence high / fingerprint `75bf656b0876993d`
  - 관측: verify_receipt는 여전히 --manifest가 없으면 receipt.manifest_path를 그대로 채택한다(686-688행). GC-001의 수정 (1)(contract_not_declared)은 들어갔지만 (2)(manifest 경로를 실행 경계에서 결정)는 적용되지 않았다. 재현(R4): worker.dispatch의 contract는 유지하고 required_docs를 observability 1건으로 줄이고 selection을 지운 사본 manifest로 `load --manifest <사본> --contract-version 2 --agent opal-security-checker --role checker --dispatch-id dsp-forged-0001`을 만든 뒤 --manifest 없이 같은 인자로 verify하면 event_loader 직접 호출과 state-tool event-verify 모두 ok:true, contract:2, dispatch_id·agent.name·role 일치, verified_document_count:1로 통과했다. 결과의 manifest_path는 scratchpad 사본을 가리켰다. 대조군: --manifest <실제 events.json>를 고정하면 document_hash_mismatch로 거부된다.
  - 영향: 개정된 워커 게이트 4항의 성공 조건(ok·contract==2·dispatch_id·agent.name·role)을 모두 만족하면서 events.json SSOT와 다른 문서 집합(필수 규칙 문서 누락, selection 미적용 등)으로 워커를 진행시킬 수 있다. receipt와 manifest를 쓸 수 있는 주체(오동작한 PM·액션 에이전트·임시 폴더 쓰기 가능 프로세스)가 대상이다. 식별자 결속은 이제 강제되므로 GC-001보다 영향 범위는 좁다.
  - 해결 방안: verify의 manifest를 receipt가 아니라 실행 경계(_default_manifest 또는 호출자의 명시 --manifest)에서 결정하고, receipt.manifest_path가 그 경로와 다르면 stale_receipt(또는 manifest_mismatch)로 거부한다. 테스트에서 사본 manifest로 load한 경우 verify에도 같은 --manifest를 넘기도록 맞춘다. 보조책으로 게이트 4항에 결과 manifest_path가 실행 경계 manifest와 같은지 확인하는 조건을 더할 수 있다.
  - 자동 수정: N
  - 검증: 사본 manifest(계약 유지, 문서 축소)로 만든 v2 receipt를 --manifest 없이 verify하면 ok:false가 되는 회귀 테스트가 통과하고, 기존 정상 경로 테스트는 유지된다.
  - 참조: https://cwe.mitre.org/data/definitions/345.html

### Low (3건)

- [ ] GC-009 [opal/agents/opal-task-action-agent/AGENT.md:28] CWE-693 Protection Mechanism Failure (하위 디스패치 성공 조건)
  - 위반 기준: CWE-693 / tier T1 / disposition advisory / confidence medium / fingerprint `4bdd559dfdb406b4`
  - 관측: 16개 진입 게이트 4항은 결과의 contract==2와 dispatch_id·agent.name·role 일치를 성공 조건으로 갖게 됐다(GC-003 해소). 다만 액션 에이전트 3종의 하위 디스패치 문장(opal-task-action-agent:28, opal-sdd-action-agent:27, opal-loop-action-agent:30)은 'verify를 통과시킨다'와 '`ok: true` 검증 결과를 주입'만 적고 같은 결과 필드 확인을 요구하지 않는다. dispatch-process.md Step 0-4에는 해당 조건이 있다.
  - 영향: loader 측 우회가 다시 생기면 하위 디스패치 경로가 진입 게이트보다 약한 기준으로 진행된다. 현재 loader가 v2 인자 결속과 contract_not_declared를 강제하므로 단독 영향은 낮다.
  - 해결 방안: 3종 하위 디스패치 문장에 'verify 결과가 ok: true이고 contract가 2이며 dispatch_id·agent.name·role이 하위 호출 값과 같을 때만 호출한다'를 추가한다. static-check 문구 검사 대상에 포함할 수 있다.
  - 자동 수정: Y
  - 검증: 3종 AGENT.md 하위 디스패치 문장에 결과 필드 확인 조건이 있다.
  - 참조: https://cwe.mitre.org/data/definitions/693.html

- [ ] GC-004 [opal/tools/event-loader/event_loader.py:414] CWE-73 External Control of File Name or Path
  - 위반 기준: CWE-73 / tier T1 / disposition advisory / confidence high / fingerprint `e06f2b9e8e53358a`
  - 관측: 이전 보고서에서 이월(알려진 한계, 후속 후보). 재확인: `load --event worker.dispatch <v2 인자> --role-doc /etc/hosts`가 ok:true이며 receipt.role_doc에 /private/etc/hosts 경로와 sha256이 기록됐다. 루트 제한·일반 파일·크기 상한 검사가 없다. 빈 문자열(cwd 디렉터리)은 OSError로 contract_arg_invalid가 되어 fail-closed다.
  - 영향: 임의 파일 존재·해시 오라클, FIFO·장치 경로 지정 시 블로킹·메모리 소모. 내용 유출은 없고 동일 로컬 사용자 범위다.
  - 해결 방안: role_doc을 project_root/source_root/deployed_root 하위 일반 파일(is_file, 크기 상한)로 제한하고 밖이면 path_outside_root로 거부한다.
  - 자동 수정: N
  - 검증: 루트 밖 경로·FIFO를 --role-doc으로 넘기면 즉시 거부되는 테스트.
  - 참조: https://cwe.mitre.org/data/definitions/73.html

- [ ] GC-006 [opal/tools/event-loader/event_loader.py:345] CWE-778 Insufficient Logging / CWE-15 External Control of System Setting
  - 위반 기준: CWE-778 / tier T1 / disposition advisory / confidence medium / fingerprint `c16860701fb2d825`
  - 관측: 이전 보고서에서 이월(알려진 한계, 후속 후보). 코드 변화 없음: OPAL_EVENT_LOADER_LEDGER·OPAL_EVENT_LOADER_NOW가 운영 경로에서 무조건 적용되고(338·345행), 원장 쓰기 실패는 경고만 남긴다(363-364행). 이번 재현도 이 변수로 원장을 scratchpad에 격리했다.
  - 영향: legacy-report 집계(legacy_accepted 종료 판단 근거)의 시각 위조·경로 전환·누락 은폐 가능. 동일 사용자 권한 범위.
  - 해결 방안: 테스트 전용 플래그가 있을 때만 override를 적용하거나 override 사용을 응답 warnings에 남긴다. 쓰기 실패를 legacy-report에서 확인할 수 있게 한다.
  - 자동 수정: N
  - 검증: override 시 경고가 표시되고 쓰기 실패가 집계에 반영되는 테스트.
  - 참조: https://cwe.mitre.org/data/definitions/778.html

### Info (1건)

- [ ] GC-010 [opal/tools/state-tool/state_tool_parts/gates.py:2676] CWE-757 / CWE-636 / CWE-1286 수정 재현 확인 (no issue observed)
  - 위반 기준: CWE-757 / tier T1 / disposition informational / confidence high / fingerprint `654350f80401e20d`
  - 관측: 재현으로 해소 확인. GC-001 원 경로(R1): contract·selection을 지운 사본 manifest receipt에 v2 인자(엉뚱한 dispatch_id)로 verify -> loader·state-tool 모두 contract_not_declared(ok:false). --role-doc 하나만 줘도 같은 거부. pilot.start에 v2 인자로 load -> contract_not_declared(R5). GC-002(R2): 구형 receipt에 state-tool로 4개 빈 인자 -> contract_arg_invalid, --dispatch-id ''만 빈 값 -> contract_arg_invalid, --role-doc ''만 -> contract_args_missing. GC-005(R3): 4개 인자 각각 끝 개행 -> contract_arg_invalid, 전각 숫자 버전 '２' -> contract_arg_invalid. GC-003: 16개 AGENT.md 진입 게이트 4항에 contract==2·dispatch_id·agent.name·role 일치 조건 존재. state-tool -> loader 호출은 shell=False argv 리스트이고, project_brief의 subprocess도 고정 argv와 timeout을 쓴다. 하드코딩 시크릿 없음.
  - 영향: 해당 없음(관측 결과 기록).
  - 해결 방안: 현행 유지. R1~R5를 회귀 테스트로 고정하는 것을 권장한다.
  - 자동 수정: N
  - 검증: 해당 없음.

---

## 4. 문서 업데이트 제안

- 해당 없음 (이전 GC-DP-001 제안이 GC-008 해소 방향과 같아 신규 제안을 만들지 않는다. 반영은 소유자 승인 후)

## 5. 문서 작성 유도

- 해당 없음 (docs/SECURITY.md 존재)
