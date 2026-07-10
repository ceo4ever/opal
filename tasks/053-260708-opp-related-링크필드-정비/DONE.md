# DONE: brain related 프론트매터 위키링크 정비 + validate 링크필드 집행 강화

> 완료일: 2026-07-10 | 스킬: opp | 모드: agentic
> 태스크: 053-260708-opp-related-링크필드-정비

## 결과 요약

brain 페이지 `related` 프론트매터에 손편집으로 유입된 마크다운 위키링크(`"[[...]]"`) 6항목을 평탄 슬러그로 정규화하고, 같은 오류가 재발하지 못하도록 `validate`에 링크필드 값 검사를 추가해 결정론적으로 집행한다(PRINCIPLES "enforce, don't advise"). `related` 요소가 `[[`·`]]`·`.md`를 포함하면 `frontmatter_invalid`로 거부하며, 검사 범위는 `related`로 한정해 `sources`의 정당 토큰(`task:045` 등) 오탐을 차단했다. 부수적으로 `add-page --related`(CSV→평탄 리스트) 플래그를 추가해 손편집 유인을 줄였다. 실행 중 강화된 validate가 표면화한 실 저장소 잔존 오류(R-K1 1페이지 + 추가작업 ADD-1 7페이지 24건)까지 정비하여 **실 `.opal/brain` validate clean(violations 0)** 상태로 마감했다.

## 변경 파일 (changed_files)

**코드/테스트** (RED-first)
- `opal/tools/brain-tool/brain_tool.py` — `LINK_FRONTMATTER = ["related"]` 상수(`:52`) + `validate_frontmatter` 링크필드 검사(`:304~`) + `--related` argparse·CSV 평탄화 + @header `[053]`
- `opal/tools/brain-tool/tests/test_brain_tool.py` — validate 링크필드 거부 4·통과 3 케이스 + add-page `--related` 지정/미지정 케이스 + `make_args`/`_add_page` 확장

**brain 페이지 정비 (R-1 + Step 3-b)**
- `.opal/brain/pages/entity/memory-tool.md` / `concept/fixture-vs-real-blind-spot-lesson.md` / `concept/memory-lifecycle-graduation-workflow.md` — quoted `"[[...]]"` 6항목 → 평탄 슬러그
- `.opal/brain/pages/entity/skill-opal-pilot-data-design.md` — `.md` 접미사 4항목 정규화 (R-K1 PM DECISION 승인분)

**문서 (R-6)**
- `opal/core/references/tools.md` — validate 링크필드 검사·`--related` 설명 + 변경이력 v2.1 (053)
- `.opal/brain/pages/entity/brain-tool.md` — 053 기능 추가 기술
- `.opal/brain/pages/concept/brain-validate-flatness-enforcement.md` — 034 사각지대를 053이 닫은 경위 확장 기술

**추가작업 ADD-1** (캡틴 승인, 상세 `ADD_DONE-1.md`)
- opdd 클러스터 7페이지 related `.md` 접미사 24항목 정규화 — `concept/dict-선행-model-ssot.md`, `concept/erd-modeler-deprecation.md`, `concept/opdd-design-artifacts-path-pattern.md`, `entity/op-data-{ddl,dictionary,model}-skill.md`, `flow/opdd-pipeline-flow.md`

## 검증 결과 (완료기준 a~e All Pass — PM 직접 재현)

| 기준 | 결과 |
|------|------|
| (a) 정비 페이지 related `[[`/`]]`/`.md` 0건 | PASS — grep 실측 0건, flat `list[str]` 파싱 확인 |
| (b) 원래 6건 missing_link 소거 | PASS — 강화 validate+lint 실행, 해당 페이지 잔존 0 |
| (c) `[[x]]`/`x.md` 거부 테스트 GREEN | PASS — RED 증거(구현 전 FAIL 로그) 확보 후 GREEN |
| (d) `add-page --related a,b` 평탄 리스트 | PASS — 미지정 시 기존 동작 불변 포함 |
| (e) 전체 스위트 회귀 0 | PASS — 118/118 GREEN (PM 재실행 재현) |
| (+) 실 저장소 validate | PASS — ADD-1 후 `valid: true, violations: 0` |

## 주요 의사결정·특이사항 (상세: AGENTIC-LOG.md)

1. **R-K1 scope_gap 승인 (DECISION #3)** — PLAN 워커가 TASK 미포착 4번째 페이지를 발견·에스컬레이션 → enforce 배포 시 자기모순 방지를 위해 R-1에 포함(Step 3-b).
2. **잔존 24건 에스컬레이션 → 캡틴 승인 (ESCALATION #6)** — 강화 validate가 opdd 클러스터 7페이지를 신규 표면화. R-K1 초과 스코프라 PM 자율 확장 대신 캡틴 상신 → "추가작업 즉시 정비" 선택으로 ADD-1 수행.
3. **링크필드 검사 `related` 한정** — `sources`·`tags` 제외로 오탐 차단(PLAN R-K2).
4. **본문 위키링크 `.md`(broken_link 42건 등 lint advisory)는 TASK 명시 제외** — 미조치. 필요 시 후속 태스크 분리 권장.
5. **tools.md "8 서브명령" 표기 stale(실제 10)** — TASK 범위 밖, 기록만 (PLAN R-K6).

## 후속 조치 (미수행 — 캡틴 지시 대기)

- **install 재배포** — 변경은 프로젝트 소스에만 반영됨. `~/.opal/tools/brain-tool/`(배포본)은 구버전이라 강화 검사 미적용 상태 → `scripts/install-mac.sh` 재실행 필요.
- **커밋** — 커밋 규칙에 따라 미수행 (명시 요청 시에만).
- (선택) 본문 위키링크 `.md`·broken_link 정비 별도 태스크.
