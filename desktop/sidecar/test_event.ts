import { AuthStorage, ModelRegistry, SessionManager, createAgentSession } from "@earendil-works/pi-coding-agent";

async function main() {
  const authStorage = AuthStorage.create();
  const modelRegistry = ModelRegistry.create(authStorage);
  const model = modelRegistry.find("local", "llama3.1:8b");
  if (!model) return console.error("No model");

  const { session } = await createAgentSession({
    authStorage, modelRegistry, model,
    sessionManager: SessionManager.inMemory(),
    tools: ["read", "bash"],
  });

  session.subscribe((event: any) => {
    if (event.type === "tool_execution_start") {
      console.log("TOOL EVENT:", JSON.stringify(event));
    }
  });

  await session.prompt("Run a quick bash command to echo hello.");
}
main();
