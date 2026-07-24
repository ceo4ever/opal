# DONE: CLOSE 단계 관련 문서 업데이트 스텝 추가

> 완료일: 2026-06-24 | 스킬: opds | 모드: agentic | 태스크: 042

## 완료 요약

8개 pilot SKILL.md(opd/opp/opdd/opds/opdw/opgc/opsdd/opwt)의 CLOSE 단계에 `op-brain-ingest` 디스패치 직전에 "관련 문서 업데이트" 스텝을 삽입했다. 이로써 모든 태스크의 CLOSE 진입 시 PROJECT.md 레지스트리 + changed_files 기반으로 관련 기획·설계 문서를 최신화한 뒤 brain ingest가 이루어지도록 보장된다.

## 변경 파일

| 파일 | 변경 내용 | 버전 |
|------|----------|------|
| `opal/skills/opal-pilot-dev/SKILL.md` | STEP 6 CLOSE 항목2 삽입, 번호 재정렬 | v4.3 |
| `opal/skills/opal-pilot-project/SKILL.md` | STEP 4 CLOSE 항목2 삽입, 번호 재정렬 | v3.3 |
| `opal/skills/opal-pilot-data-design/SKILL.md` | STEP 6 CLOSE 항목2 삽입, 번호 재정렬 | v1.1 |
| `opal/skills/opal-pilot-dev-short/SKILL.md` | STEP 5 CLOSE 항목2 삽입, 번호 재정렬 | v4.0 |
| `opal/skills/opal-pilot-dev-wireframe/SKILL.md` | STEP 4 CLOSE 항목2 삽입, 번호 재정렬 | v3.0 |
| `opal/skills/opal-pilot-gc/SKILL.md` | §4.2 무번호 단락 삽입 (번호 재정렬 비해당) | v1.7 |
| `opal/skills/opal-pilot-sdd/SKILL.md` | Phase 6 CLOSE 항목4 삽입, 번호 재정렬 | v3.5.1 |
| `opal/skills/opal-pilot-write-tech/SKILL.md` | CLOSE 단계 항목2 삽입, 번호 재정렬 | v4.5 |
| `docs/proposals/opal-brain-design.md` | §8.2 CLOSE 단계 흐름 4항목으로 갱신 | - |

## 검증 결과

| 시나리오 | 결과 |
|---------|------|
| TS-001: 8파일 "관련 문서 업데이트" 존재 | ✅ PASS (8/8) |
| TS-002: brain ingest 직전 위치 | ✅ PASS (8/8) |
| TS-003: PROJECT.md + changed_files 키워드 | ✅ PASS (8/8) |
| TS-004: CLOSE 번호 연속성 (패턴 A·B 7파일) | ✅ PASS |
| TS-005: 변경이력 행 추가 | ✅ PASS (8/8) |
| TS-006: CLOSE+변경이력 외 무변경 | ✅ PASS |

## 주요 결정

- **3패턴 분류**: A(numbered, brain=항목2, 6개) / B(numbered, brain=항목4, opsdd) / C(무번호 서브섹션, opgc)
- **버전 충돌 PM 수정**: opsdd v3.1.1→v3.5.1 / opwt v4.4(중복)→v4.5
- **관련 문서 업데이트**: docs/proposals/opal-brain-design.md §8.2 CLOSE 흐름 갱신

## 잔여 미해결

- install 재배포 필요 (소스 변경 → ~/.opal/ 배포본 발효 조건)
- 커밋 미수행 (캡틴 지시 대기)
