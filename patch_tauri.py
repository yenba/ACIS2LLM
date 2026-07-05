import json
with open("desktop/src-tauri/tauri.conf.json", "r") as f:
    conf = json.load(f)

conf["bundle"]["externalBin"] = ["binaries/pi-sidecar"]
conf["bundle"]["resources"] = {
    "resources/uv/uv": "uv/uv",
    "../../skills/acis-weather": "skills/acis-weather"
}

with open("desktop/src-tauri/tauri.conf.json", "w") as f:
    json.dump(conf, f, indent=2)
