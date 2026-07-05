import { describe, expect, test } from "bun:test";
import { serializeEvent } from "../src/events";

describe("serializeEvent", () => {
  test("forwards tool_execution_start with toolName and intent", () => {
    const line = serializeEvent({ type: "tool_execution_start", toolCallId: "t1", toolName: "bash", args: { command: "ls" } });
    expect(JSON.parse(line!)).toEqual({ type: "tool_execution_start", toolName: "bash", intent: "Searching files…" });
  });

  test("forwards agent_end with messages", () => {
    const messages = [
      { role: "assistant", content: [{ type: "text", text: "It rained 3 inches." }] },
    ];
    const line = serializeEvent({ type: "agent_end", messages });
    const parsed = JSON.parse(line!);
    expect(parsed.type).toBe("agent_end");
    expect(parsed.messages[0].content[0].text).toBe("It rained 3 inches.");
  });

  test("drops unconsumed event types", () => {
    expect(serializeEvent({ type: "message_update" })).toBeNull();
    expect(serializeEvent({ type: "turn_start" })).toBeNull();
  });

  test("drops non-serializable payload fields safely", () => {
    // agent_end events may carry extra fields; only type + messages are emitted.
    const line = serializeEvent({ type: "agent_end", messages: [], internal: () => {} });
    expect(JSON.parse(line!)).toEqual({ type: "agent_end", messages: [] });
  });

  test("omits intent for unknown tool args", () => {
    const line = serializeEvent({ type: "tool_execution_start", toolCallId: "t2", toolName: "bash", args: {} });
    expect(JSON.parse(line!)).toEqual({ type: "tool_execution_start", toolName: "bash" });
  });

  test("derives intent for edit on AGENTS.md", () => {
    const line = serializeEvent({ type: "tool_execution_start", toolCallId: "t3", toolName: "edit", args: { path: "workspace/AGENTS.md" } });
    expect(JSON.parse(line!)).toEqual({ type: "tool_execution_start", toolName: "edit", intent: "Updating agent memory…" });
  });
});
