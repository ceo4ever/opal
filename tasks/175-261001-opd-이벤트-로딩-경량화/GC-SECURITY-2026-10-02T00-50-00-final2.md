# GC SECURITY REPORT — 2026-10-02T00-50-00 (final2)

## 1. 헤더

- 실행 일시: 시작 2026-10-02 00:15 / 완료 2026-10-02 00:24 (KST)
- 범위: `명시 target_files` / 대상 파일 20개 (py 4 + AGENT.md 16)
- 에이전트: opal-security-checker (dispatch dsp-3dd987f6c07c4863875fb9f5a44485d6)
- APPLY 수행 여부: N (read-only, 수동 대기)
- 이전 보고서: `GC-SECURITY-2026-10-02T00-30-00-final.md` — GC-008·GC-009 수정분 재검증 + 새 우회·회귀 탐색

---

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 5 |
| 심각도 분포 | Critical 0 / High 0 / Medium 0 / Low 4 / Info 1 |
| 자동 수정 가능 | 1 |
| 수동 조치 필요 | 3 |
| 파일별 상위 | event_loader.py (5건, info 1 포함) |
| disposition | blocking 0 / advisory 4 / informational 1 |
| Critical/High 수 | 0 |
| 문서 업데이트 제안 수 | 0 |
| 이전 finding 처리 | GC-008 해소 / GC-009 해소 / GC-004·GC-006 이월(advisory) / 신규 GC-011·GC-012(advisory) |
| 판정(스키마 §6) | PASS_WITH_ADVISORIES — check status pass, missing_capabilities 0, blocking 0 |

---

## 3. 수정 대상 (체크리스트)

### Critical (0건)

### High (0건)

### Medium (0건)

### Low (4건)

- [ ] GC-011 [opal/tools/event-loader/event_loader.py:332] CWE-41 Improper Resolution of Path Equivalence (manifest 경로 비교 비대칭 정규화)
  - 위반 기준: CWE-41 / tier T1 / disposition advisory / confidence high / fingerprint `9bf4f8c32eb1efe0`
  - 관측: verify_receipt 688행은 receipt.manifest_path를 Path.resolve()로 정규화하지만, 비교 상대인 실행 경계 manifest_path는 --manifest가 없을 때 _default_manifest(125-128행)가 deployed_root(또는 source_root)/references/events.json을 resolve 없이 반환한다(332행). load도 같은 미정규화 값을 receipt에 기록한다. 재현(R3): 배포본 사본 루트의 references/events.json을 내용 동일한 파일로의 심볼릭 링크로 바꾸고 --deployed-root(또는 OPAL_DEPLOYED_ROOT)로 load -> 같은 인자로 verify하면 정당한 receipt가 stale_receipt(ok:false)로 거부됐다. 현재 ~/.opal/references/events.json은 일반 파일이라 실제 설치 경로에서는 재현되지 않는다.
  - 영향: events.json을 심볼릭 링크로 배치한 설치(개발용 링크 설치, dotfiles 관리 등)에서 모든 worker.dispatch가 fail-closed로 차단된다. 우회가 아니라 가용성 회귀이며 보안 경계는 약화되지 않는다.
  - 해결 방안: _context에서 기본 manifest 경로도 .resolve()로 정규화해 양쪽을 같은 규칙으로 비교한다(또는 _default_manifest 반환값을 resolve). 심볼릭 링크 events.json으로 load->verify가 ok:true인 회귀 테스트를 추가한다.
  - 자동 수정: Y
  - 검증: references/events.json이 심볼릭 링크인 배포 루트에서 load 후 같은 인자 verify가 ok:true이고, 다른 파일을 가리키는 receipt는 여전히 stale_receipt.
  - 참조: https://cwe.mitre.org/data/definitions/41.html
- [ ] GC-012 [opal/tools/event-loader/event_loader.py:136] CWE-15 External Control of System or Configuration Setting (실행 경계 재정의, GC-008 잔여 신뢰 가정)
  - 위반 기준: CWE-15 / tier T1 / disposition advisory / confidence high / fingerprint `0f015551fb44e60b`
  - 관측: GC-008 수정으로 receipt는 manifest를 고를 수 없게 됐지만 실행 경계 자체는 호출 인자(--manifest, --source-root, --deployed-root)와 환경변수 OPAL_DEPLOYED_ROOT(136행)로 바뀐다. state-tool event-verify도 이 인자들을 그대로 전달한다(gates.py 2666-2668행). 재현(R5): 문서를 observability 1건으로 줄이고 selection을 지운 events.json을 가진 사본 배포 루트로 OPAL_DEPLOYED_ROOT=<사본> load -> 같은 env로 state-tool event-verify가 ok:true, contract:2, dispatch_id·agent.name·role 일치, verified_document_count:1. 결과 manifest_path는 사본을 가리킨다. 같은 receipt를 env 없이 verify하면 stale_receipt. 명시 --manifest <사본>도 같은 결과(R1 대조군). 진입 게이트 4항과 dispatch-process Step 0-4의 성공 조건은 결과 manifest_path를 확인하지 않는다.
  - 영향: PM·워커 프로세스의 환경변수나 verify 명령 인자를 제어할 수 있는 주체는 SSOT와 다른 문서 집합으로 게이트를 통과시킬 수 있다. 동일 로컬 사용자 권한이 전제이며 receipt 파일 위조만으로는 불가능하므로 GC-008보다 공격 전제가 크게 높다. GC-006(env override)과 같은 신뢰 등급이다.
  - 해결 방안: 실행 경계가 기본값에서 벗어났을 때(--manifest/--source-root/--deployed-root/OPAL_DEPLOYED_ROOT 사용) verify 결과에 boundary_overridden 경고를 싣거나, 게이트 성공 조건에 결과 manifest_path가 기본 설치 경로(~/.opal/references/events.json 또는 소스 모드 경로)와 같음을 추가한다. 테스트 전용 override는 명시 플래그로 한정하는 방안을 GC-006과 함께 검토한다.
  - 자동 수정: N
  - 검증: OPAL_DEPLOYED_ROOT 또는 --manifest로 경계를 바꾼 verify 결과에 경고가 나타나거나 게이트가 이를 거부한다.
  - 참조: https://cwe.mitre.org/data/definitions/15.html
- [ ] GC-004 [opal/tools/event-loader/event_loader.py:414] CWE-73 External Control of File Name or Path (--role-doc 경로 제한 없음, 이월)
  - 위반 기준: CWE-73 / tier T1 / disposition advisory / confidence high / fingerprint `e06f2b9e8e53358a`
  - 관측: 알려진 한계(후속 후보)로 이월. 412-419행 코드 변화 없음: --role-doc 경로를 resolve 후 read_bytes만 하며 루트 제한·일반 파일·크기 상한 검사가 없다. 이전 실행 재현(/etc/hosts 지정 시 ok:true, 경로·sha256 기록)과 동일 조건.
  - 영향: 임의 파일 존재·해시 오라클, FIFO·장치 경로 지정 시 블로킹·메모리 소모. 내용 유출은 없고 동일 로컬 사용자 범위.
  - 해결 방안: role_doc을 project_root/source_root/deployed_root 하위 일반 파일(is_file, 크기 상한)로 제한하고 밖이면 path_outside_root로 거부한다.
  - 자동 수정: N
  - 검증: 루트 밖 경로·FIFO를 --role-doc으로 넘기면 즉시 거부되는 테스트.
  - 참조: https://cwe.mitre.org/data/definitions/73.html
- [ ] GC-006 [opal/tools/event-loader/event_loader.py:345] CWE-778 Insufficient Logging / CWE-15 (원장·시각 env override, 이월)
  - 위반 기준: CWE-778 / tier T1 / disposition advisory / confidence medium / fingerprint `c16860701fb2d825`
  - 관측: 알려진 한계(후속 후보)로 이월. 337-364행 코드 변화 없음: OPAL_EVENT_LOADER_LEDGER·OPAL_EVENT_LOADER_NOW가 운영 경로에서 무조건 적용되고, 원장 쓰기 실패는 경고만 남긴다. 이번 재현도 이 변수로 원장을 scratchpad에 격리했다.
  - 영향: legacy-report 집계(legacy_accepted 종료 판단 근거)의 시각 위조·경로 전환·누락 은폐 가능. 동일 사용자 권한 범위.
  - 해결 방안: 테스트 전용 플래그가 있을 때만 override를 적용하거나 override 사용을 응답 warnings에 남긴다. 쓰기 실패를 legacy-report에서 확인할 수 있게 한다.
  - 자동 수정: N
  - 검증: override 시 경고가 표시되고 쓰기 실패가 집계에 반영되는 테스트.
  - 참조: https://cwe.mitre.org/data/definitions/778.html

### Info (1건)

- [ ] GC-013 [opal/tools/event-loader/event_loader.py:688] CWE-345 / CWE-693 수정 재현 확인 (GC-008·GC-009 해소, no issue observed)
  - 위반 기준: CWE-345 / tier T1 / disposition informational / confidence high / fingerprint `987d3f6e2a35fef7`
  - 관측: GC-008 해소 재현: (R1) 계약 유지·문서 1건으로 축소한 사본 manifest로 v2 load한 receipt를 --manifest 없이 verify -> 설치본 loader, state-tool event-verify, 워크트리 loader 모두 stale_receipt(ok:false). (R2) receipt.manifest_path(외곽·내부 receipt 양쪽)를 실제 ~/.opal/references/events.json으로 바꿔도 document_hash_mismatch(manifest 내용 sha와 선별 재수행 해시로 거부). (R4) 정상 receipt의 manifest_path를 같은 파일의 별칭(심볼릭 링크 디렉터리 경유, ../. 포함, ~ 시작)으로 바꾸면 ok:true — 모두 같은 실제 파일로 해석되고 내용은 manifest_sha256으로 결속되므로 우회가 아니다. 상대 경로는 cwd 기준이며 같은 실제 파일일 때만 통과. manifest_path 누락·비문자열(123)은 stale_receipt. 정당한 경로: 이번 디스패치 receipt(wd-sec3.json)와 새 v2 receipt는 설치본 verify ok:true. 워크트리(소스 모드) loader로 설치본 receipt를 verify하면 stale_receipt인데, 실행 경계가 다른 매니페스트를 쓰므로 의도된 fail-closed다. 회귀 테스트 test_verify_without_manifest_rejects_receipt_from_copied_manifest 존재. GC-009 해소: 액션 에이전트 3종(task-action:28, sdd-action:27, loop-action:30) 하위 디스패치 문장에 'verify 결과가 ok: true이고 contract가 2이며 dispatch_id·agent.name·role이 하위 프롬프트에 주입할 값과 같을 때만 호출' 조건이 추가됨. 16개 AGENT.md 진입 게이트 4항 모두 동일 조건 유지. agent_sections.py·cli.py는 보안 관련 변경 없음(subprocess는 shell=False argv 리스트). 하드코딩 시크릿 없음.
  - 영향: 해당 없음(관측 결과 기록).
  - 해결 방안: 현행 유지. R2(manifest_path 재기록)와 R4(별칭) 케이스를 회귀 테스트로 고정할 것을 권장한다.
  - 자동 수정: N
  - 검증: 해당 없음.

---

## 4. 문서 업데이트 제안

- 해당 없음 (트리거 미발동)

## 5. 문서 작성 유도

- 해당 없음 (docs/SECURITY.md 존재)

## 6. 비보안 관측 (판정 미반영)

- event-loader 테스트 2건 실패: `test_static_check_ok`(opal-pilot-dev2 SKILL.md에 stage.analysis·stage.test_scenario·stage.close event_contract_missing), `test_project_brief_cli_preserves_inputs_and_multitask_counts`('경로 이상 1건' 문구 누락). 보안 범위 밖이므로 호출자 확인 필요.
