with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

# 1. Fix Provider Selection buttons (Make them rounded-full pills, use high-contrast modern active state)
old_fav = "`px-4 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${activeProvider === 'Favorites' ? 'bg-primary text-primary-foreground font-medium shadow-sm' : 'bg-secondary hover:bg-secondary/80 text-foreground'}`"
new_fav = "`px-4 py-1.5 rounded-full text-sm transition-colors flex items-center gap-2 ${activeProvider === 'Favorites' ? 'bg-foreground text-background font-medium shadow-sm' : 'bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground'}`"
text = text.replace(old_fav, new_fav)

old_prov = "`px-4 py-2 rounded-md text-sm transition-colors ${activeProvider === p ? 'bg-primary text-primary-foreground font-medium shadow-sm' : 'bg-secondary hover:bg-secondary/80 text-foreground'}`"
new_prov = "`px-4 py-1.5 rounded-full text-sm transition-colors ${activeProvider === p ? 'bg-foreground text-background font-medium shadow-sm' : 'bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground'}`"
text = text.replace(old_prov, new_prov)

# 2. Fix the left navigation tabs (Soften the active state so it's not a glaring primary block)
tabs = ['general', 'providers', 'models', 'prompt', 'data']
for tab in tabs:
    old_tab = f"`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${{activeSettingsTab === '{tab}' ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-secondary text-foreground'}}`"
    new_tab = f"`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${{activeSettingsTab === '{tab}' ? 'bg-secondary text-foreground font-medium shadow-sm' : 'hover:bg-secondary/50 text-muted-foreground hover:text-foreground'}}`"
    text = text.replace(old_tab, new_tab)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
