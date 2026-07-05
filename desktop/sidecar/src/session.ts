import {
  AuthStorage,
  ModelRegistry,
  SessionManager,
  createAgentSession,
} from "@earendil-works/pi-coding-agent";
import { join } from "node:path";
import { createSandboxedBash, type BashConfig } from "./bash-tool";

export interface SessionOptions {
  withTools: boolean;
  bash?: BashConfig;
  cwd?: string;
  agentDir?: string;
}

export async function buildSession(modelSelector: string, opts: SessionOptions) {
  const authStorage = AuthStorage.create();
  const modelRegistry = ModelRegistry.create(authStorage);

  const slash = modelSelector.indexOf("/");
  if (slash < 1) {
    throw new Error(`model not found: ${modelSelector} (expected provider/model-id)`);
  }
  const provider = modelSelector.slice(0, slash);
  const modelId = modelSelector.slice(slash + 1);
  const model = modelRegistry.find(provider, modelId);
  if (!model) {
    throw new Error(`model not found: ${modelSelector}`);
  }

  const { session } = await createAgentSession({
    authStorage,
    modelRegistry,
    model,
    cwd: opts.cwd,
    agentDir: opts.agentDir,
    sessionManager: opts.withTools ? SessionManager.create(opts.cwd ?? process.cwd(), opts.agentDir ? join(opts.agentDir, "sessions") : undefined) : SessionManager.inMemory(),
    ...(opts.withTools
      ? opts.bash
        ? { tools: ["read", "bash"], customTools: [createSandboxedBash(opts.bash)] }
        : { tools: ["read", "bash"] }
      : { noTools: "all" as const }),
  });
  return session;
}