<!--
@header {
  "module": "task-160-opst-oppb-support",
  "layer": "document",
  "domain": "opal-skill-tester",
  "description": "opal-skill-tester에 OPPB 판정 프로필과 실행 기록 수명주기 기능 시나리오를 추가하는 태스크 계약.",
  "exports": []
}
-->

# TASK: opst OPPB 지원

## 목표

`opal-skill-tester` 실제 헤드리스 세션으로 OPPB를 실행하고, 파이프라인 완주와
태스크 귀속 `.oppb-run` 보존을 합격 계약으로 판정한다.

## 범위

- `skill_tester.py` OPPB 프로필·fingerprint·P0~P5 단계 측정 추가
- canonical 태스크 `.oppb-run/<run_id>/run.closed.json` 증거와 legacy `.opal-runs` 미생성 판정
- `function-oppb-low-stock` 기능 시나리오와 숨은 인수 테스트 추가
- 시나리오 규격, 지표 문서, 회귀 테스트 동기화

## 완료 조건

1. OPPB 프로필이 `p3.continuous_execution`~`p5.worktree_finalize`를 올바르게 측정한다.
2. OPPB 합격은 닫힌 task-local archive가 있고 허브 `.opal-runs`가 없을 때만 성립한다.
3. OPPB 기능 시나리오가 `validate`를 통과하고 기반 저장소에서 숨은 테스트가 RED이다.
4. 기존 `opd`·`opds`·`opsdd` 판정은 변하지 않는다.

## 제외

- 실제 유료 헤드리스 세션은 시간·비용 최종 확인 전에 실행하지 않는다.
- 기존 OPPB runtime 계약은 변경하지 않는다.
