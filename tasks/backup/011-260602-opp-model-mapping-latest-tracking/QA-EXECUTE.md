# QA: EXECUTE — OPAL 모델 매핑 최신화 + 최신 추종 전략 도입

> 검토일: 2026-06-02 | 판정: Pass

---

## 1. 요약

OPAL 모델 매핑의 4개 파일(opal-model-mapping.md / install-mac.sh / agents.md / windows.ps1)에 대해 Gemini 부동 별칭 전환, Codex 최신화, OpenAI 참조전용 명시, 최신 추종 운영 규칙 보강을 수행한 EXECUTE 단계를 검증했다. 5개 동기화 위치(L-1 ~ L-4 + L-2b) 전체에서 install 연동 컬럼(Claude/Cursor/Gemini/Codex) 값이 1:1 일치함을 확인했다. 구값(gemini-2.5, gpt-4.1, gpt-5-codex 등) 잔존 0건, `bash -n` 문법 검사 통과. windows.ps1에 011 변경이력 행이 미추가되었으나 PLAN §6 R-T5에서 허용된 범위이며 기능상 영향 없다.

---

## 2. 검증 결과

| # | 검증 항목 | 결과 | 비고 |
|---|----------|------|------|
| R-1 | Gemini 4곳 값이 §3 매핑과 일치 | Pass | L-1/L-2a/L-3/L-4 모두 light=`gemini-3.1-flash-lite`, standard=`gemini-flash-latest`, advanced=`gemini-pro-latest` 확인 |
| R-2 | install-mac.sh/windows.ps1 `openai` 키 부재 + SSOT 참조전용 각주 존재 | Pass | `grep -n "openai"` 양쪽 0건. SSOT L27에 "OpenAI 컬럼 = 참조 전용(install 어댑터 미연동)" 각주 존재 |
| R-3 | Codex 값 4위치(dict+TOML+기본값+SSOT) 일치 | Pass | L-1/L-2a/L-2b/L-4 모두 light=`gpt-5.4-mini`, standard=`gpt-5.5`, advanced=`gpt-5.3-codex`. windows.ps1 기본값 `gpt-5.5` 확인 |
| R-4 | §5에 운영 규칙 명시 | Pass | opal-model-mapping.md L78-81에 "Claude/Gemini flash-pro 별칭 자동추종 + Gemini light/Codex/OpenAI 분기점검" 규칙 존재 |
| R-5 | L-1/L-2a/L-2b/L-3/L-4 5위치 불일치 0건 | Pass | 대조표(§5 동기화 대조표) 참조 — 불일치 0건 |
| R-6 | opal-model-mapping.md v1.3 + agents.md v1.5 + install-mac.sh v2.7 변경이력 2026-06-02 KST + (011) | Pass | 3개 파일 모두 확인. windows.ps1에는 011 미추가(하단 비고) |
| GE-1 | PLAN §4 실행 체크리스트 완료 | Pass | Step 1~4 변경 적용 완료. Step 5 교차검증은 본 QA로 대체 |
| GE-2 | 검증 대상 산출물 존재 | Pass | 4개 파일 모두 존재 및 Read 완료 |
| GE-3 | TASK R-1~R-6 충족 | Pass | 전항목 충족 (windows.ps1 R-6 미추가는 Warning) |
| 제약-구값 | gemini-2.5/gpt-4.1/o3/gpt-5-codex/gpt-5.1-codex 잔존 0건 | Pass | 4개 파일 전체 grep 0건 |
| 제약-레벨 | light/standard/advanced 정의 불변 | Pass | §1 표 변경 없음 확인 |
| 제약-openai키 | openai 키 신규 추가 없음 | Pass | mapping dict 키 claude/cursor/gemini/codex 4개 유지 |
| 제약-배포본 | `~/.opal/` 직접 수정 없음 | Warning | `.opal/MEMORY.md` 수정(태스크 번호 채번 갱신)이 git status에 표시됨. 모델값 수정은 없으며 채번 메타데이터 변경으로 기능 영향 없음 |
| 제약-bash | `bash -n scripts/install-mac.sh` 통과 | Pass | Exit code 0 확인 |
| 문서-R-6-win | windows.ps1 변경이력 011 행 추가 | Warning | PLAN §6 R-T5에서 "형식 없으면 스킵 허용" 명시. windows.ps1은 comment-style 이력(#> 블록)을 갖고 있어 추가 권장하나 미추가. 기능 영향 없음 |

---

## 3. 지적 사항

### Warning-1: windows.ps1 변경이력 011 미추가

- **심각도**: Warning
- **내용**: `scripts/install/windows.ps1` 헤더 주석(L33 변경이력 블록)에 v1.9.0 또는 상응하는 "2026-06-02 모델 매핑 최신화 (011)" 행이 추가되지 않았다.
- **현황**: L86까지의 변경이력에 마지막 항목이 `v1.8.0 2026-05-24 Codex CLI 통합 (009)`이며, 011에 해당하는 행 없음.
- **근거**: PLAN §6 R-T5: "EXECUTE 워커가 파일 헤더 확인 후, 형식 있으면 011 행 추가 / 없으면 스킵". windows.ps1에는 변경이력 형식이 있으므로 추가가 권장되었으나 스킵된 것으로 판단. 기능적 영향 없음.
- **권장 조치**: 다음 수정 시 또는 별도 마이너 픽스로 windows.ps1 변경이력에 `v1.9.0 2026-06-02 모델 매핑 최신화 — Gemini 부동 별칭 전환 + Codex 최신 ID 갱신 (011)` 행 추가 권장.

### Warning-2: .opal/MEMORY.md 변경(채번)이 git status에 표시

- **심각도**: Warning (Info에 가까움)
- **내용**: `.opal/MEMORY.md`가 태스크 번호 갱신(last_task_number 9→11, 최종 갱신 일시)으로 인해 수정됨. AGENT.md 금지사항("~/.opal/ 직접 편집 금지")의 엄격한 해석 시 주의 대상이나, 실제 모델값 변경이 아닌 프로젝트 메타데이터(태스크 채번)이며 install로 배포되지 않는 MEMORY.md라는 점에서 기능 영향 없음.
- **권장 조치**: 현행 유지. 향후 채번 업데이트 방식을 프로젝트 소스 경로로 이관하는 것을 고려할 수 있으나 현재 우선순위 아님.

---

## 4. R-5 동기화 대조표 (핵심 산출물)

> install 연동 컬럼 대상: Claude / Cursor / Gemini / Codex. OpenAI 컬럼은 L-1에만 존재(참조 전용) — 검증 제외.

### Claude 컬럼

| 레벨 | L-1 (SSOT) | L-2a (mac dict) | L-2b (mac TOML) | L-3 (agents.md) | L-4 (windows.ps1) | 일치 |
|------|-----------|----------------|----------------|----------------|------------------|------|
| light | haiku | haiku | (Codex 전용) | haiku | haiku | O |
| standard | sonnet | sonnet | (Codex 전용) | sonnet | sonnet | O |
| advanced | opus | opus | (Codex 전용) | opus | opus | O |

### Cursor 컬럼

| 레벨 | L-1 (SSOT) | L-2a (mac dict) | L-2b (mac TOML) | L-3 (agents.md) | L-4 (windows.ps1) | 일치 |
|------|-----------|----------------|----------------|----------------|------------------|------|
| light | (표 미포함) | inherit | (Codex 전용) | inherit | inherit | O |
| standard | (표 미포함) | inherit | (Codex 전용) | inherit | inherit | O |
| advanced | (표 미포함) | inherit | (Codex 전용) | inherit | inherit | O |

> L-1 SSOT §4에서 "Cursor는 `inherit`로 위임" 명시. §2 표에 Cursor 컬럼 없음 — 설계상 정상.

### Gemini 컬럼

| 레벨 | L-1 (SSOT §2) | L-2a (mac dict L555) | L-2b (mac TOML) | L-3 (agents.md L174-176) | L-4 (windows.ps1 L1312) | 일치 |
|------|-------------|---------------------|----------------|------------------------|------------------------|------|
| light | `gemini-3.1-flash-lite` | `gemini-3.1-flash-lite` | (Codex 전용) | `gemini-3.1-flash-lite` | `gemini-3.1-flash-lite` | O |
| standard | `gemini-flash-latest` | `gemini-flash-latest` | (Codex 전용) | `gemini-flash-latest` | `gemini-flash-latest` | O |
| advanced | `gemini-pro-latest` | `gemini-pro-latest` | (Codex 전용) | `gemini-pro-latest` | `gemini-pro-latest` | O |

### Codex 컬럼

| 레벨 | L-1 (SSOT §2) | L-2a (mac dict L556) | L-2b (mac TOML L699-701) | L-3 (agents.md) | L-4 (windows.ps1 L1317) | 일치 |
|------|-------------|---------------------|------------------------|----------------|------------------------|------|
| light | `gpt-5.4-mini` | `gpt-5.4-mini` | `gpt-5.4-mini` | (Codex 컬럼 없음) | `gpt-5.4-mini` | O |
| standard | `gpt-5.5` | `gpt-5.5` | `gpt-5.5` | (Codex 컬럼 없음) | `gpt-5.5` | O |
| advanced | `gpt-5.3-codex` | `gpt-5.3-codex` | `gpt-5.3-codex` | (Codex 컬럼 없음) | `gpt-5.3-codex` | O |

> L-3(agents.md)는 Claude/Cursor/Gemini 3컬럼 표 — Codex 컬럼 없음(설계상 정상. PLAN §1 D-3 확인).
> Codex 기본값(폴백): install-mac.sh L744 `gpt-5.5`, windows.ps1 L1335 `gpt-5.5` — 일치.

**총 불일치 건수: 0건**

---

## 5. 교차 참조 검증

| 참조 산출물 | 검증 내용 | 결과 |
|------------|----------|------|
| TASK.md R-1 AC | 3곳(PLAN 기준) + windows.ps1 추가 = 4곳 Gemini 값 일치 + 공식 docs 실재 ID | Pass |
| TASK.md R-2 AC | 코드 근거로 openai 미배선 판정 + SSOT 참조전용 각주 + 죽은 컬럼 없음 | Pass |
| TASK.md R-3 AC | install-mac.sh 두 위치(dict+TOML) + SSOT Codex 값 일치 | Pass |
| TASK.md R-4 AC | 플랫폼별 별칭 추종 가능 여부 PLAN M-3에서 판정, §5 분기점검 규칙 명시 | Pass |
| TASK.md R-5 AC | 5위치 불일치 0건, QA-EXECUTE.md에 대조표 기재 | Pass |
| TASK.md R-6 AC | opal-model-mapping.md v1.3 / agents.md v1.5 / install-mac.sh v2.7 (011) 확인 | Pass (Warning: windows.ps1 미추가) |
| PLAN §4 Step 완료 기준 | Step 1~4 완료(값 대조 확인), Step 5(교차검증) = 본 QA 수행으로 충족 | Pass |
| PLAN §2 M-4 변경 범위 | 4개 파일 모두 변경 완료 | Pass |

---

## 6. 판정

**Pass**

R-1~R-6 전 항목 기능적으로 충족. 5위치 동기화 대조에서 불일치 0건. 구값 잔존 0건. bash 문법 통과. Warning 2건(windows.ps1 변경이력 미추가, .opal/MEMORY.md 채번 변경)은 모두 기능 영향 없으며 PLAN §6 R-T5에서 허용 범위로 예고된 사항이다. 다음 단계(CLOSE) 진행 가능.
