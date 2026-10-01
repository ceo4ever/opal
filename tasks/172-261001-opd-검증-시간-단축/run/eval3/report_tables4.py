"""EVAL-RESULT-4 표 생성. results4.json·mapping.json만 읽는다(수치 재계산 없음). 사용: python3 report_tables4.py"""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
r = json.load(open(os.path.join(D, 'results4.json'))); m = json.load(open(os.path.join(D, 'mapping.json')))
C = ['E0', 'E1', 'E3']
f = lambda x: f"{x:.1f}"
print('## summary')
print('| 항목 | ' + ' | '.join(C) + ' |'); print('|---|' + '---|' * 3)
rows = [
 ('trial 수 (호출 수)', lambda v: f"{v['n_trials']} ({v['n_calls']})"),
 ('형식 오류 design/scenario/합계', lambda v: '/'.join(str(v['format_error_count'][k]) for k in ('design','scenario','total'))),
 ('결합 불성립 (33 중)', lambda v: str(v['combined_fail'])),
 ('결함 누락 (15 trial 중)', lambda v: f"{v['defect']['missed']} (최악 가정 {v['defect']['missed_worst_case']})"),
 ('clean fail (9 중)', lambda v: f"{v['clean']['fail']} (최악 가정 {v['clean']['fail_worst_case']})"),
 ('borderline fail (9 중, 규칙 밖)', lambda v: str(v['borderline']['fail'])),
 ('규칙 1 결함 누락 = 0', lambda v: 'O' if v['rule1'] else 'X'),
 ('규칙 2 clean fail <= 2', lambda v: 'O' if v['rule2'] else 'X'),
 ('규칙 3 형식 오류 <= 2', lambda v: 'O' if v['rule3'] else 'X'),
 ('규칙 4 결합 불성립 <= 3', lambda v: 'O' if v['rule4'] else 'X'),
 ('채택 가능', lambda v: '가능' if v['adoptable'] else '불가'),
 ('결합 소요 평균/중앙/p90/최대(초)', lambda v: '/'.join(f(v['time_combined'][k]) for k in ('mean','median','p90','max'))),
]
for n, fn in rows: print(f"| {n} | " + ' | '.join(fn(r['cands'][c]) for c in C) + ' |')
print('\n## cases')
print('| ID | 라벨 | 종류 | 기대 | ' + ' | '.join(C) + ' |'); print('|---|---|---|---|' + '---|' * 3)
for cid, v in r['cases'].items():
    cells = []
    for c in C:
        parts = []
        for t in sorted(v['cands'][c], key=lambda x: x['rep']):
            parts.append(t['verdict'] if t['verdict'] == 'pass' and not t['fail_axes'] else
                         (t['verdict'] + ('(' + ','.join({'completeness':'comp','decision_clarity':'deci','executability':'exec','recoverability':'reco'}[a] for a in t['fail_axes']) + ')' if t['fail_axes'] else '')))
        cells.append('; '.join(parts))
    exp = 'pass' if m[cid]['expected_verdict']=='pass' else 'fail[' + ','.join(m[cid]['expected_axes']) + ']'
    print(f"| {cid} | {v['label']} | {v['kind']} | {exp} | " + ' | '.join(cells) + ' |')
print('\n## time')
print('| 후보 | 구분 | 평균 | 중앙 | p90 | 최대 |'); print('|---|---|---|---|---|---|')
for c in C:
    for k, n in (('time_combined','결합'),('time_call_design','design 호출'),('time_call_scenario','scenario 호출')):
        t = r['cands'][c][k]; print(f"| {c} | {n} | {f(t['mean'])} | {f(t['median'])} | {f(t['p90'])} | {f(t['max'])} |")
