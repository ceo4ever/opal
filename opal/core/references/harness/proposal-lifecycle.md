---
module: proposal-lifecycle
role: CLOSE 시점 제안서 아카이브 판정의 단일 SSOT
load: stage.close
---

# 제안서 아카이브 판정 (CLOSE 스텝)

제안서는 소비형 입력물이며 규범 SSOT가 될 수 없다. 적용된 규칙의 원문은 해당
스킬·에이전트·harness owner 문서가 소유한다. 이 스텝은 적용 완료된 제안서가
`docs/proposals/`에 남아 SSOT처럼 인용되는 상태를 CLOSE에서 걷어낸다.

## 발동 조건

이번 태스크의 TASK.md·PLAN.md 참조 문서 또는 `changed_files`에 `docs/proposals/`
하위 파일이 포함되면 발동한다. 포함되지 않으면 자연 스킵(no-op)이다.

`docs/proposals/`가 없는 프로젝트에서도 자연 스킵한다. 이 스텝은 CLOSE를 차단하지
않는다.

## 절차

1. 소비한 제안서마다 잔여 인용을 판정한다. 판정은 아래 명령이 소유하며 PM이
   눈으로 세지 않는다.

   ```bash
   grep -rn "proposals/<파일명>" --include="*.md" opal/ docs/ skills/ README.md \
     | grep -v "/archives/" | grep -v "/backup/" | grep -v "^tasks/"
   ```

   `/archives/`(이관 완료분)·`/backup/`(동결 스냅샷 사본)·`tasks/`(과거 태스크 기록)는
   판정에서 제외한다. 셋 다 현재 규범을 인용하는 자리가 아니다.

2. **잔여 0건** — `docs/proposals/archives/`로 이동하고 상단 `> 상태:` 행을
   `적용완료` 또는 `폐기`로 바꾼다. 이동은 삭제가 아니다. 과거 태스크의 TASK·PLAN·
   DONE이 제안서를 근거로 인용하고 있어 원문이 사라지면 근거가 끊긴다.

3. **잔여 1건 이상** — 이동하지 않는다. 규범 문장을 owner 문서로 먼저 이관해야
   하므로, DONE.md에 파일별 잔여 건수와 이관 대상 경로를 기록하고 CLOSE를 진행한다.

4. 이동한 제안서가 `docs/PROJECT.md` 문서 레지스트리에 등재돼 있으면 해당 행을
   제거한다. 설계 이유(WHY)는 Project Brain이 소유하므로 brain ingest 대상으로
   넘긴다.

## 이관 판정

잔여 인용은 두 종류이며 처리가 다르다.

| 인용 형태 | 처리 |
|---|---|
| 규범 문장이 인용처에 이미 인라인으로 있음 | 출처 표기만 제거한다. 문장은 그 문서가 소유하는 자기 규칙이 된다 |
| 출처만 가리키고 본문이 없음 (`> 설계 근거: ...`) | 해당 줄을 삭제하거나 brain 페이지 참조로 교체한다 |

원문을 새 위치로 복사해 두 곳에 같은 문장을 남기지 않는다.

## 상태 어휘

`제안` · `검토` · `적용완료` · `폐기` 4종만 쓴다. 앞의 둘은 `docs/proposals/`,
뒤의 둘은 `docs/proposals/archives/`에 둔다.
