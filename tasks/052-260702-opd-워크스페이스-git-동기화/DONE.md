# DONE: 워크스페이스 Git 일괄 동기화 — git-sync-tool + opal-workspace-sync 스킬 신설

> 완료일: 2026-07-02 | 스킬: opd | 모드: agentic
> 태스크: 052-260702-opd-워크스페이스-git-동기화

## 결과 요약

워크스페이스 아래 여러 독립 git 저장소를 순회하며 안전 일괄 최신화하는 기능을 OPAL 프레임워크에 신설했다. 결정론 git 작업은 `git-sync-tool`(도구)이, 대상 결정·5섹션 보고서·승인 게이트는 `opal-workspace-sync`(스킬, alias `opws`)가 담당한다. clean + fast-forward 가능 저장소만 `git pull --ff-only`로 자동 최신화하고, 문제 저장소(dirty/diverged/detached/no-upstream/fetch-failed)는 건드리지 않고 skip·보고·승인 후에만 조치한다 (헌법 user sovereignty).

## 변경 파일 (changed_files)

**신규 생성**
- `opal/tools/git-sync-tool/run.sh` — Bash 래퍼 (state-tool 패턴)
- `opal/tools/git-sync-tool/git_sync_tool.py` — 본체 (표준 라이브러리 + git CLI, JSON 출력)
- `opal/tools/git-sync-tool/tests/conftest.py` — git fixture 8종 (bare remote + 상태별 clone)
- `opal/tools/git-sync-tool/tests/test_git_sync_tool.py` — pytest 13종
- `opal/skills/opal-workspace-sync/SKILL.md` — operator 스킬 (3분기·5섹션·승인 게이트)

**수정**
- `scripts/install-mac.sh` — git-sync-tool chmod +x 블록 + 헤더 변경이력(v3.8)
- `opal/core/references/opal-skills-registry.json` — opal-workspace-sync 등록 (배포 갭 수정)
- `opal/core/references/opal-harness.md` — §9 도구 카탈로그 행 + 변경이력(v5.9)
- `opal/core/references/tools.md` — git-sync-tool 섹션 + 변경이력(v2.0)

## 검증 결과 (All Pass)

| 항목 | 결과 |
|------|------|
| 기능 테스트 (pytest) | 13/13 PASS (RED→GREEN, PM 재현) |
| 무손실 P0 (S-16/17/18) | dirty/diverged HEAD·작업트리 불변, ff-only가 diverged 병합 안 함 |
| 5종 skip 판정 (S-2~6) | dirty/diverged/detached/no-upstream/fetch-failed 정확 분류 |
| 정적 (S-11/12/13/19) | SKILL.md 3분기·5섹션·승인게이트·git 2.22+ 명시 |
| 코드 품질 | ruff All checks passed |
| 보안 | 시크릿 0, 자율조치 코드 0, shell=True 0, subprocess 인자리스트+cwd 격리 |
| 배포·발견 (S-14/15/20) | install 재배포 → run.sh -x, SKILL.md 배포, 런타임 `skill-registry match "opws"` found:true |

## 주요 의사결정·특이사항

1. **아키텍처 = 도구+스킬 분리** — 결정론 git 로직은 도구(enforce), 오케스트레이션은 스킬(advise). OPAL "enforce, don't advise" 정합.
2. **pull 정책 `--ff-only` 고정** — diverged를 병합 판단 없이 안전 skip. "문제 시 자율 조치 금지" 원칙을 git 명령 레벨에서 집행.
3. **🐛 PLAN 판정순서 결함 보정 (폴백 승인)** — detached HEAD에서 `git ... @{u}`가 exit 128 fatal → no-upstream과 혼동. detached 판정을 no-upstream보다 선행하도록 순서 교정 (테스트 계약 유지, 더 정확).
4. **🐛 배포 갭 수정 (캡틴 실사용 중 발견)** — install은 스킬 *파일*을 배포하나 skill-registry는 `opal-skills-registry.json` *인덱스*로 발견 → 등록 누락으로 `//opws` 미발견. 레지스트리 등록 + 재배포 + 런타임 match 검증으로 해소. **교훈: 신규 스킬은 파일 배포뿐 아니라 레지스트리 JSON 등록이 필수 단계.**
5. **워커 .md Write 차단 대응** — 이 환경의 서브에이전트는 리포트 .md 직접 Write가 차단됨 → 워커는 텍스트 반환, PM이 산출물 저장.

## 후속 조치

- **커밋** — 캡틴 명시 요청 시에만 (미수행). 변경 파일 9개 + 태스크 산출물.
- **pointail 실사용** — `//opws /Volumes/Data/StoreLinkStudio/pointail/workspace` 또는 해당 디렉토리에서 `//opws` 호출.
- **install 재배포** — 본 태스크에서 이미 1회 재배포 완료 (런타임 검증 목적). 커밋 후 캡틴 PC 간 동기화 시 재실행.
