# 위험과 자율성

normal은 승인 범위 안의 가역적 개발 변경이다. agentic에서는 기계 게이트 후 진행한다.
high는 인증·개인정보·결제·파괴적 스키마·운영 변경 등 프로젝트가 정한 고위험이다.
두 모드 모두 높은 위험 intent/spec/plan에 실제 사람 승인이 필요하다.
이전 단계 high는 후속에도 유지한다.

새 외부 계약·AC·구조 선택이 미결정이면 block하고 질문한다. 구현 세부는 근거를 기록하고 진행한다.
semi-agentic은 INTENT/DESIGN/PLAN까지 승인, 이후 정상 개발/검증/리뷰/마감은 자율이다.
agentic은 normal 확인을 자동 통과한다. RELEASE/OBSERVE와 merge/push 권한은 별도다.
이미 부여된 권한은 실제 근거를 기록하고 중복 요청하지 않는다.
