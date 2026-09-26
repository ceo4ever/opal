# 태스크 143 EXECUTE 이탈·결함 기록

CLOSE 시 DONE.md에 흡수할 원본 기록이다.

## PLAN 이탈 1건

**D-1. `dashboard/frontend/vite.config.ts` 수정 (PLAN 변경 대상 외)**

- PLAN W-4의 변경 대상은 `SkillDocsPage.tsx`·`types.ts`·`router.tsx`와 기존 2화면 삭제였고, `vite.config.ts`는 어디에도 없었다.
- 그럼에도 수정한 이유: AC-9(설치본 실측)와 S-13의 "새로고침·URL 직접 접근" 항목이 이 수정 없이는 구조적으로 통과할 수 없다. 화면 자체가 뜨지 않았다.
- 변경: `base: './'` → `base: '/'` (주석으로 사유 명시)
- 사후 검증: DEC-8 6단계 전량 재실행 통과(pytest 439, node --test 23/23, npm test 153, typecheck·lint·build exit 0).

## 실측으로 발견한 결함 1건

**F-1. 2단 경로에서 자산 로드 실패로 OPAL Docs 화면 백지**

- 증상: `http://127.0.0.1:7823/docs/skills` 직접 접근 시 빈 화면. 콘솔 오류
  `Failed to load module script: Expected a JavaScript-or-Wasm module script but the server responded with a MIME type of "text/html" @ /docs/assets/index-*.js`
- 원인: `vite.config.ts`의 `base: './'`. 산출 `index.html`이 자산을 `./assets/...`로 참조하는데, `/docs/skills`는 Console에서 **유일한 2단 경로**라 브라우저가 `/docs/assets/...`로 해석한다. 그 경로는 SPA fallback이 index.html(HTML)을 돌려주고, 모듈 스크립트 MIME 검사에 걸려 앱이 부팅되지 않는다.
- 나머지 7개 화면(`/projects`·`/tasks`·`/memory`·`/doctor`·`/brain`·`/settings`·`/`)은 전부 1단 경로라 `./assets/`가 우연히 `/assets/`로 맞아떨어져 정상 동작했다.
- **혼입 시점**: `base: './'`는 태스크 115에서 들어왔고, 2단 경로는 태스크 140이 처음 도입했다. 즉 **태스크 140 이후 OPAL Docs 화면은 URL 직접 접근·새로고침에서 한 번도 뜬 적이 없다.**
- **왜 140에서 잡히지 않았나**: 메뉴 클릭으로 진입하면 클라이언트 라우팅이라 자산을 다시 받지 않는다. 화면이 보이므로 정상으로 보였다. 140의 검증이 메뉴 경유 확인에 머물렀고 URL 직접 접근을 실측하지 않았다.
- 수정: `base: '/'`. 재배포 후 콘솔 오류 0, 9개 항목 전량 통과 확인.

## 자동 검증이 놓친 이유 (개선 후보 근거)

- 백엔드 439건·프런트 153건 전부 GREEN인 상태에서도 **화면은 뜨지 않았다**. 단위·통합 테스트는 컴포넌트를 직접 마운트하므로 번들 자산 경로를 검증하지 않는다.
- S-11(회귀 6단계)도 `npm run build`의 exit code만 보았고 **산출 `index.html`의 자산 경로를 보지 않았다**.
- 실제로 잡아낸 것은 S-13 real-usage 실측 하나뿐이다. RED-first와 전수 단언을 모두 통과한 태스크가 배포 후 백지였다는 사실이 기록될 가치가 있다.

## 미해결

- **불안정 테스트 1건**: W-4 직후 `npm test`에서 1건이 실패했으나 이후 총 8회 실행에서 재현되지 않았고 이름을 잡지 못했다. 원인 미확정.
- **`ownership-tool` 훅**: `~/.claude/settings.json`이 이 저장소에 없는 `ownership-tool`을 PreToolUse(`Edit|Write|NotebookEdit|Bash`)와 SessionStart에서 참조한다. 파일이 없어 훅이 오류로 끝나고 해당 도구가 전부 차단된다. install이 `~/.opal`을 재구성할 때마다 재발한다. 이번에는 빈 스텁 파일로 넘겼다(근본 해결 아님).
- **Stop 훅 탈출구 부재**: `transition_action=continue`만 보고 차단하므로, 도구가 전부 막혀 실제로 진행 불가능한 세션에서도 계속 진행을 요구한다.
