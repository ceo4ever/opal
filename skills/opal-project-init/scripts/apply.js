#!/usr/bin/env node

/**
 * opal-project-init 템플릿 적용 스크립트
 *
 * 사용법:
 *   node apply.js --config config.json
 *   node apply.js --config config.json --mode existing
 *   node apply.js --config config.json --dry-run
 *
 * config.json 형식:
 * {
 *   "projectRoot": "/path/to/project",
 *   "projectType": "web",          // web | ai-agent | data | custom
 *   "mode": "new",                 // "new" (기본) | "existing"
 *   "placeholders": {
 *     "PROJECT_NAME": "my-project",
 *     "SERVER_PORT": "8000",
 *     ...
 *   },
 *   "optional": {
 *     "sqlite": false,
 *     "chat": false
 *   },
 *   "excludeTemplates": []         // 기존 모드에서 제외할 템플릿 상대 경로 목록
 * }
 */

const fs = require("fs");
const path = require("path");

// --- 설정 ---

const TEMPLATES_DIR = path.resolve(__dirname, "..", "templates");

const COMMON_DOCS = [
  "docs/INDEX.md",
  "docs/server/README.md",
  "docs/server/ENVIRONMENT.md",
  "docs/server/PROJECT_STRUCTURE.md",
  "docs/server/UV_SETUP.md",
  "docs/client/README.md",
  "docs/client/ARCHITECTURE.md",
  "docs/client/ENVIRONMENT.md",
  "docs/client/PROJECT_STRUCTURE.md",
  "docs/client/OPENAPI_GUIDE.md",
  "docs/client/COMMON_ISSUES.md",
];

const PLATFORM_FILES = [
  { src: "platform/CLAUDE.md", dest: "CLAUDE.md" },
  { src: "platform/GEMINI.md", dest: "GEMINI.md" },
  { src: "platform/.cursorrules", dest: ".cursorrules" },
];

const TYPE_DOCS = {
  web: [
    "docs/server/DOMAIN_GUIDE.md",
    "docs/server/HOW_TO_REQUEST_NEW_DOMAIN.md",
  ],
  "ai-agent": [
    "docs/server/DOMAIN_GUIDE.md",
    "docs/server/HOW_TO_REQUEST_NEW_DOMAIN.md",
  ],
  data: [],
  custom: [],
};

const OPTIONAL_DOCS = {
  sqlite: "docs/server/SQLITE_SETUP.md",
  chat: "docs/client/CHAT_UI_GUIDE.md",
};

const OPAL_FILES = [
  { src: "opal/AGENT.md", dest: ".opal/AGENT.md" },
  { src: "opal/MEMORY.md", dest: ".opal/MEMORY.md" },
];

// --- OPAL 마커 상수 ---

const OPAL_START_MARKER = "# === OPAL START ===";
const OPAL_END_MARKER = "# === OPAL END ===";

// --- 유틸 ---

function replacePlaceholders(content, placeholders) {
  let result = content;
  for (const [key, value] of Object.entries(placeholders)) {
    const regex = new RegExp(`\\{\\{${key}\\}\\}`, "g");
    result = result.replace(regex, value);
  }
  return result;
}

function ensureDir(filePath) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/**
 * 기존 파일을 .bak 확장자로 백업한다.
 * @param {string} filePath - 백업할 파일 경로
 * @returns {string|null} 백업 파일 경로, 원본이 없으면 null
 */
function backupFile(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      const backupPath = filePath + ".bak";
      fs.copyFileSync(filePath, backupPath);
      console.log(`  BACKUP: ${filePath} -> ${backupPath}`);
      return backupPath;
    }
  } catch (err) {
    console.error(`  BACKUP 실패: ${filePath} - ${err.message}`);
  }
  return null;
}

/**
 * CLAUDE.md를 OPAL 마커 기반으로 병합한다.
 *
 * 병합 순서:
 *   1. 새 OPAL 부트스트래퍼 (템플릿의 OPAL 구간)
 *   2. 새 프로젝트 섹션 (템플릿의 OPAL 이후 내용, 치환 완료)
 *   3. 기존 사용자 내용 (OPAL 구간 외 원본 보존)
 *
 * @param {string} existingPath - 기존 CLAUDE.md 경로
 * @param {string} newContent - 치환 완료된 템플릿 내용
 * @returns {string} 병합된 내용
 */
function mergeClaudeMd(existingPath, newContent) {
  try {
    const existing = fs.readFileSync(existingPath, "utf-8");

    // 기존 파일에서 OPAL 구간 외 사용자 내용 추출
    const existingOpalEndIdx = existing.indexOf(OPAL_END_MARKER);
    let existingUserContent = "";
    if (existingOpalEndIdx !== -1) {
      // OPAL END 마커 이후의 내용이 사용자 내용
      existingUserContent = existing
        .substring(existingOpalEndIdx + OPAL_END_MARKER.length)
        .trim();
    } else {
      // OPAL 마커가 없으면 기존 내용 전체가 사용자 내용
      existingUserContent = existing.trim();
    }

    // 새 템플릿에서 OPAL 구간과 프로젝트 섹션 분리
    const newOpalEndIdx = newContent.indexOf(OPAL_END_MARKER);
    let newOpalSection = "";
    let newProjectSection = "";
    if (newOpalEndIdx !== -1) {
      newOpalSection = newContent
        .substring(0, newOpalEndIdx + OPAL_END_MARKER.length)
        .trim();
      newProjectSection = newContent
        .substring(newOpalEndIdx + OPAL_END_MARKER.length)
        .trim();
    } else {
      // 템플릿에 OPAL 마커가 없으면 전체가 프로젝트 섹션
      newProjectSection = newContent.trim();
    }

    // 병합: OPAL 부트스트래퍼 + 프로젝트 섹션 + 기존 사용자 내용
    const parts = [];
    if (newOpalSection) {
      parts.push(newOpalSection);
    }
    if (newProjectSection) {
      parts.push(newProjectSection);
    }
    if (existingUserContent) {
      parts.push(
        "# --- 기존 프로젝트 설정 (원본 보존) ---\n\n" + existingUserContent
      );
    }

    return parts.join("\n\n") + "\n";
  } catch (err) {
    console.error(`  CLAUDE.md 병합 실패: ${err.message}`);
    // 병합 실패 시 새 내용으로 폴백
    return newContent;
  }
}

/**
 * GEMINI.md 또는 .cursorrules를 append 방식으로 병합한다.
 * 기존 내용 끝에 구분선 + 새 내용을 추가한다.
 *
 * @param {string} existingPath - 기존 파일 경로
 * @param {string} newContent - 치환 완료된 템플릿 내용
 * @returns {string} 병합된 내용
 */
function mergeAppend(existingPath, newContent) {
  try {
    const existing = fs.readFileSync(existingPath, "utf-8");
    return (
      existing.trimEnd() +
      "\n\n---\n\n# --- opal-project-init 추가 섹션 ---\n\n" +
      newContent.trim() +
      "\n"
    );
  } catch (err) {
    console.error(`  파일 병합 실패: ${err.message}`);
    return newContent;
  }
}

/**
 * 템플릿 파일을 처리하여 대상 경로에 쓴다.
 * mode에 따라 기존 파일 처리 방식이 달라진다.
 *
 * @param {string} templatePath - 템플릿 소스 경로
 * @param {string} destPath - 대상 경로
 * @param {Object} placeholders - 치환 매핑
 * @param {boolean} dryRun - 미리보기 모드
 * @param {string} mode - "new" | "existing"
 * @param {string} fileType - "docs" | "platform-claude" | "platform-other"
 * @returns {string|null} 생성된 파일 경로, 스킵 시 null
 */
function processFile(
  templatePath,
  destPath,
  placeholders,
  dryRun,
  mode,
  fileType
) {
  if (!fs.existsSync(templatePath)) {
    console.warn(`  SKIP (없음): ${templatePath}`);
    return null;
  }

  const content = fs.readFileSync(templatePath, "utf-8");
  const replaced = replacePlaceholders(content, placeholders);
  const destExists = fs.existsSync(destPath);

  if (dryRun) {
    if (mode === "existing" && destExists) {
      if (fileType === "docs") {
        console.log(`  DRY-RUN SKIP (기존 존재): ${destPath}`);
        return null;
      } else if (fileType === "platform-claude") {
        console.log(`  DRY-RUN MERGE (CLAUDE.md): ${destPath}`);
      } else if (fileType === "platform-other") {
        console.log(`  DRY-RUN MERGE (append): ${destPath}`);
      }
    } else {
      console.log(`  DRY-RUN: ${destPath}`);
    }
    return destPath;
  }

  // existing 모드에서 기존 파일 처리
  if (mode === "existing" && destExists) {
    if (fileType === "docs") {
      // docs 파일은 기존이 있으면 건너뛰기
      console.log(`  SKIP (기존 존재): ${destPath}`);
      return null;
    }

    // 플랫폼 파일은 백업 후 병합
    backupFile(destPath);

    if (fileType === "platform-claude") {
      const merged = mergeClaudeMd(destPath, replaced);
      fs.writeFileSync(destPath, merged, "utf-8");
      console.log(`  MERGE (CLAUDE.md): ${destPath}`);
      return destPath;
    }

    if (fileType === "platform-other") {
      const merged = mergeAppend(destPath, replaced);
      fs.writeFileSync(destPath, merged, "utf-8");
      console.log(`  MERGE (append): ${destPath}`);
      return destPath;
    }
  }

  // 기본 동작: 새로 쓰기
  ensureDir(destPath);
  fs.writeFileSync(destPath, replaced, "utf-8");
  console.log(`  OK: ${destPath}`);
  return destPath;
}

/**
 * 상대 경로가 excludeTemplates 목록에 포함되는지 확인한다.
 *
 * @param {string} relPath - 템플릿 상대 경로 (예: "docs/server/UV_SETUP.md")
 * @param {string[]} excludeTemplates - 제외 목록
 * @returns {boolean}
 */
function isExcluded(relPath, excludeTemplates) {
  return excludeTemplates.some(
    (excluded) =>
      relPath === excluded ||
      relPath.startsWith(excluded.replace(/\/?$/, "/"))
  );
}

// --- 메인 ---

function main() {
  const args = process.argv.slice(2);
  const configIdx = args.indexOf("--config");
  const dryRun = args.includes("--dry-run");

  // --mode CLI 옵션 (config.json보다 우선)
  const modeIdx = args.indexOf("--mode");
  const cliMode = modeIdx !== -1 ? args[modeIdx + 1] : null;

  if (configIdx === -1 || !args[configIdx + 1]) {
    console.error(
      "사용법: node apply.js --config config.json [--mode existing] [--dry-run]"
    );
    process.exit(1);
  }

  const configPath = path.resolve(args[configIdx + 1]);
  if (!fs.existsSync(configPath)) {
    console.error(`설정 파일 없음: ${configPath}`);
    process.exit(1);
  }

  const config = JSON.parse(fs.readFileSync(configPath, "utf-8"));
  const {
    projectRoot,
    projectType = "custom",
    placeholders = {},
    optional = {},
    excludeTemplates = [],
  } = config;

  // mode 결정: CLI > config > 기본값 "new"
  const mode = cliMode || config.mode || "new";

  if (!projectRoot) {
    console.error("설정 오류: projectRoot 필수");
    process.exit(1);
  }

  if (mode !== "new" && mode !== "existing") {
    console.error(`설정 오류: mode는 "new" 또는 "existing"이어야 합니다 (입력: "${mode}")`);
    process.exit(1);
  }

  // scope 결정: config > 기본값 "full"
  const scope = config.scope || "full";

  if (scope !== "full" && scope !== "opal-only") {
    console.error(`설정 오류: scope는 "full" 또는 "opal-only"이어야 합니다 (입력: "${scope}")`);
    process.exit(1);
  }

  // CURRENT_DATE 동적 주입
  placeholders["CURRENT_DATE"] = new Date().toISOString().split("T")[0];

  const absRoot = path.resolve(projectRoot);
  const createdFiles = [];
  const skippedFiles = [];

  console.log(`\nopal-project-init 템플릿 적용`);
  console.log(`  프로젝트: ${absRoot}`);
  console.log(`  유형: ${projectType}`);
  console.log(`  모드: ${mode}`);
  console.log(`  scope: ${scope}`);
  console.log(`  dry-run: ${dryRun}`);
  if (excludeTemplates.length > 0) {
    console.log(`  제외 템플릿: ${excludeTemplates.join(", ")}`);
  }
  console.log("");

  if (scope === "full") {
    // 1) 공통 문서
    console.log("[1/4] 공통 문서 (common/docs/)");
    for (const rel of COMMON_DOCS) {
      if (isExcluded(rel, excludeTemplates)) {
        console.log(`  SKIP (제외 목록): ${rel}`);
        skippedFiles.push(rel);
        continue;
      }
      const src = path.join(TEMPLATES_DIR, "common", rel);
      const dest = path.join(absRoot, rel);
      const f = processFile(src, dest, placeholders, dryRun, mode, "docs");
      if (f) {
        createdFiles.push(f);
      } else if (mode === "existing" && fs.existsSync(dest)) {
        skippedFiles.push(rel);
      }
    }

    // 2) 플랫폼 파일
    console.log("\n[2/4] 플랫폼 AI 지시 파일");
    for (const { src, dest } of PLATFORM_FILES) {
      const srcPath = path.join(TEMPLATES_DIR, "common", src);
      const destPath = path.join(absRoot, dest);
      const fileType =
        dest === "CLAUDE.md" ? "platform-claude" : "platform-other";
      const f = processFile(
        srcPath,
        destPath,
        placeholders,
        dryRun,
        mode,
        fileType
      );
      if (f) createdFiles.push(f);
    }

    // 3) 유형별 추가 문서
    const typeDocs = TYPE_DOCS[projectType] || [];
    if (typeDocs.length > 0) {
      console.log(`\n[3/4] 유형별 추가 (${projectType}/)`);
      for (const rel of typeDocs) {
        if (isExcluded(rel, excludeTemplates)) {
          console.log(`  SKIP (제외 목록): ${rel}`);
          skippedFiles.push(rel);
          continue;
        }
        const src = path.join(TEMPLATES_DIR, projectType, rel);
        const dest = path.join(absRoot, rel);
        const f = processFile(src, dest, placeholders, dryRun, mode, "docs");
        if (f) {
          createdFiles.push(f);
        } else if (mode === "existing" && fs.existsSync(dest)) {
          skippedFiles.push(rel);
        }
      }
    } else {
      console.log(`\n[3/4] 유형별 추가: 없음 (${projectType})`);
    }

    // 4) 조건부 문서
    const optionalEntries = Object.entries(optional).filter(([, v]) => v);
    if (optionalEntries.length > 0) {
      console.log("\n[4/4] 조건부 문서");
      for (const [key] of optionalEntries) {
        const rel = OPTIONAL_DOCS[key];
        if (!rel) continue;
        if (isExcluded(rel, excludeTemplates)) {
          console.log(`  SKIP (제외 목록): ${rel}`);
          skippedFiles.push(rel);
          continue;
        }
        const src = path.join(TEMPLATES_DIR, "optional", rel);
        const dest = path.join(absRoot, rel);
        const f = processFile(src, dest, placeholders, dryRun, mode, "docs");
        if (f) {
          createdFiles.push(f);
        } else if (mode === "existing" && fs.existsSync(dest)) {
          skippedFiles.push(rel);
        }
      }
    } else {
      console.log("\n[4/4] 조건부 문서: 없음");
    }
  } else {
    console.log("[1/4]~[4/4] 스킵 (scope=opal-only)");
  }

  // 5) .opal/ 파일 (PM 에이전트 프로필 + 메모리 인덱스)
  console.log("\n[5/5] .opal/ 파일 (PM 프로필)");
  for (const { src, dest } of OPAL_FILES) {
    const rel = dest;
    if (isExcluded(rel, excludeTemplates)) {
      console.log(`  SKIP (제외 목록): ${rel}`);
      skippedFiles.push(rel);
      continue;
    }
    const srcPath = path.join(TEMPLATES_DIR, "common", src);
    const destPath = path.join(absRoot, dest);
    const f = processFile(srcPath, destPath, placeholders, dryRun, mode, "docs");
    if (f) {
      createdFiles.push(f);
    } else if (mode === "existing" && fs.existsSync(destPath)) {
      skippedFiles.push(rel);
    }
  }

  // 결과 출력 (JSON)
  const result = {
    status: "success",
    projectRoot: absRoot,
    projectType,
    mode,
    scope,
    filesCreated: createdFiles.length,
    filesSkipped: skippedFiles.length,
    files: createdFiles.map((f) => path.relative(absRoot, f)),
    skipped: skippedFiles,
  };

  console.log("\n=== 결과 ===");
  console.log(JSON.stringify(result, null, 2));

  if (mode === "existing" && skippedFiles.length > 0) {
    console.log(
      `\n참고: 기존 모드에서 ${skippedFiles.length}개 파일을 건너뛰었습니다.`
    );
  }

  // 결과를 stdout JSON으로도 출력 (AI가 파싱 가능하도록)
  if (!dryRun) {
    const resultPath = path.join(absRoot, ".opal-project-init-result.json");
    fs.writeFileSync(resultPath, JSON.stringify(result, null, 2));
    console.log(`\n결과 저장: ${resultPath}`);
  }
}

main();
