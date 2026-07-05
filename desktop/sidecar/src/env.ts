import { cpSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { buildProfile } from "./sandbox";

export interface SidecarEnv {
  workspaceDir: string;
  dataDir: string;
  agentDir: string;
  profilePath: string;
  bashEnv: Record<string, string>;
}

export function initEnv(): SidecarEnv {
  const fallback = join(homedir(), ".acis-sidecar");
  const workspaceDir = process.env.ACIS_WORKSPACE_DIR || join(fallback, "workspace");
  const dataDir = process.env.ACIS_DATA_DIR || join(fallback, "data");
  const agentDir = join(dataDir, "pi-agent");
  const skillsDir = join(agentDir, "skills");

  for (const d of [workspaceDir, dataDir, skillsDir]) {
    mkdirSync(d, { recursive: true });
  }

  const skillSrc = process.env.ACIS_SKILL_DIR;
  if (skillSrc && existsSync(skillSrc)) {
    cpSync(skillSrc, join(skillsDir, "acis-weather"), { recursive: true });
  }

  const profilePath = join(dataDir, "sandbox.sb");
  writeFileSync(profilePath, buildProfile([workspaceDir, dataDir, process.env.TMPDIR || tmpdir()]));

  const uvDir = process.env.ACIS_UV_DIR;
  const basePath = process.env.PATH || "/usr/bin:/bin:/usr/sbin:/sbin";
  const bashEnv: Record<string, string> = {
    HOME: homedir(),
    TMPDIR: process.env.TMPDIR || tmpdir(),
    PATH: uvDir ? `${uvDir}:${basePath}` : basePath,
    UV_CACHE_DIR: join(dataDir, "uv-cache"),
    UV_PYTHON_INSTALL_DIR: join(dataDir, "uv-python"),
  };
  return { workspaceDir, dataDir, agentDir, profilePath, bashEnv };
}
