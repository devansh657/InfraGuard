import { BrainCircuit, CheckCircle2, DatabaseZap, GitCompareArrows, RadioTower, ShieldAlert } from "lucide-react";

const FLOW = [
  {
    icon: RadioTower,
    title: "Telemetry Intake",
    detail: "Protected samples stream into the runtime.",
    tone: "cyan"
  },
  {
    icon: BrainCircuit,
    title: "Risk Classifier",
    detail: "Supervised model estimates elevated-risk probability.",
    tone: "emerald"
  },
  {
    icon: ShieldAlert,
    title: "Anomaly Engine",
    detail: "Unsupervised detector checks unusual behavior shape.",
    tone: "amber"
  },
  {
    icon: DatabaseZap,
    title: "AI Analyst",
    detail: "Root cause, confidence, drift, and recommendations.",
    tone: "violet"
  },
  {
    icon: GitCompareArrows,
    title: "What-If Action",
    detail: "Compare mitigation impact before response.",
    tone: "rose"
  }
];

function AIFlowMap() {
  return (
    <section className="ai-flow-map rounded-2xl border border-white/10 bg-white/[0.045] p-5 backdrop-blur-2xl">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-black uppercase tracking-[0.24em] text-cyan-100">AI Decision Pipeline</p>
          <h2 className="mt-1 text-2xl font-black text-white">How InfraGuard Thinks</h2>
        </div>
        <div className="inline-flex items-center gap-2 rounded-full border border-emerald-300/20 bg-emerald-300/[0.1] px-3 py-1 text-xs font-black text-emerald-100">
          <CheckCircle2 size={14} />
          Explainable loop
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-5">
        {FLOW.map((item, index) => {
          const Icon = item.icon;
          return (
            <div className={`flow-node flow-node-${item.tone}`} key={item.title}>
              <div className="mb-4 flex items-center justify-between gap-2">
                <span className="grid h-11 w-11 place-items-center rounded-xl border border-white/10 bg-slate-950/40">
                  <Icon size={21} />
                </span>
                <span className="font-mono text-xs text-slate-500">0{index + 1}</span>
              </div>
              <h3 className="font-black text-white">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-400">{item.detail}</p>
            </div>
          );
        })}
      </div>
    </section>
  );
}

export default AIFlowMap;
