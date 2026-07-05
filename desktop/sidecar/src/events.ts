interface PiEvent {
  type: string;
  [key: string]: unknown;
}

/**
 * Map pi session events to the JSON-line protocol lib.rs parses.
 * Only two event types are consumed by the Rust side; everything else is dropped.
 */
export function serializeEvent(event: PiEvent): string | null {
  switch (event.type) {
    case "tool_execution_start": {
      const toolName = (event.toolName as string) ?? "tool";
      let intent = "";
      if (toolName === "bash" && event.args && typeof event.args === "object") {
        const args = event.args as Record<string, unknown>;
        if (typeof args.command === "string") {
          const cmd = args.command;
          if (cmd.includes("AGENTS.md")) {
            intent = "Updating agent memory…";
          } else if (cmd.includes("uv run") || cmd.includes("python")) {
            intent = "Running Python script…";
          } else if (cmd.startsWith("ls") || cmd.startsWith("find")) {
            intent = "Searching files…";
          } else {
            intent = "Executing command…";
          }
        }
      } else if (toolName === "read" && event.args && typeof event.args === "object") {
        const args = event.args as Record<string, unknown>;
        if (typeof args.path === "string") {
          const parts = args.path.split("/");
          const name = parts[parts.length - 1];
          intent = `Reading ${name}…`;
        }
      } else if ((toolName === "edit" || toolName === "write") && event.args && typeof event.args === "object") {
        const args = event.args as Record<string, unknown>;
        if (typeof args.path === "string" && args.path.includes("AGENTS.md")) {
          intent = "Updating agent memory…";
        } else {
          intent = "Writing file…";
        }
      }

      return JSON.stringify({ 
        type: "tool_execution_start", 
        toolName,
        ...(intent ? { intent } : {})
      });
    }
    case "agent_end":
      return JSON.stringify({ type: "agent_end", messages: event.messages ?? [] });
    default:
      return null;
  }
}
