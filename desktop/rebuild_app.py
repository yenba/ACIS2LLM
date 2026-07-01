import re

with open("src/App.tsx", "r") as f:
    content = f.read()

# Add sidebarWidth state and resize handler
state_replacement = """  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [sidebarWidth, setSidebarWidth] = useState(256);
  
  const isResizingRef = useRef(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizingRef.current) return;
      let newWidth = e.clientX;
      if (newWidth < 200) newWidth = 200;
      if (newWidth > 600) newWidth = 600;
      setSidebarWidth(newWidth);
    };
    const handleMouseUp = () => {
      isResizingRef.current = false;
      document.body.style.cursor = 'default';
    };
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);"""

content = content.replace(
    '  const [conversations, setConversations] = useState<Conversation[]>([]);\n  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);\n  const [isSidebarOpen, setIsSidebarOpen] = useState(true);',
    state_replacement
)

# Sidebar UI
sidebar_ui = """      {/* Sidebar */}
      {isSidebarOpen && (
        <div 
          className="border-r border-border bg-card flex flex-col shrink-0 animate-in slide-in-from-left-4 relative group"
          style={{ width: sidebarWidth }}
        >
          <div className="p-4 border-b border-border flex items-center gap-2">
            <button onClick={() => setIsSidebarOpen(false)} className="p-2 -ml-2 rounded-md hover:bg-muted/50 transition-colors text-muted-foreground shrink-0">
               <PanelLeftClose className="w-5 h-5"/>
            </button>
            <button onClick={createNewChat} className="flex-1 flex items-center justify-center gap-2 bg-primary text-primary-foreground py-2 px-4 rounded-lg hover:opacity-90 transition-opacity font-medium text-sm shadow-sm">
              <Plus className="w-4 h-4" /> New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.map(c => (
               <div key={c.id} className={`group/item flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${c.id === currentConversationId ? 'bg-secondary' : 'hover:bg-muted/50'}`} onClick={() => setCurrentConversationId(c.id)}>
                 <div className="flex items-center gap-2 min-w-0 pr-2">
                   <MessageSquare className="w-4 h-4 text-muted-foreground shrink-0" />
                   <span className="text-sm truncate">{c.title}</span>
                 </div>
                 <button onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }} className="opacity-0 group-hover/item:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all shrink-0">
                   <Trash2 className="w-4 h-4" />
                 </button>
               </div>
            ))}
          </div>
          {/* Resize Handle */}
          <div 
            className="absolute top-0 right-0 w-1 h-full cursor-col-resize hover:bg-primary/50 group-hover:bg-border transition-colors z-20"
            onMouseDown={() => {
              isResizingRef.current = true;
              document.body.style.cursor = 'col-resize';
            }}
          />
        </div>
      )}"""

old_sidebar = """      {/* Sidebar */}
      {isSidebarOpen && (
        <div className="w-64 border-r border-border bg-card flex flex-col shrink-0 animate-in slide-in-from-left-4">
          <div className="p-4 border-b border-border">
            <button onClick={createNewChat} className="w-full flex items-center justify-center gap-2 bg-primary text-primary-foreground py-2 px-4 rounded-lg hover:opacity-90 transition-opacity font-medium text-sm shadow-sm">
              <Plus className="w-4 h-4" /> New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.map(c => (
               <div key={c.id} className={`group flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${c.id === currentConversationId ? 'bg-secondary' : 'hover:bg-muted/50'}`} onClick={() => setCurrentConversationId(c.id)}>
                 <div className="flex items-center gap-2 min-w-0 pr-2">
                   <MessageSquare className="w-4 h-4 text-muted-foreground shrink-0" />
                   <span className="text-sm truncate">{c.title}</span>
                 </div>
                 <button onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }} className="opacity-0 group-hover:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all shrink-0">
                   <Trash2 className="w-4 h-4" />
                 </button>
               </div>
            ))}
          </div>
        </div>
      )}"""

content = content.replace(old_sidebar, sidebar_ui)

# Main header UI
main_header = """        <div className="flex items-center gap-2">
          {!isSidebarOpen && (
            <button onClick={() => setIsSidebarOpen(true)} className="p-2 -ml-2 rounded-full hover:bg-secondary transition-colors text-muted-foreground">
              <PanelLeftOpen className="w-5 h-5" />
            </button>
          )}
          <Bot className="w-6 h-6 text-primary" />
          <h1 className="text-lg font-semibold tracking-tight">WeatherBot</h1>
        </div>"""

old_main_header = """        <div className="flex items-center gap-2">
          <button onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="p-2 -ml-2 rounded-full hover:bg-secondary transition-colors text-muted-foreground">
            {isSidebarOpen ? <PanelLeftClose className="w-5 h-5"/> : <PanelLeftOpen className="w-5 h-5" />}
          </button>
          <Bot className="w-6 h-6 text-primary" />
          <h1 className="text-lg font-semibold tracking-tight">WeatherBot</h1>
        </div>"""

content = content.replace(old_main_header, main_header)

with open("src/App.tsx", "w") as f:
    f.write(content)
