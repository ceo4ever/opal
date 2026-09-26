# 시나리오 규격

시나리오 하나는 `scenarios/<id>/` 폴더 하나다. `id`는 `<mode>-<짧은-이름>` kebab-case로 짓는다(예: `function-stockctl-multiloc`). 규격은 `skill_tester.py validate <id>`가 검사한다.

## 폴더 구성

```
scenarios/<id>/
├── scenario.json       메타(필수)
├── request.md          세션에 줄 요구서(필수)
├── hidden/             숨은 인수 테스트(function 필수, 그 외 선택)
│   └── test_hidden.py
└── overlay/            기반 저장소 위에 덮어쓸 파일(선택)
```

기반 저장소는 `scenarios/_bases/<name>/`에 두고 여러 시나리오가 공유한다. 기반 저장소는 OPAL 프로젝트 자산을 모두 가져야 세션이 설정 누락으로 멈추지 않는다: `.opal/AGENT.md`, `.opal/code-scan.json`, `.opal/MEMORY.json`(`memory-tool init`), `.opal/worktree.json`(worktree 기본 Pilot용), `docs/PROJECT.md`, `.gitignore`(`.opal-worktrees/` 포함).

## scenario.json

```json
{
  "id": "function-stockctl-multiloc",
  "mode": "function",
  "title": "다중 위치 재고·이동·감사·가져오기·충돌 감지",
  "base": "_bases/stockctl",
  "target_pilots": ["opd", "opds"],
  "default_variant": "//opd",
  "utterance": "{variant} 요구서 {request} 대로 수행한다. 요구서의 요구를 TASK 요구사항으로 그대로 사용한다.",
  "existing_test_cmd": ["python3", "-m", "pytest", "-q", "tests"],
  "timeout_min": 90,
  "estimate": {"minutes": 30, "usd": 12},
  "decision_points": []
}
```

| 필드 | 필수 | 규칙 |
|---|---|---|
| `id` | O | 폴더명과 같다 |
| `mode` | O | `smoke` / `function` / `judgment` |
| `base` | O | `scenarios/` 기준 상대경로. 폴더가 존재해야 한다 |
| `target_pilots` | O | 시험 대상 Pilot 약어 목록. `run`은 변형의 커맨드가 이 목록 밖이면 `variant_not_targeted`로 거부한다 |
| `default_variant` | O | 단일 실행 때 쓰는 커맨드 접두(예: `//opd`, `//opds --no-pm`). 기본이 semi-agentic인 Pilot은 헤드리스 세션이 사용자 게이트에서 멈추므로 `--agentic`을 붙인다(예: `//opsdd --agentic`) |
| `utterance` | O | `{variant}`·`{request}` 토큰을 모두 포함 |
| `existing_test_cmd` | function O | 작업본에서 실행할 기존 테스트 argv |
| `timeout_min` | O | 초과 시 세션을 종료하고 `timeout`으로 기록 |
| `estimate` | O | 실행 1회의 예상 분·달러. 비용 안내에 쓴다 |
| `decision_points` | judgment O | 아래 절 |

OPPB는 workspace가 항상 project worktree이며 `--no-wt`를 허용하지 않는다. 헤드리스 시나리오가
P1 INTENT gate와 P5 local merge gate를 끝까지 실행해야 하면 `utterance`에 격리 저장소에
한정한 명시적 승인을 포함한다. 이 승인은 모의 저장소 밖 merge·push·배포로 확장되지 않는다.

## 요구서 작성

- 세션은 요구서만 보고 TASK를 쓴다. 채점할 계약(명령·출력·종료 코드·파일 형식)은 요구서에 적는다. 숨은 테스트가 요구서에 없는 세부를 채점하면 시나리오 결함이다.
- function 모드는 명세를 완전하게 쓴다. 설계 판단의 질을 보려면 judgment 모드로 만든다.
- 숨은 테스트 경로·파일명을 요구서에 쓰지 않는다.

## 숨은 테스트 작성

- `SUT_REPO` 환경변수(코드 작업본 절대경로)만으로 대상 코드를 찾는다. 실행 cwd도 작업본이다.
- 공개 인터페이스(CLI 출력·종료 코드·저장 파일)만 검증한다.
- 기반 저장소 원본에서 먼저 실행해 기능 테스트가 실패하는지 확인한다. 원본에서 이미 통과하는 테스트는 요구 기능을 가려내지 못한다(기존 동작 유지 검사는 예외).

## judgment 모드의 결정 지점

요구서에 의도적으로 모호하거나 서로 충돌하는 요구를 넣고, 세션이 반드시 사용자에게 물어야 하는 지점을 적는다.

```json
"decision_points": [
  {"id": "D-1", "summary": "재고 부족 차감을 거부할지 음수로 허용할지", "keywords": ["음수", "부족", "차감"]}
]
```

- 결정 지점은 외부 영향 결정(사용자·계약·저장 방식에 보이는 것)이어야 한다. 구현 세부는 세션이 스스로 정해도 정상이다.
- `keywords`는 결정을 요청하는 문장에 자연스럽게 나올 단어 2~4개로 둔다.

## 비교 기준

별도 기준 파일은 두지 않는다. 추세 비교는 `tasks/`·`tasks/backup/`에 쌓인 같은 변형·시나리오 기록(`record.json`+`metrics.json`)의 최근 3회 중앙값을 쓴다. 스킬을 의도적으로 바꿨는지는 이력 표의 프레임워크 지문(설치 VERSION+state-tool·Pilot SKILL.md 해시)으로 구분한다.
