with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

# Replace the broken line
import re
text = re.sub(r'const storedSystemPrompt = localStorage.getItem\("omp-system-prompt"\) \?\? `.*?`\.trim\(\);', 'const storedSystemPrompt = localStorage.getItem("omp-system-prompt") ?? "You are a capable agent with access to ACIS weather tools.\\nWhen you finish a task and have the final correct answer, briefly review your trajectory.\\nIf you encountered errors, misunderstood the API, or found an inefficient approach, use the `bash` or `write` tools to append a short tip to `AGENTS.md` in your workspace directory so you do not make the same mistake next time.";', text, flags=re.DOTALL)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
