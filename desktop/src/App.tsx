import { useState, useEffect, useRef, useMemo } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen } from "@tauri-apps/api/event";
import { Send, Settings, User, Star, CheckCircle, X, Check, Plus, Trash2, Square, ChevronDown, CloudSun, Download, Copy, RefreshCw, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { US_CITIES } from "./cities";
import "./App.css";

type Conversation = {
  id: string;
  title: string;
  updatedAt: number;
  messages: Message[];
};

type Message = {
  role: "user" | "bot";
  content: string;
  stats?: {
    ttft: number;
    tokens: number;
    totalTime: number;
  };
};

type Model = {
  id: string;
  selector?: string;
  name?: string;
  provider?: string;
  contextWindow?: number;
};

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    const stored = localStorage.getItem("omp-conversations");
    return stored ? JSON.parse(stored) : [];
  });
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(() => {
    const stored = localStorage.getItem("omp-conversations");
    if (stored) {
      const convos = JSON.parse(stored);
      if (convos.length > 0) return convos[0].id;
    }
    return null;
  });
  const [sidebarWidth, setSidebarWidth] = useState(280);
  
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
  }, []);
  
  const currentConversationIdRef = useRef<string | null>(null);
  useEffect(() => {
    currentConversationIdRef.current = currentConversationId;
  }, [currentConversationId]);
  
  useEffect(() => {
    localStorage.setItem("omp-conversations", JSON.stringify(conversations));
  }, [conversations]);
  
  const currentConversation = conversations.find(c => c.id === currentConversationId);
  const messages = currentConversation?.messages || [];
  const [input, setInput] = useState("");
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [defaultModel, setDefaultModel] = useState<string>("");
  const [favorites, setFavorites] = useState<string[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  
  const [activeProvider, setActiveProvider] = useState<string>("");
  const [systemPrompt, setSystemPrompt] = useState<string>("");
  
  const [useRelativeDates, setUseRelativeDates] = useState(() => localStorage.getItem("useRelativeDates") === "true");
  const [activeSettingsTab, setActiveSettingsTab] = useState<'general' | 'ai' | 'prompt' | 'data'>('general');
  const [favoriteCities, setFavoriteCities] = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem("favoriteCities") || "[]"); } catch { return []; }
  });
  const [newCityInput, setNewCityInput] = useState("");
  const [showCitySuggestions, setShowCitySuggestions] = useState(false);
  const [selectedSuggestionIdx, setSelectedSuggestionIdx] = useState(-1);

  const citySuggestions = useMemo(() => {
    if (newCityInput.trim().length < 2) return [];
    const q = newCityInput.toLowerCase();
    return US_CITIES.filter(c => c.toLowerCase().includes(q) && !favoriteCities.includes(c)).slice(0, 6);
  }, [newCityInput, favoriteCities]);

  const STATE_MAP: Record<string, string> = {
    'alabama': 'AL', 'alaska': 'AK', 'arizona': 'AZ', 'arkansas': 'AR', 'california': 'CA',
    'colorado': 'CO', 'connecticut': 'CT', 'delaware': 'DE', 'florida': 'FL', 'georgia': 'GA',
    'hawaii': 'HI', 'idaho': 'ID', 'illinois': 'IL', 'indiana': 'IN', 'iowa': 'IA',
    'kansas': 'KS', 'kentucky': 'KY', 'louisiana': 'LA', 'maine': 'ME', 'maryland': 'MD',
    'massachusetts': 'MA', 'michigan': 'MI', 'minnesota': 'MN', 'mississippi': 'MS', 'missouri': 'MO',
    'montana': 'MT', 'nebraska': 'NE', 'nevada': 'NV', 'new hampshire': 'NH', 'new jersey': 'NJ',
    'new mexico': 'NM', 'new york': 'NY', 'north carolina': 'NC', 'north dakota': 'ND', 'ohio': 'OH',
    'oklahoma': 'OK', 'oregon': 'OR', 'pennsylvania': 'PA', 'rhode island': 'RI', 'south carolina': 'SC',
    'south dakota': 'SD', 'tennessee': 'TN', 'texas': 'TX', 'utah': 'UT', 'vermont': 'VT',
    'virginia': 'VA', 'washington': 'WA', 'west virginia': 'WV', 'wisconsin': 'WI', 'wyoming': 'WY',
    'district of columbia': 'DC',
  };

  const formatCityName = (raw: string): string => {
    // Split on comma or last space to find city vs state
    let city: string, state: string;
    if (raw.includes(',')) {
      const parts = raw.split(',').map(s => s.trim());
      city = parts[0];
      state = parts.slice(1).join(',').trim();
    } else {
      // Try to detect state as last word(s)
      const words = raw.trim().split(/\s+/);
      // Check if last 2 words form a state name
      if (words.length >= 3 && STATE_MAP[(words.slice(-2).join(' ')).toLowerCase()]) {
        state = words.slice(-2).join(' ');
        city = words.slice(0, -2).join(' ');
      } else if (words.length >= 2) {
        state = words[words.length - 1];
        city = words.slice(0, -1).join(' ');
      } else {
        return raw.trim().split(/\s+/).map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
      }
    }
    // Title-case the city
    const titleCity = city.trim().split(/\s+/).map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(' ');
    // Resolve state: full name -> abbreviation, or uppercase if already short
    const stateLower = state.toLowerCase().trim();
    const stateAbbr = STATE_MAP[stateLower] || (state.trim().length === 2 ? state.trim().toUpperCase() : state.trim());
    return `${titleCity}, ${stateAbbr}`;
  };

  // Auto-format city names in the background
  useEffect(() => {
    if (favoriteCities.length === 0) return;
    const timer = setTimeout(() => {
      const formatted = favoriteCities.map(formatCityName);
      const changed = formatted.some((f, i) => f !== favoriteCities[i]);
      if (changed) {
        setFavoriteCities(formatted);
        localStorage.setItem("favoriteCities", JSON.stringify(formatted));
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [favoriteCities]);
  
  const handleToggleRelativeDates = () => {
    const newVal = !useRelativeDates;
    setUseRelativeDates(newVal);
    localStorage.setItem("useRelativeDates", newVal.toString());
  };

  const startTimeRef = useRef<number>(0);
  const ttftRef = useRef<number | null>(null);
  const tokensRef = useRef<number>(0);
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialization
  useEffect(() => {
    // Load local storage preferences
    const storedFavs = JSON.parse(localStorage.getItem("omp-favorites") || "[]");
    setFavorites(storedFavs);
    
    const storedDefault = localStorage.getItem("omp-default-model") || "";
    setDefaultModel(storedDefault);
    
    const storedSelected = localStorage.getItem("omp-model") || storedDefault;
    setSelectedModel(storedSelected);
    
    const storedSystemPrompt = localStorage.getItem("omp-system-prompt") || "";
    setSystemPrompt(storedSystemPrompt);

    async function fetchModels() {
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
    fetchModels();

    const unlistenOutput = listen<string>("omp-output", (event) => {
      if (ttftRef.current === null) {
        ttftRef.current = Date.now() - startTimeRef.current;
      }
      tokensRef.current += 1;
      
      setConversations((prev) => {
        return prev.map(conv => {
          if (conv.id === currentConversationIdRef.current) {
            const lastMsg = conv.messages[conv.messages.length - 1];
            if (lastMsg && lastMsg.role === "bot") {
              return {
                ...conv,
                messages: [
                  ...conv.messages.slice(0, -1),
                  { ...lastMsg, content: lastMsg.content + event.payload }
                ],
                updatedAt: Date.now()
              };
            } else {
              return {
                ...conv,
                messages: [...conv.messages, { role: "bot", content: event.payload }],
                updatedAt: Date.now()
              };
            }
          }
          return conv;
        });
      });
    });

    const unlistenDone = listen("omp-done", () => {
      setIsProcessing(false);
      const totalTime = Date.now() - startTimeRef.current;
      setConversations((prev) => {
        return prev.map(conv => {
          if (conv.id === currentConversationIdRef.current) {
            const lastMsg = conv.messages[conv.messages.length - 1];
            if (lastMsg && lastMsg.role === "bot") {
              return {
                ...conv,
                messages: [
                  ...conv.messages.slice(0, -1),
                  { 
                    ...lastMsg, 
                    stats: {
                      ttft: ttftRef.current || 0,
                      tokens: tokensRef.current,
                      totalTime
                    }
                  }
                ]
              };
            }
          }
          return conv;
        });
      });
    });

    return () => {
      unlistenOutput.then((f) => f());
      unlistenDone.then((f) => f());
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Derived state for Settings Modal
  const providers = useMemo(() => {
    const pSet = new Set<string>();
    models.forEach(m => {
      if (m.provider) pSet.add(m.provider);
      else pSet.add("unknown");
    });
    return Array.from(pSet).sort();
  }, [models]);

  useEffect(() => {
    if (providers.length > 0 && !activeProvider) {
      setActiveProvider(providers[0]);
    }
  }, [providers, activeProvider]);

  const activeModels = useMemo(() => {
    if (activeProvider === 'Favorites') {
      return models.filter(m => favorites.includes(m.id));
    }
    return models.filter(m => (m.provider || "unknown") === activeProvider);
  }, [models, activeProvider, favorites]);

  // Derived state for Quick Picker
  const quickPickerModels = useMemo(() => {
    const list = models.filter(m => favorites.includes(m.id) || m.id === selectedModel);
    // ensure unique
    return Array.from(new Map(list.map(item => [item.id, item])).values());
  }, [models, favorites, selectedModel]);

  // Actions
  const handleSelectModel = (id: string) => {
    setSelectedModel(id);
    localStorage.setItem("omp-model", id);
  };

  const handleSetDefault = (id: string) => {
    setDefaultModel(id);
    localStorage.setItem("omp-default-model", id);
    if (!selectedModel) handleSelectModel(id);
  };

  const toggleFavorite = (id: string) => {
    setFavorites(prev => {
      let next;
      if (prev.includes(id)) {
        next = prev.filter(f => f !== id);
      } else {
        next = [...prev, id];
      }
      localStorage.setItem("omp-favorites", JSON.stringify(next));
      return next;
    });
  };

  function createNewChat() {
    setCurrentConversationId(null);
  }
  
  function deleteChat(id: string) {
    setConversations(prev => prev.filter(c => c.id !== id));
    if (currentConversationId === id) setCurrentConversationId(null);
  }

  const handleSystemPromptChange = (val: string) => {
    setSystemPrompt(val);
    localStorage.setItem("omp-system-prompt", val);
  };

  const copyMessage = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(idx);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const regenerateResponse = () => {
    if (messages.length < 2 || isProcessing) return;
    const lastUserMsg = messages[messages.length - 2];
    if (lastUserMsg.role !== "user") return;
    
    setConversations(prev => prev.map(c => {
      if (c.id === currentConversationId) {
        return { ...c, messages: c.messages.slice(0, -1) };
      }
      return c;
    }));
    
    setTimeout(() => {
      // Small timeout to allow state to flush before triggering send
      sendMessage(lastUserMsg.content, true);
    }, 10);
  };

  const exportChat = () => {
    if (!currentConversation) return;
    let md = `# ${currentConversation.title}\n\n`;
    currentConversation.messages.forEach(m => {
      md += `**${m.role === 'user' ? 'User' : 'ACIS Chat'}**:\n${m.content}\n\n---\n\n`;
    });
    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const safeTitle = currentConversation.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
    const dateStr = new Date().toISOString().split('T')[0];
    a.download = `acis-${safeTitle ? safeTitle + '-' : ''}${dateStr}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const PROMPT_TEMPLATES = [
    (city: string) => `Was this June one of the wettest Junes ever in ${city}?`,
    (city: string) => `How hot was last July in ${city} compared to normal?`,
    (city: string) => `What's the rainiest month on record for ${city}?`,
    (city: string) => `What was the highest temperature recorded in ${city} last summer?`,
    (city: string) => `How many days did it rain in ${city} last January?`,
    (city: string) => `Is ${city} drier than usual this year?`,
    (city: string) => `What's the hottest day on record for ${city}?`,
    (city: string) => `Has it ever snowed in ${city}?`,
    (city: string) => `What was the coldest temperature in ${city} last winter?`,
    (city: string) => `How many days over 100°F did ${city} have last year?`,
    (city: string) => `What was the wettest spring on record for ${city}?`,
    (city: string) => `Did ${city} set any temperature records last year?`,
    (city: string) => `How much rain did ${city} get during hurricane season last year?`,
    (city: string) => `What's the average high temperature in ${city} in December?`,
    (city: string) => `How does this year's rainfall in ${city} compare to average?`,
  ];

  const DEFAULT_CITIES = [
    "Denver, CO", "Chicago, IL", "Miami, FL", "Seattle, WA",
    "Phoenix, AZ", "Boston, MA", "Atlanta, GA", "Portland, OR",
  ];

  const suggestedPrompts = useMemo(() => {
    const cities = favoriteCities.length > 0 ? favoriteCities : DEFAULT_CITIES;
    const prompts = PROMPT_TEMPLATES.map(fn => {
      const city = cities[Math.floor(Math.random() * cities.length)];
      return fn(city);
    });
    const shuffled = prompts.sort(() => 0.5 - Math.random());
    return shuffled.slice(0, 4);
  }, [currentConversationId, favoriteCities]);

  const groupedConversations = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
    const weekAgoStart = todayStart - 7 * 24 * 60 * 60 * 1000;
    
    const groups: { today: Conversation[], week: Conversation[], older: Conversation[] } = { today: [], week: [], older: [] };
    
    conversations.forEach(c => {
      if (c.updatedAt >= todayStart) groups.today.push(c);
      else if (c.updatedAt >= weekAgoStart) groups.week.push(c);
      else groups.older.push(c);
    });
    return groups;
  }, [conversations]);

  const formatDate = (dateMs: number) => {
    if (!useRelativeDates) {
      return new Date(dateMs).toLocaleDateString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
    }
    
    const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    const diff = dateMs - Date.now();
    const diffDays = Math.round(diff / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      const diffHours = Math.round(diff / (1000 * 60 * 60));
      if (diffHours === 0) {
        const diffMinutes = Math.round(diff / (1000 * 60));
        return rtf.format(diffMinutes, 'minute');
      }
      return rtf.format(diffHours, 'hour');
    }
    return rtf.format(diffDays, 'day');
  };

  const renderConversationList = (list: Conversation[], title: string) => {
    if (list.length === 0) return null;
    return (
      <div className="mb-4">
        <h3 className="px-3 mb-1 text-xs font-semibold text-muted-foreground uppercase tracking-wider">{title}</h3>
        <div className="space-y-1">
          {list.map(c => {
             const parts = c.title.split(' - ');
             const isStructured = parts.length === 2;
             return (
             <div key={c.id} className={`group/item flex items-center justify-between p-2 rounded-lg cursor-pointer transition-colors ${c.id === currentConversationId ? 'bg-secondary' : 'hover:bg-muted/50'}`} onClick={() => setCurrentConversationId(c.id)}>
               <div className="flex items-start gap-3 min-w-0 pr-2 pt-1">
                 <div className="flex flex-col min-w-0 gap-0.5">
                   {isStructured ? (
                     <>
                       <span className="text-sm font-semibold tracking-tight text-foreground truncate">{parts[0].trim()}</span>
                       <span className="text-[13px] text-muted-foreground line-clamp-2 leading-snug">{parts[1].trim()}</span>
                     </>
                   ) : (
                     <span className="text-sm font-medium line-clamp-2 leading-snug">{c.title}</span>
                   )}
                   <span className="text-[10px] text-muted-foreground/50 font-semibold tracking-wide uppercase mt-0.5">
                     {formatDate(c.updatedAt)}
                   </span>
                 </div>
               </div>
               <button onClick={(e) => { e.stopPropagation(); deleteChat(c.id); }} className="opacity-0 group-hover/item:opacity-100 p-1 text-muted-foreground hover:text-destructive transition-all shrink-0">
                 <Trash2 className="w-4 h-4" />
               </button>
             </div>
          )})}
        </div>
      </div>
    );
  };

  // omp's --model expects the fully-qualified selector (e.g. "openrouter/xiaomi/mimo-v2.5-pro").
  // A model's `id` (e.g. "xiaomi/mimo-v2.5-pro") is NOT sufficient: omp reads the segment before
  // the first slash as the provider, so passing an id would resolve to the wrong provider.
  const resolveModelArg = (id: string): string =>
    models.find(m => m.id === id)?.selector || id;

  function sendMessage(messageText: string, isRegenerate = false) {
    if ((!messageText.trim() && !isRegenerate) || isProcessing) return;

    setIsProcessing(true);
    startTimeRef.current = Date.now();
    ttftRef.current = null;
    tokensRef.current = 0;

    let activeId = currentConversationId;
    let newConversations = [...conversations];
    
    if (!activeId) {
      activeId = crypto.randomUUID();
      const newConv: Conversation = {
        id: activeId,
        title: messageText.slice(0, 30) + (messageText.length > 30 ? "..." : ""),
        updatedAt: Date.now(),
        messages: [{ role: "user", content: messageText }]
      };
      newConversations = [newConv, ...newConversations];
      setCurrentConversationId(activeId);
      
      invoke<string>("generate_title", { message: messageText, model: resolveModelArg(selectedModel) })
        .then(title => {
          setConversations(prev => prev.map(c => c.id === activeId ? { ...c, title } : c));
        })
        .catch(console.error);
    } else {
      newConversations = newConversations.map(c => {
        if (c.id === activeId) {
          const newMsgs = isRegenerate ? c.messages : [...c.messages, { role: "user" as const, content: messageText }];
          return {
            ...c,
            messages: newMsgs,
            updatedAt: Date.now()
          };
        }
        return c;
      });
      // Bring to top
      const activeConv = newConversations.find(c => c.id === activeId);
      newConversations = [activeConv!, ...newConversations.filter(c => c.id !== activeId)];
    }
    setConversations(newConversations);

    const activeHistory = newConversations.find(c => c.id === activeId)?.messages || [];

    invoke("ask_omp", { message: messageText, model: resolveModelArg(selectedModel), systemPrompt, history: activeHistory })
      .catch(e => {
        console.error(e);
        setConversations(prev => prev.map(c => c.id === activeId ? { ...c, messages: [...c.messages, { role: "bot", content: `Error: ${e}` }] } : c));
        setIsProcessing(false);
      });
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const userMessage = input.trim();
    if (!userMessage) return;
    setInput("");
    sendMessage(userMessage);
  }

  async function handleStop() {
    setIsProcessing(false);
    try {
      await invoke("stop_omp");
    } catch (e) {
      console.error(e);
    }
  }

  function handleSuggestedPrompt(prompt: string) {
    sendMessage(prompt);
  }

  return (
    <div className="flex h-screen bg-background text-foreground dark overflow-hidden">
      {/* Sidebar */}
        <div 
          className="border-r border-border bg-card flex flex-col shrink-0 animate-in slide-in-from-left-4 relative group"
          style={{ width: sidebarWidth }}
        >
          <div className="px-4 pb-2.5 pt-10 border-b border-border flex items-center gap-2" data-tauri-drag-region>
            <button onClick={createNewChat} className="flex-1 flex items-center justify-center gap-2 bg-primary text-primary-foreground py-1.5 px-4 rounded-lg hover:opacity-90 transition-opacity font-medium text-sm shadow-sm z-10 relative">
              <Plus className="w-4 h-4" /> New Chat
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-2">
            {renderConversationList(groupedConversations.today, "Today")}
            {renderConversationList(groupedConversations.week, "Previous 7 Days")}
            {renderConversationList(groupedConversations.older, "Older")}
          </div>
          <div className="p-3 border-t border-border mt-auto">
            <button 
              onClick={() => setIsSettingsOpen(true)}
              className="flex items-center gap-2 w-full text-sm font-medium text-muted-foreground hover:text-foreground transition-colors p-2 rounded-md hover:bg-secondary"
            >
              <Settings className="w-4 h-4" />
              Settings
            </button>
          </div>
          {/* Resize Handle */}
          <div 
            className="absolute top-0 right-0 w-1.5 h-full cursor-col-resize hover:bg-primary/50 group-hover:bg-border transition-colors z-20"
            onMouseDown={() => {
              isResizingRef.current = true;
              document.body.style.cursor = 'col-resize';
            }}
            onDoubleClick={() => setSidebarWidth(280)}
          />
        </div>
      
      {/* Main Container */}
      <div className="flex flex-col flex-1 min-w-0 relative">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-2.5 border-b border-border bg-card/50 backdrop-blur-md z-10 shadow-sm sticky top-0" data-tauri-drag-region>
        <div className="flex items-center gap-2.5" data-tauri-drag-region>
          <CloudSun className="w-6 h-6 text-primary pointer-events-none" />
          <h1 className="text-lg font-semibold tracking-tight pointer-events-none mr-4 mt-[4px]">ACIS Chat</h1>
        </div>
        
        <div className="flex items-center gap-4 z-10 relative">
          {/* Quick Picker */}
          {models.length > 0 && !modelsError && (
            <div className="relative flex items-center group/select">
              <select
                value={selectedModel}
                onChange={(e) => handleSelectModel(e.target.value)}
                className="appearance-none bg-secondary/60 hover:bg-secondary text-xs font-medium px-3 py-1.5 pr-8 rounded-md border border-border/60 outline-none focus:ring-2 focus:ring-primary/20 transition-all max-w-[200px] truncate cursor-pointer shadow-sm text-foreground"
                title="Select a favorite model"
              >
                {quickPickerModels.map(m => (
                  <option key={m.id} value={m.id}>
                    {m.name || m.id}
                  </option>
                ))}
              </select>
              <ChevronDown className="w-3.5 h-3.5 text-muted-foreground absolute right-3 pointer-events-none group-hover/select:text-foreground transition-colors" />
            </div>
          )}
        </div>
      </header>

      {/* Settings Modal (Full Screen Overlay) */}
      {isSettingsOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-card border border-border rounded-lg shadow-2xl w-full max-w-5xl h-[80vh] flex flex-col overflow-hidden animate-in zoom-in-95">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border">
              <h2 className="text-xl font-semibold">Settings</h2>
              <button onClick={() => setIsSettingsOpen(false)} className="p-2 rounded-md hover:bg-secondary transition-colors">
                <X className="w-5 h-5" />
              </button>
            </div>
            
            {/* Modal Body */}
            <div className="flex flex-1 overflow-hidden">
              {/* Sidebar: Categories */}
              <div className="w-56 border-r border-border bg-muted/20 flex flex-col overflow-y-auto">
                <div className="flex-1 p-3 space-y-1">
                  <button
                    onClick={() => setActiveSettingsTab('general')}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${activeSettingsTab === 'general' ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-secondary text-foreground'}`}
                  >
                    General
                  </button>
                  <button
                    onClick={() => setActiveSettingsTab('ai')}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${activeSettingsTab === 'ai' ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-secondary text-foreground'}`}
                  >
                    Models
                  </button>
                  <button
                    onClick={() => setActiveSettingsTab('prompt')}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${activeSettingsTab === 'prompt' ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-secondary text-foreground'}`}
                  >
                    System Prompt
                  </button>
                  <button
                    onClick={() => setActiveSettingsTab('data')}
                    className={`block w-full text-left px-3 py-2 rounded-md text-sm transition-colors ${activeSettingsTab === 'data' ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-secondary text-foreground'}`}
                  >
                    Data Management
                  </button>
                </div>
              </div>

              {/* Main Content: Tabs */}
              <div className="flex-1 overflow-y-auto bg-background flex flex-col">
                {activeSettingsTab === 'general' && (
                  <div className="p-6">
                    <h3 className="text-lg font-medium mb-4">Appearance</h3>
                    <div className="flex items-center justify-between p-4 border border-border rounded-lg bg-card">
                      <div>
                        <h4 className="font-medium text-sm">Use Relative Dates</h4>
                        <p className="text-xs text-muted-foreground mt-1">Display dates as "2 hours ago" instead of absolute timestamps.</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input type="checkbox" className="sr-only peer" checked={useRelativeDates} onChange={handleToggleRelativeDates} />
                        <div className="w-11 h-6 bg-secondary peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-primary"></div>
                      </label>
                    </div>

                    <h3 className="text-lg font-medium mb-4 mt-6">Favorite Cities</h3>
                    <p className="text-xs text-muted-foreground mb-3">Add your favorite cities to personalize suggested prompts. If none are set, generic US cities will be used.</p>
                    <div className="flex gap-2 mb-3">
                      <div className="relative flex-1">
                        <input
                          type="text"
                          value={newCityInput}
                          onChange={(e) => {
                            setNewCityInput(e.target.value);
                            setShowCitySuggestions(true);
                            setSelectedSuggestionIdx(-1);
                          }}
                          onFocus={() => setShowCitySuggestions(true)}
                          onBlur={() => setTimeout(() => setShowCitySuggestions(false), 150)}
                          onKeyDown={(e) => {
                            if (e.key === 'ArrowDown') {
                              e.preventDefault();
                              setSelectedSuggestionIdx(i => Math.min(i + 1, citySuggestions.length - 1));
                            } else if (e.key === 'ArrowUp') {
                              e.preventDefault();
                              setSelectedSuggestionIdx(i => Math.max(i - 1, -1));
                            } else if (e.key === 'Enter') {
                              e.preventDefault();
                              const value = selectedSuggestionIdx >= 0 ? citySuggestions[selectedSuggestionIdx] : newCityInput.trim();
                              if (value) {
                                const updated = [...favoriteCities, value];
                                setFavoriteCities(updated);
                                localStorage.setItem("favoriteCities", JSON.stringify(updated));
                                setNewCityInput("");
                                setShowCitySuggestions(false);
                                setSelectedSuggestionIdx(-1);
                              }
                            } else if (e.key === 'Escape') {
                              setShowCitySuggestions(false);
                            }
                          }}
                          placeholder="Start typing a city name..."
                          className="w-full px-3 py-2 bg-secondary/50 border border-border rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
                        />
                        {showCitySuggestions && citySuggestions.length > 0 && (
                          <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-popover border border-border rounded-md shadow-lg overflow-hidden">
                            {citySuggestions.map((city, i) => (
                              <button
                                key={city}
                                onMouseDown={(e) => {
                                  e.preventDefault();
                                  const updated = [...favoriteCities, city];
                                  setFavoriteCities(updated);
                                  localStorage.setItem("favoriteCities", JSON.stringify(updated));
                                  setNewCityInput("");
                                  setShowCitySuggestions(false);
                                  setSelectedSuggestionIdx(-1);
                                }}
                                className={`block w-full text-left px-3 py-2 text-sm transition-colors ${i === selectedSuggestionIdx ? 'bg-primary text-primary-foreground' : 'hover:bg-secondary'}`}
                              >
                                {city}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => {
                          if (newCityInput.trim()) {
                            const updated = [...favoriteCities, newCityInput.trim()];
                            setFavoriteCities(updated);
                            localStorage.setItem("favoriteCities", JSON.stringify(updated));
                            setNewCityInput("");
                          }
                        }}
                        className="px-4 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium hover:opacity-90 transition-opacity"
                      >
                        Add
                      </button>
                    </div>
                    {favoriteCities.length > 0 && (
                      <div className="flex flex-wrap gap-2">
                        {favoriteCities.map((city, i) => (
                          <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-secondary rounded-full text-sm">
                            {city}
                            <button
                              onClick={() => {
                                const updated = favoriteCities.filter((_, j) => j !== i);
                                setFavoriteCities(updated);
                                localStorage.setItem("favoriteCities", JSON.stringify(updated));
                              }}
                              className="text-muted-foreground hover:text-foreground transition-colors"
                            >
                              ×
                            </button>
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
                
                {activeSettingsTab === 'ai' && (
                  <div className="flex flex-col h-full">
                    <div className="p-6 pb-4 border-b border-border">
                      <h3 className="text-lg font-medium mb-4">Provider Selection</h3>
                      <div className="flex flex-wrap gap-2">
                        <button
                          onClick={() => setActiveProvider('Favorites')}
                          className={`px-4 py-2 rounded-md text-sm transition-colors flex items-center gap-2 ${activeProvider === 'Favorites' ? 'bg-primary text-primary-foreground font-medium shadow-sm' : 'bg-secondary hover:bg-secondary/80 text-foreground'}`}
                        >
                          <Star className={`w-4 h-4 ${activeProvider === 'Favorites' ? 'fill-current' : 'text-yellow-500'}`} /> Favorites
                        </button>
                        {providers.map(p => (
                          <button
                            key={p}
                            onClick={() => setActiveProvider(p)}
                            className={`px-4 py-2 rounded-md text-sm transition-colors ${activeProvider === p ? 'bg-primary text-primary-foreground font-medium shadow-sm' : 'bg-secondary hover:bg-secondary/80 text-foreground'}`}
                          >
                            {p}
                          </button>
                        ))}
                      </div>
                    </div>
                    
                    <div className="p-6 flex-1 overflow-y-auto border-b border-border">
                      <h3 className="text-lg font-medium mb-4">Models ({activeProvider})</h3>
                      {modelsError && (
                        <div className="p-4 bg-destructive/10 text-destructive rounded-md mb-4">
                          Error loading models: {modelsError}
                        </div>
                      )}
                      {models.length === 0 && !modelsError && (
                        <div className="text-muted-foreground text-sm">Loading models...</div>
                      )}
                      
                      <div className="space-y-2">
                      {activeModels.map(m => {
                        const isFav = favorites.includes(m.id);
                        const isDef = defaultModel === m.id;
                        const isSel = selectedModel === m.id;

                        return (
                          <div key={m.id} className={`flex items-center justify-between p-3 rounded-lg border transition-colors ${isSel ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}`}>
                            <div className="flex-1 min-w-0 pr-4">
                              <h4 className="font-medium text-sm truncate">{m.name || m.id}</h4>
                              <p className="text-xs text-muted-foreground truncate font-mono mt-1">{m.id}</p>
                            </div>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => toggleFavorite(m.id)}
                                title={isFav ? "Remove from favorites" : "Add to favorites"}
                                className={`p-2 rounded-md transition-colors ${isFav ? 'text-yellow-500 hover:bg-yellow-500/10' : 'text-muted-foreground hover:bg-secondary'}`}
                              >
                                <Star className={`w-4 h-4 ${isFav ? 'fill-current' : ''}`} />
                              </button>
                              
                              <button
                                onClick={() => handleSetDefault(m.id)}
                                title="Set as default model on startup"
                                className={`p-2 rounded-md transition-colors flex items-center gap-1 ${isDef ? 'text-green-500 bg-green-500/10' : 'text-muted-foreground hover:bg-secondary'}`}
                              >
                                <CheckCircle className={`w-4 h-4 ${isDef ? 'fill-current' : ''}`} />
                                {isDef && <span className="text-xs font-medium pr-1">Default</span>}
                              </button>

                              <button
                                onClick={() => handleSelectModel(m.id)}
                                className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-2 ${isSel ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground hover:bg-primary/20'}`}
                              >
                                {isSel ? <><Check className="w-4 h-4"/> Selected</> : "Select"}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                      </div>
                    </div>
                  </div>
                )}

                {activeSettingsTab === 'prompt' && (
                  <div className="p-6 h-full flex flex-col">
                    <h3 className="text-lg font-medium mb-4">System Prompt</h3>
                    <textarea
                      value={systemPrompt}
                      onChange={(e) => handleSystemPromptChange(e.target.value)}
                      placeholder="Provide custom instructions to guide the model's behavior..."
                      className="w-full flex-1 p-3 bg-secondary/50 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary/20 resize-none min-h-[300px]"
                    />
                    <p className="text-xs text-muted-foreground mt-2">
                      These instructions will be prepended to all future conversations.
                    </p>
                  </div>
                )}

                {activeSettingsTab === 'data' && (
                  <div className="p-6">
                    <h3 className="text-lg font-medium mb-4">Data Management</h3>
                    <div className="p-4 border border-border rounded-lg bg-card space-y-4">
                      <div>
                        <h4 className="font-medium text-sm">Regenerate Chat Titles</h4>
                        <p className="text-xs text-muted-foreground mt-1 mb-3">Re-run title generation for all existing conversations using the currently selected model.</p>
                        <button onClick={async () => {
                          for (const c of conversations) {
                            if (c.messages.length > 0) {
                               try {
                                 const title = await invoke<string>("generate_title", { message: c.messages[0].content, model: resolveModelArg(selectedModel) });
                                 setConversations(prev => prev.map(pc => pc.id === c.id ? { ...pc, title } : pc));
                               } catch(e) { console.error(e); }
                            }
                          }
                        }} className="text-sm font-medium transition-colors px-4 py-2 bg-secondary rounded-md hover:bg-secondary/80 flex items-center gap-2 w-fit">
                          ↻ Regenerate All Titles
                        </button>
                      </div>
                      <div className="pt-4 border-t border-border">
                        <h4 className="font-medium text-sm">Application Logs</h4>
                        <p className="text-xs text-muted-foreground mt-1 mb-3">Open the folder containing the log file. Useful for diagnosing model or connection errors.</p>
                        <button onClick={async () => {
                          try {
                            await invoke("open_log_folder");
                          } catch (e) {
                            console.error("Failed to open log folder", e);
                          }
                        }} className="text-sm font-medium transition-colors px-4 py-2 bg-secondary rounded-md hover:bg-secondary/80 flex items-center gap-2 w-fit">
                          <FileText className="w-4 h-4" /> Open Logs
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 pb-24 scroll-smooth">
        <div className="max-w-3xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center py-10">
              <div className="space-y-4 flex flex-col items-center">
                <CloudSun className="w-16 h-16 text-muted-foreground opacity-50" />
                <p className="text-lg text-muted-foreground">
                  Ask me about historical weather anywhere in the US.
                </p>
                <div className="text-sm text-muted-foreground/70 bg-secondary px-4 py-2 rounded-md">
                  Currently using: {models.find(m => m.id === selectedModel)?.name || selectedModel || "Loading..."}
                </div>
              </div>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-2xl mt-12 px-4">
                {suggestedPrompts.map((prompt, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSuggestedPrompt(prompt)}
                    className="p-4 bg-card border border-border rounded-lg text-left hover:bg-secondary hover:border-primary/50 transition-all shadow-sm text-sm text-foreground active:scale-[0.98]"
                  >
                    {prompt}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-start gap-4 group/msg ${
                msg.role === "user" ? "justify-end" : "justify-start"
              }`}
            >
              {msg.role === "bot" && (
                <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
                  <CloudSun className="w-5 h-5 text-primary" />
                </div>
              )}
              <div
                className={`px-4 py-3 rounded-lg max-w-[85%] overflow-x-auto ${
                  msg.role === "user"
                    ? "bg-primary text-primary-foreground shadow-sm whitespace-pre-wrap"
                    : "bg-secondary text-secondary-foreground border border-border shadow-sm prose prose-sm dark:prose-invert"
                }`}
              >
                {msg.role === "bot" ? (
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      table: ({ node, ...props }) => (
                        <div className="my-6 w-full overflow-hidden rounded-xl border border-border shadow-sm bg-card">
                          <table className="w-full !m-0 border-0" {...props} />
                        </div>
                      )
                    }}
                  >
                    {msg.content.replace(/\|\n\n\|/g, '|\n|')}
                  </ReactMarkdown>
                ) : (
                  msg.content
                )}
                {msg.role === "bot" && (
                  <div className="flex items-center justify-between mt-3 pt-3 border-t border-border/50 text-xs text-muted-foreground">
                    <div className="flex items-center gap-4">
                      {msg.stats && (
                         <div className="flex items-center gap-3">
                           <span title="Time to first token">TTFT: {(msg.stats.ttft / 1000).toFixed(2)}s</span>
                           <span title="Tokens per second (approx)">Speed: {(msg.stats.tokens / (Math.max(1, msg.stats.totalTime - msg.stats.ttft) / 1000)).toFixed(1)} t/s</span>
                           <span title="Total response time">Total: {(msg.stats.totalTime / 1000).toFixed(2)}s</span>
                         </div>
                      )}
                    </div>
                    <div className="flex items-center gap-1 opacity-0 group-hover/msg:opacity-100 transition-opacity">
                      <button onClick={() => copyMessage(msg.content, i)} className="p-1.5 hover:bg-background rounded-md transition-colors" title="Copy Message">
                        {copiedIndex === i ? <Check className="w-3.5 h-3.5 text-green-500" /> : <Copy className="w-3.5 h-3.5" />}
                      </button>
                      {i === messages.length - 1 && !isProcessing && (
                        <button onClick={regenerateResponse} className="p-1.5 hover:bg-background rounded-md transition-colors" title="Regenerate Response">
                          <RefreshCw className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
              {msg.role === "user" && (
                <div className="w-8 h-8 rounded-md bg-primary flex items-center justify-center shrink-0">
                  <User className="w-5 h-5 text-primary-foreground" />
                </div>
              )}
            </div>
          ))}
          {isProcessing && (
            <div className="flex items-start gap-4 justify-start">
              <div className="w-8 h-8 rounded-md bg-primary/10 flex items-center justify-center shrink-0">
                <CloudSun className="w-5 h-5 text-primary" />
              </div>
              <div className="px-4 py-3 rounded-lg bg-secondary text-secondary-foreground border border-border">
                <div className="flex gap-1 items-center h-5">
                  <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" />
                  <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.15s]" />
                  <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce [animation-delay:-0.3s]" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 right-0 p-4 bg-gradient-to-t from-background via-background to-transparent pointer-events-none z-10">
        <div className="max-w-3xl mx-auto pointer-events-auto">
          <form
            onSubmit={handleSubmit}
            className="flex items-center gap-2 bg-popover border border-border rounded-lg p-2 shadow-lg hover:border-muted-foreground/50 transition-colors focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20"
          >
            {messages.length > 0 && (
              <button
                type="button"
                onClick={exportChat}
                title="Export chat as Markdown"
                className="p-2 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground transition-colors"
              >
                <Download className="w-4 h-4" />
              </button>
            )}
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={messages.length === 0 ? "How hot was July 2023 in Lexington, KY compared to normal?..." : "Ask a follow up..."}
              className="flex-1 bg-transparent border-none focus:outline-none px-4 text-sm"
              disabled={isProcessing}
            />
            {isProcessing ? (
              <button
                type="button"
                onClick={handleStop}
                className="p-3 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors flex items-center justify-center shadow-sm"
              >
                <Square className="w-4 h-4 fill-current" />
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="p-3 bg-primary text-primary-foreground rounded-md hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity flex items-center justify-center shadow-sm"
              >
                <Send className="w-4 h-4" />
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
    </div>
  );
}
