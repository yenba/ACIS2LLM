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
    case "tool_execution_start":
      return JSON.stringify({ type: "tool_execution_start", toolName: event.toolName ?? "tool" });
    case "agent_end":
      return JSON.stringify({ type: "agent_end", messages: event.messages ?? [] });
    default:
      return null;
  }
}
