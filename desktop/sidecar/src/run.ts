import { initEnv } from "./env";
import { serializeEvent } from "./events";
import { buildSession } from "./session";

export async function runJson(prompt: string, model: string): Promise<void> {
  const env = initEnv();
  const session = await buildSession(model, {
    withTools: true,
    cwd: env.workspaceDir,
    agentDir: env.agentDir,
    bash: { profilePath: env.profilePath, workspaceDir: env.workspaceDir, env: env.bashEnv },
  });
  session.subscribe((event: unknown) => {
    // We treat event as a generic record with a type field for serializeEvent.
    const e = event as { type: string; [k: string]: unknown };
    const line = serializeEvent(e);
    if (line) console.log(line);
  });
  await session.prompt(prompt);
}

export async function runText(prompt: string, model: string): Promise<void> {
  const session = await buildSession(model, { withTools: false });
  await session.prompt(prompt);
  const text = session.getLastAssistantText();
  if (text) {
    console.log(text.trim());
    return;
  }
  throw new Error("model returned no text");
}