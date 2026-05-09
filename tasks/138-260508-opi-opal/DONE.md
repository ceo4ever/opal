# DONE: opi 프로젝트 초기화 (138)

- 시작: 2026-05-08 17:43
- 완료: 2026-05-08 21:43
- 모드: 초기화 (기존)

## 변경 문서 목록

| 파일 | 작업 | 비고 |
|------|------|------|
| `.opal/AGENT.md` | 신규 (90줄) | PM 프로필 첫 등록 |
| `docs/CONVENTIONS.md` | 갱신 (+95줄) | 구현 규칙 섹션 신설 (8개 하위 절) |
| `docs/ARCHITECTURE.md` | 갱신 (+45줄) | 외부 의존 서비스 섹션 신설 |
| `docs/PROJECT.md` | 미세 갱신 (+1행, 1행 보강) | 문서 테이블에 `.opal/MEMORY.md` 등록 |
| `.opal/MEMORY.md` | 갱신 | 138 행 추가 + `last_task_number=138` |
| `docs/backup/*_202605081743.md` | 백업 3종 | 변경 전 스냅샷 |

## 핵심 결정 사항

1. **PM 전문 역할**: "AI 프레임워크 설계 전문가" — 재사용성 / 플랫폼 독립성 / 컴포넌트 표준화 / 하네스 준수 4축 검토
2. **금지사항 6종 명문화**: `~/.opal/` 직접 편집 금지, 변경이력 누락 금지, 플랫폼 분기 본문 침투 금지, 하네스 우회 금지, 무승인 코드 변경 금지, STATE.md 직접 편집 금지
3. **구현 규칙 SSOT 위치**: `docs/CONVENTIONS.md ## 구현 규칙` 섹션 — Guards · 디스패치 의무 · @header · Citation Rules · State · 도구 우선 · 변경이력 · 배포 경계 · 플랫폼 분기 격리
4. **외부 의존 서비스 카탈로그**: MCP 5종(context7 / playwright / shadcn / sequential-thinking / Notion) + Anthropic Claude API + Python venv + Node.js + 배포 채널(예정)
5. **배포 채널 결정 — 후속 139(P1)**: `opal` CLI 단일 진입점 + curl/iex one-liner + GitHub Release. Homebrew·npm은 후속

## 부트스트래퍼 점검 결과

3종 모두 OPAL 마커 정상 — 추가 갱신 불필요.

## 결함 및 회고

- **채번 충돌**: 17:44 시점 137 채번 시 `.opal/MEMORY.md` 작업 히스토리 재조회를 빠뜨려 별도 세션이 16:50에 선점한 137을 인지하지 못함. 138로 시프트하여 정리.
- **개선 권장**: PM Gate 또는 opi/opp 진입 직전에 "MEMORY 작업 히스토리 재조회" 단계를 명시화. 후속 태스크에서 검토 가치 있음.

## 다음 단계

- **태스크 139 (P1)** 채번 완료 — TASK.md 작성, PLAN 단계 진입 대기.
