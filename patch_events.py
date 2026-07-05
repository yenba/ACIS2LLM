with open("desktop/sidecar/src/events.ts", "r") as f:
    text = f.read()

import re

search_bash = """          if (cmd.includes("uv run") || cmd.includes("python")) {"""
replace_bash = """          if (cmd.includes("AGENTS.md")) {
            intent = "Updating agent memory…";
          } else if (cmd.includes("uv run") || cmd.includes("python")) {"""
text = text.replace(search_bash, replace_bash)

search_write = """      } else if (toolName === "edit" || toolName === "write") {
        intent = "Writing file…";
      }"""
replace_write = """      } else if ((toolName === "edit" || toolName === "write") && event.args && typeof event.args === "object") {
        const args = event.args as Record<string, unknown>;
        if (typeof args.path === "string" && args.path.includes("AGENTS.md")) {
          intent = "Updating agent memory…";
        } else {
          intent = "Writing file…";
        }
      }"""
text = text.replace(search_write, replace_write)

with open("desktop/sidecar/src/events.ts", "w") as f:
    f.write(text)
