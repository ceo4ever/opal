# 아티팩트

태스크에 intent.md/json, spec.md/json, plan.md/json을 둔다.
Markdown은 사람이 검토하는 설명, JSON은 실행 계약이다. 둘 다 결합 해시에 포함한다.
내용의 의미 일치는 Coordinator와 Reviewer가 검토하며 JSON이 기계 판정 기준이다.

schemas의 같은 이름 계약을 따른다. validator는 사용된 닫힌 JSON Schema 부분집합만
지원하고 미지원 검증 키워드는 거부한다. 빈 문장/미결 질문 삭제로 게이트를 속이지 않는다.

- intent: 문제, 결과, AC, 비목표, 제약, 위험, 미결 질문.
- spec: 요구사항·설계·정책 버전과 intent 결합 해시.
- plan: 정확한 파일 경로, 독립 역할 ID, 실행 argv 배열 목록, 롤백, spec 결합 해시.

validate-artifacts 출력으로 현재 결합 해시를 구한다. 이를 다음 source_sha256에 넣는다.
Git commit SHA는 별도 값이다. 권한에 맞는 Git checkpoint로 아티팩트 이력을 보존한다.

templates는 작성 시작점이다. 실제 요구로 채우고 미결 질문을 해소한 뒤 전이한다.
evidence.json 템플릿은 출력 예시이며 증거 입력이 아니다. collect-evidence로 실제 생성한다.
외부 시스템이 원본이면 기록 ID·버전을 문서에 연결하고 원본 변경 시 rewind한다.
