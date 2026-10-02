#!/usr/bin/env python3
"""(A) 결정론 측정: 소스 loader를 끔/켬으로 호출해 본문·응답 바이트와 규칙 보존을 계산한다."""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path("/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_177")
PY = os.path.expanduser("~/.opal/.venv/bin/python3")
LOADER = str(ROOT / "opal/tools/event-loader/event_loader.py")
OUT = Path(__file__).parent / "results"
OUT.mkdir(exist_ok=True)
EVENTS = ["pm.activate", "stage.task", "stage.plan", "stage.design"]
MARK = re.compile(r"\[MUST")


def load(event, lazy, ctx):
    cmd = [PY, LOADER, "load", "--event", event, "--source-root", str(ROOT), "--project-root", str(ROOT)]
    if lazy:
        cmd += ["--section-mode", "lazy"]
        if ctx:
            cmd += ["--section-context", f"track={ctx}"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except Exception:
        return {"ok": False, "error": "unparseable", "stderr": p.stderr[:500], "stdout": p.stdout[:300]}


def declared_contexts(event):
    m = json.load(open(ROOT / "opal/core/references/events.json"))
    ev = [e for e in m.get("events", m) if e["id"] == event][0]
    vals = {}
    for s in ev.get("sectioning", []):
        d = json.load(open(s["source"].replace("{source_root}", str(ROOT))))
        for k, v in (d.get("contexts") or {}).items():
            vals.setdefault(k, set()).update(v)
    return sorted(vals.get("track", []))


rows, must_rows = [], []
for ev in EVENTS:
    ctxs = [None] + declared_contexts(ev)
    off = load(ev, False, None)
    assert off.get("ok"), (ev, off)
    for ctx in ctxs:
        on = load(ev, True, ctx)
        if not on.get("ok"):
            rows.append({"event": ev, "context": ctx, "error": on})
            continue
        sm = on.get("section_mode", {}).get("documents", {})
        delivered, omitted = [], []
        for did, info in sm.items():
            delivered += [f"{did}:{u}" for u in info["delivered"]]
            omitted += [f"{did}:{u}" for u in info["omitted"]]
        rows.append({
            "event": ev, "context": ctx,
            "off_payload_bytes": off["payload_bytes"], "off_response_bytes": off["response_bytes"],
            "on_payload_bytes": on["payload_bytes"], "on_response_bytes": on["response_bytes"],
            "source_payload_bytes_reported_by_on": on.get("source_payload_bytes"),
            "payload_reduction_pct": round(100 * (off["payload_bytes"] - on["payload_bytes"]) / off["payload_bytes"], 2),
            "response_change_pct": round(100 * (on["response_bytes"] - off["response_bytes"]) / off["response_bytes"], 2),
            "omitted_unit_count": len(omitted), "omitted_units": omitted, "delivered_units": delivered,
            "forced_by_must": {d: i["forced_by_must"] for d, i in sm.items() if i["forced_by_must"]},
        })
        # 규칙 보존: 원문 문서의 모든 [MUST 줄이 전달 본문에 있는지 줄 단위 대조
        body = {d["id"]: set(l.strip() for l in d["content"].splitlines()) for d in on["documents"]}
        for d in on["documents"]:
            src = Path(d["path"]).read_text(encoding="utf-8")
            # 원문 줄(공백 제거) 중 [MUST 포함 줄
            for i, line in enumerate(src.splitlines(), 1):
                if MARK.search(line):
                    present = line.strip() in body[d["id"]]
                    must_rows.append({"event": ev, "context": ctx, "doc": d["id"], "line_no": i,
                                      "present_in_lazy_body": present, "line_head": line.strip()[:70]})

# 상한 분석: [MUST 없는 단위의 바이트 합 (선언 단위 기준, 4문서 = 선언 있는 문서)
def unit_bytes(doc_decl):
    d = json.load(open(ROOT / doc_decl))
    src = (ROOT / d["document"]).read_text(encoding="utf-8")
    lines = src.splitlines(keepends=True)
    lvl = d["unit_level"]
    head = re.compile(r"^#{%d} " % lvl)
    # 단위 경계: 선언 순서대로 같은 제목 헤딩 위치를 찾는다
    pos = []
    for s in d["sections"]:
        for i, l in enumerate(lines):
            if head.match(l) and l.lstrip("#").strip() == s["title"].strip():
                pos.append((s["id"], i)); break
    pos.sort(key=lambda x: x[1])
    res = {}
    for k, (uid, i) in enumerate(pos):
        j = pos[k + 1][1] if k + 1 < len(pos) else len(lines)
        txt = "".join(lines[i:j])
        res[uid] = {"bytes": len(txt.encode()), "has_must": bool(MARK.search(txt))}
    return d["document"], len(src.encode()), res

upper = {}
for f in sorted((ROOT / "opal/core/references/sections").glob("*.json")):
    doc, total, res = unit_bytes(f.relative_to(ROOT))
    no_must = sum(v["bytes"] for v in res.values() if not v["has_must"])
    upper[doc] = {"doc_bytes": total, "units": res, "no_must_unit_bytes": no_must}
tot = sum(v["doc_bytes"] for v in upper.values()); nm = sum(v["no_must_unit_bytes"] for v in upper.values())
upper_summary = {"docs": upper, "total_doc_bytes": tot, "no_must_bytes": nm, "no_must_pct": round(100 * nm / tot, 2)}

# 제외 대상 잔여 바이트(D-17): pm.activate의 project-agent·project-registry
excl = {}
for name, rel in [("project-agent(.opal/AGENT.md)", ".opal/AGENT.md"), ("project-registry(docs/PROJECT.md)", "docs/PROJECT.md")]:
    p = ROOT / rel
    excl[name] = p.stat().st_size if p.exists() else None
pm = load("pm.activate", False, None)
excl["pm.activate off 문서별 바이트"] = {d["id"]: len(d["content"].encode()) for d in pm["documents"]}

json.dump({"rows": rows, "must_rows": must_rows, "upper_bound": upper_summary, "excluded_residual": excl},
          open(OUT / "tier-a.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(rows[:0]))
for r in rows:
    if "error" in r: print(r); continue
    print(r["event"], r["context"], r["off_payload_bytes"], r["on_payload_bytes"], r["payload_reduction_pct"], r["off_response_bytes"], r["on_response_bytes"], r["response_change_pct"], r["omitted_unit_count"])
print("MUST lines", len(must_rows), "absent", sum(1 for m in must_rows if not m["present_in_lazy_body"]))
print(upper_summary["total_doc_bytes"], upper_summary["no_must_bytes"], upper_summary["no_must_pct"]); print(excl)
