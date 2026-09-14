/**
 * @header {
 *   "module": "api-env-files-test",
 *   "layer": "test",
 *   "domain": "core",
 *   "description": "S-2 — src/vite-env.d.ts·.env.development 파일 존재(MV-25) + npm run typecheck exit 0 + npm run build(TMPDIR outDir) exit 0, 3단 모두를 판정 조건으로 묶는다(A-2, D-18). 파일 존재만으로는 통과시키지 않는다.",
 *   "task": "127-260912-oppl-E2E-하네스-구현",
 *   "scenarios": ["S-2"],
 *   "exports": []
 * }
 */

import { describe, it, expect } from "vitest";
// @types/node 미설치 프로젝트(패키지 설치 금지)이므로 node: 모듈 타입 해석을
// 개별 @ts-expect-error로 억제한다 — 값(런타임)은 vitest(Node 실행 환경)에서
// 정상 동작한다.
// @ts-expect-error TS2591 — node:child_process 타입 미해석(@types/node 미설치)
import { execFileSync } from "node:child_process";
// @ts-expect-error TS2591 — node:fs 타입 미해석(@types/node 미설치)
import { mkdtempSync, rmSync, existsSync } from "node:fs";
// @ts-expect-error TS2591 — node:os 타입 미해석(@types/node 미설치)
import { tmpdir } from "node:os";
// @ts-expect-error TS2591 — node:path 타입 미해석(@types/node 미설치)
import path from "node:path";

const viteEnvDts = import.meta.glob("/src/vite-env.d.ts");
const envDevelopment = import.meta.glob("/.env.development");

// vitest는 dashboard/frontend를 root로 실행하므로 cwd가 곧 FRONTEND_ROOT다.
// @ts-expect-error TS2591 — process(node global) 타입 미해석(@types/node 미설치)
const FRONTEND_ROOT = process.cwd();

describe("S-2: vite-env.d.ts · .env.development 존재 + typecheck + build (RED, 3단 필수)", () => {
  it("src/vite-env.d.ts가 존재한다", () => {
    expect(Object.keys(viteEnvDts).length).toBeGreaterThan(0);
  });

  it(".env.development가 존재한다", () => {
    expect(Object.keys(envDevelopment).length).toBeGreaterThan(0);
  });

  it("npm run typecheck가 exit 0으로 통과한다 (D-18 3단 중 (ii))", () => {
    execFileSync("npm", ["run", "typecheck"], {
      cwd: FRONTEND_ROOT,
      stdio: "pipe",
    });
  });

  it("npm run build가 TMPDIR outDir로 exit 0 통과하고 저장소 dist/를 남기지 않는다 (D-18 3단 중 (iii))", () => {
    const outDir = mkdtempSync(path.join(tmpdir(), "opal-e2e-fe-build-"));
    try {
      execFileSync(
        "npm",
        ["run", "build", "--", "--outDir", outDir, "--emptyOutDir"],
        { cwd: FRONTEND_ROOT, stdio: "pipe" },
      );
      expect(existsSync(path.join(FRONTEND_ROOT, "dist"))).toBe(false);
    } finally {
      rmSync(outDir, { recursive: true, force: true });
    }
  });
});
