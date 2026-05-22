---
@header {
  "module": "cmux-readme",
  "layer": "reference",
  "domain": "dev-tool",
  "description": "cmux 통합 환경 진입점 — 구조 안내·빠른 시작·프레임워크 승격 체크리스트",
  "exports": ["구조", "빠른시작", "프레임워크승격대상", "관련문서"],
  "depends": ["cmux-guide"]
}
---

# cmux MAMS 통합 환경

MAMS 프로젝트의 cmux(AI 코딩 에이전트용 macOS 터미널) 통합 자산 루트.  
문서·설정·스크립트·로그를 한 폴더로 모아 관리하며, OPAL 프레임워크 승격을 염두에 둔 변수화 설계를 적용했다.

---

## 구조

```
.opal/cmux/
├── README.md                       # 이 파일 — 진입점
├── docs/
│   ├── CMUX.md                     # 메인: 워크플로우·개념·예시 (9개 섹션)
│   └── CMUX-TOOLS.md               # CLI·Socket API·hooks 레퍼런스
├── config/
│   ├── cmux.json                   # 프로젝트 팔레트 (source of truth, 15개 명령)
│   ├── ghostty.config.sample       # Ghostty 설정 예시 (수동 적용용)
│   └── claude-hooks.sample.json    # Claude Code hooks 샘플 (수동 적용용)
├── scripts/
│   ├── _config.sh                  # 프로젝트 종속 변수 (포트·경로·명령)
│   ├── start-all.sh                # BE+FE+Batch+브라우저 일괄 기동
│   ├── stop-all.sh                 # 일괄 종료
│   ├── open-dev.sh                 # 개별 Surface 기동 (인자: be/fe/fe-wire/fe-test/batch)
│   ├── test-browser.sh             # 브라우저 E2E 러너 (A/B/C 분기 포함)
│   └── analyze-log.sh              # 최근 N분 로그 tail + ERROR/Traceback 추출
└── logs/
    └── .gitkeep                    # 실제 로그 파일은 .gitignore 처리
```

**루트 심볼릭 링크**: `cmux.json` → `.opal/cmux/config/cmux.json`  
cmux는 프로젝트 루트의 `cmux.json`을 자동 인식한다.

```bash
# 심볼릭 링크 확인
ls -l cmux.json
# → cmux.json -> .opal/cmux/config/cmux.json
```

---

## 빠른 시작

### Step 1 — 팔레트 로드 확인

cmux에서 MAMS 프로젝트 루트(`/Volumes/Data/StoreLinkStudio/mams`)를 Workspace로 열면  
`cmux.json` 팔레트가 자동 로드된다. `⌘P`를 눌러 `MAMS:` 명령이 표시되는지 확인한다.

### Step 2 — `MAMS: Start All` 실행

```bash
# 팔레트 (⌘P → "MAMS: Start All")
# 또는 직접 실행
bash .opal/cmux/scripts/start-all.sh
```

BE(8000) + FE(3000) + Batch(8080) Surface가 생성·기동된다.

### Step 3 — 검증

```bash
# Swagger 브라우저 분할 오픈 (팔레트: "MAMS: Open Swagger")
cmux browser open-split http://localhost:8000/docs

# FE 확인
cmux browser open-split http://localhost:3000

# Airflow UI 확인
cmux browser open-split http://localhost:8080
```

---

## 프레임워크 승격 대상

이 폴더의 자산을 OPAL 프레임워크(`~/.opal/cmux/`)로 승격할 때 참고한다.

### 승격 가능 (일반 cmux 자산 — 프로젝트 독립적)

- [ ] `scripts/start-all.sh` — 변수만 사용하므로 그대로 재사용 가능
- [ ] `scripts/stop-all.sh` — 동일
- [ ] `scripts/open-dev.sh` — 동일
- [ ] `scripts/test-browser.sh` — 동일
- [ ] `scripts/analyze-log.sh` — 동일
- [ ] `docs/CMUX.md §1 설치 및 초기 설정` [일반] 섹션
- [ ] `docs/CMUX.md §3 필수 단축키` [일반] 섹션
- [ ] `docs/CMUX.md §6 알림 연동` [일반] 섹션
- [ ] `docs/CMUX-TOOLS.md` 전체 (CLI·Socket API·hooks 레시피)
- [ ] `config/ghostty.config.sample` — 폰트 이름만 변경 필요
- [ ] `config/claude-hooks.sample.json` — 그대로 재사용 가능

### 프로젝트 고유 (MAMS 전용 — 승격 시 분리 필요)

- [ ] `scripts/_config.sh` — MAMS 포트·경로·명령 하드코딩 → 프로젝트별 교체 필요
- [ ] `config/cmux.json` — MAMS 전용 명령(Swagger/Airflow 등) 포함
- [ ] `docs/CMUX.md §2 Workspace/Surface 표준 구성` [MAMS 전용]
- [ ] `docs/CMUX.md §4 서버 자동 기동 레시피` [MAMS 전용]
- [ ] `docs/CMUX.md §7 예시 워크플로우` [MAMS 전용]
- [ ] `docs/CMUX.md §8 로그 분석 워크플로우` [MAMS 전용]
- [ ] `.opal/AGENT.md`의 `## cmux 자동 제안 규칙` 섹션 (트리거 테이블에 MAMS 포트 참조)

> **승격 절차**: `_config.sh`만 프로젝트별로 새로 작성하면 나머지 스크립트는 그대로 재사용 가능하도록 설계되어 있다.

---

## 관련 문서

| 문서 | 역할 |
|------|------|
| [docs/CMUX.md](./docs/CMUX.md) | cmux 워크플로우·설정·예시 메인 가이드 (9개 섹션) |
| [docs/CMUX-TOOLS.md](./docs/CMUX-TOOLS.md) | CLI 레퍼런스·Socket API·hooks 레시피 |
| [.opal/AGENT.md](../AGENT.md) `## cmux 자동 제안 규칙` | 알투 자동 제안 트리거·의무화 규칙 |
| [.claude/settings.local.json](../../.claude/settings.local.json) | 프로젝트 Claude Code 설정 (hooks 포함) |
