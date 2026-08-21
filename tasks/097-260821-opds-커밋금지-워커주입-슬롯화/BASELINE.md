# BASELINE / RED 증거 — 097

> 취득: 2026-08-21 15:16 KST | 목적: EXECUTE 전 판정식이 실제로 FAIL함을 확인(사후 자기확인 방지)

| 판정식 | 기대(개정 후) | 현재값 | RED |
|--------|--------------|--------|-----|
| `grep -c '← 전 워커 공통 고정' pm/dispatch-process.md` | 3 | 2 | FAIL 확인 |
| dispatch-process 규범구간(81-180) `공통 고정 2항목` | 0 | 1 | FAIL 확인 |
| dispatch-process `공통 고정 3항목` | >=1 | 0 | FAIL 확인 |
| op-dev-execute 절대금지 표 데이터 행 | 7 | 6 | FAIL 확인 |
| op-dev-execute `공통 고정 2항목` (원격 카운트) | 0 | 1 | FAIL 확인 |
| 파일럿 `pm/dispatch-process.md` 참조 보유 파일 수 | 10 | 0 | FAIL 확인 |
| 파일럿 열거형 `1. 하네스 Guards 핵심 규칙` 잔존 | 0 | 3 | FAIL 확인 |
| CONVENTIONS 커밋 금지 원문 (2곳) | 0 | 2 | FAIL 확인 |
| PROJECT.md 레지스트리 `구현 규칙(Guards/` | 0 | 1 | FAIL 확인 |

> **판정식 정정 1건**: 최초 취득 시 정규식을 `사용자이\|캡틴이`로 잘못 써 1건만 잡혔다. 조사 교정(`사용자가\|캡틴이`) 후 `:188`·`:203` 2건이 정상 검출된다 — PLAN H-7의 2곳 주장과 일치. EXECUTE 워커는 교정된 판정식을 사용한다.

## 불변 대상 baseline (부정 검증용)

```
HEAD                = f3dd43d0c41d2b5840c3a074623f46b63513c065
harness §1 shasum   = 4b3041449a6511b2353478d2a8a82b4ce096c623
배포본 dispatch      = 9ea6073794065e851dc1252fe7e6f835b051b023
배포본 op-dev-exec   = a25f66ec5580919b4ddb7284e164f91905d7e113
gc:219 리터럴        = 1건
파일럿 「핵심 제약」 보유 = 5/10
```
