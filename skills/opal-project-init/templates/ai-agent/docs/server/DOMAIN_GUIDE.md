# {{DOMAIN_NAME}} 도메인 아키텍처 가이드

{{PROJECT_NAME}} 프로젝트의 AI 에이전트 도메인 아키텍처와 구조를 설명합니다.

## 목차

1. [도메인 개요](#도메인-개요)
2. [Agent 아키텍처](#agent-아키텍처)
3. [Tool 시스템](#tool-시스템)
4. [Safety Level](#safety-level)
5. [디렉토리 구조](#디렉토리-구조)
6. [데이터 흐름](#데이터-흐름)
7. [확장 가이드](#확장-가이드)

---

## 도메인 개요

### {{DOMAIN_NAME}} 도메인

- **도메인 코드**: `{{DOMAIN_NAME}}`
- **아키텍처**: 멀티 에이전트 시스템
- **패턴**: Agent → Tool 직접 호출

---

## Agent 아키텍처

### Agent → Tool 직접 호출 패턴

```
사용자 요청
    ↓
Supervisor Agent (라우팅)
    ↓
전문 Agent 선택
    ↓
Tool 실행 (LLM Function Calling)
    ↓
Safety Level 확인
    ↓
결과 반환
```

### Agent 구성 요소

1. **Role**: 에이전트의 역할 정의
2. **Tools**: 사용 가능한 도구 목록
3. **System Prompt**: LLM에게 전달되는 프롬프트
4. **Model**: 사용하는 LLM 모델

---

## Tool 시스템

### Tool 구조

```python
class YourTool:
    @staticmethod
    async def _get_parameters() -> dict:
        """파라미터 스키마 (JSON Schema)"""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "설명"}
            },
            "required": ["param1"]
        }

    @staticmethod
    async def execute(**kwargs) -> dict:
        """도구 실행 로직"""
        return {"success": True, "data": {...}}
```

### Tool 등록

```python
# App/{{DOMAIN_NAME}}/main.py - setup_initial_data()

{
    "toolName": "도구 이름",
    "toolCode": "TOOL_CODE",
    "safetyLevel": SafetyLevel.SAFE.value,
    "description": "도구 설명",
    "functionName": "execute",
    "modulePath": "domains.{{DOMAIN_NAME}}.service.tool.YourTools.YourTool",
    "role": "ROLE_CODE"
}
```

### Role-Tool 매핑

- 각 Tool은 특정 Role에 매핑
- Agent는 자신의 Role에 매핑된 Tool만 사용 가능
- Supervisor는 Tool을 직접 사용하지 않고 라우팅만 수행

---

## Safety Level

### 3단계 안전성 등급

```python
class SafetyLevel(Enum):
    SAFE = "SAFE"           # 바로 실행 (조회, 검색)
    MEDIUM = "MEDIUM"       # 바로 실행 (수정, 삭제)
    DANGEROUS = "DANGEROUS" # 승인 필요 (금전, 중요 데이터)
```

### Approval Flow

```
DANGEROUS Tool 호출
    ↓
Approval 생성 (status=PENDING)
    ↓
관리자 승인/거부
    ↓
승인 시 Tool 실행
```

---

## 디렉토리 구조

```
backend/
├── App/{{DOMAIN_NAME}}/                # 애플리케이션 계층
│   ├── main.py                        # FastAPI 앱 + 초기 데이터 설정
│   ├── config/                        # 환경 설정
│   └── controller/                    # API 컨트롤러
│
└── Core/domains/{{DOMAIN_NAME}}/       # 비즈니스 로직
    ├── agent/                          # Agent 구현
    │   ├── agents/                    # 각 에이전트
    │   ├── tasks/                     # Task 워크플로우
    │   └── tools/                     # Agent 도구
    │
    ├── model/                          # DB 엔티티
    ├── dto/                            # 데이터 전송 객체
    ├── repository/                     # 데이터 접근 계층
    └── service/                        # 비즈니스 로직
        ├── tool/                      # Tool 구현
        ├── memory/                    # Memory Service
        └── approval/                  # Approval Service
```

---

## 데이터 흐름

### 일반 요청

```
사용자 요청
    ↓
Controller (POST /api/v1/chat/message)
    ↓
SupervisorAgent.execute()
    ↓
전문 Agent 선택 & 실행
    ↓
LLM이 Tool 선택 (Function Calling)
    ↓
ToolExecutionService.execute()
    ↓
결과 반환
```

### DANGEROUS Tool 실행

```
위험한 작업 요청
    ↓
Safety Level = DANGEROUS 확인
    ↓
ApprovalService.createApproval()
    ↓
승인 요청 생성 (status=PENDING)
    ↓
관리자 승인 후 Tool 실행
```

---

## 확장 가이드

### 새 Agent 추가

1. **Role 정의**: `setup_initial_data()`에 역할 추가
2. **Tool 구현**: `service/tool/`에 도구 클래스
3. **Agent 등록**: `setup_initial_data()`에 에이전트 추가
4. **Role-Tool 매핑**: 역할과 도구 연결
5. **Safety Level 설정**: 각 Tool에 안전성 등급

### 새 Tool 추가

1. Tool 클래스 구현 (`_get_parameters` + `execute`)
2. Tool 등록 (`setup_initial_data()`)
3. Safety Level 설정
4. 서버 재시작 및 테스트

자세한 내용: [HOW_TO_REQUEST_NEW_DOMAIN.md](./HOW_TO_REQUEST_NEW_DOMAIN.md)

---

## 참고 문서

- [Agent/Tool 추가 가이드](./HOW_TO_REQUEST_NEW_DOMAIN.md)
- [프로젝트 구조](./PROJECT_STRUCTURE.md)
- [환경 변수](./ENVIRONMENT.md)
