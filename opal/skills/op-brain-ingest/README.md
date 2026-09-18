# op-brain-ingest

> 이 스킬은 사용자가 직접 호출하지 않습니다. CLOSE 단계 파일럿(`opal-pilot-project` 등)이 DONE.md 생성 직후 디스패치합니다.

완료된 태스크의 산출물을 프로젝트 brain(`.opal/brain/`)에 자동 누적하는 CLOSE 단계 경량 워커입니다.

## 역할

DONE.md·PLAN.md·TASK.md를 읽어 아키텍처 결정, 신규 컴포넌트, 인터페이스 변경, 도메인 지식, 흐름 변경, 신규 업무 용어(term 채택 프로젝트만) 중 ingest 대상을 판별하고 brain 페이지(concept/entity/flow/term 등)를 작성합니다. **단방향**이며 brain 페이지 작성만 수행하고 기존 코드·문서를 역수정하지 않습니다. 오타·trivial 변경·중복·미실체(향후 계획·미확정 설계) 지식은 제외합니다.

`.opal/brain/`이 없는 프로젝트에서는 즉시 no-op(`status: skipped`)로 CLOSE를 막지 않습니다.

## 입력

- 태스크 폴더 경로 (DONE.md·PLAN.md·TASK.md가 있는 디렉토리)

## 출력

- `.opal/brain/pages/{type}/*.md` 신규·갱신 페이지 (frontmatter 필수: `type`/`title`/`created`/`updated`/`status`/`sources`)
- `brain-tool add-page`/`update-page` → `index` → `log` 순서로 집행 (index/log는 brain-tool로만 갱신, LLM 직접 편집 금지)
- 반환: `{ ingested_pages, status, summary }` (`status`: `completed` / `skipped` / `completed_with_errors`)

## 호출 시점

CLOSE 단계 파일럿이 DONE.md 생성 직후 디스패치합니다. brain 부재나 brain-tool 에러는 CLOSE를 중단시키지 않고 skip-and-continue로 처리합니다.

## 관련 문서

- `opal/core/references/harness/citation-rules.md` §8 (비즈니스 용어 우선), §8.9 (헤딩 형식)
- `.opal/brain/templates/schema-template.md` §1.5 (페이지 타입 동적 로드)
