import { serializeEvent } from "./events";
import { buildSession } from "./session";

export async function runJson(prompt: string, model: string): Promise<void> {
  const session = await buildSession(model, { withTools: true });
  session.subscribe((event: any) => {
    const line = serializeEvent(event);
    if (line) console.log(line);
  });
  await session.prompt(prompt);
}

export async function runText(prompt: string, model: string): Promise<void> {
  const session = await buildSession(model, { withTools: false });
  await session.prompt(prompt);
  // AgentSession exposes a built-in helper for this extraction (SDK 0.80.3);
  // the brief's manual `session.agent.state.messages` walk isn't needed.
  const text = session.getLastAssistantText();
  if (text) {
    console.log(text.trim());
    return;
  }
  throw new Error("model returned no text");
}
