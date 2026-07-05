import { defineTool } from "@earendil-works/pi-coding-agent";
import { Type } from "@sinclair/typebox";
import { truncateOutput } from "./sandbox";

const DEFAULT_TIMEOUT_MS = 120_000;

export interface BashConfig {
  profilePath: string;
  workspaceDir: string;
  env: Record<string, string>;
}

export function createSandboxedBash(cfg: BashConfig) {
  return defineTool({
    name: "bash",
    label: "bash",
    description:
      "Execute a bash command in the sandboxed workspace. Writes are only permitted inside the workspace and Python cache directories.",
    parameters: Type.Object({
      command: Type.String({ description: "The bash command to run" }),
      timeout: Type.Optional(Type.Number({ description: "Timeout in seconds" })),
    }),
    execute: async (_toolCallId: string, params: { command: string; timeout?: number }) => {
      const timeoutMs = params.timeout ? params.timeout * 1000 : DEFAULT_TIMEOUT_MS;
      const proc = Bun.spawn(
        ["sandbox-exec", "-f", cfg.profilePath, "/bin/bash", "-c", params.command],
        { cwd: cfg.workspaceDir, env: cfg.env, stdout: "pipe", stderr: "pipe" },
      );

      const killer = setTimeout(() => proc.kill(), timeoutMs);
      const [stdout, stderr, exitCode] = await Promise.all([
        new Response(proc.stdout).text(),
        new Response(proc.stderr).text(),
        proc.exited,
      ]);
      clearTimeout(killer);

      let text = stdout;
      if (exitCode !== 0) {
        text += `${text ? "\n" : ""}[exit code ${exitCode}]\n${stderr}`;
      }
      return {
        content: [{ type: "text" as const, text: truncateOutput(text) || "(no output)" }],
        details: {},
      };
    },
  });
}