# web-to-markdown (wtm)

URL을 입력받아 웹 페이지 콘텐츠를 정제된 Markdown(.md) 파일로 변환하는 스킬.

## 개요

웹 페이지를 AI 에이전트가 바로 활용할 수 있는 형태의 `.md`로 변환합니다. 내부적으로 Ego Lite → cmux → Playwright 순서의 3단계 후보 체인으로 콘텐츠를 취득하며, 앞 단계가 지원하지 않는 경우에만 다음 단계로 넘어갑니다(오류 시에는 그대로 중단하고, 지원 불가일 때만 폴백). 복수 URL은 전용 워커 에이전트 `opal-wtm-agent`로 병렬 처리됩니다. 일반적인 공개 정보 검색에는 이 체인을 사용하지 않고 기존 web search를 그대로 사용합니다.

## 언제 쓰나

- "URL 읽어줘", "사이트 내용 정리", "웹 페이지 마크다운", "URL 마크다운 변환", "웹 페이지 가져와", "사이트 분석해줘", "링크 내용 정리해줘", "웹 콘텐츠 추출" 요청을 받았을 때
- URL을 주면서 내용을 파악하거나 정리해달라는 요청 전반

## 사용법

호출: `//wtm`

| 명령 | 설명 |
|------|------|
| `//wtm {url}` | 단일 URL 변환 (기본: full 모드) |
| `//wtm {url1} {url2} {url3}` | 복수 URL, 자동 병렬 처리 |
| `//wtm --clean {url}` | 본문만 추출 |
| `//wtm --wireframe {url}` | 와이어프레임(기획 관점) 분석 |
| `//wtm --browser {url}` | deprecated alias — 기본 동작과 동일 |
| `//wtm --surface <handle>` | 현재 브라우저 페이지(cmux surface)를 그대로 추출, navigate 안 함 |
| `//wtm --surface <handle> {url}` | surface 재사용 + 새 URL로 이동 후 추출 |
| `//wtm --wait <ms> {url}` | 추출 전 대기 시간 지정 (기본 2000ms) |

| 모드 | 설명 | 사용 시점 |
|------|------|----------|
| **full** (기본) | nav, sidebar, header, footer 등 구조 요소까지 보존 | 사이트 구조 파악, 메뉴/링크 수집, 전체 페이지 아카이빙 |
| **clean** | 비본문 요소를 제거하고 본문만 추출 | 문서/블로그 아티클 등 본문만 필요할 때 |
| **wireframe** | 화면 구조·구성요소·기능·네비게이션·데이터 I/O를 기획 관점으로 구조화 | 와이어프레임 HTML을 기획 문서로 변환할 때 |

사용자가 모드를 명시하지 않으면 full이 기본 적용되고, "본문만"/"clean" 키워드가 있으면 clean, "와이어프레임"/"기획 분석" 키워드가 있으면 wireframe이 적용됩니다. `localhost`, `127.0.0.1` 등 로컬 호스트 URL은 browser 모드가 자동 적용됩니다.

## 동작 흐름

```
URL 입력 (단일 또는 복수)
  │
  ├─ Phase 1: Ego Lite — 준비되어 있으면 이 단계에서 추출/저장
  │     미설치면 manual/r2/cancel 선택을 반환하고 대기, cancel 시에만 다음 단계로
  │
  ├─ Phase 2: cmux-tool — Ego가 지원 불가일 때 진입, 실패 시 다음 단계로 폴백
  │
  ├─ Phase 3: playwright-tool CLI — cmux도 지원 불가일 때 진입 (fallback 최종 단계)
  │
  └─ 복수 URL → opal-wtm-agent를 URL별로 병렬 디스패치 (동일 호스트 6개 이상이면 PM이 순차 수집)
```

각 단계 모두 최종 산출물은 반드시 위 "산출물 형식"을 따르는 `.md` 파일이며, 중간 산출물(.txt, .html 등)은 생성하지 않습니다.

## 산출물

| 항목 | 내용 |
|------|------|
| 파일명 | URL 기반 kebab-case slug (예: `https://docs.example.com/api/v2/auth` → `docs-example-com-api-v2-auth.md`) |
| 저장 경로 우선순위 | ① 사용자 지정 경로 ② 태스크 작업 중이면 `{task-folder}/references/{slug}.md` ③ 그 외 `/tmp/web-to-markdown/{slug}.md` |
| wireframe 모드 저장 경로 | ① 사용자 지정 ② PROJECT.md에 지정된 경로 ③ 기본값 `docs/wireframes/` (복수 URL 시 `_index.md` 자동 생성) |

산출물 상단에는 소스 URL, 캡처 일시, 추출 방식(`cmux (모드 A|B|C)` 또는 `playwright-tool CLI`), 추출 모드가 메타 정보로 기록됩니다.

완료 시 처리한 URL 개수, 각 URL의 처리 방식(성공/폴백 여부), 저장 경로를 표로 보고합니다.

## FAQ

### 인증이 필요한 페이지도 처리할 수 있나요?
Ego Lite의 사용자 로그인 세션을 활용할 수 있지만, MFA·결제·게시·삭제·설정 변경 등은 사람에게 인계됩니다.

### 매우 긴 페이지는 어떻게 되나요?
10만자를 초과하면 그 지점에서 truncate하고 안내 메시지가 추가됩니다.

### robots.txt로 차단된 사이트는요?
강제로 우회하지 않고 안내 후 중단합니다.
