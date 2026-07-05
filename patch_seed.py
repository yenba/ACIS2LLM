import re

with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

# 1. Add promptSeed state
state_search = "  const [systemPrompt, setSystemPrompt] = useState<string>(\"\");"
state_replace = "  const [systemPrompt, setSystemPrompt] = useState<string>(\"\");\n  const [promptSeed, setPromptSeed] = useState(() => Date.now().toString());"
text = text.replace(state_search, state_replace)

# 2. Update createNewChat
new_chat_search = """  function createNewChat() {
    setCurrentConversationId(null);
  }"""
new_chat_replace = """  function createNewChat() {
    setCurrentConversationId(null);
    setPromptSeed(Date.now().toString());
  }"""
text = text.replace(new_chat_search, new_chat_replace)

# 3. Update suggestedPrompts useMemo
seed_search = """  const suggestedPrompts = useMemo(() => {
    const cities = favoriteCities.length > 0 ? favoriteCities : DEFAULT_CITIES;
    // Use a seeded shuffle based on today's date so prompts are stable
    // within a session but rotate daily
    const seed = new Date().toDateString();"""
seed_replace = """  const suggestedPrompts = useMemo(() => {
    const cities = favoriteCities.length > 0 ? favoriteCities : DEFAULT_CITIES;
    const seed = promptSeed;"""
text = text.replace(seed_search, seed_replace)

dep_search = "  }, [favoriteCities]);"
dep_replace = "  }, [favoriteCities, promptSeed]);"
text = text.replace(dep_search, dep_replace)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
