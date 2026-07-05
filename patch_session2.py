import re

with open("desktop/sidecar/src/session.ts", "r") as f:
    text = f.read()

text = text.replace('sessionManager: SessionManager.create(opts.cwd ?? process.cwd(), opts.agentDir ? join(opts.agentDir, "sessions") : undefined),', 'sessionManager: opts.withTools ? SessionManager.create(opts.cwd ?? process.cwd(), opts.agentDir ? join(opts.agentDir, "sessions") : undefined) : SessionManager.inMemory(),')

with open("desktop/sidecar/src/session.ts", "w") as f:
    f.write(text)
