# ego-browser-tool

Ego Lite를 OPAL 브라우저/E2E 후보로 연결하는 JSON CLI다. 앱은 OPAL에 번들하지 않으며, macOS에서 사용자가 `r2` 설치를 선택한 경우에만 고정 DMG를 내려받아 `hdiutil`, SHA-256, `codesign`, `spctl` 검증 후 `~/Applications`에 설치한다. quarantine 속성은 제거하지 않는다.

```bash
run.sh status
run.sh install
run.sh smoke https://example.com --expect-text "Example Domain"
run.sh smoke https://example.com --expect-text "Example Domain" --install-choice manual|r2|cancel
```

미설치 상태는 `awaiting_human`과 `manual`·`r2`·`cancel` 선택, 원래 URL/assertion을 포함한 resume 정보를 반환한다. 명시적 `cancel`과 비지원 플랫폼만 `provider_unavailable`이며, 그때만 상위 test-tool이 cmux 또는 Playwright로 전환한다.

Ego Lite는 개인·비상업 단일 사용자 선택 공급자다. 조직·상업 사용 전 Citro Enterprise 조건을 확인해야 한다. 저장 비밀번호, cookie, token은 이 도구의 출력 계약에 포함되지 않는다.
