# Final Gate 보안 검사 (read-only, 1회) — task 172

대상: convention_precheck.py, state_tool.py(_previous_gaps_for / design-gate combine 구간), scripts/tests/test_agent_effort_policy.sh, scripts/install-mac.sh(convention-precheck chmod 블록)
기준: 셸 인젝션, 임시 파일, 경로 이탈, 비밀 노출, JSON 역직렬화. Critical/High 0건.

| # | Sev | 파일 | 내용 | 권고 |
|---|-----|------|------|------|
| 1 | Low | convention_precheck.py (run_git/CodeScanClient.call) | 모든 subprocess가 argv 리스트, shell=True 없음 -> 셸 인젝션 없음. 다만 변경 파일명(rel)이 `-`로 시작하면 `code-scan target/scan <rel>`에서 옵션으로 해석될 수 있음(git 쪽은 `--`와 `rev:path` 형태라 안전). | rel 앞에 `--` 삽입 또는 `./` 접두 |
| 2 | Low | convention_precheck.py base_header_of | mkdtemp(0700) + finally rmtree. dest = tmp/rel 이며 rel은 git이 내놓은 저장소 상대경로라 `..` 불가. 심볼릭 링크는 `git show` blob 바이트를 일반 파일로 기록하므로 링크 추종 없음. | 조치 불필요 |
| 3 | Low | convention_precheck.py (--target-files, --code-scan) | `--target-files`는 norm_rel 후 changed 집합과의 교집합만 사용(경로 이탈 무영향). `--code-scan`은 임의 경로를 node로 실행하나 호출자(PM) 제어 CLI 인자 -> 신뢰 경계 내. | 문서에 신뢰 인자 명시 정도 |
| 4 | Low | convention_precheck.py CodeScanClient.__init__ | `.opal/code-scan.json`을 json.loads. 형식 오류는 처리하나 `extensions`/`exclude`가 잘못된 타입(예: 숫자)이면 is_code_file에서 TypeError 비처리 가능(DoS 수준, 코드 실행 아님). | 타입 검증 추가 |
| 5 | Info | state_tool.py _previous_gaps_for | iteration은 bool 제외 int 검증 후 `run/design-gate-i{k}.json`만 읽음 -> 경로 이탈 불가. json.loads 후 dict/str 타입 검사, 예외(OSError, ValueError) 처리. 역직렬화는 JSON 한정(pickle/yaml 없음). | 조치 불필요 |
| 6 | Low | state_tool.py cmd_design_gate_combine | `--design-result/--scenario-result/--output`은 CLI가 준 임의 경로를 읽고/쓴다(경로 제한 없음). 출력은 같은 디렉터리 mkstemp + os.replace로 원자적이고 실패 시 unlink. mkstemp 때문에 산출 파일 권한이 0600(기능상 무해). 입력은 타입·id 집합·bundle_hash 검증. 읽기 전용으로 state.json은 수정하지 않음. | 필요 시 --output이 task 폴더 하위인지 검증 |
| 7 | Info | scripts/install-mac.sh | `chmod +x $opal_home/tools/convention-precheck/run.sh` 고정 경로, 파일 존재 확인 후 실행. 인용 처리됨. 심볼릭 링크면 대상에 +x가 붙는 정도(배포 디렉터리는 설치자 소유). | 조치 불필요 |
| 8 | Info | test_agent_effort_policy.sh | mktemp -d + trap rm -rf, 실제 opal/agents 미수정, 네트워크 미사용, heredoc은 인용된 센티넬로 확장 없음. | 조치 불필요 |
| 9 | Info | 전체 | 하드코딩된 비밀·토큰·자격증명 없음 (grep token/secret/password 0건). run.sh는 $HOME venv 경로 사용. | - |

판정: 보안 Pass (차단 이슈 없음, Low 4건 권고).
