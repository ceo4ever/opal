import re,statistics,subprocess,ast,sys
R="/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_172"
rep=open(R+"/tasks/172-261001-opd-검증-시간-단축/run/PARALLEL-PROBE.md",encoding="utf-8").read()
# (a) table rows: | n | seq | par |
rows=re.findall(r"^\| (\d) \| ([\d.]+) \| ([\d.]+) \|$",rep,re.M)
seq=[float(r[1]) for r in rows]; par=[float(r[2]) for r in rows]
ms,mp=statistics.median(seq),statistics.median(par); ratio=mp/ms
print("seq",seq,"median",ms,"| par",par,"median",mp,"ratio",round(ratio,3))
preserved=bool(re.search(r"6회 실행.*모두.*일치.*보존",rep))
a_ok = ratio<=0.60 and preserved
print("(a) rule: ratio<=0.60:",ratio<=0.6,"preserved:",preserved,"=> 가능" if a_ok else "=> 불가")
# (b) rounds: | n | mark | passed | missing |
b=re.findall(r"^\| (\d) \| (\d+) \| (\d+) \| (\d+) \|$",rep,re.M)
miss=[int(x[3]) for x in b]; recompute=[8-int(x[2]) for x in b]
print("rounds",len(b),"missing(reported)",miss,"missing(8-passed)",recompute,"sum",sum(recompute))
assert miss==recompute
src=open(R+"/opal/tools/test-tool/lib/scenario.py",encoding="utf-8").read()
lock_in_code=any(k in src for k in("fcntl","flock","lockf","msvcrt","O_EXCL"))
lines=src.splitlines()
for n,sub in((206,"_save_spec"),(445,"cmd_scenario_mark"),(512,"_save_spec")):
    print("scenario.py:%d"%n,"contains",sub,":",sub in lines[n-1], "|",lines[n-1].strip()[:80])
st=open(R+"/opal/tools/state-tool/state_tool.py",encoding="utf-8").read().splitlines()
for n,sub in((4925,"_interval_sum_seconds"),(4940,"auto_seconds")):
    print("state_tool.py:%d"%n,"contains",sub,":",sub in st[n-1],"|",st[n-1].strip()[:90])
b_impossible = sum(recompute)>0 or not lock_in_code
print("lock_in_code",lock_in_code,"(b) rule: missing>0 or no lock =>", "불가" if b_impossible else "가능")
final="(a) 가능 · (b) 불가" if a_ok and b_impossible else "other"
print("recomputed final:",final)
m=re.search(r"\*\*최종 판정: (.*?)\*\*",rep); print("report final:",m.group(1)[:30])
assert m.group(1).startswith("(a) 가능 · (b) 불가") and final=="(a) 가능 · (b) 불가"
print("채택 절차 section:", "### 채택 절차" in rep, "| 비채택/대안:", "대안" in rep and "### 비채택" in rep)
# probe.py runnable?
ast.parse(open(R+"/tasks/172-261001-opd-검증-시간-단축/run/parallel-probe/probe.py").read()); print("probe.py parses OK")
pr=open(R+"/tasks/172-261001-opd-검증-시간-단축/run/parallel-probe/probe.py",encoding="utf-8").read()
print("probe.py usage doc present:", "사용: python3 probe.py" in pr, "| writes only temp fixtures (tempfile used):", "tempfile" in pr or "mkdtemp" in pr)
print("NOTE: probe.py has no --help handling; it runs the full probe on any invocation (not executed here to avoid 30s+ run; first attempt with --help was killed by timeout).")
import re as _re
for name,pat in(("_interval_sum_seconds",r"def _interval_sum_seconds"),("auto_seconds call",r"auto_seconds=_interval_sum_seconds")):
    for n,l in enumerate(st,1):
        if _re.search(pat,l): print("actual state_tool.py line of",name,"=",n,"(report cites 4925/4940)")
