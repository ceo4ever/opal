# TODO: skill-manager npx skills 전환

> 작성일: 2026-03-12

## Part A: 실행 체크리스트

### Step 1: skill-manager SKILL.md 전면 재작성
- [ ] 검색 프로세스: catalog 파싱 → npx skills find 전환
- [ ] 설치 프로세스: catalog URL → npx find 결과에서 repo 추출 → git clone
- [ ] Node.js 폴백 안내 추가
- [ ] references/skills.md 항목 추가/제거 로직 유지
- 실행: direct

### Step 2: install-mac.sh 카탈로그 복사 제거
- [ ] install_opal() 함수에서 카탈로그 복사 블록 삭제 (290-297행)
- [ ] bash -n 검증
- 실행: direct

### Step 3: opal/catalog/ 디렉토리 삭제
- [ ] opal/catalog/skills-catalog.md 삭제
- [ ] opal/catalog/ 디렉토리 삭제
- 실행: direct

### Step 4: AGENT.md, references/skills.md 업데이트
- [ ] AGENT.md에서 catalog/ 참조 확인 및 제거
- [ ] references/skills.md에서 skill-manager 트리거 업데이트
- 실행: direct

### Step 5: CLAUDE.md, README.md 반영
- [ ] CLAUDE.md 소스 구조에서 catalog/ 항목 제거
- [ ] README.md 소스 구조 및 OPAL 설명 업데이트
- 실행: direct

### Step 6: 잔여 참조 확인
- [ ] 프로젝트 전체에서 "catalog" 키워드 검색하여 누락된 참조 정리
- 실행: direct

## Part B: QA 체크리스트

- [ ] skill-manager SKILL.md 프로세스 흐름이 논리적으로 완결
- [ ] install-mac.sh bash -n 통과
- [ ] catalog/ 디렉토리가 완전히 삭제됨
- [ ] 프로젝트 내 "skills-catalog" 참조가 0개
- [ ] references/skills.md의 skill-manager 항목이 정확함
- [ ] CLAUDE.md, README.md 소스 구조가 일관됨

## 복잡도: 단순

| 기준 | 판정 |
|------|------|
| Step 수 | 6개 (경계) |
| 변경 파일 수 | 5개 + 삭제 1개 |
| 모듈 범위 | OPAL 스킬 단일 모듈 |
| 외부 의존성 | 없음 (npx skills는 런타임 의존) |

→ **단순 모드**: 메인 에이전트가 직접 실행
