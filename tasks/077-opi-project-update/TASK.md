# TASK: opi 프로젝트 최신화 (077)

> 작성일: 2026-04-03 | 작업 유형: 최신화 | 적용 스킬: opi

## 변경 감지 항목

### 신규
- `opal/core/mcps/playwright.json` — Playwright MCP 설정 추가
- `opal/tools/xlsx-tool/` — xlsx CLI 도구 신규 (076)
- `opal/tools/requirements.txt` — Python 통합 의존성 관리 파일 신규 (076)
- `~/.opal/.venv/` — Python 가상환경 (install-mac.sh `install_opal_venv()` 추가)
- `opal/core/references/tools.md` — 도구 레지스트리 신규 (xlsx-tool 등록)

### 변경
- `opal/core/references/opal-skills-registry.json` — 수정됨
- oppd 파이프라인: `ROADMAP.md` → `WBS.md` 전환 (075)

## 업데이트 대상

| 문서 | 항목 |
|------|------|
| `docs/ARCHITECTURE.md` | ① oppd 설명 ROADMAP→WBS ② Global Layer tools/ 확장 + .venv/ 추가 + references/ tools.md 반영 ③ 배포 모델 opal/tools/ 분리 + .venv + MCP 경로 정확화 ④ 디렉토리 구조 opal/tools/ 하위 항목 추가 |
| `.opal/MEMORY.md` | 작업 히스토리 075, 076, 077 추가 |
