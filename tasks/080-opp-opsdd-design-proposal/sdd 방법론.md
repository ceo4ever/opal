SDD 방법론 원래 구조                                                                                                                                   
                                                                                                                                                         
  SPEC (기능 명세 = SSOT)                                                                                                                                
   └─ tasks (스펙에서 파생된 작업 목록)                                                                                                                  
       └─ 구현                                                                                                                                           
                                                                                                                                                         
  Kiro, spec-kit, cc-sdd 전부 동일:                                                                                                                      
  Kiro:     requirements.md → design.md → tasks.md
  spec-kit: spec.md → plan.md → tasks/                                                                                                                   
  cc-sdd:   spec.md → tasks.md → 구현                                                                                                                    
                                     
  SPEC이 "무엇을 만들 것인가"의 SSOT이고, tasks는 그 스펙을 실현하기 위한 하위 작업입니다.                                                               
                                                                                                                                                         
  OPAL과의 충돌 지점                                                                                                                                     
                                                                                                                                                         
  ┌────────┬───────────────────────┬────────────────────────────────┐                                                                                    
  │        │          SDD          │              OPAL              │
  ├────────┼───────────────────────┼────────────────────────────────┤
  │ 최상위 │ SPEC (명세가 출발점)  │ TASK (요청이 출발점)           │
  ├────────┼───────────────────────┼────────────────────────────────┤
  │ 하위   │ tasks (스펙에서 파생) │ PLAN → EXECUTE (TASK에서 파생) │                                                                                    
  └────────┴───────────────────────┴────────────────────────────────┘                                                                                    
                                                                                                                                                         
  제가 아까 "TASK가 더 큰 개념"이라고 한 건 OPAL 하네스 기준이었고, SDD 방법론 자체는 SPEC이 왕입니다.                                                   
                                    
  이게 설계에 중요한 이유                                                                                                                                
                                    
  캡틴이 SDD의 가치를 충분히 적용하고 싶다면, 두 가지 선택지가 있어요:                                                                                   
                                    
  A. OPAL 중심 — TASK 안에 SPEC을 넣음 (제가 제안한 것)                                                                                                  
  TASK (하네스 공통) → SPEC → 검증 → 분해 → 루프
  - OPAL 하네스 호환 유지                                                                                                                                
  - 단, SPEC이 TASK의 하위 단계로 격하됨
                                                                                                                                                         
  B. SDD 중심 — SPEC을 최상위로 올림                                                                                                                     
  SPEC (최상위) → 검증 → TASKS → 검증 → 루프 → DONE                                                                                                      
  - SDD 철학에 충실                                                                                                                                      
  - 단, 하네스의 "TASK부터 시작" 규칙을 변경해야 함                                                                                                      
  - TASK.md 없이 spec.md가 출발점                  
                                                                                                                                                         
  C. 절충 — TASK는 진입점, SPEC이 실질적 SSOT
  TASK (진입 + 메타정보) → SPEC (실질적 SSOT) → 이후 모든 것이 SPEC 기준                                                                                 
  - TASK.md는 폴더 생성, 스킬 결정, 모드 기록 등 "행정적" 역할만        
  - spec.md가 실질적 상위 문서, tasks.md와 구현이 모두 spec에서 파생                                                                                     
  - 하네스 호환도 유지, SDD 철학도 살림                                                                                                                  
                                                                                                                                                         
  저는 C가 가장 자연스럽다고 봅니다. 캡틴은 어떻게 보세요?                                                                                               
                                                                                                                                                         
✻ Sautéed for 30s                                                                                                                                        
                                                                                                                                                         
❯ C.안은 프로세스와 폴더구조, 문서는 어떻게 되는 거지?                                                                                                   
                                                       
⏺ C안 상세                                                                                                                                               
                                    
  프로세스                                                                                                                                               
   
  TASK (진입)                                                                                                                                            
   │  하네스 공통 프로세스: 폴더 생성, 스킬 결정, 모드 기록
   │  산출물: TASK.md (메타정보 + 간략 요구사항)                                                                                                         
   │                                                                                                                                                     
   ▼                                                                                                                                                     
  SPEC (실질적 SSOT)                                                                                                                                     
   │  사용자 요구사항을 정형 명세로 확장                                                                                                                 
   │  산출물: spec.md (Background, Goals, AC, Edge Cases...)                                                                                             
   │                                                                                                                                                     
   ▼                                                                                                                                                     
  SPEC-VERIFY (명세 검증 + TDD Red)                                                                                                                      
   │  구조/의미/도메인 3계층 검증                                                                                                                        
   │  AC에서 테스트 시나리오 도출                                                                                                                        
   │  산출물: verify.md (SPEC 섹션), test-scenarios.md                                                                                                   
   │                                                                                                                                                     
   ▼                                                                                                                                                     
  TASKS (분해)                      
   │  spec.md 기준으로 태스크 분해                                                                                                                       
   │  AC ↔ 태스크 매핑 (추적 매트릭스)
   │  산출물: tasks.md                                                                                                                                   
   │                                                                                                                                                     
   ▼                                                                                                                                                     
  TASKS-VERIFY (분해 검증)                                                                                                                               
   │  커버리지, 의존관계, 자기완결성 검증
   │  산출물: verify.md (TASKS 섹션 추가)                                                                                                                
   │                                                                                                                                                     
   ▼                                                                                                                                                     
  EXECUTE-LOOP (태스크별 루프)                                                                                                                           
   │  for each task:                
   │    PLAN → EXECUTE → TEST                                                                                                                            
   │    ├─ Pass → 다음 태스크
   │    └─ Fail → 재시도 (루프 가드)                                                                                                                     
   │                                
   ▼                                                                                                                                                     
  DONE (최종 검증 + 완료)           
      전체 테스트 통과 + verify.md 최종 갱신 + DONE.md                                                                                                   
                                                                                                                                                         
  폴더 구조
                                                                                                                                                         
  tasks/{NNN}-opsdd-{name}/         
  │
  ├── TASK.md                 ← 진입점 (메타정보)
  ├── STATE.md                ← 상태 추적                                                                                                                
  │
  ├── specs/                  ← SPEC이 지배하는 공간                                                                                                     
  │   ├── spec.md             ← ★ 실질적 SSOT                                                                                                            
  │   ├── tasks.md            ← spec에서 파생된 태스크 분해                                                                                              
  │   ├── verify.md           ← 검증 저널 (누적)                                                                                                         
  │   │                                                                                                                                                  
  │   ├── tests/              ← TDD Red (구현 전 정의)                                                                                                   
  │   │   └── test-scenarios.md   ← AC → 테스트 시나리오 매핑                                                                                            
  │   │                                                                                                                                                  
  │   └── tasks/              ← 태스크별 실행 공간
  │       ├── T1-{name}/                                                                                                                                 
  │       │   ├── PLAN.md                                                                                                                                
  │       │   └── (실행 산출물)                                                                                                                          
  │       ├── T2-{name}/                                                                                                                                 
  │       │   └── ...                                                                                                                                    
  │       └── T3-{name}/
  │           └── ...                                                                                                                                    
  │                                 
  └── DONE.md                 ← 최종 완료
                                                                                                                                                         
  문서 역할 분리
                                                                                                                                                         
  ┌───────────────────┬─────────────────────────────────────────────────┬─────────────────┐
  │       문서        │                      역할                       │      성격       │
  ├───────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ TASK.md           │ 진입점. "누가, 왜, 어떤 스킬로"                 │ 행정 (하네스용) │
  ├───────────────────┼─────────────────────────────────────────────────┼─────────────────┤
  │ spec.md           │ "무엇을, 어떤 기준으로" — 모든 하위 문서의 근거 │ SSOT            │                                                              
  ├───────────────────┼─────────────────────────────────────────────────┼─────────────────┤                                                              
  │ tasks.md          │ "어떻게 쪼개서" — spec에서 파생                 │ spec의 자식     │                                                              
  ├───────────────────┼─────────────────────────────────────────────────┼─────────────────┤                                                              
  │ verify.md         │ 검증 이력 누적                                  │ 품질 저널       │
  ├───────────────────┼─────────────────────────────────────────────────┼─────────────────┤                                                              
  │ test-scenarios.md │ AC → 테스트 정의 (TDD Red)                      │ spec의 자식     │
  ├───────────────────┼─────────────────────────────────────────────────┼─────────────────┤                                                              
  │ T{N}/PLAN.md      │ 개별 태스크 구현 계획                           │ tasks.md의 자식 │
  ├───────────────────┼─────────────────────────────────────────────────┼─────────────────┤                                                              
  │ DONE.md           │ 최종 완료 확인                                  │ 종료            │
  └───────────────────┴─────────────────────────────────────────────────┴─────────────────┘                                                              
                                    
  문서 계층 (파생 관계)                                                                                                                                  
                                    
  TASK.md (진입)                                                                                                                                         
   └─ spec.md ★ (SSOT)              
       ├─ test-scenarios.md (AC에서 파생)
       ├─ tasks.md (spec에서 파생)                                                                                                                       
       │   ├─ T1/PLAN.md (태스크에서 파생)
       │   ├─ T2/PLAN.md                                                                                                                                 
       │   └─ T3/PLAN.md            
       └─ verify.md (spec·tasks 검증 결과)                                                                                                               
                                    
  모든 의사결정의 근거를 추적하면 spec.md로 돌아갑니다. TASK.md는 "이 작업이 존재한다"는 것만 증명하고, "무엇을 어떤 기준으로 만드는가"는 전부 spec.md가 
  답합니다.                         
                                                                                                                                                         
  TASK.md 예시 (가벼움)             

  # TASK: 사용자 인증 시스템
                                                                                                                                                         
  > 작성일: 2026-04-05 | 적용 스킬: opsdd | 모드: interactive                                                                                            
  > 입력: 사용자 요구사항                                                                                                                                
  > 출력: specs/spec.md → 구현                                                                                                                           
                                                                                                                                                         
  ## 요청                                                                                                                                                
  광고 플랫폼의 사용자 인증 시스템 구현                                                                                                                  
                                    
  ## 기술 스택                                                                                                                                           
  - Python 3.12 / FastAPI / PostgreSQL
                                                                                                                                                         
  ## 관련 문서                                                                                                                                           
  - docs/ARCHITECTURE.md
  - docs/BACKEND.md                                                                                                                                      
                                    
  spec.md 예시 (무거움 — SSOT)                                                                                                                           
  
  # SPEC: 사용자 인증 시스템                                                                                                                             
                                    
  > 버전: 1.0 | 상태: Verified                                                                                                                           
  
  ## Background                                                                                                                                          
  광고 플랫폼에 사용자 인증이 필요. JWT 기반,
  세션 관리 포함.                                                                                                                                        
  
  ## Goals                                                                                                                                               
  - G1: 이메일/비밀번호 기반 인증   
  - G2: JWT 토큰 발급/갱신/폐기                                                                                                                          
  - G3: 계정 잠금 정책
                                                                                                                                                         
  ## Non-goals                      
  - 소셜 로그인 (다음 단계)                                                                                                                              
  - 2FA (다음 단계)                                                                                                                                      
  
  ## Functional Requirements                                                                                                                             
  - [FR-01] 회원가입 (이메일 중복 체크)
  - [FR-02] 로그인 (JWT 발급)                                                                                                                            
  - [FR-03] 토큰 갱신 (refresh token)                                                                                                                    
  - [FR-04] 로그아웃 (토큰 무효화)                                                                                                                       
  - [FR-05] 5회 실패 시 계정 잠금                                                                                                                        
                                    
  ## Acceptance Criteria                                                                                                                                 
  - [AC-01] GIVEN 유효한 이메일+비밀번호
           WHEN POST /auth/login                                                                                                                         
           THEN 200 + access_token + refresh_token                                                                                                       
  - [AC-02] GIVEN 잘못된 비밀번호                                                                                                                        
           WHEN POST /auth/login                                                                                                                         
           THEN 401 + 실패 횟수 증가
  - [AC-03] GIVEN 5회 연속 실패                                                                                                                          
           WHEN POST /auth/login                                                                                                                         
           THEN 423 Locked + 잠금 시간 반환
  - [AC-04] ...                                                                                                                                          
                                    
  ## Edge Cases                                                                                                                                          
  - [EC-01] 동시 로그인 5개 세션 → 가장 오래된 세션 만료
  - [EC-02] 잠금 중 비밀번호 초기화 요청 → 허용                                                                                                          
                                                                                                                                                         
  ## Non-functional Requirements                                                                                                                         
  - [NFR-01] 로그인 응답 200ms 이내                                                                                                                      
  - [NFR-02] 비밀번호 bcrypt 해싱                                                                                                                        
  
  ## Constraints                                                                                                                                         
  - BaseUser 모델 상속 필수 (BACKEND.md)
  - 미들웨어 체계 준수 (BE-FRAMEWORK.md)                                                                                                                 
                                                                                                                                                         
  ## Open Questions                                                                                                                                      
  없음                                                                                                                                                   
                                                                                                                                                         
  ---
  이 구조에서 핵심은 TASK.md는 얇고 spec.md가 두껍다는 겁니다. 하네스와의 호환은 TASK.md가 지키고, SDD의 가치는 spec.md가 담당합니다.   