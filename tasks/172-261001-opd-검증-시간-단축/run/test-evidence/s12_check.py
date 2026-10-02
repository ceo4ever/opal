import json,re
d=json.load(open("S-12.response.json"))
r=d["result"]
m=re.findall(r"```json\n(.*?)```",r,re.S)
j=json.loads(m[-1])
adv=j["advisories"]
chk={
 "top_keys_ok": all(k in j for k in("input_bundle_hash","iteration","scope","status","scenario","resolved_gaps","advisories")),
 "scope_scenario": j["scope"]=="scenario",
 "cheaper_layer_S1": any(a["kind"]=="cheaper_layer" and "S-1" in a["targets"] for a in adv),
 "no_cheaper_layer_S2": not any(a["kind"]=="cheaper_layer" and "S-2" in a["targets"] for a in adv),
 "basis_names_contract": any(w in adv[0]["basis"] for w in("전달 경로","입력 조립","출력 형식")),
}
print(chk, "elapsed_ms", d.get("duration_ms"), "is_error", d.get("is_error"))
assert all(chk.values())
