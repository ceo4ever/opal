# RED-EVIDENCE-ADD2: 한글 헤더 창문 단위 비대칭 회귀 테스트 RED 증거

> 추가작업 번호: **ADD-2** | 일시: 2026-09-05 15:30~15:52 (KST)
> 근거: `ADD_DONE-1.md` §이월 **1-a** — "이 결함의 회귀 테스트 미신설"
> 작성자: `opal-test-agent` (H-9 검증 2원화 — ADD-1 구현자 `opal-be-agent`와 분리된 주체)
> 대상 파일: `opal/tools/code-scan/tests/test-validate.js` (기존 파일 확장, 신규 파일 생성 없음)

---

## 1. 고정 대상 결함

`code-scan.js`가 같은 상수 `HEADER_READ_BYTES`를 두 경로에서 다른 단위로 해석했다.

| 경로 | 교정 전 코드 | 단위 |
|------|------------|------|
| 라이브 파일 읽기 | `readFileHead` — `Buffer.alloc(N)` + `readSync` | **바이트** |
| HEAD 비교 읽기 | `classifyUncovered` — `head.content.slice(0, N)` | **문자**(UTF-16) |

교정 전 상수는 `8192`. 한글은 UTF-8 3바이트 / UTF-16 1유닛이므로 문자 창문이 바이트 창문의 약 3배를
담는다. `@header` 블록 종료가 두 창문 **사이**에 놓이면 라이브는 "헤더 미보유"·HEAD는 "헤더 보유"로
읽어 `classifyUncovered`의 「HEAD에 있었는데 지금 없다 = 회귀」 규칙에 걸리고, 워킹 사본과 커밋 사본이
**바이트 단위로 완전히 동일**해도 거짓 `newly_uncovered`(exit 2)가 난다.

교정 현행(`dd09b9f`):
- `code-scan.js:45` — `const HEADER_READ_BYTES = 24576;`
- `code-scan.js:1106` — `Buffer.from(head.content, 'utf8').subarray(0, HEADER_READ_BYTES).toString('utf8')`

---

## 2. RED 재현 방법 (mock 미사용 — 실 CLI · 실 git · 실 파일)

교정 전 코드를 스크래치패드에 복원하고, **신설한 테스트 코드 자체**를 그 복원본에 대해 실행했다.
테스트를 개조하지 않기 위해 `test-validate.js`의 CLI 해석 경로(`path.resolve(__dirname,'..','code-scan.js')`)를
그대로 이용해 임시 트리를 구성했다.

```
git show dd09b9f~1:opal/tools/code-scan/code-scan.js > <scratch>/code-scan.prefix.js
cp -R opal/tools/code-scan/tests <scratch>/redroot/tests
cp <scratch>/code-scan.prefix.js  <scratch>/redroot/code-scan.js
cd <scratch>/redroot/tests && node --test --test-reporter=spec test-validate.js
```

복원본 확인 (`git stash` 미사용 — 작업 트리 무변경):

```
39:const HEADER_READ_BYTES = 8192;
1092:  const headSlice = head.content.slice(0, HEADER_READ_BYTES);
```

### 픽스처 (경계를 한글 문자 중간에 놓도록 정밀 제어)

임시 git 레포 1개를 4파일이 공유한다. `.opal/code-scan.json`은 `headerSource:'inline'` ·
`extensions:['.java']` · `scopes:{svc:'svc/'}`. c1/c2/c3는 **커밋 후 워킹 사본을 건드리지 않아**
워킹 == 커밋(바이트 동일)이며, 대조군만 워킹 사본에서 헤더를 제거했다.

| 픽스처 | 닫는 `}` 바이트 | 닫는 `}` 문자 | 파일 크기 | 24576 바이트 경계가 한글 중간을 자름 |
|--------|---------------:|-------------:|---------:|:---:|
| `HanWinIn.java` (c1) | **24001** | **8097** | 24601 | true |
| `HanWinOut.java` (c2) | 25002 | 8432 | 25051 | true |
| `HanWinEdge.java` (c3) | 24585 | 8295 | 24635 | true |
| `HanRegressCtl.java` (대조군) | 24002 | 8104 | 24601 | true |

c1이 판별 케이스다 — 바이트 24001은 **교정 후 창문(24576) 안**, 문자 8097은 **교정 전 문자 창문(8192) 안**,
바이트 24001은 **교정 전 바이트 창문(8192) 밖**. 즉 라이브는 못 보고 HEAD만 보는 정확한 지점이다.

---

## 3. RED 실행 출력 (교정 전 코드 · 실관측)

### 3.1 신설 테스트 4건 전건 실패

```
✖ [T106/ADD-2] c1: @header 블록이 창문 **안**에서 종료 + 워킹==커밋 → covered · exit 0 · newly_uncovered 0 (445.00725ms)
✖ [T106/ADD-2] c2: @header 블록이 창문 **밖**에서 종료 + 워킹==커밋 → pre_existing · exit 0(비차단) (0.181167ms)
✖ [T106/ADD-2] c3: 창문 경계가 JSON 블록 **내부**(닫는 `}`가 창문 밖) → end === -1 정상 null → pre_existing · exit 0 (0.148291ms)
✖ [T106/ADD-2] 불변식: 라이브 창문과 HEAD 비교 창문은 **같은 바이트 창문**을 본다(플립 지점 일치) (54.157542ms)
ℹ tests 38
ℹ pass 34
ℹ fail 4
```

기존 34건은 전건 통과 — 신설분만 정확히 실패한다(기존 계약 무손상).

### 3.2 c1 — 거짓 `newly_uncovered` 1건 · exit 2

```
AssertionError [ERR_ASSERTION]: 워킹==커밋인 파일은 회귀가 아니므로 차단되면 안 됨, got exit 2
(stdout: {"ok":false,"command":"validate","mode":"changed",
  "coverage":{"total":3,"inline":0,"manifest":0,"covered":0,"percent":0},
  "counts":{"orphan":0,"uncovered":3,...,"newly_uncovered":1,"pre_existing":2,...},
  "violations":[
    {"code":"uncovered","sub":"newly_uncovered","file":"svc/mod/HanWinIn.java","detail":""},
    {"code":"uncovered","sub":"pre_existing","file":"svc/mod/HanWinOut.java","detail":""},
    {"code":"uncovered","sub":"pre_existing","file":"svc/mod/HanWinEdge.java","detail":""}],
  "skipped":[],"headerSource":"inline"})
    actual: 2,
    expected: 0,
```

→ **`newly_uncovered` 1건 · exit 2** — 요구된 RED 형태 그대로다.

### 3.3 불변식 — 플립 지점 불일치

```
AssertionError [ERR_ASSERTION]: 라이브 창문은 closeByte=24001를 본다(covered)
  + actual - expected
  +   sub: 'newly_uncovered'
    actual: { code: 'uncovered', sub: 'newly_uncovered', file: 'svc/mod/HanWinIn.java', detail: '' },
    expected: undefined,
```

### 3.4 c2·c3의 실패 사유 (관측 그대로 — 기대와 다른 부분)

c2·c3는 **자기 자신의 오분류 때문에 실패한 것이 아니다.** 교정 전에도 두 파일의 `sub`는
정상적으로 `pre_existing`이다(c2 문자 8432 > 8192, c3 문자 8295 > 8192 — 교정 전 문자 창문에도
안 들어간다). 두 케이스가 실패한 것은 c1과 **하나의 `validate --changed` 실행을 공유**하므로
c1의 거짓 차단이 공유 exit code를 2로 만들기 때문이다.

파일별 단독 실행으로 분리 관측한 결과(교정 전 코드):

```
--- HanWinIn ---   {"newly_uncovered":1,"pre_existing":0}  violations:[{sub:"newly_uncovered"}]  exit=2
--- HanWinOut ---  {"newly_uncovered":0,"pre_existing":1}  violations:[{sub:"pre_existing"}]     exit=0
--- HanWinEdge --- {"newly_uncovered":0,"pre_existing":1}  violations:[{sub:"pre_existing"}]     exit=0
```

→ **결함의 판별면은 c1 단독이다.** c2·c3는 교정 전후 `sub`가 동일한 **경계 대조군**으로,
"창문 밖이면 양 경로 모두 못 본다"·"절단 U+FFFD가 `}`로 오인되지 않는다"는 비차단 계약을 고정한다.
`ADD_DONE-1.md`의 c2/c3 명세("`pre_existing` · exit 0")는 교정 후 상태를 서술한 것이며 RED 판별
케이스로 지정된 것은 c1뿐이다 — 관측이 명세와 정합한다.

### 3.5 대조군 — 진짜 회귀는 교정 전에도 검출된다 (테스트 무력화 아님 확인)

```
--- 회귀 대조군 (교정 전) ---
{"counts":{"newly_uncovered":1,"pre_existing":0,...},
 "violations":[{"code":"uncovered","sub":"newly_uncovered","file":"svc/mod/HanRegressCtl.java"}]}
exit=2
```

대조군은 교정 전·후 모두 `newly_uncovered`다. 이 케이스의 역할은 문자/바이트 비대칭 검출이 아니라
**HEAD 창문이 라이브 창문보다 좁아지는 방향(미탐)** 을 막는 것이다 — HEAD 창문이 8192바이트로
축소되면 이 대조군이 `pre_existing`으로 미탐되어 실패한다.

---

## 4. GREEN 확인 (교정 후 현행 코드)

```
✔ [T106/ADD-2] c1: ... → covered · exit 0 · newly_uncovered 0 (429.032709ms)
✔ [T106/ADD-2] c2: ... → pre_existing · exit 0(비차단) (0.128584ms)
✔ [T106/ADD-2] c3: ... → end === -1 정상 null → pre_existing · exit 0 (0.118125ms)
✔ [T106/ADD-2] 불변식: 라이브 창문과 HEAD 비교 창문은 **같은 바이트 창문**을 본다(플립 지점 일치) (52.546708ms)
ℹ tests 38
ℹ pass 38
ℹ fail 0
```

c1 교정 후 실행 결과(3파일 공유 실행):

```
exit 0
coverage {"total":3,"inline":1,"manifest":0,"covered":1,"percent":33.3}
counts   {"uncovered":2,"newly_uncovered":0,"pre_existing":2,...}
violations [{"sub":"pre_existing","file":"svc/mod/HanWinOut.java"},
            {"sub":"pre_existing","file":"svc/mod/HanWinEdge.java"}]
```

| 케이스 | 교정 전(8192·문자) | 교정 후(24576·바이트) |
|--------|-------------------|----------------------|
| c1 `HanWinIn` | `newly_uncovered` · **exit 2** | **covered** · exit 0 |
| c2 `HanWinOut` | `pre_existing` · exit 0 | `pre_existing` · exit 0 |
| c3 `HanWinEdge` | `pre_existing` · exit 0 | `pre_existing` · exit 0 |
| 대조군 `HanRegressCtl` | `newly_uncovered` · exit 2 | `newly_uncovered` · exit 2 |

---

## 5. 임시 자원

`<scratch>/add2/` (`code-scan.prefix.js` · `redroot/` · `baseline/` · `proto.js`) 및 픽스처
임시 git 레포는 검증 종료 후 전량 삭제했다. 저장소 git 상태는 변경하지 않았다(`git stash` 미사용).
