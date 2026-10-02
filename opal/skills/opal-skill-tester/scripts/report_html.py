"""
@header {
  "module": "report_html",
  "layer": "util",
  "domain": "opal-skill-tester",
  "description": "opal-skill-tester 대시보드 보고서(report.html) 렌더러. 단일 실행은 요약(평가축 5종·단계 상세·자기 교정·전체 지표)+스킬별 이력 탭, 비교 실행은 비교(변형 설정 선언·적용, 지표별 평균·최소~최대, 품질 하한 판정, FW 불일치 시 비교 무효 배너, 핵심 지표·준수 매트릭스·단계 묶음 막대·변화율)+변형별 상세+이력 탭을 한 파일로 만든다. 이력 탭은 같은 시나리오 추세(최근 실행 중앙값 대비)와 같은 스킬의 과거 실행 표를 보여 주며 각 행은 과거 실행 상세를 페이지 안에서 펼치거나 과거 대시보드를 새 탭으로 연다. 인라인 SVG·외부 의존 없음, 라이트/다크 모드.",
  "exports": ["render_report", "axes_for"]
}
"""
import html
import json
import os
import statistics

MODE_KO = {"smoke": "스모크", "function": "기능", "judgment": "판단"}
SERIES = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)"]

CSS = """
.viz-root{color-scheme:light;--page:#f9f9f7;--surface-1:#fcfcfb;--text-primary:#0b0b0b;--text-secondary:#52514e;--muted:#898781;
--grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s1-alt:#86b6ec;
--good:#0ca30c;--crit:#d03b3b;--up:#006300;--down:#d03b3b}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;--page:#0d0d0d;--surface-1:#1a1a19;
--text-primary:#fff;--text-secondary:#c3c2b7;--grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s1-alt:#1f5ea8;--up:#0ca30c}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--page:#0d0d0d;--surface-1:#1a1a19;--text-primary:#fff;--text-secondary:#c3c2b7;--grid:#2c2c2a;--axis:#383835;
--border:rgba(255,255,255,.10);--s1:#3987e5;--s2:#d95926;--s3:#199e70;--s4:#c98500;--s1-alt:#1f5ea8;--up:#0ca30c}
*{box-sizing:border-box}body{margin:0;background:var(--page)}
.viz-root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--text-primary);background:var(--page);padding:24px 16px;max-width:1200px;margin:0 auto}
h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:0 0 12px}.sub{color:var(--text-secondary);font-size:13px}
.grid{display:grid;gap:16px;margin-bottom:16px}.g5{grid-template-columns:repeat(5,1fr)}.g2{grid-template-columns:1fr 1fr}.g4{grid-template-columns:repeat(4,1fr)}
@media(max-width:900px){.g5,.g4,.g2{grid-template-columns:1fr}}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;padding:16px;min-width:0}
.kpi .label{font-size:12px;color:var(--text-secondary)}.kpi .value{font-size:26px;font-weight:600;margin:6px 0 2px}.kpi .foot{font-size:12px;color:var(--muted)}
.chip{display:inline-flex;gap:6px;align-items:center;font-size:12px;font-weight:600;padding:3px 10px;border-radius:999px;border:1px solid var(--border)}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block}
.d-up{color:var(--up)}.d-down{color:var(--down)}.d-flat{color:var(--muted)}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:7px 8px;border-bottom:1px solid var(--grid);text-align:left;vertical-align:top}
td.n,th.n{text-align:right;font-variant-numeric:tabular-nums}th{color:var(--text-secondary);font-weight:500}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--text-secondary);margin:4px 0 8px}.legend span{display:inline-flex;gap:6px;align-items:center}
.sw{width:10px;height:10px;border-radius:2px;display:inline-block}.tag{font-size:11px;color:var(--muted)}
.tabs{display:flex;gap:4px;flex-wrap:wrap;border-bottom:1px solid var(--grid);margin:16px 0}
.tabs button{font:inherit;font-size:13px;background:none;border:0;border-bottom:2px solid transparent;padding:8px 12px;color:var(--text-secondary);cursor:pointer}
.tabs button[aria-selected=true]{color:var(--text-primary);border-bottom-color:var(--s1);font-weight:600}
.panel{display:none}.panel.on{display:block}
a{color:var(--s1)}td.lk{white-space:nowrap}tr.detail>td{background:var(--page);padding:12px}button.dt,button.cp{font:inherit;font-size:11px;padding:1px 6px;border:1px solid var(--border);border-radius:4px;background:transparent;color:var(--text-secondary);cursor:pointer}code{font-size:12px}
.overflow{overflow-x:auto}
"""

JS = """
function show(id){const b=document.querySelector('.tabs button[data-t="'+id+'"]');if(!b)return;
document.querySelectorAll('.tabs button').forEach(x=>x.setAttribute('aria-selected','false'));
document.querySelectorAll('.panel').forEach(p=>p.classList.remove('on'));
b.setAttribute('aria-selected','true');document.getElementById(id).classList.add('on');}
document.querySelectorAll('.tabs button').forEach(b=>b.addEventListener('click',()=>{show(b.dataset.t);history.replaceState(null,'','#'+b.dataset.t);}));
if(location.hash)show(decodeURIComponent(location.hash.slice(1)));
document.querySelectorAll('button.dt').forEach(b=>b.addEventListener('click',()=>{
const r=document.getElementById(b.dataset.row);const open=r.hidden;r.hidden=!open;
b.setAttribute('aria-expanded',String(open));b.textContent=open?'상세 접기':'상세 펼치기';}));
document.querySelectorAll('button.cp').forEach(b=>b.addEventListener('click',async()=>{
const url=new URL(b.dataset.href,location.href).href;let ok=false;
try{await navigator.clipboard.writeText(url);ok=true;}catch(_){const t=document.createElement('textarea');t.value=url;document.body.appendChild(t);t.select();try{ok=document.execCommand('copy');}catch(__){}t.remove();}
const o=b.textContent;b.textContent=ok?'복사됨 ✓':'복사 실패';setTimeout(()=>b.textContent=o,1500);}));
"""


def _r1(v, nd=1):
    return round(v, nd) if isinstance(v, (int, float)) else (v if v is not None else "-")


_DETAIL_IDS = __import__('itertools').count(1)


def e(x):
    return html.escape(str(x))


def chip(ok, good="PASS", bad="FAIL"):
    if ok:
        return f'<span class="chip"><span class="dot" style="background:var(--good)"></span>✓ {e(good)}</span>'
    return f'<span class="chip"><span class="dot" style="background:var(--crit)"></span>✕ {e(bad)}</span>'


def delta(cur, ref, lower_better=True, unit="", prefix=""):
    if ref is None or cur is None:
        return '<span class="d-flat">첫 기록</span>'
    d = cur - ref
    if abs(d) < 1e-9:
        return '<span class="d-flat">— 유지</span>'
    pct = d / ref * 100 if ref else 0
    good = (d < 0) == lower_better
    return (f'<span class="{"d-up" if good else "d-down"}">{"▼" if d < 0 else "▲"} {prefix}{abs(d):.1f}{unit} '
            f'({pct:+.0f}%) {"개선" if good else "악화"}</span>')


COMPLIANCE_KEYS = [("pipeline_complete", "파이프라인 완료"), ("state_valid", "상태 검증 위반 0"),
                   ("runlog_pending", "run-log 적체 0"), ("gate_evidence", "게이트 증거"), ("checkpoint_commits", "체크포인트 커밋")]


def compliance(m):
    out = []
    for k, label in COMPLIANCE_KEYS:
        if k == "runlog_pending":
            ok = m.get(k) == 0
        elif k == "checkpoint_commits":
            ok = not m.get("worktree_task") or ((m.get(k) or 0) >= 1 and not m.get("raw_commits"))
        else:
            ok = bool(m.get(k))
        out.append((label, ok))
    return out


def axes_for(m):
    comp = compliance(m)
    stages = m.get("stage_min") or {}
    longest = max(stages.items(), key=lambda kv: kv[1]) if stages else None
    return {
        "completeness": {"value": f'{round((m.get("hidden_pass_rate") or 0) * 100)}%' if m.get("hidden_summary") else f'{sum(ok for _, ok in comp)}/5',
                         "foot": f'숨은 테스트 {m.get("hidden_summary") or "-"} · 준수 {sum(ok for _, ok in comp)}/5',
                         "ok": m.get("verdict") == "PASS"},
        "speed": {"value": m.get("wall_min"), "foot": f"가장 긴 단계: {longest[0]} {longest[1]}분" if longest else "단계 소요 없음"},
        "cost": {"value": m.get("cost_usd"), "foot": f'{m.get("turns") or "-"}턴 · 출력 {round((m.get("output_tokens") or 0) / 1000, 1)}k 토큰'},
        "correction": {"found": m.get("log_error") or 0, "fixed": m.get("log_fix") or 0, "rework": max((m.get("gate_iterations") or 1) - 1, 0)},
        "autonomy": {"waits": m.get("decision_requests") or 0},
    }


def median_ref(hist, key):
    vals = [h.get(key) for h in hist if isinstance(h.get(key), (int, float))]
    return statistics.median(vals) if vals else None


def stage_bar(stages, W=1100):
    items = list(stages.items())
    total = sum(v for _, v in items) or 1
    x, out = 0.0, []
    for i, (name, v) in enumerate(items):
        c = "var(--s1)" if i % 2 == 0 else "var(--s1-alt)"
        w = (W - 40) * v / total
        lab = (f'<text x="{20 + x + 6:.1f}" y="62" font-size="12" fill="var(--text-secondary)">{e(name)} {v}분</text>' if w > 120 else
               f'<text x="{20 + x + w / 2:.1f}" y="62" font-size="10" text-anchor="middle" fill="var(--text-muted, var(--text-secondary))">{e(name[:2])}</text>' if w > 22 else "")
        out.append(f'<rect x="{20 + x:.1f}" y="10" width="{max(w - 2, 1):.1f}" height="34" rx="4" fill="{c}"><title>{e(name)}: {v}분</title></rect>{lab}')
        x += w
    return f'<svg viewBox="0 0 {W} 76" width="100%" role="img" aria-label="단계별 소요">{"".join(out)}</svg>'


def summary_panel(m, hist):
    ax = axes_for(m)
    ref_w, ref_c = median_ref(hist, "wall_min"), median_ref(hist, "cost_usd")
    c = ax["correction"]
    cards = [
        ("완성도", ax["completeness"]["value"], ax["completeness"]["foot"], chip(ax["completeness"]["ok"], "합격", "불합격")),
        ("속도", f'{ax["speed"]["value"]}분', ax["speed"]["foot"], delta(m.get("wall_min"), ref_w, unit="분")),
        ("비용 효율", f'${ax["cost"]["value"]}', ax["cost"]["foot"], delta(m.get("cost_usd"), ref_c, prefix="$")),
        ("자기 교정력", f'{c["fixed"]} / {c["found"]}', f'발견 {c["found"]} · 교정 {c["fixed"]} · 게이트 재작업 {c["rework"]}',
         delta(c["rework"], median_ref([{"r": max((h.get("gate_iterations") or 1) - 1, 0)} for h in hist], "r"), unit="회")),
        ("자율성", f'{ax["autonomy"]["waits"]}회', "사용자 결정 요청", chip(ax["autonomy"]["waits"] == 0 or m.get("mode") == "judgment", "무인 완주" if ax["autonomy"]["waits"] == 0 else "결정 요청", "확인 필요")),
    ]
    cards_html = "".join(f'<div class="card kpi"><div class="label">{e(a)}</div><div class="value">{e(b)}</div><div class="foot">{e(f)}</div><div style="margin-top:8px">{d}</div></div>' for a, b, f, d in cards)
    stages = m.get("stage_min") or {}
    slog = m.get("stage_log") or {}
    hist_stage = {s: median_ref([h.get("stage_min") or {} for h in hist], s) for s in stages}
    srows = "".join(
        f'<tr><td>{e(s)}</td><td class="n">{v}</td><td>{delta(v, hist_stage.get(s), unit="분")}</td>'
        + "".join(f'<td class="n">{(slog.get(s) or {}).get(k, 0)}</td>' for k in ("GATE", "ERROR", "FIX", "DECISION")) + "</tr>"
        for s, v in stages.items())
    corr = m.get("corrections") or []
    crow = "".join(f'<tr><td>{e(x["stage"])}</td><td>{e(x["kind"])}</td><td>{e(x["text"])}</td></tr>' for x in corr) or '<tr><td colspan="3" class="tag">기록 없음</td></tr>'
    comp = compliance(m)
    allm = [("판정", m.get("verdict")), ("불합격 사유", "; ".join(m.get("fail_reasons") or []) or "없음"), ("숨은 테스트", m.get("hidden_summary") or "-")]
    allm += [(label, "✓" if ok else "✕ 불충족") for label, ok in comp]
    allm += [("최종 수행 시간", f'{m.get("wall_min")}분'), ("비용", f'${m.get("cost_usd")}'), ("턴", m.get("turns")), ("출력 토큰", m.get("output_tokens")),
             ("서브에이전트", m.get("subagent_runs") if m.get("subagent_runs") else "측정 안 됨(run-log 워커 사건 없음)"),
             ("게이트 반복", m.get("gate_iterations")), ("체크포인트 커밋(도구/우회)", f'{m.get("checkpoint_commits", 0)} / {m.get("raw_commits", 0)}'), ("run-log 적체 첫 사건", json.dumps(m.get("runlog_first_pending"), ensure_ascii=False) if m.get("runlog_first_pending") else "없음"),
             ("프레임워크 지문", m.get("framework") or "기록 없음(지문 도입 전 실행)")]
    mrow = "".join(f'<tr><td>{e(k)}</td><td class="n">{e(v)}</td></tr>' for k, v in allm)
    total = round(sum(stages.values()), 1)
    return f"""
<div class="grid g5">{cards_html}</div>
<div class="card" style="margin-bottom:16px"><h2>단계별 소요 — run-log {total}분 (최종 수행 시간 {m.get("wall_min")}분)</h2>
{stage_bar(stages) if stages else '<div class="tag">단계 소요 없음</div>'}
<div class="overflow"><table><tr><th>단계</th><th class="n">소요(분)</th><th>이력 중앙값 대비</th><th class="n">게이트</th><th class="n">오류</th><th class="n">수정</th><th class="n">결정</th></tr>{srows}</table></div>
<div class="tag">소요: run-log 단계별 마지막 상태 전이 기준 · 게이트/오류/수정/결정: AGENTIC-LOG 단계 열 기준</div></div>
<div class="grid g2"><div class="card"><h2>자기 교정 기록</h2><div class="overflow"><table><tr><th>단계</th><th>구분</th><th>내용</th></tr>{crow}</table></div></div>
<div class="card"><h2>전체 지표</h2><table>{mrow}</table></div></div>"""


def _setting(x):
    return "미지정" if not x else f'{x.get("model")}/{x.get("effort") or "기본"}'


def settings_rows(runs):
    """변형별 변형 설정(선언 design·impl, 적용된 모델·구현 에이전트 사본)을 표 행 HTML로 만든다."""
    rows = []
    for label, pick in (("설계 설정(선언)", lambda s: _setting((s.get("declared") or {}).get("design"))),
                        ("구현 설정(선언)", lambda s: _setting((s.get("declared") or {}).get("impl"))),
                        ("적용된 모델", lambda s: ", ".join((s.get("applied") or {}).get("models") or []) or "기록 없음"),
                        ("구현 에이전트 사본", lambda s: ", ".join(sorted((s.get("applied") or {}).get("agent_overrides") or {})) or "없음")):
        rows.append(f'<tr><td>{e(label)}</td>' + "".join(f'<td>{e(pick(r.get("settings") or {}))}</td>' for r in runs) + "</tr>")
    return "".join(rows)


def comparison_card(comparison, variants):
    """비교 무효 배너 또는 변형별 지표 평균(최소~최대)과 품질 하한 판정 카드."""
    if not comparison:
        return ""
    if not comparison.get("valid", True):
        fws = comparison.get("frameworks_by_variant") or {}
        lines = "".join(f'<li>{e(v)}: <code>{e(", ".join(fws.get(v) or []) or "기록 없음")}</code></li>' for v in variants)
        return (f'<div class="card" style="margin-bottom:16px;border-color:var(--crit)"><h2 class="d-down">비교 무효 — FW 버전 상이</h2>'
                f'<div class="sub">변형 간 프레임워크 지문이 달라 결과를 비교하지 않습니다. 같은 FW 버전으로 다시 실행하세요.</div><ul>{lines}</ul></div>')
    mt = comparison.get("metrics") or {}
    head = "".join(f'<th class="n">{e(v)}</th>' for v in variants)
    body = ""
    for k in ("wall_min", "cost_usd", "turns", "subagent_runs", "gate_iterations", "hidden_pass_rate", "test_fix_iterations"):
        cells = ""
        for v in variants:
            st = (mt.get(v) or {}).get(k)
            cells += f'<td class="n">{st["avg"]:.2f} ({st["min"]:.2f}~{st["max"]:.2f})</td>' if st else '<td class="n">-</td>'
        body += f'<tr><td>{e(k)}</td>{cells}</tr>'
    fl = comparison.get("floor") or {}
    frows = "".join(
        f'<tr><td>{e(v)}</td><td>{chip(fl[v]["met"], "하한 충족", "하한 미충족(결정 대상 아님)")}</td>'
        f'<td class="n">{fl[v]["hidden_avg"]:.2f} / {fl[v]["base_hidden_avg"]:.2f}</td><td class="n">{fl[v]["pass_ratio"]:.2f} / {fl[v]["base_pass_ratio"]:.2f}</td></tr>'
        for v in variants[1:] if v in fl)
    return (f'<div class="grid g2"><div class="card"><h2>지표별 평균 (최소~최대)</h2><div class="overflow"><table><tr><th>지표</th>{head}</tr>{body}</table></div></div>'
            f'<div class="card"><h2>품질 하한 판정</h2><div class="tag" style="margin-bottom:8px">기준 변형 {e(comparison.get("baseline"))} · 숨은 테스트 통과율 평균과 PASS 비율이 모두 기준 이상이어야 충족 (후보 / 기준)</div>'
            f'<div class="overflow"><table><tr><th>변형</th><th>판정</th><th class="n">숨은 테스트 평균</th><th class="n">PASS 비율</th></tr>{frows}</table></div></div></div>')


def compare_panel(runs, comparison=None):
    variants = [r["variant"] for r in runs]
    krows = [("판정", [chip(r["verdict"] == "PASS") for r in runs]), ("숨은 테스트", [e(r.get("hidden_summary") or "-") for r in runs]),
             ("최종 수행 시간", [f'{r.get("wall_min")}분' for r in runs]), ("비용", [f'${r.get("cost_usd")}' for r in runs]),
             ("턴", [e(r.get("turns")) for r in runs]), ("서브에이전트", [e(r.get("subagent_runs") or "측정 안 됨") for r in runs]), ("게이트 반복", [e(r.get("gate_iterations")) for r in runs])]
    head = "".join(f'<th class="n">{e(v)}</th>' for v in variants)
    ktab = "".join(f'<tr><td>{e(k)}</td>' + "".join(f'<td class="n">{v}</td>' for v in vals) + "</tr>" for k, vals in krows)
    comps = [compliance(r) for r in runs]
    ctab = "".join(f'<tr><td>{e(label)}</td>' + "".join(f'<td>{"✓" if c[i][1] else "✕ 불충족"}</td>' for c in comps) + "</tr>" for i, (label, _) in enumerate(comps[0]))
    stages = []
    for r in runs:
        for s in (r.get("stage_min") or {}):
            if s not in stages:
                stages.append(s)
    mx = max([v for r in runs for v in (r.get("stage_min") or {}).values()] or [1])
    W, bw, gap = 560, 14, 2
    rowh = len(runs) * (bw + gap) + 14
    rows = []
    for i, s in enumerate(stages):
        y = 10 + i * rowh
        rows.append(f'<text x="0" y="{y + 12}" font-size="12" fill="var(--text-secondary)">{e(s)}</text>')
        for j, r in enumerate(runs):
            v = (r.get("stage_min") or {}).get(s, 0)
            w = (W - 170) * v / mx
            yy = y + j * (bw + gap)
            rows.append(f'<rect x="90" y="{yy}" width="{max(w, 1):.1f}" height="{bw}" rx="4" fill="{SERIES[j % 4]}"><title>{e(r["variant"])} · {e(s)}: {v}분</title></rect>'
                        f'<text x="{96 + w:.1f}" y="{yy + 11}" font-size="11" fill="var(--text-secondary)">{v}</text>')
    grouped = f'<svg viewBox="0 0 {W} {10 + rowh * len(stages)}" width="100%" role="img" aria-label="단계별 소요 비교">{"".join(rows)}</svg>'
    legend = "".join(f'<span><span class="sw" style="background:{SERIES[j % 4]}"></span>{e(v)}</span>' for j, v in enumerate(variants))
    diverging = ""
    if len(runs) == 2:
        a, b = runs
        mets = [("최종 수행 시간", "wall_min"), ("비용", "cost_usd"), ("턴", "turns"), ("서브에이전트", "subagent_runs"), ("게이트 반복", "gate_iterations")]
        mets = [(n, a.get(k), b.get(k)) for n, k in mets if a.get(k) and isinstance(b.get(k), (int, float))]
        if mets:
            DW, lab = 560, 110
            mxp = max(abs((y - x) / x * 100) for _, x, y in mets) or 1
            mid = lab + (DW - lab) / 2
            sc = ((DW - lab) / 2 - 80) / mxp
            drows = []
            for i, (n, x, y) in enumerate(mets):
                pct = (y - x) / x * 100
                good = pct < 0
                flat = abs(pct) < 0.5
                w = abs(pct) * sc
                xx = mid - w if pct < 0 else mid
                yy = 10 + i * 30
                tx, anc = (xx - 6, "end") if pct < 0 else (xx + w + 6, "start")
                drows.append(f'<text x="0" y="{yy + 13}" font-size="12" fill="var(--text-secondary)">{e(n)}</text>'
                             f'<rect x="{xx:.1f}" y="{yy}" width="{max(w, 2):.1f}" height="16" rx="4" fill="{"var(--axis)" if flat else "var(--s1)" if good else "var(--crit)"}"><title>{e(n)}: {x} → {y} ({pct:+.0f}%)</title></rect>'
                             f'<text x="{tx:.1f}" y="{yy + 12}" font-size="11" text-anchor="{anc}" fill="var(--text-secondary)">{"0% 동일" if flat else f"{pct:+.0f}% " + ("개선" if good else "악화")}</text>')
            drows.append(f'<line x1="{mid}" y1="4" x2="{mid}" y2="{14 + 30 * len(mets)}" stroke="var(--axis)"/>')
            diverging = (f'<div class="card"><h2>{e(b["variant"])}의 {e(a["variant"])} 대비 변화율</h2><div class="legend"><span><span class="sw" style="background:var(--s1)"></span>개선(감소)</span>'
                         f'<span><span class="sw" style="background:var(--crit)"></span>악화(증가)</span></div><svg viewBox="0 0 {DW} {20 + 30 * len(mets)}" width="100%" role="img" aria-label="변화율">{"".join(drows)}</svg></div>')
    return f"""
<div class="card" style="margin-bottom:16px"><div class="legend">{legend}</div></div>
{comparison_card(comparison, variants)}
<div class="card" style="margin-bottom:16px"><h2>변형 설정</h2><div class="overflow"><table><tr><th>항목</th>{head}</tr>{settings_rows(runs)}</table></div></div>
<div class="grid g2"><div class="card"><h2>핵심 지표</h2><div class="overflow"><table><tr><th>지표</th>{head}</tr>{ktab}</table></div></div>
<div class="card"><h2>준수 항목</h2><div class="overflow"><table><tr><th>항목</th>{"".join(f"<th>{e(v)}</th>" for v in variants)}</tr>{ctab}</table></div></div></div>
<div class="grid g2"><div class="card"><h2>단계별 소요(분)</h2>{grouped}</div>{diverging}</div>"""


def trend_chart(label, pts, unit="", prefix="", W=360, H=150):
    """pts: [(라벨, 값, 현재여부)] 오래된 순."""
    if len(pts) < 2:
        return f'<div class="card"><div class="tag">{e(label)}: 이력 1회 — 추세 없음</div></div>'
    xs = [30 + i * (W - 70) / (len(pts) - 1) for i in range(len(pts))]
    vals = [p[1] for p in pts]
    lo, hi = min(vals), max(vals)
    pad = (hi - lo) * 0.2 or 1
    lo, hi = lo - pad, hi + pad
    ys = [H - 25 - (v - lo) / (hi - lo) * (H - 45) for v in vals]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(zip(xs, ys)))
    grid = "".join(f'<line x1="30" x2="{W - 10}" y1="{H - 25 - k * (H - 45) / 2:.1f}" y2="{H - 25 - k * (H - 45) / 2:.1f}" stroke="var(--grid)"/>' for k in range(3))
    marks = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{"var(--s1)" if cur else "var(--surface-1)"}" stroke="var(--s1)" stroke-width="2"><title>{e(l)}: {prefix}{v}{unit}{" (이번 실행)" if cur else ""}</title></circle>'
                    f'<text x="{x:.1f}" y="{H - 8}" font-size="10" text-anchor="middle" fill="var(--muted)">{e(l)}</text>' for (l, v, cur), x, y in zip(pts, xs, ys))
    last = pts[-1][1]
    ref = statistics.median(vals[-4:-1]) if len(vals) > 1 else None
    return (f'<div class="card"><div style="font-size:12px;color:var(--text-secondary)">{e(label)}</div><div style="font-size:22px;font-weight:600;margin:4px 0">{prefix}{last}{unit}</div>'
            f'<div style="font-size:12px">{delta(last, ref, unit=unit, prefix=prefix)} <span class="tag">최근 3회 중앙값 대비</span></div>'
            f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="{e(label)} 추세">{grid}<path d="{path}" fill="none" stroke="var(--s1)" stroke-width="2"/>{marks}</svg></div>')


def history_panel(variant, current, scenario_id, hist_same, hist_skill, here_dir):
    seq = sorted(hist_same, key=lambda h: h["created_at"]) + [dict(current, created_at=current.get("created_at", ""), _current=True)]
    lab = lambda h: (h.get("created_at") or "")[5:10] or "이번"
    charts = (trend_chart("최종 수행 시간", [(lab(h), h.get("wall_min"), h.get("_current")) for h in seq if h.get("wall_min") is not None], unit="분")
              + trend_chart("비용", [(lab(h), h.get("cost_usd"), h.get("_current")) for h in seq if h.get("cost_usd") is not None], prefix="$")
              + trend_chart("게이트 반복", [(lab(h), h.get("gate_iterations"), h.get("_current")) for h in seq if h.get("gate_iterations") is not None], unit="회")
              + trend_chart("세션이 발견한 문제", [(lab(h), h.get("log_error") or 0, h.get("_current")) for h in seq], unit="건"))
    rows = []
    for h in sorted(hist_skill, key=lambda h: h["created_at"], reverse=True):
        links = ""
        if h.get("report_path"):
            rel = os.path.relpath(h["report_path"], here_dir)
            links = f'<a href="{e(rel)}" target="_blank" rel="noopener">새 탭 열기 ↗</a> <button class="cp" data-href="{e(rel)}" type="button">링크 복사</button>'
        did = f"d{next(_DETAIL_IDS)}"
        links = f'<button class="dt" data-row="{did}" type="button" aria-expanded="false">상세 펼치기</button> ' + links
        rows.append(f'<tr><td>{e(h["created_at"][:16])}</td><td><code>{e(h["scenario"])}</code></td><td>{e(MODE_KO.get(h.get("mode"), h.get("mode")))}</td>'
                    f'<td>{chip(h.get("verdict") == "PASS")}</td><td class="n">{e(_r1(h.get("wall_min")))}</td><td class="n">{e(_r1(h.get("cost_usd"), 2))}</td>'
                    f'<td class="n">{e(h.get("gate_iterations"))}</td><td class="tag">{e(h.get("framework") or "-")}</td><td class="lk">{links}</td></tr>'
                    f'<tr id="{did}" class="detail" hidden><td colspan="9"><div class="tag" style="margin:4px 0 8px">{e(h["created_at"][:16])} · <code>{e(h["scenario"])}</code> 실행 상세</div>{summary_panel(h, [])}</td></tr>')
    table = ("".join(rows) or '<tr><td colspan="9" class="tag">과거 기록 없음 — 이번 실행이 첫 기록입니다</td></tr>')
    return f"""
<div class="card" style="margin-bottom:16px"><b>{e(variant)}</b> · 이번 시나리오 <code>{e(scenario_id)}</code> 이력 {len(hist_same)}회 + 이번 실행</div>
<div class="grid g4">{charts}</div>
<div class="card"><h2>{e(variant)} 스킬 테스트 이력 (전체 시나리오)</h2><div class="tag" style="margin-bottom:8px">'상세 펼치기'는 과거 실행 상세를 이 페이지 안에서 보여줍니다(모든 뷰어). '새 탭 열기'는 과거 대시보드 전체를 새 탭으로 엽니다 — 로컬 파일 간 이동을 막는 뷰어(예: Orca 내장 브라우저)에서는 동작하지 않으니 '상세 펼치기'나 '링크 복사' 후 새 탭 주소창에 붙여 넣기를 쓰세요. 태스크가 <code>tasks/backup/</code>으로 아카이브돼도 다음 테스트 기록 때 모든 대시보드의 링크가 새 위치로 다시 만들어지고, 바로 고치려면 <code>refresh</code>를 실행하세요.</div>
<div class="overflow"><table><tr><th>일시</th><th>시나리오</th><th>모드</th><th>판정</th><th class="n">최종 수행 시간(분)</th><th class="n">비용($)</th><th class="n">게이트 반복</th><th>프레임워크</th><th>보고서</th></tr>{table}</table></div></div>"""


def render_report(scenario, runs, history, here_dir, created_at, comparison=None):
    """runs: 이번 실행 지표 목록, history: 과거 실행 레코드 목록(variant·scenario·created_at·report_path 포함)."""
    variants = []
    for r in runs:
        if r["variant"] not in variants:
            variants.append(r["variant"])
    first = {v: next(r for r in runs if r["variant"] == v) for v in variants}
    tabs, panels = [], []
    if len(variants) == 1:
        v = variants[0]
        hs = [h for h in history if h["variant"] == v and h["scenario"] == scenario["id"]]
        tabs.append(("summary", "요약"))
        panels.append(("summary", summary_panel(dict(first[v], mode=scenario["mode"]), hs)))
    else:
        tabs.append(("compare", "비교"))
        panels.append(("compare", compare_panel([first[v] for v in variants], comparison)))
        for i, v in enumerate(variants):
            hs = [h for h in history if h["variant"] == v and h["scenario"] == scenario["id"]]
            tabs.append((f"detail{i}", f"상세: {v}"))
            panels.append((f"detail{i}", summary_panel(dict(first[v], mode=scenario["mode"]), hs)))
    for i, v in enumerate(variants):
        hs = [h for h in history if h["variant"] == v and h["scenario"] == scenario["id"]]
        hk = [h for h in history if h["variant"].split()[0] == v.split()[0]]
        tabs.append((f"hist{i}", f"이력: {v}"))
        panels.append((f"hist{i}", history_panel(v, dict(first[v], created_at=created_at), scenario["id"], hs, hk, here_dir)))
    verdicts = " ".join(chip(first[v]["verdict"] == "PASS", f"{v} PASS", f"{v} FAIL") for v in variants)
    reps = max(r.get("rep", 1) for r in runs)
    tabs_html = "".join(f'<button data-t="{t}" aria-selected="{"true" if i == 0 else "false"}">{e(n)}</button>' for i, (t, n) in enumerate(tabs))
    panels_html = "".join(f'<section id="{t}" class="panel{" on" if i == 0 else ""}">{p}</section>' for i, (t, p) in enumerate(panels))
    title = f'스킬 테스트 보고서 — {scenario.get("title") or scenario["id"]}'
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><style>{CSS}</style></head><body><div class="viz-root">
<h1>{e(title)}</h1><div class="sub"><code>{e(scenario["id"])}</code> · {e(MODE_KO.get(scenario["mode"], scenario["mode"]))} · 변형 {len(variants)}개 · 반복 {reps}회 · {e(created_at)}</div>
<div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">{verdicts}</div>
<div class="tabs" role="tablist">{tabs_html}</div>{panels_html}
<div class="tag" style="margin-top:16px">opal-skill-tester · 반복 실행은 첫 회차 기준으로 표시하며 전체 수치는 metrics.json에 있습니다.</div>
</div><script>{JS}</script></body></html>"""
