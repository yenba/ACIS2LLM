import { afterEach, describe, expect, test } from "bun:test";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { initEnv } from "../src/env";

const saved: Record<string, string | undefined> = {};
const KEYS = ["ACIS_WORKSPACE_DIR", "ACIS_DATA_DIR", "ACIS_UV_DIR", "ACIS_SKILL_DIR"];

function setEnv(vars: Record<string, string>) {
  for (const k of KEYS) {
    saved[k] = process.env[k];
    delete process.env[k];
  }
  Object.assign(process.env, vars);
}

afterEach(() => {
  for (const k of KEYS) {
    if (saved[k] === undefined) delete process.env[k];
    else process.env[k] = saved[k]!;
  }
});

describe("initEnv", () => {
  test("creates dirs, writes profile, syncs skill, prepends uv to PATH", () => {
    const base = mkdtempSync(join(tmpdir(), "acis-env-"));
    const skillSrc = join(base, "skill-src");
    mkdirSync(skillSrc, { recursive: true });
    writeFileSync(join(skillSrc, "SKILL.md"), "---\nname: acis-weather\n---\n");
    const uvDir = join(base, "uv");
    mkdirSync(uvDir);

    setEnv({
      ACIS_WORKSPACE_DIR: join(base, "ws"),
      ACIS_DATA_DIR: join(base, "data"),
      ACIS_UV_DIR: uvDir,
      ACIS_SKILL_DIR: skillSrc,
    });

    const env = initEnv();
    expect(existsSync(env.workspaceDir)).toBe(true);
    expect(existsSync(join(env.agentDir, "skills", "acis-weather", "SKILL.md"))).toBe(true);
    expect(readFileSync(env.profilePath, "utf8")).toContain("(deny file-write*)");
    expect(env.bashEnv.PATH!.startsWith(uvDir)).toBe(true);
    expect(env.bashEnv.UV_CACHE_DIR).toBe(join(env.dataDir, "uv-cache"));
    rmSync(base, { recursive: true, force: true });
  });

  test("works without optional env vars", () => {
    setEnv({});
    const env = initEnv();
    expect(env.workspaceDir).toContain(".acis-sidecar");
    expect(existsSync(env.profilePath)).toBe(true);
  });
});
