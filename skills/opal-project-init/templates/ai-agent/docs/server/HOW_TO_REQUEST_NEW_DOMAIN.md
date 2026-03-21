# 새 Agent 및 Tool 추가 가이드

이 문서는 {{PROJECT_NAME}} 프로젝트에 새로운 에이전트나 도구를 추가하는 방법을 단계별로 안내합니다.

---

## 목차

1. [새 Agent 추가](#새-agent-추가)
2. [새 Tool 추가](#새-tool-추가)
3. [Safety Level 설정](#safety-level-설정)
4. [테스트 및 검증](#테스트-및-검증)

---

## 새 Agent 추가

### 개요

새 에이전트를 추가하려면:
1. Role 정의
2. Tool 구현
3. Agent 등록
4. Role-Tool 매핑

### Step 1: Role 정의

`backend/App/{{DOMAIN_NAME}}/main.py`의 `setup_initial_data()` 함수에 새 역할을 추가합니다.

```python
roles_data = [
    {
        "roleName": "역할 이름",
        "roleCode": "ROLE_CODE",
        "description": "역할 설명",
        "systemPrompt": "LLM 시스템 프롬프트"
    }
]
```

### Step 2: Tool 구현

```python
# Core/domains/{{DOMAIN_NAME}}/service/tool/YourTools.py

class YourTool:
    @staticmethod
    async def _get_parameters() -> dict:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "설명"}
            },
            "required": ["param1"]
        }

    @staticmethod
    async def execute(**kwargs) -> dict:
        """실행 로직"""
        return {"success": True, "data": {...}}
```

### Step 3: Tool 등록

```python
tools_data = [
    {
        "toolName": "도구 이름",
        "toolCode": "TOOL_CODE",
        "safetyLevel": SafetyLevel.MEDIUM.value,
        "description": "도구 설명",
        "functionName": "execute",
        "modulePath": "domains.{{DOMAIN_NAME}}.service.tool.YourTools.YourTool",
        "role": "ROLE_CODE"
    }
]
```

### Step 4: Agent 등록

```python
agents_data = [
    {
        "agentName": "에이전트 이름",
        "agentCode": "AGENT_CODE",
        "roleCode": "ROLE_CODE",
        "description": "에이전트 설명",
        "modelName": "gpt-4o-mini"
    }
]
```

### Step 5: 서버 재시작 및 테스트

```bash
cd backend/App/{{DOMAIN_NAME}}
uv run python main.py
```

---

## Safety Level 설정

```python
class SafetyLevel(Enum):
    SAFE = "SAFE"           # 바로 실행 (조회, 검색)
    MEDIUM = "MEDIUM"       # 바로 실행 (수정, 삭제)
    DANGEROUS = "DANGEROUS" # 승인 필요 (금전, 중요 데이터)
```

---

## 테스트 및 검증

1. **서버 로그 확인**: 초기 데이터 설정 완료 메시지
2. **API 문서**: http://localhost:{{SERVER_PORT}}/docs
3. **채팅 UI 테스트**: http://localhost:{{CLIENT_PORT}}
4. **Safety Level 테스트**: DANGEROUS 도구 승인 흐름 확인

---

## 체크리스트

- [ ] Role 정의 (`setup_initial_data()`)
- [ ] Tool 구현 (파라미터 스키마 + execute)
- [ ] Tool 등록 (`setup_initial_data()`)
- [ ] Agent 등록 (`setup_initial_data()`)
- [ ] Safety Level 설정
- [ ] 서버 재시작
- [ ] API 문서 확인
- [ ] 테스트

---

## 참고 문서

- [도메인 아키텍처](./DOMAIN_GUIDE.md)
- [프로젝트 구조](./PROJECT_STRUCTURE.md)
