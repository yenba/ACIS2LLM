with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

hooks_code = """
  const [activeSettingsTab, setActiveSettingsTab] = useState<'general' | 'ai' | 'prompt' | 'data'>('general');
  
  interface KeyStatus { provider: string; configured: boolean; }
  
  const PROVIDER_LABELS: Record<string, string> = {
    anthropic: "Anthropic", openai: "OpenAI", google: "Google (Gemini)",
    xai: "xAI", groq: "Groq", openrouter: "OpenRouter",
  };
  
  const [keyStatus, setKeyStatus] = useState<KeyStatus[]>([]);
  const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({});
  const [keyBusy, setKeyBusy] = useState<string | null>(null);
  
  const refreshKeyStatus = async () => {
    try { setKeyStatus(await invoke<KeyStatus[]>("get_api_key_status")); }
    catch (e) { console.error("get_api_key_status failed", e); }
  };
  
  useEffect(() => { if (isSettingsOpen) refreshKeyStatus(); }, [isSettingsOpen]);
  
  const saveKey = async (provider: string) => {
    const key = (keyDrafts[provider] || "").trim();
    if (!key) return;
    setKeyBusy(provider);
    try {
      await invoke("set_api_key", { provider, key });
      setKeyDrafts((d) => ({ ...d, [provider]: "" }));
      await refreshKeyStatus();
    } catch (e) { console.error("set_api_key failed", e); }
    finally { setKeyBusy(null); }
  };
  
  const removeKey = async (provider: string) => {
    setKeyBusy(provider);
    try { await invoke("delete_api_key", { provider }); await refreshKeyStatus(); }
    catch (e) { console.error("delete_api_key failed", e); }
    finally { setKeyBusy(null); }
  };"""

text = text.replace("  const [activeSettingsTab, setActiveSettingsTab] = useState<'general' | 'ai' | 'prompt' | 'data'>('general');", hooks_code)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
