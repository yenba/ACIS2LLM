import re

with open("desktop/sidecar/src/session.ts", "r") as f:
    text = f.read()

import_search = "import { createSandboxedBash, type BashConfig } from \"./bash-tool\";"
import_replace = "import { join } from \"node:path\";\nimport { createSandboxedBash, type BashConfig } from \"./bash-tool\";"

text = text.replace(import_search, import_replace)

session_search = "sessionManager: SessionManager.inMemory(),"
session_replace = 'sessionManager: SessionManager.create(opts.cwd ?? process.cwd(), opts.agentDir ? join(opts.agentDir, "sessions") : undefined),'

text = text.replace(session_search, session_replace)

with open("desktop/sidecar/src/session.ts", "w") as f:
    f.write(text)
