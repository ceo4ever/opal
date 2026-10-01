#!/usr/bin/env python3
"""W-6 / D-14 TEST 병렬 실측 프로브.

(a) 단일 에이전트 안 병렬: 독립 명령 N개(각 SLEEP초)를 순차 vs 한 번의 bash에서 `&`·`wait`로
    동시 실행, 명령별 출력·종료 코드를 파일로 받아 3회 측정한다.
(b) 동시 scenario-mark: 8프로세스가 서로 다른 S-ID를 mark하는 것을 5라운드 반복해
    scenario-status에서 사라진 시나리오 수를 센다. 임시 폴더 픽스처만 사용한다.

사용: python3 probe.py [--json OUT.json]   (환경변수 TEST_TOOL=run.sh 경로 덮어쓰기)
"""
import json, os, pathlib, shutil, statistics, subprocess, sys, tempfile, time

N, SLEEP, REPS = 4, 2, 3
PROCS, ROUNDS = 8, 5
TEST_TOOL = os.environ.get("TEST_TOOL", os.path.expanduser("~/.opal/tools/test-tool/run.sh"))


def cmd_body(i):
    # 명령 i: SLEEP초 대기 후 출력 "out-i", 종료 코드 i
    return f"sleep {SLEEP}; echo out-{i}; exit {i}"


def run_seq(work):
    t = time.monotonic()
    for i in range(N):
        p = subprocess.run(["bash", "-c", cmd_body(i)], capture_output=True, text=True)
        (work / f"{i}.out").write_text(p.stdout)
        (work / f"{i}.rc").write_text(str(p.returncode))
    return time.monotonic() - t


def run_par(work):
    lines = []
    for i in range(N):
        lines.append(f"( {cmd_body(i)} ) > {work}/{i}.out 2>&1 & pids[{i}]=$!")
    for i in range(N):
        lines.append(f"wait ${{pids[{i}]}}; echo $? > {work}/{i}.rc")
    script = "\n".join(lines)
    t = time.monotonic()
    subprocess.run(["bash", "-c", script], check=False)
    return time.monotonic() - t


def preserved(work):
    for i in range(N):
        if (work / f"{i}.out").read_text().strip() != f"out-{i}":
            return False
        if (work / f"{i}.rc").read_text().strip() != str(i):
            return False
    return True


def part_a(tmp):
    seq, par, pres = [], [], []
    for r in range(REPS):
        w = tmp / f"a-seq-{r}"; w.mkdir(); seq.append(run_seq(w)); pres.append(preserved(w))
        w = tmp / f"a-par-{r}"; w.mkdir(); par.append(run_par(w)); pres.append(preserved(w))
    ms, mp = statistics.median(seq), statistics.median(par)
    return dict(seq=seq, par=par, seq_median=ms, par_median=mp, ratio=mp / ms,
                preserved_all=all(pres), preserved_each=pres)


def tt(*a):
    return subprocess.run([TEST_TOOL, *a], capture_output=True, text=True)


def part_b(tmp):
    rounds = []
    for r in range(ROUNDS):
        fx = tmp / f"b-{r}"; fx.mkdir()
        scen = [dict(id=f"S-{k}", acceptance_ref="AC-1", type="check", expected="x", red_required=False)
                for k in range(1, PROCS + 1)]
        tt("scenario-init", "--task-path", str(fx), "--scenarios", json.dumps(scen))
        tt("scenario-lock", "--task-path", str(fx))
        procs = [subprocess.Popen([TEST_TOOL, "scenario-mark", "--task-path", str(fx), "--id", f"S-{k}",
                                   "--result", "pass"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for k in range(1, PROCS + 1)]
        outs = [p.communicate() for p in procs]
        ok_marks = sum(1 for p, o in zip(procs, outs) if p.returncode == 0 and '"ok": true' in o[0])
        st = tt("scenario-status", "--task-path", str(fx))
        try:
            passed = json.loads(st.stdout)["passed"]
            err = None
        except Exception as e:  # spec 파일 손상 등
            passed, err = 0, f"status_unreadable: {e}: {st.stdout[:120]}"
        rounds.append(dict(round=r + 1, mark_ok_reported=ok_marks, passed_in_status=passed,
                           lost=PROCS - passed, status_error=err))
    return dict(rounds=rounds, total_lost=sum(x["lost"] for x in rounds), any_lost=any(x["lost"] for x in rounds))


def verdict(a, b, lock_in_code):
    """D-14 규칙: (a) 가능 = 중앙값 비율<=0.60 and 출력·종료코드 모두 보존. (b) 불가 = 사라진 건>=1 or 코드에 파일 잠금 없음."""
    a_ok = a["ratio"] <= 0.60 and a["preserved_all"]
    b_impossible = b["any_lost"] or not lock_in_code
    return dict(a="가능" if a_ok else "불가", b="불가" if b_impossible else "가능")


def main():
    repo = pathlib.Path(__file__).resolve().parents[4]
    src = (repo / "opal/tools/test-tool/lib/scenario.py").read_text()
    lock_in_code = any(k in src for k in ("fcntl", "flock", "lockf", "msvcrt", "O_EXCL"))
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="probe-"))
    try:
        a = part_a(tmp); b = part_b(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = dict(a=a, b=b, lock_in_code=lock_in_code, verdict=verdict(a, b, lock_in_code),
               env=dict(python=sys.version.split()[0], test_tool=TEST_TOOL, n=N, sleep=SLEEP, reps=REPS,
                        procs=PROCS, rounds=ROUNDS))
    if "--json" in sys.argv:
        pathlib.Path(sys.argv[sys.argv.index("--json") + 1]).write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
