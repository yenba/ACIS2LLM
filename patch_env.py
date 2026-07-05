with open("desktop/sidecar/src/env.ts", "r") as f:
    text = f.read()

import re

search = """    UV_CACHE_DIR: join(dataDir, "uv-cache"),
    UV_PYTHON_INSTALL_DIR: join(dataDir, "uv-python"),"""
replace = """    UV_CACHE_DIR: join(dataDir, "uv-cache"),
    UV_PYTHON_INSTALL_DIR: join(dataDir, "uv-python"),
    MPLCONFIGDIR: join(dataDir, "matplotlib-cache"),"""

text = text.replace(search, replace)

with open("desktop/sidecar/src/env.ts", "w") as f:
    f.write(text)
