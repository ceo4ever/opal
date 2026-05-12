# cmux-tool

cmux browser 자동화 래퍼: URL 추출 + 사용자 surface 재사용

## 개요

cmux browser 명령을 캡슐화한 OPAL 도구 래퍼. 세 가지 모드(A/B/C)로 웹 페이지 HTML을 추출하고 JSON으로 반환한다. B/C 모드(사용자 surface 재사용)에서 세션 기반 추출 시 `user_owned: true` 시그널을 제공하여 호출자가 민감 정보 경고를 부착할 수 있게 한다.

## 요구사항

| 항목 | 내용 |
|------|------|
| cmux 버전 | 0.64.3 이상 |
| 환경 변수 | `$CMUX_SURFACE_ID` (cmux 터미널 내 자동 설정) |
| Python | 3.x (JSON 직렬화 — macOS 내장) |
| 설치 위치 | `~/.opal/tools/cmux-tool/run.sh` (install-mac.sh 자동 배포) |

## 사용법

### 모드 A — URL 신규 추출

```bash
bash ~/.opal/tools/cmux-tool/run.sh <url> [--mode <full|clean|wireframe>] [--wait <ms>]
```

예시:
```bash
bash ~/.opal/tools/cmux-tool/run.sh https://example.com
bash ~/.opal/tools/cmux-tool/run.sh https://example.com --mode clean --wait 3000
bash ~/.opal/tools/cmux-tool/run.sh https://example.com --wait 0   # sleep 생략
```

### 모드 B — 사용자 surface 현재 페이지 추출

```bash
bash ~/.opal/tools/cmux-tool/run.sh --surface <handle> [--mode <m>] [--wait <ms>]
```

예시:
```bash
bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3
bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3 --mode clean
```

### 모드 C — 사용자 surface + 네비게이션 후 추출

```bash
bash ~/.opal/tools/cmux-tool/run.sh --surface <handle> <url> [--mode <m>] [--wait <ms>]
```

예시:
```bash
bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3 https://google.com
bash ~/.opal/tools/cmux-tool/run.sh --surface surface:3 https://google.com --wait 5000
```

### 옵션 표

| 옵션 | 기본값 | 설명 |
|------|--------|------|
| `--mode <m>` | `full` | 추출 모드: `full` / `clean` / `wireframe` |
| `--wait <ms>` | `2000` | 로드 후 추가 대기 시간(밀리초). `0`이면 sleep 생략 |
| `--surface <handle>` | — | 사용자 surface 핸들 (B/C 모드 활성화) |

## 출력 스키마

성공 시 stdout으로 JSON 1줄 출력:

```json
{
  "ok": true,
  "method": "cmux",
  "mode": "A|B|C",
  "surface": "surface:N",
  "user_owned": false,
  "title": "페이지 타이틀",
  "final_url": "https://...",
  "content": "<html>...</html>",
  "bytes": 315209,
  "wait_ms": 2000
}
```

| 필드 | 타입 | 설명 |
|------|------|------|
| `ok` | bool | 성공 여부 |
| `method` | string | 항상 `"cmux"` |
| `mode` | string | 실행 모드 (`A`/`B`/`C`) |
| `surface` | string | 사용된 surface 핸들 |
| `user_owned` | bool | B/C 모드면 `true` — 민감 정보 포함 가능 시그널 |
| `title` | string | 페이지 타이틀 |
| `final_url` | string | 최종 URL (리다이렉트 후) |
| `content` | string | `document.documentElement.outerHTML` 결과 |
| `bytes` | int | content의 UTF-8 바이트 크기 |
| `wait_ms` | int | 실제 적용된 wait_ms |

실패 시 stderr로 JSON 출력 + 비정상 종료 코드:

```json
{
  "ok": false,
  "error": "<에러 코드>",
  "detail": "설명",
  "fallback": "phase3"
}
```

## 에러 코드

| 코드 | 종료값 | 원인 | 대응 |
|------|--------|------|------|
| `usage` | 1 | 인자 오류 또는 `--help` | 사용법 확인 |
| `not_in_cmux` | 2 | `CMUX_SURFACE_ID` 미설정 | cmux 터미널 내에서 실행 |
| `cmux_not_installed` | 3 | `cmux` 명령 없음 | [cmux 설치](https://cmux.com/) |
| `invalid_surface` | 4 | surface 핸들 형식 오류 | `surface:N` 또는 UUID 형식 확인 |
| `open_failed` | 5 | `cmux browser open` 실패 | cmux 상태 확인 |
| `surface_parse_failed` | 5 | open 출력에서 surface 파싱 실패 | cmux 버전 확인 |
| `goto_failed` | 6 | `cmux browser goto` 실패 | URL 및 surface 유효성 확인 |
| `wait_failed` | 7 | 페이지 로드 타임아웃 (15초) | 네트워크 상태 확인 |
| `eval_failed` | 8 | HTML 추출 실패 | surface 상태 확인 |

## 안전 가드

### B/C 모드 cleanup 절대 금지

B/C 모드(사용자 surface 재사용)에서는 `cmux browser <surface> tab close`를 **절대 호출하지 않는다**. 사용자가 직접 열어 사용 중인 탭을 닫으면 데이터 손실이 발생할 수 있다.

```
A 모드: tab close 호출 (도구가 직접 열었으므로 정리)
B 모드: tab close 호출 안 함 (cleanup 금지)
C 모드: tab close 호출 안 함 (cleanup 금지)
```

정적 검증: `grep -cE 'tab close' run.sh`로 호출 위치가 모두 `A)` 케이스 내부인지 확인.

### user_owned 시그널

B/C 모드 실행 시 출력 JSON에 `"user_owned": true`를 포함한다. 호출자(`opal-wtm-agent`)는 이 시그널을 수신하면 결과 보고에 다음 경고를 자동 부착한다:

> 사용자 세션 기반 추출 — 민감 정보 포함 가능, 외부 공유 시 검토 필요

### cmux 설치 링크

cmux 미설치 시 에러 JSON에 설치 링크를 제공한다:
- 공식 사이트: https://cmux.com/
- GitHub: https://github.com/manaflow-ai/cmux

---

| 버전 | 일시 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-05-12 21:35 KST | 초기 작성 — cmux browser 래퍼 3모드(A/B/C) + cleanup 가드 + user_owned 시그널 (002) |
