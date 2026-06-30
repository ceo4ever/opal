#!/usr/bin/env node

/**
 * opal-project-init 플랫폼 파일 적용 스크립트
 *
 * 역할: OPAL 부트스트래퍼가 포함된 플랫폼 파일(CLAUDE.md, GEMINI.md, .cursorrules)만 처리.
 *       docs/, .opal/ 문서는 에이전트가 직접 작성하므로 이 스크립트의 범위가 아님.
 *
 * 사용법:
 *   node apply.js --project-root /path/to/project
 *   node apply.js --project-root /path/to/project --dry-run
 */

const fs = require("fs");
const path = require("path");

// --- 설정 ---

const TEMPLATES_DIR = path.resolve(__dirname, "..", "templates");

const PLATFORM_FILES = [
  { src: "platform/CLAUDE.md", dest: "CLAUDE.md" },
  { src: "platform/GEMINI.md", dest: "GEMINI.md" },
  { src: "platform/.cursorrules", dest: ".cursorrules" },
  { src: "platform/AGENTS.md", dest: "AGENTS.md" },
];

// --- OPAL 마커 상수 ---

const OPAL_START_MARKER = "# === OPAL START ===";
const OPAL_END_MARKER = "# === OPAL END ===";

// --- 유틸 ---

function ensureDir(filePath) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

/**
 * 기존 파일을 .bak 확장자로 백업한다.
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
 * - 기존 파일에 OPAL 마커가 있으면: OPAL 구간만 교체, 나머지 보존
 * - 기존 파일에 OPAL 마커가 없으면: 새 부트스트래퍼 + 기존 내용 보존
 */
function mergeClaudeMd(existingPath, newContent) {
  try {
    const existing = fs.readFileSync(existingPath, "utf-8");

    // 기존 파일에서 OPAL 구간 외 사용자 내용 추출
    const existingOpalStartIdx = existing.indexOf(OPAL_START_MARKER);
    const existingOpalEndIdx = existing.indexOf(OPAL_END_MARKER);
    let existingUserContent = "";

    if (existingOpalStartIdx !== -1 && existingOpalEndIdx !== -1) {
      // OPAL 마커가 있으면: 마커 앞 + 마커 뒤 = 사용자 내용
      const before = existing.substring(0, existingOpalStartIdx).trim();
      const after = existing
        .substring(existingOpalEndIdx + OPAL_END_MARKER.length)
        .trim();
      existingUserContent = [before, after].filter(Boolean).join("\n\n");
    } else {
      // OPAL 마커가 없으면 기존 내용 전체가 사용자 내용
      existingUserContent = existing.trim();
    }

    // 병합: 새 부트스트래퍼 + 기존 사용자 내용
    const parts = [newContent.trim()];
    if (existingUserContent) {
      parts.push(existingUserContent);
    }

    return parts.join("\n\n") + "\n";
  } catch (err) {
    console.error(`  CLAUDE.md 병합 실패: ${err.message}`);
    return newContent;
  }
}

/**
 * GEMINI.md 또는 .cursorrules를 OPAL 마커 기반으로 병합한다.
 * CLAUDE.md와 동일한 로직 적용.
 */
function mergeOther(existingPath, newContent) {
  // .cursorrules의 경우 YAML frontmatter 고려
  try {
    const existing = fs.readFileSync(existingPath, "utf-8");

    const existingOpalStartIdx = existing.indexOf(OPAL_START_MARKER);
    const existingOpalEndIdx = existing.indexOf(OPAL_END_MARKER);

    if (existingOpalStartIdx !== -1 && existingOpalEndIdx !== -1) {
      // OPAL 마커가 있으면: 마커 구간만 교체
      const before = existing.substring(0, existingOpalStartIdx).trim();
      const after = existing
        .substring(existingOpalEndIdx + OPAL_END_MARKER.length)
        .trim();
      const parts = [before, newContent.trim(), after].filter(Boolean);
      return parts.join("\n\n") + "\n";
    } else {
      // OPAL 마커가 없으면: 기존 내용 + 새 부트스트래퍼 append
      return existing.trimEnd() + "\n\n" + newContent.trim() + "\n";
    }
  } catch (err) {
    console.error(`  파일 병합 실패: ${err.message}`);
    return newContent;
  }
}

// --- 메인 ---

function main() {
  const args = process.argv.slice(2);
  const rootIdx = args.indexOf("--project-root");
  const dryRun = args.includes("--dry-run");

  if (rootIdx === -1 || !args[rootIdx + 1]) {
    console.error("사용법: node apply.js --project-root /path/to/project [--dry-run]");
    process.exit(1);
  }

  const projectRoot = path.resolve(args[rootIdx + 1]);

  if (!fs.existsSync(projectRoot)) {
    console.error(`프로젝트 루트 없음: ${projectRoot}`);
    process.exit(1);
  }

  const createdFiles = [];

  console.log(`\nopal-project-init 플랫폼 파일 적용`);
  console.log(`  프로젝트: ${projectRoot}`);
  console.log(`  dry-run: ${dryRun}`);
  console.log("");

  console.log("[플랫폼 파일]");
  for (const { src, dest } of PLATFORM_FILES) {
    const srcPath = path.join(TEMPLATES_DIR, "common", src);
    const destPath = path.join(projectRoot, dest);

    if (!fs.existsSync(srcPath)) {
      console.warn(`  SKIP (템플릿 없음): ${srcPath}`);
      continue;
    }

    const newContent = fs.readFileSync(srcPath, "utf-8");
    const destExists = fs.existsSync(destPath);

    if (dryRun) {
      console.log(`  DRY-RUN: ${destPath}${destExists ? " (병합)" : ""}`);
      createdFiles.push(destPath);
      continue;
    }

    if (destExists) {
      // 기존 파일이 있으면 병합
      backupFile(destPath);
      const merged =
        dest === "CLAUDE.md"
          ? mergeClaudeMd(destPath, newContent)
          : mergeOther(destPath, newContent);
      fs.writeFileSync(destPath, merged, "utf-8");
      console.log(`  MERGE: ${destPath}`);
    } else {
      // 새로 생성
      ensureDir(destPath);
      fs.writeFileSync(destPath, newContent, "utf-8");
      console.log(`  CREATE: ${destPath}`);
    }
    createdFiles.push(destPath);
  }

  // 결과 출력
  const result = {
    status: "success",
    projectRoot,
    filesCreated: createdFiles.length,
    files: createdFiles.map((f) => path.relative(projectRoot, f)),
  };

  console.log("\n=== 결과 ===");
  console.log(JSON.stringify(result, null, 2));
}

main();
