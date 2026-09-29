import { useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  BrainCircuit,
  Bot,
  Gauge,
  LineChart,
  RadioTower,
  ShieldCheck,
  Sparkles
} from "lucide-react";
import Dashboard from "./pages/Dashboard.jsx";
import IncidentTimeline from "./pages/IncidentTimeline.jsx";
import LiveMonitor from "./pages/LiveMonitor.jsx";
import PredictLab from "./pages/PredictLab.jsx";
import SystemInsights from "./pages/SystemInsights.jsx";
import CommandPulse from "./components/CommandPulse.jsx";
import AIAnalyst from "./pages/AIAnalyst.jsx";
import MissionGuide from "./components/MissionGuide.jsx";
import NovaAssistant from "./components/NovaAssistant.jsx";
import ArchitectureMap from "./components/ArchitectureMap.jsx";

const pages = [
  {
    id: "dashboard",
    label: "Command Center",
    role: "Mission overview",
    purpose: "Current risk, AI verdict, alerts, and live operating state.",
    icon: Gauge,
    component: Dashboard
  },
  {
    id: "live",
    label: "Live Monitor",
    role: "Telemetry stream",
    purpose: "Moving telemetry, sample replay, and live anomaly markers.",
    icon: RadioTower,
    component: LiveMonitor
  },
  {
    id: "analyst",
    label: "AI Analyst",
    role: "Reasoning layer",
    purpose: "Root cause, recommendations, drift, confidence, and what-if simulation.",
    icon: Bot,
    component: AIAnalyst
  },
  {
    id: "lab",
    label: "Predict Lab",
    role: "Experiment lab",
    purpose: "Manual scenario diagnosis against the trained model schema.",
    icon: BrainCircuit,
    component: PredictLab
  },
  {
    id: "timeline",
    label: "Timeline",
    role: "Incident memory",
    purpose: "Chronological event audit for predictions, anomalies, and failures.",
    icon: LineChart,
    component: IncidentTimeline
  },
  {
    id: "insights",
    label: "Insights",
    role: "Research evidence",
    purpose: "EDA, model metrics, benchmark comparison, and validation evidence.",
    icon: Sparkles,
    component: SystemInsights
  }
];

function App() {
  const [activePage, setActivePage] = useState("dashboard");
  const currentPage = pages.find((page) => page.id === activePage) ?? pages[0];
  const ActiveComponent = currentPage.component;

  return (
    <div className="min-h-screen overflow-hidden bg-[#050812] text-slate-100">
      <div className="fixed inset-0 bg-[radial-gradient(circle_at_top_left,rgba(35,211,171,0.18),transparent_32%),radial-gradient(circle_at_top_right,rgba(84,129,255,0.16),transparent_34%),linear-gradient(135deg,#050812_0%,#0d1526_52%,#111827_100%)]" />
      <div className="fixed inset-0 bg-[linear-gradient(rgba(255,255,255,0.025)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.025)_1px,transparent_1px)] bg-[size:42px_42px]" />

      <div className="relative grid min-h-screen grid-cols-[292px_1fr] max-[980px]:grid-cols-1">
        <aside className="border-r border-white/10 bg-slate-950/55 p-5 backdrop-blur-2xl max-[980px]:border-b max-[980px]:border-r-0">
          <div className="mb-8 flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-xl bg-emerald-400 text-slate-950 shadow-[0_0_36px_rgba(52,211,153,0.35)]">
              <Activity size={24} />
            </div>
            <div>
              <p className="text-lg font-black tracking-tight">InfraGuard AI</p>
              <p className="text-xs font-medium text-slate-400">Autonomous reliability console</p>
            </div>
          </div>

          <nav className="grid gap-2 max-[980px]:grid-cols-3 max-[720px]:grid-cols-2">
            {pages.map((page) => {
              const Icon = page.icon;
              const active = page.id === activePage;
              return (
                <button
                  className={`group flex min-h-14 items-center gap-3 rounded-xl border px-4 text-left text-sm font-bold transition ${
                    active
                      ? "border-emerald-300/40 bg-emerald-300/[0.12] text-white shadow-[0_0_24px_rgba(16,185,129,0.18)]"
                      : "border-white/5 bg-white/[0.03] text-slate-300 hover:border-cyan-300/30 hover:bg-white/[0.07]"
                  }`}
                  key={page.id}
                  onClick={() => setActivePage(page.id)}
                  type="button"
                >
                  <Icon size={18} className={active ? "text-emerald-300" : "text-slate-400"} />
                  <span className="min-w-0">
                    <span className="block truncate">{page.label}</span>
                    <span className="block truncate text-[11px] font-bold text-slate-500">{page.role}</span>
                  </span>
                </button>
              );
            })}
          </nav>

          <div className="mt-5 rounded-2xl border border-white/10 bg-white/[0.045] p-4">
            <p className="text-xs font-black uppercase tracking-[0.2em] text-emerald-200">Active module</p>
            <h2 className="mt-2 text-lg font-black text-white">{currentPage.label}</h2>
            <p className="mt-2 text-sm leading-6 text-slate-400">{currentPage.purpose}</p>
          </div>

          <div className="mt-8 rounded-2xl border border-cyan-300/[0.15] bg-cyan-300/[0.08] p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-black text-cyan-100">
              <ShieldCheck size={17} />
              Secure Runtime
            </div>
            <p className="text-sm leading-6 text-slate-300">
              Failure prediction and anomaly detection run through a protected local inference channel.
              <span className="mt-2 block rounded-xl border border-cyan-300/15 bg-cyan-300/[0.08] px-3 py-2 font-mono text-xs text-cyan-100">
                LIVE_MODEL_CHANNEL
              </span>
            </p>
          </div>
        </aside>

        <main className="min-w-0 p-7 max-[720px]:p-4">
          <CommandPulse />
          <MissionGuide activePage={activePage} onNavigate={setActivePage} />
          <ArchitectureMap activePage={activePage} onNavigate={setActivePage} />
          <motion.div
            key={currentPage.id}
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.28, ease: "easeOut" }}
          >
            <ActiveComponent />
          </motion.div>
        </main>
        <NovaAssistant activePage={activePage} onNavigate={setActivePage} />
      </div>
    </div>
  );
}

export default App;
