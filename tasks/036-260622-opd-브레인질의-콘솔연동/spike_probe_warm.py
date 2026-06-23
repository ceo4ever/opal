"""S-4 후속: warm(resume) 지연 + 프라임/질의 분리 정제 측정.

1) 콜드 프라임: 세션 새로 생성(session_id=None) → t_cold, session_id, 출력
2) 웜 재개: 같은 session_id로 --resume → t_warm, 출력
비교: 웜 지연이 수용 가능한가(B1 타당성) / 웜 출력에 부트스트랩 보고가 사라지는가(프라임/질의 분리 효과).

실행:
  cd /Volumes/Data/AIStudio/workspace/ai-framework
  ~/.opal/.venv/bin/python3 tasks/036-260622-opd-브레인질의-콘솔연동/spike_probe_warm.py
"""
import os
import sys
import time
from pathlib import Path

ROOT = Path("/Volumes/Data/AIStudio/workspace/ai-framework")
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))


def has_bootstrap_noise(text: str) -> bool:
    return "[부트스트랩]" in text or "알투[PM]" in text


def main() -> None:
    from dashboard.backend.adapters.opbr_adapter import prime_and_ask

    project = str(ROOT)
    q1 = "OPAL 첫 사용 순서는?"
    q2 = "그럼 //opi 단계에서 무엇이 생성되나?"

    # 1) 콜드 프라임
    print("[cold] 프라임 질의 실행 중... (~수십초)")
    t0 = time.time()
    r1 = prime_and_ask(q1, project, session_id=None)
    t_cold = time.time() - t0
    sid = r1.get("session_id")
    a1 = r1.get("answer", "")
    print(f"[cold] {t_cold:.1f}s  session_id={sid}  부트스트랩노이즈={has_bootstrap_noise(a1)}  답변길이={len(a1)}")

    if not sid:
        print("[warn] session_id 없음 → resume 불가, warm 측정 중단")
        return

    # 2) 웜 재개 (같은 세션)
    print("[warm] resume 질의 실행 중...")
    t0 = time.time()
    r2 = prime_and_ask(q2, project, session_id=sid)
    t_warm = time.time() - t0
    a2 = r2.get("answer", "")
    print(f"[warm] {t_warm:.1f}s  부트스트랩노이즈={has_bootstrap_noise(a2)}  답변길이={len(a2)}")

    print("=" * 60)
    print(f"콜드 {t_cold:.1f}s → 웜 {t_warm:.1f}s  (웜 단축률 {100*(1-t_warm/t_cold):.0f}%)" if t_cold else "")
    print(f"웜 출력 부트스트랩 제거: {'예(프라임/질의 분리 유효)' if not has_bootstrap_noise(a2) else '아니오(여전히 혼입)'}")
    print("--- warm 답변 미리보기 ---")
    print(a2[:800])


if __name__ == "__main__":
    main()
