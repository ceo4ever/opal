`opal/tools/` 19개 도구 실측 결과를 공유한다.
▶ 다음 액션: 문서 부재 9개 도구 중 활성 사용 도구(git-sync-tool·worktree-tool·tool-scan)부터 README 작성 착수 (소요: 2시간)

## 🎯 결론·근거

> **1️⃣ code-scan이 규모 1위, 문서는 0줄 [상]**
- `opal/tools/code-scan/`은 소스 파일 87개(`.py`/`.js`/`.ts`)로 19개 도구 중 최다다.
- `code-scan/README.md`가 존재하지 않아 문서 줄 수 0이다.
**규모 1위 도구가 동시에 문서 공백 도구다.**

> **1️⃣ state-tool이 문서 1위, README 420줄 [상]**
- `state-tool/README.md` 420줄로 19개 도구 중 최장이며 소스 파일도 4개다.
- 근접 도구는 `test-tool`(368줄, 소스 8개), `memory-tool`(326줄, 소스 2개)이다.
**핵심 도구(state·test·memory)는 문서-코드 비율이 균형적이다.**

> **2️⃣ README.md 자체가 없는 도구 9개 [중]**
- `code-scan`, `git-sync-tool`, `improve-tool`, `playwright-tool`, `tool-scan`, `worktree-tool`, `xlsx-tool`, `skill-registry`, `date` 9개는 README.md 파일 자체가 없다(0줄이 아니라 파일 부재).
- 이 중 `run.sh`도 없는 도구는 `date`, `skill-registry` 2개뿐이다.
**문서 부재 9개 중 7개는 실행 도구(run.sh 보유)인데 README만 없다.**

| 도구 | run.sh | README 줄수 | 소스 파일 수 |
|---|---|---|---|
| code-scan | ✅ | 0 | 87 |
| test-tool | ✅ | 368 | 8 |
| skill-registry | ❌ | 0 | 4 |
| state-tool | ✅ | 420 | 4 |
| tool-scan | ✅ | 0 | 4 |
| worktree-tool | ✅ | 0 | 3 |
| git-sync-tool | ✅ | 0 | 3 |
| brain-tool | ✅ | 142 | 2 |
| memory-tool | ✅ | 326 | 2 |
| improve-tool | ✅ | 0 | 2 |
| opal-agent | ✅ | 242 | 2 |
| backlog-tool | ✅ | 259 | 2 |
| xlsx-tool | ✅ | 0 | 1 |
| date | ❌ | 0 | 1 |
| playwright-tool | ✅ | 0 | 1 |
| opal-action-monitor | ✅ | 132 | 1 |
| cmux-tool | ✅ | 224 | 0 |
| doctor | ✅ | 118 | 0 |
| opal-cli | ✅ | 162 | 0 |

## 📌 잔여·보류·유의

- README 부재 9개 도구는 코드 내 주석·docstring 수준의 자체 문서화 여부는 이번 조사 범위 밖이다(파일 존재 여부만 실측).
- `cmux-tool`·`doctor`·`opal-cli`는 소스 파일 수 0으로 집계됐다 — 쉘 스크립트(`run.sh`) 중심 구조일 가능성이 있어 별도 확인이 필요하다.

완료: 19/19
