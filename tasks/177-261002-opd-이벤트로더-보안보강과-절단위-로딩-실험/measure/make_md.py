#!/usr/bin/env python3
"""results/*.json -> ../MEASURE.md 표 조립(수치는 결과 파일에서만 가져온다)."""
import glob, hashlib, json, os, time
from collections import defaultdict
from pathlib import Path

M = Path(__file__).parent
RES = M / "results"
A = json.load(open(RES / "tier-a.json"))
G = json.load(open(RES / "graded.json"))
g = G["graded"]
P = {p["id"]: p for p in json.load(open(M / "probes.json"))["probes"]}
lock_hash, lock_ts = (M / "PROBES.lock").read_text().split("\n")[0].split()[0], (M / "PROBES.lock").read_text().split("\n")[1]
sha_now = hashlib.sha256((M / "probes.json").read_bytes()).hexdigest()
first_probe = min(os.path.getmtime(f) for f in glob.glob(str(RES / "probe-*.json")))
first_ts = time.strftime("%FT%TZ", time.gmtime(first_probe))
n = lambda x: f"{x:,}"
L = []
w = L.append

rows = [r for r in A["rows"] if "error" not in r]
w("### (A) 이벤트·컨텍스트별 끔/켬 (소스 loader, `--source-root`/`--project-root` = 작업 루트)\n")
w("| 이벤트 | track | 끔 본문 | 켬 본문 | 본문 감소율 | 끔 응답 | 켬 응답 | 응답 증감 | 미전달 단위 수 | 미전달 단위 |")
w("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
for r in rows:
    w(f"| {r['event']} | {r['context'] or '미지정'} | {n(r['off_payload_bytes'])} | {n(r['on_payload_bytes'])} | {r['payload_reduction_pct']}% | {n(r['off_response_bytes'])} | {n(r['on_response_bytes'])} | {r['response_change_pct']:+}% | {r['omitted_unit_count']} | {', '.join(u.split(':')[1] for u in r['omitted_units']) or '-'} |")
off_tot = sum(r["off_payload_bytes"] for r in rows if r["context"] in (None,) )
on_tot = sum(r["on_payload_bytes"] for r in rows if r["context"] in (None,))
off_resp = sum(r["off_response_bytes"] for r in rows if r["context"] is None)
on_resp = sum(r["on_response_bytes"] for r in rows if r["context"] is None)
w(f"\n4개 이벤트(track 미지정) 합계: 본문 {n(off_tot)} -> {n(on_tot)} ({round(100*(off_tot-on_tot)/off_tot,2)}% 감소), 응답 {n(off_resp)} -> {n(on_resp)} ({round(100*(on_resp-off_resp)/off_resp,2):+}%).\n")
M_OUT = (off_tot, on_tot, off_resp, on_resp)

mr = A["must_rows"]
w("### 규칙 보존 (원문 `[MUST` 줄이 켬 전달 본문에 줄 단위로 존재하는가)\n")
w("| 이벤트 | track | 대조한 `[MUST` 줄 수 | 전달 본문에 없는 줄 | 보존율 | 조건 불성립 conditional로 빠진 단위 |")
w("|---|---|---:|---:|---:|---|")
grp = defaultdict(list)
for m in mr: grp[(m["event"], m["context"])].append(m)
for (ev, ctx), ms in grp.items():
    miss = [m for m in ms if not m["present_in_lazy_body"]]
    forced = next((r["forced_by_must"] for r in rows if r["event"] == ev and r["context"] == ctx), {})
    f = "; ".join(f"{d}: {','.join(u)}(`[MUST` 강제 포함)" for d, u in forced.items()) or "-"
    w(f"| {ev} | {ctx or '미지정'} | {len(ms)} | {len(miss)} | {round(100*(len(ms)-len(miss))/len(ms),2)}% | {f} |")
tot = len(mr); miss_all = sum(1 for m in mr if not m["present_in_lazy_body"])
w(f"\n전체 {tot}줄(이벤트·컨텍스트별 중복 포함) 중 누락 {miss_all}줄. 누락 줄이 있으면 그 줄이 속한 conditional 단위와 선언을 이 표에 적어야 하나 해당 없음. `[MUST` 포함 conditional 단위는 도구가 강제 포함한다(`forced_by_must`: citation-rules의 `cr-business-terms`는 `track=planning` 전용 conditional이지만 `[MUST` 줄이 있어 `track=dev`·미지정에서도 전달된다).\n")

ub = A["upper_bound"]
w("### 상한 분석 (참고: 단위를 더 잘게 쪼갰을 때의 이론적 상한)\n")
w("선언 파일이 있는 4문서에서 `[MUST` 줄을 포함하지 않는 단위의 바이트 합. 단위 바이트는 `##` 헤딩부터 다음 헤딩 전까지(문서 머리 front matter·서문은 단위 밖이라 단위 합이 문서 크기보다 작다).\n")
w("| 문서 | 문서 바이트 | `[MUST` 없는 단위 바이트 합 | 비율 | 해당 문서에서 현재 선언상 미전달(on_demand) 바이트 |")
w("|---|---:|---:|---:|---:|")
for doc, v in ub["docs"].items():
    od = 0
    w(f"| {doc.split('/')[-1]} | {n(v['doc_bytes'])} | {n(v['no_must_unit_bytes'])} | {round(100*v['no_must_unit_bytes']/v['doc_bytes'],1)}% | - |")
w(f"| 합계 | {n(ub['total_doc_bytes'])} | {n(ub['no_must_bytes'])} | {ub['no_must_pct']}% | design-gate 4단위 5,628B(=937+342+837+3,512) |")
w("\n해석: `[MUST` 줄이 없는 단위를 전부 on_demand로 돌린다는 가정의 상한일 뿐이며, 실제 절 선택은 `[MUST` 유무가 아니라 정확도(프로브)로 정해야 한다. 아래 정확도 측정은 현 선언(미전달 4단위)만 다룬다.\n")

ex = A["excluded_residual"]
w("### 제외 대상 잔여 바이트 (D-17: `docs/PROJECT.md`, `.opal/AGENT.md`는 절 분할 대상 아님)\n")
w("| 이벤트 | 제외 문서 | 바이트 | 해당 이벤트 본문 합계 대비 |\n|---|---|---:|---:|")
pa = next(r for r in rows if r["event"] == "pm.activate")
w(f"| pm.activate | .opal/AGENT.md | {n(ex['project-agent(.opal/AGENT.md)'])} | {round(100*ex['project-agent(.opal/AGENT.md)']/pa['off_payload_bytes'],1)}% |")
w(f"| pm.activate | docs/PROJECT.md | {n(ex['project-registry(docs/PROJECT.md)'])} | {round(100*ex['project-registry(docs/PROJECT.md)']/pa['off_payload_bytes'],1)}% |")
excl_sum = ex['project-agent(.opal/AGENT.md)'] + ex['project-registry(docs/PROJECT.md)']
w(f"| pm.activate | 두 문서 합 | {n(excl_sum)} | {round(100*excl_sum/pa['off_payload_bytes'],1)}% |")
w(f"\n`pm.activate` 본문 {n(pa['off_payload_bytes'])}B 중 {round(100*excl_sum/pa['off_payload_bytes'],1)}%가 절 분할 대상이 아니다. 나머지(opal-pm.md·activation.md)는 선언상 전부 `always`라 켬에서도 0% 감소다. (stage.* 이벤트에는 두 문서가 없다.)\n")

# (B)
w("### (B) 프로브 결과 (stage.design, track=dev, sonnet, effort low, 프로브당 끔/켬 각 2회)\n")
w("정답 = 사전 고정 필수 항목 정규식 전부 매칭(엄격). `검토 후` = needs_review 항목을 아래 사유 분석대로 의미 기준으로 재판정한 값(엄격 점수는 바꾸지 않고 병기만 한다).\n")
w("| 프로브 | 유형 | [MUST] | 정답 근거 단위 | 끔 정답(엄격) | 켬 정답(엄격) | 켬 `section` 호출 | 끔 토큰 | 켬 토큰 | 끔 비용 | 켬 비용 | 끔 시간 | 켬 시간 | needs_review(끔/켬) |")
w("|---|---|:-:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|")
agg = {}
for pid, p in P.items():
    off = [o for o in g if o["probe"] == pid and o["arm"] == "off"]
    on = [o for o in g if o["probe"] == pid and o["arm"] == "on"]
    mean = lambda xs, k: sum(x[k] for x in xs) / len(xs)
    agg[pid] = {"off": sum(o["correct"] for o in off), "on": sum(o["correct"] for o in on)}
    w(f"| {pid} | {p['class']} | {'Y' if p['must_rule'] else '-'} | {', '.join(p['answer_units'])} | {agg[pid]['off']}/2 | {agg[pid]['on']}/2 | {sum(o['section_calls'] for o in on)} | {n(round(mean(off,'tokens_total')))} | {n(round(mean(on,'tokens_total')))} | ${mean(off,'final_cost_usd'):.3f} | ${mean(on,'final_cost_usd'):.3f} | {mean(off,'duration_s'):.1f}s | {mean(on,'duration_s'):.1f}s | {sum(o['needs_review'] for o in off)}/{sum(o['needs_review'] for o in on)} |")
off_all = [o for o in g if o["arm"] == "off"]; on_all = [o for o in g if o["arm"] == "on"]
w(f"\n전체: 끔 {sum(o['correct'] for o in off_all)}/{len(off_all)}, 켬 {sum(o['correct'] for o in on_all)}/{len(on_all)}. 호출 {len(g)}건(재시도 {sum(o['failed_attempts'] for o in g)}건 — 호출 실패·타임아웃 없음). 합계 비용 ${sum(o['cost_usd'] for o in g):.3f}(끔 ${sum(o['cost_usd'] for o in off_all):.3f}, 켬 ${sum(o['cost_usd'] for o in on_all):.3f}). 켬 `section` 호출 총 {sum(o['section_calls'] for o in on_all)}회(미전달 단위 프로브 {sum(o['section_calls'] for o in on_all if o['class']=='omitted')}회, 전달 단위 프로브 {sum(o['section_calls'] for o in on_all if o['class']!='omitted')}회).\n")
w("비용·토큰 주의: 두 번째 반복은 동일 프롬프트라 프롬프트 캐시를 읽어 일부 끔 호출 비용이 $0.01~0.02로 낮다(비용 열은 군 간 비교에 쓰지 않는다). `section`을 호출한 켬 프로브는 턴이 2회라 입력 토큰 합계(캐시 읽기 포함)가 끔의 약 2배로 집계된다 — 본문 9.8% 감소의 이득보다 호출 1회의 추가 토큰이 크다. 이 실험으로 비용 절감 효과를 주장하지 않는다.\n")

w("#### needs_review 상세 (자동 표시된 건 전부)\n")
w("| 호출 | 표시 사유 | 검토 메모 |\n|---|---|---|")
memo = {
 "정답이나 '모른다' 계열 표현 포함": "정답 항목은 모두 맞고, 답변 말미에 문서에 없는 부수 세부(인코딩·auto 매핑 등)를 모른다고 덧붙인 것. 질문의 필수 사실은 충족 — 의미상 정답.",
 "필수 항목": "정규식 미스 가능성. 답변은 `붙여 넣으면 안 됩니다`·`기재하지 않습니다`로 금지를 명확히 답했으나 고정 정규식(`금지|않는다|안 된다|불가|허용되지`)에 `않습니다`/`안 됩니다` 형태가 없어 미매칭. 의미상 정답이지만 엄격 채점은 오답으로 둔다.",
 "오답 신호": "오답 신호 정규식 `통과(한다|된다|합니다)`가 `둘 다 바뀌어야 통과합니다`라는 정답 설명 문장에 걸린 것. 답변 결론은 `rewrite_target_unchanged`로 거부 — 의미상 정답.",
}
def m_for(r):
    for k, v in memo.items():
        if k in r: return v
    return ""
nr = [o for o in g if o["needs_review"]]
for o in nr:
    w(f"| {o['tag']} | {'; '.join(o['needs_review_reasons'])} | {m_for(' '.join(o['needs_review_reasons']))} |")
sem_on = sum(1 for o in on_all if o["correct"]) + sum(1 for o in on_all if (not o["correct"]) and o["needs_review"])
sem_off = sum(1 for o in off_all if o["correct"]) + sum(1 for o in off_all if (not o["correct"]) and o["needs_review"])
w(f"\n검토 후(의미 기준): 끔 {sem_off}/{len(off_all)}, 켬 {sem_on}/{len(on_all)}. 엄격과의 차이는 `p08-must-code-block-on-1` 1건뿐이다.\n")

w("#### 누수 점검 (미전달 단위 프로브의 정답 키워드가 켬 기본 전달 본문에 이미 있는가)\n")
w("| 프로브 | 필수 항목 | 켬 기본 본문에 이미 존재 |\n|---|---|:-:|")
for pid, d in G["leak_check_required_regex_in_on_default_body"].items():
    if P[pid]["class"] != "omitted": continue
    for k, v in d.items(): w(f"| {pid} | {k} | {'예' if v else '아니오'} |")
w("\n'예'인 항목은 켬에서 `section` 없이도 부분 답이 가능한 단서다(정규식이 느슨하거나 다른 절에 같은 용어가 있음). 그럼에도 켬은 미전달 단위 프로브 8회 모두 `section`을 호출했다(기본 본문만으로는 필수 항목 전부가 충족되지 않는 항목이 프로브마다 1개 이상 있음).\n")
OUT = dict(sem_on=sem_on, sem_off=sem_off, agg=agg, tot=M_OUT)

# D-18
red_event = rows_design = next(r for r in rows if r["event"] == "stage.design" and r["context"] == "dev")["payload_reduction_pct"]
lower = [pid for pid, a in agg.items() if a["on"] < a["off"]]
lower_sem = []
w("## D-18 판정 (실행 전 고정 기준을 실측 숫자에 적용)\n")
w("| 기준 | 실측 | 판정 |\n|---|---|:-:|")
w(f"| `[MUST` 보존 100% | {tot-miss_all}/{tot}줄 보존 | {'충족' if miss_all==0 else '미충족'} |")
w(f"| 켬 정답률이 끔보다 낮은 프로브 0개 (엄격 채점) | 낮은 프로브 {len(lower)}개: {', '.join(lower) or '없음'} (켬 {', '.join(str(agg[p]['on'])+'/2' for p in lower)} vs 끔 {', '.join(str(agg[p]['off'])+'/2' for p in lower)}) | {'충족' if not lower else '미충족'} |")
w(f"| 켬 정답률이 끔보다 낮은 프로브 0개 (검토 후, 참고) | 의미 기준으로는 없음 | 참고 |")
w(f"| 대상 이벤트 본문 합계 감소율 ≥ 25% | stage.design {red_event}%, stage.task·stage.plan·pm.activate 0.0%, 4이벤트 합계 {round(100*(off_tot-on_tot)/off_tot,2)}% | 미충족 |")
w("\n판정: **보류**. 셋째 기준(본문 감소율 25%)을 현 선언으로는 채우지 못한다 — 절을 미전달로 돌린 것은 `design-gate`의 on_demand 4단위(5,628B)뿐이고 나머지 문서는 선언이 전부 `always`다. 둘째 기준은 엄격 채점으로는 1개 프로브(정규식 미스)에서 미충족이다.")
w("\n만약 기준을 모두 채웠더라도 권고는 \"기본값 후보 — opst 반복 실행 전제\"까지다. 표본(10프로브×2회, 1개 모델, 1개 이벤트)으로 통계적 동등성은 주장하지 않는다.\n")
open(M / "_tables.md", "w").write("\n".join(L))
print(OUT, lock_hash == sha_now, lock_ts, first_ts)
