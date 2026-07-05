import json
with open("desktop/package.json", "r") as f:
    pkg = json.load(f)

pkg["scripts"]["sidecar:build"] = "bash scripts/fetch-uv.sh && cd sidecar && bun install && bun run compile"
pkg["scripts"]["release"] = "npm run sidecar:build && node scripts/release.js"

with open("desktop/package.json", "w") as f:
    json.dump(pkg, f, indent=2)
