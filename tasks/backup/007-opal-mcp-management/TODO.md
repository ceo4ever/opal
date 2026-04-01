# TODO: OPAL MCP 관리 체계 구축

> 작성일: 2026-03-12 | 참조: TASK.md, RESEARCH.md, PLAN.md

## Part A: 실행 체크리스트

> 총 7개 Step | 실행 모드: 복잡 (순차 실행)

### Step 1: MCP 템플릿 디렉토리 및 스키마 문서 생성

- **파일**: `opal/core/mcps/README.md`
- **작업 내용**: MCP 설정 템플릿 스키마 설명 문서 작성. `install_type`, `config`, `platforms` 등 필드 정의.
- **완료 기준**: README.md가 존재하고 스키마가 명확히 기술됨
- **테스트**: 파일 존재 확인
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ⬜ 대기

### Step 2: shadcn MCP 설정 템플릿 생성

- **파일**: `opal/core/mcps/shadcn.json`
- **작업 내용**: shadcn MCP 서버의 설정 템플릿 JSON 작성. `name`, `description`, `install_type: config_merge`, `config`, `platforms: [claude, cursor]` 포함.
- **완료 기준**: 유효한 JSON, python3으로 파싱 가능
- **테스트**: `python3 -c "import json; json.load(open('opal/core/mcps/shadcn.json'))"`
- **실행 방법**: direct
- **의존**: Step 1
- **상태**: ⬜ 대기

### Step 3: merge_mcp_config() 함수 구현

- **파일**: `scripts/install-mac.sh`
- **작업 내용**: python3 기반 JSON 머지 함수 추가. 기존 키 보존, 파일 없으면 신규 생성, 중복 서버 스킵.
- **완료 기준**: 함수가 정의되고, 신규/머지/스킵 3가지 케이스 처리
- **테스트**: 임시 파일로 3가지 케이스 수동 검증
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ⬜ 대기

### Step 4: install_mcp() 함수 구현

- **파일**: `scripts/install-mac.sh`
- **작업 내용**: `opal/core/mcps/*.json` 순회 → 각 템플릿의 `install_type` 판별 → `config_merge`면 플랫폼별 mcp.json에 머지. python3 없으면 경고 후 스킵.
- **완료 기준**: 함수가 정의되고, shadcn.json 기준으로 claude/cursor에 머지 동작
- **테스트**: install_mcp 함수 단독 호출 테스트
- **실행 방법**: direct
- **의존**: Step 2, Step 3
- **상태**: ⬜ 대기

### Step 5: install_opal()에 MCP 설치 연결

- **파일**: `scripts/install-mac.sh`
- **작업 내용**: `install_opal()` 함수 끝에 `install_mcp` 호출 추가
- **완료 기준**: install_opal 실행 시 MCP 설치도 함께 수행됨
- **테스트**: install_opal 흐름 전체 확인
- **실행 방법**: direct
- **의존**: Step 4
- **상태**: ⬜ 대기

### Step 6: MCP 레지스트리 업데이트

- **파일**: `opal/core/references/mcps.md`
- **작업 내용**: "현재 등록된 MCP 서버 없음" 제거, shadcn MCP 서버 항목 등록. 설명, 프로토콜, 제공 도구, 사용 예시 기술.
- **완료 기준**: mcps.md에 shadcn 항목이 등록되고, 예시 블록이 아닌 실제 데이터로 채워짐
- **테스트**: 파일 내용 확인
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ⬜ 대기

### Step 7: CLAUDE.md 소스 구조 반영

- **파일**: `CLAUDE.md`
- **작업 내용**: 소스 구조 다이어그램의 `opal/core/` 하위에 `mcps/` 디렉토리 추가. 배포 구조에도 반영.
- **완료 기준**: CLAUDE.md 소스/배포 구조에 mcps/ 반영
- **테스트**: 파일 내용 확인
- **실행 방법**: direct
- **의존**: 없음
- **상태**: ⬜ 대기

---

## Part B: QA 체크리스트

### B-1. 기능 테스트

- [ ] `opal/core/mcps/shadcn.json`이 유효한 JSON인지 확인
- [ ] mcp.json이 없는 상태에서 install_mcp 실행 → 신규 생성 확인
- [ ] 기존 mcp.json이 있는 상태에서 install_mcp 실행 → 기존 키 보존 + shadcn 추가 확인
- [ ] 이미 shadcn이 등록된 상태에서 재실행 → 덮어쓰기 없이 스킵 확인
- [ ] Claude Code, Cursor 두 플랫폼 경로에 모두 생성 확인

### B-2. 회귀 테스트

- [ ] install-mac.sh의 기존 기능(스킬, 에이전트, 부트스트래퍼 설치)에 영향 없는지 확인
- [ ] install_opal() 전체 흐름이 정상 동작하는지 확인

### B-3. 코드 품질

- [ ] install-mac.sh의 기존 코딩 스타일(함수 네이밍, 로깅, 에러 처리) 준수
- [ ] MCP 템플릿 JSON이 indent 2로 정렬됨
- [ ] CLAUDE.md 구조 다이어그램이 기존 형식과 일관적

### B-4. 보안

- [ ] MCP 설정에 하드코딩된 토큰/시크릿 없음
- [ ] 환경변수는 `${VAR}` 형식으로 참조

---

## Part C: 실행 아키텍처

### C-1. 에이전트 토폴로지

모든 Step이 순차 direct 실행. 서브에이전트 불필요.

```
Step 1 → Step 2 → Step 3 → Step 4 → Step 5 → Step 6 → Step 7
                    ↗ (병렬 가능)                    ↗ (병렬 가능)
                Step 6, Step 7은 Step 1~5와 독립이므로 병렬 가능하나,
                단순성을 위해 순차 실행
```

### C-2. 스킬 요구사항

기존 스킬로 충분. 신규 스킬 불필요.

### C-3. 도구 요구사항

- python3: macOS 기본 포함, 추가 설치 불필요
- 추가 패키지/CLI 없음

### C-4. 테스트 전략

install-mac.sh 수정 후 임시 HOME 디렉토리를 만들어 설치 시뮬레이션으로 검증.

---

## 승인 요청

> ⚠️ 위 TODO가 승인되면 EXECUTE 단계를 시작합니다.
> Step 1~7을 순서대로 직접 실행합니다.
