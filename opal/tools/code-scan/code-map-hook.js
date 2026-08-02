#!/usr/bin/env node
/**
 * @header {
 *   "module": "code-map-hook",
 *   "layer": "util",
 *   "domain": "code-scan",
 *   "description": "PostToolUse hook — Edit/Write/MultiEdit 이벤트에서 code-map 대상 파일의 외부 매니페스트 미갱신을 감지해 결정론 경고(additionalContext)를 주입한다. 조기 이탈 10단으로 무관한 이벤트를 걸러낸다: 전역 headerSource가 미설정·무효값이거나 inline인 트리는 ⑤단에서, code-map 미사용 프로젝트(index.json 부재)는 그 뒤 ⑥단에서 즉시 무관 판정·무출력·exit 0 (PM-7, TASK 077 / TASK 080 F-005·F-12e). 여기서 무출력은 stdout·stderr 양축 0바이트를 뜻하므로 모드 게이트가 code-map 로딩보다 반드시 앞선다. 확정 모드는 ctx.headerSource로 실려 decideTarget의 모드 직결 판정을 지배한다",
 *   "exports": ["main"],
 *   "depends": ["code-scan"],
 *   "note": "조기 이탈 10단(PLAN.md §3.9.2 (C) 9단 + 080 §3.5.2 모드 게이트 신설) + 전 경로 fail-safe(todo_mirror_hook.py:124-130 패턴 준용). 모드 게이트 ⑤는 code-map 로딩 ⑥보다 위에 놓인다 — loadCodeMap이 normalizeIndexScope를 경유해 폐기 키 안내를 stderr로 1회 발화하므로(code-scan.js:455) 게이트가 아래에 있으면 조용히 이탈해야 할 트리에서 무출력 계약이 stderr 축에서 깨진다(080 F-12e, TS-076). 이 순서 자체가 계약이며 게이트 위에서 code-map을 읽어서는 안 된다. ⑤는 전역 config 1층만 본다 — hook에는 CLI 플래그가 없으므로 code-scan.js resolveHeaderSource의 2층 병합 중 CLI 층이 구조적으로 성립하지 않는다. 미설정·무효값·설정 파싱 실패는 CLI에서 전 명령 차단(exit 1)이지만 hook은 계약상 예외이며 항상 무출력 exit 0이다. WORKER_FIELDS는 code-scan.js가 module.exports로 노출하지 않으므로 표시용으로 로컬 복제(header-standard.md §7 5필드와 동기 유지)."
 * }
 */

'use strict';

const fs = require('fs');
const path = require('path');
const {
  decideTarget,
  loadCodeMap,
  loadConfig,
  findProjectRoot,
} = require('./code-scan.js');

// PostToolUse 대상 도구 3종 — matcher(claude-hooks.json)와 이중 방어(§3.9.2 (C)②)
const TOOL_NAMES = new Set(['Edit', 'Write', 'MultiEdit']);

// 워커 작성 허용 필드 — code-scan.js WORKER_FIELDS(:45)와 동일 값을 표시용으로 로컬 유지
const WORKER_FIELDS = ['description', 'exports', 'depends', 'note', 'feature'];

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch {
    return '';
  }
}

function safeReadJson(absPath) {
  try {
    return JSON.parse(fs.readFileSync(absPath, 'utf8'));
  } catch {
    return null;
  }
}

// findProjectRoot()는 process.cwd() 기준이므로, 이를 file_path와 같은 좌표계로 비교하려면
// 둘 다 실제 경로(symlink 해소)로 정규화해야 한다 — macOS의 /tmp↔/private/tmp,
// /var↔/private/var 심볼릭 링크로 인해 두 경로가 문자열상 다른 접두를 가질 수 있다.
// 새로 생성되는 파일(Write 신규)은 실재하지 않을 수 있으므로 상위 디렉터리를 realpath한다.
function toRealAbsPath(absPath) {
  try {
    return fs.realpathSync(absPath);
  } catch {
    try {
      return path.join(fs.realpathSync(path.dirname(absPath)), path.basename(absPath));
    } catch {
      return absPath;
    }
  }
}

function buildWarning(relPath, decision) {
  const manifestLine = decision.manifest
    ? `기록 위치: ${decision.manifest} (key: "${decision.key}")`
    : '기록 위치: code-map 매니페스트 (스코프 판정 불가 — .opal/code-map/index.json 설정 확인 필요)';
  return [
    '[code-map 작성층] 이 파일은 인라인 @header 대신 외부 code-map 매니페스트에 헤더를 기록해야 합니다.',
    `대상 파일: ${relPath}`,
    `사유(reason): ${decision.reason}`,
    manifestLine,
    `허용 필드: ${WORKER_FIELDS.join(', ')}`,
    `갱신 명령 예시: ~/.opal/tools/code-scan/run.sh target "${relPath}" --json`,
  ].join('\n');
}

function isManifestEntryClean(projectRoot, decision) {
  if (!decision.manifest || !decision.key) return false;
  const manifest = safeReadJson(path.join(projectRoot, decision.manifest));
  const entry = manifest && manifest.files ? manifest.files[decision.key] : null;
  if (!entry) return false;
  const hasDescription = typeof entry.description === 'string' && entry.description.trim() !== '';
  const isDraft = entry.draft === true;
  return hasDescription && !isDraft;
}

function main() {
  // ① stdin JSON 파싱 실패 / 객체 아님 → 무출력 exit 0
  let data;
  try {
    data = JSON.parse(readStdin());
  } catch {
    return;
  }
  if (!data || typeof data !== 'object') return;

  // ② tool_name ∉ {Edit, Write, MultiEdit} → 무출력 exit 0 (matcher 이중 방어)
  if (!TOOL_NAMES.has(data.tool_name)) return;

  // ③ tool_input.file_path 부재·비문자열 → 무출력 exit 0
  const toolInput = data.tool_input;
  const filePath = toolInput && typeof toolInput === 'object' ? toolInput.file_path : undefined;
  if (typeof filePath !== 'string' || filePath.length === 0) return;

  // ④ file_path 상위로 findProjectRoot 탐색 실패 → 무출력 exit 0
  let projectRoot;
  try {
    projectRoot = findProjectRoot();
  } catch {
    return;
  }
  if (!projectRoot) return;
  projectRoot = toRealAbsPath(projectRoot);

  // ⑤ 전역 headerSource가 2택이 아니거나 inline → 무출력 exit 0 (080 §3.5.2, TASK 080 F-12⑤)
  //    CLI 플래그가 없는 hook에서는 전역 config 1층이 곧 이 실행의 확정 모드다.
  //    [MUST] 미설정·무효값·설정 파싱 실패는 CLI에서 전 명령 차단(exit 1)이지만 hook만은 예외다 —
  //    매 편집마다 출력이 뜨면 세션이 망가진다(PostToolUse fail-safe 계약, 077 PM-7).
  //    inline도 같은 자리에서 끊는다: decideTarget이 항상 write_to:'inline'을 돌려주므로 ⑧단에서
  //    어차피 이탈하지만, 상위에서 끊어 resolveScope·mirrorPathForDir 연산을 생략한다.
  //    [MUST] 이 게이트는 ⑥ code-map 로딩보다 **반드시 위**에 있어야 한다 — loadCodeMap은
  //    normalizeIndexScope를 경유해 폐기 키 안내를 stderr로 1회 발화하므로(code-scan.js:455),
  //    아래에 두면 조용히 이탈해야 할 트리에서 hook의 "무출력" 계약이 stderr 축에서 깨진다
  //    (080 F-12e / TS-076). 순서 자체가 계약이며, 게이트 위에서 code-map을 읽어서는 안 된다.
  const config = loadConfig(projectRoot);
  const mode = config.headerSource;
  if (mode !== 'inline' && mode !== 'manifest') return;
  if (mode === 'inline') return;

  // ⑥ {root}/.opal/code-map/index.json 부재 → 무출력 exit 0 (code-map 미사용 프로젝트 이탈점)
  const codeMap = loadCodeMap(projectRoot);
  if (!codeMap.present || codeMap.error) return;

  // ⑦ 확장자 ∉ config.extensions → 무출력 exit 0
  const absPath = toRealAbsPath(path.resolve(filePath));
  if (!config.extensions.includes(path.extname(absPath))) return;

  const relPath = path.relative(projectRoot, absPath).split(path.sep).join('/');
  if (relPath.startsWith('..')) return;

  // 확정 모드를 ctx에 실어 전달한다 — decideTarget은 모드 직결로 판정하므로(080 §3.3.2 (B))
  // 이 값이 없으면 hook만 다른 판정을 보게 된다. ⑤를 통과한 시점에서 mode는 'manifest' 확정이다.
  const ctx = { projectRoot, config, codeMap, headerSource: mode };
  let decision;
  try {
    decision = decideTarget(relPath, ctx);
  } catch {
    return;
  }

  // ⑧ write_to: 'inline' → 무출력 exit 0
  if (!decision || decision.write_to !== 'manifest') return;

  // ⑨ 매니페스트 엔트리 존재 + draft !== true + description 비공백 → 무출력 exit 0 (갱신 완료 상태)
  if (isManifestEntryClean(projectRoot, decision)) return;

  // ⑩ 그 외 → additionalContext 경고 출력
  const warning = buildWarning(relPath, decision);
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PostToolUse',
      additionalContext: warning,
    },
  }));
}

if (require.main === module) {
  try {
    main();
  } catch {
    // 전 경로 fail-safe — 어떤 예외에서도 정상 도구 흐름을 차단하지 않는다 (todo_mirror_hook.py:124-130 준용)
  }
  process.exit(0);
}

module.exports = { main };

// 변경이력
// v1.0.0 2026-07-28 00:00: 최초 작성 — PostToolUse hook, 조기 이탈 9단 + fail-safe (태스크 077, F-009)
// v1.1.0 2026-08-02 14:45: 조기 이탈 ⑤.5 신설 — 전역 headerSource가 2택(inline|manifest)이 아니거나
//                          inline이면 무출력 exit 0. 미설정·무효값·설정 파싱 실패에서 CLI는 전 명령을
//                          차단하지만 hook은 fail-safe 계약상 예외다. loadConfig 호출을 ⑤.5로 끌어올려
//                          ⑥ 확장자 판정과 공유하고, 확정 모드를 ctx.headerSource로 실어 decideTarget의
//                          모드 직결 판정(080 §3.3.2 (B))이 hook 경로에서도 동일하게 성립하도록 배선
//                          (태스크 080, F-005)
// v1.1.1 2026-08-02 15:59: 조기 이탈 순서 교정 — 모드 게이트를 code-map 로딩 위로 재배치(구 ⑤/⑤.5 →
//                          신 ⑥/⑤, 후속 단 ⑦~⑩ 재번호). loadCodeMap → normalizeIndexScope가
//                          폐기 키 안내를 stderr로 발화하므로 게이트가 아래에 있으면 미설정·무효값·
//                          inline 트리에서 매 편집마다 stderr 295바이트가 샜다(무출력 계약 위반).
//                          분기·조건 추가 없이 순서만 교정 (태스크 080, F-12e / TS-076)
