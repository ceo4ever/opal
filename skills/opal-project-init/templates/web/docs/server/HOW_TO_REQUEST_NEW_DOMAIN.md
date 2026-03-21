# 새 서비스(도메인) 추가 가이드

이 문서는 {{PROJECT_NAME}} 프로젝트에 새로운 서비스(기능)를 추가하는 방법을 단계별로 안내합니다.

---

## 목차

1. [새 서비스 추가 개요](#새-서비스-추가-개요)
2. [Step by Step 가이드](#step-by-step-가이드)
3. [테스트 및 검증](#테스트-및-검증)
4. [체크리스트](#체크리스트)

---

## 새 서비스 추가 개요

새 서비스를 추가하려면:
1. Model 정의 (DB 엔티티)
2. DTO 생성 (요청/응답 스키마)
3. Repository 생성 (데이터 접근)
4. Service 생성 (비즈니스 로직)
5. Controller 생성 (API 엔드포인트)
6. 라우터 등록

---

## Step by Step 가이드

### Step 1: Model 생성

`Core/domains/{{DOMAIN_NAME}}/model/`에 SQLAlchemy 엔티티를 정의합니다.

```python
# Core/domains/{{DOMAIN_NAME}}/model/your_entity.py

from sqlalchemy import Column, Integer, String, DateTime
from framework.base.BaseMixin import BaseMixin

class YourEntity(BaseMixin):
    __tablename__ = "{{DOMAIN_NAME}}_your_entity"

    entityNo = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    # 추가 컬럼...
```

### Step 2: DTO 생성

요청/응답 스키마를 정의합니다.

```python
# Core/domains/{{DOMAIN_NAME}}/dto/your_entity/YourEntityForm.py (요청)
from dataclasses import dataclass

@dataclass
class YourEntityForm:
    name: str
    description: str = ""

# Core/domains/{{DOMAIN_NAME}}/dto/your_entity/YourEntityResponse.py (응답)
from pydantic import BaseModel

class YourEntityResponse(BaseModel):
    entityNo: int
    name: str
    description: str | None = None
```

### Step 3: Repository 생성

```python
# Core/domains/{{DOMAIN_NAME}}/repository/your_entity/YourEntityRepository.py

from framework.base.BaseRepository import BaseRepository
from domains.{{DOMAIN_NAME}}.model.your_entity import YourEntity

class YourEntityRepository(BaseRepository):
    def __init__(self, session):
        super().__init__(session, YourEntity)

    async def getByPK(self, entityNo: int):
        return await self.executeObject(
            self.session.query(YourEntity).filter(YourEntity.entityNo == entityNo)
        )
```

### Step 4: Service 생성

```python
# Core/domains/{{DOMAIN_NAME}}/service/your_entity/SaveYourEntityService.py

from framework.base.BaseService import BaseService

class SaveYourEntityService(BaseService):
    async def onProcess(self, form):
        repo = YourEntityRepository(self.session)
        entity = YourEntity(**form.__dict__)
        await repo.add(entity)
        self.setData(entity.toDict())
```

### Step 5: Controller 생성

```python
# App/{{DOMAIN_NAME}}/controller/YourEntityController.py

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/your-entity", tags=["YourEntity"])

@router.get("/")
async def get_list():
    # Service 호출
    pass

@router.post("/")
async def create(form: YourEntityForm):
    # Service 호출
    pass
```

### Step 6: main.py에 라우터 등록

```python
# App/{{DOMAIN_NAME}}/main.py

from controller.YourEntityController import router as your_entity_router
app.include_router(your_entity_router)
```

---

## 테스트 및 검증

### 1. 서버 실행

```bash
cd backend/App/{{DOMAIN_NAME}}
uv run python main.py
```

### 2. API 문서 확인

http://localhost:{{SERVER_PORT}}/docs 에서 새 API 확인

### 3. API 테스트

```bash
# 목록 조회
curl http://localhost:{{SERVER_PORT}}/api/v1/your-entity/

# 생성
curl -X POST http://localhost:{{SERVER_PORT}}/api/v1/your-entity/ \
  -H "Content-Type: application/json" \
  -d '{"name": "테스트", "description": "테스트 설명"}'
```

---

## 체크리스트

### 새 서비스 추가 체크리스트

- [ ] Model 생성 및 `__init__.py`에 export 추가
- [ ] Form DTO 생성 (요청 데이터)
- [ ] Response DTO 생성 (응답 데이터)
- [ ] Repository 생성 및 기본 메서드 구현
- [ ] Service 생성 및 비즈니스 로직 구현
- [ ] Controller 생성 및 엔드포인트 구현
- [ ] `main.py`에 라우터 등록
- [ ] API 문서 확인 (Swagger)
- [ ] 테스트 및 검증

---

## 참고 문서

- [도메인 아키텍처](./DOMAIN_GUIDE.md)
- [프로젝트 구조](./PROJECT_STRUCTURE.md)
- [환경 변수](./ENVIRONMENT.md)
