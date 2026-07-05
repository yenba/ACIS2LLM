with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

ui_code = """                {activeSettingsTab === 'ai' && (
                  <div className="flex flex-col h-full">
                    <div className="p-6 pb-4 border-b border-border">
                      <div className="mb-6">
                        <h3 className="text-sm font-medium mb-2">API Keys</h3>
                        <p className="text-xs text-muted-foreground mb-3">
                          Stored securely in the macOS Keychain. Required for the embedded assistant.
                        </p>
                        <div className="space-y-2">
                          {keyStatus.map(({ provider, configured }) => (
                            <div key={provider} className="flex items-center gap-2">
                              <span className="w-32 text-sm">{PROVIDER_LABELS[provider] ?? provider}</span>
                              {configured ? (
                                <>
                                  <span className="text-xs text-green-600 flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3" /> Configured
                                  </span>
                                  <button
                                    onClick={() => removeKey(provider)}
                                    disabled={keyBusy === provider}
                                    className="text-xs text-destructive hover:underline ml-2"
                                  >
                                    Remove
                                  </button>
                                </>
                              ) : (
                                <>
                                  <input
                                    type="password"
                                    value={keyDrafts[provider] ?? ""}
                                    onChange={(e) => setKeyDrafts((d) => ({ ...d, [provider]: e.target.value }))}
                                    placeholder="Paste API key"
                                    className="flex-1 px-2 py-1 text-sm rounded-md border border-input bg-background"
                                  />
                                  <button
                                    onClick={() => saveKey(provider)}
                                    disabled={keyBusy === provider || !(keyDrafts[provider] || "").trim()}
                                    className="px-2 py-1 text-xs rounded-md bg-primary text-primary-foreground disabled:opacity-50"
                                  >
                                    Save
                                  </button>
                                </>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>

                      <h3 className="text-lg font-medium mb-4">Provider Selection</h3>"""

text = text.replace("""                {activeSettingsTab === 'ai' && (
                  <div className="flex flex-col h-full">
                    <div className="p-6 pb-4 border-b border-border">
                      <h3 className="text-lg font-medium mb-4">Provider Selection</h3>""", ui_code)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
