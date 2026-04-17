<!--
  module: base-security-checklist
  layer: reference
  domain: opal-pilot-gc
  description: GC Base 보안 체크리스트 — OWASP Top 10 (2021) + CWE Top 25 + SANS Top 25 + 도메인 체크리스트
  주의: 이 파일은 opal-security-checker가 Read하는 내장 Base 원칙이다. 프로젝트 SECURITY.md와 별개.
-->

# Base Security Checklist

> **출처 계층 1 — 항상 강제 적용** (docs/SECURITY.md 유무와 무관)
> opal-security-checker 에이전트가 매 실행 시 이 파일을 Read하여 체크리스트에 로드한다.

---

## OWASP Top 10 (2021)

| 카테고리 ID | 제목 | 기본 심각도 | 감지 패턴 / 힌트 | 자동 수정 |
|------------|------|-----------|----------------|---------|
| OWASP-A01 | Broken Access Control | Critical | 인증 없는 엔드포인트, `@RequireAuth` 누락, 수평권한 체크 없음 | N |
| OWASP-A02 | Cryptographic Failures | High | MD5/SHA-1 사용, Math.random() 토큰 생성, 약한 암호화 알고리즘 | Y (알고리즘 치환) |
| OWASP-A03 | Injection | Critical | SQL concat (`"... " + userInput`), `eval()`, template literal에 미검증 입력 | N |
| OWASP-A04 | Insecure Design | High | 설계 레벨 — 인증 우회 경로, 화이트리스트 없는 파일 업로드 | N |
| OWASP-A05 | Security Misconfiguration | High | `DEBUG=True` 프로덕션, CORS `*`, default credential 잔존 | Y (설정값 수정) |
| OWASP-A06 | Vulnerable and Outdated Components | High | package.json 버전 미고정, deprecated 패키지, known CVE 의존성 | N |
| OWASP-A07 | Identification and Authentication Failures | Critical | `jwt.decode()` 단독 사용(verify 없음), 세션 만료 미설정, 기본 비밀번호 | N |
| OWASP-A08 | Software and Data Integrity Failures | High | 의존성 무결성 검증 없음 (npm lock 없음), 서명 없는 배포 패키지 | N |
| OWASP-A09 | Security Logging and Monitoring Failures | Medium | `password`, `token`, `secret` 키워드가 logger 파라미터에 포함 | N |
| OWASP-A10 | Server-Side Request Forgery (SSRF) | High | 사용자 입력 URL에 직접 fetch/request 실행, 내부망 주소 접근 가능 | N |

---

## CWE Top 25 (2023)

| Rank | CWE ID | 제목 | 기본 심각도 | 감지 패턴 / 힌트 | 자동 수정 |
|------|--------|------|-----------|----------------|---------|
| 1 | CWE-787 | Out-of-bounds Write | Critical | 버퍼 조작 코드 (C/C++ 한정) | N |
| 2 | CWE-79 | Cross-site Scripting (XSS) | High | `innerHTML = userInput`, `dangerouslySetInnerHTML`, HTML 이스케이프 누락 | Y (encode 래핑) |
| 3 | CWE-89 | SQL Injection | Critical | 문자열 concat SQL 쿼리, f-string SQL | N |
| 4 | CWE-416 | Use After Free | Critical | 해제 후 포인터 접근 (C/C++ 한정) | N |
| 5 | CWE-78 | OS Command Injection | Critical | `exec(userInput)`, `system(userInput)`, subprocess 미검증 | N |
| 6 | CWE-20 | Improper Input Validation | High | schema 검증 없는 요청 처리, 타입 미확인 | N |
| 7 | CWE-125 | Out-of-bounds Read | High | 배열 인덱스 미검증 (C/C++ 한정) | N |
| 8 | CWE-22 | Path Traversal | High | `../` 미필터, 사용자 입력 기반 파일 경로 | N |
| 9 | CWE-352 | CSRF | High | CSRF 토큰 없음, SameSite 쿠키 미설정 | N |
| 10 | CWE-434 | Unrestricted File Upload | High | 확장자 화이트리스트 없는 파일 업로드, MIME 미검증 | N |
| 11 | CWE-862 | Missing Authorization | Critical | 자원 접근 전 권한 확인 없음 | N |
| 12 | CWE-476 | NULL Pointer Dereference | High | 널 체크 없이 역참조 | N |
| 13 | CWE-287 | Improper Authentication | Critical | 인증 로직 우회 가능한 조건, 세션 고정 | N |
| 14 | CWE-190 | Integer Overflow | High | 정수 연산 범위 미검증 | N |
| 15 | CWE-502 | Deserialization of Untrusted Data | High | `pickle.loads(userInput)`, `JSON.parse` 미검증 | N |
| 16 | CWE-77 | Command Injection | Critical | `shell=True` subprocess, 미필터 명령 조합 | N |
| 17 | CWE-119 | Improper Restriction of Buffer Operations | High | 버퍼 크기 미검증 (C/C++ 한정) | N |
| 18 | CWE-798 | Hard-coded Credentials | Critical | `const API_KEY = "sk-..."`, `password = "admin"` 리터럴 | Y (.env placeholder 치환) |
| 19 | CWE-918 | SSRF | High | OWASP-A10과 동일 | N |
| 20 | CWE-306 | Missing Authentication for Critical Function | Critical | 관리자 기능 인증 없음, `isAdmin` 하드코딩 | N |
| 21 | CWE-362 | Race Condition | Medium | 공유 자원 비동기 접근, 잠금 없는 파일 쓰기 | N |
| 22 | CWE-269 | Improper Privilege Management | High | 불필요한 관리자 권한 실행, sudo 남용 | N |
| 23 | CWE-94 | Code Injection | Critical | `eval(userInput)`, `Function(userInput)` | N |
| 24 | CWE-863 | Incorrect Authorization | High | 역할 기반 접근 제어 잘못된 구현 | N |
| 25 | CWE-276 | Incorrect Default Permissions | Medium | 너무 넓은 파일 권한 (chmod 777), 세계 쓰기 가능 디렉토리 | Y (권한 수정) |

---

## SANS Top 25 — CWE Top 25 매핑

SANS Top 25는 CWE Top 25와 90% 중복이다. 추가 구분 없이 위 CWE 테이블을 사용하며,
아래는 SANS 관점 카테고리 매핑만 참조한다.

| SANS 카테고리 | 대응 CWE | 비고 |
|-------------|---------|------|
| Insecure Interaction | CWE-89, CWE-79, CWE-78, CWE-352, CWE-22 | 외부 입력 처리 |
| Risky Resource Management | CWE-787, CWE-416, CWE-125, CWE-190 | 메모리/버퍼 관리 |
| Porous Defenses | CWE-862, CWE-306, CWE-287, CWE-798, CWE-276 | 인증/인가/설정 |

---

## 도메인 체크리스트

| 도메인 | 체크 항목 | 감지 패턴 | 기본 심각도 | 자동 수정 |
|--------|----------|---------|-----------|---------|
| 시크릿 | `.env` 외 하드코딩 | `git grep`/정규식: `(?i)(api_key|secret|password|token)\s*=\s*["'][^"'${\s]` | Critical | Y (.env placeholder) |
| 시크릿 | private key 패턴 | `-----BEGIN (RSA\|EC\|PRIVATE)` | Critical | N |
| 인증 | 토큰 검증 누락 | `jwt.decode(` 또는 `base64_decode(` 단독 (verify 없이) | Critical | N |
| 인증 | 세션 만료 미설정 | `session.permanent = False` 누락, `expires` 미설정 | High | N |
| 인증 | 기본 비밀번호 | `password = "admin"\|"1234"\|"password"` | Critical | N |
| 인가 | `@RequireAuth` 누락 | 컨트롤러/라우터 엔드포인트 중 인증 데코레이터 없는 함수 | High | N |
| 인가 | 수평권한 체크 누락 | `findById(userId)` 등 소유자 확인 없는 직접 조회 | High | N |
| 입력검증 | schema 미사용 | Joi/Zod/Pydantic 미사용 요청 파라미터 처리 | High | N |
| 입력검증 | HTML 이스케이프 누락 | `innerHTML = `, `dangerouslySetInnerHTML` | High | Y (encode) |
| 의존성 | 버전 미고정 | `"react": "*"`, `"lodash": "^x"` 범위 지정 | Medium | N |
| 의존성 | deprecated 패키지 | node-gyp deprecated, request.js 등 공지된 패키지 | Medium | N |
| 로깅 | 민감 정보 로그 | `logger.*(.*\b(password\|token\|secret\|key)\b)` | High | N |
| 암호화 | 약한 해시 | `createHash('md5')\|createHash('sha1')`, `hashlib.md5` | Medium | Y (sha256 치환) |
| 암호화 | 약한 RNG | `Math.random()` 토큰 생성, `random.random()` | Low | Y (crypto.randomBytes 치환) |
| 설정 | DEBUG 프로덕션 | `DEBUG = True`, `app.run(debug=True)` (비테스트 환경) | High | Y (False 치환) |
| 설정 | CORS 과다 허용 | `cors({ origin: '*' })`, `Access-Control-Allow-Origin: *` | High | N |
| 설정 | eval 사용 | `eval(`, `new Function(` | High | N |

---

## 커뮤니티 스킬 스택별 참조 매핑

opal-security-checker가 기술 스택 감지 후 추가로 Read하는 커뮤니티 스킬 경로:

| 스택 감지 조건 | 추가 참조 경로 |
|-------------|-------------|
| `package.json: react` | `~/.opal/community-skills/openai/security-best-practices/references/javascript-typescript-react-web-frontend-security.md` |
| `package.json: vue` | `~/.opal/community-skills/openai/security-best-practices/references/javascript-typescript-vue-web-frontend-security.md` |
| `package.json: next` | `~/.opal/community-skills/openai/security-best-practices/references/javascript-typescript-next-js-web-full-stack-security.md` |
| `package.json: express` | `~/.opal/community-skills/openai/security-best-practices/references/javascript-typescript-express-web-backend-security.md` |
| `package.json: jquery` | `~/.opal/community-skills/openai/security-best-practices/references/javascript-typescript-jquery-web-frontend-security.md` |
| `requirements.txt: django` | `~/.opal/community-skills/openai/security-best-practices/references/python-django-web-backend-security.md` |
| `requirements.txt: flask` | `~/.opal/community-skills/openai/security-best-practices/references/python-flask-web-backend-security.md` |
| `requirements.txt: fastapi` | `~/.opal/community-skills/openai/security-best-practices/references/python-fast-api-web-backend-security.md` |
| `go.mod` | `~/.opal/community-skills/openai/security-best-practices/references/go-general-security.md` |

> 코드 리뷰 보조 참조 (모든 스택): `~/.opal/community-skills/getsentry/code-review/SKILL.md`
> 커뮤니티 스킬 원본은 수정하지 않는다 — Read 래핑만 사용.

---

## 언어별 식별자 정규식 (Fingerprint 산출 시 사용)

| 언어 | 식별자 정규식 |
|------|------------|
| JS/TS | `[A-Za-z_$][A-Za-z0-9_$]*` |
| Python | `[A-Za-z_][A-Za-z0-9_]*` |
| Go/Java | `[A-Za-z_][A-Za-z0-9_]*` |
