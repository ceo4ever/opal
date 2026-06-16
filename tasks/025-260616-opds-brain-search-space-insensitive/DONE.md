# DONE: brain-tool search 공백 무시 매칭

> 완료일: 2026-06-16 | 스킬: opds | 모드: agentic | 채번: 025

## 1. 작업 요약

`brain-tool search`가 한국어 복합명사의 띄어쓰기 편차로 검색이 갈리는 문제를, **검색 시점 공백 무시(whitespace-insensitive) 매칭**으로 해결했다. 정규화는 검색 순간의 휘발성 사본에만 적용되어 저장 문서·원본·스니펫 표시용 원문은 불변이다.

## 2. 캡틴 실증 요구 충족

| 요구 | 결과 |
|------|------|
| `"자동 취소"` ≡ `"자동취소"` 동일 검색 | ✅ (테스트 S-3 RED→GREEN) |
| `"선정 자동 취소"` ≡ `"선정자동취소"` ≡ `"선정자동 취소"` 동일 검색 | ✅ (테스트 S-4 RED→GREEN) |
| 배포본 실데이터 시연 (`"파이프라인"`=`"파이프 라인"`=`"파 이 프 라 인"`) | ✅ 모두 29건 동일 |

## 3. 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| `opal/tools/brain-tool/brain_tool.py` | `_norm(s)` 헬퍼 신설(`"".join(str(s).lower().split())`) + `_score_page` 4필드(title·rel·tags가중치·body) 정규화 매칭(`--tag` 필터는 정확 일치 유지) + `_make_snippet` `orig_index` 역매핑(원문 노출) + `cmd_search` `query_norm` 전환(`query=query` 원문 출력 유지) |
| `opal/tools/brain-tool/tests/test_brain_tool.py` | `TestSearch`에 등가/3원등가/비대칭/스니펫원문/계약/`_norm`단위 테스트 추가 |
| `opal/tools/brain-tool/README.md` | §5 "공백 무시 매칭" 설명 + 변경이력 v1.1 (025) |
| `~/.opal/tools/brain-tool/` (재배포) | install-mac.sh 경유 — 소스↔배포본 diff 무차이 |

## 4. 검증 결과

- **RED-first**: 구현 전 S-3/S-4 2 FAILED(RED) → 구현 후 PASS(GREEN) 전환으로 동작 변경 입증.
- **전체 테스트**: 89 passed / 0 failed / 회귀 0.
- **TEST-SCENARIO**: S-1~S-11 전 시나리오 PASS (등가·비대칭·스니펫·계약·하위호환·문서·재배포).
- **코드 품질 4/4** (외부 의존성 미추가·결정론·@header 불변), **보안 3/3** (시크릿 0·저장 문서 불변·배포 경계 준수).

## 5. 범위 제외 (별도 사안 — 미구현)

| 항목 | 사유 |
|------|------|
| 정규식 `--regex` 옵션 | 캡틴 결정으로 제외 |
| 토큰화·stopword·OR 매칭 | 정밀도 위험, 실요구 아님 |
| 문서 마이그레이션 | 검색 시점 정규화이므로 불필요 |
| 인덱싱·임베딩 | 현 규모(54페이지) 과설계 — 병목 관측/의미검색 필요 시 별도 설계 스파이크 |

## 6. 후속 / 비고

- 비대칭(부분문자열 포함 방향) 캡틴 수용: 짧은 쿼리 넓게 / 긴 쿼리 좁게.
- 원 제안서(`~/.opal/tools/brain-tool/PROPOSAL-search-improvement.md`)는 공백 매칭으로 범위 축소 확정됨 — 토큰화/OR/정규식 축은 비채택.
- 커밋: 미수행 (캡틴 지시 대기).
