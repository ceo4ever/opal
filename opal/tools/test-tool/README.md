# test-tool

> OPAL 테스트 단계별 도구 결정론적 집행기 — 4서브명령(resolve/check/unit/integration)

## 개요

`test-tool`은 `test-tools.yaml`을 읽어 FE/BE×단계별 도구를 실행·판정하는 **얇은 래퍼**다.  
러너(pytest/vitest/cmux/eslint 등)를 재구현하지 않는다 — yaml 해석 → 명령 실행(subprocess) → JSON 증거 반환.

- **단계1 (단위/EXECUTE)**: `unit` 서브명령 — lint→typecheck→unit stop-on-fail
- **단계2 (통합/TEST)**: `integration` 서브명령 — cmux-tool 에러코드 소비 → playwright 폴백

> **[MUST] 루프 한도 비보유**: test-tool은 1회 실행·판정만 수행한다.  
> 재시도 루프는 오케스트레이터 책임이다. 한도 수치는 `opal-harness.md §1` 참조.

---

## 실행 경로

```bash
bash ~/.opal/tools/test-tool/run.sh <서브명령> [옵션]
# 또는 소스에서:
bash opal/tools/test-tool/run.sh <서브명령> [옵션]
```

**의존**: `.venv python` (OPAL 설치) + PyYAML + `cmux-tool` (E2E, PATH에 있어야 함)

---

## 서브명령

### `resolve`

`test-tools.yaml` resolution_order(project→global→추론)를 해석하여 tier×scope 도구셋 JSON 반환.

```bash
bash run.sh resolve [--stack py|ts] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": true,
  "command": "resolve",
  "tiers": {
    "unit": { "fe": {...}, "be": {...} },
    "integration": { "e2e": [...], "api_db": {...} }
  },
  "source": "project",
  "stack": { "language": "typescript", "framework": "nextjs", "runtime": "node" }
}
```

**exit code**: `0` / `yaml_parse_failed(2)` / `no_runner(3)`

---

### `check`

도구 설치 상태 게이트 검사 — `required` 미설치 시 차단.

```bash
bash run.sh check [--tier unit|integration] [--category CATEGORY] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": true,
  "command": "check",
  "results": [
    { "name": "eslint", "installed": true, "required": true },
    { "name": "jest-axe", "installed": false, "required": false }
  ],
  "blocked": false
}
```

**exit code**: `0` / `required_missing(4)`

---

### `unit`

lint → typecheck → unit 계층 stop-on-fail 단발 실행.

```bash
bash run.sh unit [--scope fe|be] [--changed-files FILE...] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": true,
  "command": "unit",
  "layers": [
    { "name": "lint",      "cmd": "eslint .",     "status": "pass", "stdout": "", "exit": 0 },
    { "name": "typecheck", "cmd": "tsc --noEmit", "status": "pass", "stdout": "", "exit": 0 },
    { "name": "unit",      "cmd": "vitest run",   "status": "pass", "stdout": "", "exit": 0 }
  ],
  "stopped_at": null
}
```

**[MUST] stop-on-fail**: lint 실패 시 typecheck/unit 미실행 + `stopped_at=lint` 기록.  
**[MUST] 단발 실행**: watch 플래그(`--watch`/`-w`) 사용 금지.

**exit code**: `0` / `layer_failed(5)`

---

### `integration`

cmux-tool 에러코드 소비 → playwright 폴백 결정 + E2E mode A 실행.

```bash
bash run.sh integration [--scope fe|be] [--url URL] [--project-root PATH]
```

**출력 JSON**:
```json
{
  "ok": true,
  "command": "integration",
  "e2e": {
    "driver": "cmux",
    "status": "pass",
    "url": "http://localhost:3000"
  },
  "api_db": { "status": "skip" },
  "escalate": false
}
```

**[MUST] mode A**: `--surface` 미전달 → 신규 surface 강제 (사용자 surface B/C 재사용 금지).  
**[MUST] SUT 경계**: 앱 가동 전제 검사만 — 기동 책임 비보유. `open_failed`/`wait_failed` 시 에스컬레이션.

**exit code**: `0` / `e2e_failed(6)` / `escalation(7)`

---

## 에러 코드

| 코드 | exit | 원인 | 처리 |
|------|------|------|------|
| `venv_missing` | 1 | OPAL .venv 없음 | install-mac.sh 재실행 |
| `yaml_parse_failed` | 2 | test-tools.yaml YAML 문법 오류 | yaml 수정 후 재시도 |
| `no_runner` | 3 | yaml 없음 + 추론 불가 | test-tools.yaml 생성 |
| `required_missing` | 4 | required 도구 미설치 | 도구 설치 후 재시도 |
| `layer_failed` | 5 | unit 계층 stop-on-fail | 실패 계층 수정 후 재시도 |
| `e2e_failed` | 6 | E2E 실패 (폴백도 실패) | SUT 상태·네트워크 확인 |
| `escalation` | 7 | cmux 에스컬레이션 에러코드 (폴백 금지) | 에러코드별 원인 수정 |

### cmux-tool 에러코드 분류

**폴백 트리거 4종** (→ playwright 자동 전환):
- `not_in_cmux` — CMUX_SURFACE_ID 미설정
- `cmux_not_installed` — cmux 명령 없음
- `surface_parse_failed` — open 출력 파싱 실패
- `open_failed` — cmux browser open 실패

**에스컬레이션 5종** (→ 폴백 금지, exit 7):
- `usage` — 인자 오류
- `invalid_surface` — surface 핸들 형식 오류
- `goto_failed` — URL/navigate 오류
- `wait_failed` — 페이지 로드 타임아웃
- `eval_failed` — 명령 실행 실패

> SSOT: `cmux-tool/README.md §에러코드` 테이블.

---

## resolution_order

1. `{project}/.opal/test-tools.yaml` — 프로젝트별 오버라이드 (최우선)
2. `OPAL_TEST_TOOLS_GLOBAL` 환경변수 경로 — 글로벌 기본값
3. `package.json` / `pyproject.toml` 추론 — 내부 폴백

스키마 참조: `opal/core/references/test-tools-schema.yaml`  
템플릿 참조: `opal/templates/test-tools.yaml`

---

## 트리거 조건

| 단계 | 서브명령 | 수행 주체 |
|------|---------|---------|
| EXECUTE (단위) | `unit --scope fe|be` | 구현 워커 자가검증 |
| TEST (통합) | `integration --scope fe|be --url URL` | opal-test-agent |
| 단계 진입 전 | `check --tier unit|integration` | 워커/에이전트 |
| 도구셋 확인 | `resolve` | PM/오케스트레이터 |

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-06-23 | 초기 구현 — 4서브명령(resolve/check/unit/integration) + cmux-tool 에러코드 소비 어댑터 + stop-on-fail 러너 (T039 Step3 GREEN) |
