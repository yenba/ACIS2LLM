import re

with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

replacement = r'const storedSystemPrompt = localStorage.getItem("omp-system-prompt") ?? `You are a capable agent with access to ACIS weather tools.\nImportant: Your bash tool automatically executes inside the workspace directory. Do not use cd to navigate there.\n\nBefore delivering your final answer, briefly review your trajectory.\nIf you encountered errors, misunderstood the API, or found an inefficient approach, use the \\`bash\\` or \\`write\\` tools to append a short tip to \\`AGENTS.md\\` in your workspace directory so you do not make the same mistake next time.\nAfter updating the file (or if no update is needed), present your final answer.`;'

text = re.sub(r'const storedSystemPrompt = localStorage.getItem\("omp-system-prompt"\) \?\? `.*?`;', replacement, text, flags=re.DOTALL)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
