---
template: sdlc-v2
---
# PLAN: 주문 내보내기 CSV 다운로드

## Approach
기존 주문 조회 쿼리를 재사용하는 내보내기 엔드포인트와 화면 버튼을 추가한다.

## Findings

### 직접 변경
- `api/orders/export.py` — 신규 엔드포인트
- `admin/orders/list.py` — 내보내기 버튼

### 회귀 확인
- `api/orders/query.py` — 기존 목록 조회 필터 동작

### 문서 갱신
- `docs/API.md` — 신규 엔드포인트

### 미확인 가정
- H-1(Risks)

## Decisions and contracts

| 결정 | 변경 후 계약 | 선택 이유·근거 |
|---|---|---|
| 엔드포인트 | `GET /api/orders/export?{목록과 같은 필터}` → `200 text/csv`(UTF-8 BOM, 헤더 1행, 열: 주문번호·주문일시·금액·상태) | 목록 필터를 그대로 재사용 |
| 상한 초과 | 건수가 10,000 초과면 파일을 만들지 않고 `422 {"error":"export_limit_exceeded","count":N}`; 화면은 이 코드를 받으면 "10,000건 이하로 필터를 좁혀 주세요"를 표시 | C-1 |
| 저장 | 서버에 파일을 저장하지 않고 응답 스트림으로만 전송 | 개인정보 잔존 방지 |

## Work items

| 작업 | 담당 | 변경 대상 | 구체적 변경 | 선행 작업 | 실행 그룹 | 완료 기준 연결 |
|---|---|---|---|---|---|---|
| W-1. 내보내기 API | opal-be-agent | `api/orders/export.py`, `docs/API.md` | 위 계약대로 엔드포인트 구현, 건수 선검사 후 스트리밍, API 문서 추가 | 없음 | P1 | AC-1, AC-2, C-1 |
| W-2. 화면 버튼 | opal-fe-agent | `admin/orders/list.py` | 현재 필터로 API 호출, 422 코드 시 안내 문구 표시 | W-1 | P2 | AC-1, AC-2 |

## Risks

| 위험 | 깨질 수 있는 동작·계약 | 영향 | 설계 대응 |
|---|---|---|---|
| H-1. 10,000건 스트리밍이 게이트웨이 30초 제한 안에 끝난다 | 내보내기 응답 | 대량 내보내기 실패 | S-3 부하 측정 |

## Release and recovery
- 적용 순서: P1 → P2 → 스테이징 배포 → 운영 배포
- 검증 범위: API 단위·통합, 화면 E2E, 10,000건 부하
- 실패 시: 버튼 기능 플래그를 끄고 이전 버전으로 롤백
