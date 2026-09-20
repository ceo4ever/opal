# E2E 여정·조각 작성 계약

## 여정

Markdown 문서 안에 fenced YAML 한 벌을 둔다. 최소 필드는 `id`, `profile`,
`required_fidelity`, `surface_ref`, `steps`, `assertions`, `required_evidence`다.

```yaml
id: login-to-dashboard
profile: browser
required_fidelity: real-usage
surface_ref: console.login
steps:
  - {fragment: login, with: {id_ref: E2E_USER, pw_ref: E2E_PASSWORD}}
assertions:
  - {id: dashboard-visible, verifier: dom_text, target: h1, expected: Dashboard, match: equals}
required_evidence: [actions, screenshot, metadata]
```

## 조각

조각은 `id`, `params`, `steps`와 하나 이상의 `postconditions`를 가져야 한다.
조각끼리 참조하지 않으며 여정만 조각을 참조한다.

```yaml
id: login
params: [id_ref, pw_ref]
steps:
  - {kind: fill, target: "#id", value_ref: "{id_ref}"}
  - {kind: fill, target: "#password", value_ref: "{pw_ref}"}
  - {kind: click, target: "button[type=submit]"}
postconditions:
  - {verifier: url, expected: /dashboard, match: equals}
```

`fill`·`type`에 `value` 원문을 두지 않는다. 자격증명과 개인 정보는 환경 변수 이름을
가리키는 `value_ref`로만 선언한다. 사후 조건이 없는 조각은 등록 대상이 아니다.

## 확인 체크리스트

- 사용자가 달성하려는 결과와 `surface_ref`가 일치한다.
- 모든 step의 target과 모든 assertion의 expected가 사용자의 확인을 받았다.
- 입력 비밀값은 `value_ref`만 사용한다.
- 조각은 하나 이상의 사후 조건을 가진다.
- 승격 전 같은 journey id의 완전한 pass 증적을 `e2e promote-check`가 확인했다.
