"""
@header {
  "module": "test_cache",
  "layer": "test",
  "domain": "oppb-runtime",
  "description": "oppb-runtime-tool cache 공개 CLI 계약 RED 테스트. 132 TEST-SCENARIO.md S-14(AC-13, H-4)와 S-15(AC-14)를 검증한다 — 같은 parent에서 fork한 병렬 candidate 2개를 모두 검증 통과시킨 뒤 하나를 publication해도 두 overlay가 모두 CAS에 잔존하고, stale sibling이 결정론적 seed에 intervening delta를 replay해 cold fallback 0으로 복구되며, conformance 미통과 opaque adapter는 non_reusable로 강등되어 해당 명령만 cold 실행된다. 또 soft cap·최소 여유를 작게 두고 retention 만료를 앞당긴 cache root에서 active·실행 중 candidate·publication 대기 node 삭제 0, closed node만 last-access LRU 회수, DONE·evidence 불변, 공간 부족 시 cacheless 강등 또는 disk_budget_exceeded를 확인한다. 제안서 §4.5 3계층 cache·cache DAG·retention이 SSOT다. PLAN H-6에 따라 내부 함수·클래스를 import하지 않고 공개 CLI(run.sh)와 cache root 파일 계약으로만 검증한다. mock/patch 금지 — 실제 git 저장소·실제 파일시스템만 사용한다(PLAN W-17).",
  "exports": [],
  "depends": ["opal/tools/oppb-runtime-tool/run.sh", "git CLI 2.x", "opal/tools/worktree-tool/tests/conftest.py(패턴 원천)"]
}
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess

import pytest

TOOL_DIR = pathlib.Path(__file__).resolve().parents[1]
RUN_SH = TOOL_DIR / "run.sh"

GIT_AUTHOR_ARGS = [
    "-c",
    "user.email=test@opal.local",
    "-c",
    "user.name=OPAL Test",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "init.defaultBranch=main",
]

# 제안서 §4.5 — pin 대상 3종. 이 상태의 node는 GC 삭제 대상이 아니다.
PINNED_STATES = ("active_run", "running_candidate", "publication_pending")


def run_git(args: list[str], cwd: pathlib.Path, check: bool = True) -> subprocess.CompletedProcess:
    cmd = ["git", *GIT_AUTHOR_ARGS, *args]
    result = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"git fixture 구성 실패: {' '.join(cmd)}\n"
            f"cwd={cwd}\nstdout={result.stdout}\nstderr={result.stderr}"
        )
    return result


def run_oppb(args: list[str], timeout: int = 180) -> subprocess.CompletedProcess:
    """공개 인터페이스(run.sh 서브프로세스)로만 호출한다. run.sh·cache 하위명령이 아직
    없으면(W-6·W-15 구현 전) 이 실패가 RED 증거다."""
    if not RUN_SH.exists():
        pytest.fail(
            "RED: opal/tools/oppb-runtime-tool/run.sh 미존재 — W-6·W-15 구현 전 정상 실패. "
            f"요청 명령: run.sh {' '.join(args)}"
        )
    return subprocess.run(
        ["bash", str(RUN_SH), *args], capture_output=True, text=True, timeout=timeout
    )


def parse_json_stdout(result: subprocess.CompletedProcess, label: str = "") -> dict:
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        pytest.fail(
            f"{label} stdout이 유효 JSON이 아님. exit={result.returncode}\n"
            f"stdout={result.stdout!r}\nstderr={result.stderr!r}\n원인: {exc}"
        )


def write_json(path: pathlib.Path, data) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _write(repo: pathlib.Path, relpath: str, content: str) -> pathlib.Path:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_hub_repo(base: pathlib.Path, name: str = "hub") -> pathlib.Path:
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    _write(repo, "README.md", "# hub\n")
    run_git(["add", "README.md"], cwd=repo)
    run_git(["commit", "-m", "init"], cwd=repo)
    return repo


def make_project_repo(base: pathlib.Path, name: str = "project") -> pathlib.Path:
    repo = base / name
    repo.mkdir(parents=True)
    run_git(["init", "-b", "main", "."], cwd=repo)
    _write(repo, "src/a.py", "A = 1\n")
    _write(repo, "src/b.py", "B = 1\n")
    _write(repo, "lockfile.lock", "dep-a==1.0.0\n")
    run_git(["add", "-A"], cwd=repo)
    run_git(["commit", "-m", "project seed"], cwd=repo)
    return repo


def init_run(repo: pathlib.Path, project: pathlib.Path) -> dict:
    result = run_oppb(
        ["init", "--allocator-root", str(repo), "--project-root", str(project)]
    )
    assert result.returncode == 0, (
        f"init 실패: exit={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}"
    )
    payload = parse_json_stdout(result, "init")
    for key in ("run_id", "run_root", "cache_root"):
        assert key in payload, f"init 응답에 {key} 없음: {payload}"
    return payload


# ─────────────────────────────────────────────────────────────────────────────
# adapter fixture — conformance suite에 투입할 실제 실행 가능 adapter 2종.
# mock이 아니라 진짜 스크립트다. replayable은 입력 변경을 검출하고 overlay를 격리하며,
# opaque는 입력이 바뀌어도 같은 출력을 재사용해 검출에 실패한다.
# ─────────────────────────────────────────────────────────────────────────────

REPLAYABLE_ADAPTER = """#!/usr/bin/env python3
import hashlib, json, pathlib, sys

args = json.loads(sys.argv[1])
overlay = pathlib.Path(args["overlay"])
overlay.mkdir(parents=True, exist_ok=True)
digest = hashlib.sha256()
for rel in sorted(args["inputs"]):
    digest.update(rel.encode())
    digest.update(pathlib.Path(args["source"], rel).read_bytes())
key = digest.hexdigest()
(overlay / "build.out").write_text(key, encoding="utf-8")
print(json.dumps({"ok": True, "output_manifest": {"build.out": key}, "input_key": key}))
"""

OPAQUE_ADAPTER = """#!/usr/bin/env python3
import json, pathlib, sys

args = json.loads(sys.argv[1])
overlay = pathlib.Path(args["overlay"])
overlay.mkdir(parents=True, exist_ok=True)
# 입력이 무엇이든 같은 산출물을 낸다 — 입력 변경 검출 실패.
(overlay / "build.out").write_text("constant", encoding="utf-8")
print(json.dumps({"ok": True, "output_manifest": {"build.out": "constant"}, "input_key": "constant"}))
"""


def install_adapter(base: pathlib.Path, name: str, body: str) -> pathlib.Path:
    path = base / f"{name}.py"
    path.write_text(body, encoding="utf-8")
    path.chmod(0o755)
    return path


def cache_nodes(cache_root: str) -> list[dict]:
    payload = parse_json_stdout(
        run_oppb(["cache", "list-nodes", "--cache-root", cache_root]), "cache list-nodes"
    )
    assert payload.get("ok") is True, f"cache list-nodes 실패: {payload}"
    return payload.get("nodes", [])


def node_ids(cache_root: str) -> set:
    return {node["node_id"] for node in cache_nodes(cache_root)}


@pytest.fixture
def cache_env(tmp_path: pathlib.Path):
    hub = make_hub_repo(tmp_path)
    repo = make_project_repo(tmp_path)
    payload = init_run(hub, repo)
    return {
        "tmp": tmp_path,
        "hub": hub,
        "repo": repo,
        "run_root": payload["run_root"],
        "cache_root": payload["cache_root"],
    }


# ═════════════════════════════════════════════════════════════════════════════
# S-14: cache DAG replay와 adapter conformance (수용기준 29, H-4)
# ═════════════════════════════════════════════════════════════════════════════


def test_s14_1_conformance_suite_classifies_adapters(cache_env):
    """[T132/S-14] conformance suite가 clean input·단일 source delta·config delta·
    dependency delta·병렬 overlay·stale seed 6항목을 검증한다. 입력 변화 검출과 overlay
    격리를 증명한 adapter만 `replayable`이고, 증명하지 못하면 `non_reusable`이다
    (제안서 §P2.2 cache adapter 계약, §4.5)."""
    cache_root, tmp = cache_env["cache_root"], cache_env["tmp"]
    good = install_adapter(tmp, "adapter_replayable", REPLAYABLE_ADAPTER)
    bad = install_adapter(tmp, "adapter_opaque", OPAQUE_ADAPTER)

    ok_payload = parse_json_stdout(
        run_oppb(["cache", "conformance", "--cache-root", cache_root, "--adapter", str(good)]),
        "cache conformance(replayable)",
    )
    assert ok_payload.get("ok") is True, ok_payload
    assert ok_payload.get("classification") == "replayable", ok_payload
    for case in (
        "clean_input",
        "source_delta",
        "config_delta",
        "dependency_delta",
        "parallel_overlay",
        "stale_seed",
    ):
        assert ok_payload.get("cases", {}).get(case) == "pass", (
            f"conformance 항목 {case}가 통과로 기록되지 않았다: {ok_payload.get('cases')}"
        )

    bad_payload = parse_json_stdout(
        run_oppb(["cache", "conformance", "--cache-root", cache_root, "--adapter", str(bad)]),
        "cache conformance(opaque)",
    )
    assert bad_payload.get("classification") == "non_reusable", (
        f"입력 변경을 검출하지 못한 adapter가 강등되지 않았다: {bad_payload}"
    )
    assert bad_payload.get("evidence_path"), f"conformance evidence가 없다: {bad_payload}"


def test_s14_2_non_reusable_adapter_forces_cold_only_for_its_command(cache_env):
    """[T132/S-14] `non_reusable` 강등은 **해당 명령만** cold 실행시킨다. 다른 명령의
    warm 재사용까지 일괄 폐기하지 않는다(제안서 §4.5 "adapter가 선언한 영향 shard만 무효화")."""
    cache_root, tmp = cache_env["cache_root"], cache_env["tmp"]
    good = install_adapter(tmp, "adapter_replayable", REPLAYABLE_ADAPTER)
    bad = install_adapter(tmp, "adapter_opaque", OPAQUE_ADAPTER)
    for adapter in (good, bad):
        run_oppb(["cache", "conformance", "--cache-root", cache_root, "--adapter", str(adapter)])

    cold = parse_json_stdout(
        run_oppb(
            [
                "cache",
                "plan-execution",
                "--cache-root",
                cache_root,
                "--command",
                "build-opaque",
                "--adapter",
                str(bad),
            ]
        ),
        "cache plan-execution(opaque)",
    )
    assert cold.get("execution") == "cold", cold
    assert cold.get("reason") == "non_reusable", cold

    warm_capable = parse_json_stdout(
        run_oppb(
            [
                "cache",
                "plan-execution",
                "--cache-root",
                cache_root,
                "--command",
                "build-good",
                "--adapter",
                str(good),
            ]
        ),
        "cache plan-execution(replayable)",
    )
    assert warm_capable.get("execution") != "cold", (
        f"무관한 명령까지 cold로 강등됐다: {warm_capable}"
    )


def test_s14_3_both_sibling_overlays_survive_first_publication(cache_env):
    """[T132/S-14] 같은 parent에서 fork한 병렬 candidate 2개가 모두 검증을 통과하면
    승자 하나만 남기지 않는다 — 각 overlay를 immutable CAS node로 **모두** 보존한다
    (제안서 §4.5, 수용기준 29 전반부)."""
    cache_root, repo, tmp = cache_env["cache_root"], cache_env["repo"], cache_env["tmp"]
    adapter = install_adapter(tmp, "adapter_replayable", REPLAYABLE_ADAPTER)
    parent = run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()

    sealed = {}
    for candidate in ("cand-A", "cand-B"):
        forked = parse_json_stdout(
            run_oppb(
                [
                    "cache",
                    "overlay-fork",
                    "--cache-root",
                    cache_root,
                    "--parent",
                    parent,
                    "--candidate",
                    candidate,
                    "--adapter",
                    str(adapter),
                    "--source-root",
                    str(repo),
                ]
            ),
            f"cache overlay-fork({candidate})",
        )
        assert forked.get("ok") is True, forked
        assert forked.get("overlay_path"), forked

        node = parse_json_stdout(
            run_oppb(
                [
                    "cache",
                    "seal",
                    "--cache-root",
                    cache_root,
                    "--candidate",
                    candidate,
                    "--verification",
                    "pass",
                ]
            ),
            f"cache seal({candidate})",
        )
        assert node.get("ok") is True, node
        sealed[candidate] = node["node_id"]

    assert sealed["cand-A"] != sealed["cand-B"], "두 overlay가 같은 CAS node로 합쳐졌다."

    published = parse_json_stdout(
        run_oppb(
            ["cache", "record-publication", "--cache-root", cache_root, "--candidate", "cand-A"]
        ),
        "cache record-publication",
    )
    assert published.get("ok") is True, published

    remaining = node_ids(cache_root)
    assert sealed["cand-A"] in remaining, "publication된 overlay가 CAS에서 사라졌다."
    assert sealed["cand-B"] in remaining, (
        "첫 publication 후 stale sibling overlay가 폐기됐다 — 두 overlay 모두 CAS에 남아야 한다."
    )

    head_set = parse_json_stdout(
        run_oppb(["cache", "head-set", "--cache-root", cache_root]), "cache head-set"
    )
    assert set(head_set.get("head_set", [])) >= set(sealed.values()), (
        f"accepted head가 재사용 가능한 cache DAG head set을 기록하지 않았다: {head_set}"
    )


def test_s14_4_stale_sibling_replays_deterministic_seed_without_cold_fallback(cache_env):
    """[T132/S-14] stale sibling을 새 head에 다시 올릴 때 input 일치가 가장 크고 적용할
    Git delta가 가장 작은 seed를 **결정론적으로** 선택하고, intervening accepted source
    delta를 replay한다 — cold fallback 0(수용기준 29 후반부)."""
    cache_root, repo, tmp = cache_env["cache_root"], cache_env["repo"], cache_env["tmp"]
    adapter = install_adapter(tmp, "adapter_replayable", REPLAYABLE_ADAPTER)
    parent = run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()

    for candidate in ("cand-A", "cand-B"):
        run_oppb(
            [
                "cache",
                "overlay-fork",
                "--cache-root",
                cache_root,
                "--parent",
                parent,
                "--candidate",
                candidate,
                "--adapter",
                str(adapter),
                "--source-root",
                str(repo),
            ]
        )
        run_oppb(
            [
                "cache",
                "seal",
                "--cache-root",
                cache_root,
                "--candidate",
                candidate,
                "--verification",
                "pass",
            ]
        )
    run_oppb(["cache", "record-publication", "--cache-root", cache_root, "--candidate", "cand-A"])

    # cand-A가 publication되어 project head가 전진한다 — cand-B에게는 intervening delta다.
    _write(repo, "src/a.py", "A = 2\n")
    run_git(["add", "-A"], cwd=repo)
    run_git(["commit", "-m", "accept cand-A"], cwd=repo)
    new_head = run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()

    def reseed() -> dict:
        return parse_json_stdout(
            run_oppb(
                [
                    "cache",
                    "reseed",
                    "--cache-root",
                    cache_root,
                    "--candidate",
                    "cand-B",
                    "--new-head",
                    new_head,
                    "--source-root",
                    str(repo),
                    "--adapter",
                    str(adapter),
                ]
            ),
            "cache reseed(cand-B)",
        )

    first = reseed()
    assert first.get("ok") is True, f"stale sibling 복구 실패: {first}"
    assert first.get("cold_fallback") is False, (
        f"replayable adapter인데 cold fallback이 발생했다: {first}"
    )
    assert first.get("replayed_delta"), f"intervening delta replay 기록이 없다: {first}"
    assert first.get("seed_node"), first
    assert first.get("byte_merged") is False, (
        "cache 파일끼리 byte merge는 금지다(제안서 §4.5)."
    )

    second = reseed()
    assert second.get("seed_node") == first.get("seed_node"), (
        f"seed 선택이 결정론적이지 않다: {first.get('seed_node')} vs {second.get('seed_node')}"
    )


def test_s14_5_exact_hit_requires_all_three_manifest_hashes(cache_env):
    """[T132/S-14] 무실행 exact cache hit는 source·dependency·build manifest hash가 **모두**
    일치할 때만 허용한다. 하나라도 다르면 replay 또는 cold다(제안서 §4.5)."""
    cache_root, repo, tmp = cache_env["cache_root"], cache_env["repo"], cache_env["tmp"]
    adapter = install_adapter(tmp, "adapter_replayable", REPLAYABLE_ADAPTER)
    parent = run_git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
    run_oppb(
        [
            "cache",
            "overlay-fork",
            "--cache-root",
            cache_root,
            "--parent",
            parent,
            "--candidate",
            "cand-A",
            "--adapter",
            str(adapter),
            "--source-root",
            str(repo),
        ]
    )
    run_oppb(
        ["cache", "seal", "--cache-root", cache_root, "--candidate", "cand-A", "--verification", "pass"]
    )

    same = parse_json_stdout(
        run_oppb(
            [
                "cache",
                "lookup",
                "--cache-root",
                cache_root,
                "--source-root",
                str(repo),
                "--adapter",
                str(adapter),
            ]
        ),
        "cache lookup(identical)",
    )
    assert same.get("hit") == "exact", same

    _write(repo, "lockfile.lock", "dep-a==2.0.0\n")
    changed = parse_json_stdout(
        run_oppb(
            [
                "cache",
                "lookup",
                "--cache-root",
                cache_root,
                "--source-root",
                str(repo),
                "--adapter",
                str(adapter),
            ]
        ),
        "cache lookup(dependency changed)",
    )
    assert changed.get("hit") != "exact", (
        f"dependency manifest가 달라졌는데 무실행 exact hit가 났다: {changed}"
    )


# ═════════════════════════════════════════════════════════════════════════════
# S-15: 용량 관리 — pin·LRU·cacheless 강등·disk_budget_exceeded (수용기준 33)
# ═════════════════════════════════════════════════════════════════════════════


def seed_capacity_fixture(cache_env) -> dict:
    """작은 soft cap·최소 여유와 인위적으로 앞당긴 retention 만료를 가진 cache root.

    pin 대상 3종(active run·실행 중 candidate·publication 대기)과 closed node 3개를
    서로 다른 last-access 시각으로 실제 생성한다."""
    cache_root = cache_env["cache_root"]
    policy = write_json(
        cache_env["tmp"] / "cache_policy.json",
        {
            "soft_cap_bytes": 4096,
            "min_free_bytes": 1024,
            "warm_retention_days": 0,
        },
    )
    applied = parse_json_stdout(
        run_oppb(["cache", "set-policy", "--cache-root", cache_root, "--policy", str(policy)]),
        "cache set-policy",
    )
    assert applied.get("ok") is True, applied

    created = {}
    seeds = [
        ("node-active", "active_run", "2026-09-01T00:00:00Z"),
        ("node-running", "running_candidate", "2026-09-01T00:00:00Z"),
        ("node-pending", "publication_pending", "2026-09-01T00:00:00Z"),
        ("node-closed-old", "closed", "2026-01-01T00:00:00Z"),
        ("node-closed-mid", "closed", "2026-05-01T00:00:00Z"),
        ("node-closed-new", "closed", "2026-09-10T00:00:00Z"),
    ]
    for name, state, last_access in seeds:
        payload = parse_json_stdout(
            run_oppb(
                [
                    "cache",
                    "put-node",
                    "--cache-root",
                    cache_root,
                    "--node",
                    name,
                    "--state",
                    state,
                    "--last-access",
                    last_access,
                    "--size-bytes",
                    "2048",
                ]
            ),
            f"cache put-node({name})",
        )
        assert payload.get("ok") is True, payload
        created[name] = payload["node_id"]
    return created


def test_s15_1_gc_never_deletes_pinned_nodes(cache_env):
    """[T132/S-15] active run·실행 중 candidate·publication 대기 node는 lease로 pin되어
    **삭제 0**이다. closed node만 회수 대상이다(수용기준 33, 제안서 §4.5)."""
    cache_root = cache_env["cache_root"]
    created = seed_capacity_fixture(cache_env)

    payload = parse_json_stdout(
        run_oppb(["cache", "gc", "--cache-root", cache_root]), "cache gc"
    )
    assert payload.get("ok") is True, payload

    evicted = set(payload.get("evicted", []))
    surviving = node_ids(cache_root)
    for name in ("node-active", "node-running", "node-pending"):
        assert created[name] not in evicted, f"pin된 node가 회수됐다: {name}"
        assert created[name] in surviving, f"pin된 node가 삭제됐다: {name}"
    assert evicted, "cap을 넘겼는데 회수가 전혀 일어나지 않았다."
    for node in cache_nodes(cache_root):
        if node["node_id"] in evicted:
            pytest.fail(f"회수 보고된 node가 여전히 존재한다: {node}")


def test_s15_2_closed_nodes_are_reclaimed_in_last_access_lru_order(cache_env):
    """[T132/S-15] closed node는 warm retention 만료 뒤 last-access receipt 기준 LRU로
    제거된다 — 오래된 것부터다."""
    cache_root = cache_env["cache_root"]
    created = seed_capacity_fixture(cache_env)

    payload = parse_json_stdout(
        run_oppb(["cache", "gc", "--cache-root", cache_root]), "cache gc(LRU)"
    )
    evicted = payload.get("evicted", [])
    assert evicted, payload

    order = [created["node-closed-old"], created["node-closed-mid"], created["node-closed-new"]]
    evicted_rank = [order.index(node) for node in evicted if node in order]
    assert evicted_rank == sorted(evicted_rank), (
        f"closed node 회수가 last-access LRU 순서가 아니다: {evicted}"
    )
    assert created["node-closed-old"] in evicted, (
        f"가장 오래 미접근한 closed node가 회수되지 않았다: {evicted}"
    )


def test_s15_3_gc_does_not_touch_done_or_evidence(cache_env):
    """[T132/S-15] evidence·DONE·source code는 cache GC 대상이 아니다 — GC 전후 불변이다."""
    cache_root, run_root = cache_env["cache_root"], cache_env["run_root"]
    seed_capacity_fixture(cache_env)

    evidence_path = write_json(
        pathlib.Path(run_root) / "evidence" / "project" / "ev-0001.json",
        {"evidence_id": "ev-0001", "verdict": "pass"},
    )
    done_path = cache_env["repo"] / "DONE.md"
    done_path.write_text("# DONE\ncache object hash manifest\n", encoding="utf-8")
    before = (sha256_file(evidence_path), sha256_file(done_path))

    assert parse_json_stdout(
        run_oppb(["cache", "gc", "--cache-root", cache_root]), "cache gc(evidence)"
    ).get("ok") is True

    assert evidence_path.exists(), "GC가 evidence를 삭제했다."
    assert done_path.exists(), "GC가 DONE을 삭제했다."
    assert (sha256_file(evidence_path), sha256_file(done_path)) == before, (
        "GC가 DONE·evidence 내용을 바꿨다."
    )


def test_s15_4_insufficient_space_degrades_to_cacheless_or_blocks(cache_env):
    """[T132/S-15] pin되지 않은 node를 모두 제거해도 최소 여유 공간을 확보하지 못하면
    warm cache를 끈 격리 실행으로 강등하고, 그 실행 공간도 없으면 `disk_budget_exceeded`로
    구조화 blocked한다(제안서 §4.5, 수용기준 33)."""
    cache_root = cache_env["cache_root"]
    seed_capacity_fixture(cache_env)
    impossible = write_json(
        cache_env["tmp"] / "impossible_policy.json",
        {
            "soft_cap_bytes": 1,
            "min_free_bytes": 1 << 62,  # 어떤 파일시스템에서도 확보 불가능
            "warm_retention_days": 0,
        },
    )
    run_oppb(["cache", "set-policy", "--cache-root", cache_root, "--policy", str(impossible)])

    payload = parse_json_stdout(
        run_oppb(["cache", "gc", "--cache-root", cache_root]), "cache gc(공간 부족)"
    )

    if payload.get("ok") is True:
        assert payload.get("degraded") == "cacheless", (
            f"공간 부족인데 cacheless 강등도 blocked도 아니다: {payload}"
        )
    else:
        assert payload.get("error") == "disk_budget_exceeded", payload
        assert payload.get("blocked") is True, payload

    # 어느 경로든 pin된 node는 여전히 삭제되지 않는다.
    surviving_states = {node["node_id"]: node.get("state") for node in cache_nodes(cache_root)}
    for state in PINNED_STATES:
        assert state in surviving_states.values(), (
            f"공간 부족 처리에서 pin 상태 {state} node가 삭제됐다: {surviving_states}"
        )
