# login-to-dashboard

프로젝트 로그인 조각을 사용해 대시보드에 도달하는 기준 여정이다.

```yaml
id: login-to-dashboard
surface_kind: browser
profile: browser
actors: [browser]
required_evidence: [metadata, actions]
steps:
  - fragment: login
    with:
      id_ref: OPAL_E2E_LOGIN_ID
      pw_ref: OPAL_E2E_LOGIN_PASSWORD
      entry_url: /login
assertions: []
```
