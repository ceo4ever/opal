# PM 검토 게이트

> 출처: opal/core/references/opal-pm.md §4
> 로드 시점: PM Gate 수행 시 / 워커 완료 수신 직후
> 역할: 워커 완료 선언 / 검토 11항목 / Pass·Fail 판정 / 문서 등록 확인 / 하네스와의 관계

---

각 단계 워커 완료 후, PM 관점에서 결과를 검토한다.

### 워커 완료 선언

워커 결과 수신 직후, Observability 선언을 수행한다 (하네스 §5 참조):

> `⚙️ 워커 완료:` {단계명} — {결과 한 줄 요약}

### 검토 절차

1. 관련 참조 문서가 워커에게 전달되었는가
2. 기술 스택에 맞는 MCP/스킬이 활용되었는가 (예: shadcn/ui → shadcn MCP 사용 여부)
3. `.opal/AGENT.md`의 PM 검토 기준 체크리스트 평가
4. TASK.md 요구사항과 산출물의 정합성
5. 참조 문서 내용이 산출물에 반영되었는가
6. `docs/PROJECT.md`의 프로젝트 원칙/기준에 부합하는가
7. 금지사항 위반 여부
8. EXECUTE 결과 changed_files 중 code-scan 대상 확장자 파일에 @header가 올바르게 작성되었는가
   - 확인 방법: `code-scan scan <file> --json` 실행
   - 결과 없음: @header 누락 → Fail
   - 결과 있음: module/layer/domain/description/exports 필드 존재 여부 확인 → 누락 시 Fail
   - EXECUTE 결과에 새 domain/scope 추가 시 code-scan.json 갱신 여부도 함께 확인 (§9 참조)
9. 전문 에이전트 영역 침범 여부
   - FE 에이전트가 BE 파일을 수정하지 않았는가
   - BE 에이전트가 FE 파일을 수정하지 않았는가
   - 공통 영역(타입 정의 등) 변경 시 양쪽에 영향 분석이 되었는가
10. Batch 간 인터페이스 정합성 (BE API ↔ FE 호출 일치)
11. docs/ 무효화 체크
   - EXECUTE의 changed_files가 docs/ 문서의 내용을 무효화하지 않는가
   - 새 API 추가 → BACKEND.md 갱신 필요?
   - 새 컴포넌트 추가 → FRONTEND.md 갱신 필요?
   - 구조 변경 → ARCHITECTURE.md 갱신 필요?
   - 새 패턴 도입 → CONVENTIONS.md 갱신 필요?
   - 갱신 필요 시: PM이 직접 갱신하거나, opi 최신화를 제안

### 판정

- **Pass**: 소유자에게 보고
- **Fail**: 워커에게 재지시 (최대 1회) → 재검토 → 보고
- **Fail (영역 침범/인터페이스 불일치)**: 해당 전문 에이전트에 재지시 (최대 1회)
- **`.opal/AGENT.md` 미존재 시**: PM 검토를 스킵하고 기존 흐름대로 진행 (하위 호환)

### 하네스와의 관계

하네스 interactive §3 PM Gate가 "PM 검토를 수행하라"고 지시하면, 이 §4의 절차를 따른다. 하네스는 게이트 구조(언제)를, 이 문서는 검토 내용(무엇을 어떻게)을 정의한다.

### 문서 등록 확인

작업 완료 후 새 문서가 `docs/` 하위에 생성된 경우:
1. 소유자에게 확인: "이 문서를 프로젝트 문서로 등록할까요?"
2. 소유자 승인 시 → 용도 인터뷰 → `docs/PROJECT.md` 문서 테이블에 등록

---

## 변경이력

| 버전 | 날짜 | 내용 |
|------|------|------|
| v1.0 | 2026-04-21 | 다운사이징 — opal-pm.md §4 분리 (128) |
