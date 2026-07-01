import re

with open("src/App.tsx", "r") as f:
    content = f.read()

# 1. Update imports
new_imports = """import { Send, Settings, Bot, User, Star, CheckCircle, X, Check, PanelLeftClose, PanelLeftOpen, MessageSquare, Plus, Trash2, Square } from "lucide-react";"""
content = content.replace(
    'import { Send, Settings, Bot, User, Star, CheckCircle, X, Check, PanelLeftClose, PanelLeftOpen, MessageSquare, Plus, Trash2 } from "lucide-react";',
    new_imports
)

# 2. Add Stop generating function
stop_fn = """  async function handleStop() {
    setIsProcessing(false);
    try {
      await invoke("stop_omp");
    } catch (e) {
      console.error(e);
    }
  }

  function handleSuggestedPrompt(prompt: string) {"""

content = content.replace("  function handleSuggestedPrompt(prompt: string) {", stop_fn)

# 3. Add stop button UI
old_send_btn = """              <button
                type="submit"
                disabled={!input.trim() || isProcessing}
                className="absolute right-2 top-2 p-2 bg-muted text-muted-foreground rounded-full hover:bg-primary hover:text-primary-foreground transition-colors disabled:opacity-50"
              >
                <Send className="w-5 h-5" />
              </button>"""

new_send_btn = """              {isProcessing ? (
                <button
                  type="button"
                  onClick={handleStop}
                  className="absolute right-2 top-2 p-2 bg-destructive text-destructive-foreground rounded-full hover:bg-destructive/90 transition-colors"
                >
                  <Square className="w-5 h-5 fill-current" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={!input.trim()}
                  className="absolute right-2 top-2 p-2 bg-muted text-muted-foreground rounded-full hover:bg-primary hover:text-primary-foreground transition-colors disabled:opacity-50"
                >
                  <Send className="w-5 h-5" />
                </button>
              )}"""

content = content.replace(old_send_btn, new_send_btn)

# 4. Grouped conversations
grouped_conversations = """  const groupedConversations = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const weekAgoStart = todayStart - 7 * 24 * 60 * 60 * 1000;
    
    const groups: { today: typeof conversations, week: typeof conversations, older: typeof conversations } = { today: [], week: [], older: [] };
    
    conversations.forEach(c => {
      if (c.updatedAt >= todayStart) groups.today.push(c);
      else if (c.updatedAt >= weekAgoStart) groups.week.push(c);
      else groups.older.push(c);
    });
    return groups;
  }, [conversations]);

  const renderConversationList = (list: typeof conversations, title: string) => {
    if (list.length === 0) return null;
    return (
      <div className="mb-4">
        <h3 className="px-3 mb-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">{title}</h3>
        <div className="space-y-1">
          {list.map(c => (
             <div key={c.id} className={`group/item flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${c.id === currentConversationId ? 'bg-secondary' : 'hover:bg-muted/50'}`} onClick={() => setCurrentConversationId(c.id)}>
               <div className="flex items-start gap-2 min-w-0 pr-2 pt-1">
                 <MessageSquare className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                 <div className="flex flex-col min-w-0 gap-1">
                   <span className="text-sm line-clamp-2 leading-snug">{c.title}</span>
                   <span className="text-[10px] text-muted-foreground/50 font-medium tracking-wide uppercase">
                     {new Date(c.updatedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                   </span>
                 </div>
               </div>
               <button onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }} className="opacity-0 group-hover/item:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all shrink-0">
                 <Trash2 className="w-4 h-4" />
               </button>
             </div>
          ))}
        </div>
      </div>
    );
  };"""

old_sidebar_list = """          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {conversations.map(c => (
               <div key={c.id} className={`group/item flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${c.id === currentConversationId ? 'bg-secondary' : 'hover:bg-muted/50'}`} onClick={() => setCurrentConversationId(c.id)}>
                 <div className="flex items-start gap-2 min-w-0 pr-2 pt-1">
                   <MessageSquare className="w-4 h-4 text-muted-foreground shrink-0 mt-0.5" />
                   <div className="flex flex-col min-w-0 gap-1">
                     <span className="text-sm line-clamp-2 leading-snug">{c.title}</span>
                     <span className="text-[10px] text-muted-foreground/50 font-medium tracking-wide uppercase">
                       {new Date(c.updatedAt).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
                     </span>
                   </div>
                 </div>
                 <button onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }} className="opacity-0 group-hover/item:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all shrink-0">
                   <Trash2 className="w-4 h-4" />
                 </button>
               </div>
            ))}
          </div>"""

new_sidebar_list = """          <div className="flex-1 overflow-y-auto p-2">
            {renderConversationList(groupedConversations.today, "Today")}
            {renderConversationList(groupedConversations.week, "Previous 7 Days")}
            {renderConversationList(groupedConversations.older, "Older")}
          </div>"""

content = content.replace("  const activeConversation = conversations.find(c => c.id === currentConversationId);", grouped_conversations + "\n\n  const activeConversation = conversations.find(c => c.id === currentConversationId);")
content = content.replace(old_sidebar_list, new_sidebar_list)

with open("src/App.tsx", "w") as f:
    f.write(content)
