with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

# Fix Provider Selection buttons (Make them subtle like standard macOS segmented controls)
old_fav = "`px-4 py-1.5 rounded-full text-sm transition-colors flex items-center gap-2 ${activeProvider === 'Favorites' ? 'bg-foreground text-background font-medium shadow-sm' : 'bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground'}`"
new_fav = "`px-4 py-1.5 rounded-full text-sm transition-colors flex items-center gap-2 ${activeProvider === 'Favorites' ? 'bg-secondary text-foreground font-medium shadow-sm ring-1 ring-border/50' : 'hover:bg-secondary/50 text-muted-foreground hover:text-foreground'}`"
text = text.replace(old_fav, new_fav)

old_prov = "`px-4 py-1.5 rounded-full text-sm transition-colors ${activeProvider === p ? 'bg-foreground text-background font-medium shadow-sm' : 'bg-secondary hover:bg-secondary/80 text-muted-foreground hover:text-foreground'}`"
new_prov = "`px-4 py-1.5 rounded-full text-sm transition-colors ${activeProvider === p ? 'bg-secondary text-foreground font-medium shadow-sm ring-1 ring-border/50' : 'hover:bg-secondary/50 text-muted-foreground hover:text-foreground'}`"
text = text.replace(old_prov, new_prov)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
