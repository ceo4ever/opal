# DONE: opi 아키텍처 문서 생성 깊이 강화 (WHERE → HOW)

> 완료일시: 2026-06-14 15:26 KST | 스킬: //opp --agentic | 태스크: 020

## 목표 달성

opi(`opal-project-init`)가 생성하는 프로젝트 문서를 "지도(WHERE)" 수준에서 **"맵과 나침반"(WHERE+HOW)** 수준으로 끌어올렸다. 목표 = 이 문서만 읽고 해당 프로젝트 규약대로 새 도메인/API/화면을 구현할 수 있는 깊이. 적용 범위 = BE·FE·도메인 전 영역.

## 변경 산출물

| 구분 | 파일 | 핵심 변경 |
|------|------|----------|
| 🆕 신규 | `opal/skills/opal-project-init/references/code-analysis-guide.md` | 초기화·최신화 공통 심층 분석 방법론 SSOT. 블록1(탐색 패턴 표 11행), 블록2(BE/FE 스택별 체크리스트), 블록3(작성 후 코드 1:1 재대조 + 4분류), 블록4(멀티레포/멀티서비스 판별 + 자체 docs 흡수·출처 추적) |
| ✏️ 수정 | `opal/skills/opal-project-init/references/docs-guide.md` | ARCHITECTURE에 HOW 섹션 5종(레이어 규칙·의존 방향 / 데이터 흐름 / 트랜잭션·상태 전이 / 명명 규칙 / 새 기능 추가 절차) + 멀티서비스 분기 안내. BACKEND/FRONTEND 도메인 패턴·새 기능 가이드 심화. 3개 문서에 "구현 시 주입 가능 수준" 작성 기준 명문화. 변경이력 표 신설 |
| ✏️ 수정 | `opal/skills/opal-project-init/SKILL.md` | v4.0.0→4.2.0. 초기화 Phase 3-1 심층화·재대조 이식(B), 최신화 Step C/D 가이드 참조 치환(정보손실 0), 멀티레포·멀티서비스 판별·문서 세트 분기(D), 자체 docs 탐색·흡수 분기(E), 대형 코드베이스 전문 워커 디스패치 분기(C, 임계: 영역≥2 or 빌드모듈≥10) |

## 처방 → 결과 매핑 (요구사항 A~E)

| 처방 | 핵심 설계 | 상태 |
|------|----------|------|
| A 템플릿 심화 | docs-guide HOW 5종 + "구현 시 주입 가능 수준" 기준 | ✅ |
| B 초기화 심층화 | 최신화 Step C/D를 code-analysis-guide로 추출(헌법 §2 중복 제거) → 초기화·최신화 공통 참조로 비대칭 해소 | ✅ |
| C 워커 디스패치 | opgc 검증 패턴 재사용 + 조건부(임계 이상) + 폴백 + 디스패치 의무 명시 | ✅ |
| D 멀티레포·멀티서비스 | 독립 git N개 + 단일레포 다중모듈 양쪽 판별 → `docs/services/{서비스명}/` 분기 | ✅ |
| E 자체 docs 흡수 | 발견→정제·흡수(출처 추적 [MUST]) vs 직접 생성 분기 + 코드 재대조 검증 | ✅ |

## 핵심 결정 (AGENTIC-LOG 참조)

- 멀티서비스 문서 세트 경로 = `docs/services/{서비스명}/` (OPAL 표준 일관성, `docs/claude/services/`는 특정 프로젝트 관례)
- 디스패치 임계 = 영역 수 ≥ 2 또는 빌드 모듈 ≥ 10 (living reference pointail/backend = 50+ Gradle 모듈)
- 설계 기준점(living reference): `pointail/workspace/backend/docs/architecture/`(layer-rules·transaction-patterns 등)의 L3 깊이 = "맵과 나침반"의 정답지

## 검증 상태 (정직 고지)

| 검증 유형 | 상태 |
|----------|------|
| **정적 검증** (구조·HOW 섹션 존재·정보 보존·플랫폼 독립·배포 경계·커밋 가드) | ✅ 완료 — PM 직접 Read/grep, code-analysis-guide 블록1·3에 기존 Step C/D 정보손실 0 확인 |
| **동작 검증** (install 재배포 + 업그레이드 opi 재실행으로 실제 HOW 산출 실증) | ⏳ **후속** — 글로벌 ~/.opal 환경 변경 수반. 캡틴 CLOSE 승인으로 본 태스크에서는 정적 검증까지. 헌법 §4 완전 충족은 후속 동작검증에서 |

## 후속 작업

1. **[필수] install 재배포** — `./scripts/install-mac.sh`로 `opal/skills/opal-project-init/` 소스를 `~/.opal/`에 동기화 (배포 경계 원칙)
2. **[권장] 동작검증** — 재배포 후 업그레이드 opi를 pointail/backend류 대형 BE에 (최신화 모드) 실행 → ARCHITECTURE/BACKEND HOW 섹션이 코드 근거로 채워지는지, 자체 docs 흡수·서비스 분기 작동 확인 (헌법 §4)
3. **[선택] 커밋** — 캡틴 지시 시
