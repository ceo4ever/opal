"""
@header {
  "module": "conftest",
  "task": "161",
  "layer": "test",
  "domain": "opal-tools",
  "description": "unit-real 고정 사례는 각자 격리된 실행 대상(ruff/mypy/pytest/eslint/tsc/vitest)이며 test-tool 자체 회귀 스위트의 수집 대상이 아니다. 상위 pytest 실행이 이 트리를 수집하면 동일 basename(test_calc.py 등)이 여러 사례 폴더에 있어 import 충돌이 난다. 전부 수집 제외한다.",
  "exports": ["collect_ignore_glob"]
}

[T161] fixtures/unit-real 전체를 pytest 수집 대상에서 제외한다.
이 디렉터리의 test_*.py는 test-tool 자신의 회귀 테스트가 아니라, S-9/S-10이
실제 도구(ruff/mypy/pytest/eslint/tsc/vitest)로 임시 폴더에 복사해 실행하는
고정 사례 프로젝트다.
"""

collect_ignore_glob = ["*"]
