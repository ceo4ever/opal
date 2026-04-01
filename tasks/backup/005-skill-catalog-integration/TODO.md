# Awesome Agent Skills 카탈로그 통합 — 실행 체크리스트

> 작성일: 2026-03-09 | 작성자: OPAL | 버전: v1.0

## Part A: 복잡도 판별

- **파일 수**: 신규 2 + 수정 2 = 총 4개
- **작업 유형**: 문서 작성 + 스크립트 수정
- **판정**: 단순 (메인 에이전트 직접 실행)

## Part B: 실행 체크리스트

### Step 1: 스킬 카탈로그 생성

- [ ] `templates/opal/catalog/` 디렉토리 생성
- [ ] `templates/opal/catalog/skills-catalog.md` 작성
  - 549개+ 스킬을 카테고리별 테이블로 정리
  - 기본 설치 23개는 "✅ 기본설치" 표시
  - 소스 URL 포함

### Step 2: skill-manager 스킬 작성

- [ ] `templates/opal/skills/skill-manager/SKILL.md` 작성
  - YAML frontmatter (name, description + 트리거)
  - 검색 프로세스 (카탈로그 Read → 키워드 매칭)
  - 설치 프로세스 (git clone → community-skills/ 배치)
  - 목록/삭제 프로세스

### Step 3: install-mac.sh 수정

- [ ] `install_basic_skills()` 함수 추가
  - anthropics/skills 리포에서 17개 스킬 복사
  - google-labs-code/stitch-skills 리포에서 6개 스킬 복사
- [ ] `install_opal()` 함수에서 `install_basic_skills` 호출
- [ ] 카탈로그 파일 복사 (`~/.opal/catalog/`)

### Step 4: AGENT.md 수정

- [ ] 스킬 참조 섹션에 커뮤니티 스킬 경로 추가
- [ ] OPAL 전용 스킬에 skill-manager 추가

### 완료 검증

- [ ] `templates/opal/catalog/skills-catalog.md` 존재 확인
- [ ] `templates/opal/skills/skill-manager/SKILL.md` 존재 확인
- [ ] `scripts/install-mac.sh` 문법 오류 없음 (bash -n)
- [ ] AGENT.md 일관성 확인

| 버전 | 날짜 | 작성자 | 변경내용 |
|------|------|--------|---------|
| v1.0 | 2026-03-09 | OPAL | 최초 작성 — 4단계 실행 체크리스트 |
