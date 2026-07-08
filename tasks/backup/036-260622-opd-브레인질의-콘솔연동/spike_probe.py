"""S-4 스파이크 실 구독 E2E probe.

POST /api/brain/query 1건을 TestClient(인프로세스)로 실행한다.
실제 `claude -p "//opbr ask ..."`가 떠서 캡틴 Claude 구독으로 합성한다(콜드: OPAL 부트스트랩 로딩으로 수십초 소요 가능).

측정: ①답변 ②콜드 지연 ③.opal/brain 변경 파일(read-only 검증) ④구독 작동(API키 없이) ⑤opbr 로딩 정황.

실행:
  cd /Volumes/Data/AIStudio/workspace/ai-framework
  python3 tasks/036-260622-opd-브레인질의-콘솔연동/spike_probe.py
  # 질문 바꾸려면:  python3 .../spike_probe.py "원하는 질문"
"""
import hashlib
import os
import sys
import time
from pathlib import Path

ROOT = Path("/Volumes/Data/AIStudio/workspace/ai-framework")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

BRAIN = ROOT / ".opal" / "brain"


def manifest() -> dict[str, str]:
    """.opal/brain 하위 모든 파일의 {상대경로: sha256} — 변경 탐지용."""
    out: dict[str, str] = {}
    for p in sorted(BRAIN.rglob("*")):
        if p.is_file():
            out[p.relative_to(BRAIN).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main() -> None:
    from fastapi.testclient import TestClient

    from dashboard.backend.main import app

    client = TestClient(app)

    print("=" * 60)
    # 0) 인증 상태
    auth = client.get("/api/brain/auth")
    print("[auth ]", auth.status_code, auth.json())

    # 1) brain 변경 전 스냅샷
    before = manifest()
    print(f"[brain] 질의 전 파일 {len(before)}개 스냅샷")

    # 2) 실제 질의 (구독 토큰 소모, OPAL 로딩으로 콜드 수십초 가능)
    question = sys.argv[1] if len(sys.argv) > 1 else "OPAL 첫 사용 순서는?"
    print(f"[query] {question!r}")
    print("        실행 중... (콜드: OPAL 부트스트랩+opbr 로딩으로 수십초 걸릴 수 있음)")
    t0 = time.time()
    resp = client.post("/api/brain/query", json={"question": question, "project": str(ROOT)})
    elapsed = time.time() - t0

    # 3) 결과
    print("=" * 60)
    print(f"[status ] {resp.status_code}   [elapsed] {elapsed:.1f}s")
    try:
        data = resp.json()
        ans = data.get("answer", "")
        print("[session] ", data.get("session_id"))
        print("[answer ]\n" + (ans[:1500] if ans else "(빈 답변)"))
    except Exception as e:  # noqa: BLE001
        print("[parse error]", e)
        print(resp.text[:800])

    # 4) read-only 검증 — 변경 파일 목록
    after = manifest()
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(k for k in before if k in after and before[k] != after[k])
    print("=" * 60)
    if not (added or removed or modified):
        print("[read-only] ✅ PASS — .opal/brain 변경 0건")
    else:
        print("[read-only] ⚠️ 변경 감지:")
        for k in added:
            print(f"   + 추가: {k}")
        for k in modified:
            print(f"   ~ 수정: {k}")
        for k in removed:
            print(f"   - 삭제: {k}")
        print("   (log.md만이면 query 로깅 — 정책 판단 필요 / pages 변경이면 쓰기 누수)")
    print("=" * 60)
    print("판단 포인트: 답변이 brain 근거인가 / 콜드 지연 수용 가능한가 / 변경이 log.md뿐인가")


if __name__ == "__main__":
    main()
