# 인용 규칙 — 개발 트랙 부록 (Citation Rules · Dev)

> 출처: `opal/core/references/harness/citation-rules.md` §2.5 (분리 이전 원문)
> 로드 시점: 개발 트랙 산출물(ANALYSIS/PLAN/EXECUTE 등) 작성 시
> 역할: 개발 트랙 `[MUST]` 토큰 인용 대상 6종 + Good/Bad 예시
> 트랙 판별표: `citation-rules.md` §1.5(개발/비개발 트랙별 근거 매트릭스) — 개발 트랙 행은 문서/기획 산출물/설계 산출물/소스 코드 근거가 전부 **필수**다.

---

## 2.5 개발 트랙 [MUST] 토큰 대상

개발 트랙에서 `[MUST]` 인용이 반드시 필요한 구체 토큰 유형 6종:

#### (1) 필드명

- **Good**: `` [MUST] `docs/CONVENTIONS.md` §3.1: "API 응답은 camelCase" ``
- **Bad**: `"API 응답은 camelCase다 (컨벤션 문서 참고)"`

#### (2) 함수 시그니처

- **Good**: `` [MUST] `src/user.py:45`: "def create_user(email: str) -> User" ``
- **Bad**: `"create_user는 email 받는다"`

#### (3) 타입명

- **Good**: `` [MUST] `src/types/user.ts:12`: "type UserRole = 'admin' | 'member'" ``
- **Bad**: `"UserRole은 admin 또는 member"`

#### (4) ERD 컬럼명

- **Good**: `` [MUST] `docs/ERD.md` §2.3: "users.deleted_at TIMESTAMP NULL" ``
- **Bad**: `"users 테이블에 deleted_at 있음"`

#### (5) IA 화면 ID/라우트

- **Good**: `` [MUST] `docs/IA.md` §4.1: "SCREEN-U001 /settings/profile" ``
- **Bad**: `"설정 페이지 경로"`

#### (6) 정책 조항 번호

- **Good**: `` [MUST] `docs/policy.md` §5.2.1: "만 14세 미만 가입 불가" ``
- **Bad**: `"14세 제한 정책"`

---

## 변경이력

| 버전 | 날짜 | 변경내용 |
|------|------|---------|
| v1.0 | 2026-08-09 20:50 | `citation-rules.md` §2.5(개발 트랙 [MUST] 토큰 6종)을 조건부 로드 분리 신설 — 원문 그대로 이동, 내용 축약 없음 (087) |
