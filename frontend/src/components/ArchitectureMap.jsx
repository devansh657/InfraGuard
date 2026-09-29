import { useState } from "react";
import {
  Activity,
  BrainCircuit,
  ChevronDown,
  Database,
  Gauge,
  GitBranch,
  LineChart,
  RadioTower,
  ShieldCheck,
  Sparkles
} from "lucide-react";

const LAYERS = [
  {
    id: "live",
    icon: RadioTower,
    title: "1. Observe",
    module: "Live Monitor",
    summary: "Protected telemetry is replayed as a live stream so the system has movement and context."
  },
  {
    id: "lab",
    icon: BrainCircuit,
    title: "2. Diagnose",
    module: "Predict Lab",
    summary: "Manual scenarios test how the trained models respond to changing operating conditions."
  },
  {
    id: "analyst",
    icon: Sparkles,
    title: "3. Explain",
    module: "AI Analyst",
    summary: "Risk becomes root cause, confidence, drift status, recommendations, and what-if impact."
  },
  {
    id: "timeline",
    icon: Database,
    title: "4. Remember",
    module: "Timeline",
    summary: "Every decision becomes event memory for audit, incident history, and trend review."
  },
  {
    id: "insights",
    icon: LineChart,
    title: "5. Validate",
    module: "Insights",
    summary: "EDA, ROC AUC, recall, benchmark results, and model evidence prove the AI layer."
  },
  {
    id: "dashboard",
    icon: Gauge,
    title: "6. Command",
    module: "Command Center",
    summary: "The system returns to one operational view for risk, alerts, status, and NOVA control."
  }
];

const PRINCIPLES = [
  "Every feature belongs to the monitoring-to-response loop.",
  "NOVA is the interaction layer, not a separate toy.",
  "Research evidence supports the AI claims made in the dashboard."
];

function ArchitectureMap({ activePage, onNavigate }) {
  const [open, setOpen] = useState(true);

  if (!open) {
    return (
      <button
        className="mb-6 inline-flex min-h-11 items-center gap-2 rounded-2xl border border-amber-300/20 bg-amber-300/[0.1] px-4 text-sm font-black text-amber-100 transition hover:bg-amber-300/[0.16]"
        onClick={() => setOpen(true)}
        type="button"
      >
        <GitBranch size={17} />
        Show System Architecture
      </button>
    );
  }

  return (
    <section className="architecture-map mb-6 overflow-hidden rounded-2xl border border-white/10 bg-slate-950/45 p-4 shadow-2xl shadow-slate-950/25 backdrop-blur-2xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl border border-amber-300/25 bg-amber-300/[0.12] text-amber-100">
            <GitBranch size={21} />
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-[0.22em] text-amber-100">Unified Architecture</p>
            <h2 className="text-xl font-black text-white">One AI Operations Loop</h2>
          </div>
        </div>
        <button
          className="rounded-xl border border-white/10 bg-white/[0.045] px-3 py-2 text-xs font-black text-slate-300 transition hover:bg-white/[0.08]"
          onClick={() => setOpen(false)}
          type="button"
        >
          <ChevronDown size={15} className="inline" /> Hide map
        </button>
      </div>

      <div className="grid grid-cols-[1fr_300px] gap-4 max-[1080px]:grid-cols-1">
        <div className="architecture-flow">
          {LAYERS.map((layer, index) => {
            const Icon = layer.icon;
            const active = layer.id === activePage;
            return (
              <button
                className={`architecture-node ${active ? "architecture-node-active" : ""}`}
                key={layer.id}
                onClick={() => onNavigate(layer.id)}
                type="button"
              >
                <div className="mb-3 flex items-center justify-between gap-3">
                  <span className="grid h-10 w-10 place-items-center rounded-xl border border-white/10 bg-slate-950/45 text-amber-100">
                    <Icon size={19} />
                  </span>
                  <span className="font-mono text-xs text-slate-500">{String(index + 1).padStart(2, "0")}</span>
                </div>
                <p className="text-xs font-black uppercase tracking-[0.18em] text-amber-100">{layer.title}</p>
                <h3 className="mt-1 font-black text-white">{layer.module}</h3>
                <p className="mt-2 text-xs leading-5 text-slate-400">{layer.summary}</p>
              </button>
            );
          })}
        </div>

        <div className="architecture-nova">
          <div className="mb-4 flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-xl border border-cyan-300/20 bg-cyan-300/[0.1] text-cyan-100">
              <Activity size={20} />
            </div>
            <div>
              <p className="text-xs font-black uppercase tracking-[0.2em] text-cyan-100">NOVA Layer</p>
              <h3 className="font-black text-white">Controls The Loop</h3>
            </div>
          </div>
          <p className="text-sm leading-6 text-slate-300">
            NOVA sits across the full platform: it can brief risk, start scans, navigate modules,
            open analyst reasoning, and guide demos without exposing protected internals.
          </p>
          <div className="mt-4 grid gap-2">
            {PRINCIPLES.map((principle) => (
              <div className="flex gap-2 rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm text-slate-300" key={principle}>
                <ShieldCheck size={16} className="mt-0.5 shrink-0 text-emerald-200" />
                <span>{principle}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

export default ArchitectureMap;
