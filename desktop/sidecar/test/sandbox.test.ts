import { describe, expect, test } from "bun:test";
import { mkdtempSync, existsSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildProfile, truncateOutput } from "../src/sandbox";

describe("buildProfile", () => {
  test("allows default, denies writes except listed subpaths", () => {
    const p = buildProfile(["/tmp/ws", "/tmp/uv"]);
    expect(p).toContain("(version 1)");
    expect(p).toContain("(allow default)");
    expect(p).toContain("(deny file-write*)");
    expect(p).toContain('(subpath "/tmp/ws")');
    expect(p).toContain('(subpath "/tmp/uv")');
    // deny must come before the allow-list so the allow wins (SBPL: later rules take precedence)
    expect(p.indexOf("(deny file-write*)")).toBeLessThan(p.indexOf('(subpath "/tmp/ws")'));
  });
});

describe("truncateOutput", () => {
  test("passes short output through", () => {
    expect(truncateOutput("hello")).toBe("hello");
  });
  test("truncates long output with marker", () => {
    const out = truncateOutput("x".repeat(60_000), 50_000);
    expect(out.length).toBeLessThan(51_000);
    expect(out).toContain("[output truncated]");
  });
});

// Integration: real sandbox-exec (macOS only)
describe("sandbox-exec enforcement", () => {
  test("blocks writes outside allowed paths, permits inside", async () => {
    const ws = mkdtempSync(join(tmpdir(), "sbx-ws-"));
    const outside = mkdtempSync(join(tmpdir(), "sbx-outside-"));
    // Only ws is writable; outside is not listed.
    const profile = buildProfile([ws]);
    const profilePath = join(ws, "test.sb");
    writeFileSync(profilePath, profile);

    const inside = Bun.spawnSync(
      ["sandbox-exec", "-f", profilePath, "/bin/bash", "-c", `touch ${ws}/ok.txt`],
    );
    expect(inside.exitCode).toBe(0);
    expect(existsSync(`${ws}/ok.txt`)).toBe(true);

    const blocked = Bun.spawnSync(
      ["sandbox-exec", "-f", profilePath, "/bin/bash", "-c", `touch ${outside}/nope.txt`],
    );
    expect(blocked.exitCode).not.toBe(0);
    expect(existsSync(`${outside}/nope.txt`)).toBe(false);
  });
});
