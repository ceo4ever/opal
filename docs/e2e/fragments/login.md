# login

환경 변수로 전달된 자격증명으로 로그인하고 대시보드 진입을 검증하는 재사용 조각이다.

```yaml
id: login
params: [id_ref, pw_ref, entry_url]
steps:
  - id: open-entry
    kind: navigate
    target: "{entry_url}"
  - id: open-login
    kind: click
    target: "header a.login"
  - id: fill-id
    kind: fill
    target: "#id"
    value_ref: "{id_ref}"
  - id: fill-password
    kind: fill
    target: "#pw"
    value_ref: "{pw_ref}"
  - id: submit
    kind: click
    target: "button[type=submit]"
postconditions:
  - id: dashboard-url
    verifier: url
    expected: /dashboard
    match: equals
```
