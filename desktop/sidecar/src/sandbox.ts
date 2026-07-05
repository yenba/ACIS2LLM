import { realpathSync } from "node:fs";

const DEFAULT_MAX_OUTPUT = 50_000;

/**
 * SBPL profile: everything allowed except file writes, which are limited to
 * the given directories (plus /dev for tty/null). Later rules take precedence,
 * so the allow-list must follow the deny.
 */
export function buildProfile(writablePaths: string[]): string {
  const canonical = writablePaths.map((p) => {
    try {
      return realpathSync(p);
    } catch {
      return p;
    }
  });
  const subpaths = [...canonical, "/dev"].map((p) => `  (subpath "${p}")`).join("\n");
  return [
    "(version 1)",
    "(allow default)",
    "(deny file-write*)",
    "(allow file-write*",
    subpaths,
    ")",
  ].join("\n");
}

export function truncateOutput(s: string, max: number = DEFAULT_MAX_OUTPUT): string {
  if (s.length <= max) return s;
  return s.slice(0, max) + "\n[output truncated]";
}