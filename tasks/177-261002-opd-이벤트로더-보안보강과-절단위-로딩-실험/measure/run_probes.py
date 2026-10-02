#!/usr/bin/env python3
"""(B) 프로브 실행: 프로브 x {off,on} x 2회. 모든 시도(실패 포함)를 results/probe-<id>-<arm>-<run>.json에 기록."""
import json, os, subprocess, sys, time, hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

M = Path(__file__).parent.resolve()
RES = M / "results"
NEUTRAL = "/private/tmp/claude-501/-Volumes-Data-AiStudio-workspace-opal--opal-worktrees-task-177/7aca0aa1-d561-4487-8f00-e11a4c4fbab1/scratchpad/neutral"
os.makedirs(NEUTRAL, exist_ok=True)
AGENT = os.path.expanduser("~/.opal/tools/opal-agent/run.sh")
probes = json.load(open(M / "probes.json"))
lock = (M / "PROBES.lock").read_text().split()[0]
assert hashlib.sha256((M / "probes.json").read_bytes()).hexdigest() == lock, "probes.json 변경됨 - 무효"
RUNS = int(os.environ.get("RUNS", "2"))
ONLY = os.environ.get("ONLY")  # 쉼표 구분 프로브 id 필터(디버그)


def docs_text(arm):
    r = json.load(open(RES / f"receipt-stage.design-{arm}.json"))
    return "\n\n".join(f"=== 문서: {d['id']} ===\n{d['content']}" for d in r["documents"])


DOCS = {a: docs_text(a) for a in ("off", "on")}
FRAME = "아래 문서만을 근거로 질문에 답하라. 문서에 없는 내용은 모른다고 답하라. 답은 한국어로 간결하게(핵심 사실 위주) 작성하라."
ON_NOTE = ("\n\n[절 조회] 문서 중 '미전달 절 목차'에 나열된 절은 본문에 없다. 질문에 답하는 데 필요하다고 판단하면 "
           "반드시 아래 명령만 사용해 가져올 수 있다(다른 방법으로 파일을 직접 읽거나 검색하지 말 것):\n"
           "  {wrapper} {tag} <id>[,<id>...]\n"
           "(receipt 경로: {receipt} - wrapper가 내부에서 사용하므로 직접 지정할 필요 없음). 필요 없으면 호출하지 않는다.")
OFF_NOTE = "\n\n도구를 사용하지 않는다. 위 문서만 본다."


def build(p, arm, tag):
    note = OFF_NOTE if arm == "off" else ON_NOTE.format(wrapper=str(M / "section_wrapper.sh"), tag=tag, receipt=str(RES / "receipt-stage.design-on.json"))
    return f"{FRAME}{note}\n\n{DOCS[arm]}\n\n=== 질문 ===\n{p['question']}\n"


def call(prompt):
    t0 = time.time()
    cmd = [AGENT, "--opal-bootstrap", "off", "--provider", "claude", "--model", "sonnet", "--effort", "low",
           "--allowed-tools", "Bash", "--cwd", NEUTRAL, "--json", "--timeout", "300"]
    try:
        pr = subprocess.run(cmd, input=prompt, capture_output=True, text=True, timeout=330)
        out, err, rc = pr.stdout, pr.stderr, pr.returncode
    except subprocess.TimeoutExpired:
        out, err, rc = "", "outer-timeout", 124
    try:
        j = json.loads(out)
    except Exception:
        j = None
    ok = bool(j) and not j.get("is_error") and j.get("subtype") == "success" and bool(j.get("result"))
    return {"ok": ok, "rc": rc, "wall_s": round(time.time() - t0, 1), "json": j, "stdout_head": None if j else out[:500], "stderr": err[:500]}


def run(job):
    p, arm, run_i = job
    tag = f"{p['id']}-{arm}-{run_i}"
    f = RES / f"probe-{tag}.json"
    if f.exists():
        return tag, "skip"
    prompt = build(p, arm, tag)
    attempts = []
    for k in range(2):  # 최초 1 + 재시도 1
        a = call(prompt); a["attempt"] = k + 1
        attempts.append(a)
        if a["ok"]:
            break
    json.dump({"probe": p["id"], "arm": arm, "run": run_i, "tag": tag, "prompt_bytes": len(prompt.encode()),
               "attempts": attempts, "final_ok": attempts[-1]["ok"]}, open(f, "w"), ensure_ascii=False, indent=1)
    cost = sum((a["json"] or {}).get("total_cost_usd", 0) or 0 for a in attempts)
    return tag, f"ok={attempts[-1]['ok']} attempts={len(attempts)} cost=${cost:.3f}"


if __name__ == "__main__":
    jobs = [(p, arm, r) for p in probes["probes"] if (not ONLY or p["id"] in ONLY.split(",")) for r in range(1, RUNS + 1) for arm in ("off", "on")]
    print(len(jobs), "jobs", flush=True)
    with ThreadPoolExecutor(int(os.environ.get("PAR", "4"))) as ex:
        for tag, st in ex.map(run, jobs):
            print(tag, st, flush=True)
