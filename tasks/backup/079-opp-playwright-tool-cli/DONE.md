# DONE: playwright-tool CLI 구현 + wtm 스킬 연동

> 완료일: 2026-04-03 | 적용 스킬: opp

## 완료 요약

Playwright를 독립 CLI 툴로 래핑하여 OPAL 툴로 등록하고, wtm 스킬의 `--browser` 모드가 MCP 대신 CLI를 호출하도록 전환했다. 복수 URL + browser 모드에서 에이전트 병렬 디스패치가 가능해졌다.

## 변경 파일

| 파일 | 유형 | 내용 |
|------|------|------|
| `opal/tools/playwright-tool/run.sh` | 신규 | OPAL 툴 래퍼 (xlsx-tool 패턴, playwright 설치 체크 포함) |
| `opal/tools/playwright-tool/main.py` | 신규 | playwright sync API CLI, argparse, JSON 출력, 3단 변환 폴백 |
| `scripts/install-mac.sh` | 수정 | playwright-tool run.sh chmod +x 블록 추가 |
| `skills/web-to-markdown/SKILL.md` | 수정 | v1.6 → v1.7: Phase 2 MCP → CLI 전환, browser 모드 병렬화 허용 |

## 주요 결정

- **멀티브라우저(CLI) vs 멀티탭(MCP)**: CLI 방식 채택 — 프로세스 격리로 탭 충돌 원천 차단, OPAL 도구 우선 원칙 부합
- **playwright sync API**: CLI 단일 URL 처리, xlsx-tool과 일관성
- **배포 자동 포함**: `install_dir` 전체 복사로 playwright-tool 디렉토리 자동 배포, chmod 블록만 추가

## QA 결과

| 항목 | 결과 |
|------|------|
| 기본 실행 (https://example.com) | ✅ |
| --mode clean | ✅ |
| --output 파일 저장 + path 필드 | ✅ |
| --timeout 초과 에러 처리 | ✅ |
| 잘못된 URL 에러 처리 | ✅ |
| JSON 파싱 가능 | ✅ |
