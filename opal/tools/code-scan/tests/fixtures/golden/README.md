# golden 픽스처 — 재캡처 근거

> Task 080 §3.7.3 골든 재캡처 설계. 캡처 명령·설정 조건과 재캡처 결과를 담는다.
> 재캡처는 Task 080 Step 13에서 실행 완료됐다 (2026-08-02, `code-scan` v1.4.0).

## 캡처 대상

`legacy-repo` (`.opal/code-map/index.json` 부재 — inline-only 픽스처)

## 캡처 시 픽스처 설정 전문

`opal/tools/code-scan/tests/fixtures/legacy-repo/.opal/code-scan.json`:

```json
{
  "headerSource": "inline",
  "scopes": {
    "be": "be/",
    "fe": "fe/"
  },
  "extensions": [".py", ".ts"],
  "exclude": ["node_modules", "__pycache__", ".git"],
  "excludePatterns": []
}
```

## 캡처 명령

```bash
cd opal/tools/code-scan/tests/fixtures/legacy-repo
for c in "scan --json:scan.json" "domain:domain.txt" "layer:layer.txt" \
         "search auth --json:search.json" "exports token --json:exports.json" \
         "summary:summary.txt" "depends auth_service:depends.txt" "missing:missing.txt"; do
  node ../../../code-scan.js ${c%%:*} > ../golden/${c##*:}
done
```

## 예측 결과 — 바이트 차이 0

| 근거 | 설명 |
|------|------|
| ① | `legacy-repo`에는 `.opal/code-map/index.json`이 없다 (`find` 결과 미검출) |
| ② | 구 코드는 `auto` + `!ctx.codeMap.present` → `extractHeader` 결과를 그대로 반환했다 (`code-scan.js:699-701`) |
| ③ | 신 코드는 `inline` 모드 → `extractHeader` 결과를 그대로 반환한다 (§3.3.2 (A)) |
| ④ | `include`/`exclude` 미설정이므로 `isInScope`는 항상 true (§3.2.2 (B)) |

`git diff --stat opal/tools/code-scan/tests/fixtures/golden/`가 비어 있으면 정상이다. 바이트가 달라지면 조회 경로에 의도치 않은 회귀가 발생한 것이므로 원인을 규명한다(H-10) — GREEN 완료 조건으로 삼지 않는다.

## 077 골든 대비 diff 결과

**결론: 차이 0 — 골든 8종 전부 077 캡처본과 바이트 동일.** 예측(H-10)이 그대로 성립했다.

재캡처 실행일 2026-08-02 · `code-scan` v1.4.0 · 8커맨드 전부 exit 0.

`git diff --stat`이 **빈 출력**이었다 (추적 파일 8종 중 변경 0건):

```
$ git diff --stat opal/tools/code-scan/tests/fixtures/golden/
$ git status --porcelain opal/tools/code-scan/tests/fixtures/golden/
?? opal/tools/code-scan/tests/fixtures/golden/README.md
```

`README.md`만 untracked로 잡히는데 이는 Task 080 Step 1에서 신규 추가된 이 문서 자신이며, 골든 산출물 8종과 무관하다.

빈 diff가 "캡처가 실행되지 않아서"가 아님을 3중으로 교차 확인했다:

| 확인 | 방법 | 결과 |
|------|------|------|
| 파일이 실제로 재기록됐다 | 캡처 전후 mtime 대조 | 8종 전부 `14:59:18~19`로 갱신됨 (077 캡처본은 `07-28 14:40`) |
| 내용이 동일하다 | 캡처 전후 `shasum -a 256` 대조 | 8종 해시 전부 불변 |
| 내용이 동일하다 (독립 경로) | 캡처 전 사본을 떠 두고 `diff -r` | 차이 0, exit 0 |

차이가 0인 근거는 위 "예측 결과" 표 ①~④와 같다. 추가로 이번 재캡처에서 실측 확인한 사항:

| 항목 | 실측 | 의미 |
|------|------|------|
| `legacy-repo`의 `.opal/code-map/index.json` | 부재 (`find` 미검출) | 근거 ① 재확인 — inline 외 소스가 애초에 없다 |
| `scan.json`의 `_source` 키 | 0건 | `inline` 모드는 `_source`를 부착하지 않는다 (§3.3.2 (A), TS-064) |
| 골든 8종의 버전 문자열 | 0건 | v1.3.x → v1.4.0 승격이 골든에 새지 않는다 |
| 골든 8종의 `validate` 출력 | 미포함 (캡처 대상 8커맨드에 `validate` 없음) | Task 080이 바꾼 `validate`의 `headerSource` 필드 신설·커버리지 합산 폐기가 골든에 닿지 않는다 |

마지막 항목이 "차이 0"의 핵심이다. Task 080의 출력 변경은 `validate` 계열에 국한되는데 골든 캡처 대상은 조회 8커맨드(`scan`/`domain`/`layer`/`search`/`exports`/`summary`/`depends`/`missing`)뿐이라, 변경면과 캡처면이 겹치지 않는다.
