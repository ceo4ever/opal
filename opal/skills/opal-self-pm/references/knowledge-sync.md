<!--
@header {
  "module": "opal-self-pm-knowledge-sync",
  "layer": "reference",
  "domain": "opal-pipeline",
  "description": "opal-self-pm 루프 완료 직전 기획·설계·프로젝트 문서·CONVENTIONS·SECURITY·brain·memory·code-scan 8영역을 update 또는 no-op + 근거로 무근거 생략 없이 판정하는 절차와 기록 형식을 규정한다.",
  "exports": ["8영역 판정 표", "기록 형식", "중복 기록 금지"]
}
-->

# knowledge-sync — 완료 직전 8영역 판정

> 소유: `opal-self-pm/SKILL.md` §7.

**[MUST] 무근거 생략 금지** — 8영역 전부를 판정한다. "관련 없어 보임"만으로 항목을 건너뛰지 않는다. 영향이 있으면 `update`, 없으면 반드시 근거를 댄 `no-op + 근거`로 닫는다. 판정되지 않은 영역이 하나라도 남아 있으면 §8 사용자 최종 확인으로 넘어가지 않는다(`opal-self-pm/SKILL.md` §7).

## 8영역 판정 표

| # | 영역 | owner 문서/도구 | 판정 방법 |
|---|---|---|---|
| 1 | 기획 | 프로젝트 기획서·정책서·사용자 흐름 문서(`docs/PROJECT.md` 문서 레지스트리로 소재 확인) | 이번 변경이 현재 요구·정책·흐름 서술과 어긋나거나 새 결정을 반영해야 하면 `update`. 대상 문서 없음/무관하면 근거와 함께 `no-op` |
| 2 | 설계 | 아키텍처·인터페이스·데이터 모델 문서(`docs/ARCHITECTURE.md` 등, 프로젝트 문서 레지스트리 기준) | 구조·인터페이스·데이터 모델이 바뀌었으면 `update`. 순수 구현 세부만 바뀌었으면 근거와 함께 `no-op` |
| 3 | 프로젝트 문서 | `docs/PROJECT.md`(컴포넌트·문서 레지스트리·폴더 구조맵) | 신규 컴포넌트·문서·경로가 생겼으면 `update`. 기존 등재로 충분하면 근거와 함께 `no-op` |
| 4 | CONVENTIONS | `docs/CONVENTIONS.md`(허브+링크 모델 — `opal/core/references/conventions-hub-model.md` 규약) | 새 컨벤션 패턴을 만들었거나 기존 규칙을 벗어난 예외를 승인받았으면 `update`. 기존 규칙 그대로 따랐으면 근거와 함께 `no-op` |
| 5 | SECURITY | `docs/SECURITY.md`(부재 시 `op-gc-security` §2 기준 선택 순서의 T1 baseline로 검사만 수행) | 보안 기준·위협 모델에 영향을 준 변경이면 `update`. 영향 없으면 근거와 함께 `no-op`(문서 부재 자체는 실패 아님 — `op-gc-security` §7 [MUST] 3 참조) |
| 6 | brain | `.opal/brain/`(`brain-tool` — 결정 이유·채택/폐기 근거) | `.opal/brain/` 존재 시: 이번 결정이 향후 참조할 WHY를 담고 있으면 `~/.opal/tools/brain-tool/run.sh add-page`로 `update`. `.opal/brain/` 미초기화면 근거("brain 미초기화")와 함께 `no-op` |
| 7 | memory | 프로젝트 memory(`memory-tool` — 다음 세션 주의사항·후속) | 다음 세션이 알아야 할 주의사항·후속 작업이 있으면 `~/.opal/tools/memory-tool/run.sh append`로 `update`. 없으면 근거와 함께 `no-op` |
| 8 | code-scan | `code-scan`(코드 구조·exports·depends 원천) | `changed_files` 중 code-scan 적용 확장자가 있으면 @header 갱신 여부를 `code-scan validate --changed`로 확인(`header-rules.md` §갱신 시점 (4단) (d) 포인터 — `opal-self-pm/SKILL.md` §5 완료 게이트와 동일 실행). 적용 대상 없으면 근거와 함께 `no-op` |

## 기록 형식

각 영역 판정은 `self-pm-tool`의 `knowledge_impact` 필드에 아래 형식 문자열로 append한다(`opal-self-pm/SKILL.md` §7 명령 참조).

```
<영역명>: update - <무엇을 갱신했는지 1줄>
<영역명>: no-op - <근거 1줄>
```

예:
```
기획: no-op - 이번 변경은 기존 정책 범위 내 구현 세부이며 정책 문서 서술과 불일치 없음
brain: update - pages/concept/self-pm-tool.md 신규 등록 (add-page 완료)
```

## 중복 기록 금지

각 owner 문서·도구에 현재 사실만 반영한다. 이미 다른 영역에서 기록한 내용을 다른 영역에 다시 옮겨 적지 않는다 — 예: brain에 남긴 WHY를 프로젝트 문서에 다시 쓰지 않는다(각 owner는 제안서 §6.5의 정보 유형 표대로 단일 책임을 갖는다).
