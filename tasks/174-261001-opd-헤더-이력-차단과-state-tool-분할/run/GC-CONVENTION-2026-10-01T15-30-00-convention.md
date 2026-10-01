# GC-CONVENTION 2026-10-01T15-30-00 (convention)
- base_ref: dee405ca, 대상 40+10개(중복 제거) 파일, check_status: pass
- 기준: docs/CONVENTIONS.md, header-rules.md, header-standard.md
- 결과: Critical 0 / High 0 / Medium 10 / Low 0 (전부 이번 변경이 새로 만듦, pre_existing 0)
- Medium 10건(GC-001~010): 신규 디렉터리 state_tool_parts가 kebab-case가 아님(advisory). 단 Python import 가능 패키지명이어야 하며 CONVENTIONS는 Python 파일 snake_case를 허용하므로 사실상 예외 해석 가능. 10건은 동일 원인 1개.
- 모델 점검: 신규 10개 모듈의 인라인 @header는 형식(module/layer/domain/description/exports) 일치, 이력 누적 없음, description 현재 역할 한 줄. state_tool.py 헤더도 동일. 새 위반 없음.
- 한계: exports의 실제 정의 일치는 전수 대조하지 않음(code-scan 몫).
