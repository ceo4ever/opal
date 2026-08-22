`opal/tools/` 하위 19개 도구 디렉토리의 규모(run.sh 유무·README 줄 수·소스 파일 수)를 실측 정리해 달라는 요청으로 이해했습니다.
▶ 다음 액션: 실측 결과 확인 (소요: 5분)

---

## 🎯 결론·근거

> **1️⃣ code-scan이 핵심 소스 규모 최대이면서 문서는 전무 [상]**
- `code-scan/code-scan.js` 1개 파일이 3,651줄로 전체 도구 중 단일 파일 기준 최대다.
- `code-scan/` 디렉토리에는 `README.md` 자체가 없어 README 줄 수가 0이다.
**code-scan은 규모와 문서화 수준의 격차가 19개 도구 중 가장 크다.**

> **2️⃣ README 부재 도구가 19개 중 9개(47%) [중]**
- `date`·`git-sync-tool`·`improve-tool`·`playwright-tool`·`code-scan`·`skill-registry`·`tool-scan`·`worktree-tool`·`xlsx-tool` 9개에 README.md가 없다.
- 이 중 `worktree-tool`은 핵심 소스가 1,049줄로 README 부재 도구 중 규모가 두 번째로 크다.
**README 부재는 소수 예외가 아니라 절반에 가까운 비율이다.**

> **3️⃣ run.sh 부재는 2개뿐, 이미 표준화된 축 [하]**
- `date`·`skill-registry` 2개 도구만 run.sh가 없다.
**run.sh 체계는 19개 중 17개(89%)에서 이미 정착돼 있다.**

| 도구 | run.sh | README 줄 | 핵심 소스 파일 수 | 핵심 소스 줄 수 |
|---|---|---|---|---|
| `code-scan` | ✅ | 0 | 2 | 3,841 |
| `state-tool` | ✅ | 420 | 2 | 3,061 |
| `memory-tool` | ✅ | 326 | 1 | 1,611 |
| `test-tool` | ✅ | 368 | 6 | 1,589 |
| `brain-tool` | ✅ | 142 | 1 | 1,346 |

---

## 📌 잔여·보류·유의

- 핵심 소스 파일 수는 `*.py`/`*.js`/`*.mjs`/`*.ts` 확장자만 집계했다 — `opal-cli`·`cmux-tool`·`doctor`는 셸 스크립트(`lib/*.sh`) 기반이라 이 지표에서 0으로 잡힌다(유의).
- `code-scan/tests/` 하위 85개 테스트·픽스처 파일은 핵심 소스 집계에서 제외했다(유의).
- 디스크 용량(`du -sh`) 기준 1위는 `state-tool`(2.2M)이나 그중 1.8M이 `tests/`이므로 규모 지표로는 핵심 소스 줄 수를 채택했다(유의).
