/**
 * @header {
 *   "module": "test-regression",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — 소비자 파급(이 저장소 8커맨드·brain-tool sync-header 무수정 전달)·.gitignore 예외 반전·골든 재캡처 바이트 동일·픽스처 계약·규칙 문서 5종 + docs/ 3종 산출물 검사·auto 잔존 0·모드 판정 지점 봉인(TS-070) 회귀 테스트 (F-005/F-006/F-007, 태스크 080)",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "080",
 *   "scenarios": ["S-14", "S-15", "S-16", "S-17", "S-18"]
 * }
 */
//
// [Task 080 재작성 — 계약 이전이지 테스트 약화가 아니다]
// 077이 고정한 회귀 자산 중 두 축이 080에서 방향을 바꾼다.
//  (1) `.opal/code-scan.json` 무시 여부 — 077은 "계속 무시되어야 함(exit 0)"을 단언했다
//      (구 `test-regression.js:126-127`). 080은 `headerSource` 미설정 시 전 명령이 차단되므로
//      이 파일이 **저장소가 동작하기 위한 필수 계약**이 된다(PLAN §3.5.3). 추적되지 않으면 신규
//      clone·CI에서 저장소 자신이 즉시 `header_source_unset`으로 멎는다. 따라서 `.gitignore`에
//      `!.opal/code-scan.json` 예외를 채택하고 단언을 **비무시(exit 1)로 반전**한다(TS-046).
//      `.opal/code-map/index.json`의 비무시 단언(TS-047)은 **불변**으로 유지한다.
//  (2) 문서 산출물 검사 — 077이 고정한 "4단 기록 위치 판정(reason 4값)"은 `auto` 시대의 서술이다.
//      080은 `reason`/`write_to`를 각 **3값** 폐쇄 도메인으로 재정의하므로(PLAN §3.6.2 (2)),
//      077 TS-049의 `readonly_repo`/`inline_exists`/`legacy_no_header` 존재 단언은 그 **반대 방향**
//      (신 3값 존재 + 구 4값 잔존 0)으로 재고정된다(TS-053).
// 두 반전 모두 기대값을 느슨하게 바꿔 통과시키는 것이 아니라, 같은 불변식을 신 계약 위에서 **같은
// 강도로 다시 고정**하는 계약 이전이다. 077 자산 중 방향이 바뀌지 않은 것(픽스처 이중 격리·테스트
// 파일 @header 자산화·"별도 도구 없음" 0건·brain-tool README 2소스·PM Gate `validate --changed`)은
// 그대로 승계해 회귀 가드로 남긴다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
// 기대값 완화로 통과를 유도하는 것은 reward hacking이다.
//
// [MUST] **TS-ID 네임스페이스** (PLAN §3.7.2 각주): 본 태스크(080)의 TS-ID와 077의 TS-ID는 서로 다른
// 번호 체계다. 077 자산을 가리킬 때는 항상 `077 TS-NNN`으로 표기한다 — 특히 본 PLAN에도 TS-044~047이
// 있으므로 077 TS-044~047·077 TS-055와 혼동하면 엉뚱한 테스트를 지운다.
//
// TC ↔ TS-ID ↔ S-ID 매핑 표 (PLAN.md §3.5.5/§3.6.5/§3.7.5, TEST-SCENARIO.md §3 S-14~S-18 / §4):
//
// | 케이스 프리픽스                  | TS-ID              | S-ID | 현 시점 기대 |
// |----------------------------------|--------------------|------|--------------|
// | [T080/L2-F12a]                   | TS-044, TS-046, TS-047 | S-14, S-15 | RED(설정·gitignore 미반영) |
// | [T080/L2-F12c]                   | TS-045             | S-14 | RED(게이트 미구현) |
// | [T080/L2-F13]                    | TS-060, TS-061, TS-064 | S-17 | TS-060/064 PASS(기준선 유효성) · TS-061 RED |
// | [T080/L2-완료기준]                | TS-062, TS-063     | S-16 | TS-063 PASS · TS-062 RED |
// | [T080/L2-F11]                    | TS-050~TS-055      | S-18 | RED(문서 미갱신) |
// | [T080/L2-F11b]                   | TS-066, TS-067     | S-18 | RED |
// | [T080/L2-F11c]                   | TS-068             | S-18 | RED |
// | [T080/L2-F11d]                   | TS-070, TS-071     | S-18 | TS-070 RED · TS-071 PASS(봉인) |
// | 077 자산 유지                     | 077 TS-052/053/057/048/051 | S-19, S-21 | PASS(회귀 가드) |
//
// [MUST] red-first.md §4 — 공개 인터페이스로만 검증한다: 실 CLI subprocess의 exit code·stdout·stderr,
// 실 `git check-ignore`, 실 `brain-tool` subprocess, 그리고 산출물 파일(문서·골든·소스)의 내용.
// mock 금지 — 어떤 케이스도 code-scan/brain-tool의 내부 함수를 스텁하지 않는다.
// 픽스처·골든은 수정하지 않는다(읽기 전용). TS-045만 임시 트리를 만들고 종료 시 파기한다.
//
// ─────────────────────────────────────────────────────────────────────────────
// [메타테스트 재귀 가드 규약 — 3파일 공통, 동일 문구] (083)
//   가드 환경변수: `CODE_SCAN_META_CHILD` — 유일한 규약이다. 새 이름을 만들지 않는다.
//   대상: 전 스위트를 재실행하는 "메타테스트" 3종
//         test-shard-policy.js TS-080 · test-regression.js TS-062 · test-shard.js S-19
//   ① 각 메타테스트는 함수 진입부에서 `process.env.CODE_SCAN_META_CHILD === '1'`이면 본문을
//      수행하지 않고 즉시 `return`한다(= 통과 처리). 자식 프로세스에서는 메타테스트를 돌리지 않는다.
//   ② 각 메타테스트가 자식 스위트를 `spawnSync`할 때 `env`에 `CODE_SCAN_META_CHILD='1'`을 주입한다.
//      기존 `NODE_TEST_CONTEXT`/`NODE_TEST_WORKER_ID` 제거와 `OPAL_HOME` 관련 주입은 그대로 보존한다.
//   ③ 근거: 가드가 세 메타테스트 중 하나에만 걸려 있으면 서로를 재실행해 타임아웃 예산이 곱해져
//      발산한다(083 Step 11 실측 — TS-080 370,651ms/상한 60초, TS-062·S-19 상한 정각 초과).
//      상한 상향은 처방이 아니다 — 가드를 한 종으로 통일해 곱셈을 끊는 것이 처방이다.
//   ④ 네 번째 메타테스트를 추가할 때도 이 규약을 그대로 따른다. 가드 경로에 `skip`·`todo` 마킹을
//      쓰지 않는다(TS-085의 "skip·todo 0건" 감사와 충돌하며, 단언 완화로 오인된다).
// ─────────────────────────────────────────────────────────────────────────────
//
// 변경이력:
//   v1.0 2026-07-28 KST: RED-first 최초 작성 (태스크 077, opal-test-agent mode:red)
//   v2.0 2026-08-02 KST: 태스크 080 RED 재작성 — 077 TS-055 gitignore 단언 반전(TS-046/047),
//     문서 산출물 검사를 신 3값 도메인 기준으로 재고정(TS-050~055/067/068), `auto` 자산 잔존
//     0건(TS-066), 모드 판정 지점 화이트리스트 봉인(TS-070) 신설, brain-tool 무수정 전달(TS-045),
//     골든 바이트 동일·픽스처 계약(TS-060~064) 이전 (opal-test-agent mode:red)
//   v2.1 2026-08-04 KST: 공용 `run()` 헬퍼에 `OPAL_HOME` 주입(가짜 홈 격리, H-4, 태스크 083)
//   v2.2 2026-08-04 18:06 KST: TS-062 재귀 가드를 공통 규약 `CODE_SCAN_META_CHILD`로 일원화 (083)
//     — 구 `T080_SUITE_CHILD`(이 파일 단독 규약)를 폐기하고 위 규약 ①②를 적용. `skip:` 옵션 →
//     함수 진입부 조기 return으로 교체(규약 ④, 스킵 표기 증가 방지). 단언 삭제·완화 0건
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const TOOL_DIR = path.resolve(__dirname, '..');
const CODE_SCAN_JS = path.join(TOOL_DIR, 'code-scan.js');
const FIX = path.resolve(__dirname, 'fixtures');
const GOLDEN = path.join(FIX, 'golden');
const LEGACY_REPO = path.join(FIX, 'legacy-repo');
const REPO_ROOT = path.resolve(TOOL_DIR, '..', '..', '..'); // opal/tools/code-scan -> repo root
const CORE_REF = path.join(REPO_ROOT, 'opal', 'core', 'references');
const DOCS = path.join(REPO_ROOT, 'docs');
const BRAIN_TOOL_PY = path.join(REPO_ROOT, 'opal', 'tools', 'brain-tool', 'brain_tool.py');
// [MUST] 083부터 code-scan이 ~/.opal/setting.json(샤드 정책)을 읽는다 — OPAL_HOME을 주입하지
// 않으면 개발자 실제 홈이 결과에 유입된다(H-4). 기본 격리는 homes/absent(setting.json 없음 → 코드 상수 폴백).
const HOME_ABSENT = path.join(FIX, 'shard-policy', 'homes', 'absent');

function run(cwd, args) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 20000,
    env: Object.assign({}, process.env, { OPAL_HOME: HOME_ABSENT }),
  });
  return { exitCode: result.status, stdout: result.stdout || '', stderr: result.stderr || '' };
}

// 8커맨드 (제약② 조회 경로) — 골든 파일명 동반
const GOLDEN_COMMANDS = [
  { args: ['scan', '--json'], golden: 'scan.json' },
  { args: ['domain'], golden: 'domain.txt' },
  { args: ['layer'], golden: 'layer.txt' },
  { args: ['search', 'auth', '--json'], golden: 'search.json' },
  { args: ['exports', 'token', '--json'], golden: 'exports.json' },
  { args: ['summary'], golden: 'summary.txt' },
  { args: ['depends', 'auth_service'], golden: 'depends.txt' },
  { args: ['missing'], golden: 'missing.txt' },
];

// ═════════════════════════════════════════════════════════════════════════
// 소스 산출물 검사 공용 — JS 어휘 분류기 (TS-066 / TS-070)
//
// PLAN §3.1.5는 "문자열 리터럴 내부·주석 내부는 제외"를 요구한다. 줄 단위 정규식으로 문자열을
// 지우면 (a) `const USAGE = ` ... `` 처럼 **여러 줄에 걸친 템플릿 리터럴**과 (b) 템플릿 안의
// `${...}` **코드 구간**을 구분하지 못한다 — 전자는 USAGE 설정 예시(`code-scan.js:108`)를 코드로
// 오인해 영구 오탐을 만들고, 후자는 `` `${ctx.headerSource}` `` 같은 실제 참조를 놓친다(미탐).
// 그래서 파일 전체를 한 번 훑어 문자 단위로 code/string/comment/regex를 판정한다.
// ═════════════════════════════════════════════════════════════════════════

function classifySource(src) {
  const kind = new Array(src.length).fill('code');
  const stack = [{ t: 'code', depth: 0 }];
  const top = () => stack[stack.length - 1];
  const REGEX_PREV = '(,=:[!&|?{};+-*%~^<>\n';
  const REGEX_KEYWORDS = ['return', 'typeof', 'case', 'in', 'of', 'new', 'delete', 'void', 'instanceof', 'do', 'else', 'yield'];
  let lastSig = '';
  let lastWord = '';
  let i = 0;

  while (i < src.length) {
    const st = top();
    const ch = src[i];

    if (st.t === 'tpl') {
      if (ch === '\\') { kind[i] = 'string'; if (i + 1 < src.length) kind[i + 1] = 'string'; i += 2; continue; }
      if (ch === '`') { kind[i] = 'string'; i++; stack.pop(); lastSig = '`'; lastWord = ''; continue; }
      if (ch === '$' && src[i + 1] === '{') {
        kind[i] = 'string'; kind[i + 1] = 'string'; i += 2;
        stack.push({ t: 'code', depth: 0 });
        lastSig = '('; lastWord = '';
        continue;
      }
      kind[i] = 'string'; i++; continue;
    }

    // st.t === 'code'
    if (ch === '/' && src[i + 1] === '/') {
      while (i < src.length && src[i] !== '\n') { kind[i] = 'comment'; i++; }
      lastSig = '\n'; lastWord = '';
      continue;
    }
    if (ch === '/' && src[i + 1] === '*') {
      kind[i] = 'comment'; kind[i + 1] = 'comment'; i += 2;
      while (i < src.length && !(src[i] === '*' && src[i + 1] === '/')) { kind[i] = 'comment'; i++; }
      if (i < src.length) { kind[i] = 'comment'; kind[i + 1] = 'comment'; i += 2; }
      continue;
    }
    if (ch === '/') {
      const isRegex = lastSig === '' || REGEX_PREV.includes(lastSig) || REGEX_KEYWORDS.includes(lastWord);
      if (isRegex) {
        kind[i] = 'regex'; i++;
        let inClass = false;
        while (i < src.length) {
          const c = src[i];
          kind[i] = 'regex';
          if (c === '\\') { if (i + 1 < src.length) kind[i + 1] = 'regex'; i += 2; continue; }
          if (c === '[') inClass = true;
          else if (c === ']') inClass = false;
          else if (c === '/' && !inClass) { i++; break; }
          else if (c === '\n') { break; }
          i++;
        }
      } else { i++; }
      lastSig = '/'; lastWord = '';
      continue;
    }
    if (ch === "'" || ch === '"') {
      const q = ch;
      kind[i] = 'string'; i++;
      while (i < src.length) {
        kind[i] = 'string';
        if (src[i] === '\\') { if (i + 1 < src.length) kind[i + 1] = 'string'; i += 2; continue; }
        if (src[i] === q) { i++; break; }
        if (src[i] === '\n') { i++; break; }
        i++;
      }
      lastSig = q; lastWord = '';
      continue;
    }
    if (ch === '`') { kind[i] = 'string'; i++; stack.push({ t: 'tpl' }); continue; }
    if (ch === '{') { st.depth++; lastSig = ch; lastWord = ''; i++; continue; }
    if (ch === '}') {
      st.depth--;
      if (st.depth < 0 && stack.length > 1) { stack.pop(); i++; lastSig = '}'; lastWord = ''; continue; }
      lastSig = ch; lastWord = ''; i++; continue;
    }
    if (/\s/.test(ch)) { if (ch === '\n') { lastSig = lastSig || '\n'; } i++; continue; }
    if (/[A-Za-z0-9_$]/.test(ch)) {
      let j = i;
      while (j < src.length && /[A-Za-z0-9_$]/.test(src[j])) j++;
      lastWord = src.slice(i, j);
      lastSig = src[j - 1];
      i = j;
      continue;
    }
    lastSig = ch; lastWord = ''; i++;
  }
  return kind;
}

function analyzeJs(file) {
  const src = fs.readFileSync(file, 'utf8');
  const kind = classifySource(src);
  // 코드가 아닌 문자는 공백으로 치환 (열 위치 보존)
  const codeChars = new Array(src.length);
  for (let i = 0; i < src.length; i++) codeChars[i] = (kind[i] === 'code' || src[i] === '\n') ? src[i] : ' ';
  const codeSrc = codeChars.join('');

  const lineStarts = [0];
  for (let i = 0; i < src.length; i++) if (src[i] === '\n') lineStarts.push(i + 1);
  const lineOf = (idx) => {
    let lo = 0, hi = lineStarts.length - 1;
    while (lo < hi) { const m = (lo + hi + 1) >> 1; if (lineStarts[m] <= idx) lo = m; else hi = m - 1; }
    return lo + 1; // 1-based
  };
  const lineText = (n) => {
    const s = lineStarts[n - 1];
    const e = n < lineStarts.length ? lineStarts[n] - 1 : src.length;
    return src.slice(s, e);
  };
  const codeLineText = (n) => {
    const s = lineStarts[n - 1];
    const e = n < lineStarts.length ? lineStarts[n] - 1 : src.length;
    return codeSrc.slice(s, e);
  };

  // ① 허용 영역의 줄 범위를 중괄호 깊이 계산으로 확정한다 (정규식 아님)
  function funcRange(name) {
    const re = new RegExp('^function\\s+' + name + '\\s*\\(', 'm');
    const m = re.exec(src);
    if (!m || kind[m.index] !== 'code') return null;
    let depth = 0, started = false;
    for (let i = m.index; i < src.length; i++) {
      if (kind[i] !== 'code') continue;
      if (src[i] === '{') { depth++; started = true; }
      else if (src[i] === '}') {
        depth--;
        if (started && depth === 0) return [lineOf(m.index), lineOf(i)];
      }
    }
    return null;
  }

  // 최상위 `const NAME = ...;` 선언의 줄 범위 (템플릿 리터럴 포함 — 종결 세미콜론까지)
  function declRange(name) {
    const re = new RegExp('^const\\s+' + name + '\\s*=', 'm');
    const m = re.exec(src);
    if (!m || kind[m.index] !== 'code') return null;
    let curly = 0, paren = 0, square = 0;
    for (let i = m.index; i < src.length; i++) {
      if (kind[i] !== 'code') continue;
      const c = src[i];
      if (c === '{') curly++; else if (c === '}') curly--;
      else if (c === '(') paren++; else if (c === ')') paren--;
      else if (c === '[') square++; else if (c === ']') square--;
      else if (c === ';' && curly === 0 && paren === 0 && square === 0) return [lineOf(m.index), lineOf(i)];
    }
    return null;
  }

  function occurrences(pattern) {
    const re = new RegExp(pattern.source, pattern.flags.includes('g') ? pattern.flags : pattern.flags + 'g');
    const out = [];
    let m;
    while ((m = re.exec(src)) !== null) {
      const line = lineOf(m.index);
      const ls = lineStarts[line - 1];
      const le = line < lineStarts.length ? lineStarts[line] - 1 : src.length;
      out.push({
        index: m.index,
        line,
        kind: kind[m.index],
        text: m[0],
        before: codeSrc.slice(ls, m.index),
        after: codeSrc.slice(m.index + m[0].length, le),
        raw: src.slice(ls, le),
      });
    }
    return out;
  }

  return { src, kind, funcRange, declRange, occurrences, lineText, codeLineText };
}

const inRange = (line, range) => !!range && line >= range[0] && line <= range[1];

// ═════════════════════════════════════════════════════════════════════════
// 문서 산출물 검사 공용
// ═════════════════════════════════════════════════════════════════════════

const RULE_DOCS = {
  headerStandard: path.join(CORE_REF, 'header-standard.md'),
  headerRules: path.join(CORE_REF, 'harness', 'header-rules.md'),
  codeScanMgmt: path.join(CORE_REF, 'pm', 'code-scan-management.md'),
  pmReviewGate: path.join(CORE_REF, 'harness', 'pm-review-gate.md'),
  toolsMd: path.join(CORE_REF, 'tools.md'),
};
const DOCS_TARGETS = {
  conventions: path.join(DOCS, 'CONVENTIONS.md'),
  architecture: path.join(DOCS, 'ARCHITECTURE.md'),
  project: path.join(DOCS, 'PROJECT.md'),
};
const LEGACY_ASSET_DOCS = {
  brainReadme: path.join(REPO_ROOT, 'opal', 'tools', 'brain-tool', 'README.md'),
  opalHarness: path.join(CORE_REF, 'opal-harness.md'),
};

/** 변경이력 구역(문서 말미)의 시작 줄 인덱스 — 이후는 "과거 기록"이므로 잔존 검사 대상에서 제외한다. */
function changelogStart(lines) {
  for (let i = lines.length - 1; i >= 0; i--) {
    if (/^#{0,6}\s*변경이력\s*:?\s*$/.test(lines[i].trim())) return i;
  }
  return lines.length;
}

/** 변경이력 구역을 제외한 본문 줄 목록 — [{n, text}] */
function bodyLines(file) {
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const cut = changelogStart(lines);
  return lines.slice(0, cut).map((text, idx) => ({ n: idx + 1, text }));
}

/** 변경이력 구역의 줄 목록 */
function changelogLines(file) {
  const lines = fs.readFileSync(file, 'utf8').split('\n');
  const cut = changelogStart(lines);
  return lines.slice(cut).map((text, idx) => ({ n: cut + idx + 1, text }));
}

/** 마크다운 섹션 본문 추출 — 헤딩 정규식에 매칭되는 절의 다음 헤딩 직전까지 */
function mdSection(text, headingRe) {
  const lines = text.split('\n');
  const start = lines.findIndex(l => /^#{1,6}\s/.test(l) && headingRe.test(l));
  if (start < 0) return null;
  const out = [];
  for (let i = start + 1; i < lines.length; i++) {
    if (/^#{1,6}\s/.test(lines[i])) break;
    out.push(lines[i]);
  }
  return out.join('\n');
}

/**
 * `headerSource` 값 도메인을 서술하는 문맥의 줄만 추린다 (TS-067).
 * 무관한 `auto`(`--owner <...|auto>`·`--auto-pass`·`auto-detect`·스크립트 파일명)를 오탐하지 않기 위해
 * ① 줄 자체에 headerSource가 있거나 ② 소속 절 제목에 headerSource가 있거나
 * ③ 소속 펜스 코드블록 안에 headerSource가 있는 줄만 대상으로 한다.
 */
function headerSourceContextLines(file) {
  const all = bodyLines(file);
  const fenceOwner = new Map();  // 줄 인덱스 -> 블록 id
  const fenceHas = new Map();    // 블록 id -> headerSource 포함 여부
  const sectionOwner = new Map();
  const sectionHas = new Map();
  let fenceId = null, fenceCount = 0;
  let sectionId = 0;
  sectionHas.set(0, false);

  for (const { n, text } of all) {
    if (/^\s*```/.test(text)) {
      if (fenceId === null) { fenceCount++; fenceId = fenceCount; fenceHas.set(fenceId, false); }
      else { fenceId = null; }
      continue;
    }
    if (fenceId === null && /^#{1,6}\s/.test(text)) {
      sectionId++;
      sectionHas.set(sectionId, /headerSource/.test(text));
      continue;
    }
    if (fenceId !== null) {
      fenceOwner.set(n, fenceId);
      if (/headerSource/.test(text)) fenceHas.set(fenceId, true);
    }
    sectionOwner.set(n, sectionId);
  }

  return all.filter(({ n, text }) => {
    if (/headerSource/.test(text)) return true;
    if (sectionHas.get(sectionOwner.get(n))) return true;
    const f = fenceOwner.get(n);
    return f !== undefined && fenceHas.get(f) === true;
  });
}

const DEPRECATION_MARK = /제거|deprecated|폐기|삭제|더 이상|무시(?!하지)|미사용|사용하지\s*않/;

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F12a] S-14·S-15 — 이 저장소 설정 + .gitignore 예외 (TS-044, TS-046, TS-047)
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F12a] TS-044 (S-14): 이 저장소 .opal/code-scan.json에 전역 headerSource "inline"이 명시된다', () => {
  const cfgPath = path.join(REPO_ROOT, '.opal', 'code-scan.json');
  assert.ok(fs.existsSync(cfgPath), `.opal/code-scan.json이 존재해야 함: ${cfgPath}`);
  const cfg = JSON.parse(fs.readFileSync(cfgPath, 'utf8'));
  // [RED 기대] Step 9 미완료 — 현재 이 저장소 설정에는 headerSource 키가 없다.
  assert.strictEqual(cfg.headerSource, 'inline',
    '[RED expect] 이 저장소는 인라인 @header 자산을 보유하므로 전역 headerSource가 "inline"이어야 한다 (PLAN §3.5.3). ' +
    `got ${JSON.stringify(cfg.headerSource)}`);
});

test('[T080/L2-F12a] TS-044 (S-14): 이 저장소 루트에서 8커맨드가 전부 exit 0 (게이트가 자기 저장소를 막지 않는다)', () => {
  const failures = [];
  for (const c of GOLDEN_COMMANDS) {
    const { exitCode, stdout, stderr } = run(REPO_ROOT, c.args);
    if (exitCode !== 0) failures.push(`${c.args.join(' ')} -> exit ${exitCode} | stdout=${stdout.slice(0, 200)} | stderr=${stderr.slice(0, 200)}`);
  }
  assert.deepStrictEqual(failures, [],
    '전 명령 차단 게이트 도입 후에도 이 저장소 루트의 조회 8커맨드는 exit 0이어야 한다 (F-12① AC)');
});

test('[T080/L2-F12a] TS-046 (S-15): git check-ignore .opal/code-scan.json → exit 1 (비무시) — 077 TS-055 반전', () => {
  // 주의(077 승계): `-v`를 붙이면 negation 패턴이 매치돼도 exit 0을 반환하는 git 고유 동작이 있어
  // exit code만으로 무시 여부를 판별할 수 없다. 판별은 `-v` 없이, `-v`는 진단 출력 용도로만 쓴다.
  const r = spawnSync('git', ['check-ignore', '.opal/code-scan.json'], { cwd: REPO_ROOT, encoding: 'utf8' });
  const rv = spawnSync('git', ['check-ignore', '-v', '.opal/code-scan.json'], { cwd: REPO_ROOT, encoding: 'utf8' });
  // [RED 기대] `.gitignore`에 `!.opal/code-scan.json` 예외가 아직 없다 → 현재 exit 0(무시됨).
  assert.strictEqual(r.status, 1,
    '[RED expect] headerSource 미설정 시 전 명령이 차단되므로 이 설정 파일은 필수 계약이 된다 — 추적되지 않으면 ' +
    `신규 clone·CI에서 저장소가 즉시 멎는다(PLAN §3.5.3). exit 1(비무시) 기대, got ${r.status}, 매칭 패턴: ${rv.stdout.trim()}`);
});

test('[T080/L2-F12a] TS-047 (S-15): git check-ignore .opal/code-map/index.json → exit 1 유지 (077 단언 불변)', () => {
  const r = spawnSync('git', ['check-ignore', '.opal/code-map/index.json'], { cwd: REPO_ROOT, encoding: 'utf8' });
  const rv = spawnSync('git', ['check-ignore', '-v', '.opal/code-map/index.json'], { cwd: REPO_ROOT, encoding: 'utf8' });
  assert.strictEqual(r.status, 1,
    `.opal/code-map/index.json 비무시 단언은 080에서도 불변이다. exit 1 기대, got ${r.status}, 매칭 패턴: ${rv.stdout.trim()}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F12c] S-14 — brain-tool sync-header 실패 사유 전달 (TS-045)
//
// mock 금지: 실 `brain_tool.py`를 실 subprocess로 돌린다. brain_tool은 code-scan.js를
// `~/.opal/tools/code-scan/code-scan.js` → (부재 시) `<cwd>/opal/tools/code-scan/code-scan.js`
// 순으로 찾으므로(`brain_tool.py:779-783`), HOME을 임시 디렉토리로 돌려 **배포본이 아니라 이 저장소의
// 소스 code-scan.js**가 실행되게 한다. 배포 시점에 결과가 좌우되면 검증이 아니다.
// ═════════════════════════════════════════════════════════════════════════

function makeUnsetTree() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 't080-brain-'));
  fs.mkdirSync(path.join(root, '.opal', 'brain'), { recursive: true });
  fs.mkdirSync(path.join(root, 'opal', 'tools', 'code-scan'), { recursive: true });
  fs.mkdirSync(path.join(root, 'src'), { recursive: true });
  fs.mkdirSync(path.join(root, 'fakehome', '.opal', 'tools'), { recursive: true });
  // brain 초기화 판정은 SCHEMA.md 존재 여부만 본다 (brain_tool.py:241-243)
  fs.writeFileSync(path.join(root, '.opal', 'brain', 'SCHEMA.md'), '# stub schema\n');
  // headerSource가 **없는** 설정 — 게이트 대상
  fs.writeFileSync(path.join(root, '.opal', 'code-scan.json'), JSON.stringify({
    scopes: { src: 'src/' }, extensions: ['.js'], exclude: [], excludePatterns: [],
  }, null, 2) + '\n');
  fs.writeFileSync(path.join(root, 'src', 'a.js'), 'const a = 1;\n');
  fs.symlinkSync(CODE_SCAN_JS, path.join(root, 'opal', 'tools', 'code-scan', 'code-scan.js'));
  // date.js는 실물이 필요하다 (sync-header 후반 경로). code-scan만 배포본에서 떼어낸다.
  fs.symlinkSync(path.join(os.homedir(), '.opal', 'tools', 'date'), path.join(root, 'fakehome', '.opal', 'tools', 'date'));
  return root;
}

test('[T080/L2-F12c] TS-045 (S-14): 미설정 트리에서 brain-tool sync-header 실패 detail에 header_source_unset이 실린다', () => {
  const venvPython = path.join(os.homedir(), '.opal', '.venv', 'bin', 'python');
  assert.ok(fs.existsSync(venvPython),
    `OPAL .venv python이 필요하다(실 brain-tool subprocess 검증 — mock 금지): ${venvPython}. 부재 시 PM 에스컬레이션.`);
  assert.ok(fs.existsSync(BRAIN_TOOL_PY), `brain_tool.py가 필요하다: ${BRAIN_TOOL_PY}`);

  const root = makeUnsetTree();
  try {
    const r = spawnSync(venvPython, [BRAIN_TOOL_PY, 'sync-header'], {
      cwd: root, encoding: 'utf8', timeout: 90000,
      env: Object.assign({}, process.env, { HOME: path.join(root, 'fakehome') }),
    });
    const out = (r.stdout || '').trim();
    let json = null;
    try { json = JSON.parse(out); } catch { /* not JSON */ }

    // [RED 기대] 게이트가 없으므로 code-scan이 exit 0으로 스캔에 성공하고 sync-header는 ok:true를 낸다.
    assert.ok(json, `sync-header stdout이 JSON이어야 함, got: ${out.slice(0, 400)} | stderr: ${(r.stderr || '').slice(0, 300)}`);
    assert.strictEqual(json.ok, false,
      `[RED expect] headerSource 미설정 트리에서는 code-scan이 exit 1로 차단되므로 sync-header도 실패해야 한다, got ${out.slice(0, 400)}`);
    assert.ok(/header_source_unset/.test(JSON.stringify(json)),
      '[RED expect] code-scan이 stderr에 게이트 사유를 병기해야 brain_tool.py:791-792의 detail 조립에 실려 최종 사용자에게 도달한다 ' +
      `(F-12③ AC — stdout 전용이면 detail="code-scan exit=1, stderr="가 되어 사유가 소실된다). got ${out.slice(0, 400)}`);
  } finally {
    fs.rmSync(root, { recursive: true, force: true });
  }
});

test('[T080/L2-F12c] TS-045 (S-14): brain_tool.py는 변경 0줄 — stderr 병기 설계로 무수정 성립 (PLAN §3.5.4)', () => {
  const r = spawnSync('git', ['diff', '--numstat', 'HEAD', '--', 'opal/tools/brain-tool/brain_tool.py'],
    { cwd: REPO_ROOT, encoding: 'utf8' });
  assert.strictEqual(r.status, 0, `git diff 실행 실패: ${r.stderr}`);
  assert.strictEqual((r.stdout || '').trim(), '',
    `brain_tool.py는 이 태스크에서 수정하지 않는다(무수정 성립이 F-12③의 설계 결론이다). got:\n${r.stdout}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F13] S-17 — 골든 재캡처 바이트 동일 (TS-060, TS-061, TS-064)
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F13] TS-060 (S-17): legacy-repo 픽스처가 headerSource "inline"을 명시한다 (캡처 조건)', () => {
  const cfg = JSON.parse(fs.readFileSync(path.join(LEGACY_REPO, '.opal', 'code-scan.json'), 'utf8'));
  assert.strictEqual(cfg.headerSource, 'inline',
    '골든 캡처 조건 — code-map 부재 픽스처는 inline 모드를 명시해야 한다 (PLAN §3.7.2)');
});

for (const c of GOLDEN_COMMANDS) {
  test(`[T080/L2-F13] TS-060 (S-17): headerSource inline 명시 하 "${c.args.join(' ')}" 출력이 골든과 바이트 동일`, () => {
    const { exitCode, stdout, stderr } = run(LEGACY_REPO, c.args);
    assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode} | stderr: ${stderr.slice(0, 300)}`);
    const expected = fs.readFileSync(path.join(GOLDEN, c.golden), 'utf8');
    assert.strictEqual(stdout, expected,
      `골든과 바이트 동일해야 함(${c.golden}). 차이가 나오면 조회 경로 회귀이므로 GREEN 처리 금지하고 원인을 규명한다(H-10).`);
  });
}

test('[T080/L2-F13] TS-064 (S-17): inline 모드 scan --json 결과에 _source 키 0건', () => {
  const { exitCode, stdout } = run(LEGACY_REPO, ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  const json = JSON.parse(stdout);
  const withSource = Object.keys(json).filter(k => Object.prototype.hasOwnProperty.call(json[k], '_source'));
  assert.deepStrictEqual(withSource, [],
    'inline 모드 결과에는 _source 키가 붙지 않는다 (§3.3.2 (A) — 제약② 하위호환 보증 지점)');
});

test('[T080/L2-F13] TS-061 (S-17): fixtures/golden/README.md에 캡처 조건 + 077 대비 diff 근거가 기록된다', () => {
  const readmePath = path.join(GOLDEN, 'README.md');
  assert.ok(fs.existsSync(readmePath), `골든 캡처 근거 문서가 필요하다: ${readmePath}`);
  const text = fs.readFileSync(readmePath, 'utf8');

  // 캡처 조건 (현재 충족)
  assert.ok(/code-scan\.js/.test(text) && /scan --json/.test(text), '캡처 명령이 기록되어야 함');
  assert.ok(/"headerSource"\s*:\s*"inline"/.test(text), '캡처 시 픽스처 설정 전문(headerSource inline)이 기록되어야 함');

  // 077 대비 diff 근거 (Step 13 산출물)
  const sec = mdSection(text, /077.*diff|diff 결과/);
  assert.ok(sec !== null, '"077 골든 대비 diff 결과" 절이 존재해야 함');
  // [RED 기대] 현재는 "_(Step 13에서 채운다 ...)_" 플레이스홀더만 있다.
  assert.ok(!/채운다|TBD|TODO/.test(sec),
    `[RED expect] diff 근거 자리표시자가 남아 있으면 안 된다(재캡처 결과 미기록). got: ${sec.trim().slice(0, 200)}`);
  assert.ok(/git diff|바이트|diff --stat/.test(sec) && sec.trim().length >= 30,
    `[RED expect] 재캡처 후 git diff --stat 결과와 (차이가 있었다면) 그 원인이 기록되어야 함. got: ${sec.trim().slice(0, 200)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-완료기준] S-16 — 픽스처 계약 + 전량 GREEN (TS-063, TS-062)
// ═════════════════════════════════════════════════════════════════════════

function fixtureConfigs() {
  const out = [];
  (function walk(dir) {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) walk(p);
      else if (e.isFile() && e.name === 'code-scan.json' && path.basename(path.dirname(p)) === '.opal') out.push(p);
    }
  })(FIX);
  return out.sort();
}

test('[T080/L2-완료기준] TS-063 (S-16): 픽스처 전량(20종 이상)이 headerSource를 2택 값으로 명시한다', () => {
  const configs = fixtureConfigs();
  assert.ok(configs.length >= 20,
    `픽스처 .opal/code-scan.json이 20종 이상이어야 함(H-9 대상 집합), got ${configs.length}`);
  const missing = [];
  const invalid = [];
  for (const p of configs) {
    const text = fs.readFileSync(p, 'utf8');
    const m = /"headerSource"\s*:\s*"([^"]*)"/.exec(text);
    if (!m) missing.push(path.relative(FIX, p));
    else if (m[1] !== 'inline' && m[1] !== 'manifest') invalid.push(`${path.relative(FIX, p)}=${m[1]}`);
  }
  assert.deepStrictEqual(missing, [], 'headerSource 미명시 픽스처가 있으면 게이트 도입 즉시 전량 exit 1이 된다 (H-9)');
  assert.deepStrictEqual(invalid, [], 'auto 제거 후 픽스처 값은 inline|manifest 2택뿐이다');
});

test('[T080/L2-완료기준] TS-062 (S-16): 전체 테스트 스위트가 전량 pass하고 exit 0', () => {
  // 재귀 가드 규약 ① (파일 상단 규약 참조) — 이 프로세스 자체가 다른 메타테스트의 자식이면
  // 본 메타테스트를 수행하지 않고 통과 처리한다. skip/todo 마킹 대신 조기 return을 쓴다(규약 ④).
  if (process.env.CODE_SCAN_META_CHILD === '1') return;
  const files = fs.readdirSync(__dirname)
    .filter(f => f.startsWith('test-') && f.endsWith('.js'))
    .map(f => path.join(__dirname, f))
    .sort();
  assert.ok(files.length >= 10, `테스트 파일이 10종 이상이어야 함, got ${files.length}`);
  // node --test는 테스트 파일을 자식 프로세스로 돌리며 NODE_TEST_CONTEXT를 심는다. 이 값을 물려주면
  // 손자 러너가 "테스트 자식"으로 오인해 즉시 exit 0으로 빠져나가 검사가 무력화된다 — 반드시 제거한다.
  // 재귀 가드 규약 ② — 자식 스위트의 메타테스트(TS-080·S-19)를 무동작시킨다.
  const childEnv = Object.assign({}, process.env, { CODE_SCAN_META_CHILD: '1' });
  delete childEnv.NODE_TEST_CONTEXT;
  const r = spawnSync(process.execPath, ['--test', ...files], {
    cwd: REPO_ROOT, encoding: 'utf8', timeout: 300000, env: childEnv,
  });
  const tail = ((r.stdout || '') + (r.stderr || '')).split('\n').filter(l => /^ℹ (tests|pass|fail|skipped)/.test(l)).join(' | ');
  // [RED 기대] 신 계약 구현 전이므로 전량 pass하지 않는다.
  assert.strictEqual(r.status, 0,
    `[RED expect] 게이트 도입으로 기존 케이스가 붕괴하지 않고 전량 pass해야 한다 (완료 기준). exit ${r.status} | ${tail}`);
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F11] S-18 — 규칙 문서 5종 + docs/ 3종 산출물 검사 (TS-050~TS-055)
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F11] TS-050 (S-18): 규칙 문서 5종 변경이력 표에 신규 행(버전 · YYYY-MM-DD HH:mm KST · (080))', () => {
  const missing = [];
  for (const [name, file] of Object.entries(RULE_DOCS)) {
    const rows = changelogLines(file).filter(l => /\(080\)/.test(l.text));
    const ok = rows.some(l => /v\d+\.\d+/.test(l.text) && /\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}/.test(l.text));
    if (!ok) missing.push(`${name}(${rows.length}행 중 형식 충족 0)`);
  }
  // [RED 기대] Step 10~11 미완료.
  assert.deepStrictEqual(missing, [],
    '[RED expect] 5문서 변경이력에 버전·일시(KST)·태스크 번호 (080)을 갖춘 신규 행이 있어야 함');
});

test('[T080/L2-F11] TS-051 (S-18): 규칙 문서 5종에 readonly를 판정 근거로 서술하는 문장 0건 (폐기 표기는 허용)', () => {
  const hits = [];
  for (const [name, file] of Object.entries(RULE_DOCS)) {
    for (const { n, text } of bodyLines(file)) {
      if (!/readonly/.test(text)) continue;
      if (DEPRECATION_MARK.test(text)) continue; // "제거됨/deprecated/무시된다" 표기는 허용
      hits.push(`${name}:${n} ${text.trim().slice(0, 110)}`);
    }
  }
  // [RED 기대] header-rules.md:20,25 · tools.md:240 · header-standard.md:206 ·
  //            code-scan-management.md:73,80,81 · pm-review-gate.md:56 가 남아 있다.
  assert.deepStrictEqual(hits, [],
    '[RED expect] readonly는 판정 근거가 아니다 — 기록 소스는 전역 headerSource가 결정한다 (F-11 AC). ' +
    'deprecated/무시 표기로만 남길 수 있다');
});

test('[T080/L2-F12d] TS-052 (S-18): 규칙 문서 5종에 개인 식별자 신규 기재 0건 (역할명 PM/소유자만)', () => {
  // 선례: header-rules.md 변경이력 v1.0("알투(비서)" → "에이전트(비서)" 치환) ·
  //       tools.md 변경이력 v1.4("캡틴 확인" → "{owner_name}" 치환).
  // AC는 "**신규** 기재 0건"이다. 이 태스크와 무관한 절의 선존 누설(예: tools.md §cmux-tool 트리거)까지
  // 여기서 강제하면 검사 범위가 태스크 경계를 넘는다. 그래서 두 축으로 좁혀 고정한다.
  //   (A) 이 태스크가 **추가한 줄**(git diff HEAD의 + 라인) — 신규 기재의 정확한 정의
  //   (B) headerSource 값 도메인을 서술하는 문맥 줄 — 080이 재작성하는 바로 그 영역
  const IDENTIFIERS = ['캡틴', '알투'];
  const hits = [];

  const rel = Object.values(RULE_DOCS).map(f => path.relative(REPO_ROOT, f));
  const diff = spawnSync('git', ['diff', 'HEAD', '--unified=0', '--', ...rel], { cwd: REPO_ROOT, encoding: 'utf8' });
  assert.strictEqual(diff.status, 0, `git diff 실행 실패: ${diff.stderr}`);
  let currentFile = '';
  for (const line of (diff.stdout || '').split('\n')) {
    if (line.startsWith('+++ b/')) { currentFile = line.slice(6); continue; }
    if (!line.startsWith('+') || line.startsWith('+++')) continue;
    for (const id of IDENTIFIERS) {
      if (line.includes(id)) hits.push(`(added) ${currentFile}: "${id}" — ${line.trim().slice(0, 90)}`);
    }
  }

  for (const [name, file] of Object.entries(RULE_DOCS)) {
    for (const { n, text } of headerSourceContextLines(file)) {
      for (const id of IDENTIFIERS) {
        if (text.includes(id)) hits.push(`${name}:${n} "${id}" — ${text.trim().slice(0, 90)}`);
      }
    }
  }

  assert.deepStrictEqual(hits, [],
    '규칙 문서에는 에이전트 이름·소유자 호칭을 신규 기재하지 않는다 — 역할명(PM/소유자)만 사용한다 (D-1)');
});

test('[T080/L2-F11] TS-053 (S-18): header-rules.md 기록 위치 판정표의 reason이 3값 폐쇄 도메인', () => {
  const body = bodyLines(RULE_DOCS.headerRules).map(l => l.text).join('\n');

  // [RED 기대] 신 3값이 아직 없다.
  for (const v of ['header_source_inline', 'header_source_manifest', 'out_of_scope']) {
    assert.ok(new RegExp(v).test(body), `[RED expect] reason 값 \`${v}\`이 판정표에 있어야 함`);
  }
  // 구 4값 도메인 잔존 0건 (폐기 표기 줄은 예외)
  const legacyHits = bodyLines(RULE_DOCS.headerRules).filter(({ text }) =>
    /(readonly_repo|inline_exists|legacy_no_header|new_file)/.test(text) && !DEPRECATION_MARK.test(text));
  assert.deepStrictEqual(legacyHits.map(l => `${l.n} ${l.text.trim().slice(0, 100)}`), [],
    '[RED expect] 구 4단 판정(reason 4값)은 auto 시대의 서술이므로 잔존 0건이어야 함');
  // 폐쇄 도메인 문장이 3값 기준으로 쓰였는가
  assert.ok(/3값/.test(body), '[RED expect] "이 3값 외를 반환하지 않는다" 형태의 폐쇄 도메인 문장이 필요함');
  const wrongArity = bodyLines(RULE_DOCS.headerRules).filter(({ text }) =>
    /(reason|write_to)/.test(text) && /(4값|2값)/.test(text));
  assert.deepStrictEqual(wrongArity.map(l => `${l.n} ${l.text.trim().slice(0, 100)}`), [],
    '[RED expect] 문서가 구현보다 좁거나 넓은 폐쇄 도메인을 선언하면 077 H-6과 동형 결함을 새로 고정한다');
});

test('[T080/L2-F11] TS-054 (S-18): code-scan-management.md 최소 구조 예시에 headerSource 포함', () => {
  const text = fs.readFileSync(RULE_DOCS.codeScanMgmt, 'utf8');
  const blocks = text.split(/```/).filter((_, i) => i % 2 === 1);
  const minimal = blocks.filter(b => /"scopes"/.test(b) && /"extensions"/.test(b));
  assert.ok(minimal.length > 0, '최소 구조 예시(JSON) 블록이 존재해야 함');
  // [RED 기대] 현재 예시에 headerSource가 없다 (H-11 영속 원인).
  const withHeaderSource = minimal.filter(b => /"headerSource"\s*:\s*"(inline|manifest)"/.test(b));
  assert.ok(withHeaderSource.length === minimal.length,
    `[RED expect] 생성 규약이 headerSource를 포함해야 다음 프로젝트가 미설정으로 태어나지 않는다. ` +
    `${minimal.length}개 예시 중 ${withHeaderSource.length}개만 포함`);
});

test('[T080/L2-F11] TS-055 (S-18): docs/ 3종에 Task 080 변경이력 행 + CONVENTIONS 판정 근거 교체', () => {
  const missing = [];
  for (const [name, file] of Object.entries(DOCS_TARGETS)) {
    const text = fs.readFileSync(file, 'utf8');
    if (!/\(Task 080\)|\(080\)/.test(text)) missing.push(name);
  }
  // [RED 기대] Step 12 미완료.
  assert.deepStrictEqual(missing, [], '[RED expect] docs/ 3종에 Task 080 변경 기록이 있어야 함');

  const conv = fs.readFileSync(DOCS_TARGETS.conventions, 'utf8');
  assert.ok(!/읽기 전용 스코프는 code-map 강제/.test(conv),
    '[RED expect] CONVENTIONS.md §@header 규칙의 readonly 기반 서술이 제거되어야 함 (PLAN §3.6.2 (6))');
  assert.ok(/headerSource/.test(conv),
    '[RED expect] CONVENTIONS.md는 "전역 headerSource가 manifest이면 code-map 강제"로 재서술되어야 함');

  const arch = fs.readFileSync(DOCS_TARGETS.architecture, 'utf8');
  assert.ok(/headerSource/.test(arch),
    '[RED expect] ARCHITECTURE.md tools/ 표 code-scan 행이 headerSource 단일 기준을 반영해야 함');
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F11b] S-18 — auto 자산 잔존 0 (TS-066, TS-067)
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F11b] TS-066 (S-18): code-scan.js DEFAULT_CONFIG·USAGE·loadConfig에 auto 리터럴 0건', () => {
  const a = analyzeJs(CODE_SCAN_JS);
  const ranges = {
    DEFAULT_CONFIG: a.declRange('DEFAULT_CONFIG'),
    USAGE: a.declRange('USAGE'),
    loadConfig: a.funcRange('loadConfig'),
  };
  for (const [name, r] of Object.entries(ranges)) {
    assert.ok(r, `검사 대상 영역 ${name}의 줄 범위를 확정하지 못했다 — 소스 구조 변경 시 이 검사부터 재검토한다`);
  }

  const occ = a.occurrences(/\bauto\b/g).filter(o => o.kind !== 'comment');
  const inTargets = occ.filter(o => Object.values(ranges).some(r => inRange(o.line, r)));
  assert.deepStrictEqual(inTargets.map(o => `${o.line}: ${o.raw.trim().slice(0, 100)}`), [],
    '[RED expect] auto는 완전 제거된다(D-3) — 기본값·사용법 예시·설정 로더 어디에도 남지 않아야 한다');

  // 예외 1개소: 마이그레이션 힌트 **문자열**만 허용한다.
  const asString = occ.filter(o => o.kind === 'string');
  assert.ok(asString.length <= 1,
    `[RED expect] auto 문자열 잔존은 마이그레이션 힌트 1개소만 허용된다(§3.1.4), got ${asString.length}건: ` +
    asString.map(o => `${o.line}: ${o.raw.trim().slice(0, 80)}`).join(' / '));
  const asCode = occ.filter(o => o.kind === 'code');
  assert.deepStrictEqual(asCode.map(o => `${o.line}: ${o.raw.trim().slice(0, 80)}`), [],
    'auto를 식별자·값으로 다루는 코드는 0건이어야 한다');
});

test('[T080/L2-F11b] TS-067 (S-18): 3문서에 auto를 유효값으로 서술하는 문장 0건 (폐기 표기는 허용)', () => {
  const targets = {
    toolsMd: RULE_DOCS.toolsMd,
    headerStandard: RULE_DOCS.headerStandard,
    codeScanMgmt: RULE_DOCS.codeScanMgmt,
  };
  const hits = [];
  for (const [name, file] of Object.entries(targets)) {
    for (const { n, text } of headerSourceContextLines(file)) {
      if (!/\bauto\b/.test(text)) continue;
      if (DEPRECATION_MARK.test(text)) continue; // "auto는 제거됨(Task 080)" 폐기 표기는 허용
      hits.push(`${name}:${n} ${text.trim().slice(0, 110)}`);
    }
  }
  // [RED 기대] code-scan-management.md:69,73 · header-standard.md:191 이 auto를 유효값으로 나열한다.
  assert.deepStrictEqual(hits, [],
    '[RED expect] headerSource 값 도메인을 서술하는 지점에서 auto를 유효값으로 나열하지 않는다 (D-3)');
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F11c] S-18 — write_to 3값 + 축 분리 (TS-068)
// ═════════════════════════════════════════════════════════════════════════

const REASON_VALUES = ['header_source_inline', 'header_source_manifest', 'out_of_scope'];
const LEGACY_REASON_VALUES = ['inline_exists', 'readonly_repo', 'legacy_no_header', 'new_file'];
const WRITE_TO_VALUES = ['inline', 'manifest', 'none'];

test('[T080/L2-F11c] TS-068 (S-18): header-rules.md·tools.md에 write_to 3값 반영 + reason과 한 목록에 섞이지 않음', () => {
  const targets = { headerRules: RULE_DOCS.headerRules, toolsMd: RULE_DOCS.toolsMd };

  for (const [name, file] of Object.entries(targets)) {
    const body = bodyLines(file).map(l => l.text).join('\n');
    // [RED 기대] 신 도메인 미반영.
    for (const v of WRITE_TO_VALUES) {
      assert.ok(new RegExp('`' + v + '`|\\b' + v + '\\b').test(body),
        `[RED expect] ${name}에 write_to 값 \`${v}\`이 서술되어야 함 (3값 도메인)`);
    }
    for (const v of REASON_VALUES) {
      assert.ok(new RegExp(v).test(body), `[RED expect] ${name}에 reason 값 \`${v}\`이 서술되어야 함 (3값 도메인)`);
    }
  }

  // 축 혼합 검출 — 한 슬래시 목록 안에 reason 값과 write_to 값이 섞이면 M-2(tools.md:240) 오기의 재생산이다.
  const LIST_RE = /`?[A-Za-z_][A-Za-z0-9_]*`?(?:\s*\/\s*`?[A-Za-z_][A-Za-z0-9_]*`?)+/g;
  const mixed = [];
  for (const [name, file] of Object.entries(targets)) {
    for (const { n, text } of bodyLines(file)) {
      let m;
      LIST_RE.lastIndex = 0;
      while ((m = LIST_RE.exec(text)) !== null) {
        const items = m[0].split('/').map(s => s.replace(/`/g, '').trim());
        if (items.length < 2) continue;
        const hasReason = items.some(it => REASON_VALUES.includes(it) || LEGACY_REASON_VALUES.includes(it));
        const hasWriteTo = items.some(it => WRITE_TO_VALUES.includes(it));
        if (hasReason && hasWriteTo) mixed.push(`${name}:${n} [${items.join('/')}]`);
      }
    }
  }
  assert.deepStrictEqual(mixed, [],
    '[RED expect] write_to와 reason은 서로 다른 축이다 — 한 목록에 섞어 나열하면 현행 오기(M-2)를 그대로 재생산한다');
});

// ═════════════════════════════════════════════════════════════════════════
// [T080/L2-F11d] S-18 — 모드 판정 지점 봉인 (TS-070) + discover 산출물 (TS-071)
//
// PLAN §3.1.5: 리터럴 blacklist(`config.headerSource` 문자열 매칭)는 구조분해
// (`const { headerSource } = config`)·별칭(`const cfg = config; cfg.headerSource`)으로 뚫린다.
// 그래서 검사 방향을 뒤집는다 — **허용 영역과 허용 형태를 열거하고 그 밖의 토큰 출현을 FAIL로 본다.**
// ═════════════════════════════════════════════════════════════════════════

test('[T080/L2-F11d] TS-070 (S-18): headerSource 판정·재계산 지점이 resolveHeaderSource 외 0곳', () => {
  const a = analyzeJs(CODE_SCAN_JS);

  // ① 허용 영역 3개의 줄 범위를 중괄호 깊이 계산으로 확정 (정규식 아님)
  const allowed = {
    resolveHeaderSource: a.funcRange('resolveHeaderSource'),
    loadConfig: a.funcRange('loadConfig'),
    parseArgs: a.funcRange('parseArgs'),
  };
  assert.ok(allowed.resolveHeaderSource,
    '[RED expect] 유일한 모드 판정 지점 `function resolveHeaderSource(config, opts)`가 존재해야 한다 (§3.1.2 (C))');
  assert.ok(allowed.loadConfig, '`loadConfig`의 줄 범위를 확정하지 못했다');
  assert.ok(allowed.parseArgs, '`parseArgs`의 줄 범위를 확정하지 못했다');

  const buildCtxRange = a.funcRange('buildCtx');
  const defaultConfigRange = a.declRange('DEFAULT_CONFIG');
  assert.ok(buildCtxRange, '`buildCtx`의 줄 범위를 확정하지 못했다 — 허용 형태 (b) 판정에 필요하다');
  assert.ok(defaultConfigRange, '`DEFAULT_CONFIG`의 줄 범위를 확정하지 못했다 — 허용 형태 (c) 판정에 필요하다');

  // ②③ 검사 대상 = 파일 전체 − 허용 영역 3개, 문자열·주석 내부는 제외
  const occ = a.occurrences(/\bheaderSource\b/g)
    .filter(o => o.kind === 'code')
    .filter(o => !Object.values(allowed).some(r => inRange(o.line, r)));

  // ④ 허용 3형태 판정
  const ASSIGN_RE = /^\s*(=(?!=)|\+\+|--|\+=|-=|\*=|\/=|%=|\|\|=|&&=|\?\?=)/;
  const violations = [];
  let formCCount = 0;

  for (const o of occ) {
    const isProperty = /(?:\?\.|\.)\s*$/.test(o.before);
    const isCtxRead = /\bctx\s*(?:\?\.|\.)\s*$/.test(o.before) && !ASSIGN_RE.test(o.after);
    // (a) ctx.headerSource 읽기 (대입 좌변 아님)
    if (isCtxRead) continue;
    // (b) buildCtx 시그니처·본문의 파라미터 전달 (호출 인자 포함)
    if (!isProperty && (inRange(o.line, buildCtxRange) || /\bbuildCtx\s*\(/.test(a.codeLineText(o.line)))) continue;
    // (c) DEFAULT_CONFIG 프로퍼티 키 정의 (1회)
    if (!isProperty && inRange(o.line, defaultConfigRange) && /^\s*:/.test(o.after)) { formCCount++; continue; }
    violations.push(`${o.line}: ${o.raw.trim().slice(0, 120)}`);
  }

  // 분류기 자체가 망가지면 위반이 조용히 사라진다 — 형태 (c) 1회를 자기점검으로 고정한다.
  assert.strictEqual(formCCount, 1,
    `허용 형태 (c) DEFAULT_CONFIG의 headerSource 키 정의는 정확히 1회여야 한다, got ${formCCount}`);

  assert.deepStrictEqual(violations, [],
    '[RED expect] 모드는 실행당 1값으로 확정되며(F-1 AC) 판정은 resolveHeaderSource 1곳에만 존재한다. ' +
    '허용 영역 밖의 허용 형태는 (a) ctx.headerSource 읽기(대입 좌변 아님) · (b) buildCtx 시그니처·본문·호출줄의 ' +
    '파라미터 전달 · (c) DEFAULT_CONFIG 키 정의 1회 뿐이다 (PLAN §3.1.5). ' +
    '확정값을 실어 나르는 main()의 지역 변수와 중간 전달 함수(scanAll/cmdDiscover/cmdScaffold/cmdTarget/cmdValidate)의 ' +
    '파라미터는 `headerSource` 이외의 이름(예: mode)을 쓴다 — 이름이 곧 판정 지점의 표식이므로, 허용 영역 밖에 같은 ' +
    '이름이 흩어져 있으면 파일 단위 재계산이 되살아나도 아무도 눈치채지 못한다 (PLAN §12).');
});

test('[T080/L2-F11d] TS-071 (S-18): discover 산출물 scopes[]에 headerSource 키 0건', () => {
  const { exitCode, stdout, stderr } = run(LEGACY_REPO, ['discover', '--dry-run', '--json']);
  assert.strictEqual(exitCode, 0, `discover --dry-run은 exit 0이어야 함, got ${exitCode} | stderr: ${stderr.slice(0, 300)}`);
  const json = JSON.parse(stdout);
  assert.ok(json && json.index && json.index.scopes, `discover 산출물에 index.scopes가 있어야 함, got ${stdout.slice(0, 200)}`);
  const withMode = Object.entries(json.index.scopes)
    .filter(([, v]) => Object.prototype.hasOwnProperty.call(v, 'headerSource'))
    .map(([k]) => k);
  assert.deepStrictEqual(withMode, [],
    'discover가 모드 키를 산출물에 심으면 그 순간부터 스코프 오버라이드가 자산에 고정된다 — 도구 추측은 오탐을 자산에 고정시킨다');
});

// ═════════════════════════════════════════════════════════════════════════
// 077 자산 유지 — 방향이 바뀌지 않은 회귀 가드 (S-19, S-21)
// ═════════════════════════════════════════════════════════════════════════

test('077 TS-052 (S-19): 저장소 루트 scan --json 결과에 fixtures/ 경로 0건 (픽스처 이중 격리)', () => {
  const { exitCode, stdout } = run(REPO_ROOT, ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  const bad = Object.keys(JSON.parse(stdout)).filter(p => p.includes('fixtures/'));
  assert.deepStrictEqual(bad, [], '픽스처가 저장소 스캔 결과를 오염시키면 안 된다');
});

test('077 TS-053 (S-19): 픽스처 루트 cwd 실행 결과에 저장소 파일 0건', () => {
  const { exitCode, stdout } = run(path.join(FIX, 'codemap-repo'), ['scan', '--json']);
  assert.strictEqual(exitCode, 0, `exit 0 기대, got ${exitCode}`);
  const leaks = Object.keys(JSON.parse(stdout)).filter(p => p.startsWith('opal/') || p.startsWith('tasks/'));
  assert.deepStrictEqual(leaks, [], '자기완결 픽스처는 상위 저장소를 스캔하면 안 된다');
});

test('077 TS-057: tests/ 전 테스트 파일이 @header를 보유하고 code-scan에 discoverable함', () => {
  const testFiles = fs.readdirSync(__dirname).filter(f => f.startsWith('test-') && f.endsWith('.js')).sort();
  assert.ok(testFiles.length >= 10, `테스트 파일 10종 이상 기대, got ${testFiles.length}`);
  const { exitCode, stdout } = run(REPO_ROOT, ['scan', '--json']);
  assert.strictEqual(exitCode, 0);
  const json = JSON.parse(stdout);

  const problems = [];
  for (const f of testFiles) {
    const key = Object.keys(json).find(p => p.endsWith(`tests/${f}`));
    if (!key) { problems.push(`${f}: scan 결과 미검출`); continue; }
    if (json[key].layer !== 'test') problems.push(`${f}: layer=${json[key].layer}`);
    // 허용 태스크 번호는 테스트 자산을 신설한 태스크만 누적한다 (083: test-shard-policy.js 신설).
    if (!['077', '080', '082', '083'].includes(String(json[key].task))) problems.push(`${f}: task=${json[key].task}`);
    if (!Array.isArray(json[key].scenarios) || json[key].scenarios.length === 0) problems.push(`${f}: scenarios 없음`);
  }
  assert.deepStrictEqual(problems, [], '테스트 파일도 @header 자산이다 (header-standard.md §3)');
});

test('077 TS-048 (S-21): header-rules.md에 "별도 도구 없음" 문구 잔존 0건', () => {
  const text = fs.readFileSync(RULE_DOCS.headerRules, 'utf8');
  assert.strictEqual((text.match(/별도 도구 없음/g) || []).length, 0,
    '077이 제거한 문구가 되살아나면 안 된다');
});

test('077 TS-051 (S-21): brain-tool README 2소스 문언 + opal-harness.md §9 code-scan 서브명령 정합', () => {
  const brainText = fs.readFileSync(LEGACY_ASSET_DOCS.brainReadme, 'utf8');
  const harnessText = fs.readFileSync(LEGACY_ASSET_DOCS.opalHarness, 'utf8');
  assert.ok(/code-map/.test(brainText) && /인라인/.test(brainText), 'brain-tool README의 2소스 의미 변화 문장 유지');
  assert.ok(/단방향/.test(brainText), '단방향 계약 문언은 080에서도 불변이다');
  const codeScanLine = harnessText.split('\n').find(l => l.includes('| code-scan |'));
  assert.ok(codeScanLine && /discover/.test(codeScanLine) && /scaffold/.test(codeScanLine),
    `opal-harness.md §9 code-scan 행의 서브명령 열거 유지, got: ${codeScanLine}`);
});

test('077 S-21: pm-review-gate.md에 validate --changed 게이트 절차 + 커버리지 언급 유지', () => {
  const text = fs.readFileSync(RULE_DOCS.pmReviewGate, 'utf8');
  assert.ok(/validate --changed/.test(text), 'CLOSE 진입 전 validate --changed 게이트 절차 유지');
  assert.ok(/커버리지|coverage/.test(text), '커버리지 판정 언급 유지');
});
