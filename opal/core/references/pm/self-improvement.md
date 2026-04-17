# 자기 개선 세부 프로세스

> 출처: opal-pm.md §5.2
> Lazy 트리거: 태스크 완료 또는 소유자 피드백 수신 시
> 탐색 경로: `opal/core/references/pm/self-improvement.md`

트리거 테이블은 `opal-pm.md` §5에 유지되며, 이 문서는 세부 프로세스를 담는다.

## 개선 대상과 기록 위치

| 발견 내용 | 기록 위치 | 예시 |
|----------|----------|------|
| 프로젝트 공통 원칙 | `.opal/AGENT.md` 확정 기준 | "모든 API는 인증 필수" |
| PM 검토 기준 개선 | `.opal/AGENT.md` PM 검토 기준 | "회귀 테스트 커버리지 체크 추가" |
| BE 도메인 규칙 | `.opal/agents/opal-be-agent/AGENT.md` 확정 기준 | "camelCase 응답" |
| FE 도메인 규칙 | `.opal/agents/opal-fe-agent/AGENT.md` 확정 기준 | "shadcn Dialog 사용 시 Portal 필수" |
| DB 도메인 규칙 | `.opal/agents/opal-db-agent/AGENT.md` 확정 기준 | "soft delete 컬럼명 is_deleted" |
| 전문 에이전트 테이블 변경 | `.opal/AGENT.md` 전문 에이전트 섹션 | 새 에이전트 추가/제거 |

## 자기 개선 프로세스

```
1. 관찰: 태스크/대화에서 개선 대상 발견
2. 분류: 공통 원칙 / 도메인 규칙 / PM 기준 / 일회성
3. 기록:
   - 공통 → .opal/AGENT.md 확정 기준 추가
   - 도메인 → 해당 프로젝트 전문 에이전트 확정 기준 추가
   - PM → .opal/AGENT.md 검토 기준 갱신
   - 일회성 → .opal/memory/에 기록 (다음 태스크 참조용)
4. 보고: "이 규칙을 추가했습니다: {내용}" — 소유자에게 간략 보고
5. 소유자가 이의 없으면 확정, 이의 있으면 조정
```

## 자기 개선 제한

- **기존 확정 기준 수정/삭제는 소유자 승인 필수** — 추가만 자율, 변경/삭제는 제안 후 승인
- **금지사항 추가는 소유자 승인 필수** — 금지는 영향이 크므로 반드시 확인
- **프레임워크 에이전트(`~/.opal/agents/`)는 수정 안 함** — 프로젝트 에이전트만 갱신
