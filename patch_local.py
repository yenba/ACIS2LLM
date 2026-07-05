import re

with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

# Add states for local provider
hooks_search = """  const [keyStatus, setKeyStatus] = useState<KeyStatus[]>([]);
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({});
  const [keyBusy, setKeyBusy] = useState<string | null>(null);"""

hooks_replace = """  const [keyStatus, setKeyStatus] = useState<KeyStatus[]>([]);
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({});
  const [keyBusy, setKeyBusy] = useState<string | null>(null);
  
  const [localUrl, setLocalUrl] = useState<string>("");
  const [localBusy, setLocalBusy] = useState<boolean>(false);
  const [localStatusMsg, setLocalStatusMsg] = useState<{ type: 'error' | 'success', text: string } | null>(null);"""

text = text.replace(hooks_search, hooks_replace)

# Fetch local provider on mount
fetch_search = """  const refreshKeyStatus = async () => {
    try { setKeyStatus(await invoke<KeyStatus[]>("get_api_key_status")); }
    catch (e) { console.error("get_api_key_status failed", e); }
  };"""

fetch_replace = """  const refreshKeyStatus = async () => {
    try { 
      setKeyStatus(await invoke<KeyStatus[]>("get_api_key_status"));
      const url = await invoke<string | null>("get_local_provider");
      if (url) {
        setLocalUrl(url);
      }
    }
    catch (e) { console.error("get_api_key_status failed", e); }
  };"""

text = text.replace(fetch_search, fetch_replace)

# Add local provider save handlers
handlers_search = """  const removeKey = async (provider: string) => {
    setKeyBusy(provider);
    try { await invoke("delete_api_key", { provider }); await refreshKeyStatus(); }
    catch (e) { console.error("delete_api_key failed", e); }
    finally { setKeyBusy(null); }
  };"""

handlers_replace = handlers_search + """

  const saveLocalProvider = async () => {
    setLocalBusy(true);
    setLocalStatusMsg(null);
    try {
      await invoke("set_local_provider", { url: localUrl });
      setLocalStatusMsg({ type: 'success', text: localUrl ? 'Connected successfully!' : 'Provider removed.' });
      await refreshModels();
    } catch (e) {
      console.error("set_local_provider failed", e);
      setLocalStatusMsg({ type: 'error', text: String(e) });
    } finally {
      setLocalBusy(false);
    }
  };"""

text = text.replace(handlers_search, handlers_replace)

# Add to UI under API Keys
ui_search = """                          ))}
                        </div>
                      </div>"""

ui_replace = """                          ))}
                        </div>
                      </div>

                      <div className="mb-6">
                        <h3 className="text-lg font-medium mb-2">Local Provider</h3>
                        <p className="text-xs text-muted-foreground mb-3">
                          Connect to an OpenAI-compatible local API (e.g. llama.cpp, LM Studio, Ollama). Point this to the base URL that exposes <code className="bg-muted px-1 rounded">/models</code> (typically <code className="bg-muted px-1 rounded">http://localhost:11434/v1</code> or <code className="bg-muted px-1 rounded">http://localhost:8080/v1</code>).
                        </p>
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center gap-2">
                            <input
                              type="text"
                              value={localUrl}
                              onChange={(e) => setLocalUrl(e.target.value)}
                              placeholder="http://localhost:11434/v1"
                              className="flex-1 px-2 py-1 text-sm rounded-md border border-input bg-background"
                            />
                            <button
                              onClick={saveLocalProvider}
                              disabled={localBusy}
                              className="px-3 py-1 text-xs rounded-md bg-primary text-primary-foreground disabled:opacity-50"
                            >
                              {localUrl ? "Connect" : "Remove"}
                            </button>
                          </div>
                          {localStatusMsg && (
                            <p className={`text-xs ${localStatusMsg.type === 'error' ? 'text-destructive' : 'text-green-600'}`}>
                              {localStatusMsg.text}
                            </p>
                          )}
                        </div>
                      </div>"""

text = text.replace(ui_search, ui_replace)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
