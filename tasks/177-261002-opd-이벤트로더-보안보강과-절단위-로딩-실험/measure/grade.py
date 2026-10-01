#!/usr/bin/env python3
"""사전 고정 채점 기준(probes.json)으로 결정론 채점. 애매하면 needs_review."""
import json, re
from pathlib import Path

M = Path(__file__).parent
RES = M / "results"
P = json.load(open(M / "probes.json"))
ABST = re.compile(P["abstain_regex"])
calls = [json.loads(l) for l in (RES / "section-calls.jsonl").read_text().splitlines() if l.strip()] if (RES / "section-calls.jsonl").exists() else []
on_receipt = json.load(open(RES / "receipt-stage.design-on.json"))
off_body = "\n".join(d["content"] for d in json.load(open(RES / "receipt-stage.design-off.json"))["documents"])
on_body = "\n".join(d["content"] for d in on_receipt["documents"])
FL = re.I | re.S
out = []
for p in P["probes"]:
    # 누수 점검: 정답 키워드가 켬 기본 전달 본문에 이미 있는가(미전달 단위 프로브의 비교 타당성)
    leak = {r["name"]: bool(re.search(r["regex"], on_body, FL)) for r in p["required"]}
    for arm in ("off", "on"):
        for run in (1, 2):
            tag = f"{p['id']}-{arm}-{run}"
            f = RES / f"probe-{tag}.json"
            if not f.exists():
                out.append({"tag": tag, "probe": p["id"], "arm": arm, "run": run, "status": "missing"}); continue
            d = json.load(open(f))
            att = d["attempts"]
            fin = att[-1]
            j = fin["json"] or {}
            ans = j.get("result") or ""
            matched = {r["name"]: bool(re.search(r["regex"], ans, FL)) for r in p["required"]}
            correct = fin["ok"] and all(matched.values())
            wrong = [w for w in p.get("wrong_signals", []) if re.search(w, ans, FL)]
            abst = bool(ABST.search(ans))
            sc = [c for c in calls if c["run_tag"] == tag]
            reasons = []
            if correct and wrong: reasons.append(f"정답이나 오답 신호 매칭: {wrong}")
            if correct and abst: reasons.append("정답이나 '모른다' 계열 표현 포함")
            if not correct and fin["ok"] and sum(matched.values()) >= len(matched) - 1 and not abst:
                reasons.append(f"필수 항목 {sum(matched.values())}/{len(matched)} 충족(정규식 미스 가능성)")
            if arm == "off" and j.get("num_turns", 1) > 1: reasons.append("끔 프로브가 도구 사용(num_turns>1)")
            if arm == "on" and p["class"] == "omitted" and not sc and not correct: pass
            u = j.get("usage") or {}
            tokens = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("output_tokens", 0))
            out.append({
                "tag": tag, "probe": p["id"], "class": p["class"], "must_rule": p["must_rule"], "arm": arm, "run": run,
                "correct": correct, "matched": matched, "abstain": abst, "wrong_signals": wrong,
                "needs_review": bool(reasons), "needs_review_reasons": reasons,
                "section_calls": len(sc), "section_ids": [c["ids"] for c in sc],
                "attempts": len(att), "failed_attempts": sum(1 for a in att if not a["ok"]),
                "cost_usd": round(sum(((a["json"] or {}).get("total_cost_usd") or 0) for a in att), 4),
                "final_cost_usd": round(j.get("total_cost_usd") or 0, 4),
                "duration_s": round((j.get("duration_ms") or 0) / 1000, 1), "wall_s": fin["wall_s"],
                "tokens_total": tokens, "output_tokens": u.get("output_tokens", 0), "num_turns": j.get("num_turns"),
                "prompt_bytes": d["prompt_bytes"], "answer": ans,
            })
summary = {"leak_check_required_regex_in_on_default_body": {p["id"]: {r["name"]: bool(re.search(r["regex"], on_body, FL)) for r in p["required"]} for p in P["probes"]}}
json.dump({"graded": out, **summary}, open(RES / "graded.json", "w"), ensure_ascii=False, indent=1)
for o in out:
    if o.get("status") == "missing": print(o["tag"], "MISSING"); continue
    print(o["tag"], "C" if o["correct"] else "-", "NR" if o["needs_review"] else "", "sec=%d" % o["section_calls"], f"${o['cost_usd']}", o["duration_s"], o["matched"] if not o["correct"] else "")
