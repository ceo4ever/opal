# date

> KST(Asia/Seoul) 기준 날짜·시각 문자열을 표준출력으로 내보내는 무의존 유틸리티
> 소스: `opal/tools/date/date.js` | 배포: `~/.opal/tools/date/date.js`
> 의존성: Node.js만 (`Intl.DateTimeFormat` 사용, 외부 패키지 0건)

## 개요

`date.js`는 시스템 로컬 타임존과 무관하게 **항상 `Asia/Seoul` 기준** 시점 문자열 하나를 stdout에 출력한다. OPAL의 다른 도구(`backlog-tool`·`brain-tool` 등)가 시점 기록이 필요할 때 subprocess로 호출하는 공용 시점 취득 창구다.

- **`run.sh` 래퍼가 없다** — 소스 트리와 배포 트리 모두 `date.js` 단일 파일이며 `node`로 직접 호출한다.
- 출력은 JSON이 아니라 **개행으로 끝나는 평문 한 줄**이다. 다른 OPAL 파이썬/노드 도구의 단일라인 JSON 계약을 따르지 않는다.
- 파일을 읽거나 쓰지 않으며 인자 외의 입력을 받지 않는다.

## 호출 형식

```bash
node ~/.opal/tools/date/date.js [format]
```

개발 중에는 소스 경로로 직접 호출한다.

```bash
node opal/tools/date/date.js [format]
```

## 포맷 인자 (4종)

| `format` | 출력 | 예시 |
|----------|------|------|
| `yymmdd` | `YYMMDD` | `260409` |
| `date` | `YYYY-MM-DD` | `2026-04-09` |
| `datetime` | `YYYY-MM-DD HH:mm` | `2026-04-09 10:29` |
| `datetime-sec` | `YYYY-MM-DD HH:mm:ss` | `2026-04-09 10:29:07` |

시각은 24시간제(`hour12: false`)이며 모든 구성요소가 2자리로 zero-padding된다(`yymmdd`의 연도는 4자리 연도의 뒤 2자리).

`datetime`(분 해상도)과 `datetime-sec`(초 해상도)은 별개 포맷으로 공존한다 — 초가 필요한 소비자만 `datetime-sec`을 요청하고, 기존 분 해상도 소비자의 출력은 바뀌지 않는다.

## 사용 예시

```bash
# 태스크 폴더명용 날짜 (예: 131-260914-...)
node ~/.opal/tools/date/date.js yymmdd
# → 260914

# 문서 본문 표기용
node ~/.opal/tools/date/date.js date
# → 2026-09-14

# 로그·이력 기록용 (분)
node ~/.opal/tools/date/date.js datetime
# → 2026-09-14 01:02

# 실행 ledger 등 초 해상도가 필요한 소비자
node ~/.opal/tools/date/date.js datetime-sec
# → 2026-09-14 01:02:07
```

셸 변수로 받을 때:

```bash
NOW="$(node ~/.opal/tools/date/date.js datetime)"
```

## 오류 코드

**선언 목록 없음.** 이 도구는 오류 코드 식별자를 정의하지 않으며, `ok`/`error` 필드를 가진 JSON을 출력하지 않는다.

## 종료 코드

| 코드 | 조건 |
|------|------|
| `0` | 모든 경우 |

인자를 생략하면 사용법을 stdout에 출력하고 exit 0으로 끝난다. **미지원 포맷 문자열을 주어도 실패로 끝나지 않는다** — `미지원 포맷: <입력>` 한 줄과 사용법을 stdout에 출력한 뒤 역시 exit 0으로 끝난다.

## 주의 — 종료 코드로 성공을 판정할 수 없다

`date.js`는 잘못된 인자에도 exit 0을 돌려주므로, 호출자는 **종료 코드 대신 stdout 내용을 검증해야 한다.** 오타난 포맷을 넘기면 시점 문자열 대신 사용법 여러 줄을 받게 되며, 그 값을 그대로 파일명이나 타임스탬프에 쓰면 조용히 오염된다. 호출자는 다음 중 하나를 택한다.

- 넘기는 포맷 문자열을 위 4종 중 하나로 고정한다.
- 받은 값이 기대 형식(예: `^\d{4}-\d{2}-\d{2}`)과 일치하는지 확인한 뒤 사용한다.

또한 stderr로는 아무것도 출력하지 않는다 — 사용법도 오류 안내도 전부 stdout이다.
