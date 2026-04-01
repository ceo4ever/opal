# QA: PLAN -- Claude Code Hooks 알림 설정 및 install-mac.sh 배포

> 검토일: 2026-03-20 | 판정: ⚠️ Needs Revision

## 1. 요약

Claude Code의 hooks 시스템(SubagentStop, Stop)을 활용하여 장시간 작업 완료 시 macOS 네이티브 알림을 보내는 기능을 구현하는 Short Task PLAN이다. hooks 설정 소스 파일(`opal/core/hooks/claude-hooks.json`)을 신규 생성하고, `install-mac.sh`에 `merge_hooks_config()` 함수를 추가하여 `~/.claude/settings.json`에 머지하는 방식이다. 기존 `merge_mcp_config()` 패턴을 재활용하며, 변경 파일은 2개(신규 JSON 1개 + 스크립트 수정 1개)로 범위가 명확하다.

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| SP-1 | 코드 분석 충분성 | ✅ | `install-mac.sh`의 `merge_mcp_config()`(99-129행), `install_claude()`(230-239행), `install_mcp()`(315-405행), `main()`(554-612행)을 실제 라인 번호와 함께 분석. 실제 코드와 대조 결과 정확함. 영향 범위(호출 관계, 공유 데이터)도 식별됨. |
| SP-2 | 구현 계획 구체성 | ⚠️ | hooks JSON 구조와 `merge_hooks_config()` 함수 코드가 구체적으로 제시됨. 단, hooks JSON 구조에 문제가 있음 (지적 사항 참조). |
| SP-3 | 체크리스트 완전성 | ✅ | TASK.md 요구사항 4개(hooks 설정 파일 추가, SubagentStop 알림, install-mac.sh 머지, 기존 설정 보존)가 Step 1-3으로 빠짐없이 분해됨. |
| SP-4 | QA 항목 커버리지 | ✅ | 기능 테스트(JSON 유효성, 빈/기존 settings 머지), 회귀 테스트(기존 기능 보존, 전체 설치 경로), 코드 품질(스타일 일관성, python3 체크, 경로 누락 처리)까지 포괄적. |
| SP-5 | Short Task 적정성 | ✅ | 변경 파일 2개, 기존 패턴 재활용, 명확한 범위. Short Task로 적합. |

## 3. 지적 사항

### 🔴 Critical

**[C-1] hooks JSON 구조가 공식 스펙과 불일치**

PLAN의 `claude-hooks.json`에서 각 이벤트 배열 요소에 `"matcher"` 필드가 포함되어 있으나, 공식 문서상 `matcher`는 `PreToolUse`, `PostToolUse` 등 tool 관련 이벤트에서만 사용된다. `SubagentStop`과 `Stop` 이벤트에서도 `matcher`를 지정하는 것이 동작에 영향을 주지 않을 수 있으나, 더 중요한 문제는 **소스 파일의 JSON 구조와 settings.json의 hooks 구조가 이중 래핑**되어 있다는 점이다.

PLAN의 소스 파일 구조:
```json
{
  "hooks": {
    "SubagentStop": [...]
  }
}
```

settings.json에 머지 후 기대되는 최종 구조:
```json
{
  "hooks": {
    "SubagentStop": [...]
  }
}
```

`merge_hooks_config()` 코드에서 `source.get('hooks', {})`로 내부를 꺼내서 `data['hooks']`에 넣으므로 결과적으로는 올바르게 동작한다. 다만 소스 파일 자체가 settings.json의 부분 구조를 래핑한 형태이므로, 소스 파일의 최상위 `"hooks"` 키가 혼동을 줄 수 있다. MCP JSON 파일들(`opal/core/mcps/*.json`)은 `name`, `description`, `config` 등 메타데이터를 포함하는 자체 스키마를 사용하는데, hooks 소스 파일은 settings.json 구조를 그대로 래핑만 한 형태여서 일관성이 떨어진다.

**수정 권장**: 소스 파일 구조를 MCP JSON과 유사한 메타데이터 포함 형식으로 통일하거나, 아니면 래핑 없이 이벤트 맵만 포함하도록 단순화할 것.

**[C-2] `Stop` 이벤트 알림이 TASK.md 범위를 초과**

TASK.md 요구사항은 "SubagentStop 이벤트로 서브에이전트 완료 시 macOS 알림"만 명시하고 있다. PLAN에서는 `Stop` 이벤트(일반 응답 완료)까지 추가하고 있는데, 이는 TASK.md에 없는 범위 확장이다. `Stop` 이벤트는 모든 응답 완료마다 알림을 보내므로, 짧은 질의응답에서도 매번 알림이 울려 사용성에 부정적일 수 있다.

**수정 권장**: `Stop` 이벤트 추가가 필요하다면 TASK.md에 요구사항을 먼저 추가하거나, PLAN에서 `Stop` 포함 근거와 사용성 고려(예: 실행 시간 조건 필터)를 명시할 것.

### 🟡 Warning

**[W-1] python3 존재 여부 사전 체크 누락**

QA 체크리스트(코드 품질 마지막 항목)에서 python3 체크 필요성을 언급했으나, `merge_hooks_config()` 함수 구현이나 `install_claude()` 수정 코드에 python3 존재 여부 확인 로직이 포함되어 있지 않다. macOS에서는 기본 설치되어 있으나, 방어적 코딩으로 체크를 추가하는 것이 좋다.

### 🔵 Info

**[I-1] `Notification` 이벤트 미활용**

Claude Code hooks에는 `Notification` 이벤트도 존재한다. TASK.md에서도 관련 문서로 "SubagentStop, Stop, Notification 이벤트"를 언급하고 있으나, PLAN에서는 `Notification` 이벤트를 채택하지 않은 근거가 명시되어 있지 않다. 의도적 제외라면 그 이유를 기재하면 좋다.

## 4. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md | 요구사항 4개(hooks 파일 추가, SubagentStop 알림, install-mac.sh 머지, 기존 설정 보존)의 PLAN 반영 여부 | ⚠️ Stop 이벤트가 TASK 범위 초과 (C-2) |
| TASK.md | 제약 조건(Claude Code 전용, 머지 방식, macOS)의 PLAN 반영 여부 | ✅ 모두 반영됨 |
| TASK.md | 관련 문서(`scripts/install-mac.sh`) 분석 여부 | ✅ 라인 단위로 상세 분석 |
| install-mac.sh 실제 코드 | PLAN의 라인 번호 및 함수 설명 정확성 | ✅ `merge_mcp_config()`(99-129행), `install_claude()`(230-239행), `main()`(554-612행) 모두 일치 |

## 5. 판정

**⚠️ Needs Revision**

C-2(Stop 이벤트의 TASK 범위 초과)는 사용자 확인이 필요한 범위 문제이고, C-1(소스 파일 구조 일관성)은 유지보수성에 영향을 준다. 두 Critical 항목을 해결한 후 진행하는 것을 권장한다. 코드 분석의 정확성과 구현 계획의 구체성은 우수하다.
