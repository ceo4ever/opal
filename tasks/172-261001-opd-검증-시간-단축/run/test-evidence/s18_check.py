import subprocess,re,sys
R="/Volumes/Data/AiStudio/workspace/opal/.opal-worktrees/task_172"
def sh(*a): return subprocess.run(a,cwd=R,capture_output=True,text=True).stdout
def rd(p): return open(R+"/"+p,encoding="utf-8").read()
MB=sh("git","merge-base","HEAD","main").strip(); print("merge-base HEAD main =",MB)
res={}
def chk(k,ok,detail=""): res[k]=ok; print(("PASS " if ok else "FAIL ")+k,detail)
# (a)
g=rd("opal/skills/op-dev-test-scenario/references/test-scenario-guide.md")
added=sh("git","diff",MB,"HEAD","--","opal/skills/op-dev-test-scenario/references/test-scenario-guide.md")
print("--- (a) added lines:\n"+"\n".join(l[:160] for l in added.splitlines() if l.startswith("+") and not l.startswith("+++")))
chk("a1 [실호출 1회] 표지","[실호출 1회]" in g)
chk("a2 실호출 한정 기준","실호출" in g and ("수용 기준" in g))
chk("a3 1회 제한","1회" in g)
chk("a4 Setup 병렬 그룹","병렬 그룹" in g and "Setup" in g)
# (b)
ev=rd("opal/agents/opal-evaluator-agent/AGENT.md")
chk("b1 cheaper_layer 조항","`cheaper_layer` 조항" in ev)
chk("b2 scope 입력","| scope |" in ev and "`design`(설계 4축만)" in ev)
chk("b3 부분 결과 계약","부분 결과 계약" in ev and '"scope": "design"' in ev and '"scope": "scenario"' in ev)
chk("b4 effort: default 없음", not re.search(r"^effort:\s*default",ev,re.M))
# (c)
sg=rd("opal/skills/op-scenario-gate/SKILL.md")
chk("c1 previous_gaps 산문 조회 규칙 없음","`previous_gaps` 조회 규칙" not in sg and "design_gate.history`를 최신부터 역순" not in sg and "첫 번째 `: ` 앞부분" not in sg)
chk("c2 resolved_gaps 산문 검증 문단 없음","응답 `resolved_gaps`의 완전성을 검증한다" not in sg and "집합이 보낸 `previous_gaps`" not in sg)
steps=re.findall(r"^[①②③④⑤⑥] ",sg,re.M); chk("c3 병렬 5단계(①~⑤ + ⑥ 반환)", all(s in "".join(steps) for s in "①②③④⑤"),"steps="+"".join(steps))
chk("c4 combine 명령 + 동시 디스패치","design-gate combine" in sg and "한 메시지에서 동시에" in sg)
# (d)
dg=rd("opal/core/references/harness/design-gate.md")
sec=dg[dg.index("## 실패 코드"):]
tbl=sec[sec.index("| 코드 | 의미 |"):]; tbl=tbl[:tbl.index("\n\n")] if "\n\n" in tbl else tbl
codes=re.findall(r"^\| `([a-z_]+)` \|",tbl,re.M)
print("failure codes:",len(codes),codes)
chk("d1 18종 표기 및 18행","아래 18종" in sec and len(codes)==18)
chk("d2 partial_invalid combine 소속","design_gate_partial_invalid` | `combine`" in sec and "(`combine` 소속" in sec)
# (e)
d=sh("git","diff","-U0",MB,"HEAD","--","opal/core/references/harness/design-gate.md")
changed=[l[1:] for l in d.splitlines() if l[:1] in "+-" and l[:3] not in("+++","---")]
kw=["4축","completeness","decision_clarity","executability","recoverability","--owner user","reset","design_gate_retry_limit","3회","상한","verdict: pass"]
print("--- (e) changed-line keyword hits:")
hits={k:[l[:120] for l in changed if k in l] for k in kw}
for k,v in hits.items(): 
    if v: print(" ",k,len(v),v[:2])
# main design axes table text and limit statements exist unchanged: they must not appear in changed lines except in lines that merely mention existing codes
axes_tbl_changed=[l for l in changed if re.search(r"completeness|decision_clarity|executability|recoverability",l)]
chk("e1 설계 4축 표 변경 없음",not axes_tbl_changed, str(axes_tbl_changed[:1]))
chk("e2 verdict 규칙 변경 없음", not any("verdict 규칙" in l or "시나리오 3축 각" in l for l in changed))
chk("e3 반복 상한 3회 문구 변경 없음", not any(("3회" in l or "limit" in l and "3" in l) for l in changed))
chk("e4 reset --owner user 문구 변경 없음", not any("--owner user" in l for l in changed))
# also state the 4축 table in evaluator AGENT.md unchanged? check evaluator diff doesn't remove design 4-axis rows
ed=sh("git","diff","-U0",MB,"HEAD","--","opal/agents/opal-evaluator-agent/AGENT.md")
removed=[l for l in ed.splitlines() if l.startswith("-") and not l.startswith("---")]
print("--- evaluator AGENT.md removed lines:",len(removed)); [print("   ",l[:150]) for l in removed]
chk("e5 evaluator 4축 정의·verdict 규칙 행 삭제/변경 없음", not any(re.search(r"completeness|decision_clarity|verdict 규칙|통과선",l) for l in removed))
# (f)
chk("f1 op-gc-convention base_ref","base_ref" in rd("opal/skills/op-gc-convention/SKILL.md"))
chk("f2 checker AGENT base_ref","base_ref" in rd("opal/agents/opal-convention-checker/AGENT.md"))
pm=rd("opal/core/references/harness/pm-review-gate.md"); i=pm.index("13."); 
chk("f3 pm-review-gate §13 base_ref","base_ref" in pm)
print("   pm-review-gate base_ref line:",[l.strip()[:100] for l in pm.splitlines() if "base_ref" in l])
chk("f4 gc-finding-schema.md main 대비 무변경", sh("git","diff",MB,"HEAD","--","opal/core/references/harness/gc-finding-schema.md")=="")
# (g)
tc=rd("opal/core/references/harness/test-cycle.md")
chk("g1 병렬 그룹 실행 절","## 병렬 그룹 실행" in tc)
chk("g2 다중 에이전트 비채택 근거·대안","다중 에이전트 병렬은 채택하지 않는다" in tc and "대안은 후속 태스크" in tc)
chk("g3 실호출 시나리오 절","## 실호출 시나리오" in tc)
chk("g4 actor.md 무변경", sh("git","diff",MB,"HEAD","--","opal/core/references/harness/actor.md")=="")
# (h)
dm=sh("git","diff","-U0",MB,"HEAD","--","scripts/install-mac.sh")
add=[l for l in dm.splitlines() if l.startswith("+") and not l.startswith("+++")]; rem=[l for l in dm.splitlines() if l.startswith("-") and not l.startswith("---")]
print("--- (h) install-mac.sh added",len(add),"removed",len(rem)); [print("   ",l) for l in add]
chk("h1 install-mac.sh 변경=convention-precheck chmod 블록만", not rem and len(add)==7 and all(("convention-precheck" in l or "convention_precheck" in l or l.strip("+ ").startswith(("local","if","chmod","success","fi")) or l=="+") for l in add) and any("chmod +x \"$convention_precheck_run\"" in l for l in add))
def seg(p):
    t=rd(p).splitlines(); a=[i for i,l in enumerate(t) if l.startswith("# >>> OPAL_ADAPTER_FIELD_SPEC >>>")][0]; b=[i for i,l in enumerate(t) if l.startswith("# <<< OPAL_ADAPTER_FIELD_SPEC <<<")][0]
    return "\n".join(t[a:b+1]).encode()
m,w=seg("scripts/install-mac.sh"),seg("scripts/install/windows.ps1")
chk("h2 센티넬 구간 mac==windows 바이트 동일 (%d bytes)"%len(m), m==w)
mainsh=subprocess.run(["git","show",MB+":scripts/install-mac.sh"],cwd=R,capture_output=True).stdout.decode().splitlines()
a=[i for i,l in enumerate(mainsh) if l.startswith("# >>> OPAL_ADAPTER_FIELD_SPEC >>>")][0]; b=[i for i,l in enumerate(mainsh) if l.startswith("# <<< OPAL_ADAPTER_FIELD_SPEC <<<")][0]
chk("h3 센티넬 구간 main 대비 무변경", "\n".join(mainsh[a:b+1]).encode()==m)
# (i)
chk("i1 tools.md convention-precheck 행", "| `convention-precheck` |" in rd("opal/core/references/tools.md"))
chk("i2 docs/PROJECT.md convention-precheck 행", "| `convention-precheck` |" in rd("docs/PROJECT.md"))
# (j)
files=[f for f in sh("git","diff","--name-only",MB,"HEAD").splitlines()]
non_task=sorted(f for f in files if not f.startswith("tasks/172-"))
other_tasks=[f for f in files if f.startswith("tasks/") and not f.startswith("tasks/172-")]
allowed="""docs/PROJECT.md opal/agents/opal-convention-checker/AGENT.md opal/agents/opal-evaluator-agent/AGENT.md opal/agents/opal-test-agent/AGENT.md opal/core/references/agents.md opal/core/references/harness/design-gate.md opal/core/references/harness/pm-review-gate.md opal/core/references/harness/test-cycle.md opal/core/references/tools.md opal/skills/op-dev-test-scenario/references/test-scenario-guide.md opal/skills/op-gc-convention/SKILL.md opal/skills/op-scenario-gate/README.md opal/skills/op-scenario-gate/SKILL.md opal/skills/opal-pilot-dev/README.md opal/skills/opal-pilot-dev/SKILL.md opal/tools/convention-precheck/README.md opal/tools/convention-precheck/convention_precheck.py opal/tools/convention-precheck/run.sh opal/tools/convention-precheck/tests/test_convention_precheck.py opal/tools/state-tool/README.md opal/tools/state-tool/state_tool.py opal/tools/state-tool/tests/test_design_gate_parallel.py scripts/install-mac.sh scripts/tests/test_agent_effort_policy.sh""".split()
print("non-task changed:",len(non_task),"| extra:",sorted(set(non_task)-set(allowed)),"| missing:",sorted(set(allowed)-set(non_task)),"| other tasks/ dirs:",other_tasks)
chk("j1 변경 파일 = PM 지정 24개 + 이 태스크 산출물", set(non_task)==set(allowed) and not other_tasks)
print("\nSUMMARY:",sum(res.values()),"/",len(res),"checks pass; failed:",[k for k,v in res.items() if not v])
