#!/usr/bin/env node
// code-scan — OPAL @header metadata scanner
//
// 코드 파일의 @header 메타블록을 스캔하여 프로젝트 코드 구조를 빠르게 파악한다.
// 프로젝트별 .opal/code-scan.json 설정으로 scope(be/fe 등)를 정의한다.
//
// 사용법: node code-scan.js <command> [options]
//   scan [path]          파일 스캔 (기본: 전체)
//   domain [name]        도메인별 조회 (인자 없으면 목록)
//   layer [name]         레이어별 조회 (인자 없으면 목록)
//   search <keyword>     헤더 내 키워드 검색
//   exports <keyword>    exports 필드 전용 검색
//   summary              도메인/레이어 요약
//   depends <module>     의존 관계 추적
//   missing              @header 없는 파일 목록

'use strict';

const fs = require('fs');
const path = require('path');

// ═══════════════════════════════════════════
// Constants
// ═══════════════════════════════════════════

const VERSION = '1.1.0';
const HEADER_READ_BYTES = 8192;

const DEFAULT_CONFIG = {
  scopes: {},
  extensions: ['.py', '.js', '.ts', '.vue', '.jsx', '.tsx', '.svelte', '.kt', '.kts', '.java', '.swift'],
  exclude: ['node_modules', '__pycache__', '.git', 'dist', 'build', '.venv', 'env', '.next', '.nuxt', '.output'],
  excludePatterns: []
};

const USAGE = `
code-scan v${VERSION} — OPAL @header metadata scanner

Usage: node code-scan.js <command> [options]

Commands:
  scan [path]           Scan files for @header (default: all scopes)
  domain [name]         List domains, or filter by domain
  layer [name]          List layers, or filter by layer
  search <keyword>      Search within header content
  exports <keyword>     Search within exports field only
  summary               Project overview by domain/layer
  depends <module>      Show dependency relationships
  missing               List files without @header

Options:
  --scope <name>        Scope filter (e.g., be, fe)
  --domain <name>       Filter by domain (combinable)
  --layer <name>        Filter by layer (combinable)
  --exclude <patterns>  Exclude file patterns (comma-separated)
                        e.g., --exclude "__init__.py,test_*,*.spec.ts"
  --brief               One-line summary (default)
  --full                Full header JSON
  --json                Raw JSON for piping

Exclude patterns:
  Supports wildcards: * (any chars), ? (single char)
  Matched against filename by default, or path if pattern contains /
  Set in CLI (--exclude) or config (excludePatterns), both are merged

Config:
  {project}/.opal/code-scan.json
  {
    "scopes": { "be": "workspace/backend/", "fe": "workspace/frontend/src/" },
    "extensions": [".py", ".js", ".ts", ".vue"],
    "exclude": ["node_modules", "__pycache__"],
    "excludePatterns": ["__init__.py", "test_*", "*.spec.ts"]
  }
`.trim();

// ═══════════════════════════════════════════
// Colors (auto-detect TTY)
// ═══════════════════════════════════════════

const isTTY = process.stdout.isTTY;
const C = {
  reset: isTTY ? '\x1b[0m' : '',
  bold:  isTTY ? '\x1b[1m' : '',
  dim:   isTTY ? '\x1b[2m' : '',
  cyan:  isTTY ? '\x1b[36m' : '',
  green: isTTY ? '\x1b[32m' : '',
  yellow:isTTY ? '\x1b[33m' : '',
  gray:  isTTY ? '\x1b[90m' : '',
};

// ═══════════════════════════════════════════
// CLI Parsing
// ═══════════════════════════════════════════

function parseArgs(argv) {
  const args = argv.slice(2);
  const opts = {
    command: null,
    commandArg: null,
    scope: null,
    domain: null,
    layer: null,
    output: 'brief',
    targetPath: null,
    excludePatterns: [],
  };

  let i = 0;
  while (i < args.length) {
    const a = args[i];
    if (a === '--scope'  && i + 1 < args.length) { opts.scope  = args[++i]; }
    else if (a === '--domain' && i + 1 < args.length) { opts.domain = args[++i]; }
    else if (a === '--layer'  && i + 1 < args.length) { opts.layer  = args[++i]; }
    else if (a === '--exclude' && i + 1 < args.length) {
      opts.excludePatterns.push(...args[++i].split(',').map(s => s.trim()).filter(Boolean));
    }
    else if (a === '--brief') { opts.output = 'brief'; }
    else if (a === '--full')  { opts.output = 'full';  }
    else if (a === '--json')  { opts.output = 'json';  }
    else if (a === '--help' || a === '-h') { opts.command = 'help'; }
    else if (a === '--version' || a === '-v') { opts.command = 'version'; }
    else if (!a.startsWith('-') && !opts.command) { opts.command = a; }
    else if (!a.startsWith('-') && !opts.commandArg) { opts.commandArg = a; }
    i++;
  }

  if (!opts.command) opts.command = 'help';
  if (opts.command === 'scan' && opts.commandArg) opts.targetPath = opts.commandArg;
  return opts;
}

// ═══════════════════════════════════════════
// Project & Config
// ═══════════════════════════════════════════

function findProjectRoot() {
  let dir = process.cwd();
  const root = path.parse(dir).root;
  while (dir !== root) {
    if (fs.existsSync(path.join(dir, '.git')) ||
        fs.existsSync(path.join(dir, '.opal')) ||
        fs.existsSync(path.join(dir, 'CLAUDE.md'))) {
      return dir;
    }
    dir = path.dirname(dir);
  }
  return process.cwd();
}

function loadConfig(projectRoot) {
  const configPath = path.join(projectRoot, '.opal', 'code-scan.json');
  if (fs.existsSync(configPath)) {
    try {
      const user = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      return {
        extensions: user.extensions || DEFAULT_CONFIG.extensions,
        exclude: user.exclude || DEFAULT_CONFIG.exclude,
        excludePatterns: user.excludePatterns || [],
        scopes: user.scopes || {},
      };
    } catch { return DEFAULT_CONFIG; }
  }
  return DEFAULT_CONFIG;
}

// ═══════════════════════════════════════════
// Exclude Pattern Matching
// ═══════════════════════════════════════════

function patternToRegex(pattern) {
  let re = '';
  for (let i = 0; i < pattern.length; i++) {
    const ch = pattern[i];
    if (ch === '*' && pattern[i + 1] === '*') {
      re += '.*'; i++;
      if (pattern[i + 1] === '/') i++;
    } else if (ch === '*') { re += '[^/]*'; }
    else if (ch === '?') { re += '.'; }
    else if ('.+^${}()|[]\\'.includes(ch)) { re += '\\' + ch; }
    else { re += ch; }
  }
  return new RegExp('^' + re + '$');
}

function isExcluded(relPath, fileName, patterns) {
  for (const p of patterns) {
    const re = patternToRegex(p);
    // Pattern with / → match against relative path, otherwise → match against filename
    if (p.includes('/') ? re.test(relPath) : re.test(fileName)) return true;
  }
  return false;
}

function mergeExcludePatterns(config, opts) {
  return [...(config.excludePatterns || []), ...(opts.excludePatterns || [])];
}

// ═══════════════════════════════════════════
// File Discovery
// ═══════════════════════════════════════════

function walkDir(dir, config) {
  const files = [];
  if (!fs.existsSync(dir)) return files;

  function recurse(d) {
    let entries;
    try { entries = fs.readdirSync(d, { withFileTypes: true }); }
    catch { return; }
    for (const e of entries) {
      if (config.exclude.includes(e.name)) continue;
      const full = path.join(d, e.name);
      if (e.isDirectory()) recurse(full);
      else if (e.isFile() && config.extensions.includes(path.extname(e.name))) {
        files.push(full);
      }
    }
  }
  recurse(dir);
  return files;
}

function getSearchPaths(projectRoot, config, opts) {
  if (opts.scope) {
    const sp = config.scopes[opts.scope];
    if (!sp) {
      const avail = Object.keys(config.scopes).join(', ') || '(none)';
      process.stderr.write(`Error: Unknown scope "${opts.scope}". Available: ${avail}\n`);
      process.exit(1);
    }
    return [path.resolve(projectRoot, sp)];
  }
  if (opts.targetPath) {
    return [path.resolve(projectRoot, opts.targetPath)];
  }
  const scopes = Object.values(config.scopes);
  return scopes.length > 0
    ? scopes.map(s => path.resolve(projectRoot, s))
    : [projectRoot];
}

function discoverFiles(projectRoot, config, opts) {
  const paths = getSearchPaths(projectRoot, config, opts);
  const all = [];
  for (const p of paths) {
    if (fs.existsSync(p) && fs.statSync(p).isFile()) all.push(p);
    else all.push(...walkDir(p, config));
  }

  // Apply exclude patterns (config + CLI merged)
  const patterns = mergeExcludePatterns(config, opts);
  if (patterns.length === 0) return all.sort();

  return all.filter(f => {
    const rel = path.relative(projectRoot, f);
    return !isExcluded(rel, path.basename(f), patterns);
  }).sort();
}

// ═══════════════════════════════════════════
// Header Parsing
// ═══════════════════════════════════════════

function readFileHead(filePath) {
  try {
    const fd = fs.openSync(filePath, 'r');
    const buf = Buffer.alloc(HEADER_READ_BYTES);
    const n = fs.readSync(fd, buf, 0, HEADER_READ_BYTES, 0);
    fs.closeSync(fd);
    return buf.toString('utf8', 0, n);
  } catch { return null; }
}

function extractHeader(filePath) {
  const content = readFileHead(filePath);
  if (!content) return null;

  const idx = content.indexOf('@header');
  if (idx === -1) return null;

  // Find opening brace
  const braceStart = content.indexOf('{', idx + 7);
  if (braceStart === -1) return null;

  // Match closing brace (string-aware)
  let depth = 0, inStr = false, esc = false, end = -1;
  for (let i = braceStart; i < content.length; i++) {
    const ch = content[i];
    if (esc) { esc = false; continue; }
    if (ch === '\\' && inStr) { esc = true; continue; }
    if (ch === '"') { inStr = !inStr; continue; }
    if (inStr) continue;
    if (ch === '{') depth++;
    else if (ch === '}') { depth--; if (depth === 0) { end = i; break; } }
  }
  if (end === -1) return null;

  const raw = content.substring(braceStart, end + 1);

  // Try direct parse (Python docstring, Vue HTML comment)
  try { return JSON.parse(raw); } catch {}

  // Clean comment prefixes and retry (JSDoc *, Python #, TS //)
  const cleaned = raw.split('\n').map(line =>
    line.replace(/^\s*\*\s?/, '')
        .replace(/^\s*#\s?/, '')
        .replace(/^\s*\/\/\s?/, '')
  ).join('\n');
  try { return JSON.parse(cleaned); } catch {}

  return null;
}

// ═══════════════════════════════════════════
// Scanning & Filtering
// ═══════════════════════════════════════════

function scanAll(projectRoot, config, opts) {
  const files = discoverFiles(projectRoot, config, opts);
  const withHeader = [];
  const noHeader = [];

  for (const f of files) {
    const header = extractHeader(f);
    const rel = path.relative(projectRoot, f);
    if (header) {
      withHeader.push({ path: rel, file: path.basename(f), header });
    } else {
      noHeader.push({ path: rel, file: path.basename(f) });
    }
  }
  return { withHeader, noHeader };
}

function scanHeaders(projectRoot, config, opts) {
  const { withHeader } = scanAll(projectRoot, config, opts);
  return withHeader.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
}

// ═══════════════════════════════════════════
// Output Formatting
// ═══════════════════════════════════════════

function fmtBrief(results) {
  if (results.length === 0) { console.log('No files found.'); return; }

  const maxLayer = Math.max(...results.map(r => (r.header.layer || '?').length));
  const maxFile  = Math.max(...results.map(r => r.file.length));

  for (const r of results) {
    const layer = (r.header.layer || '?').padEnd(maxLayer);
    const file  = r.file.padEnd(maxFile);
    const desc  = r.header.description || '';
    console.log(`${C.cyan}[${layer}]${C.reset}  ${C.bold}${file}${C.reset}  ${C.dim}—${C.reset} ${desc}`);
  }
  console.log(`${C.dim}\n${results.length} file(s)${C.reset}`);
}

function fmtFull(results) {
  if (results.length === 0) { console.log('No files found.'); return; }
  for (const r of results) {
    console.log(`\n${C.cyan}── ${r.path} ──${C.reset}`);
    console.log(JSON.stringify(r.header, null, 2));
  }
  console.log(`${C.dim}\n${results.length} file(s)${C.reset}`);
}

function fmtJson(results) {
  const out = {};
  for (const r of results) out[r.path] = r.header;
  console.log(JSON.stringify(out, null, 2));
}

function output(results, opts) {
  switch (opts.output) {
    case 'full': return fmtFull(results);
    case 'json': return fmtJson(results);
    default:     return fmtBrief(results);
  }
}

// ═══════════════════════════════════════════
// Commands
// ═══════════════════════════════════════════

function cmdScan(projectRoot, config, opts) {
  output(scanHeaders(projectRoot, config, opts), opts);
}

function cmdDomain(projectRoot, config, opts) {
  if (opts.commandArg) {
    opts.domain = opts.commandArg;
    return output(scanHeaders(projectRoot, config, opts), opts);
  }
  // List all domains grouped
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  if (results.length === 0) { console.log('No @header blocks found.'); return; }

  const groups = {};
  for (const r of results) {
    const d = r.header.domain || '(none)';
    if (!groups[d]) groups[d] = [];
    groups[d].push(r);
  }
  for (const [domain, files] of Object.entries(groups).sort()) {
    console.log(`\n${C.green}[${domain}]${C.reset}`);
    const ml = Math.max(...files.map(r => (r.header.layer || '?').length));
    const mf = Math.max(...files.map(r => r.file.length));
    for (const r of files) {
      const layer = (r.header.layer || '?').padEnd(ml);
      const file  = r.file.padEnd(mf);
      console.log(`  ${C.cyan}[${layer}]${C.reset}  ${file}  ${C.dim}—${C.reset} ${r.header.description || ''}`);
    }
  }
}

function cmdLayer(projectRoot, config, opts) {
  if (opts.commandArg) {
    opts.layer = opts.commandArg;
    return output(scanHeaders(projectRoot, config, opts), opts);
  }
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  if (results.length === 0) { console.log('No @header blocks found.'); return; }

  const groups = {};
  for (const r of results) {
    const l = r.header.layer || '(none)';
    if (!groups[l]) groups[l] = [];
    groups[l].push(r);
  }
  for (const [layer, files] of Object.entries(groups).sort()) {
    console.log(`\n${C.green}[${layer}]${C.reset}`);
    const md = Math.max(...files.map(r => (r.header.domain || '?').length));
    const mf = Math.max(...files.map(r => r.file.length));
    for (const r of files) {
      const domain = (r.header.domain || '?').padEnd(md);
      const file   = r.file.padEnd(mf);
      console.log(`  ${C.cyan}[${domain}]${C.reset}  ${file}  ${C.dim}—${C.reset} ${r.header.description || ''}`);
    }
  }
}

function cmdSearch(projectRoot, config, opts) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan search <keyword>'); process.exit(1); }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  const kw = keyword.toLowerCase();
  const matches = all.filter(r => JSON.stringify(r.header).toLowerCase().includes(kw));

  // Re-apply filters
  const filtered = matches.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
  output(filtered, opts);
}

function cmdExports(projectRoot, config, opts) {
  const keyword = opts.commandArg;
  if (!keyword) { console.error('Usage: code-scan exports <keyword>'); process.exit(1); }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  const kw = keyword.toLowerCase();
  const matches = all.filter(r => {
    if (!r.header.exports || !Array.isArray(r.header.exports)) return false;
    return r.header.exports.some(e => e.toLowerCase().includes(kw));
  });

  // Re-apply domain/layer filters
  const filtered = matches.filter(r => {
    if (opts.domain && r.header.domain !== opts.domain) return false;
    if (opts.layer && r.header.layer !== opts.layer) return false;
    return true;
  });
  output(filtered, opts);
}

function cmdSummary(projectRoot, config, opts) {
  const results = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });
  if (results.length === 0) { console.log('No @header blocks found.'); return; }

  const domains = {};
  for (const r of results) {
    const d = r.header.domain || '(none)';
    const l = r.header.layer || '(none)';
    if (!domains[d]) domains[d] = {};
    if (!domains[d][l]) domains[d][l] = 0;
    domains[d][l]++;
  }

  const scopeLabel = opts.scope ? ` (scope: ${opts.scope})` : '';
  console.log(`\n${C.bold}Code Header Summary${scopeLabel}${C.reset}`);
  console.log('─'.repeat(55));

  for (const [domain, layerMap] of Object.entries(domains).sort()) {
    const total = Object.values(layerMap).reduce((a, b) => a + b, 0);
    const detail = Object.entries(layerMap).sort()
      .map(([l, c]) => `${l}×${c}`).join(', ');
    console.log(`${C.green}${domain.padEnd(15)}${C.reset} : ${String(total).padStart(3)} files  ${C.dim}(${detail})${C.reset}`);
  }

  console.log('─'.repeat(55));
  console.log(`Total: ${C.bold}${results.length}${C.reset} files across ${Object.keys(domains).length} domains`);
}

function cmdDepends(projectRoot, config, opts) {
  const target = opts.commandArg;
  if (!target) { console.error('Usage: code-scan depends <module>'); process.exit(1); }

  const all = scanHeaders(projectRoot, config, { ...opts, domain: null, layer: null });

  // Find target file
  const targetResult = all.find(r =>
    r.header.module === target ||
    r.file === target ||
    r.file.replace(path.extname(r.file), '') === target
  );

  // Reverse deps: who depends on target
  const dependedBy = all.filter(r => {
    if (!r.header.depends) return false;
    return r.header.depends.some(d =>
      d.includes(target) || path.basename(d).replace(path.extname(d), '') === target
    );
  });

  // Forward deps: what target depends on
  const dependsOn = [];
  if (targetResult && targetResult.header.depends) {
    for (const dep of targetResult.header.depends) {
      const found = all.find(r => r.path.includes(dep) || r.path.endsWith(dep));
      dependsOn.push({ ref: dep, resolved: found || null });
    }
  }

  const label = targetResult
    ? `${C.bold}${targetResult.header.module}${C.reset} ${C.cyan}[${targetResult.header.layer}]${C.reset}`
    : `${C.bold}${target}${C.reset}`;
  console.log(`\n${label}`);

  console.log(`\n  ${C.yellow}depended by:${C.reset}`);
  if (dependedBy.length > 0) {
    for (const r of dependedBy) console.log(`    ← ${r.file} ${C.cyan}[${r.header.layer}]${C.reset}`);
  } else {
    console.log(`    ${C.dim}(none)${C.reset}`);
  }

  console.log(`\n  ${C.yellow}depends on:${C.reset}`);
  if (dependsOn.length > 0) {
    for (const d of dependsOn) {
      if (d.resolved) console.log(`    → ${d.resolved.file} ${C.cyan}[${d.resolved.header.layer}]${C.reset}`);
      else console.log(`    → ${d.ref} ${C.dim}(not found)${C.reset}`);
    }
  } else {
    console.log(`    ${C.dim}(none)${C.reset}`);
  }
}

function cmdMissing(projectRoot, config, opts) {
  const { noHeader } = scanAll(projectRoot, config, opts);
  if (noHeader.length === 0) {
    console.log(`${C.green}All files have @header blocks.${C.reset}`);
    return;
  }
  for (const r of noHeader) {
    console.log(`${C.yellow}[missing]${C.reset}  ${r.path}`);
  }
  console.log(`${C.dim}\n${noHeader.length} file(s) without @header${C.reset}`);
}

// ═══════════════════════════════════════════
// Main
// ═══════════════════════════════════════════

function main() {
  const opts = parseArgs(process.argv);

  if (opts.command === 'help')    { console.log(USAGE); return; }
  if (opts.command === 'version') { console.log(`code-scan v${VERSION}`); return; }

  const projectRoot = findProjectRoot();
  const config = loadConfig(projectRoot);

  const commands = {
    scan:    cmdScan,
    domain:  cmdDomain,
    layer:   cmdLayer,
    search:  cmdSearch,
    exports: cmdExports,
    summary: cmdSummary,
    depends: cmdDepends,
    missing: cmdMissing,
  };

  const fn = commands[opts.command];
  if (!fn) {
    console.error(`Unknown command: "${opts.command}". Run with --help for usage.`);
    process.exit(1);
  }
  fn(projectRoot, config, opts);
}

main();

// 변경이력
// v1.0.0 — 초기 작성 — scan/domain/layer/search/summary/depends/missing 커맨드
// v1.1.0 — 2026-04-12 — exports 커맨드 추가 — exports 필드 전용 검색 (109)
