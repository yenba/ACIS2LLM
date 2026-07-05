import re

with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

# 1. Update the state type
text = text.replace("useState<'general' | 'ai' | 'prompt' | 'data'>", "useState<'general' | 'providers' | 'models' | 'prompt' | 'data'>")

# 2. Update the sidebar navigation
nav_search = """                  <button
                    onClick={() => setActiveSettingsTab('ai')}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${activeSettingsTab === 'ai' ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-secondary text-foreground'}`}
                  >
                    Models
                  </button>"""
nav_replace = """                  <button
                    onClick={() => setActiveSettingsTab('providers')}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${activeSettingsTab === 'providers' ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-secondary text-foreground'}`}
                  >
                    API Keys
                  </button>
                  <button
                    onClick={() => setActiveSettingsTab('models')}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${activeSettingsTab === 'models' ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-secondary text-foreground'}`}
                  >
                    Models
                  </button>"""
text = text.replace(nav_search, nav_replace)

# 3. Split the content
# Currently:
# {activeSettingsTab === 'ai' && (
#   <div className="flex flex-col h-full">
#     <div className="p-6 pb-4 border-b border-border">
#       <div className="mb-6">
#         <h3 className="text-sm font-medium mb-2">API Keys</h3>
# ...
#         </div>
#       </div>
#
#       <h3 className="text-lg font-medium mb-4">Provider Selection</h3>

ai_tab_search = """                {activeSettingsTab === 'ai' && (
                  <div className="flex flex-col h-full">
                    <div className="p-6 pb-4 border-b border-border">
                      <div className="mb-6">
                        <h3 className="text-sm font-medium mb-2">API Keys</h3>"""

ai_tab_replace = """                {activeSettingsTab === 'providers' && (
                  <div className="flex flex-col h-full">
                    <div className="p-6 pb-4 border-b border-border">
                      <div className="mb-6">
                        <h3 className="text-lg font-medium mb-2">API Keys</h3>"""

text = text.replace(ai_tab_search, ai_tab_replace)

# We need to close the providers tab and open the models tab before "Provider Selection"
provider_selection_search = """                      </div>

                      <h3 className="text-lg font-medium mb-4">Provider Selection</h3>"""

provider_selection_replace = """                      </div>
                    </div>
                  </div>
                )}
                
                {activeSettingsTab === 'models' && (
                  <div className="flex flex-col h-full">
                    <div className="p-6 pb-4 border-b border-border">
                      <h3 className="text-lg font-medium mb-4">Provider Selection</h3>"""

text = text.replace(provider_selection_search, provider_selection_replace)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
