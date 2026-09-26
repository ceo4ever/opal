# opal-skill-tester

OPAL 스킬(주로 Pilot)을 모의 프로젝트로 실제 실행해 보고, 표준 지표로 합격 여부와 기준 대비 추세를 판정하는 스킬입니다.

## 개요

단위 테스트를 모두 통과해도 실제 실행에서만 드러나는 결함이 있습니다. 이 스킬은 스킬 안의 `scenarios/`에 있는 모의 프로젝트와 요구서로 격리된 저장소를 만들고, 헤드리스 세션으로 Pilot을 끝까지 돌립니다. 결과는 세션에 보여주지 않은 숨은 인수 테스트와 지표로 채점합니다.

## 트리거

- "스킬 테스트", "모의 태스크로 테스트", "파일럿 테스트 돌려줘"
- "opd랑 opd --no-pm 비교"
- "스킬 수정 후 회귀 확인"
- "시나리오 추가"

## 사용법

```bash
T=~/.opal/skills/opal-skill-tester/scripts/skill_tester.py
python3 $T list                                   # 시나리오 목록
python3 $T validate --all                         # 시나리오 규격 검사
python3 $T run smoke-version-flag                 # 단일 실행(기본 변형)
python3 $T run function-stockctl-multiloc \
  --variant "//opd --no-pm" --variant "//opd" --repeat 2   # 비교 실행
python3 $T report /tmp/opal-skill-tester/<실행폴더>        # 보고서 재생성
```

실행 1회가 실제 Pilot 세션이라 시간과 비용이 듭니다. 기능 시나리오 기준 약 20~35분, $10~15입니다.

## 테스트 모드

| 모드 | 검증 질문 |
|---|---|
| 스모크 | 파이프라인이 끝까지 규칙대로 도는가 |
| 기능 | 명세대로 제대로 만드는가 |
| 판단 | 모호·충돌 요구를 사용자 결정으로 올리는가 |

## 구성

| 경로 | 내용 |
|---|---|
| `SKILL.md` | 실행 절차와 판정 규칙 |
| `references/metrics.md` | Pilot 측정 지표 기준 |
| `references/scenario-spec.md` | 시나리오 규격과 추가 방법 |
| `scripts/skill_tester.py` | 실행기 |
| `scenarios/` | 시나리오 카탈로그와 공유 기반 저장소(`_bases/`) |
