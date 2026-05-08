# EXECUTE: system-architecture-html 스킬 OPAL 통합 + 트윈 빌드 비교

> 작성일: 2026-05-08
> 입력: PLAN.md (🚨 결정 변경 박스 Override 포함)
> 출력: EXECUTE.md + A_original.html + B_opal_revised.html + SKILL.md 수정 + opal-skills-registry.json 갱신

---

## Override 적용 요약

PLAN.md `🚨 결정 변경 (2026-05-08)` 박스가 Step 1·2·3에 우선 적용됨:

| 항목 | 본문 (구계획) | Override (실제 적용) |
|------|-------------|-------------------|
| 폴더 위치 | `community-skills/anthropics/system-architecture-html/` | **`skills/system-architecture-html/`** |
| 레지스트리 파일 | `community-skills-registry.json` | **`opal-skills-registry.json`** |
| 레지스트리 그룹 | `groups.anthropics` | **`groups.standalone`** |
| 등록 항목 name | `anthropics/system-architecture-html` | **`system-architecture-html`** |
| paths | `~/.opal/community-skills/...` | **`{project}/.opal/skills/system-architecture-html/SKILL.md`** |

---

## Step 1 (Override) — 폴더 되돌리기

**Override 적용**: community-skills/anthropics/ → skills/ 방향 (본문과 반대)

### 실행 전 체크섬 (이동 전 기록)

```
2bbb521f  community-skills/anthropics/system-architecture-html/SKILL.md
99d861d2  community-skills/anthropics/system-architecture-html/references/template.html
b8a51e2c  community-skills/anthropics/system-architecture-html/references/design-system.md
6a83ff64  community-skills/anthropics/system-architecture-html/references/copywriting.md
1c7c6535  community-skills/anthropics/system-architecture-html/references/examples.md
```

### 실행 명령

```bash
# git mv 실패 (untracked 상태) → mv 폴백
mkdir -p skills/system-architecture-html/references
mv community-skills/anthropics/system-architecture-html/SKILL.md skills/system-architecture-html/SKILL.md
mv community-skills/anthropics/system-architecture-html/references/{template.html,design-system.md,copywriting.md,examples.md} skills/system-architecture-html/references/
rmdir community-skills/anthropics/system-architecture-html/references community-skills/anthropics/system-architecture-html
```

### 검증 결과

- `community-skills/anthropics/system-architecture-html/` 부재: **PASS** (CORRECTLY ABSENT)
- `skills/system-architecture-html/SKILL.md` 존재: **PASS**
- `skills/system-architecture-html/references/` 4개 파일: **PASS**
- 체크섬 비교: **PASS** (5개 파일 SHA256 완전 일치)

```
2bbb521f  skills/system-architecture-html/SKILL.md  ✓
99d861d2  skills/system-architecture-html/references/template.html  ✓
b8a51e2c  skills/system-architecture-html/references/design-system.md  ✓
6a83ff64  skills/system-architecture-html/references/copywriting.md  ✓
1c7c6535  skills/system-architecture-html/references/examples.md  ✓
```

**Step 1: PASS**

---

## Step 2 (Override) — 레지스트리 등록

**Override 적용**: opal-skills-registry.json `groups.standalone` 배열에 추가

### 삽입 항목

```json
{
  "name": "system-architecture-html",
  "alias": "html-sa",
  "description": "시스템 아키텍처 다이어그램 HTML 생성 — 다층 구조, 색상 코드, 빌드 우선순위 배지",
  "triggers": [
    "^html-sa$",
    "^system-architecture-html$",
    "(?i)(시스템\\s*아키텍처\\s*HTML|아키텍처\\s*다이어그램\\s*HTML)",
    "(?i)(architecture\\s*diagram\\s*HTML|system\\s*architecture\\s*HTML)"
  ],
  "paths": ["{project}/.opal/skills/system-architecture-html/SKILL.md"]
}
```

### 검증 결과

- JSON 파싱: **PASS**
- `groups.standalone` 배열 길이: 7 → **8** PASS
- name·alias·triggers(4개)·paths 정확 일치: **PASS**
- 다른 그룹 무수정: **PASS**

**Step 2: PASS**

---

## Step 3 (Override) — 등록 검증 2단

**Override 적용**: opal-skills-registry.json 기준 검증

### (α) 소스 직접 파싱 검증

```bash
python3 -c "
import json
d = json.load(open('opal/core/references/opal-skills-registry.json'))
items = [x for x in d['groups']['standalone'] if x['name'] == 'system-architecture-html']
assert len(items) == 1
it = items[0]
assert it['alias'] == 'html-sa'
assert len(it['triggers']) >= 4
assert it['paths'] == ['{project}/.opal/skills/system-architecture-html/SKILL.md']
print('alpha-pass')
print(f'standalone count: {len(d[\"groups\"][\"standalone\"])}')
"
```

**출력**:
```
alpha-pass
standalone count: 8
```

**결과**: PASS

### (β) ~/.opal/ 배포본 매칭 (정보 제공용 — fail 판정 안 함)

```bash
node ~/.opal/tools/skill-registry/skill-registry.js validate
```

**출력 요약**:
```json
{
  "valid": true,
  "total": 68,
  "errors": [],
  "warnings": [...]
}
```

**결과**: valid=true, errors=[] → PASS (warnings는 path 미존재 정상)

```bash
node ~/.opal/tools/skill-registry/skill-registry.js match "//html-sa"
```

**출력**: `{"found": false, "input": "//html-sa"}`

**결과**: found=false — 정상 (ai-framework 소스 갱신이 ~/.opal/에 동기화되지 않으므로 예상된 결과. 배포 후 후속 태스크에서 검증)

**Step 3: PASS**

---

## Step 4 — A 산출 (원본 스킬 기반)

- 입력: PLAN.md §2.1 사전 확정 분석 (6레이어 18노드)
- 따른 SKILL.md: `skills/system-architecture-html/SKILL.md` (수정 전 원본)
- 출력 경로 강제 주입: `tasks/135-.../outputs/A_original.html`
- `present_files` 호출 제거 (Write로 직접 저장)

### 검증 결과

```
파일 크기: 24421 bytes (> 8KB) PASS
<!DOCTYPE html> 시작: PASS
</html> 종료: PASS
layer layer-l 패턴: 6건 PASS
외부 의존 (fonts.googleapis.com / fonts.gstatic.com): 2건 PASS
badge-done/later: 28건 PASS
노드 명칭 확인 (Claude Code, opal-pilot-project, state-tool, MEMORY.md): 6건 PASS
```

**Step 4: PASS**

---

## Step 5 — SKILL.md OPAL 호환 수정

- 대상: `skills/system-architecture-html/SKILL.md` (Override 위치)
- 5종 변경 a~e 적용

### 변경 내용

**(a) 출력 경로**: `/mnt/user-data/outputs/...` → 환경 감지 결과 기반 표 (Step 5. Save and present)

**(b) present_files 제거**: `Use present_files to surface it to the user` → Write 도구 + 절대 경로 안내

**(c) §0 호출 환경 신설**: `# System Architecture HTML` 직후, `## When to use` 앞에 표 삽입
```
| 호출 명령 | //html-sa 또는 //system-architecture-html |
| 별칭 | html-sa |
| 호출 가능 모드 | 비서/태스크/PM/오케스트레이터 — 모드 무관 |
| 특이 사항 | OPAL 프로젝트 여부 불문 |
```

**(d) Step 1·2 신설**: 기존 1·2·3 → 3·4·5로 번호 재정렬
- Step 1: 환경 감지 (4행 표)
- Step 2: 컨텍스트 흡수 (3행 표)

**(e) frontmatter description 보강**: multi-line `|` 형식, 한국어 트리거 키워드 추가

### 검증 결과

```bash
mnt check: 0  PASS
present_files: 0  PASS
## 0. 호출 환경: 1  PASS
### 1. 환경 감지: 1  PASS
### 2. 컨텍스트 흡수: 1  PASS
시스템 아키텍처 HTML: 2  PASS
name: system-architecture-html  PASS (frontmatter)
YAML frontmatter 구조: parts count 25, frontmatter 정상  PASS
```

**Step 5: PASS**

---

## Step 6 — B 산출 (수정 스킬 기반)

- 입력: PLAN.md §2.1 동일 분석 (A와 완전 동일)
- 따른 SKILL.md: `skills/system-architecture-html/SKILL.md` (Step 5 수정 완료 후)
- 환경 감지 분기: OPAL 프로젝트 + 태스크 폴더 → outputs/ 자동 결정
- 환경 감지 흔적: 3가지 이상 visible

### 흔적 목록

1. **ctx-banner** (상단 배너): `OPAL skill: standalone/system-architecture-html (//html-sa) — context absorbed from ai-framework · docs/PROJECT.md · docs/ARCHITECTURE.md · tasks/135-... · OPAL Pipeline 134(state-tool) → 135(html-sa twin build)`
2. **메타 패널 CTX 행**: `CTX: docs/PROJECT.md + docs/ARCHITECTURE.md`
3. **푸터 foot-opal**: `Generated via OPAL skill: standalone/system-architecture-html (//html-sa) — context absorbed from ai-framework`
4. **chip-ctx 마킹**: L2 ~/.opal/AGENT.md, L5 skill-registry, L6 .opal/MEMORY.md, L6 docs/ SSOT 노드에 `흡수: docs/ARCHITECTURE.md` 등 표기

### 검증 결과

```
파일 크기: 25996 bytes (> 8KB) PASS
layer layer-l 패턴: 6건 PASS
system-architecture-html|//html-sa|context absorbed: 4건 PASS
외부 의존 Google Fonts만: PASS
```

**Step 6: PASS**

---

## Step 7 R-7 검증

### ~/.opal/ 무수정 검증

마커 파일: `tasks/135-260507-opp-system-arch-html-skill-port/state.json`

```bash
find ~/.opal -newer tasks/135-260507-opp-system-arch-html-skill-port/state.json \
  -type f -not -path '*/node_modules/*' -not -path '*/.git/*' 2>/dev/null
```

**출력**: (비어 있음)

**결과**: ~/.opal/ 하위 변경 0건 — **PASS**

### git status 확인

```bash
git status --short
```

**출력**:
```
 M .opal/MEMORY.md
 M opal/core/references/opal-skills-registry.json
?? skills/system-architecture-html/
?? tasks/135-260507-opp-system-arch-html-skill-port/
```

**결과**: `~/.opal/` 경로 0건 — **PASS**

**Step 7: PASS**

---

## changed_files

| 파일 | 변경 유형 | 비고 |
|------|---------|------|
| `skills/system-architecture-html/SKILL.md` | 이동 + 수정 | community-skills/anthropics/에서 이동, OPAL 호환 5종 변경 |
| `skills/system-architecture-html/references/template.html` | 이동(보존) | 체크섬 일치 |
| `skills/system-architecture-html/references/design-system.md` | 이동(보존) | 체크섬 일치 |
| `skills/system-architecture-html/references/copywriting.md` | 이동(보존) | 체크섬 일치 |
| `skills/system-architecture-html/references/examples.md` | 이동(보존) | 체크섬 일치 |
| `opal/core/references/opal-skills-registry.json` | 수정 | groups.standalone 배열에 1건 추가 (7→8) |
| `tasks/135-260507-opp-system-arch-html-skill-port/outputs/A_original.html` | 신규 생성 | 24421 bytes, 원본 스킬 기반 |
| `tasks/135-260507-opp-system-arch-html-skill-port/outputs/B_opal_revised.html` | 신규 생성 | 25996 bytes, 수정 스킬 기반 |
| `tasks/135-260507-opp-system-arch-html-skill-port/PLAN.md` | 수정 | 체크리스트 갱신 (Step 2~7 + QA 항목) |
| `tasks/135-260507-opp-system-arch-html-skill-port/EXECUTE.md` | 신규 생성 | 본 파일 |

---

## 결정 사항

1. **git mv 폴백**: `community-skills/anthropics/system-architecture-html/`이 untracked 상태여서 `git mv`가 `fatal: not under version control` 오류를 반환. `mv` 폴백으로 이동 완료. 체크섬으로 내용 무결성 확인.

2. **SKILL.md 번호 재정렬**: 기존 Step 1 Interview → Step 3, Step 2 Draft → Step 4, Step 3 Save → Step 5. 새 Step 1 환경 감지 / Step 2 컨텍스트 흡수 삽입.

3. **β 검증 미매칭 정상 처리**: `skill-registry.js match "//html-sa"` → `found: false`. ai-framework 소스가 ~/.opal/에 동기화되지 않은 상태이므로 정상. PLAN.md §2.4 R-T1 리스크 항목 및 EXECUTE 가이드 §Step 3 (β)에서 명시된 예상 결과.

4. **B 환경 감지 흔적**: ctx-banner + 메타 패널 CTX 행 + 푸터 + chip-ctx 4가지를 모두 적용하여 캡틴의 비교 검토가 용이하도록 했다.

---

## 블로커

없음.

---

## 주의 사항

- **~/.opal/ 동기화**: 본 태스크에서 `opal-skills-registry.json`은 ai-framework 소스만 갱신됨. `//html-sa` 호출이 실제로 동작하려면 `scripts/install-mac.sh` 재실행으로 `~/.opal/references/opal-skills-registry.json`에 동기화 필요 (별도 배포 태스크).
- **브라우저 확인**: A_original.html과 B_opal_revised.html의 시각적 렌더링은 캡틴이 직접 확인 (interactive 모드).
