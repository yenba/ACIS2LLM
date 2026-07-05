with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

default_prompt = """You are a capable agent with access to ACIS weather tools.
When you finish a task and have the final correct answer, briefly review your trajectory.
If you encountered errors, misunderstood the API, or found an inefficient approach, use the `bash` or `write` tools to append a short tip to `AGENTS.md` in your workspace directory so you do not make the same mistake next time.
"""

search = 'const storedSystemPrompt = localStorage.getItem("omp-system-prompt") || "";'
replace = f'const storedSystemPrompt = localStorage.getItem("omp-system-prompt") ?? `{default_prompt}`.trim();'

text = text.replace(search, replace)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
