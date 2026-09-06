opal/tools/ 하위 19개 도구 디렉토리의 run.sh·README·소스파일 규모를 실측했다.
▶ 다음 액션: 문서 빈약 도구 목록을 확인한다 (소요: 5분)

---
## 🎯 결론·근거
> **1️⃣ 소스 파일 수 기준 최대 도구는 code-scan [상]**
- `code-scan/`은 `.js` 파일 22개(테스트 포함 총 11,743줄)로 19개 도구 중 파일 수 1위다.
- `state-tool/`은 파일 4개뿐이지만 총 12,422줄로 LOC 기준 1위다(`state_tool.py` 2,897줄 + 대형 테스트 파일 1개가 8,987줄).
**파일 수와 총 LOC 기준이 서로 다른 도구를 1위로 지목한다 — 규모 지표는 관점에 따라 달라진다.**
> **2️⃣ code-scan은 최대 규모임에도 README가 없다 [상]**
- 19개 디렉토리 중 10개(`backlog-tool`·`brain-tool`·`cmux-tool`·`doctor`·`memory-tool`·`opal-action-monitor`·`opal-agent`·`opal-cli`·`state-tool`·`test-tool`)만 `README.md`를 보유한다.
- `code-scan`·`tool-scan`·`worktree-tool`·`git-sync-tool`·`skill-registry`·`improve-tool`·`xlsx-tool`·`playwright-tool`·`date`는 README가 없다.
**소스 파일 수 1위·LOC 2위인 code-scan이 README 부재 9곳 중 하나로, 규모 대비 문서 공백이 가장 크다.**

---
## 📌 잔여·보류·유의
- `opal-cli`·`doctor`·`cmux-tool`은 README가 있으나 `.py`/`.js` 소스가 0건으로 집계됐다 — 다른 확장자(`.sh` 등) 구현일 가능성이 있다(유의).
- run.sh는 `skill-registry`·`date` 2곳을 제외한 17곳에 존재한다(유의).
