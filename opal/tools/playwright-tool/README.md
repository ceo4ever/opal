# playwright-tool

> 웹 페이지를 headless Chromium으로 로드해 Markdown으로 변환하는 단일 명령 CLI
> 소스: `opal/tools/playwright-tool/` | 배포: `~/.opal/tools/playwright-tool/`
> 의존성: `~/.opal/.venv/bin/python` + `playwright` 패키지 + Chromium 브라우저 바이너리

## 개요

`playwright-tool`은 URL 하나를 받아 실제 브라우저로 렌더한 뒤(`wait_until="networkidle"`), HTML을 Markdown으로 변환해 단일 라인 JSON으로 돌려준다. JS로 본문을 그리는 페이지처럼 정적 fetch로 얻을 수 없는 문서를 수집할 때 쓴다.

- **서브명령이 없다** — 위치 인자 `url` 하나와 옵션 3개뿐인 단일 명령 CLI다.
- 출력 JSON의 `content`에 변환 결과 전문이 실린다. `--output`을 주면 같은 내용을 파일로도 저장한다.
- **브라우저를 띄우는 도구다** — 네트워크 요청과 프로세스 기동이라는 부수효과가 있으므로 사용법 확인 목적으로는 `--help`만 실행한다.

## 의존성 3단

| 단계 | 확인 주체 | 미충족 시 |
|------|----------|----------|
| `~/.opal/.venv` 존재 | `run.sh` | stderr에 `OPAL .venv not found...` JSON 후 exit 1 |
| `playwright` 패키지 import 가능 | `run.sh` (`python -c "import playwright"`) | stderr에 `playwright not installed in .venv...` JSON 후 exit 1 |
| Chromium 바이너리 설치 | `main.py`(launch 시점) | stdout에 `browser not installed. Run: ~/.opal/.venv/bin/playwright install chromium` 후 exit 1 |

패키지 설치: `~/.opal/.venv/bin/pip install playwright` → 브라우저 설치: `~/.opal/.venv/bin/playwright install chromium`.

HTML → Markdown 변환은 선택 패키지에 따라 3단으로 내려간다. `markdownify`가 있으면 그것으로, 없으면 `bs4`(BeautifulSoup) 기반 자체 변환기로, `bs4`마저 없으면 정규식 태그 제거 폴백으로 처리한다. **세 경로 모두 `ok: true`를 돌려주므로 출력 품질은 설치 상태에 따라 달라진다** — 어떤 경로를 탔는지는 응답에 실리지 않는다.

## 호출 형식

```bash
~/.opal/tools/playwright-tool/run.sh <url> [--mode full|clean] [--output <path>] [--timeout <초>]
```

| 인자 | 기본값 | 설명 |
|------|-------|------|
| `url` (위치, 필수) | — | 수집할 URL |
| `--mode {full,clean}` | `full` | `full`은 `script`/`style`/`noscript`/`iframe`만 제거. `clean`은 여기에 더해 `nav`/`header`/`footer`/`aside`와 `role="navigation"`·`"banner"`·`"contentinfo"` 요소를 제거한다 |
| `--output <PATH>` | 없음 | 지정 시 변환 결과를 이 경로에 UTF-8로 저장한다(상위 디렉토리는 자동 생성). 미지정 시 `path`가 `null` |
| `--timeout <초>` | `30` | 페이지 로딩 타임아웃(초). 내부적으로 ms로 환산해 `page.goto`에 전달 |

## 산출물 형식

저장 파일과 응답 `content`는 동일하며, 헤더 메타 블록 뒤에 본문이 온다.

```markdown
# <페이지 title>

> 소스: <url>
> 캡처일: <로컬 시각 YYYY-MM-DD HH:mm>
> 추출 방식: playwright-tool CLI
> 추출 모드: <full|clean>

---

<변환된 본문>
```

`캡처일`은 KST 고정이 아니라 **실행 호스트의 로컬 시각**이다(`datetime.datetime.now()`).

## 출력 형식

```json
// 성공
{"ok": true, "url": "...", "mode": "full", "path": "/abs/path.md 또는 null", "content": "..."}

// 실패
{"ok": false, "url": "...", "error": "<사람이 읽는 메시지>"}
```

## 사용 예시

```bash
# stdout JSON으로만 받기
~/.opal/tools/playwright-tool/run.sh https://example.com/docs

# 본문만 추출해 파일로 저장
~/.opal/tools/playwright-tool/run.sh https://example.com/docs \
  --mode clean --output ./docs/refs/example.md

# 느린 페이지 — 타임아웃 연장
~/.opal/tools/playwright-tool/run.sh https://example.com/heavy --timeout 60
```

## 오류 코드

**선언 목록 없음.** `error` 값은 안정 식별자가 아니라 **사람이 읽는 자유 문자열**이다. 소스에 `ERROR_CODES` 같은 카탈로그가 없고, 각 실패 지점이 메시지를 직접 구성한다. 호출자는 `error` 문자열을 키로 분기하지 말고 `ok` 필드만 판정에 쓴다.

실제로 방출되는 메시지 계열은 다음과 같다(문면은 고정 계약이 아니다).

| 상황 | 메시지 계열 |
|------|-----------|
| `playwright` 모듈 부재 | `playwright module not found. Run: ...` |
| Chromium 미설치 | `browser not installed. Run: ...` |
| 브라우저 기동 실패(그 외) | `browser launch failed: <원문>` |
| 로딩 타임아웃 | `timeout: page load exceeded <N>s` |
| DNS 해석 실패 | `DNS resolution failed: <url>` |
| 변환 실패 | `content extraction failed: <원문>` |
| `--output` 쓰기 실패 | `file write failed: <원문>` |

## 종료 코드

| 코드 | 의미 |
|------|------|
| `0` | 성공 — 변환 결과 JSON 출력 |
| `1` | 수집·변환·저장 실패(위 표 전건), 그리고 `run.sh`의 venv·패키지 선검사 실패 |
| `2` | argparse 인자 오류(위치 인자 `url` 누락, `--mode` 도메인 위반 등) |

exit 2 경로는 argparse 기본 동작이므로 **JSON이 아닌 usage 텍스트를 stderr로 출력한다.** `ok` 키를 기대하는 호출자는 이 경로를 별도로 처리해야 한다.

## 제약

- **단일 URL 전용이다.** 여러 URL을 한 번에 처리하는 인자가 없으므로 호출자가 URL마다 프로세스를 나눠 호출한다.
- 대기 조건이 `networkidle` 고정이라 폴링·스트리밍이 계속되는 페이지는 `--timeout`까지 기다렸다가 타임아웃으로 실패한다.
- 인증·쿠키·헤더 주입 인자가 없다 — 로그인이 필요한 페이지는 수집할 수 없다.
- `content`가 응답 JSON에 통째로 실리므로, 큰 페이지에서는 stdout 크기가 그대로 문서 크기만큼 커진다. 파이프로 소비할 때는 `--output`을 함께 쓰는 편이 안전하다.
