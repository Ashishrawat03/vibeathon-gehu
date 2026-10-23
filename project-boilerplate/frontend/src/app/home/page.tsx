"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  Plus,
  Globe,
  ArrowRight,
  Copy,
  Check,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  X,
  LogOut,
  User,
  Briefcase,
  Heart,
  Scale,
  Zap,
  Mail,
  Headphones,
  Users,
  ShoppingBag,
  Code,
  TrendingUp,
  Search,
  Pencil,
  ThumbsUp,
  ThumbsDown,
  Type,
  BarChart2,
  PanelLeft,
  SquarePen,
  MessageSquare,
  Trash2,
  Send,
} from "lucide-react";
import { useRouter } from "next/navigation";
import {
  EmailComposerDialog,
  type EmailComposerDialogHandle,
} from "@/components/email-composer-dialog";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface Persona {
  id: string;
  label: string;
  description: string;
  icon: React.ElementType;
  custom?: boolean;
  tone?: string;
}

interface ChangeAnalysis {
  change_percent: number;
  meaning_preserved: string;
  tone_shift: string;
  key_changes: string[];
}

interface TransformResult {
  output_id?: string;
  persona_id: string;
  persona_label: string;
  original: string;
  rewritten: string;
  language?: string;
  analysis: ChangeAnalysis;
  error?: string;
}

interface ChatTurn {
  id: string;
  draft: string;
  results: TransformResult[];
  targetLanguage: string | null;
  createdAt: number;
}

interface ChatSession {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  selectedIds: string[];
  targetLanguage: string | null;
  turns: ChatTurn[];
}

const CHATS_KEY = "pt-chats";
const ACTIVE_CHAT_KEY = "pt-active-chat";
const SIDEBAR_KEY = "pt-sidebar-collapsed";
const TOKEN_KEY = "pt-token";

function userStorageKey(key: string): string {
  return `${key}:${localStorage.getItem("pt-user-id") || "guest"}`;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------
const DEFAULT_PERSONAS: Persona[] = [
  { id: "executive",   label: "Executive / C-Level",    description: "Concise, strategic, confident, and focused on outcomes.",           icon: Briefcase },
  { id: "peer",        label: "Supportive Peer",        description: "Empathetic, constructive, encouraging, and respectful.",            icon: Heart },
  { id: "legal",       label: "Legal / Compliance",     description: "Precise, formal, neutral, and unambiguous.",                       icon: Scale },
  { id: "genz",        label: "Gen-Z / Casual",         description: "Energetic, conversational, modern, and informal. No emojis.",      icon: Zap },
  { id: "email",       label: "Professional Email",     description: "Polished, clear, and business-appropriate.",                       icon: Mail },
  { id: "support",     label: "Customer Support",       description: "Helpful, reassuring, empathetic, and solution-oriented.",          icon: Headphones },
  { id: "manager",     label: "Manager / Leadership",   description: "Clear, accountable, motivating, and action-oriented.",             icon: Users },
  { id: "client",      label: "Client / Customer",      description: "Courteous, professional, and customer-focused.",                   icon: ShoppingBag },
  { id: "technical",   label: "Technical / Engineering", description: "Specific, structured, and technically accurate.",                 icon: Code },
  { id: "investor",    label: "Investor / Stakeholder", description: "Results-oriented, concise, and focused on business impact.",       icon: TrendingUp },
];

const LANGUAGES = [
  "English", "Hindi", "Spanish", "French", "German", "Portuguese",
  "Japanese", "Korean", "Chinese", "Arabic", "Bengali", "Tamil",
  "Italian", "Russian", "Dutch", "Turkish", "Vietnamese", "Polish",
  "Swedish", "Norwegian",
];

const REFINEMENT_OPTIONS = [
  "Make it shorter",
  "Make it warmer",
  "Make it more formal",
  "Make it more persuasive",
  "Make it clearer",
];

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------
function levenshtein(a: string, b: string): number {
  const m = a.length, n = b.length;
  const dp: number[][] = Array.from({ length: m + 1 }, (_, i) =>
    Array.from({ length: n + 1 }, (_, j) => (i === 0 ? j : j === 0 ? i : 0))
  );
  for (let i = 1; i <= m; i++)
    for (let j = 1; j <= n; j++)
      dp[i][j] = a[i - 1] === b[j - 1]
        ? dp[i - 1][j - 1]
        : 1 + Math.min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1]);
  return dp[m][n];
}

function changePercent(orig: string, rw: string): number {
  if (!orig.trim()) return 0;
  const dist = levenshtein(orig.trim().slice(0, 500), rw.trim().slice(0, 500));
  const maxLen = Math.max(orig.trim().length, rw.trim().length, 1);
  return Math.round(Math.min(100, (dist / maxLen) * 100));
}

function stripEmojis(text: string): string {
  if (!text) return "";
  return text
    .replace(/\p{Extended_Pictographic}/gu, "")
    .replace(/[\uFE0F\u200D]/g, "")
    .replace(/[ \t]{2,}/g, " ")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

function titleFromDraft(draft: string): string {
  const t = draft.replace(/\s+/g, " ").trim();
  if (!t) return "New chat";
  return t.length > 36 ? `${t.slice(0, 36)}...` : t;
}

function newChatSession(): ChatSession {
  const now = Date.now();
  return {
    id: crypto.randomUUID(),
    title: "New chat",
    createdAt: now,
    updatedAt: now,
    selectedIds: [],
    targetLanguage: null,
    turns: [],
  };
}

function sanitizeResults(results: TransformResult[]): TransformResult[] {
  return results.map((r) => ({
    ...r,
    rewritten: r.rewritten ? stripEmojis(r.rewritten) : r.rewritten,
    error: r.error ? stripEmojis(r.error) : r.error,
  }));
}

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

// ---- Persona Chip ----
function PersonaChip({ persona, onRemove }: { persona: Persona; onRemove: () => void }) {
  return (
    <motion.span
      initial={{ opacity: 0, scale: 0.85 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.85 }}
      className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-white/10 border border-white/20 text-white/80 text-xs font-medium"
    >
      <persona.icon className="w-3 h-3 shrink-0" />
      {persona.label}
      <button onClick={onRemove} className="ml-0.5 text-white/40 hover:text-white/80 transition-colors">
        <X className="w-3 h-3" />
      </button>
    </motion.span>
  );
}

// ---- Persona Picker Popover ----
function PersonaPicker({
  selected,
  onToggle,
  onClose,
  onCreateCustom,
  customPersonas,
}: {
  selected: Set<string>;
  onToggle: (p: Persona) => void;
  onClose: () => void;
  onCreateCustom: () => void;
  customPersonas: Persona[];
}) {
  const allPersonas = [...DEFAULT_PERSONAS, ...customPersonas];
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.97 }}
      transition={{ duration: 0.15 }}
      className="absolute bottom-full mb-2 left-0 w-[360px] bg-[#141414] border border-white/10 rounded-2xl shadow-2xl shadow-black/70 z-50 overflow-hidden"
    >
      <div className="p-4 border-b border-white/[0.07]">
        <h3 className="text-sm font-semibold text-white">Who is this message for?</h3>
        <p className="text-xs text-white/40 mt-0.5">Select one or more personas</p>
      </div>
      <div className="overflow-y-auto max-h-[320px] p-2">
        {allPersonas.map((p) => {
          const Icon = p.icon;
          const isSelected = selected.has(p.id);
          return (
            <button
              key={p.id}
              onClick={() => onToggle(p)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition-all duration-150 group ${
                isSelected ? "bg-white/10 border border-white/20" : "hover:bg-white/[0.05] border border-transparent"
              }`}
            >
              <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-colors ${isSelected ? "bg-white" : "bg-white/8"}`}>
                <Icon className={`w-4 h-4 ${isSelected ? "text-black" : "text-white/50"}`} />
              </div>
              <div className="flex-1 min-w-0">
                <div className={`text-sm font-medium truncate ${isSelected ? "text-white" : "text-white/70"}`}>{p.label}</div>
                <div className="text-[11px] text-white/30 truncate">{p.description}</div>
              </div>
              <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center shrink-0 transition-all ${isSelected ? "bg-white border-white" : "border-white/20"}`}>
                {isSelected && <Check className="w-2.5 h-2.5 text-black" />}
              </div>
            </button>
          );
        })}
      </div>
      <div className="p-2 border-t border-white/[0.07]">
        <button
          onClick={onCreateCustom}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-xl text-white/50 hover:text-white/80 hover:bg-white/[0.05] transition-all text-sm"
        >
          <Plus className="w-4 h-4" />
          Create custom persona
        </button>
      </div>
    </motion.div>
  );
}

// ---- Custom Persona Form ----
function CustomPersonaForm({
  onSave,
  onCancel,
}: {
  onSave: (p: Persona) => void;
  onCancel: () => void;
}) {
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [tone, setTone] = useState("");

  const handleSave = () => {
    if (!name.trim()) return;
    const id = `custom-${Date.now()}`;
    onSave({
      id,
      label: name.trim(),
      description: desc.trim() || `Custom persona: ${name}`,
      icon: User,
      custom: true,
      tone: tone.trim() || undefined,
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 8 }}
      className="absolute bottom-full mb-2 left-0 w-[360px] bg-[#141414] border border-white/10 rounded-2xl shadow-2xl shadow-black/70 z-50 p-4"
    >
      <h3 className="text-sm font-semibold text-white mb-3">Create custom persona</h3>
      <div className="space-y-3">
        <div>
          <label className="text-[11px] text-white/40 uppercase tracking-wider">Persona name *</label>
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder='e.g. "My Manager"'
            className="mt-1 w-full bg-[#1e1e1e] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-white/25 transition-colors"
          />
        </div>
        <div>
          <label className="text-[11px] text-white/40 uppercase tracking-wider">Description</label>
          <input
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
            placeholder="Describe the audience"
            className="mt-1 w-full bg-[#1e1e1e] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-white/25 transition-colors"
          />
        </div>
        <div>
          <label className="text-[11px] text-white/40 uppercase tracking-wider">Preferred tone</label>
          <input
            value={tone}
            onChange={(e) => setTone(e.target.value)}
            placeholder="e.g. Direct, friendly, academic"
            className="mt-1 w-full bg-[#1e1e1e] border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-white/25 transition-colors"
          />
        </div>
        <div className="flex gap-2 pt-1">
          <button onClick={onCancel} className="flex-1 py-2 rounded-lg border border-white/10 text-white/50 hover:text-white/80 text-sm transition-colors">
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!name.trim()}
            className="flex-1 py-2 rounded-lg bg-white text-black text-sm font-semibold hover:bg-white/90 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            Save persona
          </button>
        </div>
      </div>
    </motion.div>
  );
}

// ---- Language Picker Popover ----
function LanguagePicker({
  selected,
  onSelect,
  onClose,
}: {
  selected: string | null;
  onSelect: (lang: string | null) => void;
  onClose: () => void;
}) {
  const [search, setSearch] = useState("");
  const ref = useRef<HTMLDivElement>(null);
  const filtered = LANGUAGES.filter((l) => l.toLowerCase().includes(search.toLowerCase()));

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [onClose]);

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, y: 8, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 8, scale: 0.97 }}
      transition={{ duration: 0.15 }}
      className="absolute bottom-full mb-2 left-0 w-[260px] bg-[#141414] border border-white/10 rounded-2xl shadow-2xl shadow-black/70 z-50 overflow-hidden"
    >
      <div className="p-3 border-b border-white/[0.07]">
        <p className="text-xs font-semibold text-white mb-2">Translate to</p>
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-white/30" />
          <input
            autoFocus
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search language..."
            className="w-full bg-[#1e1e1e] border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-white placeholder:text-white/25 focus:outline-none focus:border-white/25 transition-colors"
          />
        </div>
      </div>
      <div className="overflow-y-auto max-h-[220px] p-1.5">
        {selected && (
          <button
            onClick={() => { onSelect(null); onClose(); }}
            className="w-full text-left px-3 py-2 rounded-lg text-xs text-white/40 hover:text-white/70 hover:bg-white/[0.05] transition-colors"
          >
            Clear translation
          </button>
        )}
        {filtered.map((lang) => (
          <button
            key={lang}
            onClick={() => { onSelect(lang); onClose(); }}
            className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm transition-colors ${
              selected === lang ? "text-white bg-white/10" : "text-white/60 hover:text-white hover:bg-white/[0.05]"
            }`}
          >
            {lang}
            {selected === lang && <Check className="w-3.5 h-3.5" />}
          </button>
        ))}
      </div>
    </motion.div>
  );
}

// ---- Change Analysis Panel ----
function ChangeAnalysisPanel({ result }: { result: TransformResult }) {
  const [expanded, setExpanded] = useState(false);
  const [showComparison, setShowComparison] = useState(false);
  const pct = result.analysis?.change_percent ?? changePercent(result.original, result.rewritten);

  const barColor = pct > 60 ? "bg-amber-400" : pct > 30 ? "bg-blue-400" : "bg-emerald-400";

  return (
    <div className="mt-4 border border-white/[0.08] rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-white/[0.03] transition-colors"
      >
        <span className="text-xs font-medium text-white/50 uppercase tracking-wider">Change Analysis</span>
        <div className="flex items-center gap-3">
          <span className="text-xs text-white/40">{pct}% changed</span>
          {expanded ? <ChevronUp className="w-3.5 h-3.5 text-white/30" /> : <ChevronDown className="w-3.5 h-3.5 text-white/30" />}
        </div>
      </button>

      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4 space-y-4">
              {/* Change bar */}
              <div>
                <div className="flex justify-between items-center text-[11px] text-white/30 mb-1.5">
                  <span>Text changed</span>
                  <span className="font-medium text-white/60">{pct}%</span>
                </div>
                <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                  <motion.div
                    className={`h-full rounded-full ${barColor}`}
                    initial={{ width: "0%" }}
                    animate={{ width: `${pct}%` }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                  />
                </div>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-3 gap-2">
                <div className="bg-white/[0.04] rounded-lg p-2.5 text-center">
                  <div className="text-[10px] text-white/30 uppercase tracking-wider">Meaning</div>
                  <div className="text-sm font-semibold text-white mt-1">{result.analysis?.meaning_preserved ?? "High"}</div>
                </div>
                <div className="bg-white/[0.04] rounded-lg p-2.5 text-center col-span-2">
                  <div className="text-[10px] text-white/30 uppercase tracking-wider">Tone Shift</div>
                  <div className="text-sm font-semibold text-white mt-1 truncate">{result.analysis?.tone_shift ?? `Original → ${result.persona_label}`}</div>
                </div>
              </div>

              {/* Key changes */}
              {result.analysis?.key_changes?.length > 0 && (
                <div>
                  <div className="text-[11px] text-white/30 uppercase tracking-wider mb-2">Key Changes</div>
                  <ul className="space-y-1">
                    {result.analysis.key_changes.map((c, i) => (
                      <li key={i} className="flex items-start gap-2 text-xs text-white/50">
                        <span className="text-white/20 mt-0.5">•</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Before/After */}
              <button
                onClick={() => setShowComparison(!showComparison)}
                className="text-xs text-white/40 hover:text-white/70 transition-colors flex items-center gap-1.5"
              >
                <BarChart2 className="w-3.5 h-3.5" />
                {showComparison ? "Hide" : "Show"} before / after comparison
              </button>
              <AnimatePresence>
                {showComparison && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    className="grid grid-cols-2 gap-2"
                  >
                    <div>
                      <p className="text-[10px] text-white/30 mb-1.5 uppercase tracking-wider">Original</p>
                      <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 text-xs text-white/40 whitespace-pre-wrap leading-relaxed max-h-32 overflow-y-auto">
                        {result.original}
                      </div>
                    </div>
                    <div>
                      <p className="text-[10px] text-white/30 mb-1.5 uppercase tracking-wider">Rewritten</p>
                      <div className="bg-white/[0.03] border border-white/[0.06] rounded-lg p-3 text-xs text-white/70 whitespace-pre-wrap leading-relaxed max-h-32 overflow-y-auto">
                        {result.rewritten}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ---- Result Card ----
function ResultCard({
  result,
  draftId,
  onRegenerate,
  onFeedback,
  selectedPersonas,
}: {
  result: TransformResult;
  draftId: string;
  onRegenerate: (instructions?: string) => Promise<void>;
  onFeedback: (outputId: string, feedback: "like" | "dislike" | null) => void;
  selectedPersonas: Persona[];
}) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");
  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState(result.rewritten);
  const [refineInput, setRefineInput] = useState("");
  const [isRewriting, setIsRewriting] = useState(false);
  const [largerText, setLargerText] = useState(false);
  const [feedback, setFeedback] = useState<"like" | "dislike" | null>(null);
  const composerRef = useRef<EmailComposerDialogHandle>(null);

  const persona = selectedPersonas.find((p) => p.id === result.persona_id);
  const Icon = persona?.icon ?? Sparkles;

  const handleCopy = async () => {
    setCopyError("");
    try {
      await navigator.clipboard.writeText(editing ? editText : result.rewritten);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setCopyError("Clipboard access failed. Check your browser permissions.");
    }
  };

  const handleRewrite = async (instructions?: string) => {
    setIsRewriting(true);
    try {
      await onRegenerate(instructions);
      setRefineInput("");
    } finally {
      setIsRewriting(false);
    }
  };

  if (result.error) {
    return (
      <div className="bg-red-500/5 border border-red-500/20 rounded-2xl p-5">
        <p className="text-sm font-medium text-red-400">{result.persona_label}</p>
        <p className="text-xs text-red-400/60 mt-1">{result.error}</p>
      </div>
    );
  }

  return (
    <div className="bg-[#111111] border border-white/[0.08] rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-white/[0.06]">
        <div className="w-8 h-8 rounded-lg bg-white/8 flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-white/60" />
        </div>
        <div>
          <p className="text-sm font-semibold text-white">{result.persona_label}</p>
          {result.language && (
            <p className="text-[11px] text-white/30 mt-0.5">in {result.language}</p>
          )}
        </div>
        <div className="ml-auto flex items-center gap-1">
          <button
            onClick={() => setLargerText((current) => !current)}
            className={`p-2 rounded-lg transition-all ${largerText ? "text-white bg-white/10" : "text-white/30 hover:text-white/70 hover:bg-white/5"}`}
            title={largerText ? "Use standard text size" : "Make output text larger"}
            aria-label={largerText ? "Use standard text size" : "Make output text larger"}
          >
            <Type className="w-4 h-4" />
          </button>
          <button
            onClick={handleCopy}
            className="p-2 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
            title="Copy"
            aria-label="Copy generated response"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
          </button>
          <button
            onClick={() => { setEditing(!editing); setEditText(result.rewritten); }}
            className="p-2 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all"
            title="Edit"
            aria-label="Edit generated response"
          >
            <Pencil className="w-4 h-4" />
          </button>
          <button
            onClick={() => composerRef.current?.open()}
            className="p-2 rounded-lg text-white/30 hover:text-white hover:bg-white/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 transition-all"
            title="Compose email"
            aria-label={`Review and compose email for ${result.persona_label}`}
          >
            <Send className="w-4 h-4" aria-hidden="true" />
          </button>
          <button
            onClick={() => void handleRewrite()}
            disabled={isRewriting}
            className="p-2 rounded-lg text-white/30 hover:text-white/70 hover:bg-white/5 transition-all disabled:opacity-40"
            title="Rewrite"
          >
            <RefreshCw className={`w-4 h-4 ${isRewriting ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {(copied || copyError) && (
        <p
          role={copyError ? "alert" : "status"}
          aria-live="polite"
          className={`px-5 pt-3 text-xs ${copyError ? "text-red-300" : "text-emerald-300"}`}
        >
          {copyError || "Copied to clipboard."}
        </p>
      )}

      {/* Rewritten text */}
      <div className="px-5 py-4">
        {editing ? (
          <textarea
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="w-full bg-white/[0.03] border border-white/10 rounded-xl p-3 text-lg text-white/80 leading-relaxed whitespace-pre-wrap resize-none focus:outline-none focus:border-white/20 transition-colors min-h-[80px]"
            style={{ height: "auto" }}
            rows={Math.max(4, editText.split("\n").length)}
          />
        ) : (
          <p className={`${largerText ? "text-xl" : "text-lg"} text-white/80 leading-8 whitespace-pre-wrap`}>{stripEmojis(result.rewritten)}</p>
        )}

        <div className="mt-3 flex items-center gap-2">
          <span className="text-xs text-white/30">Was this helpful?</span>
          <button
            onClick={() => {
              const next = feedback === "like" ? null : "like";
              setFeedback(next);
              if (result.output_id) onFeedback(result.output_id, next);
            }}
            className={`p-1.5 rounded-md transition-colors ${feedback === "like" ? "text-emerald-300 bg-emerald-400/10" : "text-white/35 hover:text-white/80"}`}
            aria-label="Like output"
            title="Like"
          >
            <ThumbsUp className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              const next = feedback === "dislike" ? null : "dislike";
              setFeedback(next);
              if (result.output_id) onFeedback(result.output_id, next);
            }}
            className={`p-1.5 rounded-md transition-colors ${feedback === "dislike" ? "text-red-300 bg-red-400/10" : "text-white/35 hover:text-white/80"}`}
            aria-label="Dislike output"
            title="Dislike"
          >
            <ThumbsDown className="w-4 h-4" />
          </button>
        </div>

        {/* Refine */}
        <div className="mt-4">
          <div className="flex flex-wrap gap-1.5 mb-2">
            {REFINEMENT_OPTIONS.map((opt) => (
              <button
                key={opt}
                onClick={() => void handleRewrite(opt)}
                disabled={isRewriting}
                className="px-2.5 py-1 rounded-full border border-white/[0.08] text-white/35 hover:text-white/60 hover:border-white/20 text-xs transition-all disabled:opacity-40"
              >
                {opt}
              </button>
            ))}
          </div>
          <form
            className="flex gap-2 mt-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (refineInput.trim()) void handleRewrite(refineInput.trim());
            }}
          >
            <input
              value={refineInput}
              onChange={(e) => setRefineInput(e.target.value)}
              placeholder="Or enter a custom rewrite instruction..."
              className="flex-1 bg-white/[0.04] border border-white/[0.08] rounded-lg px-3 py-1.5 text-xs text-white/60 placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
            />
            <button
              type="submit"
              disabled={isRewriting || !refineInput.trim()}
              className="px-3 py-1.5 bg-white/10 hover:bg-white/15 text-white/70 rounded-lg text-xs font-medium transition-colors disabled:opacity-40"
            >
              {isRewriting ? "Rewriting..." : "Rewrite"}
            </button>
          </form>
        </div>
      </div>

      {/* Change Analysis */}
      <div className="px-5 pb-5">
        <ChangeAnalysisPanel result={result} />
      </div>
      <EmailComposerDialog
        ref={composerRef}
        sourceId={draftId}
        personaLabel={result.persona_label}
        generatedText={result.rewritten}
      />
    </div>
  );
}

function ChatSidebar({
  collapsed,
  onToggle,
  chats,
  activeId,
  onNewChat,
  onSelect,
  onDelete,
  onSignOut,
}: {
  collapsed: boolean;
  onToggle: () => void;
  chats: ChatSession[];
  activeId: string;
  onNewChat: () => void;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onSignOut: () => void;
}) {
  const visibleChats = chats.filter((c) => c.turns.length > 0 || c.id === activeId);

  return (
    <aside
      className={`h-full shrink-0 bg-[#0c0c0c] border-r border-white/[0.06] flex flex-col transition-[width] duration-200 ease-out ${
        collapsed ? "w-[52px]" : "w-[260px]"
      }`}
    >
      <div className={`flex items-center ${collapsed ? "flex-col gap-1 py-3" : "justify-between px-3 py-3"}`}>
        {collapsed ? (
          <>
            <button
              onClick={onToggle}
              title="Open sidebar"
              className="w-9 h-9 rounded-lg flex items-center justify-center text-white/50 hover:text-white hover:bg-white/8 transition-colors"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center mt-1">
              <Sparkles className="w-3.5 h-3.5 text-black" />
            </div>
            <button
              onClick={onNewChat}
              title="New chat"
              className="w-9 h-9 rounded-lg flex items-center justify-center text-white/50 hover:text-white hover:bg-white/8 transition-colors mt-1"
            >
              <SquarePen className="w-4 h-4" />
            </button>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-lg bg-white flex items-center justify-center shrink-0">
                <Sparkles className="w-3.5 h-3.5 text-black" />
              </div>
              <span className="text-white font-semibold text-sm tracking-tight truncate">Persona Transformer</span>
            </div>
            <button
              onClick={onToggle}
              title="Close sidebar"
              className="w-8 h-8 rounded-lg flex items-center justify-center text-white/40 hover:text-white hover:bg-white/8 transition-colors"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          </>
        )}
      </div>

      {!collapsed && (
        <div className="px-2 pb-2">
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg border border-white/10 text-white/80 hover:bg-white/8 text-sm font-medium transition-colors"
          >
            <SquarePen className="w-4 h-4" />
            New chat
          </button>
        </div>
      )}

      <div className={`flex-1 overflow-y-auto ${collapsed ? "px-1.5" : "px-2"} py-1`}>
        {!collapsed && visibleChats.some((c) => c.turns.length > 0) && (
          <p className="px-2 pb-2 text-[11px] uppercase tracking-wider text-white/30">Chats</p>
        )}
        {visibleChats.map((chat) => {
          const active = chat.id === activeId;
          if (collapsed) {
            return (
              <button
                key={chat.id}
                onClick={() => onSelect(chat.id)}
                title={chat.title}
                className={`w-9 h-9 mx-auto mb-1 rounded-lg flex items-center justify-center transition-colors ${
                  active ? "bg-white/12 text-white" : "text-white/40 hover:text-white hover:bg-white/8"
                }`}
              >
                <MessageSquare className="w-4 h-4" />
              </button>
            );
          }
          return (
            <div
              key={chat.id}
              className={`group flex items-center rounded-lg mb-0.5 ${
                active ? "bg-white/10" : "hover:bg-white/[0.05]"
              }`}
            >
              <button
                onClick={() => onSelect(chat.id)}
                className="flex-1 min-w-0 flex items-center gap-2 px-3 py-2 text-left"
              >
                <MessageSquare className={`w-3.5 h-3.5 shrink-0 ${active ? "text-white/70" : "text-white/30"}`} />
                <span className={`text-sm truncate ${active ? "text-white" : "text-white/55"}`}>{chat.title}</span>
              </button>
              {chat.turns.length > 0 && (
                <button
                  onClick={() => onDelete(chat.id)}
                  title="Delete chat"
                  className="opacity-0 group-hover:opacity-100 p-2 text-white/30 hover:text-white/80 transition-opacity"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          );
        })}
      </div>

      <div className={`border-t border-white/[0.06] ${collapsed ? "p-1.5" : "p-2"}`}>
        <button
          onClick={onSignOut}
          title="Sign out"
          className={`flex items-center rounded-lg text-white/45 hover:text-white hover:bg-white/8 transition-colors ${
            collapsed ? "w-9 h-9 mx-auto justify-center" : "w-full gap-2 px-3 py-2 text-sm"
          }`}
        >
          <LogOut className="w-4 h-4" />
          {!collapsed && <span>Sign out</span>}
        </button>
      </div>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------
export default function HomePage() {
  const router = useRouter();

  // Draft state
  const [draft, setDraft] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Persona state
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [customPersonas, setCustomPersonas] = useState<Persona[]>(() => {
    if (typeof window === "undefined") return [];
    try { return JSON.parse(localStorage.getItem(userStorageKey("pt-custom-personas")) || "[]"); } catch { return []; }
  });
  const [showPersonaPicker, setShowPersonaPicker] = useState(false);
  const [showCustomForm, setShowCustomForm] = useState(false);
  const personaAnchorRef = useRef<HTMLDivElement>(null);

  // Language state
  const [targetLanguage, setTargetLanguage] = useState<string | null>(null);
  const [showLangPicker, setShowLangPicker] = useState(false);
  const langAnchorRef = useRef<HTMLDivElement>(null);

  // Transform state
  const [isTransforming, setIsTransforming] = useState(false);
  const [results, setResults] = useState<TransformResult[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const threadRef = useRef<HTMLDivElement>(null);

  const [chats, setChats] = useState<ChatSession[]>(() => {
    if (typeof window === "undefined") return [];
    try {
      const parsed = JSON.parse(localStorage.getItem(userStorageKey(CHATS_KEY)) || "[]") as ChatSession[];
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  });
  const [activeId, setActiveId] = useState<string>(() => {
    if (typeof window === "undefined") return "";
    return localStorage.getItem(userStorageKey(ACTIVE_CHAT_KEY)) || "";
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return localStorage.getItem(userStorageKey(SIDEBAR_KEY)) === "1";
  });

  // All personas (default + custom)
  const allPersonas = [...DEFAULT_PERSONAS, ...customPersonas];
  const selectedPersonas = allPersonas.filter((p) => selectedIds.has(p.id));
  const activeChat = chats.find((c) => c.id === activeId);
  const turns = activeChat?.turns ?? [];
  const hasThread = turns.length > 0;

  // Auto-resize textarea
  useEffect(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 320)}px`;
  }, [draft]);

  // Persist custom personas
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      router.replace("/");
      return;
    }
    localStorage.setItem(userStorageKey("pt-custom-personas"), JSON.stringify(customPersonas));
  }, [customPersonas]);

  useEffect(() => {
    if (localStorage.getItem(TOKEN_KEY)) {
      localStorage.setItem(userStorageKey(CHATS_KEY), JSON.stringify(chats));
    }
  }, [chats]);

  useEffect(() => {
    if (activeId && localStorage.getItem(TOKEN_KEY)) {
      localStorage.setItem(userStorageKey(ACTIVE_CHAT_KEY), activeId);
    }
  }, [activeId]);

  useEffect(() => {
    if (localStorage.getItem(TOKEN_KEY)) {
      localStorage.setItem(userStorageKey(SIDEBAR_KEY), sidebarCollapsed ? "1" : "0");
    }
  }, [sidebarCollapsed]);

  useEffect(() => {
    if (!activeId) {
      const created = newChatSession();
      setChats((prev) => (prev.length ? prev : [created]));
      setActiveId((id) => id || created.id);
    }
  }, [activeId]);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((j) => setBackendOk(Boolean(j.ok)))
      .catch(() => setBackendOk(false));
  }, []);

  const updateActiveChat = useCallback((patch: Partial<ChatSession> | ((c: ChatSession) => ChatSession)) => {
    setChats((prev) =>
      prev.map((c) => {
        if (c.id !== activeId) return c;
        return typeof patch === "function" ? patch(c) : { ...c, ...patch, updatedAt: Date.now() };
      })
    );
  }, [activeId]);

  const handleNewChat = () => {
    const current = chats.find((c) => c.id === activeId);
    if (current && current.turns.length === 0 && !draft.trim()) {
      setResults([]);
      setError(null);
      return;
    }
    const created = newChatSession();
    setChats((prev) => [created, ...prev.filter((c) => c.turns.length > 0)]);
    setActiveId(created.id);
    setDraft("");
    setResults([]);
    setError(null);
    setSelectedIds(new Set());
    setTargetLanguage(null);
  };

  const handleSelectChat = (id: string) => {
    const chat = chats.find((c) => c.id === id);
    if (!chat) return;
    setActiveId(id);
    setSelectedIds(new Set(chat.selectedIds));
    setTargetLanguage(chat.targetLanguage);
    setDraft("");
    setResults([]);
    setError(null);
  };

  const handleDeleteChat = (id: string) => {
    setChats((prev) => {
      const next = prev.filter((c) => c.id !== id);
      if (id === activeId) {
        const fallback = next.find((c) => c.turns.length > 0) ?? newChatSession();
        if (!next.find((c) => c.id === fallback.id)) next.unshift(fallback);
        setActiveId(fallback.id);
        setDraft("");
        setResults([]);
        setSelectedIds(new Set(fallback.selectedIds));
        setTargetLanguage(fallback.targetLanguage);
      }
      return next;
    });
  };

  const togglePersona = useCallback((p: Persona) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(p.id)) next.delete(p.id);
      else next.add(p.id);
      return next;
    });
  }, []);

  const removePersona = (id: string) => {
    setSelectedIds((prev) => { const next = new Set(prev); next.delete(id); return next; });
  };

  const handleSaveCustom = (p: Persona) => {
    setCustomPersonas((prev) => [...prev, p]);
    setSelectedIds((prev) => new Set([...prev, p.id]));
    setShowCustomForm(false);
    setShowPersonaPicker(true);
  };

  const handleTransform = async () => {
    if (!draft.trim()) { setError("Please write or paste your draft first."); return; }
    if (selectedIds.size === 0) { setError("Please select at least one persona before transforming."); return; }

    setError(null);
    setIsTransforming(true);
    setResults([]);

    try {
      const res = await fetch("/api/transform/batch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ""}`,
        },
        body: JSON.stringify({
          draft,
          chat_id: activeId || undefined,
          personas: selectedPersonas.map((p) => ({
            id: p.id,
            label: p.label,
            description: p.description,
            tone: p.tone,
          })),
          target_language: targetLanguage ?? undefined,
        }),
      });

      const json = await res.json();

      if (!res.ok) {
        if (res.status === 401) {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem("pt-user-id");
          router.replace("/");
        }
        throw new Error(json.detail || json.error || "Transform failed");
      }

      const data: TransformResult[] = sanitizeResults(json.data ?? []);
      setResults(data);
      const turn: ChatTurn = {
        id: crypto.randomUUID(),
        draft,
        results: data,
        targetLanguage,
        createdAt: Date.now(),
      };
      setChats((prev) => {
        const exists = prev.some((c) => c.id === activeId);
        const base = exists ? prev : [newChatSession(), ...prev];
        const id = exists ? activeId : base[0].id;
        if (!exists) setActiveId(id);
        return base.map((c) => {
          if (c.id !== id) return c;
          const isFirst = c.turns.length === 0;
          return {
            ...c,
            title: isFirst || c.title === "New chat" ? titleFromDraft(draft) : c.title,
            selectedIds: Array.from(selectedIds),
            targetLanguage,
            turns: [...c.turns, turn],
            updatedAt: Date.now(),
          };
        });
      });
      setDraft("");
      setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 100);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong. Please try again.");
    } finally {
      setIsTransforming(false);
    }
  };

  const handleRegenerateOne = async (
    result: TransformResult,
    turnId: string,
    turnLanguage: string | null,
    instructions?: string,
  ) => {
    const persona = allPersonas.find((item) => item.id === result.persona_id);
    if (!persona || !result.original.trim()) {
      setError("Could not find the persona or original draft for this output.");
      return;
    }
    try {
      const res = await fetch("/api/transform/batch", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ""}`,
        },
        body: JSON.stringify({
          draft: result.original,
          chat_id: activeId || undefined,
          personas: [{
            id: persona.id,
            label: persona.label,
            description: persona.description,
            tone: persona.tone,
            custom_instructions: [
              persona.custom ? persona.description : undefined,
              instructions?.trim() || undefined,
            ].filter(Boolean).join("\n") || undefined,
          }],
          target_language: turnLanguage ?? undefined,
        }),
      });
      const json = await res.json();
      if (!res.ok) throw new Error(json.detail || json.error || "Rewrite failed");
      const newResult: TransformResult = json.data?.[0];
      if (!newResult) throw new Error("The backend returned no rewritten output.");
      if (newResult.error) throw new Error(newResult.error);
      const cleaned = sanitizeResults([newResult])[0];
      setResults((prev) => prev.map((item) =>
        item.persona_id === result.persona_id ? cleaned : item
      ));
      updateActiveChat((chat) => {
        const targetTurnId = turnId || [...chat.turns].reverse().find((turn) =>
          turn.results.some((item) =>
            item.persona_id === result.persona_id && item.original === result.original
          )
        )?.id;
        return {
          ...chat,
          turns: chat.turns.map((turn) =>
            turn.id === targetTurnId
              ? {
                  ...turn,
                  results: turn.results.map((item) =>
                    item.persona_id === result.persona_id ? cleaned : item
                  ),
                }
              : turn
          ),
        };
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Rewrite failed");
    }
  };

  const handleFeedback = async (outputId: string, feedback: "like" | "dislike" | null) => {
    try {
      const response = await fetch(`/api/transform/outputs/${encodeURIComponent(outputId)}/feedback`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem(TOKEN_KEY) || ""}`,
        },
        body: JSON.stringify({ feedback }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Could not save feedback");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save feedback");
    }
  };

  const wordCount = draft.trim().split(/\s+/).filter(Boolean).length;

  return (
    <div className="h-screen bg-[#080808] flex overflow-hidden">
      <ChatSidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed((v) => !v)}
        chats={chats}
        activeId={activeId}
        onNewChat={handleNewChat}
        onSelect={handleSelectChat}
        onDelete={handleDeleteChat}
        onSignOut={() => {
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem("pt-user-id");
          router.push("/");
        }}
      />

      <div className="flex-1 min-w-0 flex flex-col">
      {/* ---- Header ---- */}
      <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[#080808]/80 backdrop-blur-xl px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {sidebarCollapsed && (
            <button
              onClick={() => setSidebarCollapsed(false)}
              className="w-8 h-8 rounded-lg flex items-center justify-center text-white/40 hover:text-white hover:bg-white/8 md:hidden"
              title="Open sidebar"
            >
              <PanelLeft className="w-4 h-4" />
            </button>
          )}
          <span className="text-white font-semibold text-sm tracking-tight truncate">
            {activeChat?.title || "New chat"}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[11px] ${backendOk ? "text-emerald-400/80" : backendOk === false ? "text-red-400/80" : "text-white/30"}`}>
            {backendOk ? "Backend connected" : backendOk === false ? "Backend offline" : "Checking backend"}
          </span>
        </div>
      </header>

      {/* ---- Main ---- */}
      <main className="flex-1 flex flex-col items-center px-4 pt-10 pb-8 overflow-y-auto">
        {hasThread && (
          <div ref={resultsRef} className="w-full max-w-2xl space-y-8 mb-10">
            {turns.map((turn) => (
              <div key={turn.id} className="space-y-4">
                <div className="flex justify-end">
                  <div className="max-w-[85%] bg-white/10 border border-white/[0.08] rounded-2xl px-4 py-3 text-sm text-white/80 whitespace-pre-wrap">
                    {turn.draft}
                  </div>
                </div>
                {turn.results.map((result) => (
                  <ResultCard
                    key={`${turn.id}-${result.persona_id}`}
                    result={result}
                    draftId={`${turn.id}-${result.output_id ?? result.persona_id}`}
                    selectedPersonas={selectedPersonas}
                    onRegenerate={(instructions) => handleRegenerateOne(result, turn.id, turn.targetLanguage, instructions)}
                    onFeedback={handleFeedback}
                  />
                ))}
              </div>
            ))}
          </div>
        )}
        {/* Hero */}
        {!hasThread && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="text-center mb-10"
        >
          <h1 className="text-4xl sm:text-5xl font-semibold text-white tracking-tight leading-tight">
            One message.{" "}
            <span className="text-white/40">Every persona.</span>
          </h1>
          <p className="mt-4 text-white/40 text-base sm:text-lg max-w-lg mx-auto leading-relaxed">
            Transform your rough drafts into the right message for every audience.
          </p>
        </motion.div>
        )}

        {/* ---- Composer ---- */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
          className="w-full max-w-2xl"
        >
          {/* Selected persona chips */}
          <AnimatePresence>
            {selectedPersonas.length > 0 && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="flex flex-wrap gap-1.5 mb-3"
              >
                {selectedPersonas.map((p) => (
                  <PersonaChip key={p.id} persona={p} onRemove={() => removePersona(p.id)} />
                ))}
                {targetLanguage && (
                  <motion.span
                    initial={{ opacity: 0, scale: 0.85 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-blue-500/15 border border-blue-500/30 text-blue-300/80 text-xs font-medium"
                  >
                    <Globe className="w-3 h-3" />
                    {targetLanguage}
                    <button onClick={() => setTargetLanguage(null)} className="ml-0.5 opacity-60 hover:opacity-100">
                      <X className="w-3 h-3" />
                    </button>
                  </motion.span>
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Composer box */}
          <div className="bg-[#111111] border border-white/[0.09] rounded-2xl shadow-2xl shadow-black/40 overflow-visible">
            <textarea
              ref={textareaRef}
              value={draft}
              onChange={(e) => { setDraft(e.target.value); setResults([]); setError(null); }}
              placeholder="Write or paste your rough draft here..."
              className="w-full bg-transparent text-white text-[15px] placeholder:text-white/20 resize-none p-5 pb-2 focus:outline-none leading-relaxed min-h-[140px]"
              style={{ height: "auto" }}
            />

            {/* Bottom toolbar */}
            <div className="flex items-center gap-1.5 px-4 pb-4 pt-2 relative">
              {/* Add Persona */}
              <div className="relative" ref={personaAnchorRef}>
                <button
                  onClick={() => {
                    setShowPersonaPicker(!showPersonaPicker);
                    setShowLangPicker(false);
                    setShowCustomForm(false);
                  }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                    selectedIds.size > 0
                      ? "border-white/25 bg-white/10 text-white/80"
                      : "border-white/[0.08] text-white/40 hover:text-white/70 hover:border-white/20 hover:bg-white/5"
                  }`}
                >
                  <Plus className="w-3.5 h-3.5" />
                  {selectedIds.size > 0 ? `${selectedIds.size} persona${selectedIds.size > 1 ? "s" : ""}` : "Add persona"}
                </button>

                <AnimatePresence>
                  {showPersonaPicker && !showCustomForm && (
                    <PersonaPicker
                      selected={selectedIds}
                      onToggle={togglePersona}
                      onClose={() => setShowPersonaPicker(false)}
                      onCreateCustom={() => { setShowPersonaPicker(false); setShowCustomForm(true); }}
                      customPersonas={customPersonas}
                    />
                  )}
                  {showCustomForm && (
                    <CustomPersonaForm
                      onSave={handleSaveCustom}
                      onCancel={() => { setShowCustomForm(false); setShowPersonaPicker(true); }}
                    />
                  )}
                </AnimatePresence>
              </div>

              {/* Translate */}
              <div className="relative" ref={langAnchorRef}>
                <button
                  onClick={() => {
                    setShowLangPicker(!showLangPicker);
                    setShowPersonaPicker(false);
                    setShowCustomForm(false);
                  }}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl border text-xs font-medium transition-all ${
                    targetLanguage
                      ? "border-blue-500/30 bg-blue-500/10 text-blue-300/80"
                      : "border-white/[0.08] text-white/40 hover:text-white/70 hover:border-white/20 hover:bg-white/5"
                  }`}
                >
                  <Globe className="w-3.5 h-3.5" />
                  {targetLanguage ? targetLanguage : "Translate"}
                </button>

                <AnimatePresence>
                  {showLangPicker && (
                    <LanguagePicker
                      selected={targetLanguage}
                      onSelect={setTargetLanguage}
                      onClose={() => setShowLangPicker(false)}
                    />
                  )}
                </AnimatePresence>
              </div>

              {/* Word count */}
              <span className="ml-2 text-[11px] text-white/20">
                {wordCount > 0 ? `${wordCount} words` : ""}
              </span>

              {/* Transform button */}
              <button
                onClick={handleTransform}
                disabled={isTransforming || !draft.trim()}
                className="ml-auto flex items-center gap-2 px-4 py-1.5 rounded-xl bg-white text-black text-xs font-semibold hover:bg-white/90 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                {isTransforming ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-3.5 h-3.5 border-2 border-black/20 border-t-black rounded-full"
                    />
                    Transforming…
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    Transform
                    <ArrowRight className="w-3.5 h-3.5" />
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Error / hint */}
          <AnimatePresence>
            {error && (
              <motion.p
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-3 text-xs text-red-400/80 text-center"
              >
                {error}
              </motion.p>
            )}
          </AnimatePresence>
        </motion.div>

        {/* ---- Loading ---- */}
        <AnimatePresence>
          {isTransforming && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="mt-12 flex flex-col items-center gap-3 text-center"
            >
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-white/40"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{ duration: 1.2, repeat: Infinity, delay: i * 0.2 }}
                  />
                ))}
              </div>
              <p className="text-sm text-white/30">
                Transforming your draft
                {selectedPersonas.length > 1 ? ` for ${selectedPersonas.length} personas` : ""}
                {targetLanguage ? ` → ${targetLanguage}` : ""}…
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {/* ---- Live results (before chat persist paints) ---- */}
        <AnimatePresence>
          {results.length > 0 && !isTransforming && !hasThread && (
            <motion.div
              ref={resultsRef}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="mt-12 w-full max-w-2xl space-y-5"
            >
              {results.map((result, idx) => (
                <motion.div
                  key={result.persona_id}
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.08, duration: 0.35 }}
                >
                  <ResultCard
                    result={result}
                    draftId={`${activeId}-${result.output_id ?? result.persona_id}`}
                    selectedPersonas={selectedPersonas}
                    onRegenerate={(instructions) => handleRegenerateOne(
                      result,
                      activeChat?.turns.find((turn) =>
                        turn.results.some((item) => item.persona_id === result.persona_id)
                      )?.id ?? "",
                      targetLanguage,
                      instructions,
                    )}
                    onFeedback={handleFeedback}
                  />
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>
      </main>
      </div>
    </div>
  );
}
