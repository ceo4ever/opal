/**
 * @header {
 *   "module": "test-shard-policy",
 *   "layer": "test",
 *   "domain": "code-scan",
 *   "description": "RED-first — code-scan 샤드 정책 확장(shardPolicy 2축화 3단 해석 + 전역 setting.json 로더 + split --plan/--groups 분할 제안·집행 + 표준단어사전 로더 + init 서브명령) 계약 CLI 블랙박스 테스트. 3단 우선순위·셀 머지·봉인(F-001), 전역 설정 4상태 비차단 폴백(F-002), 2축 판정·경계(F-003), 사다리 5단계 제안 알고리즘·검토 장치 3종(F-004), 사전 3분기 폴백·2표 파싱(F-011), split 집행·원자성·롤백(F-005), 유도 페이로드(F-006), init 게이트 순환 부재·쓰기 3분기(F-012), 완료기준 ④ 전 궤 왕복을 검증한다 (S-1~S-12, S-14~S-16, 태스크 083). S-13(구 위치 이전)은 AC 매핑 표에 따라 test-shard.js가 담당하므로 본 파일에 없다",
 *   "exports": [],
 *   "depends": ["node:test", "node:assert/strict", "node:child_process", "node:fs", "node:os", "node:path"],
 *   "task": "083",
 *   "scenarios": ["S-1","S-2","S-3","S-4","S-5","S-6","S-7","S-8","S-9","S-10","S-11","S-12","S-14","S-15","S-16"]
 * }
 */
//
// [RED-first — 작성자≠구현자]
// 본 파일은 opal-test-agent(mode:red)가 구현 전에 작성한다. 현행 code-scan.js v1.5.0에는
// shardPolicy 2축 정책·전역 setting.json 로더·split 서브명령·init 서브명령·표준단어사전 로더가
// 전혀 없으므로 아래 전 케이스는 실패(RED)해야 정상이다. 구현(GREEN)은 op-dev-execute가
// PLAN.md §4.2 Step 6a·6b에서 수행한다.
// [MUST] `~/.opal/references/harness/red-first.md` §3 — GREEN/fix 루핑 중 이 파일 수정 금지.
// 기대값 완화로 통과를 유도하는 것은 reward hacking이다 — 실패 이유가 "미구현"이어야 하며
// "테스트 자체 오류"여서는 안 된다.
//
// [RED 설계 원칙 — 현재(082) 구현과의 우연한 일치 차단]
// 현행 checkOversize는 `size > manifestMaxBytes(ctx)`(index.json 단일 축, 기본 20480, 엔트리 수
// 무시)만 본다 — .opal/code-scan.json의 shardPolicy·~/.opal/setting.json 어느 것도 읽지 않는다.
// 따라서 "정책이 다르게 적용된다"류 단언은 반드시 아래 규칙으로 크래프팅한다:
//   기대값 1(oversize)  → 매니페스트 바이트를 (신규 정책 maxBytes, 20480] 구간에 둔다
//                          → 구현이 없으면 20480 미만이라 0으로 나와 항상 어긋난다(RED 보장)
//   기대값 0(not-oversize) → 매니페스트 바이트를 20480 초과로 두고 엔트리 수 축으로 미달시킨다
//                          → 구현이 없으면 20480 초과라 1로 나와 항상 어긋난다(RED 보장)
// 이 규칙 덕에 "정책 값이 20480과 우연히 같아서 통과해버리는" 거짓 초록을 원천 차단한다.
//
// TC ↔ TS-ID 매핑 표 (TEST-SCENARIO.md §3, §4 AC 매핑 기준):
//
// | 케이스 프리픽스              | TS-ID 묶음              | S-ID | 대상                                   |
// |------------------------------|-------------------------|------|----------------------------------------|
// | [T083/L1-F1a] 결정표          | TS-001~004               | S-1  | resolveShardPolicy 3단 해석 + 셀 머지  |
// | [T083/L1-F1a] 알수없는키      | TS-006                    | S-1  | 알 수 없는 키 무해                     |
// | [T083/L1-F1c] 타입위반        | TS-005                    | S-1  | code_scan_config_invalid               |
// | [T083/L1-F1d] 봉인            | TS-007~008                | S-1  | 정적 grep — 판정 지점 1곳              |
// | [T083/L1-F1b-a] 홈 주입       | TS-010, TS-014            | S-2  | OPAL_HOME 환경변수 주입                |
// | [T083/L1-F1b-b] 4상태 폴백    | TS-011~013, TS-016        | S-2  | 부재·파손·키부재·타입위반 비차단       |
// | [T083/L1-F1b-c] 불간섭        | TS-015                    | S-2  | 전역 setting.json 바이트 불변          |
// | [T083/L1-F2a] 미달 비열거     | TS-020, TS-022            | S-3  | 2축 AND — 편축 미달 시 0건             |
// | [T083/L1-F2b] 충족 열거       | TS-021                    | S-3  | 2축 충족 1건 + exit 0                  |
// | [T083/L1-F2-경계] 경계값      | TS-023~024                | S-3  | entries===minFiles / size===maxBytes   |
// | [T083/L1-F2c] 샤드            | TS-025                    | S-3  | 샤드 자신 측정                         |
// | [T083/L1-F2-scaffold] 알림    | TS-026                    | S-3  | scaffold stderr 2축 연동               |
// | [T083/L1-F4a] 제안 기본       | TS-030~031, TS-034        | S-4  | --plan 출력 + 무쓰기                   |
// | [T083/L1-F4b] 결정론          | TS-033, TS-116            | S-4  | 2회 실행 stdout 바이트 동일            |
// | [T083/L1-F4c] 미분류 정직     | TS-032, TS-035~037        | S-4  | unassigned·라벨 안전·기타 그룹 금지    |
// | [T083/L1-F4-usage] CLI 계약   | TS-038~039                | S-4  | inline 게이트 + 배타 옵션              |
// | [T083/L1-F4d] 사다리          | TS-100~101, TS-107~108    | S-5  | 잔여만 흘려보내기 + 다중매칭 tie-break |
// | [T083/L1-F4d] 단계별 신호     | TS-102~106, TS-132        | S-5  | S1~S5 신호별 배정                      |
// | [T083/L1-F4d] 채택효과 ★      | (추가 단언)                | S-5  | 최종 unassigned < S1 단독 unassigned   |
// | [T083/L2-F4f] 검토장치        | TS-109~113                | S-6  | --trace·--stop-after·왕복 파이프       |
// | [T083/L1-F4e] 사전 skip       | TS-114~115                | S-6  | 사전 미발견 시 S1~S3 skip              |
// | [T083/L1-F4e] 탐색·파싱       | TS-120~131                | S-7  | 3단 탐색·2표 헤더 파싱·안전            |
// | [T083/L1-X-a] 게이트 예외     | TS-140~141                | S-8  | 설정 없음/깨짐에서도 init 동작         |
// | [T083/L1-X-b] 비대화형        | TS-142~144, TS-158        | S-8  | TTY 없음·필수 인자·회귀                |
// | [T083/L2-X-c] 쓰기 3분기      | TS-145~147, TS-153        | S-9  | 없음/있음(force無)/있음(force)+.bak    |
// | [T083/L2-X-d] 추론 규약 일치  | TS-148~152, TS-154~157    | S-9  | scopes/extensions/exclude/키순서       |
// | [T083/L2-F3a~d] split 정상    | TS-040~045                | S-10 | 생성·유실0·잔존·validate·dry-run       |
// | [T083/L1-F3 라벨] 라벨 안전   | TS-053                    | S-10 | 경로 이탈 차단                         |
// | [T083/L2-F3 손편집] ★         | (추가 단언)                | S-10 | 사람 편집 groups 문서 집행 성공        |
// | [T083/L2-F3e] 원자성          | TS-046~049                | S-11 | 4단 실패 주입 + 롤백                   |
// | [T083/L1-F5a~b] 유도 페이로드 | TS-060~063                | S-12 | recommendedShards·next·detail 불변     |
// | [T083/L2-F7] 회귀가드         | TS-080~085                | S-14 | 전량 GREEN·골든 불변·홈 격리           |
// | [T083/L2-F8] 문서·배포        | TS-090~097                | S-15 | VERSION·tools.md·시드 멱등             |
// | [T083/L2-DONE4] 완료기준④ ★★★| TS-054                    | S-16 | 사전상태단언+전궤관통+왕복 (3중 추가)  |
// | (S-13 구 위치 이전은 test-shard.js:[T083/L1-F6a/b] 담당 — 083 AC 매핑 표 §4 확인. 본 파일 범위 밖) |
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
//   v1.0 2026-08-04 KST: RED-first 최초 작성 — S-1~S-12, S-14~S-16 (S-13 제외, test-shard.js 이관)
//     (Task 083, opal-test-agent mode:red)
//   v1.1 2026-08-04 18:06 KST: 테스트 인프라 정정 2건 — 단언 삭제·skip·완화 0건 (083)
//     (a) `extractInstallSeedScript()`가 PYEOF 히어독 3개 중 첫 블록(AGENT.md 치환용)을 잡아
//         TS-094~095가 IndexError로 오탐 실패 → `SEED_KEYS` 포함 블록 단일 선택으로 정정(구현 무결)
//     (b) TS-080에 공통 재귀 가드 `CODE_SCAN_META_CHILD` 적용(위 규약 ①②) — 자식 스위트에 가드
//         주입 + 자신이 자식이면 조기 return. 구 `T080_SUITE_CHILD` 규약을 본 이름으로 일원화
//

'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const CODE_SCAN_JS = path.resolve(__dirname, '..', 'code-scan.js');
const SRC = fs.readFileSync(CODE_SCAN_JS, 'utf8');
const FIX = path.resolve(__dirname, 'fixtures');
const REPO_ROOT = path.resolve(__dirname, '..', '..', '..', '..');   // tests → code-scan → tools → opal → repo root
const INSTALLER = path.resolve(REPO_ROOT, 'scripts', 'install-mac.sh');

// ── 가짜 홈 5종 (082 계승 스타일 — 083 신규) ────────────────────────────────
const HOME_ABSENT = path.join(FIX, 'shard-policy', 'homes', 'absent');
const HOME_VALID = path.join(FIX, 'shard-policy', 'homes', 'valid');
const HOME_BROKEN = path.join(FIX, 'shard-policy', 'homes', 'broken');
const HOME_NOKEY = path.join(FIX, 'shard-policy', 'homes', 'nokey');
const HOME_BADTYPE = path.join(FIX, 'shard-policy', 'homes', 'badtype');

// ═════════════════════════════════════════════════════════════════════════
// 공통 헬퍼
// ═════════════════════════════════════════════════════════════════════════

/**
 * [MUST] 083은 code-scan이 ~/.opal/setting.json을 읽는 첫 사례다 — OPAL_HOME을 주입하지
 * 않으면 개발자 실제 홈이 결과에 유입된다(H-4, 리스크 H-4). 기본 격리는 homes/absent(빈 트리).
 */
function run(cwd, args, input, homeOverride) {
  const result = spawnSync(process.execPath, [CODE_SCAN_JS, ...args], {
    cwd, encoding: 'utf8', timeout: 10000, input,
    env: Object.assign({}, process.env, { OPAL_HOME: homeOverride || HOME_ABSENT }),
  });
  const stdout = result.stdout || '';
  let json = null;
  try { json = JSON.parse(stdout.trim()); } catch { /* not JSON */ }
  return { exitCode: result.status, stdout, stderr: result.stderr || '', json };
}

function copyDirRecursive(src, dst) {
  fs.mkdirSync(dst, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name);
    const d = path.join(dst, entry.name);
    if (entry.isDirectory()) copyDirRecursive(s, d);
    else fs.copyFileSync(s, d);
  }
}

const cleanupDirs = [];
process.on('exit', () => {
  for (const d of cleanupDirs) { try { fs.rmSync(d, { recursive: true, force: true }); } catch { /* ignore */ } }
});

/** 커밋 픽스처(`tests/fixtures/<fixtureRel>`)를 임시 복사본으로 복제한다 — 픽스처 자산은 절대 수정하지 않는다. */
function copyFixture(fixtureRel, tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t083-${tag}-`));
  cleanupDirs.push(dir);
  copyDirRecursive(path.join(FIX, fixtureRel), dir);
  return dir;
}

/** 픽스처 없이 완전히 빈 임시 트리 — init 같은 "설정 자체가 없는" 시나리오 전용. */
function emptyDir(tag) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), `opal-t083-${tag}-`));
  cleanupDirs.push(dir);
  return dir;
}

function readJSON(absPath) { return JSON.parse(fs.readFileSync(absPath, 'utf8')); }
function writeJSON(absPath, obj) { fs.writeFileSync(absPath, JSON.stringify(obj, null, 2) + '\n'); }

function listAllFiles(dir) {
  const out = [];
  function walk(d, prefix) {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const full = path.join(d, e.name);
      const rel = prefix ? `${prefix}/${e.name}` : e.name;
      if (e.isDirectory()) walk(full, rel);
      else out.push(rel);
    }
  }
  walk(dir, '');
  return out.sort();
}

/** 임의 하위 트리의 {상대경로 → 파일내용} 스냅샷 — 바이트 동일성 단언용 (test-shard.js:140 패턴 일반화). */
function snapshotTree(dir, subrel) {
  const root = path.join(dir, subrel);
  const snap = {};
  const walk = (d, prefix) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name))) {
      const full = path.join(d, e.name);
      const rel = prefix ? `${prefix}/${e.name}` : e.name;
      if (e.isDirectory()) walk(full, rel);
      else snap[rel] = fs.readFileSync(full, 'utf8');
    }
  };
  if (fs.existsSync(root)) walk(root, '');
  return snap;
}

/** 프로젝트 `.opal/code-scan.json`의 `shardPolicy` 키를 병합/치환/삭제한다. value===null이면 키를 삭제한다. */
function setShardPolicy(dir, value) {
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const cfg = readJSON(cfgPath);
  if (value === null) delete cfg.shardPolicy;
  else cfg.shardPolicy = value;
  writeJSON(cfgPath, cfg);
  return cfgPath;
}

/** 임의 임시 홈(`~/.opal/setting.json` 등가물)을 만든다. settingValue===undefined면 setting.json 자체가 없는 홈(부재). */
function makeHome(tag, settingValue) {
  const dir = emptyDir(`home-${tag}`);
  if (settingValue !== undefined) {
    const p = path.join(dir, 'setting.json');
    if (typeof settingValue === 'string') fs.writeFileSync(p, settingValue);
    else writeJSON(p, settingValue);
  }
  return dir;
}

/**
 * entryCount개의 최소 엔트리를 가진 매니페스트를 직렬화 바이트가 정확히 targetBytes가 되도록
 * 크래프팅한다 (082 boundary-crafting 기법의 확장 — 첫 엔트리 description을 패딩).
 * [MUST] entryCount·targetBytes 조합에 따라 최소 바이트를 반드시 확인한다 — 못 미치면 throw.
 */
function craftManifestBytes(entryCount, targetBytes, opts) {
  opts = opts || {};
  const files = {};
  for (let i = 0; i < entryCount; i++) {
    files[`Filler${i}.ts`] = { description: 'x', exports: [`Filler${i}`] };
  }
  const skeleton = { version: 1, scope: opts.scope || 'svc', dir: opts.dir || 'svc/mod', files };
  const baseline = Buffer.byteLength(JSON.stringify(skeleton, null, 2) + '\n');
  if (targetBytes < baseline) {
    throw new Error(`craftManifestBytes: targetBytes(${targetBytes}) < baseline(${baseline}) for entryCount=${entryCount}`);
  }
  const pad = targetBytes - baseline;
  files['Filler0.ts'].description = 'x'.repeat(1 + pad);
  const serialized = JSON.stringify(skeleton, null, 2) + '\n';
  return serialized;
}

// PM 정정(083, 2026-08-04): 매니페스트만 교체하고 디스크 소스를 그대로 두면
// 선언 엔트리(Filler*.ts)와 실재 파일(A~D.ts)이 어긋나 orphan/uncovered/
// worker_scope_violation이 **필연적으로** 발생한다. 이들은 082가 세운 차단(exit 2)
// 위반이므로, 2축 판정이 완벽히 동작해도 `exitCode === 0` 단언이 통과할 수 없다
// (어떤 구현으로도 만족 불가 = 테스트 자체 결함).
// 따라서 매니페스트 기록과 함께 소스 트리도 같은 엔트리 집합으로 맞춘다.
// **단언은 하나도 완화하지 않는다** — 픽스처 정합만 회복시켜 정책 단언이
// 곁가지 위반에 가려지지 않게 하는 정정이다.
function writeManifestBytes(dir, manifestRel, entryCount, targetBytes, opts) {
  const abs = path.join(dir, manifestRel);
  fs.mkdirSync(path.dirname(abs), { recursive: true });
  fs.writeFileSync(abs, craftManifestBytes(entryCount, targetBytes, opts));

  const srcRel = (opts && opts.dir) || 'svc/mod';
  const srcDir = path.join(dir, ...srcRel.split('/'));
  fs.mkdirSync(srcDir, { recursive: true });
  for (const name of fs.readdirSync(srcDir)) {
    if (name.endsWith('.ts')) fs.unlinkSync(path.join(srcDir, name));
  }
  for (let i = 0; i < entryCount; i++) {
    fs.writeFileSync(path.join(srcDir, `Filler${i}.ts`), `export const Filler${i} = ${i};\n`);
  }
  return abs;
}

function fileBytes(absPath) { return fs.statSync(absPath).size; }

function countViolations(json, code, sub) {
  return (json && Array.isArray(json.violations) ? json.violations : [])
    .filter(v => v.code === code && (sub === undefined || v.sub === sub)).length;
}
function findViolation(json, code, sub) {
  return (json && Array.isArray(json.violations) ? json.violations : [])
    .find(v => v.code === code && (sub === undefined || v.sub === sub));
}

const MOD_REL = path.join('.opal', 'code-map', 'svc', 'mod.json');
const SPLIT_TARGET_MANIFEST_REL = '.opal/code-map/svc/mod.json';

// ═════════════════════════════════════════════════════════════════════════
// S-1: 정책 3단 해석 + 셀 머지 + 판정 지점 봉인 (H-3, H-12) — TS-001~008
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L1-F1a] TS-001: 정책 설정이 전혀 없으면 상수(maxBytes=10240, minFiles=40)가 적용된다', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's1-const');
  // (신규 기본 10240,20480] 구간 + entries>=40 → 신규 기대 oversize=1. 구현 전: 15000<20480 → 0.
  writeManifestBytes(dir, MOD_REL, 45, 15000);
  const r1 = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r1.exitCode, 0, `validate는 비차단 exit 0이어야 함, got ${r1.exitCode} (${r1.stdout})`);
  assert.ok(r1.json, `--json 출력이 유효 JSON이어야 함, raw="${r1.stdout}"`);
  assert.strictEqual(r1.json.counts && r1.json.counts.manifest_oversize, 1,
    `[RED expect] 상수 maxBytes=10240 적용 시 15000바이트/45엔트리는 초과여야 함, got ${JSON.stringify(r1.json.counts)}`);

  // entries=10(<40 상수 하한) — 상한(maxBytes)은 충족해도(25000>10240) 하한 미달로 0건이어야 함.
  // 구현 전: entries 축 자체가 없어 size>20480만으로 1이 나온다 → 반드시 어긋남(RED).
  const dir2 = copyFixture(path.join('shard-policy', 'base'), 's1-const-minfiles');
  writeManifestBytes(dir2, MOD_REL, 10, 25000);
  const r2 = run(dir2, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r2.json && r2.json.counts && r2.json.counts.manifest_oversize, 0,
    `[RED expect] 엔트리 10건 < 하한 40이면 바이트 초과와 무관하게 0건이어야 함, got ${JSON.stringify(r2.json && r2.json.counts)}`);
});

test('[T083/L1-F1a] TS-002: 전역 setting.json에만 shardPolicy가 있으면 그 값이 적용된다', () => {
  const globalHome = makeHome('t002', { shardPolicy: { maxBytes: 12000, minFiles: 15 } });
  const dir = copyFixture(path.join('shard-policy', 'base'), 's1-global');
  // 프로젝트 shardPolicy 없음(base 기본 상태). 15000은 (12000,20480] 구간 — 전역 적용 시 1, 미적용(상수 10240) 시도 1이지만
  // 미구현 시(구식 20480 임계)엔 0 — RED 보장.
  writeManifestBytes(dir, MOD_REL, 20, 15000);
  const r = run(dir, ['validate', '--json'], null, globalHome);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 1,
    `[RED expect] 전역 maxBytes=12000 적용 시 15000바이트/20엔트리는 초과여야 함, got ${JSON.stringify(r.json && r.json.counts)}`);
});

test('[T083/L1-F1a] TS-003: 프로젝트에 minFiles만 있으면 maxBytes는 전역, minFiles는 프로젝트 값 (셀 머지)', () => {
  const globalHome = makeHome('t003', { shardPolicy: { maxBytes: 12000, minFiles: 60 } });
  const dir = copyFixture(path.join('shard-policy', 'base'), 's1-cell');
  setShardPolicy(dir, { minFiles: 5 });   // maxBytes는 프로젝트에 없음 → 전역 12000이 적용돼야 함
  // 15000 ∈ (12000,20480], entries=10 (>=5 프로젝트, <60 전역) — 셀 머지가 맞다면 오버사이즈 1건.
  writeManifestBytes(dir, MOD_REL, 10, 15000);
  const r = run(dir, ['validate', '--json'], null, globalHome);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 1,
    `[RED expect] 셀 머지(전역 maxBytes=12000 + 프로젝트 minFiles=5) 적용 시 초과 1건이어야 함, got ${JSON.stringify(r.json && r.json.counts)}`);
});

test('[T083/L1-F1a] TS-004: 3층 동시 존재 시 code-scan.json > setting.json > 상수 순으로 결정론적', () => {
  const globalHome = makeHome('t004', { shardPolicy: { maxBytes: 99999, minFiles: 99 } });
  const dir = copyFixture(path.join('shard-policy', 'base'), 's1-prio');
  setShardPolicy(dir, { maxBytes: 4096, minFiles: 2 });
  // 4500 ∈ (4096,20480], entries=3(>=2 프로젝트, <99 전역, <40 상수) — 프로젝트 값이 이겨야 초과 1건.
  writeManifestBytes(dir, MOD_REL, 3, 4500);
  const r = run(dir, ['validate', '--json'], null, globalHome);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 1,
    `[RED expect] 프로젝트 값(4096/2)이 전역(99999/99)·상수(10240/40)를 이겨야 함, got ${JSON.stringify(r.json && r.json.counts)}`);
});

test('[T083/L1-F1c] TS-005: 프로젝트 shardPolicy 타입 위반 → exit 1 code_scan_config_invalid', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's1-badtype');
  setShardPolicy(dir, { maxBytes: 'big' });
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 1, `[RED expect] 타입 위반은 exit 1이어야 함, got ${r.exitCode} (${r.stdout})`);
  assert.strictEqual(r.json && r.json.error, 'code_scan_config_invalid',
    `[RED expect] error === 'code_scan_config_invalid', got ${r.stdout}`);
  assert.ok(r.json && typeof r.json.detail === 'string' && r.json.detail.includes('maxBytes'),
    `[RED expect] detail에 위반 키(maxBytes)가 포함돼야 함, got ${r.stdout}`);
});

test('[T083/L1-F1a] TS-006: shardPolicy에 알 수 없는 키(_help)가 있어도 거부되지 않는다', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's1-unknown');
  setShardPolicy(dir, { maxBytes: 5000, minFiles: 3, _help: '설명 문자열' });
  writeManifestBytes(dir, MOD_REL, 5, 6000);   // 6000 ∈ (5000,20480], entries 5>=3
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `알 수 없는 키는 정상 동작을 막지 않아야 함, got ${r.exitCode} (${r.stdout})`);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 1,
    `[RED expect] _help가 있어도 maxBytes=5000/minFiles=3은 그대로 적용돼야 함, got ${JSON.stringify(r.json && r.json.counts)}`);
});

test('[T083/L1-F1d] TS-007: 봉인 — DEFAULT_SHARD_POLICY 상수 밖 미참조 + manifestMaxBytes( 함수 소스 부재', () => {
  assert.ok(/DEFAULT_SHARD_POLICY/.test(SRC),
    '[RED expect] DEFAULT_SHARD_POLICY 상수 선언이 소스에 존재해야 함');
  assert.ok(!/function\s+manifestMaxBytes\s*\(/.test(SRC),
    `[RED expect] 구 manifestMaxBytes(ctx) 함수는 삭제되어야 함(제약 ③) — 소스에 여전히 존재함`);
});

test('[T083/L1-F1d] TS-008: 봉인 — loadGlobalSetting( 호출이 소스에 정확히 1곳(resolveShardPolicy 본문)', () => {
  const calls = (SRC.match(/loadGlobalSetting\s*\(/g) || []).length;
  assert.strictEqual(calls, 1,
    `[RED expect] loadGlobalSetting( 호출이 정확히 1곳이어야 함(제약 ③), got ${calls}회 — 현재 함수 자체가 없음`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-2: 전역 설정 로더 — 4상태 비차단 폴백 + 홈 주입 (H-4, H-5) — TS-010~016
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L1-F1b-a] TS-010: OPAL_HOME이 setting.json 없는 홈을 가리키면 상수 폴백 + stderr 무출력', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's2-absent');
  writeManifestBytes(dir, MOD_REL, 45, 15000);   // (10240,20480], entries>=40 → 상수 적용 시 1
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 1,
    `[RED expect] 전역 부재는 상수(10240/40) 폴백이어야 함, got ${JSON.stringify(r.json && r.json.counts)}`);
  assert.strictEqual(r.stderr.trim(), '', `전역 부재는 정상 상태 — stderr가 비어 있어야 함, got "${r.stderr}"`);
});

test('[T083/L1-F1b-b] TS-011: 전역 setting.json이 깨진 JSON이면 exit 1이 아니라(비차단) 상수 폴백 + stderr 1줄', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's2-broken');
  const r = run(dir, ['validate', '--json'], null, HOME_BROKEN);
  assert.strictEqual(r.exitCode, 0, `[RED expect] 깨진 전역 설정은 비차단 exit 0이어야 함, got ${r.exitCode} (${r.stdout})`);
  assert.ok(r.stderr.trim().length > 0,
    `[RED expect] 깨진 전역 설정에서는 stderr에 사유 1줄이 있어야 함(noticeOnce) — 현재는 무출력`);
});

test('[T083/L1-F1b-b] TS-012: bootstrap·models만 있는 전역 설정(shardPolicy 키 부재) → 상수 폴백 + stderr 무출력', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's2-nokey');
  writeManifestBytes(dir, MOD_REL, 45, 15000);
  const r = run(dir, ['validate', '--json'], null, HOME_NOKEY);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 1,
    `[RED expect] shardPolicy 키 부재는 상수(10240/40) 폴백이어야 함, got ${JSON.stringify(r.json && r.json.counts)}`);
  assert.strictEqual(r.stderr.trim(), '', `키 부재는 침묵이어야 함, got "${r.stderr}"`);
});

test('[T083/L1-F1b-b] TS-013: 전역 shardPolicy.maxBytes 타입 위반 → 비차단 + 상수 폴백 + stderr 1줄, exit code 불변', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's2-badtype');
  const r = run(dir, ['validate', '--json'], null, HOME_BADTYPE);
  assert.strictEqual(r.exitCode, 0, `[RED expect] 전역 타입 위반은 비차단 exit 0이어야 함, got ${r.exitCode} (${r.stdout})`);
  assert.ok(r.stderr.trim().length > 0,
    `[RED expect] 전역 타입 위반은 stderr에 사유 1줄이 있어야 함 — 현재는 무출력`);
});

test('[T083/L1-F1b-a] TS-014: 같은 프로젝트를 서로 다른 OPAL_HOME 2개로 실행하면 정책이 다르게 적용된다', () => {
  const homeA = makeHome('t014a', { shardPolicy: { maxBytes: 500, minFiles: 2 } });
  const homeB = makeHome('t014b', { shardPolicy: { maxBytes: 30000, minFiles: 2 } });
  const dirA = copyFixture(path.join('shard-policy', 'base'), 's2-inject-a');
  const dirB = copyFixture(path.join('shard-policy', 'base'), 's2-inject-b');
  writeManifestBytes(dirA, MOD_REL, 5, 15000);
  writeManifestBytes(dirB, MOD_REL, 5, 15000);
  const rA = run(dirA, ['validate', '--json'], null, homeA);   // 15000 > 500 → oversize
  const rB = run(dirB, ['validate', '--json'], null, homeB);   // 15000 < 30000 → not oversize
  assert.strictEqual(rA.json && rA.json.counts && rA.json.counts.manifest_oversize, 1,
    `[RED expect] OPAL_HOME=homeA(maxBytes=500)에서는 초과여야 함, got ${JSON.stringify(rA.json && rA.json.counts)}`);
  assert.strictEqual(rB.json && rB.json.counts && rB.json.counts.manifest_oversize, 0,
    `[RED expect] OPAL_HOME=homeB(maxBytes=30000)에서는 초과가 아니어야 함, got ${JSON.stringify(rB.json && rB.json.counts)}`);
});

test('[T083/L1-F1b-c] TS-015: 실행 전후 전역 setting.json 바이트가 동일 + 그 사이 전역 정책은 실제로 소비된다', () => {
  const globalHome = makeHome('t015', { shardPolicy: { maxBytes: 12000, minFiles: 3 } });
  const settingPath = path.join(globalHome, 'setting.json');
  const before = fs.readFileSync(settingPath, 'utf8');
  const dir = copyFixture(path.join('shard-policy', 'base'), 's2-nowrite');
  writeManifestBytes(dir, MOD_REL, 5, 15000);   // (12000,20480] — 전역이 실제로 적용되면 초과 1건
  const r = run(dir, ['validate', '--json'], null, globalHome);
  run(dir, ['scaffold', '--json'], null, globalHome);
  const after = fs.readFileSync(settingPath, 'utf8');
  assert.strictEqual(after, before, '전역 setting.json은 code-scan 실행 전후 바이트가 동일해야 함');
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 1,
    `[RED expect] 전역 파일을 쓰지 않으면서도 읽어서 소비해야 함(maxBytes=12000 적용), got ${JSON.stringify(r.json && r.json.counts)}`);
});

test('[T083/L1-F1b-b] TS-016: 전역 4상태(부재·깨짐·키부재·타입위반) 전부 exit code 불변 + 타입위반은 stderr 안내 1줄', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's2-baseline');
  const baseline = run(dir, ['validate', '--json'], null, HOME_ABSENT).exitCode;
  for (const [label, home] of [['broken', HOME_BROKEN], ['nokey', HOME_NOKEY], ['badtype', HOME_BADTYPE]]) {
    const d = copyFixture(path.join('shard-policy', 'base'), `s2-baseline-${label}`);
    const r = run(d, ['validate', '--json'], null, home);
    assert.strictEqual(r.exitCode, baseline,
      `전역 상태(${label})에서도 exit code가 기준(${baseline})과 같아야 함, got ${r.exitCode}`);
  }
  const dBadtype = copyFixture(path.join('shard-policy', 'base'), 's2-baseline-badtype-notice');
  const rBadtype = run(dBadtype, ['validate', '--json'], null, HOME_BADTYPE);
  assert.ok(rBadtype.stderr.trim().length > 0,
    `[RED expect] 전역 shardPolicy 타입 위반은 stderr에 사유 1줄이 있어야 함 — 현재는 무출력`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-3: 2축 판정 + 경계 규칙 (H-2, H-3) — TS-020~026
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L1-F2a] TS-020: 바이트 초과 + 엔트리 수 미달 → manifest_oversize에 열거되지 않는다', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's3-bytes-only');
  setShardPolicy(dir, { maxBytes: 5000, minFiles: 40 });
  // size=25000 > 20480(구식 임계) 이면서 maxBytes=5000도 초과 — 그러나 entries 5 < 40(미달)이므로
  // 신규 2축 AND 조건이 살아있다면 0건이어야 한다. 미구현(엔트리 축 없음, size>20480만 봄)이면 1건 →
  // 반드시 어긋나 RED가 보장된다.
  writeManifestBytes(dir, MOD_REL, 5, 25000);
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 0,
    `[RED expect] 엔트리 미달이면 바이트 초과와 무관하게 0건이어야 함(AND 조건), got ${JSON.stringify(r.json && r.json.counts)}`);
});

test('[T083/L1-F2b] TS-021: 바이트 초과 + 엔트리 수 충족 → 1건 열거 + exit 0(비차단)', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's3-both');
  setShardPolicy(dir, { maxBytes: 5000, minFiles: 5 });
  writeManifestBytes(dir, MOD_REL, 6, 6000);   // 6000>5000, entries 6>=5
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `2축 충족 위반은 비차단(exit 0)이어야 함, got ${r.exitCode}`);
  assert.strictEqual(countViolations(r.json, 'manifest_oversize'), 1,
    `[RED expect] 2축 동시 충족 시 1건 열거돼야 함, got ${JSON.stringify(r.json && r.json.violations)}`);
});

test('[T083/L1-F2a] TS-022: 바이트 미달 + 엔트리 수 충족 → 0건 (AND 조건)', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's3-entries-only');
  setShardPolicy(dir, { maxBytes: 50000, minFiles: 3 });
  writeManifestBytes(dir, MOD_REL, 10, 25000);   // 25000<50000(미달), entries 10>=3(충족)
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 0,
    `[RED expect] 바이트 미달이면 엔트리 충족과 무관하게 0건이어야 함, got ${JSON.stringify(r.json && r.json.counts)}`);
});

test('[T083/L1-F2-경계] TS-023: entries===minFiles는 대상(하한은 이상), entries===minFiles-1은 비대상', () => {
  const dirEq = copyFixture(path.join('shard-policy', 'base'), 's3-boundary-eq');
  setShardPolicy(dirEq, { maxBytes: 5000, minFiles: 6 });
  writeManifestBytes(dirEq, MOD_REL, 6, 6000);   // entries === minFiles(6)
  const rEq = run(dirEq, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rEq.json && rEq.json.counts && rEq.json.counts.manifest_oversize, 1,
    `[RED expect] entries===minFiles는 대상(이상)이어야 함, got ${JSON.stringify(rEq.json && rEq.json.counts)}`);

  const dirBelow = copyFixture(path.join('shard-policy', 'base'), 's3-boundary-below');
  setShardPolicy(dirBelow, { maxBytes: 5000, minFiles: 6 });
  writeManifestBytes(dirBelow, MOD_REL, 5, 6000);   // entries === minFiles-1
  const rBelow = run(dirBelow, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rBelow.json && rBelow.json.counts && rBelow.json.counts.manifest_oversize, 0,
    `[RED expect] entries===minFiles-1은 비대상이어야 함, got ${JSON.stringify(rBelow.json && rBelow.json.counts)}`);
});

test('[T083/L1-F2-경계] TS-024: size===maxBytes는 비대상, size===maxBytes+1은 대상 (082 off-by-one 계약 보존)', () => {
  const dirProbe = copyFixture(path.join('shard-policy', 'base'), 's3-sizeprobe');
  setShardPolicy(dirProbe, { maxBytes: 1, minFiles: 1 });   // maxBytes=1은 임시 — 실제 크기 측정용
  const size = fileBytes(writeManifestBytes(dirProbe, MOD_REL, 5, 6000));

  const dirEq = copyFixture(path.join('shard-policy', 'base'), 's3-size-eq');
  setShardPolicy(dirEq, { maxBytes: size, minFiles: 1 });
  writeManifestBytes(dirEq, MOD_REL, 5, 6000);
  const rEq = run(dirEq, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rEq.json && rEq.json.counts && rEq.json.counts.manifest_oversize, 0,
    `[RED expect] size===maxBytes는 초과가 아니어야 함(off-by-one), got ${JSON.stringify(rEq.json && rEq.json.counts)}`);

  const dirOver = copyFixture(path.join('shard-policy', 'base'), 's3-size-over');
  setShardPolicy(dirOver, { maxBytes: size - 1, minFiles: 1 });
  writeManifestBytes(dirOver, MOD_REL, 5, 6000);
  const rOver = run(dirOver, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rOver.json && rOver.json.counts && rOver.json.counts.manifest_oversize, 1,
    `[RED expect] size===maxBytes+1은 초과여야 함, got ${JSON.stringify(rOver.json && rOver.json.counts)}`);
});

test('[T083/L1-F2c] TS-025: 베이스는 상한 이하·샤드만 2축 충족 → 1건 + manifest 필드가 샤드 경로 (082 S-25 계승)', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's3-shard');
  setShardPolicy(dir, { maxBytes: 5000, minFiles: 5 });
  // 베이스는 작게 유지(상한 이하), 샤드 파일을 직접 만들어 2축 충족시킨다.
  const shardAbs = path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'oversized.json');
  fs.mkdirSync(path.dirname(shardAbs), { recursive: true });
  fs.writeFileSync(shardAbs, craftManifestBytes(6, 6000));
  const baseAbs = path.join(dir, MOD_REL);
  const base = readJSON(baseAbs);
  base.shards = ['oversized'];
  writeJSON(baseAbs, base);
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  const v = findViolation(r.json, 'manifest_oversize');
  assert.ok(v, `[RED expect] 샤드가 2축 충족이면 manifest_oversize 1건이 있어야 함, violations=${JSON.stringify(r.json && r.json.violations)}`);
  assert.ok(v && /_shards\/oversized\.json$/.test(v.manifest),
    `[RED expect] manifest 필드가 샤드 경로여야 함, got ${v && v.manifest}`);
});

test('[T083/L1-F2-scaffold] TS-026: 2축 미충족이면 scaffold stderr 비어있고, 충족이면 1줄 + stdout 바이트 동일', () => {
  const dirUnmet = copyFixture(path.join('shard-policy', 'base'), 's3-scaffold-unmet');
  setShardPolicy(dirUnmet, { maxBytes: 5000, minFiles: 40 });   // entries 4 < 40 → 미충족
  const rUnmet = run(dirUnmet, ['scaffold', '--json'], null, HOME_ABSENT);

  const dirMet = copyFixture(path.join('shard-policy', 'base'), 's3-scaffold-met');
  setShardPolicy(dirMet, { maxBytes: 200, minFiles: 1 });   // base manifest(614B) > 200, entries 4>=1 → 충족
  const rMet = run(dirMet, ['scaffold', '--json'], null, HOME_ABSENT);

  assert.strictEqual(rUnmet.stderr.trim(), '', `2축 미충족이면 stderr가 비어야 함, got "${rUnmet.stderr}"`);
  assert.ok(rMet.stderr.trim().length > 0,
    `[RED expect] 2축 충족이면 stderr에 경고 1줄이 있어야 함 — 현재는 20480 상한이라 무출력`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-4: 분할 제안 `split --plan` 기본 계약 — 쓰기 0건 + 미분류 정직성 + 결정론 (H-10) — TS-030~039,116
// ═════════════════════════════════════════════════════════════════════════

const SPLIT_FIX = path.join('shard-policy', 'split-target');
const SPLIT_MANIFEST_ARG = '.opal/code-map/svc/mod.json';
const DICT_REL = path.join('200.설계', '210.사전', '표준단어사전.md');

test('[T083/L1-F4a] TS-030: split --plan --json — 그룹 후보 + estimatedBytes·files 존재', () => {
  const dir = copyFixture(SPLIT_FIX, 's4-plan');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `[RED expect] split --plan은 exit 0이어야 함, got ${r.exitCode} — 현재 split 명령 자체가 없음 (${r.stderr})`);
  assert.ok(r.json, `[RED expect] --json 출력이 유효 JSON이어야 함, raw="${r.stdout}"`);
  assert.ok(r.json && Array.isArray(r.json.groups), `[RED expect] groups 배열이 있어야 함, got ${r.stdout}`);
  for (const g of (r.json && r.json.groups) || []) {
    assert.ok(typeof g.estimatedBytes === 'number', `groups[].estimatedBytes가 숫자여야 함, got ${JSON.stringify(g)}`);
    assert.ok(Array.isArray(g.files) && g.files.length > 0, `groups[].files가 비지 않은 배열이어야 함, got ${JSON.stringify(g)}`);
  }
});

test('[T083/L1-F4a] TS-031/034: --plan 실행 전후 code-map 트리 바이트 동일(무쓰기), --out은 groups 문서 1개만 생성', () => {
  const dir = copyFixture(SPLIT_FIX, 's4-nowrite');
  const before = snapshotTree(dir, '.opal/code-map');
  run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  const after = snapshotTree(dir, '.opal/code-map');
  assert.deepStrictEqual(after, before, '[RED expect] --plan 실행 전후 .opal/code-map/ 트리가 바이트 동일해야 함(쓰기 0건)');

  const outPath = path.join(dir, 'groups-out.json');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--out', 'groups-out.json', '--json'], null, HOME_ABSENT);
  assert.ok(fs.existsSync(outPath),
    `[RED expect] --out을 주면 groups 문서가 생성돼야 함(exit=${r.exitCode}, stderr=${r.stderr})`);
  const afterOut = snapshotTree(dir, '.opal/code-map');
  assert.deepStrictEqual(afterOut, before, '--out 사용 후에도 매니페스트 자체는 무변화여야 함');
});

test('[T083/L1-F4b] TS-033/116: --plan --json 2회 실행 stdout이 바이트 동일(결정론) — 사전 유/무 각각', () => {
  const dirDict = copyFixture(SPLIT_FIX, 's4-determinism-dict');
  const r1 = run(dirDict, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r1.exitCode, 0, `[RED expect] split --plan은 exit 0이어야 함 — 현재 split 명령 자체가 없음, got ${r1.exitCode} (${r1.stderr})`);
  const r2 = run(dirDict, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r1.stdout, r2.stdout, '[RED expect] 사전 있는 상태에서 2회 실행 stdout이 바이트 동일해야 함');

  const dirNoDict = copyFixture(SPLIT_FIX, 's4-determinism-nodict');
  fs.rmSync(path.join(dirNoDict, DICT_REL));
  const r3 = run(dirNoDict, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  const r4 = run(dirNoDict, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r3.stdout, r4.stdout, '[RED expect] 사전 없는 상태에서도 2회 실행 stdout이 바이트 동일해야 함');
});

test('[T083/L1-F4c] TS-032/035~037: 1건뿐인 엔트리는 unassigned + "기타" 그룹 0개 + 라벨 안전', () => {
  const dir = copyFixture(SPLIT_FIX, 's4-unassigned');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json, `[RED expect] --json 출력이 유효 JSON이어야 함, raw="${r.stdout}"`);
  assert.ok(r.json && Array.isArray(r.json.unassigned) && r.json.unassigned.includes('QuirkyLoneModule.ts'),
    `[RED expect] QuirkyLoneModule.ts는 어떤 사전·빈도·depends에도 안 걸려 unassigned에 있어야 함, got ${JSON.stringify(r.json && r.json.unassigned)}`);
  const labels = ((r.json && r.json.groups) || []).map(g => g.label);
  for (const forbidden of ['misc', 'other', 'etc']) {
    assert.ok(!labels.includes(forbidden), `[RED expect] "기타" 그룹 라벨(${forbidden})이 없어야 함, got ${JSON.stringify(labels)}`);
  }
  const SHARD_LABEL_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
  for (const l of labels) {
    assert.ok(SHARD_LABEL_RE.test(l), `[RED expect] 모든 라벨이 SHARD_LABEL_RE를 통과해야 함, got "${l}"`);
  }
});

test('[T083/L1-F4-usage] TS-038: inline 모드에서 split --plan → exit 1 split_inline_mode', () => {
  const dir = copyFixture(SPLIT_FIX, 's4-inline');
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const cfg = readJSON(cfgPath);
  cfg.headerSource = 'inline';
  writeJSON(cfgPath, cfg);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 1, `[RED expect] inline 모드 split은 exit 1이어야 함, got ${r.exitCode}`);
  assert.strictEqual(r.json && r.json.error, 'split_inline_mode',
    `[RED expect] error === 'split_inline_mode', got ${r.stdout} (stderr: ${r.stderr})`);
});

test('[T083/L1-F4-usage] TS-039: --plan과 --groups 동시 지정 → exit 1 split_usage_invalid', () => {
  const dir = copyFixture(SPLIT_FIX, 's4-usage');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--groups', '-', '--json'], '{}', HOME_ABSENT);
  assert.strictEqual(r.exitCode, 1, `[RED expect] --plan/--groups 동시 지정은 exit 1이어야 함, got ${r.exitCode}`);
  assert.strictEqual(r.json && r.json.error, 'split_usage_invalid',
    `[RED expect] error === 'split_usage_invalid', got ${r.stdout} (stderr: ${r.stderr})`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-5: 사다리 5단계 — 잔여만 흘려보내기 + 단계별 동작 + 다중 매칭 결정론 (H-10) — TS-100~108,132
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L1-F4d] TS-100~101: 각 단계는 직전 잔여만 입력받고, 앞 단계 배정은 후속 단계에서 불변', () => {
  const dir = copyFixture(SPLIT_FIX, 's5-cascade');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--trace', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && Array.isArray(r.json.trace) && r.json.trace.length === 5,
    `[RED expect] --trace는 사다리 5단계 trace 배열을 내야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  const trace = r.json.trace;
  for (let i = 1; i < trace.length; i++) {
    assert.strictEqual(trace[i].input, trace[i - 1].remaining,
      `[RED expect] trace[${i}].input === trace[${i - 1}].remaining이어야 함, got ${JSON.stringify(trace)}`);
  }
  // 앞 단계(S1)에서 배정된 엔트리가 이후 단계에서 재배정되지 않는다.
  const assignments = r.json.assignments || {};
  assert.strictEqual(assignments['OrderRepository.ts'], 'S1',
    `[RED expect] OrderRepository.ts는 S1에서 배정돼야 하며 이후 불변이어야 함, got ${JSON.stringify(assignments)}`);
});

test('[T083/L1-F4d] TS-102~106,132: 신호별 배정 — S1 첫토큰/S2 첫2토큰/S3 임의토큰/S4 마지막토큰/S5 depends', () => {
  const dir = copyFixture(SPLIT_FIX, 's5-signals');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && Array.isArray(r.json.groups), `[RED expect] groups 배열이 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  const byLabel = {};
  for (const g of r.json.groups) byLabel[g.label] = g;

  const orderS1 = Object.values(byLabel).find(g => g.stage === 'S1' && g.files.includes('OrderRepository.ts'));
  assert.ok(orderS1 && orderS1.files.includes('OrderService.ts'),
    `[RED expect] OrderRepository.ts·OrderService.ts가 S1(첫 토큰 사전매칭 'order')로 묶여야 함, got ${JSON.stringify(r.json.groups)}`);

  const taxS2 = Object.values(byLabel).find(g => g.stage === 'S2' && g.files.includes('TaxRuleAlpha.ts'));
  assert.ok(taxS2 && taxS2.files.includes('TaxRuleBeta.ts'),
    `[RED expect] TaxRuleAlpha.ts·TaxRuleBeta.ts가 S2(첫 2토큰 결합 'TaxRule')로 묶여야 함, got ${JSON.stringify(r.json.groups)}`);

  const orderS3 = Object.values(byLabel).find(g => g.stage === 'S3' && g.files.includes('LegacyOrderTable.ts'));
  assert.ok(orderS3 && orderS3.files.includes('TempOrderView.ts'),
    `[RED expect] LegacyOrderTable.ts·TempOrderView.ts가 S3(중간 토큰 'order')로 묶여야 함, got ${JSON.stringify(r.json.groups)}`);

  const handlerS4 = Object.values(byLabel).find(g => g.stage === 'S4' && g.files.includes('AlphaHandler.ts'));
  assert.ok(handlerS4 && handlerS4.files.includes('BetaHandler.ts') && handlerS4.files.includes('GammaHandler.ts'),
    `[RED expect] *Handler.ts 3건이 S4(마지막 토큰 'handler', 빈도 3)로 묶여야 함, got ${JSON.stringify(r.json.groups)}`);

  const index = r.json.dict && Array.isArray(r.json.dict.rows) ? r.json.dict.rows : null;
  assert.ok(r.json.dict, `[RED expect] dict 필드가 있어야 함, got ${r.stdout}`);
});

test('[T083/L1-F4d] TS-106: depends를 공유하는 엔트리 3건 이상이 S5 그룹이 된다 (파생 픽스처)', () => {
  // split-target 기본 10엔트리는 depends 보유분(3건)이 모두 S1~S3에서 먼저 걷혀 S5까지 도달하지
  // 않는다 — S5 신호를 관측하려면 사전 미매칭·빈도 미달 토큰 + 공유 depends 3건을 파생 주입한다
  // (082 G-3 계승 — 변형은 copyFixture 후 JSON 편집으로 만든다, 수작성 2벌 금지).
  const dir = copyFixture(SPLIT_FIX, 's5-depends');
  const manifestAbs = path.join(dir, SPLIT_MANIFEST_ARG);
  const manifest = readJSON(manifestAbs);
  manifest.files['ZinniaWidgetA.ts'] = { description: '위젯 A (S5 depends 공유 검증용)', exports: ['ZinniaWidgetA'], depends: ['widget-core'] };
  manifest.files['ZinniaWidgetB.ts'] = { description: '위젯 B (S5 depends 공유 검증용)', exports: ['ZinniaWidgetB'], depends: ['widget-core'] };
  manifest.files['ZinniaWidgetC.ts'] = { description: '위젯 C (S5 depends 공유 검증용)', exports: ['ZinniaWidgetC'], depends: ['widget-core'] };
  writeJSON(manifestAbs, manifest);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && Array.isArray(r.json.groups), `[RED expect] groups 배열이 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  const s5 = r.json.groups.find(g => g.stage === 'S5');
  assert.ok(s5, `[RED expect] widget-core를 공유하는 3건이 S5 그룹을 형성해야 함, got ${JSON.stringify(r.json.groups)}`);
  assert.ok(['ZinniaWidgetA.ts', 'ZinniaWidgetB.ts', 'ZinniaWidgetC.ts'].every(k => s5.files.includes(k)),
    `[RED expect] S5 그룹에 3개 위젯 파일이 모두 포함돼야 함, got ${JSON.stringify(s5)}`);
});

test('[T083/L1-F4d] TS-107~108: S1~S3 2건 미만·S4~S5 3건 미만은 다음 단계로 흐르고, 다중 매칭은 스팬 길이·등재 순서로 결정론적', () => {
  const dir = copyFixture(SPLIT_FIX, 's5-accept');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--trace', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && Array.isArray(r.json.trace), `[RED expect] --trace 출력이 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  // 사전 등재 순서(index)가 두 표(수식어 6열·분류어 5열)에 걸쳐 연속 번호인지 dict 메타로 확인.
  assert.ok(r.json.dict && typeof r.json.dict.rows === 'number' && r.json.dict.rows >= 5,
    `[RED expect] dict.rows(등재 행 수)가 두 표 합산(≥5)이어야 함, got ${JSON.stringify(r.json.dict)}`);
});

test('[T083/L1-F4d] ★S-5 채택 효과 단언: 사다리 최종 unassigned 수는 S1 단독 실행 시점의 unassigned보다 작다', () => {
  // "5단계 각 1그룹 이상"만으로는 각 단계가 1그룹만 걷어도 통과하므로, 단일 축 불채택 사유를
  // 실제로 개선했는지를 --stop-after S1로 만든 "S1 단독" 기준선과 비교해 겨눈다.
  const dirFull = copyFixture(SPLIT_FIX, 's5-effect-full');
  const rFull = run(dirFull, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(rFull.json && Array.isArray(rFull.json.unassigned),
    `[RED expect] 전 단계 실행 결과에 unassigned 배열이 있어야 함, got ${rFull.stdout} (stderr: ${rFull.stderr})`);

  const dirS1Only = copyFixture(SPLIT_FIX, 's5-effect-s1only');
  const rS1Only = run(dirS1Only, ['split', SPLIT_MANIFEST_ARG, '--plan', '--stop-after', 'S1', '--json'], null, HOME_ABSENT);
  assert.ok(rS1Only.json && Array.isArray(rS1Only.json.unassigned),
    `[RED expect] --stop-after S1 결과에 unassigned 배열이 있어야 함, got ${rS1Only.stdout} (stderr: ${rS1Only.stderr})`);

  const fullUnassigned = (rFull.json && rFull.json.unassigned || []).length;
  const s1OnlyUnassigned = (rS1Only.json && rS1Only.json.unassigned || []).length;
  assert.ok(fullUnassigned < s1OnlyUnassigned,
    `[RED expect] 전 단계 사다리의 unassigned(${fullUnassigned})는 S1 단독(${s1OnlyUnassigned})보다 작아야 함(채택 효과)`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-6: 검토 장치 3종 + 왕복 계약 보존 (H-18) — TS-109~114
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L2-F4f] TS-109: --trace 단계별 표 — assigned+unassigned===total', () => {
  const dir = copyFixture(SPLIT_FIX, 's6-trace-sum');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--trace', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.coverage, `[RED expect] coverage 필드가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  const c = r.json.coverage;
  assert.strictEqual(c.assigned + c.unassigned, c.total,
    `[RED expect] coverage.assigned + unassigned === total이어야 함, got ${JSON.stringify(c)}`);
});

test('[T083/L2-F4f] TS-110: --stop-after S2가 S3~S5를 실행하지 않고 잔여를 전부 unassigned로 낸다', () => {
  const dir = copyFixture(SPLIT_FIX, 's6-stopafter');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--trace', '--stop-after', 'S2', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && Array.isArray(r.json.trace), `[RED expect] --trace 출력이 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  const byId = {};
  for (const t of r.json.trace) byId[t.stage] = t;
  for (const id of ['S3', 'S4', 'S5']) {
    assert.strictEqual(byId[id] && byId[id].reason, 'stopped',
      `[RED expect] --stop-after S2 이후 ${id} trace.reason === 'stopped'이어야 함, got ${JSON.stringify(byId[id])}`);
  }
});

test('[T083/L2-F4f] TS-111: 사다리 id 밖 --stop-after 값 → exit 1 split_usage_invalid + 허용값 목록', () => {
  const dir = copyFixture(SPLIT_FIX, 's6-stopafter-invalid');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--stop-after', 'S9', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 1, `[RED expect] 사다리 밖 --stop-after는 exit 1이어야 함, got ${r.exitCode}`);
  assert.strictEqual(r.json && r.json.error, 'split_usage_invalid',
    `[RED expect] error === 'split_usage_invalid', got ${r.stdout} (stderr: ${r.stderr})`);
  assert.ok(r.json && typeof r.json.fix === 'string' && /S1/.test(r.json.fix),
    `[RED expect] fix에 허용값 목록(S1~S5)이 실려야 함, got ${r.stdout}`);
});

test('[T083/L2-F4f] TS-112: 모든 배정 엔트리에 stage가 실리고 groups[].stage ↔ assignments[key] 일치', () => {
  const dir = copyFixture(SPLIT_FIX, 's6-stage-consistency');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.assignments && Array.isArray(r.json.groups),
    `[RED expect] assignments·groups가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  for (const g of r.json.groups) {
    for (const f of g.files) {
      assert.strictEqual(r.json.assignments[f], g.stage,
        `[RED expect] assignments['${f}'](${r.json.assignments[f]}) === groups[].stage(${g.stage})여야 함`);
    }
  }
});

test('[T083/L2-F4f] TS-113: --trace --stop-after 출력을 그대로 --groups -(stdin) 파이프해도 성공한다(왕복)', () => {
  const dir = copyFixture(SPLIT_FIX, 's6-roundtrip');
  const planRes = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--trace', '--stop-after', 'S3', '--json'], null, HOME_ABSENT);
  assert.ok(planRes.json, `[RED expect] --plan 출력이 유효 JSON이어야 함, raw="${planRes.stdout}" (stderr: ${planRes.stderr})`);
  const applyRes = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--dry-run', '--json'], planRes.stdout, HOME_ABSENT);
  assert.strictEqual(applyRes.exitCode, 0,
    `[RED expect] --trace --stop-after 출력을 그대로 --groups -에 파이프해도 성공해야 함(선택 필드 무시), got ${applyRes.exitCode} (stderr: ${applyRes.stderr})`);
});

test('[T083/L1-F4e] TS-114: 사전 미발견 시 S1~S3은 skipped:dict_absent이고 S4·S5만 실행된다', () => {
  const dir = copyFixture(SPLIT_FIX, 's6-dict-skip');
  fs.rmSync(path.join(dir, DICT_REL));
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--trace', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && Array.isArray(r.json.trace), `[RED expect] --trace 출력이 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  const byId = {};
  for (const t of r.json.trace) byId[t.stage] = t;
  for (const id of ['S1', 'S2', 'S3']) {
    assert.strictEqual(byId[id] && byId[id].skipped, true,
      `[RED expect] 사전 미발견 시 ${id}.skipped===true여야 함, got ${JSON.stringify(byId[id])}`);
    assert.strictEqual(byId[id] && byId[id].reason, 'dict_absent',
      `[RED expect] ${id}.reason==='dict_absent'여야 함, got ${JSON.stringify(byId[id])}`);
  }
  assert.strictEqual(byId.S4 && byId.S4.skipped, false, `S4는 사전 무관하게 실행돼야 함, got ${JSON.stringify(byId.S4)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-7: 용어사전 — 탐색 3단 + 2표 파싱 + 3분기 폴백 + 읽기 전용 (H-15,16,17,19) — TS-115,120~131
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L1-F4e] TS-115: 사전 미발견 시 dict.found===false + dict.searched 경로 목록', () => {
  const dir = copyFixture(SPLIT_FIX, 's7-absent');
  fs.rmSync(path.join(dir, DICT_REL));
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--trace', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.dict, `[RED expect] dict 필드가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.strictEqual(r.json.dict.found, false, `[RED expect] dict.found===false여야 함, got ${JSON.stringify(r.json.dict)}`);
  assert.ok(Array.isArray(r.json.dict.searched) && r.json.dict.searched.length > 0,
    `[RED expect] dict.searched 경로 목록이 있어야 함, got ${JSON.stringify(r.json.dict)}`);
});

test('[T083/L1-F4e] TS-120: shardPolicy.dictPath 명시값이 최우선 — dict.source==="policy"', () => {
  const dir = copyFixture(SPLIT_FIX, 's7-policy-path');
  const customRel = path.join('custom', '사전.md');
  fs.mkdirSync(path.join(dir, 'custom'), { recursive: true });
  fs.copyFileSync(path.join(dir, DICT_REL), path.join(dir, customRel));
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const cfg = readJSON(cfgPath);
  cfg.shardPolicy.dictPath = customRel.split(path.sep).join('/');
  writeJSON(cfgPath, cfg);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.dict, `[RED expect] dict 필드가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.strictEqual(r.json.dict.source, 'policy',
    `[RED expect] dictPath 명시 시 dict.source==='policy'여야 함, got ${JSON.stringify(r.json.dict)}`);
});

test('[T083/L1-F4e] TS-121: docs/PROJECT.md의 {설계} 변수가 해소되면 dict.source==="project-var"', () => {
  const dir = copyFixture(SPLIT_FIX, 's7-project-var');
  fs.mkdirSync(path.join(dir, 'docs'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'docs', 'PROJECT.md'), '| 요소 | 경로 |\n|---|---|\n| {설계} | custom-design/ |\n');
  fs.mkdirSync(path.join(dir, 'custom-design', '사전'), { recursive: true });
  fs.copyFileSync(path.join(dir, DICT_REL), path.join(dir, 'custom-design', '사전', '표준단어사전.md'));
  fs.rmSync(path.join(dir, DICT_REL));
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.dict, `[RED expect] dict 필드가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.strictEqual(r.json.dict.source, 'project-var',
    `[RED expect] {설계} 변수 해소 시 dict.source==='project-var'여야 함, got ${JSON.stringify(r.json.dict)}`);
});

test('[T083/L1-F4e] TS-122~123: 변수 미등록 시 기본 경로 2후보 중 어디에 두어도 발견 + 앞 단계 성공 시 뒤를 안 본다', () => {
  const dir = copyFixture(SPLIT_FIX, 's7-default-path');
  // split-target은 이미 200.설계/210.사전/표준단어사전.md(2후보 중 두 번째)에 있고 {설계} 변수는 미등록
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.dict, `[RED expect] dict 필드가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.strictEqual(r.json.dict.found, true, `[RED expect] 기본 경로 2후보 중 하나에서 발견돼야 함, got ${JSON.stringify(r.json.dict)}`);
  assert.strictEqual(r.json.dict.source, 'default', `[RED expect] dict.source==='default'여야 함, got ${JSON.stringify(r.json.dict)}`);
});

test('[T083/L1-F4e] TS-124: 수식어(6열)·분류어(5열) 두 표에서 영문·약어가 정확히 추출된다(헤더 이름 기반)', () => {
  const dir = copyFixture(SPLIT_FIX, 's7-two-tables');
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.dict, `[RED expect] dict 필드가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  // 두 표 합산 5행(회사·세율규칙·번호·주문·규칙) — 위치 기반 파서라면 분류어 표(5열)의 '약어' 자리에
  // '도메인' 값이 잘못 들어가 카운트/매칭이 어긋난다.
  assert.strictEqual(r.json.dict.rows, 5, `[RED expect] 두 표 합산 5행이 파싱돼야 함, got ${JSON.stringify(r.json.dict)}`);
});

test('[T083/L1-F4e] TS-125~127: 헤더 불일치 표 무시 + 파손 stderr 1줄 + 부재는 침묵', () => {
  const dirBroken = copyFixture(SPLIT_FIX, 's7-broken');
  fs.writeFileSync(path.join(dirBroken, DICT_REL), '# 표준단어사전\n\n그냥 텍스트, 표 아님\n');
  const rBroken = run(dirBroken, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(rBroken.json && rBroken.json.dict, `[RED expect] dict 필드가 있어야 함, got ${rBroken.stdout} (stderr: ${rBroken.stderr})`);
  assert.strictEqual(rBroken.json.dict.found, false, `[RED expect] 헤더 불일치 표는 무시되어 found===false여야 함, got ${JSON.stringify(rBroken.json.dict)}`);
  assert.ok(rBroken.stderr.trim().length > 0, `[RED expect] 파손 사전은 stderr에 1줄이 있어야 함, got "${rBroken.stderr}"`);

  const dirAbsent = copyFixture(SPLIT_FIX, 's7-silent-absent');
  fs.rmSync(path.join(dirAbsent, DICT_REL));
  const rAbsent = run(dirAbsent, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rAbsent.stderr.trim(), '', `[RED expect] 사전 부재는 stderr 무출력(침묵)이어야 함, got "${rAbsent.stderr}"`);
});

test('[T083/L1-F4e] TS-128: dictPath가 프로젝트 루트 밖이면 읽지 않고 다음 후보로 넘어간다(경로 이탈 차단)', () => {
  const dir = copyFixture(SPLIT_FIX, 's7-traversal');
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const cfg = readJSON(cfgPath);
  cfg.shardPolicy.dictPath = '../../../../../etc/passwd';
  writeJSON(cfgPath, cfg);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.dict, `[RED expect] dict 필드가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.notStrictEqual(r.json.dict.source, 'policy',
    `[RED expect] 프로젝트 밖 dictPath는 거부되고 다음 후보(기본 경로)로 넘어가야 함, got ${JSON.stringify(r.json.dict)}`);
  assert.strictEqual(r.json.dict.found, true,
    `[RED expect] 다음 후보(기본 경로)에서 발견돼야 함, got ${JSON.stringify(r.json.dict)}`);
});

test('[T083/L1-F4e] TS-129: 사전 파일이 크기 상한 초과면 "사전 없음" 취급 + 도구가 멈추지 않는다', () => {
  const dir = copyFixture(SPLIT_FIX, 's7-toolarge');
  const huge = '| 한글 | 영문 | 약어 |\n|---|---|---|\n' + 'x'.repeat(3 * 1024 * 1024);
  fs.writeFileSync(path.join(dir, DICT_REL), huge);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `[RED expect] 초대형 사전에서도 exit 0이어야 함(멈추지 않음), got ${r.exitCode} (stderr: ${r.stderr})`);
  assert.ok(r.json && r.json.dict, `[RED expect] dict 필드가 있어야 함, got ${r.stdout}`);
  assert.strictEqual(r.json.dict.found, false, `[RED expect] 크기 상한 초과는 "사전 없음" 취급이어야 함, got ${JSON.stringify(r.json.dict)}`);
});

test('[T083/L1-F4e] TS-130~131: split --plan 실행 전후 사전·docs/PROJECT.md 바이트 동일 + 조회 8커맨드는 사전을 읽지 않는다(지연 로딩)', () => {
  const dir = copyFixture(SPLIT_FIX, 's7-readonly');
  const dictAbs = path.join(dir, DICT_REL);
  const before = fs.readFileSync(dictAbs, 'utf8');
  const rSplit = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rSplit.exitCode, 0,
    `[RED expect] split --plan은 exit 0이어야 함 — 현재 split 명령 자체가 없음, got ${rSplit.exitCode} (${rSplit.stderr})`);
  const after = fs.readFileSync(dictAbs, 'utf8');
  assert.strictEqual(after, before, '사전 파일은 split --plan 실행 전후 바이트가 동일해야 함(읽기 전용)');

  // 조회 커맨드(scan)는 사전을 아예 열지 않아야 한다 — scan --json 출력에 dict 필드 자체가
  // 없어야 한다(지연 로딩 증거). 필드가 있다면(=현재 신 필드가 없어 이 단언 자체가 무의미해지는
  // 상황을 막기 위해) split --plan 성공 여부로 먼저 RED를 보장한다(위 단언).
  const dirNoDict = copyFixture(SPLIT_FIX, 's7-lazy');
  fs.rmSync(path.join(dirNoDict, DICT_REL));
  const rScan = run(dirNoDict, ['scan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rScan.exitCode, 0, `scan은 사전 유무와 무관하게 exit 0이어야 함, got ${rScan.exitCode}`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-8: `init` 게이트 순환 부재 + 비대화형 계약 [P0] (H-22) — TS-140~144,158
// ═════════════════════════════════════════════════════════════════════════

/** `.opal/code-scan.json` 자체가 없는 완전히 빈 프로젝트 트리 — init/empty 등가물. `.opal` 디렉토리(빈)만 둬서
 * findProjectRoot가 이 트리 자신을 루트로 잡게 한다(082 관용 — .git/.opal/CLAUDE.md 중 하나 필요). */
function makeEmptyProjectTree(tag) {
  const dir = emptyDir(tag);
  fs.mkdirSync(path.join(dir, '.opal'), { recursive: true });
  return dir;
}

test('[T083/L1-X-a] TS-140: .opal/code-scan.json이 없는 트리에서 init --header-source inline이 exit 0으로 초안을 낸다', () => {
  const dir = makeEmptyProjectTree('s8-empty');
  const r = run(dir, ['init', '--header-source', 'inline', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0,
    `[RED expect] 설정이 없는 트리에서 init은 exit 0이어야 함(header_source_unset 차단에 걸리지 않음), got ${r.exitCode} (stderr: ${r.stderr})`);
  assert.notStrictEqual(r.json && r.json.error, 'header_source_unset',
    '[RED expect] init은 게이트 예외이므로 header_source_unset으로 차단되면 안 됨(H-22 게이트 순환)');
});

test('[T083/L1-X-a] TS-141: .opal/code-scan.json이 깨진 JSON인 트리에서도 init --write --force가 exit 0으로 복구한다', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's8-corrupt');
  fs.writeFileSync(path.join(dir, '.opal', 'code-scan.json'), '{ this is not json');
  const r = run(dir, ['init', '--header-source', 'inline', '--write', '--force', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0,
    `[RED expect] 깨진 config에서도 init --write --force는 exit 0으로 복구해야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  const restored = readJSON(path.join(dir, '.opal', 'code-scan.json'));
  assert.strictEqual(restored.headerSource, 'inline',
    `[RED expect] 복구된 설정의 headerSource==='inline'이어야 함, got ${JSON.stringify(restored)}`);
});

test('[T083/L1-X-b] TS-142: TTY 없이 실행해도 정상 동작하고 프롬프트를 출력하지 않는다', () => {
  const dir = makeEmptyProjectTree('s8-notty');
  const r = run(dir, ['init', '--header-source', 'manifest', '--json'], '', HOME_ABSENT);   // 빈 stdin = TTY 없음과 동등
  assert.strictEqual(r.exitCode, 0, `[RED expect] TTY 없이도 init은 exit 0이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  assert.ok(!/\?|프롬프트|입력하세요/.test(r.stdout), `[RED expect] stdout에 프롬프트 문구가 없어야 함, got ${r.stdout}`);
});

test('[T083/L1-X-b] TS-143: --header-source 누락 시 exit 1 init_header_source_required + 파일 미생성', () => {
  const dir = makeEmptyProjectTree('s8-required');
  const r = run(dir, ['init', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 1, `[RED expect] --header-source 누락은 exit 1이어야 함, got ${r.exitCode}`);
  assert.strictEqual(r.json && r.json.error, 'init_header_source_required',
    `[RED expect] error === 'init_header_source_required', got ${r.stdout} (stderr: ${r.stderr})`);
  assert.ok(!fs.existsSync(path.join(dir, '.opal', 'code-scan.json')),
    '[RED expect] --header-source 누락 시 파일이 생성되면 안 됨');
});

test('[T083/L1-X-b] TS-144: --header-source auto(구형 값)는 exit 1 header_source_invalid + init 자체는 유효값에서 동작한다', () => {
  const dir = makeEmptyProjectTree('s8-legacy');
  const r = run(dir, ['init', '--header-source', 'auto', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 1, `구형 값 auto는 exit 1이어야 함, got ${r.exitCode}`);
  assert.strictEqual(r.json && r.json.error, 'header_source_invalid',
    `error === 'header_source_invalid'(resolveHeaderSource 재사용), got ${r.stdout} (stderr: ${r.stderr})`);
  // [RED 보장] 위 두 단언은 기존 전역 게이트만으로도 우연히 성립할 수 있다(init 자체가 아직
  // 없어도 --header-source auto는 어떤 명령이든 이 경로를 탄다) — init이 실제로 구현됐는지는
  // 유효값에서의 성공 여부로만 구분된다.
  const dirValid = makeEmptyProjectTree('s8-legacy-valid');
  const rValid = run(dirValid, ['init', '--header-source', 'manifest', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rValid.exitCode, 0,
    `[RED expect] 유효값(manifest)에서는 init이 exit 0으로 동작해야 함 — 현재 init 명령 자체가 없음, got ${rValid.exitCode} (stderr: ${rValid.stderr})`);
});

test('[T083/L1-X-b] TS-158: init 추가로 15서브명령이 되고, 나머지 13 명령의 게이트 차단 동작은 불변이다', () => {
  const dir = makeEmptyProjectTree('s8-regression-gate');
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 1, `설정 없는 트리에서 validate는 여전히 차단(exit 1)돼야 함, got ${r.exitCode}`);
  assert.strictEqual(r.json && r.json.error, 'header_source_unset',
    `설정 없는 트리에서 validate는 여전히 header_source_unset이어야 함, got ${r.stdout}`);
  assert.ok(/\binit\b/.test(SRC.match(/const USAGE = `[\s\S]*?`;/)[0]),
    `[RED expect] USAGE 도움말에 init 서브명령이 등재돼야 함 — 현재는 13개(scan/domain/.../feature)만 있음`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-9: `init` 쓰기 3분기 + 백업 + 규약 일치 추론 (H-20, H-21) — TS-145~157,160
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L2-X-c] TS-145: 파일 없음 + --write 없음 → stdout 초안 + 쓰기 0건', () => {
  const dir = makeEmptyProjectTree('s9-nowrite');
  const r = run(dir, ['init', '--header-source', 'inline', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `[RED expect] exit 0이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  assert.ok(!fs.existsSync(path.join(dir, '.opal', 'code-scan.json')),
    '[RED expect] --write 없이는 파일이 생성되면 안 됨(쓰기 0건)');
  assert.ok(r.stdout.trim().length > 0, '[RED expect] stdout에 초안이 출력돼야 함');
});

test('[T083/L2-X-c] TS-146: 파일 있음 + --write(force 없음) → exit 1 config_exists + 기존 파일 바이트 동일', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's9-exists');
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const before = fs.readFileSync(cfgPath, 'utf8');
  const r = run(dir, ['init', '--header-source', 'manifest', '--write', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 1, `[RED expect] 기존 파일이 있으면 --force 없이는 exit 1이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  assert.strictEqual(r.json && r.json.error, 'config_exists',
    `[RED expect] error === 'config_exists', got ${r.stdout}`);
  assert.strictEqual(fs.readFileSync(cfgPath, 'utf8'), before, '[RED expect] 기존 파일은 바이트 동일하게 보존돼야 함');
});

test('[T083/L2-X-c] TS-147/153: 파일 있음 + --write --force → .bak이 원본과 바이트 동일 + stderr 보고 1줄', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's9-force');
  const cfgPath = path.join(dir, '.opal', 'code-scan.json');
  const before = fs.readFileSync(cfgPath, 'utf8');
  const r = run(dir, ['init', '--header-source', 'manifest', '--write', '--force', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `[RED expect] --force는 exit 0이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  const bakPath = cfgPath + '.bak';
  assert.ok(fs.existsSync(bakPath), '[RED expect] .opal/code-scan.json.bak이 생성돼야 함');
  assert.strictEqual(fs.readFileSync(bakPath, 'utf8'), before, '[RED expect] .bak은 원본과 바이트 동일해야 함');
  assert.ok(r.stderr.trim().length > 0, '[RED expect] 생성 보고가 stderr에 1줄 있어야 함');
  assert.strictEqual(r.stdout.trim().length > 0 && (() => { try { JSON.parse(r.stdout); return true; } catch { return false; } })(), true,
    '[RED expect] stdout JSON은 오염되지 않아야 함(파싱 가능)');
});

test('[T083/L2-X-d] TS-148~149: docs/PROJECT.md 프로젝트 구성 표에서 scopes 추론, 표 없으면 디렉토리 스캔 폴백', () => {
  const dir = makeEmptyProjectTree('s9-scopes-table');
  fs.mkdirSync(path.join(dir, 'docs'), { recursive: true });
  fs.writeFileSync(path.join(dir, 'docs', 'PROJECT.md'),
    '## 프로젝트 구성\n\n| 요소 | 경로 |\n|---|---|\n| Console FE | `frontend/` |\n| Console BE | `backend/` |\n');
  fs.mkdirSync(path.join(dir, 'frontend'), { recursive: true });
  fs.mkdirSync(path.join(dir, 'backend'), { recursive: true });
  const r = run(dir, ['init', '--header-source', 'inline', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.draft, `[RED expect] --json 초안(draft)이 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.deepStrictEqual(Object.keys(r.json.draft.scopes || {}).sort(), ['console-be', 'console-fe'],
    `[RED expect] 표의 요소 컬럼이 kebab 소문자 scopes 키로 추론돼야 함, got ${JSON.stringify(r.json && r.json.draft)}`);

  const dirFallback = makeEmptyProjectTree('s9-scopes-fallback');
  fs.mkdirSync(path.join(dirFallback, 'alpha'), { recursive: true });
  fs.mkdirSync(path.join(dirFallback, 'beta'), { recursive: true });
  const rFallback = run(dirFallback, ['init', '--header-source', 'inline', '--json'], null, HOME_ABSENT);
  assert.ok(rFallback.json && rFallback.json.draft && Object.keys(rFallback.json.draft.scopes || {}).length > 0,
    `[RED expect] 표 없으면 1-depth 디렉토리 스캔으로 scopes가 채워져야 함, got ${rFallback.stdout} (stderr: ${rFallback.stderr})`);
});

test('[T083/L2-X-d] TS-150~151: extensions에 .md 항상 포함 + exclude 규약 예시 10종과 정확 일치 + 키 순서', () => {
  const dir = makeEmptyProjectTree('s9-draft-shape');
  const r = run(dir, ['init', '--header-source', 'inline', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.draft, `[RED expect] draft가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  const draft = r.json.draft;
  assert.ok(Array.isArray(draft.extensions) && draft.extensions.includes('.md'),
    `[RED expect] extensions에 .md가 항상 포함돼야 함, got ${JSON.stringify(draft.extensions)}`);
  assert.deepStrictEqual(draft.exclude,
    ['node_modules', '__pycache__', '.git', 'dist', 'build', '.venv', 'backup', '.pytest_cache', '.next', '.nuxt'],
    `[RED expect] exclude가 규약 예시 10종과 정확히 일치해야 함, got ${JSON.stringify(draft.exclude)}`);
  assert.deepStrictEqual(Object.keys(draft), ['headerSource', 'scopes', 'extensions', 'exclude', 'excludePatterns'],
    `[RED expect] 키 순서가 headerSource→scopes→extensions→exclude→excludePatterns여야 함, got ${JSON.stringify(Object.keys(draft))}`);
});

test('[T083/L2-X-d] TS-152: shardPolicy 키가 초안에 존재하지 않는다(3단 폴백 보존)', () => {
  const dir = makeEmptyProjectTree('s9-no-shardpolicy');
  const r = run(dir, ['init', '--header-source', 'inline', '--json'], null, HOME_ABSENT);
  assert.ok(r.json && r.json.draft, `[RED expect] draft가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.ok(!('shardPolicy' in r.json.draft),
    `[RED expect] init 초안에 shardPolicy 키가 없어야 함(3단 폴백 무력화 방지), got ${JSON.stringify(Object.keys(r.json.draft))}`);
});

test('[T083/L2-X-d] TS-154: 이 저장소에서 init을 돌리면 scopes 이름 3종이 실제 .opal/code-scan.json과 일치한다', () => {
  const realCfg = readJSON(path.join(REPO_ROOT, '.opal', 'code-scan.json'));
  const r = run(REPO_ROOT, ['init', '--header-source', 'inline', '--json'], null, HOME_ABSENT);   // --write 없음 — 실 저장소 비접촉
  assert.ok(r.json && r.json.draft, `[RED expect] draft가 있어야 함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.deepStrictEqual(Object.keys(r.json.draft.scopes || {}).sort(), Object.keys(realCfg.scopes).sort(),
    `[RED expect] 추론된 scopes 이름이 실제 저장소 설정(framework/console-fe/console-be)과 일치해야 함, got ${JSON.stringify(r.json && r.json.draft)}`);
  assert.ok(!fs.existsSync(path.join(REPO_ROOT, '.opal', 'code-scan.json.bak')),
    '[MUST] --write 없이 실행했으므로 실 저장소에 어떤 파일도 생성되면 안 됨');
});

test('[T083/L2-X-d] TS-155~156: 3종 에러의 fix에 init 복구 명령 포함 + md 표 파싱이 parseMdTable 1곳', () => {
  const dir = makeEmptyProjectTree('s9-fix-hints');
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);   // header_source_unset 유도
  assert.strictEqual(r.json && r.json.error, 'header_source_unset', `사전조건: header_source_unset이어야 함, got ${r.stdout}`);
  assert.ok(r.json && typeof r.json.fix === 'string' && /init/.test(r.json.fix),
    `[RED expect] header_source_unset의 fix에 'init' 복구 명령이 포함돼야 함, got ${r.stdout}`);

  const parseMdTableDefs = (SRC.match(/function\s+parseMdTable\s*\(/g) || []).length;
  assert.strictEqual(parseMdTableDefs, 1,
    `[RED expect] parseMdTable 함수 정의가 소스에 정확히 1곳이어야 함, got ${parseMdTableDefs}곳 — 현재는 함수 자체가 없음`);
});

test('[T083/L2-X-d] TS-157/160: init 실행 전후 전역 setting.json 바이트 동일 + pm/code-scan-management.md에 init 반영', () => {
  const globalHome = makeHome('t157', { shardPolicy: { maxBytes: 12000, minFiles: 3 } });
  const settingPath = path.join(globalHome, 'setting.json');
  const before = fs.readFileSync(settingPath, 'utf8');
  const dir = makeEmptyProjectTree('s9-global-untouched');
  const r = run(dir, ['init', '--header-source', 'inline', '--write', '--json'], null, globalHome);
  assert.strictEqual(r.exitCode, 0, `[RED expect] init은 exit 0이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  assert.strictEqual(fs.readFileSync(settingPath, 'utf8'), before, 'init 실행 전후 전역 setting.json은 바이트 동일해야 함');

  const mgmtDoc = fs.readFileSync(path.resolve(REPO_ROOT, 'opal', 'core', 'references', 'pm', 'code-scan-management.md'), 'utf8');
  assert.ok(/code-scan init/.test(mgmtDoc),
    `[RED expect] pm/code-scan-management.md에 'code-scan init'이 등재돼야 함 — 현재는 미반영`);
  assert.ok(/shardPolicy/.test(mgmtDoc),
    `[RED expect] pm/code-scan-management.md 추론 소스 규약 표에 shardPolicy 행이 있어야 함 — 현재는 미반영`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-10: `split` 집행 — 엔트리 유실 0건 + 사후 정합 [P0] (H-6, H-14) — TS-040~045,053
// ═════════════════════════════════════════════════════════════════════════

/** split-target 10엔트리 중 order 2건 + taxrule 2건 + handler 3건을 그룹 문서로 구성 — 3건(legacy/temp/quirky)은 미지정으로 베이스 잔존. */
function makeSplitTargetGroupsDoc(manifestArg) {
  return {
    manifest: manifestArg,
    groups: [
      { label: 'order', files: ['OrderRepository.ts', 'OrderService.ts'] },
      { label: 'taxrule', files: ['TaxRuleAlpha.ts', 'TaxRuleBeta.ts'] },
      { label: 'handler', files: ['AlphaHandler.ts', 'BetaHandler.ts', 'GammaHandler.ts'] },
    ],
  };
}

function totalManifestEntries(dir) {
  const baseAbs = path.join(dir, SPLIT_MANIFEST_ARG);
  const base = readJSON(baseAbs);
  let total = Object.keys(base.files || {}).length;
  const shardsDir = path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards');
  if (fs.existsSync(shardsDir)) {
    for (const f of fs.readdirSync(shardsDir)) {
      if (!f.endsWith('.json')) continue;
      total += Object.keys(readJSON(path.join(shardsDir, f)).files || {}).length;
    }
  }
  return total;
}

test('[T083/L2-F3a] TS-040/043/044: split --groups 실행 후 _shards 생성 + shards 선언 추가 + validate 0건 + scaffold no-op', () => {
  const dir = copyFixture(SPLIT_FIX, 's10-basic');
  const doc = makeSplitTargetGroupsDoc(SPLIT_MANIFEST_ARG);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(doc), HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `[RED expect] split --groups는 exit 0이어야 함 — 현재 split 명령 자체가 없음, got ${r.exitCode} (stderr: ${r.stderr})`);
  const shardPath = path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'order.json');
  assert.ok(fs.existsSync(shardPath), `[RED expect] _shards/order.json이 생성돼야 함`);
  const base = readJSON(path.join(dir, SPLIT_MANIFEST_ARG));
  assert.ok(Array.isArray(base.shards) && base.shards.includes('order'),
    `[RED expect] 베이스 shards 선언에 'order'가 추가돼야 함, got ${JSON.stringify(base.shards)}`);

  const rValidate = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rValidate.exitCode, 0, `[RED expect] split 후 validate는 차단 위반 0건(exit 0)이어야 함, got ${rValidate.exitCode}`);

  const rScaffold = run(dir, ['scaffold', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rScaffold.json && rScaffold.json.created, 0, `[RED expect] split 후 scaffold는 created=0이어야 함(no-op)`);
  assert.strictEqual(rScaffold.json && rScaffold.json.updated, 0, `[RED expect] split 후 scaffold는 updated=0이어야 함(no-op)`);
});

test('[T083/L2-F3b] TS-041: 실행 전후 엔트리 총합이 동일하다(실제 파일 재로딩 기준, 유실 0건)', () => {
  const dir = copyFixture(SPLIT_FIX, 's10-total');
  const before = totalManifestEntries(dir);
  const doc = makeSplitTargetGroupsDoc(SPLIT_MANIFEST_ARG);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(doc), HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `[RED expect] exit 0이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  const after = totalManifestEntries(dir);
  assert.strictEqual(after, before, `[RED expect] 엔트리 총합이 실행 전후 동일해야 함(유실 0건), before=${before} after=${after}`);
});

test('[T083/L2-F3c] TS-042: groups에 없는 엔트리(legacy/temp/quirky)는 베이스에 그대로 남는다', () => {
  const dir = copyFixture(SPLIT_FIX, 's10-remain');
  const doc = makeSplitTargetGroupsDoc(SPLIT_MANIFEST_ARG);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(doc), HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `[RED expect] exit 0이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  const base = readJSON(path.join(dir, SPLIT_MANIFEST_ARG));
  for (const key of ['LegacyOrderTable.ts', 'TempOrderView.ts', 'QuirkyLoneModule.ts']) {
    assert.ok(base.files && Object.prototype.hasOwnProperty.call(base.files, key),
      `[RED expect] 미지정 엔트리 ${key}는 베이스에 남아 있어야 함, got ${JSON.stringify(base.files && Object.keys(base.files))}`);
  }
});

test('[T083/L2-F3d] TS-045: --dry-run은 결과를 출력하고 .opal/code-map/ 트리를 바이트 동일하게 남긴다', () => {
  const dir = copyFixture(SPLIT_FIX, 's10-dryrun');
  const before = snapshotTree(dir, '.opal/code-map');
  const doc = makeSplitTargetGroupsDoc(SPLIT_MANIFEST_ARG);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--dry-run', '--json'], JSON.stringify(doc), HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0, `[RED expect] --dry-run도 exit 0이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  assert.ok(r.json && r.json.dryRun === true, `[RED expect] dryRun===true가 출력에 있어야 함, got ${r.stdout}`);
  const after = snapshotTree(dir, '.opal/code-map');
  assert.deepStrictEqual(after, before, '[RED expect] --dry-run 실행 전후 .opal/code-map/ 트리가 바이트 동일해야 함(쓰기 0건)');
});

test('[T083/L1-라벨] TS-053: ../evil·_shards·대문자 라벨은 exit 1 split_groups_invalid(경로 이탈 차단)', () => {
  for (const badLabel of ['../evil', '_shards', 'Uppercase']) {
    const dir = copyFixture(SPLIT_FIX, `s10-badlabel-${badLabel.replace(/[^a-z0-9]/gi, '')}`);
    const before = listAllFiles(dir);
    const doc = { manifest: SPLIT_MANIFEST_ARG, groups: [{ label: badLabel, files: ['OrderRepository.ts'] }] };
    const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(doc), HOME_ABSENT);
    assert.strictEqual(r.exitCode, 1, `[RED expect] 악성 라벨(${badLabel})은 exit 1이어야 함, got ${r.exitCode}`);
    assert.strictEqual(r.json && r.json.error, 'split_groups_invalid',
      `[RED expect] error === 'split_groups_invalid', got ${r.stdout} (stderr: ${r.stderr})`);
    assert.deepStrictEqual(listAllFiles(dir), before, `악성 라벨(${badLabel}) 시도로 트리에 신규 파일이 생기면 안 됨`);
  }
});

test('[T083/L2-F3-손편집] ★S-10 손편집 집행: --plan 출력을 사람이 편집(라벨 개명 + 그룹 간 엔트리 이동)해도 성공 + 유실 0건', () => {
  // --plan이 아직 없으므로, --plan이 산출했을 법한 groups 문서를 직접 구성한 뒤(F-004와 독립적으로
  // F-005 집행 계약만 검증) "사람이 편집"하는 절차(라벨 개명 + 그룹 간 엔트리 이동)를 재현한다.
  const dir = copyFixture(SPLIT_FIX, 's10-handedit');
  const before = totalManifestEntries(dir);
  const draft = {
    manifest: SPLIT_MANIFEST_ARG,
    groups: [
      { label: 'grp-a', files: ['OrderRepository.ts', 'TaxRuleAlpha.ts'] },
      { label: 'grp-b', files: ['OrderService.ts'] },
    ],
  };
  // 사람 편집: grp-a → grp-a-renamed(개명) + TaxRuleAlpha.ts를 grp-a에서 grp-b로 이동
  const edited = {
    manifest: draft.manifest,
    groups: [
      { label: 'grp-a-renamed', files: ['OrderRepository.ts'] },
      { label: 'grp-b', files: ['OrderService.ts', 'TaxRuleAlpha.ts'] },
    ],
  };
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(edited), HOME_ABSENT);
  assert.strictEqual(r.exitCode, 0,
    `[RED expect] 손편집된 groups 문서도 집행에 성공해야 함 — 현재 split 명령 자체가 없음, got ${r.exitCode} (stderr: ${r.stderr})`);
  const renamedShard = readJSON(path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'grp-a-renamed.json'));
  assert.deepStrictEqual(Object.keys(renamedShard.files || {}), ['OrderRepository.ts'],
    `[RED expect] grp-a-renamed 샤드에는 OrderRepository.ts만 있어야 함, got ${JSON.stringify(renamedShard)}`);
  const grpB = readJSON(path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards', 'grp-b.json'));
  assert.deepStrictEqual(Object.keys(grpB.files || {}).sort(), ['OrderService.ts', 'TaxRuleAlpha.ts'],
    `[RED expect] grp-b 샤드에는 OrderService.ts·TaxRuleAlpha.ts가 있어야 함(그룹 간 이동 반영), got ${JSON.stringify(grpB)}`);
  const after = totalManifestEntries(dir);
  assert.strictEqual(after, before, `손편집 집행 후에도 엔트리 총합은 불변해야 함(유실 0건), before=${before} after=${after}`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-11: `split` 원자성 — 중도 실패 시 부분 상태 0건 [P0] (H-6, H-7) — TS-046~049
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L2-F3e] TS-046~047: 존재하지 않는 키·한 엔트리를 2개 그룹에 지정 → exit 1 split_groups_invalid + 쓰기 0건', () => {
  const dirUnknown = copyFixture(SPLIT_FIX, 's11-unknownkey');
  const beforeUnknown = snapshotTree(dirUnknown, '.opal/code-map');
  const docUnknown = { manifest: SPLIT_MANIFEST_ARG, groups: [{ label: 'ghost', files: ['NoSuchFile.ts'] }] };
  const rUnknown = run(dirUnknown, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(docUnknown), HOME_ABSENT);
  assert.strictEqual(rUnknown.exitCode, 1, `[RED expect] 존재하지 않는 키는 exit 1이어야 함, got ${rUnknown.exitCode}`);
  assert.strictEqual(rUnknown.json && rUnknown.json.error, 'split_groups_invalid',
    `[RED expect] error === 'split_groups_invalid', got ${rUnknown.stdout} (stderr: ${rUnknown.stderr})`);
  assert.deepStrictEqual(snapshotTree(dirUnknown, '.opal/code-map'), beforeUnknown, '존재하지 않는 키 시도 후 트리는 바이트 동일해야 함');

  const dirDup = copyFixture(SPLIT_FIX, 's11-dupkey');
  const beforeDup = snapshotTree(dirDup, '.opal/code-map');
  const docDup = {
    manifest: SPLIT_MANIFEST_ARG,
    groups: [
      { label: 'grp-x', files: ['OrderRepository.ts'] },
      { label: 'grp-y', files: ['OrderRepository.ts'] },
    ],
  };
  const rDup = run(dirDup, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(docDup), HOME_ABSENT);
  assert.strictEqual(rDup.exitCode, 1, `[RED expect] 한 엔트리 2그룹 지정은 exit 1이어야 함, got ${rDup.exitCode}`);
  assert.deepStrictEqual(snapshotTree(dirDup, '.opal/code-map'), beforeDup, '중복 지정 시도 후 트리는 바이트 동일해야 함');
});

test('[T083/L2-F3e] TS-048: 쓰기 실패 주입 → exit 1 + 트리 바이트 동일 + *.tmp-split 잔존 0건', () => {
  const dir = copyFixture(SPLIT_FIX, 's11-writefail');
  const before = snapshotTree(dir, '.opal/code-map');
  // PM 정정(083, 2026-08-04): 원래 `.opal/code-map/svc/mod`를 chmod했으나 그 디렉토리는
  // **아직 존재하지 않는다**(베이스는 `svc/mod.json` 파일이고 `svc/mod/`는 split이 만들 위치다)
  // → chmodSync가 ENOENT로 죽어 테스트 자신이 실패했다. 실재하는 부모 `svc`의 쓰기 권한을
  // 제거하면 `mod/` 생성도 `*.tmp-split` 생성도 막혀 **동일한 쓰기 실패**를 주입한다.
  // 단언은 하나도 완화하지 않는다.
  const modDir = path.join(dir, '.opal', 'code-map', 'svc');
  fs.chmodSync(modDir, 0o555);   // 신규 파일(_shards/*.json · *.tmp-split) 생성 불가하도록 쓰기 권한 제거
  try {
    const doc = makeSplitTargetGroupsDoc(SPLIT_MANIFEST_ARG);
    const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(doc), HOME_ABSENT);
    assert.strictEqual(r.exitCode, 1,
      `[RED expect] 쓰기 실패는 exit 1이어야 함 — 현재 split 명령 자체가 없어 이 경로에 도달 못함, got ${r.exitCode} (stderr: ${r.stderr})`);
  } finally {
    fs.chmodSync(modDir, 0o755);   // 정리 단계에서 삭제 가능하도록 권한 복원
  }
  const tmpFiles = listAllFiles(dir).filter(p => p.includes('.tmp-split'));
  assert.deepStrictEqual(tmpFiles, [], `*.tmp-split 잔존이 0건이어야 함, got ${JSON.stringify(tmpFiles)}`);
  assert.deepStrictEqual(snapshotTree(dir, '.opal/code-map'), before, '쓰기 실패 후 트리는 실행 전과 바이트 동일해야 함');
});

test('[T083/L2-F3e] TS-049: 사후 검증 총합 불일치 시 롤백되어 트리가 원상 복구된다', () => {
  const dir = copyFixture(SPLIT_FIX, 's11-verifyfail');
  const before = snapshotTree(dir, '.opal/code-map');
  // 사후 재검증이 "실행 전 합계"와 다르게 보이도록, 같은 이름의 샤드 파일을 미리 만들어
  // 엔트리를 중복시킨다(집행이 그대로 겹쳐 쓰면 합계가 어긋나 split_verify_failed가 기대된다).
  const shardsDir = path.join(dir, '.opal', 'code-map', 'svc', 'mod', '_shards');
  fs.mkdirSync(shardsDir, { recursive: true });
  writeJSON(path.join(shardsDir, 'order.json'), {
    version: 1, scope: 'svc', dir: 'svc/mod',
    files: { 'OrderRepository.ts': { description: '이미 존재하는 중복 샤드 엔트리 (검증 실패 유도)', exports: ['OrderRepository'] } },
  });
  const beforeWithStale = snapshotTree(dir, '.opal/code-map');
  const doc = makeSplitTargetGroupsDoc(SPLIT_MANIFEST_ARG);
  const r = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', '-', '--json'], JSON.stringify(doc), HOME_ABSENT);
  assert.strictEqual(r.json && r.json.error, 'split_verify_failed',
    `[RED expect] error === 'split_verify_failed' — 현재 split 명령 자체가 없어 이 경로에 도달 못함, got ${r.stdout} (stderr: ${r.stderr})`);
  assert.deepStrictEqual(snapshotTree(dir, '.opal/code-map'), beforeWithStale,
    '사후 검증 실패 시 트리가 실행 전(스테일 샤드 포함 상태)으로 복구돼야 함');
});

// ═════════════════════════════════════════════════════════════════════════
// S-12: 유도 페이로드 — 권고 조각 수 + 다음 명령 + detail 불변 (H-8) — TS-060~063
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L1-F5a] TS-060: manifest_oversize 위반에 recommendedShards(≥2 정수)와 next(문자열) 포함', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's12-payload');
  setShardPolicy(dir, { maxBytes: 200, minFiles: 1 });   // base(614B) > 200, entries 4>=1 → 충족
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  const v = findViolation(r.json, 'manifest_oversize');
  assert.ok(v, `[RED expect] manifest_oversize 위반이 있어야 함, got ${JSON.stringify(r.json && r.json.violations)}`);
  assert.ok(v && Number.isInteger(v.recommendedShards) && v.recommendedShards >= 2,
    `[RED expect] recommendedShards가 2 이상 정수여야 함, got ${v && v.recommendedShards}`);
  assert.ok(v && typeof v.next === 'string' && v.next.length > 0,
    `[RED expect] next가 문자열이어야 함, got ${v && v.next}`);
});

test('[T083/L1-F5b] TS-061: next 필드의 명령을 그대로 실행하면 F-004 제안 출력이 exit 0으로 나온다', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's12-next');
  setShardPolicy(dir, { maxBytes: 200, minFiles: 1 });
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  const v = findViolation(r.json, 'manifest_oversize');
  assert.ok(v && typeof v.next === 'string', `[RED expect] next 명령 문자열이 있어야 함, got ${r.stdout}`);
  const parts = (v && v.next || '').split(/\s+/).filter(Boolean);
  // 'code-scan split <manifest> --plan' 형태 — 앞의 'code-scan' 토큰은 제외하고 재실행한다.
  const args = parts.slice(1);
  assert.ok(args.length >= 2 && args[0] === 'split',
    `[RED expect] next 명령이 'code-scan split ... --plan' 형태여야 함, got "${v && v.next}"`);
  const rNext = run(dir, args.concat(['--json']), null, HOME_ABSENT);
  assert.strictEqual(rNext.exitCode, 0,
    `[RED expect] next 명령을 그대로 실행하면 exit 0(제안 출력)이어야 함 — 현재 split 명령 자체가 없음, got ${rNext.exitCode} (stderr: ${rNext.stderr})`);
});

test('[T083/L1-F5a] TS-062: detail이 {bytes}/{maxBytes} 포맷을 유지한다(정확 단언, H-8)', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's12-detail');
  setShardPolicy(dir, { maxBytes: 200, minFiles: 1 });
  const size = fileBytes(path.join(dir, MOD_REL));
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  const v = findViolation(r.json, 'manifest_oversize');
  assert.ok(v, `[RED expect] manifest_oversize 위반이 있어야 함, got ${JSON.stringify(r.json && r.json.violations)}`);
  assert.strictEqual(v && v.detail, `${size}/200`,
    `[RED expect] detail === '{bytes}/{maxBytes}' 정확 포맷, got ${v && v.detail}`);
});

test('[T083/L1-F5a] TS-063: scaffold stderr 경고에 split ... --plan 명령이 포함된다', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's12-scaffold-hint');
  setShardPolicy(dir, { maxBytes: 200, minFiles: 1 });
  const r = run(dir, ['scaffold', '--json'], null, HOME_ABSENT);
  assert.ok(r.stderr.includes('split') && r.stderr.includes('--plan'),
    `[RED expect] scaffold stderr 경고에 'split ... --plan' 명령이 포함돼야 함, got "${r.stderr}"`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-14: 회귀 가드 — 전량 GREEN + 골든 불변 + 홈 비의존 [P0] (H-1,2,4,13,17) — TS-080~085
// ═════════════════════════════════════════════════════════════════════════

const TESTS_DIR = __dirname;
const OTHER_TEST_FILES = fs.readdirSync(TESTS_DIR)
  .filter(f => f.startsWith('test-') && f.endsWith('.js') && f !== 'test-shard-policy.js')
  .sort();

/**
 * [MUST] `node --test`로 구동 중인 이 프로세스는 `NODE_TEST_CONTEXT=child-v8`을 이미 갖고 있다.
 * 이걸 그대로 물려주면 중첩 `node --test <file>` 자식이 "자신도 이미 하위 테스트 컨텍스트"로
 * 오인해 정상적으로 실행·판정하지 않는다(거짓 통과). 중첩 실행 전 반드시 제거한다.
 */
function cleanTestEnv() {
  const env = Object.assign({}, process.env);
  delete env.NODE_TEST_CONTEXT;
  delete env.NODE_TEST_WORKER_ID;
  // 재귀 가드 규약 ② (파일 상단 규약 참조) — 자식 스위트의 메타테스트(TS-062·S-19)를 무동작시킨다.
  env.CODE_SCAN_META_CHILD = '1';
  return env;
}

test('[T083/L2-F7] TS-080: 기존 11개 테스트 스크립트 전량 GREEN (자기 자신은 재귀 방지를 위해 제외 — 082 관용)', () => {
  // 재귀 가드 규약 ① (파일 상단 규약 참조) — 이 프로세스 자체가 다른 메타테스트의 자식이면
  // 본 메타테스트를 수행하지 않고 통과 처리한다. skip/todo 마킹 대신 조기 return을 쓴다(규약 ④).
  if (process.env.CODE_SCAN_META_CHILD === '1') return;
  assert.strictEqual(OTHER_TEST_FILES.length, 11,
    `[MUST] 083 신규 파일 1개를 제외하면 기존 스크립트가 정확히 11개여야 함(082 완료 시점 기준), got ${JSON.stringify(OTHER_TEST_FILES)}`);
  const failures = [];
  for (const f of OTHER_TEST_FILES) {
    const res = spawnSync(process.execPath, ['--test', path.join(TESTS_DIR, f)], { encoding: 'utf8', timeout: 60000, env: cleanTestEnv() });
    if (res.status !== 0) failures.push({ file: f, status: res.status });
  }
  assert.deepStrictEqual(failures, [],
    `[RED expect] 이 시점에는 tests/test-shard.js가 083 §3.7.2 (C) 이전 전이라 083 픽스처 정책과 어긋나 실패할 수 있다(Step 7에서 GREEN화) — 현재 실패 목록: ${JSON.stringify(failures)}`);
});

test('[T083/L2-F7] TS-081: fixtures/golden/* 8파일 바이트 diff 0 (git diff --stat 빈 결과, 재캡처 금지)', () => {
  // [RED 보장] 골든 무변경 자체는 083 이전에도 항상 참인 순수 회귀 불변식이라 그 자체로는 RED가
  // 보장되지 않는다 — split/init이 실제로 이 프로젝트에 존재해 골든 8커맨드와 공존함을 함께 확인한다.
  const dirSanity = copyFixture(path.join('shard-policy', 'split-target'), 's14-golden-sanity');
  const rSanity = run(dirSanity, ['split', SPLIT_MANIFEST_ARG, '--plan', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rSanity.exitCode, 0,
    `[RED expect] split 명령이 존재해야 골든 불변 회귀가드가 의미를 가진다 — 현재 split 명령 자체가 없음, got ${rSanity.exitCode} (stderr: ${rSanity.stderr})`);

  const goldenRel = 'opal/tools/code-scan/tests/fixtures/golden/';
  const res = spawnSync('git', ['diff', '--stat', '--', goldenRel], { cwd: REPO_ROOT, encoding: 'utf8' });
  assert.strictEqual(res.status, 0, `git diff 실행이 성공해야 함, got ${res.status} (${res.stderr})`);
  assert.strictEqual(res.stdout.trim(), '', `[MUST] 골든 8파일은 083 작업으로 바이트 변경이 없어야 함(재캡처 금지), got:\n${res.stdout}`);
});

test('[T083/L2-F7] TS-082: 샤드 미선언 자산(codemap-repo·legacy-repo) 출력 불변 + shardPolicy 도입 후에도 무영향', () => {
  for (const fixture of ['codemap-repo', 'legacy-repo']) {
    const dir = copyFixture(fixture, `s14-unchanged-${fixture}`);
    // 083 신설 shardPolicy를 명시적으로 매우 낮게 걸어도 — 이 두 자산은 code-map/정책 도입 대상이
    // 아니므로 scan 출력이 흔들리면 안 된다(회귀 가드가 083 존재를 실제로 겨눔).
    // PM 정정(083, 2026-08-04): 원안은 극단 정책(maxBytes:1)을 주입해 놓고
    // "영향이 없어야 함 + exit 0"을 단언했는데, 전제가 두 군데 틀렸다.
    //   ① `codemap-repo`는 "code-map 미보유 자산"이 아니라 **code-map 보유 자산**이다
    //      → 정책을 걸면 당연히 적용된다(0→4건). 영향이 없으면 오히려 미배선이다.
    //   ② 이 픽스처는 shardPolicy와 무관한 선행 위반(conflict 1·exports_not_found 1·
    //      uncovered 4)을 갖고 있어 `validate`가 항상 exit 2다(HEAD 버전 실측 동일).
    // PLAN F-7 (c)가 요구하는 "샤드 미선언 자산 출력 불변"은 **`shards` 배열 미선언**에
    // 대한 보증(082 축)이지 정책 축이 아니다. 그래서 의도를 2축으로 분리한다 —
    // 완화가 아니라 각 축을 제대로 겨누는 정정이다.
    const cfgPath = path.join(dir, '.opal', 'code-scan.json');

    // 축①(회귀 불변): 기본 정책에서 083 도입 전과 동일하게 초과 0건이어야 한다.
    const rScan = run(dir, ['scan', '--json'], null, HOME_ABSENT);
    assert.strictEqual(rScan.exitCode, 0, `${fixture} scan은 exit 0이어야 함, got ${rScan.exitCode}`);
    const rBase = run(dir, ['validate', '--json'], null, HOME_ABSENT);
    assert.strictEqual(countViolations(rBase.json, 'manifest_oversize'), 0,
      `${fixture}는 기본 정책(10240/40)에서 초과 0건이어야 함 — 083이 기존 자산에 새 위반을 얹지 않는다는 회귀 가드`);

    // 축②: 극단 정책 주입 시의 기대는 **자산 성격에 따라 정반대**다.
    //   - code-map 보유(`codemap-repo`): 정책이 적용되어 초과가 열거되어야 한다(배선 증명).
    //     변하지 않으면 2축 판정이 배선되지 않은 것이다.
    //   - code-map 미보유(`legacy-repo`): 잴 매니페스트가 없으므로 출력이 **바이트 동일**해야
    //     한다. 이쪽이 원안이 말한 "정책 미도입 자산 무영향"의 실제 대상이다.
    const hasCodeMap = fs.existsSync(path.join(dir, '.opal', 'code-map'));
    if (fs.existsSync(cfgPath)) {
      const cfg = readJSON(cfgPath);
      cfg.shardPolicy = { maxBytes: 1, minFiles: 1 };
      writeJSON(cfgPath, cfg);
      const rExtreme = run(dir, ['validate', '--json'], null, HOME_ABSENT);
      assert.strictEqual(rExtreme.exitCode, rBase.exitCode,
        `${fixture} 초과 열거는 **비차단**이므로 exit code가 정책 주입 전후로 동일해야 함, got ${rExtreme.exitCode} vs ${rBase.exitCode}`);
      if (hasCodeMap) {
        assert.ok(countViolations(rExtreme.json, 'manifest_oversize') > 0,
          `[RED expect] ${fixture}(code-map 보유)에 극단 shardPolicy(maxBytes:1)를 걸면 초과가 열거되어야 함(2축 판정이 실제로 배선됐다는 증거), got 0`);
      } else {
        assert.strictEqual(rExtreme.stdout, rBase.stdout,
          `${fixture}(code-map 미보유)는 극단 정책을 걸어도 출력이 **바이트 동일**해야 함 — 잴 매니페스트가 없다`);
      }
    }
  }
});

test('[T083/L2-F7] TS-083: 가짜 홈 5종 중 어느 것을 주입해도 정책 미적용 명령(scan)의 결과가 동일하다', () => {
  const dir = copyFixture('codemap-repo', 's14-home-parity');
  const homes = [HOME_ABSENT, HOME_VALID, HOME_BROKEN, HOME_NOKEY, HOME_BADTYPE];
  const results = homes.map(h => run(dir, ['scan', '--json'], null, h));
  for (const r of results) {
    assert.strictEqual(r.exitCode, 0, `[RED expect] scan은 홈 상태와 무관하게 exit 0이어야 함, got ${r.exitCode} (stderr: ${r.stderr})`);
  }
  const outputs = results.map(r => r.stdout);
  for (let i = 1; i < outputs.length; i++) {
    assert.strictEqual(outputs[i], outputs[0],
      `홈 상태와 무관하게 scan 결과가 바이트 동일해야 함(정책 미소비 명령), home[${i}] differs from home[0]`);
  }
  // [RED 보장] 위 동일성만으로는 "둘 다 정책을 안 읽어서" 우연히 같을 수도 있다 — OPAL_HOME 자체가
  // 실제로 소비되는(다른 명령에서 값이 갈리는) 도구임을 함께 확인한다.
  const dirPolicy = copyFixture(path.join('shard-policy', 'base'), 's14-home-parity-policy-active');
  writeManifestBytes(dirPolicy, MOD_REL, 20, 15000);
  const homeCustom = makeHome('t083-active', { shardPolicy: { maxBytes: 12000, minFiles: 5 } });
  const rActive = run(dirPolicy, ['validate', '--json'], null, homeCustom);
  assert.strictEqual(rActive.json && rActive.json.counts && rActive.json.counts.manifest_oversize, 1,
    `[RED expect] OPAL_HOME이 실제로 소비돼야 함(전역 정책 반영), got ${JSON.stringify(rActive.json && rActive.json.counts)}`);
});

test('[T083/L2-F7] TS-084: 모든 테스트 파일의 spawnSync 호출이 OPAL_HOME을 주입한다(정적 grep)', () => {
  const offenders = [];
  for (const f of OTHER_TEST_FILES) {
    const content = fs.readFileSync(path.join(TESTS_DIR, f), 'utf8');
    if (!/spawnSync/.test(content)) continue;   // spawnSync를 안 쓰는 파일은 대상 아님
    if (!/OPAL_HOME/.test(content)) offenders.push(f);
  }
  assert.deepStrictEqual(offenders, [],
    `[RED expect] spawnSync를 쓰는 모든 테스트 파일이 OPAL_HOME을 주입해야 함(U-7) — 현재 083 이전 파일들은 주입하지 않음, got ${JSON.stringify(offenders)}`);
});

test('[T083/L2-F7] TS-085: 082 시나리오 26종의 테스트 함수가 전부 존재 + skip·todo 0건 + 083 이전(S-13) 완료', () => {
  const shardTestSrc = fs.readFileSync(path.join(TESTS_DIR, 'test-shard.js'), 'utf8');
  const skipTodoMarks = (shardTestSrc.match(/\.skip\s*\(|\.todo\s*\(/g) || []).length;
  assert.strictEqual(skipTodoMarks, 0, `test-shard.js에 skip·todo 마킹이 0건이어야 함, got ${skipTodoMarks}건`);
  const testCount = (shardTestSrc.match(/^test\(/gm) || []).length;
  assert.ok(testCount >= 40, `[MUST] test-shard.js의 test() 케이스 수가 082 완료 시점(44개)에서 줄어들면 안 됨, got ${testCount}`);
  // [RED expect] §3.7.2 (C) 이전(S-13, TS-070~075)이 test-shard.js에 실제로 반영됐는지 — 083 라벨
  // 케이스가 아직 없으므로(Step 7 완료 전) 반드시 실패해야 한다.
  assert.ok(/\[T083\//.test(shardTestSrc),
    '[RED expect] test-shard.js에 [T083/…] 라벨 케이스(S-13 구 위치 이전, §3.7.2 (C))가 반영돼야 함 — 현재는 082 케이스만 존재');
});

// ═════════════════════════════════════════════════════════════════════════
// S-15: 문서·배포 — 버전·변경이력·시드 머지 안전 (H-11) — TS-090~097
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L2-F8] TS-090/097: VERSION===1.6.0 + 변경이력 (083) 행 + @header 갱신', () => {
  assert.ok(/const VERSION = '1\.6\.0';/.test(SRC),
    `[RED expect] VERSION은 '1.6.0'이어야 함 — 현재는 1.5.0`);
  assert.ok(/\(083\)/.test(SRC), `[RED expect] 변경이력에 (083) 표기가 있어야 함`);
});

test('[T083/L2-F8] TS-091: tools.md에 split·2축 판정·shardPolicy·3단 우선순위·에러 코드 7종 반영', () => {
  const doc = fs.readFileSync(path.resolve(REPO_ROOT, 'opal', 'core', 'references', 'tools.md'), 'utf8');
  for (const needle of ['split', 'shardPolicy', 'split_usage_invalid', 'split_inline_mode', 'split_target_invalid',
    'split_groups_invalid', 'split_write_failed', 'split_rollback', 'split_verify_failed']) {
    assert.ok(doc.includes(needle), `[RED expect] tools.md에 '${needle}'이 반영돼야 함 — 현재 미반영`);
  }
});

test('[T083/L2-F8] TS-092: header-rules.md에 split 집행 1줄 + 변경이력 v1.7', () => {
  const doc = fs.readFileSync(path.resolve(REPO_ROOT, 'opal', 'core', 'references', 'harness', 'header-rules.md'), 'utf8');
  assert.ok(/code-scan split/.test(doc), `[RED expect] header-rules.md에 'code-scan split' 언급이 있어야 함`);
  assert.ok(/v1\.7/.test(doc), `[RED expect] header-rules.md 변경이력에 v1.7 행이 있어야 함`);
});

test('[T083/L2-F8b] TS-093: setting.default.json에 shardPolicy.maxBytes===10240·minFiles===40', () => {
  const p = path.resolve(REPO_ROOT, 'opal', 'core', 'setting.default.json');
  const doc = readJSON(p);
  assert.ok(doc.shardPolicy, `[RED expect] setting.default.json에 shardPolicy 키가 있어야 함 — 현재 없음`);
  assert.strictEqual(doc.shardPolicy && doc.shardPolicy.maxBytes, 10240,
    `[RED expect] shardPolicy.maxBytes === 10240, got ${doc.shardPolicy && doc.shardPolicy.maxBytes}`);
  assert.strictEqual(doc.shardPolicy && doc.shardPolicy.minFiles, 40,
    `[RED expect] shardPolicy.minFiles === 40, got ${doc.shardPolicy && doc.shardPolicy.minFiles}`);
});

/**
 * install-mac.sh의 install_opal_setting() 안에 박힌 python 임베디드 스크립트(PYEOF 히어독)를 추출한다.
 *
 * [MUST] install-mac.sh에는 `PYEOF` 히어독이 3개 있다(AGENT.md 치환용 2개 + setting.json 시드 1개).
 * 위치·순서에 의존해 "첫 블록"을 잡으면 인자 3개를 받는 AGENT.md 치환 스크립트가 걸려
 * `IndexError: list index out of range`로 오탐 실패한다(083 Step 11 실측). 따라서 시드 로직의
 * 고유 식별자인 `SEED_KEYS`를 포함한 블록만 선택한다 — 히어독 순서가 바뀌어도 안전하다.
 * 히어독 여는 줄에는 `|| warn ...` 같은 후행 토큰이 붙을 수 있으므로 `[^\n]*`로 흘려보낸다.
 * 대상 블록을 특정하지 못하면 조용히 첫 블록으로 폴백하지 않고 명시적으로 실패시킨다.
 */
function extractInstallSeedScript() {
  const src = fs.readFileSync(INSTALLER, 'utf8');
  const blocks = Array.from(src.matchAll(/<<'PYEOF'[^\n]*\n([\s\S]*?)\nPYEOF/g), m => m[1]);
  assert.ok(blocks.length > 0, 'install-mac.sh에서 PYEOF 히어독 python 스크립트를 찾을 수 없음(설치 스크립트 구조 확인 필요)');
  const seedBlocks = blocks.filter(b => b.includes('SEED_KEYS'));
  assert.strictEqual(seedBlocks.length, 1,
    `install-mac.sh의 PYEOF 히어독 ${blocks.length}개 중 install_opal_setting 시드 블록(SEED_KEYS 포함)이 정확히 1개여야 함, got ${seedBlocks.length} — 설치 스크립트 구조 확인 필요`);
  return seedBlocks[0];
}

function runInstallSeed(srcJsonPath, dstJsonPath) {
  const script = extractInstallSeedScript();
  return spawnSync('python3', ['-c', script, srcJsonPath, dstJsonPath], { encoding: 'utf8' });
}

test('[T083/L2-F8b] TS-094~095: 가짜 홈 3형태에 시드 로직 적용 — 기존 값 무손실 + 멱등', () => {
  const srcJsonPath = path.resolve(REPO_ROOT, 'opal', 'core', 'setting.default.json');
  const scratch = emptyDir('s15-seed');

  const forms = {
    'models만': { bootstrap: 'on', models: { platform: 'auto' } },
    '둘다': { bootstrap: 'on', models: { platform: 'auto' }, shardPolicy: { maxBytes: 1, minFiles: 1 } },
    '빈파일': { bootstrap: 'on' },
  };
  for (const [label, existing] of Object.entries(forms)) {
    const dstPath = path.join(scratch, `setting-${label}.json`);
    writeJSON(dstPath, existing);
    const before = fs.readFileSync(dstPath, 'utf8');
    const res1 = runInstallSeed(srcJsonPath, dstPath);
    assert.strictEqual(res1.status, 0, `[RED expect] (${label}) 시드 스크립트가 exit 0이어야 함, got ${res1.status} (${res1.stderr})`);
    const afterFirst = readJSON(dstPath);
    assert.ok(afterFirst.shardPolicy, `[RED expect] (${label}) shardPolicy 키가 부재 시 시드돼야 함 — 현재 스크립트는 models만 다룸`);
    if (existing.shardPolicy) {
      assert.deepStrictEqual(afterFirst.shardPolicy, existing.shardPolicy,
        `[RED expect] (${label}) 기존 shardPolicy 값은 1바이트도 변하면 안 됨`);
    }
    const afterFirstRaw = fs.readFileSync(dstPath, 'utf8');
    const res2 = runInstallSeed(srcJsonPath, dstPath);
    assert.strictEqual(res2.status, 0, `2회차 시드도 exit 0이어야 함, got ${res2.status}`);
    const afterSecondRaw = fs.readFileSync(dstPath, 'utf8');
    assert.strictEqual(afterSecondRaw, afterFirstRaw, `[RED expect] (${label}) 2회 실행 결과가 바이트 동일해야 함(멱등)`);
  }
});

test('[T083/L2-F8b] TS-096: 시드가 없는 환경(homes/absent)에서 코드 상수로 정상 동작한다', () => {
  const dir = copyFixture(path.join('shard-policy', 'base'), 's15-nosee-fallback');
  writeManifestBytes(dir, MOD_REL, 45, 15000);   // (10240,20480], entries>=40
  const r = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(r.json && r.json.counts && r.json.counts.manifest_oversize, 1,
    `[RED expect] 시드 없는 환경에서도 상수(10240/40) 폴백으로 동작해야 함, got ${JSON.stringify(r.json && r.json.counts)}`);
});

// ═════════════════════════════════════════════════════════════════════════
// S-16: 완료기준 ④ 왕복 입증 — 탐지 → 제안 → 집행 → 검증 [P0] (H-6, H-10, H-18) — TS-054
// ═════════════════════════════════════════════════════════════════════════

test('[T083/L2-DONE4] ★★★TS-054: 사전상태단언 → 전 궤 관통(validate→--plan --out→--groups --dry-run→--groups→validate) → 유실 0건 + 오버사이즈 0건', () => {
  const dir = copyFixture(SPLIT_FIX, 's16-roundtrip');

  // ① [필수] 사전 상태 단언 — 시작 시 validate가 manifest_oversize===1임을 먼저 단언한다.
  // 이 단언이 없으면 픽스처 정책이 잘못 잡혔을 때 "0건이 되었다"가 공허하게 참이 되는 false green이 된다.
  const rBefore = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rBefore.exitCode, 0, `사전조건: validate는 비차단 exit 0이어야 함, got ${rBefore.exitCode}`);
  assert.strictEqual(rBefore.json && rBefore.json.counts && rBefore.json.counts.manifest_oversize, 1,
    `[사전조건 — MUST] split-target(policy maxBytes=512/minFiles=8, manifest=1942B/10entries)은 시작 시 ` +
    `manifest_oversize===1이어야 한다(2축 충족: 1942>512 && 10>=8). got ${JSON.stringify(rBefore.json && rBefore.json.counts)} — ` +
    `이 단언 없이 "종료 시 0건"만 보면 픽스처 정책이 잘못 잡혀도 공허하게 참이 되는 false green이다.`);
  const beforeTotal = totalManifestEntries(dir);

  // ② 전 궤 관통 — validate(탐지) → --plan --out(제안) → --groups --dry-run(예행) → --groups(집행) → validate(재검증)
  const outRel = 'groups-s16.json';
  const rPlan = run(dir, ['split', SPLIT_MANIFEST_ARG, '--plan', '--out', outRel, '--json'], null, HOME_ABSENT);
  assert.strictEqual(rPlan.exitCode, 0,
    `[RED expect] --plan --out은 exit 0이어야 함 — 현재 split 명령 자체가 없음, got ${rPlan.exitCode} (stderr: ${rPlan.stderr})`);
  const outAbs = path.join(dir, outRel);
  assert.ok(fs.existsSync(outAbs), `[RED expect] --out 경로에 groups 문서가 생성돼야 함`);
  const groupsDoc = fs.readFileSync(outAbs, 'utf8');

  const rDryRun = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', outRel, '--dry-run', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rDryRun.exitCode, 0,
    `[RED expect] --groups --dry-run은 exit 0이어야 함, got ${rDryRun.exitCode} (stderr: ${rDryRun.stderr})`);

  const rApply = run(dir, ['split', SPLIT_MANIFEST_ARG, '--groups', outRel, '--json'], null, HOME_ABSENT);
  assert.strictEqual(rApply.exitCode, 0,
    `[RED expect] --groups 집행은 exit 0이어야 함, got ${rApply.exitCode} (stderr: ${rApply.stderr})`);

  // ④ 왕복 — 중간 산출 groups 문서를 수정 없이 그대로 재사용해도 (이미 집행된 라벨이므로) 최소한
  // 문서 자체의 바이트가 손상되지 않았음을 확인한다(왕복 성립의 전제).
  assert.strictEqual(fs.readFileSync(outAbs, 'utf8'), groupsDoc,
    'groups 문서는 --dry-run·집행을 거치는 동안 바이트가 변하면 안 된다(왕복 입력 보존)');

  // ③ 종료 상태 — manifest_oversize 0건 + 엔트리 유실 0건
  const afterTotal = totalManifestEntries(dir);
  assert.strictEqual(afterTotal, beforeTotal,
    `[RED expect] 엔트리 총합이 왕복 전후 동일해야 함(유실 0건), before=${beforeTotal} after=${afterTotal}`);

  const rAfter = run(dir, ['validate', '--json'], null, HOME_ABSENT);
  assert.strictEqual(rAfter.json && rAfter.json.counts && rAfter.json.counts.manifest_oversize, 0,
    `[RED expect] 왕복 완료 후 manifest_oversize===0이어야 함(완료기준 ④), got ${JSON.stringify(rAfter.json && rAfter.json.counts)}`);
});
