# TASK: context-compactor 스킬 생성 (Phase 1)

> 작성일: 2026-03-22 | 작업 유형: 신규 개발

## 작업 목표
에이전트의 메모리 파일들을 압축하여 장기 기억(Long-term Memory)으로 변환하는 `context-compactor` 스킬을 생성한다. Phase 1은 임베딩 없이 LLM 기반 압축 + 포인터 시스템만 구현한다.

## 배경
- 에이전트가 장기 실행되면 `.opal/memory/*.md`에 메모리가 누적됨
- 전체 메모리를 매번 로드하면 컨텍스트 윈도우를 과도하게 소비
- 압축된 장기 기억(COMPACTED.md)을 생성하면 부트스트랩 시 가벼운 브리핑만으로 전체 맥락 파악 가능
- 최근 기억(memory/*.md) + 장기 기억(archive/COMPACTED.md) 2계층 메모리 구조 확립

## 요구사항
- [ ] `skills/context-compactor/SKILL.md` 생성
- [ ] 3가지 입력 모드 지원: `memory` (OPAL 메모리), `history` (대화 히스토리/로그), `document` (임의 문서)
- [ ] 3가지 압축 레벨: `brief` (~20%), `compact` (~50%, 기본값), `dense` (~70%)
- [ ] 압축 원칙 정의: WHY 보존, 포인터 유지, 시간축 보존, 타입 태깅
- [ ] 출력물: COMPACTED.md (frontmatter + 카테고리별 그루핑 + 포인터)
- [ ] CLASSIFY → COMPRESS → VERIFY 3단계 파이프라인
- [ ] 에이전트 부트스트랩 연동: COMPACTED.md 존재 시 메모리 대신 로드하는 흐름 정의
- [ ] 스킬 레지스트리(skills.md) 등록

## 제약 조건
- Phase 1: 임베딩/벡터 인덱스 없음 (Phase 2에서 추가 예정)
- 기존 OPAL 메모리 구조(`MEMORY.md` + `memory/*.md`)와 호환
- SKILL.md 단독으로 동작 (외부 의존성 없음)
- 기존 스킬 포맷/패턴 준수

## 관련 문서
- 이전 대화에서 합의한 설계: 메모리 계층, 출력 문서 구조, 라이프사이클
- V-Compress(context-compressor) 참고: 5단계 워크플로우, 가드레일
- MemGPT/Letta 참고: 3계층 메모리 모델
- Mem0 참고: 사실 추출 + ADD/UPDATE/SKIP 판단

## 기술 스택
- 순수 마크다운 스킬 (SKILL.md)
- OPAL 프레임워크 스킬 포맷
