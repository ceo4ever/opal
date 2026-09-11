# OPAL 부트스트래퍼 (Claude Code)

> 이 문서의 코드 블록은 설치 시 `~/.claude/CLAUDE.md`의 OPAL 마커 구간에 삽입된다.

```markdown
## OPAL AI Agent — 이벤트 부트스트랩

**[MUST] 아래 순서를 바꾸거나 생략하지 않는다.**

1. `~/.opal/setting.json`과, 현재 프로젝트에 있으면
   `.opal/setting.local.json`을 읽고 로컬 우선으로 병합한다. 둘 다 없거나 파싱에
   실패하면 bootstrap은 활성으로 간주한다.
2. effective setting의 `bootstrap`이 정확히 `off`이면
   `session.disabled`다. 설정 게이트 뒤 OPAL 문서를 하나도 읽지 않고,
   부트스트랩 보고 없이 실제 요청을 순수 처리한다.
3. 그 외에는 사용자 메시지의 첫 줄만 판정한다.
   - 정확히 `[WORKER]`: `session.worker`. 전역 OPAL 부트를 전부 생략하고 다음
     줄부터 처리한다. 후속 `worker.dispatch` 이벤트 로드는 허용한다.
   - 정확히 `[ASSISTANT]`: `session.assistant`. 프로젝트 안에서도 PM 승격과
     project brief를 억제한다.
   - 마커가 없고 프로젝트 루트에 `.opal/AGENT.md`가 존재:
     `session.project`.
   - 그 외: `session.assistant`.
4. `session.assistant`는 아래 명령을 실행하고 성공 응답의
   `documents[].content` 전문을 모두 적용한다.

   `~/.opal/tools/event-loader/run.sh load --event session.assistant --project-root <project-root>`
5. `session.project`는 4번을 먼저 수행한 뒤 같은 loader로
   `session.project`를 load한다. 프로젝트 `.opal/AGENT.md`,
   `docs/PROJECT.md`, PM·harness 문서는 읽지 않는다. `.opal/MEMORY.json`이
   있으면 아래 bounded 출력만 추가한다.

   먼저 상태 요약을 실행한다.

   `~/.opal/tools/state-tool/run.sh boot-summary <project-root>`

   상태 요약이 성공한 뒤 메모리 검토 후보를 조회한다.

   `~/.opal/tools/memory-tool/run.sh show --file <project-root>/.opal/MEMORY.json --boot-brief --max-bytes 1024 --memories 3 --history 0`

   두 명령의 성공한 JSON 결과만 사용해 첫 응답에 조건부로 `이어보기`(진행 중
   작업 최대 1건: 제목·단계·다음 행동)와 `우선 검토`(review_rows 최대 2건:
   제목·요약) 블록을 렌더링한다. 두 결과가 모두 비어 있거나 MEMORY.json이
   없으면 기존 짧은 응답을 유지한다. 두 블록과 JSON은 합쳐 UTF-8 1,024바이트
   이내로 결정론적으로 축약하며, 실패·파싱 오류 결과는 버린다. 이 조회와
   렌더링은 `session.project`에서만 수행한다.
6. loader 실패나 필수 문서 누락 시 OPAL 활성화를 중단하고 오류를 보고한다.

프로젝트 존재만으로 PM을 활성화하지 않는다. 프로젝트 작업이나 `//` 커맨드는 로드된
AGENT.md의 `pm.activate` 계약을 따른다.
```
