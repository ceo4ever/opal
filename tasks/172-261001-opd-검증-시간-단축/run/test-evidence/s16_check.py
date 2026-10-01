import re,json,statistics,subprocess,os
R="/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_172"; T=R+"/tasks/172-261001-opd-검증-시간-단축"
md=open(T+"/run/EVAL-RESULT.md",encoding="utf-8").read()
def section(a,b):
    i=md.index(a); j=md.index(b,i+1); return md[i:j]
s2=section("## 2. checker 결과","## 3. evaluator"); s31=section("### 3.1 호출별","### 3.2") if "### 3.2" in md else section("### 3.1 호출별","## 4.")
rows2=[[c.strip() for c in l.strip().strip("|").split("|")] for l in s2.splitlines() if re.match(r"\| (162|161|163|169|syn)",l)]
print("checker rows",len(rows2)); assert len(rows2)==40
# columns: case,cand,expected,actual,match,highmiss,flip,sec,note
ck={}
for r in rows2:
    assert len(r)==9, r
    d=ck.setdefault(r[1],{"n":0,"nores":0,"miss":0,"flip":0,"mismatch":0,"secs":[]})
    d["n"]+=1
    if "결과 없음" in r[3]: d["nores"]+=1; continue
    d["miss"]+=int(r[5]); d["flip"]+=int(r[6]); d["mismatch"]+= (r[4]!="O"); d["secs"].append(float(r[7]))
# evaluator per-call rows (48)
ev=[[c.strip() for c in l.strip().strip("|").split("|")] for l in md.splitlines() if re.match(r"\| (pass|defect)-\d+(-i\d)? \| E\d \| (design|scenario) \|",l)]
print("evaluator per-call rows",len(ev)); assert len(ev)==48
print("rows without result:",sum(1 for r in ev if "결과 없음" in r[4]))
comb=[[c.strip() for c in l.strip().strip("|").split("|")] for l in md.splitlines() if re.match(r"\| (pass|defect)-\d+(-i\d)? \| E\d \| (pass|fail) \| (pass|fail) \|",l)]
print("combined rows",len(comb)); assert len(comb)==24
# combined cols: case,cand,exp_verdict,verdict,exp_axes,actual_axes,match,missed,flip,d,s,pair,note
evd={}
for r in comb:
    d=evd.setdefault(r[1],{"n":0,"miss":0,"flip":0,"verdict_diff":0,"pair":[]})
    d["n"]+=1; d["miss"]+=int(r[7]); d["flip"]+=int(r[8]); d["verdict_diff"]+= (r[2]!=r[3]); d["pair"].append(float(r[11]))
    # recompute missed axes from expected vs actual
    exp=set(filter(None,r[4].split(","))) if r[4] not in("-","") else set(); act=set(filter(None,r[5].split(",")))
    assert int(r[7])==len(exp-act), r
    # recompute flip: expected pass but verdict fail
    assert int(r[8])==(1 if (r[2]=="pass" and r[3]=="fail") else 0), r
# cross-check md vs results.json
res=json.load(open(T+"/run/eval/results.json"))
assert len(res["rows"]["checker"])==40 and len(res["rows"]["evaluator"])==48 and len(res["rows"]["combined"])==24
for c in res["rows"]["combined"]:
    m=[r for r in comb if r[0]==c["case"] and r[1]==c["cand"]][0]
    assert m[3]==c["verdict"] and float(m[11])==c["pair_wall_s"] and int(m[8])==c["flip"], (m,c)
print("md combined rows == results.json combined rows: OK")
for c in res["rows"]["checker"]:
    m=[r for r in rows2 if r[0]==c["case"] and r[1]==c["cand"]][0]
    assert float(m[7])==c["elapsed_s"] and int(m[6])==c["flip"] and int(m[5])==c["high_miss"], (m,c)
print("md checker rows == results.json checker rows: OK")
# D-13 recompute
rep=md[md.index("## 4. 후보별"):md.index("### 4.1")]
rep_rows={ [c.strip() for c in l.strip().strip("|").split("|")][0]:[c.strip() for c in l.strip().strip("|").split("|")] for l in rep.splitlines() if re.match(r"\| [KE]\d \|",l)}
ok=True
for cand,d in {**ck,**evd}.items():
    n=d["n"]; nores=d.get("nores",0); miss=d["miss"]; flip=d["flip"]
    verdict="채택 가능" if (miss==0 and flip==0 and nores==0) else "채택 불가"
    rr=rep_rows[cand]; same = rr[5]==verdict and int(rr[2].split("/")[0])==n-nores and int(rr[3])==miss and int(rr[4])==flip
    ok&=same
    print(cand,"n=%d nores=%d miss=%d flip=%d -> %s | report: %s results=%s %s"%(n,nores,miss,flip,verdict,rr[5],rr[2],"MATCH" if same else "MISMATCH"))
print("all 7 candidate verdicts match recomputation:",ok)
print("evaluator combined verdict differing from 170 expected:",sum(d["verdict_diff"] for d in evd.values()),"(of 24)")
for cand,d in sorted(ck.items()): print(cand,"mean sec",round(statistics.mean(d["secs"]),1),"mismatch rows",d["mismatch"])
for cand,d in sorted(evd.items()): print(cand,"mean pair wall",round(statistics.mean(d["pair"]),1))
# no-result reasons: any 결과 없음 rows?
print("'결과 없음' 행 수 (checker,evaluator):",sum("결과 없음" in l for l in s2.splitlines()),sum("결과 없음" in l for l in s31.splitlines()),"| header: 결과 있음 88 / 없음 0:", "결과 있음 88·결과 없음 0" in md)
# relative-only wording
print("상대 비교 한정 문구:", "후보 간 상대 비교" in md, "| 절대 누락률 주장 없음 문구:", "절대 누락률" in md)
# 8절 and initial files
print("section8 present:", "## 8. 재집계 경위" in md, "| results-initial.json:", os.path.exists(T+"/run/eval/results-initial.json"), "| results-initial-EVAL-RESULT.md:", os.path.exists(T+"/run/eval/results-initial-EVAL-RESULT.md"))
ri=json.load(open(T+"/run/eval/results-initial.json")); ck0=ri["rows"]["checker"]; print("initial checker flips:",sum((c.get("flip") or 0) for c in ck0),"initial no-result:",sum(1 for c in ck0 if c.get("result") in (None,False)))
# frontmatter
def fm(p):
    t=open(p,encoding="utf-8").read().split("---")[1]; return dict(re.findall(r"^(model|effort):\s*(\S+)",t,re.M))
a=fm(R+"/opal/agents/opal-convention-checker/AGENT.md"); b=fm(R+"/opal/agents/opal-evaluator-agent/AGENT.md")
print("checker fm",a,"evaluator fm",b)
assert a=={"model":"standard","effort":"low"} and b=={"model":"advanced","effort":"medium"}
log=open(T+"/AGENTIC-LOG.md",encoding="utf-8").read()
print("AGENTIC-LOG row7 states K1/E1:", bool(re.search(r"\| 7 \|.*standard.*low.*advanced.*medium",log)))
print("run-log activity evt_36956d9a present:", "evt_36956d9a-15ff-4d56-9fd6-d435e0dc6dbd" in open(T+"/run/run-log-run_f22100a0-3a14-49b5-a688-d44d7ede148e-0001.jsonl").read())
