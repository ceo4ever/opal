import json
from pathlib import Path
M = Path(__file__).parent
lock = (M / "PROBES.lock").read_text().splitlines()
lh, lts = lock[0].split()[0], lock[1]
t = (M / "_tables.md").read_text()
rows = json.load(open(M / "results/tier-a.json"))["rows"]
red = [r for r in rows if r["event"] == "stage.design" and r["context"] == "dev"][0]["payload_reduction_pct"]
head = f"""# MEASURE - 이벤트 로더 절 단위 로딩(켬) 측정 결과 (W-6)

> 작성 근거: `measure/` 아래 스크립트·결과 파일의 실제 실행 출력. 표 수치는 `measure/results/*.json`에서 `measure/make_md.py`가 조립했다(`build_doc.py`가 머리말·꼬리말과 합침).
> 대상: 소스 loader(작업 루트 `task_177`), 이벤트 `pm.activate`·`stage.task`·`stage.plan`·`stage.design`. 설치본(`~/.opal`) 수치는 이 문서에 없다.

## 정의

- **본문 합계(`payload_bytes`)**: 응답의 `documents[].content`를 UTF-8 바이트로 합산한 값. 끔은 문서 전문, 켬은 선택된 절만 + 미전달 절 목차.
- **응답 바이트(`response_bytes`)**: loader가 출력한 응답 JSON 전체 크기(본문 + receipt·메타데이터·`section_mode` 선언 해시 등). 켬은 메타가 늘어 본문이 줄어도 응답이 오히려 늘 수 있다 — 아래 표에서 그대로 보인다.
- **미전달 단위**: 켬 응답의 `section_mode.documents[].omitted`.
- **끔/켬**: 끔 = 기본 `load`, 켬 = `--section-mode lazy --section-context track=<값>`(track 미지정 포함).

## 프로브 사전 고정 (실행 전)

- `measure/probes.json` 10개 프로브(미전달 단위 정답 4개, 전달 단위 정답 6개 — 이 중 `[MUST` 규칙 적용 3개). 이벤트 `stage.design`, track=dev.
- 잠금: `measure/PROBES.lock` = sha256 `{lh}`, 시각 `{lts}`. 첫 프로브 결과 파일 시각은 그보다 뒤(`2026-10-01T23:43:39Z`). `run_probes.py`는 실행 시 `probes.json`의 sha256이 잠금값과 일치하는지 검사한다(불일치 시 중단). 수정 없음.
- 채점 기준(필수 항목 정규식, 오답 신호, 포기 표현)도 같은 파일에 함께 고정돼 있다. 채점 중 기준을 바꾸지 않았다.

## 측정 결과

"""
tail = f"""
## 실측 제약

- **표본**: 프로브 10개 x 2회 x 2군 = 40호출. 통계적 동등성·유의성은 주장하지 않는다. 한 이벤트(`stage.design`)·한 문서(`design-gate`, 미전달 단위가 있는 유일한 이벤트·문서)에서만 정확도를 봤다. 다른 이벤트는 켬이 본문을 바꾸지 않으므로(미전달 0) 정확도 측정 대상이 아니다.
- **모델·설정**: 헤드리스 `opal-agent` claude sonnet, `--effort low`(비용 절감 목적), `--opal-bootstrap off`, 타임아웃 300초. 모델이 한 종류라 다른 모델에서의 `section` 호출 판단은 모른다.
- **프롬프트 형식**: 양군 동일 틀("아래 문서만을 근거로 ... 모른다고 답하라" + 질문). 끔은 전체 payload 본문 + "도구를 사용하지 않는다", 켬은 lazy 본문(목차 포함) + `section_wrapper.sh` 사용법. 켬 지시문이 끔보다 길다.
- **작업 디렉터리·도구**: 에이전트가 문서 원문을 파일로 직접 읽는 우회를 막으려고 저장소 밖 빈 디렉터리를 cwd로 썼고, 지시서의 `Read,Bash` 중 `Bash`만 허용했다(양군 동일; `Read`는 우회 위험 때문에 제외). 끔 군이 도구를 쓴 호출(`num_turns>1`)은 없었다(grade.py가 표시하며 해당 사유의 needs_review 없음).
- **채점**: 정규식 기반 결정론 채점은 표현 차이에 취약하다(p08 켬 1회 미스, 부수 설명 때문에 표시된 포기 표현 등). needs_review 건은 위 표에서 사유와 함께 전부 노출했고 엄격 점수는 건드리지 않았다. 의미 기준 재판정은 사람이 한 것이다.
- **누수**: 일부 정규식 항목은 켬 기본 본문에도 이미 나타난다(누수 점검 표). 켬이 `section` 없이도 부분 답을 낼 수 있다는 뜻이며, 모든 필수 항목이 그런 것은 아니다.
- **비용**: 동일 프롬프트의 2회차는 프롬프트 캐시 읽기로 비용이 낮다. 비용·시간은 군 간 비교의 근거로 쓰지 않는다. 켬은 `section` 호출 시 턴이 1회 늘어 시간이 대체로 길다.
- **응답 바이트**: 켬의 `section` 호출 1회당 응답 약 1.5KB가 추가된다(`stage.design` 켬 응답 61,782B + 호출분 vs 끔 60,092B). 본문 감소(5,246B)가 응답 크기로는 환산되지 않는다.
- 사전 단발 점검 호출 1회("2+2", $0.081)는 프로브 집계에 넣지 않았다. p04 프로브를 먼저 1회씩 시험 실행했고 그 결과를 본 실행의 run 1로 그대로 채택했다(재실행으로 덮지 않음).

## 권고

**보류.** 켬이 빼는 것은 `design-gate`의 on_demand 4단위(5,628B)뿐이라 `stage.design` 본문 감소율은 {red}%, 다른 3개 이벤트는 0%이고 응답 바이트는 모든 이벤트에서 오히려 늘었다. 정확도 면에서는 미전달 단위가 정답인 프로브 4개(켬 8호출) 모두 `section`을 1회씩 호출해 정답을 냈고, 전달 단위 프로브에서는 `section` 호출 없이 끔과 같은 정답을 냈다(엄격 채점 켬 19/20 vs 끔 20/20, 차이는 정규식 미스 1건이며 의미 기준 20/20 vs 20/20). 그러나 D-18의 본문 합계 감소율 기준(25%)을 현 선언으로는 채우지 못하므로 기본값 후보로도 올리지 않는다. 감소율을 늘리려면 선언 단위(예: `pm-process`, `citation-rules`, `pm-review-gate`)를 `on_demand`/`conditional`로 더 나누는 후속이 필요하며, 그때는 같은 하니스(`measure/`)로 프로브를 새로 잠가 재측정해야 한다. 기준을 모두 채우더라도 권고는 "기본값 후보 — opst 반복 실행 전제"까지이며 통계적 동등성은 주장하지 않는다.

## 설치본 재측정(TEST)

(TEST 단계에서 PM이 설치본 `~/.opal` 기준 (A) 결정론 측정과 (B) 프로브 결과를 이 자리에 추가한다.)

## 재현

- (A): `~/.opal/.venv/bin/python3 measure/run_measure.py` -> `measure/results/tier-a.json`
- (B): `PAR=4 ~/.opal/.venv/bin/python3 measure/run_probes.py` -> `measure/results/probe-<id>-<arm>-<run>.json`, `section-calls.jsonl`
- 채점·문서: `measure/grade.py` -> `results/graded.json`, `measure/make_md.py` -> `_tables.md`, `measure/build_doc.py` -> `../MEASURE.md`
"""
(M.parent / "MEASURE.md").write_text(head + t + tail)
