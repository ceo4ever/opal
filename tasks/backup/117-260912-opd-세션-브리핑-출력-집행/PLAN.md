---
template: sdlc-v2
---
# PLAN: 세션 브리핑 출력 집행

> 입력: [TASK.md](TASK.md), [ANALYSIS.md](ANALYSIS.md)

## Approach
기존 상태·메모리 SSOT의 선택 로직은 유지하고, 세션 이벤트 진입점인 `event-loader`가 두 결과를 조합해 첫 응답용 Markdown을 직접 반환한다. 플랫폼 부트스트래퍼는 단일 명령의 stdout 전문을 그대로 출력하며, 실제 문자열을 fixture로 검증한다.

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| `event-loader project-brief` 공개 | 기본 출력은 완성된 Markdown, `--json`은 진단용 envelope | 이벤트·root 해석을 이미 소유한 컴포넌트에 조율 책임을 둔다 (`opal/tools/event-loader/event_loader.py:62-92`). |
| 성공 결과만 부분 조립 | 상태 또는 메모리 조회 실패 시 해당 블록만 생략하고 전체 명령은 성공 | 기존 부트 폴백을 보존하고 프로젝트 진입을 불필요하게 차단하지 않는다. |
| stdout 전문 출력 | 부트스트래퍼는 명령 성공 시 stdout을 byte-for-byte 첫 응답 맨 앞에 둔다 | JSON 해석과 응답 조립 사이의 누락 지점을 제거한다. |
| 1,024바이트 상한 | 조립기가 UTF-8 바이트 길이를 기준으로 필드 내용을 결정론적으로 축약한다 | 기존 bounded 부트 계약을 유지한다. |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 브리핑 생산자 구현 | 알투(PM 직접) | `opal/tools/event-loader/event_loader.py`, `opal/tools/event-loader/tests/test_event_loader_extended.py` | 두 SSOT 도구 호출, 단일행 정규화, Markdown 조립, UTF-8 상한, raw/JSON CLI와 fixture 테스트 추가 | 없음 | P1 | AC-1, AC-2, AC-3, AC-4, C-1, C-2 |
| W-2. 최초 소비자 계약 교체 | 알투(PM 직접) | `opal/bootstrapper/claude-bootstrap.md`, `opal/bootstrapper/codex-bootstrap.md`, `opal/bootstrapper/cursor-bootstrap.mdc`, `opal/bootstrapper/gemini-bootstrap.md`, `opal/core/AGENT.md` | 개별 JSON 조회를 단일 명령으로 교체하고 stdout 전문 출력 MUST를 명시 | W-1 | P2 | AC-3, AC-5, AC-6, C-1, C-3 |
| W-3. 통합 감사 강화 | 알투(PM 직접) | `scripts/tests/task113_bootstrap_audit.py`, `scripts/tests/test_task113_bootstrap_contract.py` | 플랫폼 본문 동등성, 빈 결과, 실제 렌더 stdout과 상한을 자동 검증 | W-1, W-2 | P3 | AC-1, AC-2, AC-3, AC-4, AC-5, AC-6 |
| W-4. 문서·배포 경계 최신화 | 알투(PM 직접) | `opal/tools/event-loader/README.md`, `opal/core/references/opal-pm.md`, `docs/ARCHITECTURE.md`, `docs/PROJECT.md` | 새 CLI 소유권, 세션 경계, source→installed 계약 반영 | W-1 | P3 | AC-6, C-3, C-4 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 플랫폼이 stdout 출력 지시를 위반함 | 완성된 브리핑이 생성돼도 첫 응답에서 빠질 수 있음 | 사용자 세션 복원 정보 누락 | 조립 재량을 제거하고 네 플랫폼 부트 본문에 byte-for-byte MUST 및 정적 감사를 둔다. |
| H-2. source와 installed 도구 경로가 다름 | 설치본에서 형제 도구를 찾지 못함 | 짧은 부트 응답으로 조용히 폴백 | `__file__` 상대 경로를 사용하고 install 뒤 parity·실호출을 검증한다. |

## Release and recovery
- 적용 순서: W-1 → W-2 → W-3·W-4 → source 검증 → `install-mac.sh` 배포 → installed parity와 실제 프로젝트 호출
- 검증 범위: event-loader 단위 테스트, 부트 통합 감사, 네 플랫폼 본문 동등성, 실제 프로젝트 Markdown, code-scan header 검증
- 실측 경계: 도구 stdout이 UTF-8 1,024바이트 이하이며 `이어보기`와 `우선 검토`를 한 번에 포함하는지 확인
- 실패 시: install 전에는 변경 파일을 수정해 재검증하고, install 후 실패하면 배포본과 소스 해시 불일치를 확인한 뒤 재설치한다. 사용자 소유 태스크 115 변경은 복구 대상에 포함하지 않는다.
