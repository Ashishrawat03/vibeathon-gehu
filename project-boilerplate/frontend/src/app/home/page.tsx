"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Sparkles,
  Copy,
  Check,
  ChevronDown,
  Briefcase,
  Heart,
  Scale,
  Zap,
  ArrowRightLeft,
  FileText,
  BarChart2,
  MessageSquare,
  LogOut,
  History,
  Settings,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useRouter } from "next/navigation";

const PERSONAS = [
  {
    id: "executive",
    label: "Executive C-Level",
    description: "Crisp, decisive, results-focused",
    icon: Briefcase,
    color: "text-white",
    bg: "bg-white/8",
  },
  {
    id: "peer",
    label: "Supportive Peer",
    description: "Warm, empathetic, encouraging",
    icon: Heart,
    color: "text-white",
    bg: "bg-white/8",
  },
  {
    id: "legal",
    label: "Legal / Compliance",
    description: "Precise, neutral, formal",
    icon: Scale,
    color: "text-white",
    bg: "bg-white/8",
  },
  {
    id: "genz",
    label: "Gen-Z Hype",
    description: "Energetic, casual, relatable",
    icon: Zap,
    color: "text-white",
    bg: "bg-white/8",
  },
];

const PLUS_OPTIONS = [
  { id: "voice-mix", label: "Voice Mix", icon: Sparkles, description: "Choose a persona preset" },
  { id: "context", label: "Context", icon: FileText, description: "Add audience / channel info" },
  { id: "compare", label: "Compare Mode", icon: ArrowRightLeft, description: "See all rewrites side by side" },
  { id: "diff", label: "Diff View", icon: BarChart2, description: "Track what changed" },
  { id: "constraints", label: "Constraints", icon: Settings, description: "Must keep / never use rules" },
  { id: "tone-prompt", label: "Tone Prompt", icon: MessageSquare, description: "Custom tone instructions" },
];

const TABS = ["Rewrite", "Diff", "Compare", "Prompt"];

const SAMPLE_REWRITE = `Hi team,

okay real talk: bottom line — API integration is running late by 3 days.

• Frontend is stuck on the auth bug
• Need two more people to hit the Friday demo

Ask: confirm by EOD.

we're locked in, let's ship it fr.

Best,
[Your name]`;

const REWRITTEN_VERSIONS: Record<string, string> = {
  executive: `Team,

API integration is delayed by 3 days due to auth issues. We need 2 additional engineers to meet the Friday demo deadline. Confirm resource availability by EOD.

— [Your name]`,
  peer: `Hey everyone 👋

Just wanted to give you all a heads-up — we're running about 3 days behind on the API integration, mostly because of a tricky auth bug on the frontend.

We could really use 2 more people to help us push through before the Friday demo. Would anyone be able to jump in? Means a lot 🙏

Thanks so much,
[Your name]`,
  legal: `To: Engineering Team
Re: API Integration — Schedule Variance Notification

Please be advised that the API integration deliverable is delayed by approximately 72 hours from the originally agreed timeline. The delay is attributable to unresolved frontend authentication issues. Resource augmentation of two (2) additional engineers is required to achieve the Friday demonstration milestone.

Action required: Confirm availability by end of business.

Regards,
[Your name]`,
  genz: `okay real talk: API integration is running late by 3 days no cap 💀

frontend auth bug is actually cooked rn. we NEED 2 more ppl or the friday demo is cooked too

hmu by EOD if you can help, fr we're locked in 🔒

— [Your name]`,
};

export default function HomePage() {
  const router = useRouter();
  const [rawDraft, setRawDraft] = useState("");
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("Rewrite");
  const [showPlusMenu, setShowPlusMenu] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isTransforming, setIsTransforming] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [wordCount, setWordCount] = useState(0);
  const plusMenuRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const words = rawDraft.trim().split(/\s+/).filter(Boolean).length;
    setWordCount(words);
  }, [rawDraft]);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (plusMenuRef.current && !plusMenuRef.current.contains(e.target as Node)) {
        setShowPlusMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleTransform = () => {
    if (!rawDraft.trim() || !selectedPersona) return;
    setIsTransforming(true);
    setTimeout(() => {
      setIsTransforming(false);
      setShowResult(true);
    }, 1200);
  };

  const handleCopy = () => {
    const text = showResult && selectedPersona ? REWRITTEN_VERSIONS[selectedPersona] : "";
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const rewrittenText = selectedPersona ? REWRITTEN_VERSIONS[selectedPersona] : "";

  const computeChangedPercent = () => {
    if (!showResult || !selectedPersona) return 0;
    const orig = rawDraft.trim().split(/\s+/).filter(Boolean).length;
    const rw = rewrittenText.trim().split(/\s+/).filter(Boolean).length;
    const change = Math.abs(rw - orig);
    return Math.min(100, Math.round((change / Math.max(orig, 1)) * 100 + 20));
  };

  return (
    <div className="min-h-screen bg-[#080808] flex flex-col">
      {/* Top nav */}
      <header className="border-b border-white/[0.06] px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-white flex items-center justify-center">
              <Sparkles className="w-3 h-3 text-black" />
            </div>
            <span className="text-white font-semibold text-sm tracking-tight">VoiceCraft</span>
          </div>
          <span className="text-white/20 text-xs">/</span>
          <span className="text-white/40 text-xs">AI Persona Transformer</span>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-1.5 rounded-md text-white/30 hover:text-white/60 hover:bg-white/5 transition-all">
            <History className="w-4 h-4" />
          </button>
          <button
            onClick={() => router.push("/")}
            className="p-1.5 rounded-md text-white/30 hover:text-white/60 hover:bg-white/5 transition-all"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Page title */}
      <div className="px-6 pt-6 pb-4 shrink-0">
        <h1 className="text-2xl font-semibold text-white tracking-tight">Persona Transformer</h1>
        <p className="text-white/35 text-sm mt-0.5">
          One rough draft, any voice. Mix the tone yourself, set your priorities, and see exactly what changed.
        </p>
      </div>

      {/* Main grid */}
      <div className="flex-1 grid grid-cols-[320px_1fr_340px] gap-0 overflow-hidden">
        {/* LEFT: Raw draft + Voice mix */}
        <div className="border-r border-white/[0.06] flex flex-col overflow-y-auto">
          {/* Raw Draft Section */}
          <div className="p-4 border-b border-white/[0.06]">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-white/50 uppercase tracking-wider">Raw draft</span>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setRawDraft(
                      "API integration is delayed by 3 days\nFrontend is blocked on the auth bug\nNeed two more people to hit the Friday demo"
                    );
                    setShowResult(false);
                  }}
                  className="text-xs text-white/30 hover:text-white/60 transition-colors"
                >
                  Sample
                </button>
                <button
                  onClick={() => {
                    setRawDraft("");
                    setShowResult(false);
                  }}
                  className="text-xs text-white/30 hover:text-white/60 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>

            <div className="relative">
              <textarea
                ref={textareaRef}
                value={rawDraft}
                onChange={(e) => {
                  setRawDraft(e.target.value);
                  setShowResult(false);
                }}
                placeholder={`Bullets, a rushed email, blunt feedback...`}
                className="w-full bg-[#111111] border border-white/[0.07] rounded-xl text-white text-sm placeholder:text-white/20 resize-none p-3 min-h-[140px] focus:outline-none focus:border-white/20 transition-colors"
              />
              {/* Plus button */}
              <div className="relative" ref={plusMenuRef}>
                <button
                  onClick={() => setShowPlusMenu(!showPlusMenu)}
                  className="absolute bottom-3 left-3 w-6 h-6 rounded-md bg-white/10 hover:bg-white/20 flex items-center justify-center transition-all text-white/50 hover:text-white"
                >
                  <Plus className="w-3.5 h-3.5" />
                </button>

                <AnimatePresence>
                  {showPlusMenu && (
                    <motion.div
                      initial={{ opacity: 0, scale: 0.95, y: 8 }}
                      animate={{ opacity: 1, scale: 1, y: 0 }}
                      exit={{ opacity: 0, scale: 0.95, y: 8 }}
                      transition={{ duration: 0.15 }}
                      className="absolute bottom-10 left-0 bg-[#161616] border border-white/10 rounded-xl p-1.5 shadow-2xl shadow-black/80 z-50 w-56"
                    >
                      {PLUS_OPTIONS.map((opt) => {
                        const Icon = opt.icon;
                        return (
                          <button
                            key={opt.id}
                            onClick={() => setShowPlusMenu(false)}
                            className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-left hover:bg-white/[0.06] transition-colors group"
                          >
                            <Icon className="w-3.5 h-3.5 text-white/40 group-hover:text-white/70 shrink-0" />
                            <div>
                              <div className="text-xs font-medium text-white/70 group-hover:text-white leading-none">
                                {opt.label}
                              </div>
                              <div className="text-[10px] text-white/25 mt-0.5 leading-none">{opt.description}</div>
                            </div>
                          </button>
                        );
                      })}
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </div>

            <div className="flex items-center justify-between mt-2">
              <span className="text-[11px] text-white/25">{wordCount} words</span>
            </div>
          </div>

          {/* Voice Mix */}
          <div className="p-4">
            <div className="mb-3">
              <span className="text-xs font-medium text-white/50 uppercase tracking-wider">Voice mix</span>
              <p className="text-[11px] text-white/25 mt-0.5">Choose from a preset to transform your draft</p>
            </div>

            <div className="grid grid-cols-1 gap-1.5">
              {PERSONAS.map((persona) => {
                const Icon = persona.icon;
                const isSelected = selectedPersona === persona.id;
                return (
                  <button
                    key={persona.id}
                    onClick={() => {
                      setSelectedPersona(persona.id);
                      setShowResult(false);
                    }}
                    className={`flex items-center gap-2.5 px-3 py-2.5 rounded-xl border text-left transition-all duration-200 ${
                      isSelected
                        ? "border-white/30 bg-white/[0.07]"
                        : "border-white/[0.06] bg-transparent hover:border-white/15 hover:bg-white/[0.04]"
                    }`}
                  >
                    <div
                      className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 ${
                        isSelected ? "bg-white" : "bg-white/8"
                      }`}
                    >
                      <Icon className={`w-3.5 h-3.5 ${isSelected ? "text-black" : "text-white/50"}`} />
                    </div>
                    <div>
                      <div className={`text-xs font-medium ${isSelected ? "text-white" : "text-white/60"}`}>
                        {persona.label}
                      </div>
                      <div className="text-[10px] text-white/25">{persona.description}</div>
                    </div>
                    {isSelected && (
                      <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white shrink-0" />
                    )}
                  </button>
                );
              })}
            </div>

            {/* Transform button */}
            <Button
              onClick={handleTransform}
              disabled={!rawDraft.trim() || !selectedPersona || isTransforming}
              className="w-full mt-4 h-9 bg-white text-black text-sm font-semibold rounded-xl hover:bg-white/90 disabled:opacity-30 disabled:cursor-not-allowed transition-all"
            >
              {isTransforming ? (
                <span className="flex items-center gap-2">
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-3.5 h-3.5 border-2 border-black/30 border-t-black rounded-full"
                  />
                  Transforming…
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5" />
                  Transform
                </span>
              )}
            </Button>
          </div>
        </div>

        {/* CENTER: Output */}
        <div className="border-r border-white/[0.06] flex flex-col overflow-hidden">
          {/* Tab bar */}
          <div className="flex items-center gap-0 border-b border-white/[0.06] px-4 pt-3">
            {TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-xs font-medium rounded-t-md transition-all relative ${
                  activeTab === tab ? "text-white" : "text-white/35 hover:text-white/60"
                }`}
              >
                {tab}
                {activeTab === tab && (
                  <motion.div
                    layoutId="tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-px bg-white"
                  />
                )}
              </button>
            ))}
            <div className="ml-auto mb-1">
              <button
                onClick={handleCopy}
                disabled={!showResult}
                className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs text-white/40 hover:text-white/70 hover:bg-white/5 transition-all disabled:opacity-30"
              >
                {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                {copied ? "Copied" : "Copy rewrite"}
              </button>
            </div>
          </div>

          {/* Output area */}
          <div className="flex-1 p-6 overflow-y-auto">
            <AnimatePresence mode="wait">
              {!showResult ? (
                <motion.div
                  key="empty"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="h-full flex flex-col items-center justify-center text-center"
                >
                  <div className="w-12 h-12 rounded-2xl bg-white/5 border border-white/[0.06] flex items-center justify-center mb-4">
                    <Sparkles className="w-5 h-5 text-white/20" />
                  </div>
                  <p className="text-white/20 text-sm font-medium">Your transformed text will appear here</p>
                  <p className="text-white/12 text-xs mt-1">
                    {!selectedPersona
                      ? "Select a voice preset to get started"
                      : !rawDraft.trim()
                      ? "Add your raw draft on the left"
                      : "Click Transform to rewrite"}
                  </p>
                </motion.div>
              ) : (
                <motion.div
                  key="result"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="space-y-4"
                >
                  {activeTab === "Rewrite" && (
                    <div className="text-sm text-white/80 leading-relaxed whitespace-pre-wrap font-mono bg-[#0f0f0f] border border-white/[0.06] rounded-xl p-5">
                      {rewrittenText}
                    </div>
                  )}
                  {activeTab === "Diff" && (
                    <div className="space-y-2">
                      <p className="text-xs text-white/30 mb-3">Showing changes from original to rewrite</p>
                      <div className="bg-[#0f0f0f] border border-white/[0.06] rounded-xl p-5 space-y-1 font-mono text-xs">
                        {rawDraft.split("\n").map((line, i) => (
                          <div key={i} className="flex gap-2">
                            <span className="text-red-400/60">-</span>
                            <span className="text-red-400/60 line-through">{line}</span>
                          </div>
                        ))}
                        {rewrittenText.split("\n").map((line, i) => (
                          <div key={`rw-${i}`} className="flex gap-2">
                            <span className="text-green-400/60">+</span>
                            <span className="text-green-400/70">{line}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {activeTab === "Compare" && (
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <p className="text-xs text-white/30 mb-2">Original</p>
                        <div className="bg-[#0f0f0f] border border-white/[0.06] rounded-xl p-4 text-xs text-white/50 whitespace-pre-wrap font-mono">
                          {rawDraft}
                        </div>
                      </div>
                      <div>
                        <p className="text-xs text-white/30 mb-2">Rewrite</p>
                        <div className="bg-[#0f0f0f] border border-white/[0.06] rounded-xl p-4 text-xs text-white/80 whitespace-pre-wrap font-mono">
                          {rewrittenText}
                        </div>
                      </div>
                    </div>
                  )}
                  {activeTab === "Prompt" && (
                    <div className="bg-[#0f0f0f] border border-white/[0.06] rounded-xl p-5">
                      <p className="text-xs text-white/30 mb-3">Send this prompt to your LLM to go live</p>
                      <pre className="text-xs text-white/60 whitespace-pre-wrap font-mono">
                        {`Rewrite the following text in a ${selectedPersona} voice.\nMake it appropriate for professional communication.\nPreserve the core message and key facts.\n\nOriginal:\n${rawDraft}\n\nRewrite:`}
                      </pre>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* RIGHT: Change meter */}
        <div className="flex flex-col overflow-y-auto p-4 space-y-4">
          {/* Change meter */}
          <div>
            <h3 className="text-xs font-medium text-white/50 uppercase tracking-wider mb-1">Change meter</h3>
            <p className="text-[11px] text-white/25">How far the rewrite moved from your draft</p>

            <div className="mt-3 h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-white rounded-full"
                initial={{ width: "0%" }}
                animate={{ width: showResult ? `${computeChangedPercent()}%` : "0%" }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              />
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-3">
              <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Changed</div>
              <div className="text-2xl font-semibold text-white">
                {showResult ? `${computeChangedPercent()}%` : "—"}
              </div>
            </div>
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-3">
              <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Kept</div>
              <div className="text-2xl font-semibold text-white">
                {showResult
                  ? rawDraft.trim().split(/\s+/).filter(Boolean).length -
                    Math.round((computeChangedPercent() / 100) * rawDraft.trim().split(/\s+/).filter(Boolean).length)
                  : "—"}
              </div>
            </div>
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-3">
              <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Added</div>
              <div className="text-2xl font-semibold text-white/70">
                {showResult
                  ? `+${Math.max(0, rewrittenText.trim().split(/\s+/).filter(Boolean).length - rawDraft.trim().split(/\s+/).filter(Boolean).length)}`
                  : "—"}
              </div>
            </div>
            <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-3">
              <div className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Length</div>
              <div className="text-sm font-semibold text-white/70">
                {showResult
                  ? `${rawDraft.trim().split(/\s+/).filter(Boolean).length} → ${rewrittenText.trim().split(/\s+/).filter(Boolean).length}`
                  : "—"}
              </div>
            </div>
          </div>

          {/* Constraint check */}
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-3">
            <h4 className="text-[10px] text-white/30 uppercase tracking-wider mb-2">Constraint check</h4>
            <div className="flex flex-wrap gap-1.5">
              <Badge className="bg-white/8 text-white/50 border-white/10 text-[10px] px-2 py-0.5 font-normal">
                API ✓
              </Badge>
              <Badge className="bg-red-500/10 text-red-400/70 border-red-500/20 text-[10px] px-2 py-0.5 font-normal">
                missing · Friday
              </Badge>
            </div>
          </div>

          {/* Demo notice */}
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-3">
            <div className="flex gap-2">
              <div className="w-3 h-3 rounded-full border border-white/20 flex items-center justify-center shrink-0 mt-0.5">
                <div className="w-1 h-1 rounded-full bg-white/40" />
              </div>
              <div>
                <p className="text-[11px] text-white/40 font-medium">Demo engine</p>
                <p className="text-[10px] text-white/20 mt-0.5 leading-relaxed">
                  Rewrites are rule-based right now. Send the Prompt tab output to your LLM to go live.
                </p>
              </div>
            </div>
          </div>

          {/* Save voice mix */}
          <div className="bg-[#111111] border border-white/[0.07] rounded-xl p-3">
            <h4 className="text-[10px] text-white/30 uppercase tracking-wider mb-1">Save this mix</h4>
            <p className="text-[10px] text-white/20 mb-2.5">It shows up as a chip in Voice mix.</p>
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="Friday client update"
                className="flex-1 bg-[#1a1a1a] border border-white/[0.08] rounded-lg px-2.5 py-1.5 text-xs text-white/60 placeholder:text-white/20 focus:outline-none focus:border-white/20 transition-colors"
              />
              <button className="px-2.5 py-1.5 bg-white/[0.08] hover:bg-white/[0.12] text-white/60 hover:text-white rounded-lg text-xs font-medium transition-all">
                Save
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
