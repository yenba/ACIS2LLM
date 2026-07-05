import re

with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

extract_search = """    async function fetchModels() {
      try {
        const jsonStr: string = await invoke("get_models");
        const parsed = JSON.parse(jsonStr);
        const fetchedModels: Model[] = parsed.models || [];
        setModels(fetchedModels);
        
        if (fetchedModels.length > 0 && !storedSelected) {
          setSelectedModel(fetchedModels[0].id);
        }
      } catch (e: any) {
        console.error("Failed to fetch models", e);
        setModelsError(String(e));
      }
    }
    fetchModels();"""

extract_replace = "    fetchModels();"

text = text.replace(extract_search, extract_replace)

add_search = """  const refreshKeyStatus = async () => {"""
add_replace = """  const fetchModels = async () => {
    try {
      const jsonStr: string = await invoke("get_models");
      const parsed = JSON.parse(jsonStr);
      const fetchedModels: Model[] = parsed.models || [];
      setModels(fetchedModels);
      
      const storedSelected = localStorage.getItem("omp-model");
      if (fetchedModels.length > 0 && !storedSelected) {
        setSelectedModel(fetchedModels[0].id);
      }
    } catch (e: any) {
      console.error("Failed to fetch models", e);
      setModelsError(String(e));
    }
  };

  const refreshKeyStatus = async () => {"""

text = text.replace(add_search, add_replace)

# Fix `await refreshModels();` to `await fetchModels();`
text = text.replace("await refreshModels();", "await fetchModels();")

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
