#!/usr/bin/env node
/**
 * @header {
 *   "module": "code-map-hook",
 *   "layer": "util",
 *   "domain": "code-scan",
 *   "description": "PostToolUse hook — Edit/Write/MultiEdit 이벤트에서 code-map 대상 파일의 외부 매니페스트 미갱신을 감지해 결정론 경고(additionalContext)를 주입한다. code-map 미사용 프로젝트에서는 조기 이탈(index.json 부재)로 즉시 무관 판정·무출력·exit 0 (PM-7, TASK 077)",
 *   "exports": ["main"],
 *   "depends": ["code-scan"],
 *   "note": "조기 이탈 9단(PLAN.md §3.9.2 (C)) + 전 경로 fail-safe(todo_mirror_hook.py:124-130 패턴 준용). WORKER_FIELDS는 code-scan.js가 module.exports로 노출하지 않으므로 표시용으로 로컬 복제(header-standard.md §7 5필드와 동기 유지)."
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

  // ⑤ {root}/.opal/code-map/index.json 부재 → 무출력 exit 0 (code-map 미사용 프로젝트 이탈점)
  const codeMap = loadCodeMap(projectRoot);
  if (!codeMap.present || codeMap.error) return;

  // ⑥ 확장자 ∉ config.extensions → 무출력 exit 0
  const config = loadConfig(projectRoot);
  const absPath = toRealAbsPath(path.resolve(filePath));
  if (!config.extensions.includes(path.extname(absPath))) return;

  const relPath = path.relative(projectRoot, absPath).split(path.sep).join('/');
  if (relPath.startsWith('..')) return;

  const ctx = { projectRoot, config, codeMap };
  let decision;
  try {
    decision = decideTarget(relPath, ctx);
  } catch {
    return;
  }

  // ⑦ write_to: 'inline' → 무출력 exit 0
  if (!decision || decision.write_to !== 'manifest') return;

  // ⑧ 매니페스트 엔트리 존재 + draft !== true + description 비공백 → 무출력 exit 0 (갱신 완료 상태)
  if (isManifestEntryClean(projectRoot, decision)) return;

  // ⑨ 그 외 → additionalContext 경고 출력
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
// v1.0 2026-07-28: 최초 작성 — PostToolUse hook, 조기 이탈 9단 + fail-safe (태스크 077, F-009)
