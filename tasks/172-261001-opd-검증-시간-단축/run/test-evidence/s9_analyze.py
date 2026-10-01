import json,glob,sys
for tag,pat in (("scan1 @48f25a5a","/var/folders/0k/n9rvmztx6xs3xvjsvf0qqzdw0000gn/T/tmp.RVsLLlMjHd/gc-findings*.json"),("scan2 HEAD vs main","/var/folders/0k/n9rvmztx6xs3xvjsvf0qqzdw0000gn/T/tmp.4nPyLM1NFq/gc-findings*.json")):
    for p in glob.glob(pat):
        d=json.load(open(p)); print("==",tag,p.split('/')[-1],"status",d.get("status"),"n=",len(d.get("findings",[])))
        for f in d.get("findings",[]):
            print({k:f.get(k) for k in ("id","severity","disposition","rule_id","source_tier","file","line","rule_ref")} if 0 else json.dumps({k:v for k,v in f.items() if k in("id","severity","disposition","file","path","line","location","rule_ref","rule","source_tier")},ensure_ascii=False))
