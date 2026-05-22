# cmux-tool

cmux browser 자동화 래퍼: 12+1종 서브명령 디스패처

## 개요

cmux browser 명령을 캡슐화한 OPAL 도구 래퍼. 단일 진입점(`run.sh`)을 통해 12+1종 서브명령을 지원하며 모든 결과를 JSON으로 반환한다. 첫 인자가 URL이면 `extract`로 자동 라우팅하여 레거시 호출 호환성을 유지한다.

**단독 호출 경계**: 알투/워커가 cmux-tool을 단독 호출할 때 이 도구는 단일 책임(cmux browser 래퍼)만 수행한다. cmux 미설치 시 에러 JSON 반환, fallback은 도구 내부에 없다 (PLAN §2.5).

## 요구사항

| 항목 | 내용 |
|------|------|
| cmux 버전 | 0.64.3 이상 |
| 환경 변수 | `$CMUX_SURFACE_ID` (cmux 터미널 내 자동 설정) |
| Python | 3.x (JSON 직렬화 — macOS 내장) |
| 설치 위치 | `~/.opal/tools/cmux-tool/run.sh` (install-mac.sh 자동 배포) |

## 사용법

### 레거시 호환 — URL 단독 (extract 자동 라우팅)

```bash
bash ~/.opal/tools/cmux-tool/run.sh https://example.com
bash ~/.opal/tools/cmux-tool/run.sh https://example.com --mode clean --wait 3000
bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3 https://google.com
```

### 서브명령 — 직접 지정

```bash
# 사용법 보기
bash ~/.opal/tools/cmux-tool/run.sh --help

# extract: 기존 3모드 흐름 유지 (R-2 호환)
bash ~/.opal/tools/cmux-tool/run.sh extract https://example.com
bash ~/.opal/tools/cmux-tool/run.sh extract --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh extract --surface surface:3 https://google.com

# snapshot: Accessibility tree 스냅샷
bash ~/.opal/tools/cmux-tool/run.sh snapshot --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh snapshot --surface surface:3 --compact

# eval: JavaScript 실행
bash ~/.opal/tools/cmux-tool/run.sh eval --script "document.title" --surface surface:3

# wait: 요소/로드 완료 대기
bash ~/.opal/tools/cmux-tool/run.sh wait --load-state complete --surface surface:3 --timeout-ms 10000
bash ~/.opal/tools/cmux-tool/run.sh wait --selector "#success-msg" --surface surface:3

# navigate: URL 이동
bash ~/.opal/tools/cmux-tool/run.sh navigate https://example.com/page --surface surface:3

# click: 요소 클릭
bash ~/.opal/tools/cmux-tool/run.sh click "#submit-btn" --surface surface:3

# fill: 입력 채우기 (--text 플래그 사용 — 외부 SSOT R-T1 검증)
bash ~/.opal/tools/cmux-tool/run.sh fill "#email" --text "user@example.com" --surface surface:3

# open: 신규 브라우저 오픈
bash ~/.opal/tools/cmux-tool/run.sh open https://example.com

# open-split: 브라우저 분할 오픈
bash ~/.opal/tools/cmux-tool/run.sh open-split https://example.com

# reload: 새로고침
bash ~/.opal/tools/cmux-tool/run.sh reload --surface surface:3

# press: 키 입력
bash ~/.opal/tools/cmux-tool/run.sh press "Enter" --surface surface:3

# get: 요소 텍스트/속성 조회
bash ~/.opal/tools/cmux-tool/run.sh get title --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh get "#link" --attr href --surface surface:3
```

### 옵션 표

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--mode <m>` | `full` | 추출 모드 (extract 전용): `full` / `clean` / `wireframe` |
| `--wait <ms>` | `2000` | 로드 후 추가 대기(밀리초). `0`이면 생략 (extract 전용) |
| `--surface <handle>` | — | surface 핸들 (B/C 모드 활성화) |
| `--timeout-ms <ms>` | — | wait 명령 타임아웃 |
| `--compact` | — | snapshot 압축 출력 |
| `--text <value>` | — | fill 값 (--text 플래그 사용) |
| `--script <js>` | — | eval JS 스크립트 |
| `--attr <name>` | — | get 속성명 |

## 출력 스키마

### 공통 5필드 (모든 서브명령)

```json
{
  "ok": true,
  "command": "snapshot",
  "surface": "surface:3",
  "user_owned": true,
  "error": null
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `ok` | bool | 성공 여부 |
| `command` | string | 실행된 서브명령 (`extract`/`snapshot`/`click` 등) |
| `surface` | string\|null | 사용된 surface 핸들. 전역 명령에서 null |
| `user_owned` | bool | `--surface` 핸들 명시 시 `true` — 민감 정보 경고 시그널 |
| `error` | string\|null | 실패 시 에러 코드 (성공 시 없음) |

### 명령별 특화 필드

| 서브명령 | 특화 필드 |
|---------|----------|
| `extract` | `method`(="cmux") / `mode`("A"/"B"/"C") / `title` / `final_url` / `content` / `bytes` / `wait_ms` — **기존 8필드 그대로 유지 (R-2 호환)** |
| `snapshot` | `snapshot_text` / `length` |
| `eval` | `result` (eval 반환값) / `script_len` |
| `wait` | `selector` / `elapsed_ms` / `matched`(bool) |
| `navigate` | `from_url` / `to_url` |
| `click` / `fill` / `press` | `selector` (해당 시) / `value` (해당 시) / `key` |
| `get` | `selector` / `value` |
| `open` / `open-split` | `new_surface` / `to_url` |
| `reload` | `before_url` / `after_url` |

성공 예시 (snapshot):
```json
{"ok":true,"command":"snapshot","surface":"surface:3","user_owned":true,"snapshot_text":"...","length":4096}
```

실패 예시 (공통 5필드 + fallback):
```json
{"ok":false,"command":"click","surface":"surface:3","user_owned":true,"error":"eval_failed","detail":"cmux browser click 실패: #foo"}
```

## extract 모드 (A/B/C)

| 모드 | 조건 | 설명 |
|------|------|------|
| A | URL만 지정 | 신규 surface 열기 → 추출 → tab close |
| B | `--surface <h>` 단독 | 현재 페이지 추출 (cleanup 절대 금지) |
| C | `--surface <h>` + URL | surface 재사용 + navigate (cleanup 절대 금지) |

## 에러 코드

| 코드 | 종료값 | 원인 | wtm-agent 처리 |
|------|--------|------|---------------|
| `usage` | 1 | 인자 오류 | 호출자 수정 필요 (폴백 금지) |
| `not_in_cmux` | 2 | `CMUX_SURFACE_ID` 미설정 | wtm-agent 자동 폴백 |
| `cmux_not_installed` | 3 | `cmux` 명령 없음 | wtm-agent 자동 폴백 |
| `invalid_surface` | 4 | surface 핸들 형식 오류 | 호출자 수정 필요 (폴백 금지) |
| `open_failed` | 5 | `cmux browser open` 실패 | wtm-agent 자동 폴백 |
| `surface_parse_failed` | 5 | open 출력 파싱 실패 | wtm-agent 자동 폴백 |
| `goto_failed` | 6 | `cmux browser goto` 실패 | 폴백 금지 (URL 오류) |
| `wait_failed` | 7 | 페이지 로드 타임아웃 | 폴백 금지 (네트워크 문제) |
| `eval_failed` | 8 | 명령 실행 실패 | 폴백 금지 (명령 오류) |

> **wtm-agent 폴백 트리거 4종**: `not_in_cmux` / `cmux_not_installed` / `surface_parse_failed` / `open_failed`  
> 나머지 5종은 입력 정정 필요 — 즉시 에스컬레이션.

## 안전 가드

### B/C 모드 cleanup 절대 금지

B/C 모드(사용자 surface 재사용)에서는 `cmux browser <surface> tab close`를 **절대 호출하지 않는다**.

```
A 모드: tab close 호출 (도구가 직접 열었으므로 정리)
B 모드: tab close 호출 안 함 (cleanup 금지)
C 모드: tab close 호출 안 함 (cleanup 금지)
```

정적 검증: `grep -n 'tab close' lib/dispatch.sh` — 모든 호출이 `A)` 케이스 내부.

### user_owned 시그널

B/C 모드 실행 시 `"user_owned": true` 포함. `opal-wtm-agent`는 이 시그널 수신 시 경고를 자동 부착한다:

> 사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요

## 파일 구조

```
opal/tools/cmux-tool/
├── run.sh                          # 디스패처 진입점
├── README.md                       # 이 파일
├── lib/                            # 공통 헬퍼
│   ├── dispatch.sh                 # 서브명령 라우팅 + cmux 실행 (N-1)
│   ├── cmux-helpers.sh             # surface 기동·검증 헬퍼 (N-2)
│   ├── branch.sh                   # A/B/C 분기 결정 (N-3)
│   └── json.sh                     # JSON 직렬화 공통 (N-4)
├── examples/                       # 흡수된 레시피
│   ├── e2e-form-fill.sh            # 폼 채우기 E2E (N-5)
│   ├── e2e-branch-auto.sh          # A/B/C 분기 자동 결정 E2E (N-6)
│   └── claude-hooks.sample.json    # Claude Code hooks 3종 (N-7)
└── docs/
    └── CMUX-REFERENCE.md           # CLI 18종 + Socket API + 단축키 + hooks (N-8)
```

## 흡수 자산 출처 표

| 신규 파일 | 원본 자산 | 처분 |
|----------|----------|------|
| `lib/cmux-helpers.sh` | `cmux/scripts/_lib.sh:11-103` | 전량 흡수 |
| `lib/branch.sh` | `cmux/scripts/test-browser.sh:65-100` | 분기 로직 흡수 |
| `lib/dispatch.sh` | `opal/tools/cmux-tool/run.sh` (extract 흐름) | 재설계 흡수 |
| `lib/json.sh` | `opal/tools/cmux-tool/run.sh:178-207` | 분리 흡수 |
| `examples/e2e-form-fill.sh` | `cmux/docs/CMUX.md §7-A` + `test-browser.sh` | 조합 흡수 |
| `examples/e2e-branch-auto.sh` | `cmux/scripts/test-browser.sh:1-133` | 원형 보존 흡수 |
| `examples/claude-hooks.sample.json` | `cmux/config/claude-hooks.sample.json` | 전량 흡수 (subtitle MAMS→OPAL) |
| `docs/CMUX-REFERENCE.md` | `cmux/docs/CMUX-TOOLS.md` 전량 + `cmux/docs/CMUX.md [일반]섹션` | 부분 흡수 |

폐기 자산: `cmux/scripts/_config.sh` / `start-all.sh` / `stop-all.sh` / `open-dev.sh` / `analyze-log.sh` / `cmux/config/cmux.json` / `CMUX.md [MAMS 전용]섹션` (MAMS 특화 또는 범위 외)

---

## 변경이력

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-12 21:35 KST | 초기 작성 — cmux browser 래퍼 3모드(A/B/C) + cleanup 가드 + user_owned 시그널 (002) |
| v1.1 | 2026-05-22 10:00 KST | 디스패처 재설계 — 12+1종 서브명령 + lib/ 공통 헬퍼 4파일 + examples/ E2E 레시피 + docs/ 통합 참조 + fallback 라벨 phase3→phase2 + 흡수 자산 출처 표 (007) |
