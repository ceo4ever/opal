<!--
@module opal-pilot-gc
@layer reference
@domain security
@description opal-security-checker가 생성하는 GC-SECURITY 보고서 샘플
@audience opal-pilot-gc 개발자 / 보고서 포맷 검수자
-->

# GC SECURITY REPORT — 샘플

> 본 문서는 `opal-pilot-gc` CHECK 단계에서 `opal-security-checker`가 생성하는 보안 보고서의 **샘플**입니다.
> 실사용 시 `tasks/{NNN}-opgc-{요약}/GC-SECURITY-{타임스탬프}.md`로 저장됩니다.

## 1. 헤더

- 실행 일시: 2026-04-17 14:30:12 ~ 14:32:47 (소요 2분 35초)
- 범위: `staged` / 대상 파일 7개
- 에이전트: `opal-security-checker`
- APPLY 수행: ✅ (승인 모드 A)

## 2. 요약 지표

| 지표 | 값 |
|------|-----|
| 총 이슈 수 | 7 |
| 심각도 분포 | Critical 1 / High 2 / Medium 2 / Low 1 / Info 1 |
| 자동 수정 가능 | 2 |
| 수동 조치 필요 | 5 |
| 파일별 상위 Top 3 | `src/auth/login.js` (3), `src/config/api.js` (2), `src/db/query.js` (2) |
| 카테고리별 빈도 | CWE-798 Hard-coded Credentials (2 파일) |
| Critical/High 수 | **3** (심각도 트리거 발동) |
| 문서 업데이트 제안 수 | 2 |

## 3. 수정 대상 (체크리스트)

### Critical (1건)

- [x] GC-001 [src/config/api.js:12] 하드코딩된 API 키
  - 카테고리: OWASP A07 / CWE-798
  - 위반 기준: Base (OWASP Top 10 2021)
  - 설명: 프로덕션 API 키가 소스 코드에 하드코딩됨 (`const API_KEY = "sk_live_..."`)
  - 해결 방안: 환경 변수(`process.env.API_KEY`) 또는 시크릿 매니저로 이동
  - 자동 수정: N
  - 참조: <https://owasp.org/Top10/A07_2021-Identification_and_Authentication_Failures/>
  - **적용 시각**: 2026-04-17 14:31 — 소유자 수동 조치 후 재검증 통과

### High (2건)

- [!] GC-002 [src/db/query.js:45] SQL 인젝션 가능성
  - 카테고리: OWASP A03 / CWE-89
  - 위반 기준: Base
  - 설명: 사용자 입력이 문자열 연결로 쿼리에 삽입됨 (`"SELECT * FROM users WHERE id=" + userId`)
  - 해결 방안: 파라미터 바인딩으로 전환 (`WHERE id=?` + prepared statement)
  - 자동 수정: Y (시도됨)
  - 참조: <https://cwe.mitre.org/data/definitions/89.html>
  - **실패 사유**: 동적 테이블명 참조로 인해 자동 변환 불가
  - **권장**: 테이블명 whitelist + 수동 리팩토링

- [?] GC-003 [src/auth/session.js:88] 약한 세션 토큰
  - 카테고리: OWASP A02 / CWE-330
  - 위반 기준: Base
  - 설명: `Math.random()` 기반 세션 토큰 생성
  - 해결 방안: 암호학적 난수(`crypto.randomBytes`) 사용
  - 자동 수정: N
  - 참조: <https://owasp.org/Top10/A02_2021-Cryptographic_Failures/>
  - **확인 요청**: 토큰 방식 변경 시 기존 세션 일괄 로그아웃 발생 — 마이그레이션 전략 결정 필요

### Medium (2건)

- [x] GC-004 [src/config/api.js:28] 하드코딩된 내부 URL
  - 카테고리: 설정 관리 / CWE-798 변형
  - 위반 기준: 프로젝트(SECURITY.md §2.3)
  - 해결 방안: 환경별 config 파일로 분리
  - 자동 수정: Y
  - 참조: <https://cwe.mitre.org/data/definitions/798.html>
  - **적용 시각**: 2026-04-17 14:31

- [~] GC-005 [src/legacy/old-api.js:120] 구버전 암호화 알고리즘 (MD5)
  - 카테고리: OWASP A02 / CWE-327
  - 위반 기준: Base
  - 해결 방안: SHA-256 이상으로 마이그레이션 + 기존 해시 재생성
  - 자동 수정: Y (가능하나)
  - 참조: <https://owasp.org/Top10/A02_2021-Cryptographic_Failures/>
  - **보류 사유**: 레거시 파일 — 2026 Q2 전체 리팩토링 예정으로 이번에는 스킵

### Low (1건)

- [?] GC-006 [src/api/handler.js:200] 상세 에러 메시지 노출
  - 카테고리: OWASP A05 / CWE-209
  - 위반 기준: Base
  - 해결 방안: 사용자 응답은 일반 메시지, 로그에만 상세 기록
  - 자동 수정: N
  - 참조: <https://cwe.mitre.org/data/definitions/209.html>
  - **확인 요청**: 개발 환경에서는 상세 에러가 유용 — 환경별 분기 필요성 결정 요청

### Info (1건)

- [ ] GC-007 [src/utils/crypto.js:5] 주석 스타일 일관성 (보안 유틸 문서화 권장)
  - 카테고리: 문서화
  - 위반 기준: 프로젝트(SECURITY.md §4)
  - 해결 방안: JSDoc 형식 통일
  - 자동 수정: N
  - 참조: <https://jsdoc.app/>

## 4. 문서 업데이트 제안 (§9·§10)

§9의 3개 트리거를 **독립 판정**하여 각각 분리 표기:

### 4.1 빈도 트리거 (동일 fingerprint ≥ N=3 파일)

**발동 안 함** — `CWE-798 Hard-coded Credentials`가 2개 파일(`api.js`, `legacy/old-api.js`)에서 발견되었으나 임계값 N=3 미달.

### 4.2 심각도 트리거 (Critical 또는 High 1건 이상)

**발동 (3건 해당)**:

- [ ] GC-001 (Critical, CWE-798 Hard-coded Credentials) → SECURITY.md §2 체크리스트에 "시크릿 하드코딩 금지 + CI 스캔" 항목 추가 권장
- [ ] GC-002 (High, CWE-89 SQL Injection) → SECURITY.md에 "SQLi 예방 — 파라미터 바인딩 의무" 규칙 추가 권장
- [ ] GC-003 (High, CWE-330 약한 난수) → SECURITY.md §2 체크리스트에 "암호학적 난수(crypto.randomBytes) 의무" 항목 추가 권장

### 4.3 새 카테고리 트리거 (기존 docs 섹션 미존재)

**발동 (1건)**:

- [ ] `CWE-89 SQLi` — 기존 `docs/SECURITY.md`에 해당 카테고리 섹션 없음. 새 섹션 "SQL Injection 예방" 신설 권장.

## 5. 문서 작성 유도

- `docs/SECURITY.md` 존재 확인 ✅ — 작성 유도 안내 없음.
