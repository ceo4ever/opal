---
name: op-dev-wireframe
description: |
  **와이어프레임 생성 단계 스킬**. TASK.md와 입력물(정책서/이미지/구두 요청)을 기반으로 wireframe-builder 스킬에 위임하여 wireframe.md를 생성한다.
  반드시 이 스킬을 사용해야 하는 상황: 오케스트레이터(opal-pilot-dev-wireframe)가 WIREFRAME 단계를 디스패치할 때.
  필수 입력: TASK.md + 입력물. 보장 출력: wireframe.md.
---

# op-dev-wireframe — 와이어프레임 생성

## 실행 컨텍스트

- **호출자**: 오케스트레이터(opal-pilot-dev-wireframe)가 WIREFRAME 단계를 디스패치
- **실행 주체**: 워커 에이전트 (dtp-wireframe-ui-agent)
- **입력**: `tasks/{NNN}-{태스크명}/TASK.md` + 입력물 (정책서/이미지/구두 요청)
- **출력**: `tasks/{NNN}-{태스크명}/wireframe.md`

## 페르소나

```
Read ~/.opal/skills/op-dev-wireframe/personas/service-planner.md
```

페르소나 파일이 없으면 다음 역할을 따른다:
- 시니어 서비스 기획자
- 사용자 관점에서 화면 구성과 흐름을 설계한다
- 기술 구현 가능성을 고려하되, UX 우선으로 판단한다

## 프로세스

### Step 1. 입력물 확인

TASK.md에서 참조하는 입력물을 확인한다:

| 입력물 유형 | 확인 방법 |
|------------|----------|
| 정책서 (.md, .docx, .pdf) | TASK.md에 명시된 경로에서 Read |
| 이미지 (.png, .jpg) | TASK.md에 명시된 경로에서 Read (시각적 확인) |
| 구두 요청 | TASK.md 본문에 포함된 요구사항 |

### Step 2. 입력물 부족 시 보완

입력물이 부족하여 wireframe.md를 작성하기 어려운 경우, interview 스킬을 연동한다:

```
Read {프로젝트}/.opal/skills/interview/SKILL.md
→ 없으면: Read ~/.opal/skills/interview/SKILL.md
```

interview 스킬로 부족한 요구사항을 수집한 후 Step 3으로 진행한다.

### Step 3. wireframe-builder 스킬에 위임

wireframe.md 생성을 wireframe-builder 스킬에 위임한다:

```
Read {프로젝트}/.opal/skills/wireframe-builder/SKILL.md
→ 없으면: Read ~/.opal/skills/wireframe-builder/SKILL.md
```

wireframe-builder 스킬의 프로세스에 따라 wireframe.md를 생성한다.

**위임 시 전달 정보**:
- TASK.md 경로
- 입력물 경로 (정책서/이미지)
- 수집된 추가 요구사항 (interview로 보완한 경우)

## 활용 스킬

| 스킬 | 용도 | 사용 시점 |
|------|------|----------|
| wireframe-builder | wireframe.md 생성 (위임) | Step 3에서 항상 사용 |
| interview | 요구사항 수집 | Step 2에서 입력물 부족 시 |

## 출력

wireframe-builder가 생성한 wireframe.md가 이 스킬의 출력이다.

**저장 경로**:
```
tasks/{NNN}-{태스크명}/wireframe.md
```

## 완료 후 동작

워커는 QA를 직접 호출하지 않는다. wireframe.md 생성이 완료되면 결과를 오케스트레이터에 반환한다. 오케스트레이터가 QA 단계 실행 여부를 결정한다.

**반환 형식**:
```
WIREFRAME 완료: tasks/{NNN}-{태스크명}/wireframe.md
```

## 와이어프레임 품질 체크리스트

wireframe.md 생성 후 자체 검증한다:

- [ ] TASK.md의 모든 화면/기능 요구사항이 wireframe.md에 반영되었는가
- [ ] 각 화면에 ASCII 레이아웃이 포함되었는가
- [ ] 컴포넌트 계층(레이아웃/컨테이너/요소)이 명확히 정의되었는가
- [ ] 인터랙션(클릭, 입력, 전환)이 명세되었는가
- [ ] shadcn/ui 컴포넌트 매핑이 포함되었는가
- [ ] ui-designer 스킬로 바로 구현 가능한 수준인가
