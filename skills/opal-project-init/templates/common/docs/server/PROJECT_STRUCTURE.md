# 프로젝트 구조 상세 가이드

## 디렉토리 구조 및 역할

### App/ (애플리케이션 진입점)

#### main.py
- FastAPI 애플리케이션 초기화
- 미들웨어 설정 (CORS, 보안, 예외 처리)
- 라우터 등록
- 서버 실행 설정

#### config/
- **env.py**: 환경별 설정 (local, dev, production)
- **security.py**: 보안 관련 설정

#### controller/
- API 엔드포인트 정의
- 요청/응답 처리
- Service 호출

### Core/ (핵심 비즈니스 로직)

#### framework/ (프레임워크 기반 클래스)

##### base/
- **BaseController.py**: 모든 Controller의 기본 클래스
  - `setData()`: 응답 데이터 설정
  - `getResponse()`: 표준 응답 형식 반환

- **BaseService.py**: 모든 Service의 기본 클래스
  - `doService()`: 트랜잭션 자동 관리
  - `onProcess()`: 하위 클래스에서 구현해야 하는 추상 메서드

- **BaseRepository.py**: 모든 Repository의 기본 클래스
  - `executeObject()`: 단일 객체 조회
  - `executeList()`: 목록 조회
  - `executePaginate()`: 페이징 조회
  - `add()`, `update()`, `delete()`: CRUD 작업

##### api/
- **BaseHttpResponse.py**: 표준 API 응답 모델
- **api_response.py**: API 응답 처리 유틸리티
- **apimessage.py**: 에러 메시지 코드 정의

##### exception/
- **serviceexception.py**: 비즈니스 로직 예외
- **sessionexception.py**: 세션 관련 예외

##### orm/
- **db.py**: 데이터베이스 연결 설정 (AsyncSQLAlchemy)

##### util/
- **dateutil.py**: 날짜/시간 유틸리티
- **cmmn_utils.py**: 공통 유틸리티 함수
- **logger.py**: 로깅 유틸리티

#### domains/ (도메인별 비즈니스 로직)

##### {domain}/model/
- SQLAlchemy 엔티티 정의
- 데이터베이스 테이블과 매핑
- `BaseMixin`을 상속하여 `toDict()` 메서드 제공

##### {domain}/dto/
- **Form DTO**: 요청 데이터 검증 (dataclass 기반)
- **Response DTO**: 응답 데이터 모델 (Pydantic BaseModel)

##### {domain}/repository/
- 데이터베이스 접근 로직
- `BaseRepository`를 상속하여 공통 기능 사용
- 도메인별 특화 쿼리 메서드 구현

##### {domain}/service/
- 비즈니스 로직 구현
- `BaseService`를 상속하여 트랜잭션 관리
- `onProcess()` 메서드에서 실제 로직 구현

##### {domain}/process/
- 복잡한 프로세스 로직 (예: 로그인 프로세스)
- 여러 Service를 조합하여 복잡한 작업 수행

## 데이터 흐름

```
Client Request
    ↓
Controller (요청 검증)
    ↓
Service (비즈니스 로직)
    ↓
Repository (데이터 접근)
    ↓
Database
    ↓
Repository (결과 반환)
    ↓
Service (비즈니스 로직 처리)
    ↓
Controller (응답 생성)
    ↓
Client Response
```

## 샘플 코드 구조

### Todo 샘플 (완전한 CRUD 예제)

1. **Model**: `Core/domains/{domain}/model/sample.py`
   - `Todo` 엔티티 정의

2. **DTO**:
   - `Core/domains/{domain}/dto/sample/TodoForm.py` (요청)
   - `Core/domains/{domain}/dto/sample/TodoResponse.py` (응답)

3. **Repository**: `Core/domains/{domain}/repository/sample/TodoRepository.py`
   - `getByPK()`, `getListByMemberNo()`, `getAll()` 메서드

4. **Service**:
   - `Core/domains/{domain}/service/sample/SaveTodoService.py` (생성/수정)
   - `Core/domains/{domain}/service/sample/DeleteTodoService.py` (삭제)

5. **Controller**: `App/{domain}/controller/SampleController.py`
   - GET, POST, PUT, DELETE 엔드포인트

### 회원 관리 샘플 (인증 예제)

1. **Model**: `Core/domains/{domain}/model/member.py`
   - `Member`, `MemberToken` 엔티티

2. **DTO**:
   - `Core/domains/{domain}/dto/member/MemberForm.py` (회원가입)
   - `Core/domains/{domain}/dto/member/MemberLogin.py` (로그인)
   - `Core/domains/{domain}/dto/member/MemberResponse.py` (응답)

3. **Repository**:
   - `Core/domains/{domain}/repository/member/MemberRepository.py`
   - `Core/domains/{domain}/repository/member/MemberTokenRepository.py`

4. **Service**:
   - `Core/domains/{domain}/service/member/SaveMemberService.py` (회원가입)

5. **Process**:
   - `Core/domains/{domain}/process/member/MemberLoginProcess.py` (로그인)

6. **Controller**: `App/{domain}/controller/MemberController.py`
   - 회원가입, 로그인, 내 정보 조회 엔드포인트

## 개발 시 체크리스트

새로운 기능을 추가할 때 다음 순서로 진행하세요:

- [ ] Model 생성 및 `__init__.py`에 export 추가
- [ ] Form DTO 생성 (요청 데이터)
- [ ] Response DTO 생성 (응답 데이터)
- [ ] Repository 생성 및 기본 메서드 구현
- [ ] Service 생성 및 비즈니스 로직 구현
- [ ] Controller 생성 및 엔드포인트 구현
- [ ] `main.py`에 라우터 등록
- [ ] 테스트 및 검증

## 주의사항

1. **비동기 처리**: 모든 데이터베이스 작업은 `async/await` 사용 필수
2. **트랜잭션**: Service의 `doService()` 사용 시 자동 관리
3. **예외 처리**: `ServiceException` 사용하여 일관된 에러 응답
4. **코드 스타일**: PEP 8 준수, 타입 힌팅 사용
5. **네이밍**: 클래스는 PascalCase, 함수/변수는 camelCase
