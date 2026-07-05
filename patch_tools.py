with open("desktop/sidecar/src/session.ts", "r") as f:
    text = f.read()

text = text.replace('{ tools: ["read"], customTools: [createSandboxedBash(opts.bash)] }', '{ tools: ["read", "bash"], customTools: [createSandboxedBash(opts.bash)] }')

with open("desktop/sidecar/src/session.ts", "w") as f:
    f.write(text)
