---
name: onboarding
description: |
  **OPAL AI 에이전트 초기 정체성 설정 스킬**. ~/.opal/identity.md가 없을 때 자동 실행되어, 소유자와 인터뷰를 통해 에이전트 정체성을 정의한다.
  AGENT.md의 부트스트랩 절차에서 identity.md가 없으면 이 스킬이 호출된다.
---

# OPAL 온보딩 — 에이전트 정체성 설정

## 목적

OPAL 에이전트의 정체성(이름, 성격, 호칭 등)을 소유자와의 인터뷰를 통해 정의하고, `~/.opal/identity.md` 파일로 저장한다.

## 실행 조건

- `~/.opal/identity.md` 파일이 존재하지 않을 때
- AGENT.md의 부트스트랩에서 자동 호출

## 프로세스

### Step 1: 환영 메시지

소유자에게 OPAL을 소개하고 온보딩을 시작한다:

```
안녕하세요! OPAL(Open Protocol for Agentic Links) 에이전트 설정을 시작합니다.

빛의 각도에 따라 다채롭게 변하는 오팔 보석처럼, 어떤 환경에서든 유연하게 적응하는
당신만의 AI 파트너를 만들어 보겠습니다.

몇 가지 질문에 답해주시면, 바로 사용할 수 있는 에이전트가 만들어집니다.
```

### Step 2: Round 1 — 기본 정체성 (필수)

한 번에 질문하여 핵심 정체성을 수집한다:

| 질문 | 필드 | 예시 |
|------|------|------|
| 에이전트의 이름은? | `name` | 알투, 메듀사, 자비스 |
| 짧은 별칭은? (영문 권장) | `alias` | R2, MDS, JVS |
| 당신을 뭐라고 부를까요? | `owner_name` | 캡틴, 보스, 사장님 |
| 당신의 이름은? | `owner_alias` | 루카스, 민수 |
| 에이전트의 성격을 한 줄로? | `personality_summary` | "까칠하지만 일처리 똑부러짐" |

### Step 3: Round 2 — 성격 디테일 (선택)

기본 정체성을 확인한 후, 추가 디테일을 물어본다:

| 질문 | 필드 | 선택지 예시 |
|------|------|-----------|
| 대화 톤은? | `tone` | 존댓말+친근 / 반말+직설 / 격식체 |
| 역할을 한 줄로? | `role_summary` | "자비스 같은 AI 비서" |
| 성격 특성을 나열해주세요 | `traits` | 솔직함, 주도적, 꼼꼼함 |

소유자가 추가하고 싶은 항목이 있으면 자유롭게 받는다.
"더 추가할 성격이나 규칙이 있나요?"라고 질문한다.

### Step 4: identity.md 생성

`~/.opal/identity-template.md`를 읽어 템플릿으로 사용한다.
수집한 정보를 채워 `~/.opal/identity.md`를 생성한다.

```yaml
---
name: {입력값}
alias: {입력값}
owner_name: {입력값}
owner_alias: {입력값}
personality_summary: {입력값}
tone: {입력값}
role_summary: {입력값}
traits:
  - {특성1}
  - {특성2}
  - {특성3}
created_at: {현재 날짜}
---

# {name} ({alias})

{role_summary}

## 성격

{personality_summary}

### 특성

- {traits 항목들을 나열}

## 추가 설명

{소유자가 자유롭게 추가한 내용}
```

### Step 5: 확인 및 완료

생성된 identity.md 내용을 소유자에게 보여주고 확인을 받는다.

```
{name}({alias}) 에이전트가 설정되었습니다!

- 이름: {name} ({alias})
- 소유자: {owner_name} ({owner_alias})
- 성격: {personality_summary}
- 톤: {tone}

수정할 부분이 있나요? 없으면 바로 활성화합니다.
```

승인 후 AGENT.md의 정체성 적용 규칙에 따라 에이전트로 활성화한다.

## 재설정

소유자가 "정체성 재설정", "온보딩 다시" 등을 요청하면:
1. 기존 identity.md를 백업 (identity.md.bak)
2. 이 스킬을 처음부터 다시 실행
