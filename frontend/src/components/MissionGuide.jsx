import { useMemo, useState } from "react";
import {
  BrainCircuit,
  Compass,
  Database,
  Gauge,
  GitCompareArrows,
  LineChart,
  PlayCircle,
  RadioTower,
  Sparkles
} from "lucide-react";

const GUIDE_STEPS = [
  {
    page: "dashboard",
    icon: Gauge,
    title: "1. Read Current Risk",
    detail: "Start with the command center. It shows live risk, model decision, alert feed, and the latest protected telemetry sample."
  },
  {
    page: "live",
    icon: RadioTower,
    title: "2. Watch Telemetry Move",
    detail: "Use Live Monitor to show the system ingesting new samples and updating charts, labels, AI verdicts, and alerts."
  },
  {
    page: "analyst",
    icon: BrainCircuit,
    title: "3. Ask The AI Why",
    detail: "AI Analyst explains root cause, confidence, drift, response playbook, and recommended remediation steps."
  },
  {
    page: "analyst",
    icon: GitCompareArrows,
    title: "4. Simulate What-If",
    detail: "Compare current telemetry with a mitigation scenario and show how risk, priority, and severity would change."
  },
  {
    page: "lab",
    icon: BrainCircuit,
    title: "5. Test Scenarios",
    detail: "Use Predict Lab to create manual scenarios and prove that the AI reacts to changing inputs."
  },
  {
    page: "timeline",
    icon: Database,
    title: "6. Audit Incidents",
    detail: "Open Timeline to show that predictions and anomalies become persistent incident memory."
  },
  {
    page: "insights",
    icon: LineChart,
    title: "7. Prove The Model",
    detail: "Open Insights to show EDA, benchmark results, recall, ROC AUC, and model evidence for academic/demo validation."
  }
];

function MissionGuide({ activePage, onNavigate }) {
  const [open, setOpen] = useState(true);
  const currentIndex = useMemo(() => {
    const index = GUIDE_STEPS.findIndex((step) => step.page === activePage);
    return index >= 0 ? index : 0;
  }, [activePage]);

  if (!open) {
    return (
      <button
        className="mb-6 inline-flex min-h-11 items-center gap-2 rounded-2xl border border-cyan-300/20 bg-cyan-300/[0.1] px-4 text-sm font-black text-cyan-100 transition hover:bg-cyan-300/[0.16]"
        onClick={() => setOpen(true)}
        type="button"
      >
        <Compass size={17} />
        Open Mission Guide
      </button>
    );
  }

  return (
    <section className="mission-guide mb-6 overflow-hidden rounded-2xl border border-white/10 bg-slate-950/45 p-4 shadow-2xl shadow-slate-950/25 backdrop-blur-2xl">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="grid h-11 w-11 place-items-center rounded-xl border border-cyan-300/25 bg-cyan-300/[0.12] text-cyan-100">
            <Sparkles size={21} />
          </div>
          <div>
            <p className="text-xs font-black uppercase tracking-[0.22em] text-cyan-100">Interactive Demo Guide</p>
            <h2 className="text-xl font-black text-white">How To Explain InfraGuard AI</h2>
          </div>
        </div>
        <button
          className="rounded-xl border border-white/10 bg-white/[0.045] px-3 py-2 text-xs font-black text-slate-300 transition hover:bg-white/[0.08]"
          onClick={() => setOpen(false)}
          type="button"
        >
          Hide guide
        </button>
      </div>

      <div className="grid grid-cols-[1fr_280px] gap-4 max-[980px]:grid-cols-1">
        <div className="grid gap-3 lg:grid-cols-7">
          {GUIDE_STEPS.map((step, index) => {
            const Icon = step.icon;
            const active = index === currentIndex || step.page === activePage;
            return (
              <button
                className={`guide-step group text-left ${active ? "guide-step-active" : ""}`}
                key={`${step.title}-${index}`}
                onClick={() => onNavigate(step.page)}
                type="button"
              >
                <div className="mb-3 flex items-center justify-between gap-2">
                  <span className="grid h-9 w-9 place-items-center rounded-xl border border-white/10 bg-white/[0.05] text-cyan-100">
                    <Icon size={18} />
                  </span>
                  <span className="font-mono text-xs text-slate-500">{String(index + 1).padStart(2, "0")}</span>
                </div>
                <h3 className="text-sm font-black text-white">{step.title}</h3>
                <p className="mt-2 text-xs leading-5 text-slate-400">{step.detail}</p>
              </button>
            );
          })}
        </div>

        <div className="rounded-xl border border-emerald-300/15 bg-emerald-300/[0.08] p-4">
          <div className="mb-3 flex items-center gap-2 text-emerald-100">
            <PlayCircle size={18} />
            <h3 className="font-black">One-minute story</h3>
          </div>
          <p className="text-sm leading-6 text-slate-300">
            InfraGuard AI monitors protected telemetry, predicts elevated risk, detects unusual patterns,
            explains root cause, recommends actions, and lets us test mitigation before acting.
          </p>
        </div>
      </div>
    </section>
  );
}

export default MissionGuide;
